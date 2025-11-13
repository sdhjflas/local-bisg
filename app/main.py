"""
BISG Labels Service - Main Flask Application
Handles Stripe checkout sessions and webhooks for automated label generation
"""

import os
import sys
import time
import json
from flask import Flask, request, jsonify, send_file, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from dotenv import load_dotenv
import stripe

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from config directory
config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
env_path = os.path.join(config_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()  # Try current directory as fallback

# Import local modules from new structure
from app.services import stripe_service, sheets_service, label_service, email_service
from app.utils import validation, security, logger

# Setup logger
app_logger = logger.setup_logger('bisg-labels')

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.logger = app_logger

# Detect environment
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
IS_PRODUCTION = FLASK_ENV == 'production'

# Enable CORS with proper origin restrictions
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*')
if IS_PRODUCTION and allowed_origins != '*':
    # In production, use specific domains
    origins_list = [origin.strip() for origin in allowed_origins.split(',')]
    CORS(app, resources={r"/*": {"origins": origins_list}})
else:
    # In development, allow all origins
    CORS(app, resources={r"/*": {"origins": "*"}})

# Security headers (only in production to avoid issues with local dev)
if IS_PRODUCTION:
    Talisman(app,
             force_https=True,
             strict_transport_security=True,
             content_security_policy={
                 'default-src': "'self'",
                 'connect-src': ["'self'", "https://app.bisglabels.com", "https://api.stripe.com"],  # Allow API connections
                 'script-src': ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://js.stripe.com"],
                 'style-src': ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://fonts.googleapis.com"],
                 'font-src': ["'self'", "https://cdnjs.cloudflare.com", "https://fonts.gstatic.com"],
                 'img-src': ["'self'", "data:", "https:"],
             })

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=security.rate_limit_key,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


# ==================== ENVIRONMENT VALIDATION ====================

def validate_environment():
    """
    Validate required environment variables at startup.
    Exits with error if critical variables are missing.
    """
    required_vars = [
        'FLASK_SECRET_KEY',
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'GOOGLE_SHEETS_CREDS',
        'STOCK_SHEET_ID',
        'FORM_SHEET_ID',
        'GMAIL_TOKEN',
        'SENDER_EMAIL'
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        error_msg = f"❌ Missing required environment variables: {', '.join(missing_vars)}"
        app.logger.error(error_msg)
        print(error_msg)
        print("\n💡 Check your .env file and ensure all required variables are set.")
        print("   See config/.env.example for reference.\n")
        raise SystemExit(1)

    # Validate Stripe key format
    stripe_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe_key.startswith('sk_'):
        app.logger.warning("⚠️  STRIPE_SECRET_KEY doesn't start with 'sk_' - may be invalid")

    if stripe_key.startswith('sk_live_'):
        app.logger.warning("⚠️  Using LIVE Stripe key - real charges will occur!")

    app.logger.info("✅ All required environment variables are set")


# ==================== FRONTEND ====================

@app.route('/', methods=['GET'])
def serve_frontend():
    """Serve the frontend HTML page"""
    frontend_path = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(frontend_path):
        return send_file(frontend_path)
    else:
        return jsonify({'error': 'Frontend not found', 'path': frontend_path}), 404


@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests to prevent 404/403 errors"""
    # Return a 204 No Content response (no favicon available)
    return '', 204


# ==================== HEALTH CHECK ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Railway"""
    import stripe
    stripe_file = stripe.__file__ if hasattr(stripe, '__file__') else 'unknown'
    return jsonify({
        'status': 'healthy',
        'service': 'BISG Labels',
        'version': '1.0.0',
        'stripe_location': stripe_file
    }), 200


# ==================== SUCCESS PAGE ====================

@app.route('/success', methods=['GET'])
def payment_success():
    """Success page after Stripe checkout"""
    # Get customer type from query parameters (set in checkout URL)
    customer_type = request.args.get('type', 'direct')

    # Different messages for PBS vs Direct customers
    if customer_type == 'pbs':
        message = """
            <h1>Payment Successful!</h1>
            <p>Thank you for your order. Your BISG-compliant labels have been generated and are being sent via email.</p>
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: left;">
                <p style="margin: 0 0 10px 0; font-size: 16px;"><strong>✅ Labels Sent to Pathway Book Service</strong></p>
                <p style="margin: 0; font-size: 14px;">Your labels have been automatically sent to Pathway Book Service and will be applied to your shipment.</p>
                <p style="margin: 10px 0 0 0; font-size: 14px;">You'll also receive a copy for your records via email shortly.</p>
            </div>
            <p style="font-size: 14px;"><small>Please check your email (including spam folder) for your label copies.</small></p>
        """
    else:
        message = """
            <h1>Payment Successful!</h1>
            <p>Thank you for your order. Your BISG-compliant labels are being generated and will be emailed to you shortly.</p>
            <p style="font-size: 14px;"><small>Please check your email (including spam folder) for your labels.</small></p>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Successful - BISG Labels</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 60px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 550px;
            }}
            .checkmark {{
                width: 80px;
                height: 80px;
                border-radius: 50%;
                display: block;
                stroke-width: 2;
                stroke: #4bb71b;
                stroke-miterlimit: 10;
                margin: 0 auto 30px;
                box-shadow: inset 0px 0px 0px #4bb71b;
                animation: fill .4s ease-in-out .4s forwards, scale .3s ease-in-out .9s both;
            }}
            .checkmark__circle {{
                stroke-dasharray: 166;
                stroke-dashoffset: 166;
                stroke-width: 2;
                stroke-miterlimit: 10;
                stroke: #4bb71b;
                fill: none;
                animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
            }}
            .checkmark__check {{
                transform-origin: 50% 50%;
                stroke-dasharray: 48;
                stroke-dashoffset: 48;
                animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;
            }}
            @keyframes stroke {{
                100% {{ stroke-dashoffset: 0; }}
            }}
            @keyframes scale {{
                0%, 100% {{ transform: none; }}
                50% {{ transform: scale3d(1.1, 1.1, 1); }}
            }}
            @keyframes fill {{
                100% {{ box-shadow: inset 0px 0px 0px 30px #4bb71b; }}
            }}
            h1 {{ color: #333; margin-bottom: 20px; }}
            p {{ color: #666; font-size: 18px; line-height: 1.6; }}
            .btn {{
                display: inline-block;
                margin-top: 30px;
                padding: 15px 40px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                transition: transform 0.2s;
            }}
            .btn:hover {{ transform: translateY(-2px); }}
        </style>
    </head>
    <body>
        <div class="container">
            <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
                <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
            </svg>
            {message}
            <a href="/" class="btn">Return to Home</a>
        </div>
    </body>
    </html>
    """


# ==================== MIDDLEWARE ====================

@app.before_request
def before_request():
    """Execute before each request"""
    g.start_time = time.time()

    # Log request
    if os.getenv('ENABLE_REQUEST_LOGGING', 'True') == 'True':
        logger.log_request(app.logger, request)


@app.after_request
def after_request(response):
    """Execute after each request"""
    # Calculate request duration
    if hasattr(g, 'start_time'):
        duration_ms = (time.time() - g.start_time) * 1000
        logger.log_response(app.logger, request, response, duration_ms)

    return response


# ==================== CREATE CHECKOUT SESSION ====================

@app.route('/create-checkout', methods=['POST', 'OPTIONS'])
@limiter.limit(os.getenv('RATE_LIMIT_CHECKOUT', '10 per minute'))
@security.require_json
def create_checkout():
    """
    Create Stripe checkout session for label purchase

    Expected JSON body:
    {
        "isbn": "9780985347024",
        "date": "10/2/2025",
        "label_type": "both",  // 'book', 'carton', or 'both'
        "customer_type": "pbs",  // 'pbs' or 'direct'
        "book_format": "both",  // 'single', 'sheet', or 'both' - optional, default: 'both'
        "carton_format": "both"  // 'single', 'twoup', or 'both' - optional, default: 'both'
    }

    Returns:
    {
        "checkout_url": "https://checkout.stripe.com/..."
    }
    """
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()

        # Check honeypot for bot detection
        if not security.check_honeypot(data):
            app.logger.warning(f"Honeypot triggered from IP: {security.get_client_ip()}")
            return jsonify({'error': 'Invalid request'}), 400

        # Sanitize all input data
        data = security.sanitize_checkout_data(data)

        # Log sanitized data (without sensitive info)
        safe_log_data = logger.sanitize_log_data(data)
        app.logger.info(f"Checkout request from {security.get_client_ip()}: ISBN {data.get('isbn', 'N/A')}")

        # Validate request data
        is_valid, error_msg = validation.validate_checkout_request(data)
        if not is_valid:
            app.logger.error(f"Validation failed: {error_msg}")
            return jsonify({'error': error_msg}), 400

        isbn = data['isbn']
        date = data.get('date', '')  # Optional for book-only orders
        label_type = data['label_type']
        customer_type = data['customer_type']
        book_format = data.get('book_format', 'both')  # Default to both (single + sheet)
        carton_format = data.get('carton_format', 'both')  # Default to both (single + twoup)

        # Handle direct publishers vs PBS clients differently
        if customer_type == 'direct':
            # Direct publishers provide all data in the form
            book_title = data.get('title', 'Unknown Title')
            publisher_email = data.get('email', '')

            if not publisher_email:
                return jsonify({
                    'error': 'Email is required',
                    'details': 'Please provide your email address'
                }), 400

            # Store the provided data for later use in webhook
            combined_data = {
                'title': data.get('title', ''),
                'author': data.get('author', ''),
                'publisher': data.get('publisher', ''),
                'isbn': isbn,
                'price': data.get('price', '0'),
                'currency': data.get('currency', 'USD'),
                'country': data.get('country', 'USA'),
                'pub_date': data.get('pub_date', ''),
                'carton_qty': data.get('carton_qty', '10'),
                'carton_weight': data.get('carton_weight', '0'),
                'books_per_carton': data.get('books_per_carton', '1'),
                'publisher_email': publisher_email,
                'is_custom_upc': data.get('is_custom_upc', False)
            }

        else:
            # PBS clients - lookup from Google Sheets
            app.logger.info(f"Looking up data for ISBN {isbn}, date {date}")
            combined_data = sheets_service.get_combined_data(isbn, date)
            app.logger.info(f"Got combined data: {combined_data}")

            if not combined_data:
                return jsonify({
                    'error': 'Book data not found',
                    'details': f'No record found for ISBN {isbn} on {date}'
                }), 404

            book_title = combined_data.get('title', 'Unknown Title')
            publisher_email = combined_data.get('publisher_email', '')

            if not publisher_email:
                return jsonify({
                    'error': 'Publisher email not found',
                    'details': 'Unable to pre-fill customer email'
                }), 404

        # Create Stripe checkout session
        # For direct publishers, pass all book data in metadata as JSON
        if customer_type == 'direct':
            book_data_json = json.dumps({
                'title': combined_data.get('title'),
                'author': combined_data.get('author'),
                'publisher': combined_data.get('publisher'),
                'price': combined_data.get('price'),
                'currency': combined_data.get('currency'),
                'country': combined_data.get('country'),
                'pub_date': combined_data.get('pub_date'),
                'carton_qty': combined_data.get('carton_qty'),
                'carton_weight': combined_data.get('carton_weight'),
                'books_per_carton': combined_data.get('books_per_carton'),
                'is_custom_upc': combined_data.get('is_custom_upc', False)
            })
            checkout_url = stripe_service.create_checkout_session(
                isbn=isbn,
                date=date,
                label_type=label_type,
                customer_type=customer_type,
                book_title=book_title,
                publisher_email=publisher_email,
                book_data=book_data_json,  # Pass as JSON string
                book_format=book_format,
                carton_format=carton_format
            )
        else:
            checkout_url = stripe_service.create_checkout_session(
                isbn=isbn,
                date=date,
                label_type=label_type,
                customer_type=customer_type,
                book_title=book_title,
                publisher_email=publisher_email,
                book_format=book_format,
                carton_format=carton_format
            )

        return jsonify({'checkout_url': checkout_url}), 200

    except Exception as e:
        import traceback
        app.logger.error(f"Error creating checkout session: {str(e)}")
        app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


# ==================== STRIPE WEBHOOK ====================

@app.route('/webhook', methods=['POST'])
@limiter.limit(os.getenv('RATE_LIMIT_WEBHOOK', '100 per minute'))
def stripe_webhook():
    """
    Handle Stripe webhook events
    Processes completed payments and generates labels
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        # Verify webhook signature
        event = stripe_service.verify_webhook_signature(payload, sig_header)

    except ValueError as e:
        # Invalid payload
        app.logger.error(f"Invalid webhook payload: {str(e)}")
        return jsonify({'error': 'Invalid payload'}), 400

    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        app.logger.error(f"Invalid webhook signature: {str(e)}")
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        try:
            # Extract payment metadata
            payment_data = stripe_service.handle_payment_success(session)

            isbn = payment_data['isbn']
            date = payment_data['date']
            label_type = payment_data['label_type']
            customer_type = payment_data['customer_type']
            customer_email = payment_data.get('customer_email', '')
            all_emails = payment_data.get('all_emails', customer_email)  # Fallback to single email if not set
            book_format = payment_data.get('book_format', 'both')
            carton_format = payment_data.get('carton_format', 'both')

            app.logger.info(f"Processing payment for ISBN {isbn}, type: {label_type}, customer: {customer_type}")
            app.logger.info(f"Notification emails: {all_emails}")

            # Handle direct publishers vs PBS clients
            if customer_type == 'direct':
                # Direct publishers: book data is in metadata
                book_data_json = payment_data.get('book_data', '{}')
                book_data = json.loads(book_data_json) if book_data_json else {}

                # Use submitted data
                books_per_carton = int(book_data.get('books_per_carton', 1))
                carton_weight = float(book_data.get('carton_weight', 0))

                label_data = {
                    'Title': book_data.get('title', ''),
                    'Author': book_data.get('author', ''),
                    'Publisher': book_data.get('publisher', ''),
                    'ISBN13': isbn,
                    'Price': book_data.get('price', '0'),
                    'Currency': book_data.get('currency', 'USD'),
                    'PrintedIn': book_data.get('country', 'USA'),
                    'OnSale': book_data.get('pub_date', ''),
                    'CTN_QTY': str(books_per_carton),
                    'CTN_WGT': str(int(carton_weight))
                }

            else:
                # PBS clients: lookup from Google Sheets
                book_data = sheets_service.get_combined_data(isbn, date)

                if not book_data:
                    app.logger.error(f"Book data not found for ISBN {isbn} on {date}")
                    return jsonify({'error': 'Book data not found'}), 404

                # Get books per carton and case weight from sheet data
                books_per_carton = int(book_data.get('books_per_carton', 1))
                carton_weight = float(book_data.get('carton_weight', 0))

                label_data = {
                    'Title': book_data.get('title', ''),
                    'Author': book_data.get('author', ''),
                    'Publisher': book_data.get('publisher', ''),
                    'ISBN13': isbn,
                    'Price': book_data.get('price', '0'),
                    'PrintedIn': book_data.get('country', 'USA'),
                    'OnSale': book_data.get('pub_date', ''),
                    'CTN_QTY': str(books_per_carton),
                    'CTN_WGT': str(int(carton_weight)),
                    'Currency': 'USD'
                }

            # Generate labels
            # Use /tmp for Railway (writable ephemeral storage)
            output_dir = os.getenv('LABEL_OUTPUT_DIR', '/tmp/bisg-labels')
            generated_files = label_service.generate_labels(
                data=label_data,
                label_type=label_type,
                output_dir=output_dir,
                book_format=book_format,
                carton_format=carton_format
            )

            app.logger.info(f"Generated labels: {list(generated_files.keys())}")

            # Collect file paths for email
            label_files = list(generated_files.values())

            # Send labels via email to all recipients
            # Use all_emails (comma-separated) for notifications, fallback to book_data email if needed
            recipient_emails = all_emails or book_data.get('publisher_email', '')
            email_success = email_service.send_labels_email(
                recipient_email=recipient_emails,
                label_files=label_files,
                customer_type=customer_type,
                book_title=book_data.get('title', ''),
                isbn=isbn,
                publisher=label_data.get('Publisher', ''),
                label_type=label_type
            )

            if email_success:
                app.logger.info(f"Labels sent successfully to {recipient_emails}")
            else:
                app.logger.warning(f"Failed to send labels to {recipient_emails}")

            return jsonify({'status': 'success'}), 200

        except Exception as e:
            app.logger.error(f"Error processing webhook: {str(e)}")
            return jsonify({'error': 'Processing error', 'details': str(e)}), 500

    else:
        # Other event types - acknowledge but don't process
        app.logger.info(f"Received webhook event: {event['type']}")
        return jsonify({'status': 'ignored'}), 200


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ==================== RUN APPLICATION ====================

if __name__ == '__main__':
    # Validate environment variables before starting
    validate_environment()

    # For local development
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    app.logger.info(f"🚀 Starting BISG Labels Service on port {port}")
    app.logger.info(f"   Debug mode: {debug}")
    app.logger.info(f"   Stripe mode: {'TEST' if os.getenv('STRIPE_SECRET_KEY', '').startswith('sk_test_') else 'LIVE'}")

    app.run(host='0.0.0.0', port=port, debug=debug)
