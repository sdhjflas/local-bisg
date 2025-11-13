# One-Page Accession Report - Implementation Guide

## Goal
Create a **ONE-PAGE PDF** with ALL Google Form fields, emailed to robert.zippoli@pathwaybook.com for every accession.

## Data Source
**Google Form Responses Sheet ID:** `1Bzdrw6lKHd_Cx-8Nt1IQykz3PSbPbbBh6tQvzd-SoDA`

## Form Fields (All on One Page)
```
Timestamp, Email Address, Date Received, Counted By, Delivered By,
Number of Cartons, Books Per Carton, Total Books, Damaged Books,
ISBN-13, Publisher, Format, Book Price, Country, Pub Date,
Missing Barcodes, Missing Carton Labels, Book Weight, Case Weight,
Book Height, Book Width, Book Depth, Carton Width, Carton Length,
Carton Height, Author, Title, Slot, Skid info, etc.
```

## Implementation

### File: `app/reports/form_pdf_generator.py`

```python
"""
One-Page Accession Report from Google Forms
Uses tiny 7pt font to fit ALL fields on one 8.5x11 page
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle

FORM_SHEET_ID = '1Bzdrw6lKHd_Cx-8Nt1IQykz3PSbPbbBh6tQvzd-SoDA'

class FormPDFGenerator:
    """Generate ultra-condensed one-page PDF from Form data."""

    def __init__(self, sheets_service, output_dir="reports"):
        self.sheets_service = sheets_service
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def get_form_data_by_isbn(self, isbn: str):
        """
        Fetch form response data by ISBN from Google Sheets.

        Args:
            isbn: ISBN to search for

        Returns:
            dict: Row data with all form fields
        """
        try:
            # Read all form responses
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=FORM_SHEET_ID,
                range='Form Responses!A:AZ'  # Adjust range as needed
            ).execute()

            values = result.get('values', [])
            if not values:
                return None

            # First row is headers
            headers = values[0]

            # Find row with matching ISBN
            for row in values[1:]:
                # Pad row if it's shorter than headers
                row_data = row + [''] * (len(headers) - len(row))

                # Find ISBN column (adjust index if needed)
                isbn_col = headers.index('Book ISBN-13') if 'Book ISBN-13' in headers else 12

                if len(row_data) > isbn_col and row_data[isbn_col].replace('-', '') == isbn.replace('-', ''):
                    # Return as dict
                    return dict(zip(headers, row_data))

            return None

        except Exception as e:
            print(f"Error fetching form data: {e}")
            return None

    def generate_one_page_pdf(self, form_data: dict) -> str:
        """
        Generate ultra-condensed one-page PDF.

        Args:
            form_data: Dict with all form fields

        Returns:
            str: Path to generated PDF
        """
        # Create filename
        isbn = form_data.get('Book ISBN-13', 'unknown').replace('-', '')
        filename = f"accession_{isbn}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        # Create PDF with minimal margins
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.4*inch,
            leftMargin=0.4*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        story = []

        # Ultra-condensed title style
        title_style = ParagraphStyle(
            name='Tiny',
            fontSize=10,
            alignment=1,  # Center
            spaceAfter=6
        )

        story.append(Paragraph("PATHWAY BOOK SERVICE - ACCESSION REPORT", title_style))
        story.append(Spacer(1, 0.1*inch))

        # Build condensed table with ALL fields (7pt font, tight spacing)
        table_data = []

        # Group fields in pairs for space efficiency
        fields = [
            ('Timestamp', form_data.get('Timestamp', '')),
            ('Date Received', form_data.get('Date Received', '')),
            ('Counted By', form_data.get('Counted By', '')),
            ('Delivered By', form_data.get('Delivered By', '')),
            ('Title', form_data.get('Book Title', '')),
            ('Author', form_data.get('Author', '')),
            ('ISBN-13', form_data.get('Book ISBN-13', '')),
            ('Publisher', form_data.get('Publisher', '')),
            ('Format', form_data.get('Format', '')),
            ('Book Price', form_data.get('Book Price', '')),
            ('Country', form_data.get('Country of Origin', '')),
            ('Pub Date', form_data.get('Pub Date - If Forthcoming', '')),
            ('# Cartons', form_data.get('Number Of Cartons', '')),
            ('Books/Carton', form_data.get('Number of Books Per Carton', '')),
            ('Total Books', form_data.get('Total Number of Books Received', '')),
            ('Damaged', form_data.get('Number of Books Received Damaged', '')),
            ('Missing Barcodes', form_data.get('Missing Barcodes?', '')),
            ('Missing Carton Labels', form_data.get('Missing Carton Labels?', '')),
            ('Book Weight', form_data.get('Book Weight', '')),
            ('Case Weight', form_data.get('Case Weight', '')),
            ('Book Height', form_data.get('Book Height', '')),
            ('Book Width', form_data.get('Book Width', '')),
            ('Book Depth', form_data.get('Book Depth', '')),
            ('Carton Width', form_data.get('Carton - Width', '')),
            ('Carton Length', form_data.get('Carton - Length', '')),
            ('Carton Height', form_data.get('Carton - Height', '')),
            ('Slot', form_data.get('Slot', '')),
            ('Skid', form_data.get('Skid', '')),
        ]

        # Create 2-column layout (field: value | field: value)
        for i in range(0, len(fields), 2):
            row = []
            # Left pair
            row.append(fields[i][0] + ':')
            row.append(fields[i][1] or 'N/A')
            # Right pair (if exists)
            if i + 1 < len(fields):
                row.append(fields[i+1][0] + ':')
                row.append(fields[i+1][1] or 'N/A')
            else:
                row.extend(['', ''])
            table_data.append(row)

        # Create table with tiny font
        table = Table(table_data, colWidths=[1.3*inch, 2.2*inch, 1.3*inch, 2.2*inch])
        table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 7),  # Tiny 7pt font
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f0f0')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ]))

        story.append(table)

        # Build PDF
        doc.build(story)

        return filepath
```

### File: `app/processors/receipt_processor.py` (Add This Method)

```python
from app.reports.form_pdf_generator import FormPDFGenerator

class ReceiptProcessor:
    def __init__(self, gmail_service, sheets_service, spreadsheet_id: str, test_mode: bool = False):
        # ... existing init code ...
        self.form_pdf_generator = FormPDFGenerator(sheets_service)  # Add this

    def process_daily_receipts(self, range_name: str) -> None:
        """Process all receipts for today."""
        try:
            receipts = self.spreadsheet_handler.get_todays_receipts(range_name)

            for receipt in receipts:
                try:
                    self.receipt = receipt

                    # GENERATE ONE-PAGE PDF FROM FORM DATA
                    form_data = self.form_pdf_generator.get_form_data_by_isbn(receipt.isbn)
                    if form_data:
                        pdf_path = self.form_pdf_generator.generate_one_page_pdf(form_data)
                        self._email_pdf_to_robert(pdf_path, receipt)

                    # Continue with normal processing...
                    if self._should_create_draft(receipt):
                        # ... draft logic
                    else:
                        self._send_email(receipt)

                except Exception as e:
                    logger.error(f"Error processing receipt: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in process_daily_receipts: {e}")
            raise

    def _email_pdf_to_robert(self, pdf_path: str, receipt) -> None:
        """Email one-page PDF to robert.zippoli@pathwaybook.com"""
        try:
            import base64
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.application import MIMEApplication

            message = MIMEMultipart()
            message['to'] = 'robert.zippoli@pathwaybook.com'
            message['from'] = self.sender
            message['subject'] = f"Accession Report - {receipt.title} ({receipt.isbn})"

            body = f"""
            <html><body>
            <h3>New Accession Report</h3>
            <p>Title: {receipt.title}<br>
            ISBN: {receipt.isbn}<br>
            Publisher: {receipt.publisher}</p>
            <p>Complete details attached as PDF.</p>
            </body></html>
            """

            message.attach(MIMEText(body, 'html'))

            # Attach PDF
            with open(pdf_path, 'rb') as f:
                pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                pdf_attachment.add_header('Content-Disposition', 'attachment',
                                         filename=os.path.basename(pdf_path))
                message.attach(pdf_attachment)

            # Send
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()

            logger.info(f"Emailed PDF to Robert: {pdf_path}")

        except Exception as e:
            logger.error(f"Failed to email PDF: {e}")
```

## Key Points

1. **7pt font** - Everything fits on one page
2. **2-column layout** - Maximizes space
3. **Fetches from Form Responses Sheet** - Has ALL fields
4. **Matches by ISBN** - Links Stock Receipt to Form Response
5. **Auto-emails to Robert** - Every accession, regardless of who it's for

## Column Mapping (Update if needed)

Adjust these indices in `get_form_data_by_isbn` based on actual column positions:
- `Book ISBN-13` column name
- Headers row = Row 1
- Data starts = Row 2

## Testing

1. Run Stock Receipts with test accession
2. Check `reports/` folder for PDF
3. Verify PDF is ONE page
4. Verify robert.zippoli@pathwaybook.com receives email with PDF
5. Open PDF - should fit on one printed page

---

**Created:** October 3, 2025
