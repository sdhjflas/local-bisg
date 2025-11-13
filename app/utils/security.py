"""
Security utilities and middleware for BISG Labels service
"""

import os
import re
import bleach
from functools import wraps
from flask import request, jsonify


def sanitize_string(text, max_length=500):
    """
    Sanitize user input to prevent injection attacks

    Args:
        text: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        str: Sanitized string
    """
    if not text:
        return ""

    # Convert to string if not already
    text = str(text)

    # Truncate to max length
    text = text[:max_length]

    # Remove HTML tags and dangerous characters
    text = bleach.clean(text, tags=[], strip=True)

    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    return text.strip()


def sanitize_email(email):
    """
    Validate and sanitize email address

    Args:
        email: Email address to validate

    Returns:
        str: Sanitized email or empty string if invalid
    """
    if not email:
        return ""

    email = str(email).strip().lower()

    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if re.match(email_pattern, email) and len(email) <= 254:
        return email

    return ""


def sanitize_isbn(isbn):
    """
    Sanitize and validate ISBN-13

    Args:
        isbn: ISBN string

    Returns:
        str: Sanitized ISBN (digits only) or empty string if invalid
    """
    if not isbn:
        return ""

    # Remove all non-digits
    isbn = re.sub(r'\D', '', str(isbn))

    # Must be exactly 13 digits
    if len(isbn) == 13:
        return isbn

    return ""


def sanitize_price(price):
    """
    Sanitize and validate price

    Args:
        price: Price value (string or number)

    Returns:
        str: Sanitized price or "0" if invalid
    """
    if not price:
        return "0"

    try:
        # Convert to float
        price_float = float(price)

        # Validate range (0.01 to 9999.99)
        if 0 <= price_float <= 9999.99:
            # Return with 2 decimal places
            return f"{price_float:.2f}"
    except (ValueError, TypeError):
        pass

    return "0"


def validate_request_data(data, required_fields):
    """
    Validate that all required fields are present in request data

    Args:
        data: Request data dictionary
        required_fields: List of required field names

    Returns:
        tuple: (is_valid, error_message)
    """
    if not data:
        return False, "Request body is required"

    missing = [field for field in required_fields if field not in data or not data[field]]

    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    return True, None


def check_honeypot(data):
    """
    Check honeypot field to detect bots

    Args:
        data: Request data dictionary

    Returns:
        bool: True if request appears legitimate, False if likely bot
    """
    # If honeypot field exists and is filled, it's a bot
    honeypot_fields = ['website', 'url', 'homepage']

    for field in honeypot_fields:
        if field in data and data[field]:
            return False

    return True


def rate_limit_key():
    """
    Generate rate limit key based on IP address or API key

    Returns:
        str: Rate limit identifier
    """
    # Use IP address as default identifier
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    # If multiple IPs in X-Forwarded-For, use the first one
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    return f"ip:{ip}"


def require_json(f):
    """
    Decorator to ensure request contains JSON data

    Usage:
        @app.route('/api/endpoint', methods=['POST'])
        @require_json
        def endpoint():
            data = request.get_json()
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type must be application/json'
            }), 400
        return f(*args, **kwargs)
    return decorated_function


def sanitize_checkout_data(data):
    """
    Sanitize all fields in checkout request

    Args:
        data: Request data dictionary

    Returns:
        dict: Sanitized data
    """
    sanitized = {}

    # Check if custom UPC first (before sanitizing ISBN)
    is_custom_upc = bool(data.get('is_custom_upc', False))

    # Required fields
    # Sanitize ISBN differently based on custom UPC flag
    if is_custom_upc:
        # For custom UPC, keep alphanumeric characters (A-Z, 0-9)
        isbn_raw = str(data.get('isbn', '')).strip().upper()
        sanitized['isbn'] = re.sub(r'[^A-Z0-9]', '', isbn_raw)[:13]  # Max 13 chars
    else:
        # For ISBN, use standard sanitization (digits only)
        sanitized['isbn'] = sanitize_isbn(data.get('isbn', ''))

    sanitized['label_type'] = sanitize_string(data.get('label_type', ''), max_length=20)
    sanitized['customer_type'] = sanitize_string(data.get('customer_type', ''), max_length=20)
    sanitized['date'] = sanitize_string(data.get('date', ''), max_length=20)

    # Optional fields for direct customers
    if 'title' in data:
        sanitized['title'] = sanitize_string(data.get('title', ''), max_length=500)
    if 'author' in data:
        sanitized['author'] = sanitize_string(data.get('author', ''), max_length=200)
    if 'publisher' in data:
        sanitized['publisher'] = sanitize_string(data.get('publisher', ''), max_length=200)
    if 'price' in data:
        sanitized['price'] = sanitize_price(data.get('price', '0'))
    if 'email' in data:
        sanitized['email'] = sanitize_email(data.get('email', ''))
    if 'country' in data:
        sanitized['country'] = sanitize_string(data.get('country', ''), max_length=100)
    if 'pub_date' in data:
        sanitized['pub_date'] = sanitize_string(data.get('pub_date', ''), max_length=20)
    if 'carton_qty' in data:
        try:
            qty = int(data.get('carton_qty', 1))
            sanitized['carton_qty'] = str(max(1, min(qty, 10000)))  # Limit to reasonable range
        except (ValueError, TypeError):
            sanitized['carton_qty'] = '1'
    if 'books_per_carton' in data:
        try:
            books = int(data.get('books_per_carton', 1))
            sanitized['books_per_carton'] = str(max(1, min(books, 1000)))
        except (ValueError, TypeError):
            sanitized['books_per_carton'] = '1'
    if 'carton_weight' in data:
        sanitized['carton_weight'] = sanitize_price(data.get('carton_weight', '0'))
    if 'currency' in data:
        sanitized['currency'] = sanitize_string(data.get('currency', 'USD'), max_length=3).upper()
    if 'book_format' in data:
        sanitized['book_format'] = sanitize_string(data.get('book_format', 'both'), max_length=20)
    if 'carton_format' in data:
        sanitized['carton_format'] = sanitize_string(data.get('carton_format', 'both'), max_length=20)
    if 'is_custom_upc' in data:
        # Convert to boolean
        sanitized['is_custom_upc'] = bool(data.get('is_custom_upc', False))

    return sanitized


def get_client_ip():
    """
    Get client IP address from request headers

    Returns:
        str: Client IP address
    """
    # Check for forwarded IP (behind proxy/load balancer)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Get first IP in chain
        return forwarded_for.split(',')[0].strip()

    # Check other common headers
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip

    # Fallback to remote_addr
    return request.remote_addr or 'unknown'
