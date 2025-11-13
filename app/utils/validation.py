"""
Input validation utilities for BISG Labels service
"""

import re
from datetime import datetime
from typing import Tuple, Optional


def validate_isbn13(isbn: str) -> Tuple[bool, Optional[str]]:
    """
    Validate ISBN-13 format and checksum.

    Args:
        isbn: ISBN string to validate

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, error_message) if invalid
    """
    # Remove hyphens and spaces
    isbn_clean = re.sub(r'[-\s]', '', isbn)

    # Check if it's all digits
    if not isbn_clean.isdigit():
        return False, "ISBN must contain only digits"

    # Check length
    if len(isbn_clean) != 13:
        return False, f"ISBN-13 must be exactly 13 digits (got {len(isbn_clean)})"

    # Validate checksum
    try:
        # Calculate checksum
        total = 0
        for i, digit in enumerate(isbn_clean[:12]):
            multiplier = 1 if i % 2 == 0 else 3
            total += int(digit) * multiplier

        checksum = (10 - (total % 10)) % 10

        if checksum != int(isbn_clean[12]):
            return False, "Invalid ISBN-13 checksum"

        return True, None

    except (ValueError, IndexError) as e:
        return False, f"Invalid ISBN format: {str(e)}"


def validate_date(date_str: str, date_format: str = "%m/%d/%Y") -> Tuple[bool, Optional[str]]:
    """
    Validate date string format.

    Args:
        date_str: Date string to validate
        date_format: Expected date format (default: MM/DD/YYYY)

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, error_message) if invalid
    """
    if not date_str or not date_str.strip():
        return False, "Date is required"

    try:
        datetime.strptime(date_str.strip(), date_format)
        return True, None
    except ValueError:
        return False, f"Invalid date format. Expected {date_format} (e.g., 10/02/2025)"


def validate_label_type(label_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate label type.

    Args:
        label_type: Label type string

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_types = ['book', 'carton', 'both']

    if not label_type or not label_type.strip():
        return False, "Label type is required"

    if label_type.lower().strip() not in valid_types:
        return False, f"Label type must be one of: {', '.join(valid_types)}"

    return True, None


def validate_customer_type(customer_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate customer type.

    Args:
        customer_type: Customer type string

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_types = ['pbs', 'direct']

    if not customer_type or not customer_type.strip():
        return False, "Customer type is required"

    if customer_type.lower().strip() not in valid_types:
        return False, f"Customer type must be one of: {', '.join(valid_types)}"

    return True, None


def validate_checkout_request(data: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate complete checkout request data.

    Args:
        data: Request data dictionary

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if all fields valid
        - (False, error_message) if validation fails
    """
    # Check required fields (date is optional now)
    required_fields = ['isbn', 'label_type', 'customer_type']
    missing = [f for f in required_fields if f not in data]

    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    # Validate ISBN or custom UPC
    is_custom_upc = data.get('is_custom_upc', False)
    if is_custom_upc:
        # Validate custom UPC (alphanumeric, 8-13 characters)
        upc = data['isbn']
        if not upc or not upc.strip():
            return False, "UPC/Barcode is required"

        upc_clean = upc.strip().upper()
        if not re.match(r'^[A-Z0-9]{8,13}$', upc_clean):
            return False, "Custom UPC/Barcode must be 8-13 alphanumeric characters (letters and numbers only)"
    else:
        # Validate standard ISBN-13
        is_valid, error = validate_isbn13(data['isbn'])
        if not is_valid:
            return False, f"ISBN validation failed: {error}"

    # Validate date only if provided (it's optional for book-only orders)
    if 'date' in data and data['date']:
        is_valid, error = validate_date(data['date'])
        if not is_valid:
            return False, f"Date validation failed: {error}"

    # Validate label type
    is_valid, error = validate_label_type(data['label_type'])
    if not is_valid:
        return False, f"Label type validation failed: {error}"

    # Validate customer type
    is_valid, error = validate_customer_type(data['customer_type'])
    if not is_valid:
        return False, f"Customer type validation failed: {error}"

    return True, None
