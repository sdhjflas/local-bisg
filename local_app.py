"""
BISG Labels - Local Label Generator (No External Dependencies)
Simple Flask app for generating labels locally without Stripe/Sheets/Gmail
"""

import os
from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import tempfile

# Import label generation service
from app.services import label_service

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'local-dev-secret-key'

# Enable CORS for local development
CORS(app, resources={r"/*": {"origins": "*"}})

# Output directory for generated labels
OUTPUT_DIR = os.path.join(tempfile.gettempdir(), 'bisg-labels-local')
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Serve the simple HTML form
@app.route('/', methods=['GET'])
def serve_form():
    """Serve the simple label generation form"""
    html_path = os.path.join(os.path.dirname(__file__), 'simple_form.html')
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return jsonify({'error': 'Form not found'}), 404


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'BISG Labels (Local)',
        'version': '1.0.0-local'
    }), 200


@app.route('/generate-labels', methods=['POST'])
def generate_labels_endpoint():
    """
    Generate labels directly from form data (no payment required)

    Expected JSON body:
    {
        "title": "Book Title",
        "author": "Author Name",
        "publisher": "Publisher Name",
        "isbn": "9780985347024",
        "price": "24.99",
        "currency": "USD",
        "country": "USA",
        "pub_date": "01/15/2025",
        "carton_qty": "10",
        "carton_weight": "25.5",
        "label_type": "both",  // 'book', 'carton', or 'both'
        "book_format": "both",  // 'single', 'sheet', or 'both'
        "carton_format": "both",  // 'single', 'twoup', or 'both'
        "is_custom_upc": false
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['isbn', 'label_type']
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing_fields
            }), 400

        # Extract data
        label_type = data.get('label_type', 'both')
        book_format = data.get('book_format', 'both')
        carton_format = data.get('carton_format', 'both')

        # Prepare label data
        label_data = {
            'Title': data.get('title', ''),
            'Author': data.get('author', ''),
            'Publisher': data.get('publisher', ''),
            'ISBN13': data.get('isbn', ''),
            'Price': data.get('price', '0'),
            'Currency': data.get('currency', 'USD'),
            'PrintedIn': data.get('country', 'USA'),
            'OnSale': data.get('pub_date', ''),
            'CTN_QTY': data.get('carton_qty', '10'),
            'CTN_WGT': data.get('carton_weight', '0'),
            'is_custom_upc': data.get('is_custom_upc', False)
        }

        # Generate labels
        generated_files = label_service.generate_labels(
            data=label_data,
            label_type=label_type,
            output_dir=OUTPUT_DIR,
            book_format=book_format,
            carton_format=carton_format
        )

        # Return list of generated files with download links
        result = {
            'success': True,
            'message': 'Labels generated successfully',
            'files': {}
        }

        for label_name, file_path in generated_files.items():
            result['files'][label_name] = {
                'filename': os.path.basename(file_path),
                'download_url': f'/download/{os.path.basename(file_path)}'
            }

        return jsonify(result), 200

    except Exception as e:
        import traceback
        print(f"Error generating labels: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            'error': 'Failed to generate labels',
            'details': str(e)
        }), 500


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download generated label file"""
    try:
        file_path = os.path.join(OUTPUT_DIR, filename)

        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("=" * 60)
    print("🏷️  BISG Labels - Local Label Generator")
    print("=" * 60)
    print(f"✅ Server running at: http://localhost:{port}")
    print(f"📁 Labels will be saved to: {OUTPUT_DIR}")
    print("=" * 60)
    print("\n🎯 Open your browser and go to:")
    print(f"   http://localhost:{port}\n")

    app.run(host='0.0.0.0', port=port, debug=True)
