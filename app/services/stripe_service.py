"""
Stripe payment integration handler for BISG Labels service.

This module provides functionality for creating checkout sessions,
verifying webhook signatures, and handling payment success events.
"""

import os
import stripe
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Stripe with secret key from environment
# Strip whitespace to prevent issues from copy/paste errors in Railway
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '').strip()
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '').strip()

# Stripe 6.x doesn't have lazy-loading issues

# Validate Stripe configuration
if not stripe.api_key:
    raise ValueError("STRIPE_SECRET_KEY environment variable is not set")
if not STRIPE_WEBHOOK_SECRET:
    raise ValueError("STRIPE_WEBHOOK_SECRET environment variable is not set")

# Pricing configuration
PRICING = {
    'book': 5000,      # $50.00 in cents
    'carton': 5000,    # $50.00 in cents
    'both': 10000      # $100.00 in cents
}

# Label type descriptions
LABEL_DESCRIPTIONS = {
    'book': 'BISG Book Label',
    'carton': 'BISG Carton Label',
    'both': 'BISG Book and Carton Labels'
}


def create_checkout_session(
    isbn: str,
    date: str,
    label_type: str,
    customer_type: str,
    book_title: str,
    publisher_email: str,
    success_url: str = None,
    cancel_url: str = None,
    book_data: str = None,
    book_format: str = "both",
    carton_format: str = "both"
) -> str:
    """
    Create a Stripe checkout session for BISG label purchase.

    Args:
        isbn: The ISBN of the book
        date: The publication date
        label_type: Type of label ('book', 'carton', or 'both')
        customer_type: Customer type classification
        book_title: Title of the book
        publisher_email: Email address of the publisher
        success_url: URL to redirect after successful payment (optional)
        cancel_url: URL to redirect if payment is cancelled (optional)
        book_data: JSON string of book data for direct publishers (optional)
        book_format: Format for book labels - 'single', 'sheet', or 'both' (default: 'both')
        carton_format: Format for carton labels - 'single', 'twoup', or 'both' (default: 'both')

    Returns:
        str: The checkout session URL

    Raises:
        ValueError: If label_type is invalid or required parameters are missing
        stripe.error.StripeError: If Stripe API call fails
    """
    # Validate label type
    if label_type not in PRICING:
        raise ValueError(
            f"Invalid label_type '{label_type}'. Must be one of: {list(PRICING.keys())}"
        )

    # Validate required parameters (date is optional for book-only orders)
    if not all([isbn, label_type, customer_type, book_title, publisher_email]):
        raise ValueError("Required parameters missing: isbn, label_type, customer_type, book_title, publisher_email")

    # Set default URLs if not provided
    if success_url is None:
        # Include customer_type in success URL for customized messaging
        success_url = f"https://app.bisglabels.com/success?session_id={{CHECKOUT_SESSION_ID}}&type={customer_type}"
    if cancel_url is None:
        cancel_url = "https://app.bisglabels.com/"

    try:
        # Create custom line item description
        line_item_description = f"{book_title} (ISBN: {isbn})"

        # Handle multiple comma-separated emails - Stripe only accepts one email
        # Take the first email as the primary contact
        primary_email = publisher_email.split(',')[0].strip() if ',' in publisher_email else publisher_email

        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': LABEL_DESCRIPTIONS[label_type],
                        'description': line_item_description,
                    },
                    'unit_amount': PRICING[label_type],
                },
                'quantity': 1,
            }],
            mode='payment',
            allow_promotion_codes=True,  # Enable coupon/promo code field
            customer_creation='always',  # Always create customer record, even for $0 orders
            customer_email=primary_email,
            metadata={
                'isbn': isbn,
                'date': date,
                'label_type': label_type,
                'customer_type': customer_type,
                'book_title': book_title,
                'book_data': book_data if book_data else '',  # For direct publishers
                'book_format': book_format,  # 'single' or 'sheet'
                'carton_format': carton_format,  # 'single' or 'twoup'
                'all_emails': publisher_email  # Store all emails for notifications
            },
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return session.url

    except stripe.error.StripeError as e:
        # Re-raise Stripe errors for caller to handle
        raise


def verify_webhook_signature(payload: bytes, sig_header: str) -> stripe.Event:
    """
    Verify the Stripe webhook signature and construct the event.

    Args:
        payload: The raw request body from Stripe webhook
        sig_header: The Stripe-Signature header value

    Returns:
        stripe.Event: The verified event object

    Raises:
        ValueError: If webhook secret is not configured
        stripe.error.SignatureVerificationError: If signature verification fails
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise ValueError("STRIPE_WEBHOOK_SECRET environment variable is not set")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        return event

    except stripe.error.SignatureVerificationError as e:
        # Re-raise signature verification errors for caller to handle
        raise


def handle_payment_success(session: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract metadata from a completed payment session.

    Args:
        session: The Stripe checkout session object (dict)

    Returns:
        dict: Dictionary containing:
            - isbn: The book ISBN
            - date: The publication date
            - label_type: Type of label purchased
            - customer_type: Customer type classification
            - book_title: Title of the book
            - customer_email: Customer's email address (first email only)
            - all_emails: All comma-separated emails for notifications
            - session_id: Stripe session ID
            - amount_total: Total amount paid in cents

    Raises:
        KeyError: If required metadata is missing from session
    """
    try:
        metadata = session.get('metadata', {})

        # Extract required metadata
        result = {
            'isbn': metadata['isbn'],
            'date': metadata['date'],
            'label_type': metadata['label_type'],
            'customer_type': metadata['customer_type'],
            'book_title': metadata.get('book_title', ''),
            'customer_email': session.get('customer_email', session.get('customer_details', {}).get('email', '')),
            'all_emails': metadata.get('all_emails', ''),  # All emails for notifications
            'session_id': session.get('id', ''),
            'amount_total': session.get('amount_total', 0),
            'book_data': metadata.get('book_data', ''),  # For direct publishers
            'book_format': metadata.get('book_format', 'both'),  # Default to both (single + sheet)
            'carton_format': metadata.get('carton_format', 'both')  # Default to both (single + twoup)
        }

        return result

    except KeyError as e:
        raise KeyError(f"Missing required metadata in session: {e}")


def get_session(session_id: str) -> Dict[str, Any]:
    """
    Retrieve a checkout session by ID.

    Args:
        session_id: The Stripe checkout session ID

    Returns:
        dict: The session object

    Raises:
        stripe.error.StripeError: If session retrieval fails
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session

    except stripe.error.StripeError as e:
        raise


def format_amount(amount_cents: int) -> str:
    """
    Format an amount in cents to a dollar string.

    Args:
        amount_cents: Amount in cents

    Returns:
        str: Formatted amount (e.g., "$50.00")
    """
    dollars = amount_cents / 100
    return f"${dollars:.2f}"
