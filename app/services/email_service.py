"""
Email sender module for BISG Labels service using Gmail API.
"""

import os
import logging
import json
import base64
from typing import List
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logger = logging.getLogger(__name__)

# Email configuration
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'labels@bisglabels.com')


def get_gmail_service():
    """
    Authenticate and return Gmail API service object.

    Reads credentials from environment variables or token file.
    """
    creds = None

    # Try to load credentials from environment variable (for Railway)
    gmail_token = os.getenv('GMAIL_TOKEN')
    if gmail_token:
        try:
            # Clean up any control characters or whitespace
            gmail_token_clean = gmail_token.strip().replace('\n', '').replace('\r', '')
            creds = Credentials.from_authorized_user_info(json.loads(gmail_token_clean))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GMAIL_TOKEN JSON: {e}")
            logger.error(f"Token preview (first 100 chars): {gmail_token[:100] if gmail_token else 'empty'}")
        except Exception as e:
            logger.error(f"Failed to load credentials from GMAIL_TOKEN: {e}")

    # Fallback to token.json file (for local development)
    if not creds:
        token_file = os.path.join(os.path.dirname(__file__), 'token.json')
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file)
        else:
            logger.error("No Gmail credentials found. Set GMAIL_TOKEN env var or run generate_gmail_token.py")
            return None

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            logger.error(f"Failed to refresh Gmail token: {e}")
            return None

    if not creds or not creds.valid:
        logger.error("Invalid Gmail credentials")
        return None

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Failed to build Gmail service: {e}")
        return None


def create_message_with_attachments(sender: str, to: str, subject: str, body_html: str, files: List[str]):
    """
    Create a message with PDF attachments for Gmail API.

    Args:
        sender: Email address of sender
        to: Email address(es) of recipient(s) - can be comma-separated
        subject: Subject line
        body_html: HTML body content
        files: List of file paths to attach

    Returns:
        dict: Message ready for Gmail API
    """
    message = MIMEMultipart()
    # Handle comma-separated emails - MIME supports multiple recipients
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    # Add HTML body
    msg_body = MIMEText(body_html, 'html')
    message.attach(msg_body)

    # Attach PDF files
    for file_path in files:
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.warning(f"File not found: {file_path}")
                continue

            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'pdf')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={file_path_obj.name}'
                )
                message.attach(part)
                logger.info(f"Attached: {file_path_obj.name}")

        except Exception as e:
            logger.error(f"Failed to attach file {file_path}: {e}")

    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}


def get_email_template(customer_type: str, book_title: str, isbn: str, recipient_type: str = 'customer') -> str:
    """
    Get HTML email template based on customer type and recipient.

    Args:
        customer_type: 'pbs' or 'direct'
        book_title: Title of the book
        isbn: ISBN of the book
        recipient_type: 'customer' or 'pathway_pm' (for Sage)

    Returns:
        str: HTML email body
    """
    if recipient_type == 'pathway_pm':
        # Template for Sage at Pathway (operational/PM view)
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2563eb;">Labels Ready for Affixing</h2>
            <p>Hi Sage,</p>
            <p>Labels have been generated and are ready to print and affix to the following shipment:</p>

            <div style="background: #f0f9ff; border: 2px solid #2563eb; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; width: 120px;">Title:</td>
                        <td style="padding: 8px 0;">{book_title}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">ISBN:</td>
                        <td style="padding: 8px 0;">{isbn}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Publisher:</td>
                        <td style="padding: 8px 0;">{'{publisher}'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold;">Missing Labels:</td>
                        <td style="padding: 8px 0;">{'{label_types}'}</td>
                    </tr>
                </table>
            </div>

            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0;">
                <p style="margin: 0 0 10px 0;"><strong>📋 Attached Files:</strong></p>
                <ul style="margin: 5px 0;">
                    <li><strong>Sheet format</strong> - Book labels (30 per page)</li>
                    <li><strong>Two-up format</strong> - Carton labels (2 per page)</li>
                    <li><strong>Single labels</strong> - Reference copies</li>
                </ul>
            </div>

            <p style="margin-top: 20px;">Publisher has been notified that labels will be applied by Pathway.</p>

            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">
                BISG Labels Service - Automated Label Generation
            </p>
        </body>
        </html>
        """
    elif customer_type == 'pbs':
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2563eb;">Your BISG Labels are Ready</h2>
            <p>Hello,</p>
            <p>Thank you for your order. Your BISG-compliant labels for the following book are attached:</p>
            <ul>
                <li><strong>Title:</strong> {book_title}</li>
                <li><strong>ISBN:</strong> {isbn}</li>
            </ul>

            <div style="background: #f0f9ff; border-left: 4px solid #2563eb; padding: 15px; margin: 20px 0;">
                <p style="margin: 0 0 10px 0;"><strong>📋 What You're Receiving:</strong></p>
                <p style="margin: 0 0 5px 0;">You'll find multiple label formats attached for your convenience:</p>
                <ul style="margin: 5px 0;">
                    <li><strong>Single labels</strong> - Individual labels for reference</li>
                    <li><strong>Sheet format</strong> - Book labels (30 per page on standard Letter paper)</li>
                    <li><strong>Two-up format</strong> - Carton labels (2 per page on standard Letter paper)</li>
                </ul>
            </div>

            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0;">
                <p style="margin: 0;"><strong>✅ Labels Sent to Pathway Book Service</strong></p>
                <p style="margin: 10px 0 0 0;">These labels have been automatically sent to Pathway Book Service and will be applied to your shipment. The copies attached to this email are <strong>for your records only</strong>.</p>
                <p style="margin: 10px 0 0 0;"><em>Optional:</em> You may provide these to your printer for future orders if needed.</p>
            </div>

            <p>If you have any questions, please contact us at <a href="mailto:support@bisglabels.com">support@bisglabels.com</a>.</p>
            <p>Thank you for using BISG Labels!</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">
                BISG Labels | <a href="https://bisglabels.com">bisglabels.com</a><br>
                Professional BISG-compliant label generation service
            </p>
        </body>
        </html>
        """
    else:  # direct
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2563eb;">Your BISG Labels are Ready</h2>
            <p>Hello,</p>
            <p>Thank you for your order! Your BISG-compliant labels are attached to this email.</p>
            <p><strong>Order Details:</strong></p>
            <ul>
                <li><strong>Title:</strong> {book_title}</li>
                <li><strong>ISBN:</strong> {isbn}</li>
            </ul>

            <div style="background: #f0f9ff; border-left: 4px solid #2563eb; padding: 15px; margin: 20px 0;">
                <p style="margin: 0 0 10px 0;"><strong>📋 What You're Receiving:</strong></p>
                <p style="margin: 0 0 5px 0;">You'll find multiple label formats attached for your convenience:</p>
                <ul style="margin: 5px 0;">
                    <li><strong>Single labels</strong> - Individual labels for reference or single-use printing</li>
                    <li><strong>Sheet format</strong> - Book labels (30 per page on standard Letter paper)</li>
                    <li><strong>Two-up format</strong> - Carton labels (2 per page on standard Letter paper)</li>
                </ul>
            </div>

            <p><strong>Printing Instructions:</strong></p>
            <ul>
                <li><strong>Book labels (sheet):</strong> Print on Letter-size 2" x 1.25" label sheets (30-up)</li>
                <li><strong>Carton labels (two-up):</strong> Print on Letter-size 6" x 4" label sheets (2-up)</li>
                <li>Use a laser or inkjet printer with high quality settings</li>
                <li>Ensure barcodes are clear and scannable before applying</li>
                <li>Test print on regular paper first to verify alignment</li>
            </ul>
            <p>If you have any questions or need assistance, please contact us at <a href="mailto:support@bisglabels.com">support@bisglabels.com</a>.</p>
            <p>Thank you for using BISG Labels!</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">
                BISG Labels | <a href="https://bisglabels.com">bisglabels.com</a><br>
                Professional BISG-compliant label generation service
            </p>
        </body>
        </html>
        """


def send_labels_email(
    recipient_email: str,
    label_files: List[str],
    customer_type: str,
    book_title: str,
    isbn: str,
    publisher: str = "",
    label_type: str = "both"
) -> bool:
    """
    Send book labels via email to the recipient(s) using Gmail API.
    For PBS customers, also sends a copy to Pathway Book Service.

    Args:
        recipient_email: Email address(es) of the recipient(s) - can be comma-separated for multiple recipients
        label_files: List of PDF file paths containing the labels
        customer_type: Type of customer - 'pbs' or 'direct'
        book_title: Title of the book for the labels
        isbn: ISBN of the book
        publisher: Publisher name (for Pathway PM email)
        label_type: Type of labels - 'book', 'carton', or 'both' (for Pathway PM email)

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Validate inputs
        if not recipient_email:
            logger.error("No recipient email provided")
            return False

        if not label_files:
            logger.error("No label files to send")
            return False

        logger.info(f"Preparing to send email to: {recipient_email}")
        logger.info(f"Book: {book_title} (ISBN: {isbn})")
        logger.info(f"Customer Type: {customer_type.upper()}")
        logger.info(f"Attachments: {len(label_files)} files")

        # Get Gmail service
        service = get_gmail_service()
        if not service:
            logger.error("Failed to get Gmail service - email not sent")
            return False

        # Get email template
        body_html = get_email_template(customer_type, book_title, isbn)
        subject = f"BISG Labels for {book_title} (ISBN: {isbn})"

        # Send email to publisher
        message = create_message_with_attachments(
            sender=SENDER_EMAIL,
            to=recipient_email,
            subject=subject,
            body_html=body_html,
            files=label_files
        )

        logger.info("Sending email to publisher via Gmail API...")
        result = service.users().messages().send(userId='me', body=message).execute()
        logger.info(f"✅ Email sent to publisher! Message ID: {result.get('id')}")

        # If PBS customer, also send to Pathway Book Service (with PM-specific template)
        if customer_type == 'pbs':
            pbs_email = 'sage.friedman@pathwaybook.com'
            logger.info(f"PBS customer - also sending labels to {pbs_email}")

            # Format label types for PM email
            label_types_text = {
                'book': 'Book Labels Only',
                'carton': 'Carton Labels Only',
                'both': 'Book + Carton Labels'
            }.get(label_type, label_type.title())

            # Get PM-specific template with publisher and label type info
            pm_body_html = get_email_template(customer_type, book_title, isbn, recipient_type='pathway_pm')
            # Replace placeholders with actual data
            pm_body_html = pm_body_html.replace('{publisher}', publisher if publisher else 'N/A')
            pm_body_html = pm_body_html.replace('{label_types}', label_types_text)

            pm_subject = f"Label Order: {publisher} - {book_title} (ISBN: {isbn})"

            pbs_message = create_message_with_attachments(
                sender=SENDER_EMAIL,
                to=pbs_email,
                subject=pm_subject,
                body_html=pm_body_html,
                files=label_files
            )

            pbs_result = service.users().messages().send(userId='me', body=pbs_message).execute()
            logger.info(f"✅ Email sent to PBS! Message ID: {pbs_result.get('id')}")

        return True

    except HttpError as e:
        logger.error(f"Gmail API error: {e}")
        return False

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        logger.exception("Full traceback:")
        return False
