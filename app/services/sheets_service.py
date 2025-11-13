"""
Google Sheets integration handler for BISG Labels service.

This module provides functions to interact with Google Sheets API v4 for:
- Querying form responses for book data
- Looking up publisher email addresses
- Combining data from multiple sheets
"""

import os
import json
import pickle
import logging
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logger = logging.getLogger(__name__)


def get_sheets_service():
    """
    Authenticate with Google Sheets API and return service object.

    Supports token-based auth (GOOGLE_SHEETS_TOKEN), Service Account, or OAuth credentials.
    Prioritizes GOOGLE_SHEETS_TOKEN for Railway compatibility (same as Gmail service).

    Returns:
        googleapiclient.discovery.Resource: Authenticated Google Sheets service object

    Raises:
        ValueError: If no credentials are configured
        json.JSONDecodeError: If credentials JSON is invalid
    """
    creds = None
    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    # Try token-based auth first (same as Gmail service - works on Railway)
    sheets_token = os.getenv('GOOGLE_SHEETS_TOKEN')
    if sheets_token:
        try:
            # Clean up any control characters or whitespace
            sheets_token_clean = sheets_token.strip().replace('\n', '').replace('\r', '')
            creds = Credentials.from_authorized_user_info(json.loads(sheets_token_clean))
            logger.info("Using GOOGLE_SHEETS_TOKEN for authentication")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GOOGLE_SHEETS_TOKEN JSON: {e}")
        except Exception as e:
            logger.error(f"Failed to load credentials from GOOGLE_SHEETS_TOKEN: {e}")

    # Fallback to GOOGLE_SHEETS_CREDS if token not available
    if not creds:
        creds_json = os.getenv('GOOGLE_SHEETS_CREDS')
        if not creds_json:
            raise ValueError("Neither GOOGLE_SHEETS_TOKEN nor GOOGLE_SHEETS_CREDS environment variable is set")

        try:
            creds_dict = json.loads(creds_json)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in GOOGLE_SHEETS_CREDS: {e.msg}", e.doc, e.pos)

        # Check if it's a service account
        if creds_dict.get('type') == 'service_account':
            creds = ServiceAccountCredentials.from_service_account_info(creds_dict, scopes=scopes)
            logger.info("Using service account credentials")
        elif 'installed' in creds_dict:
            # OAuth flow - not suitable for Railway (requires browser)
            raise ValueError("OAuth 'installed' credentials not supported on Railway. Use GOOGLE_SHEETS_TOKEN instead.")
        else:
            raise ValueError("Invalid credentials format. Use GOOGLE_SHEETS_TOKEN with token JSON.")

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            logger.info("Refreshed expired token")
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")

    if not creds or not creds.valid:
        raise ValueError("Invalid Google Sheets credentials")

    service = build('sheets', 'v4', credentials=creds)
    return service


def lookup_book_data(isbn: str, date: str) -> Optional[Dict[str, Any]]:
    """
    Query Form Responses sheet for book data matching ISBN and date.

    Searches the Form Responses sheet using FORM_SHEET_ID environment variable.
    Columns: H=Cartons, I=Books/Carton, M=Title, N=ISBN, O=Publisher, Q=Price,
             R=Country, S=PubDate, T=MissingBookLabel, U=MissingCarton, X=CaseWeight, AF=Author

    Args:
        isbn: ISBN number to search for
        date: Date string to match

    Returns:
        Dict containing book data if found:
            {
                'title': str,
                'author': str,
                'isbn': str,
                'publisher': str,
                'price': str,
                'country': str,
                'pub_date': str,
                'missing_book_label': str,
                'missing_carton': str,
                'carton_qty': str,
                'books_per_carton': str
            }
        None if no matching record found

    Raises:
        ValueError: If FORM_SHEET_ID environment variable is not set
        HttpError: If API request fails
    """
    sheet_id = os.getenv('FORM_SHEET_ID')
    if not sheet_id:
        raise ValueError("FORM_SHEET_ID environment variable is not set")

    try:
        service = get_sheets_service()

        # Read all data from the form responses sheet
        # Assuming data starts from row 2 (row 1 is headers)
        # Extended to column AF (index 31) to include Author
        # Use A:AF without sheet name to read from first/active sheet
        range_name = 'A:AF'
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()

        values = result.get('values', [])

        if not values:
            return None

        # Find matching row by ISBN (column N, index 13) and date
        # Note: Date comparison might need adjustment based on actual date format
        for row in values[1:]:  # Skip header row
            if len(row) > 13:  # Ensure row has enough columns
                row_isbn = row[13].strip() if len(row) > 13 else ''

                # Match ISBN (and optionally date if date column exists)
                if row_isbn == isbn.strip():
                    return {
                        'title': row[12].strip() if len(row) > 12 else '',
                        'author': row[31].strip() if len(row) > 31 else '',  # Column AF (index 31)
                        'isbn': row[13].strip() if len(row) > 13 else '',
                        'publisher': row[14].strip() if len(row) > 14 else '',
                        'price': row[16].strip() if len(row) > 16 else '0.00',  # Column Q (index 16)
                        'country': row[17].strip() if len(row) > 17 else 'USA',  # Column R (index 17)
                        'pub_date': row[18].strip() if len(row) > 18 else '',  # Column S (index 18)
                        'missing_book_label': row[19].strip() if len(row) > 19 else '',  # Column T (index 19)
                        'missing_carton': row[20].strip() if len(row) > 20 else '',  # Column U (index 20)
                        'carton_weight': row[23].strip() if len(row) > 23 else '0',  # Column X (index 23) - Case Weight
                        'carton_qty': row[7].strip() if len(row) > 7 else '10',  # Column H (index 7)
                        'books_per_carton': row[8].strip() if len(row) > 8 else '1'  # Column I (index 8)
                    }

        return None

    except HttpError as error:
        logger.error(f"An error occurred while querying book data: {error}")
        raise


def lookup_publisher_email(isbn: str, date: str) -> Optional[str]:
    """
    Query Stock Receipts sheet for publisher email matching ISBN and date.

    Searches the Stock Receipts sheet using STOCK_SHEET_ID environment variable.
    Columns: A=Date, F=ISBN, H=PubEmail

    Args:
        isbn: ISBN number to search for
        date: Date string to match

    Returns:
        str: Publisher email if found
        None: If no matching record found

    Raises:
        ValueError: If STOCK_SHEET_ID environment variable is not set
        HttpError: If API request fails
    """
    sheet_id = os.getenv('STOCK_SHEET_ID')
    if not sheet_id:
        raise ValueError("STOCK_SHEET_ID environment variable is not set")

    try:
        service = get_sheets_service()

        # Read relevant columns from the stock receipts sheet (A-Q for all data)
        # Use A:Q without sheet name to read from first/active sheet
        range_name = 'A:Q'
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()

        values = result.get('values', [])

        if not values:
            return None

        # Find matching row by ISBN (column F, index 5) and date (column A, index 0)
        for row in values[1:]:  # Skip header row
            if len(row) > 5:  # Ensure row has enough columns
                row_date = row[0].strip() if len(row) > 0 else ''
                row_isbn = row[5].strip() if len(row) > 5 else ''

                # Match both ISBN and date
                if row_isbn == isbn.strip() and row_date == date.strip():
                    # Return email as string for backward compatibility
                    return row[7].strip() if len(row) > 7 else None

        return None

    except HttpError as error:
        logger.error(f"An error occurred while querying publisher email: {error}")
        raise


def get_combined_data(isbn: str, date: str) -> Optional[Dict[str, Any]]:
    """
    Combine data from both Form Responses and Stock Receipts sheets.

    Queries both sheets and returns a combined dictionary with all fields.

    Args:
        isbn: ISBN number to search for
        date: Date string to match

    Returns:
        Dict containing combined data if found:
            {
                'title': str,
                'isbn': str,
                'publisher': str,
                'country': str,
                'pub_date': str,
                'missing_book_label': str,
                'missing_carton': str,
                'publisher_email': str or None
            }
        None if no matching book data found

    Raises:
        ValueError: If required environment variables are not set
        HttpError: If API requests fail
    """
    try:
        # Get book data from form responses
        book_data = lookup_book_data(isbn, date)

        if not book_data:
            return None

        # Get publisher email from stock receipts
        publisher_email = lookup_publisher_email(isbn, date)

        # Combine data
        combined_data = book_data.copy()
        combined_data['publisher_email'] = publisher_email

        return combined_data

    except (ValueError, HttpError) as error:
        logger.error(f"An error occurred while getting combined data: {error}")
        raise
