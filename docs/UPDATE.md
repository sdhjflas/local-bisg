# BISG Labels & Stock Receipts - Update Instructions

## Overview
This document contains instructions for two major updates to the Pathway Book Service systems:
1. **PBS Integration** - Add Stripe payment links to Stock Receipts emails for missing labels
2. **Digital Accession Reports** - Generate and email PDF reports for all accessions to management

---

## Part 1: PBS Integration with BISG Labels Service

### Current State
The BISG Labels service at `https://app.bisglabels.com` is **100% complete**:
- ✅ Stripe checkout & payment processing
- ✅ BISG-compliant label PDF generation (book & carton)
- ✅ Automated email delivery with attachments
- ✅ Public frontend for direct publishers

**What's Missing:** Stock Receipts program doesn't include payment links in emails.

### What Needs to Be Done

**Location:** `C:\Users\lucam\OneDrive\Documents\Desktop\EMS - Work\BISGLabels.com\Context\Stock-Receipts\`

#### Step 1: Add BISG Labels API Integration

**File:** `app/processors/receipt_processor.py`

Add this method to the `ReceiptProcessor` class (around line 95, after `_should_create_draft`):

```python
def _generate_stripe_link(self, receipt: StockReceipt) -> str:
    """
    Generate Stripe checkout link for missing labels via BISG Labels API.

    Args:
        receipt: StockReceipt object with missing label flags

    Returns:
        str: Stripe checkout URL, or None if no labels needed
    """
    import requests

    # Determine label type based on missing flags
    missing_book = receipt.missing_book_label.lower() in ['yes', 'y']
    missing_carton = receipt.missing_carton_label.lower() in ['yes', 'y']

    if not (missing_book or missing_carton):
        return None

    if missing_book and missing_carton:
        label_type = 'both'
    elif missing_book:
        label_type = 'book'
    elif missing_carton:
        label_type = 'carton'
    else:
        return None

    # Call BISG Labels API
    try:
        response = requests.post(
            'https://app.bisglabels.com/create-checkout',
            json={
                'isbn': receipt.isbn,
                'date': receipt.date,
                'label_type': label_type,
                'customer_type': 'pbs'
            },
            timeout=10
        )

        if response.status_code == 200:
            checkout_url = response.json().get('checkout_url')
            logger.info(f"Generated Stripe link for {receipt.isbn}: {checkout_url}")
            return checkout_url
        else:
            logger.error(f"Failed to generate Stripe link: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error calling BISG Labels API: {e}")
        return None
```

#### Step 2: Update Email Sending Logic

**File:** `app/processors/receipt_processor.py`

Find the `_send_email` method (around line 104) and modify it to generate and include Stripe link:

```python
def _send_email(self, receipt: StockReceipt) -> None:
    """Send email notification for a receipt."""
    try:
        # Generate Stripe checkout link if labels are missing
        stripe_link = self._generate_stripe_link(receipt)

        # Build email body with label message
        label_message = self.template_manager.get_label_message(
            receipt.missing_book_label,
            receipt.missing_carton_label
        )

        email_body = self.template_manager.build_email_body(
            receipt=receipt,
            label_message=label_message,
            stripe_link=stripe_link  # Pass the link to template
        )

        # ... rest of existing code
```

#### Step 3: Update Template Manager

**File:** `app/processors/template_manager.py`

Update the `build_email_body` method to accept and use `stripe_link`:

```python
def build_email_body(self, receipt, label_message: str, stripe_link: str = None) -> str:
    """Build the complete email body."""

    # Load base template
    base_template = self.load_template('base_email')

    # Replace placeholders
    email_body = base_template.replace('{LABEL_MESSAGE}', label_message)

    # Add Stripe payment link if available
    if stripe_link:
        payment_section = f"""
        <div style="background: #f0f9ff; border-left: 4px solid #2563eb; padding: 20px; margin: 30px 0;">
            <h3 style="color: #1e40af; margin-top: 0;">Option 3: Order Labels Online (Instant Delivery)</h3>
            <p>You can now order BISG-compliant labels directly and receive them via email within minutes:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{stripe_link}" style="display: inline-block; padding: 15px 40px; background: #2563eb; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                    Pay Online &amp; Get Labels Instantly
                </a>
            </p>
            <p style="font-size: 14px; color: #64748b;">
                <strong>Pricing:</strong> Book Label: $50 | Carton Label: $50 | Both Labels: $100<br>
                Payment processed securely via Stripe. Labels emailed immediately after payment.
            </p>
        </div>
        """
        # Insert before the closing section
        email_body = email_body.replace(
            '</body>',
            f'{payment_section}</body>'
        )

    # ... rest of existing replacement logic

    return email_body
```

#### Step 4: Add Requests Dependency

**File:** `requirements.txt`

Add this line:
```
requests>=2.31.0
```

Then reinstall:
```bash
pip install -r requirements.txt
```

#### Step 5: Test the Integration

**Test Data:**
- ISBN: 9781234567890
- Date: 01/15/2025
- Missing Book Label: Yes
- Missing Carton Label: Yes
- Publisher Email: test@example.com

**Expected Result:**
- Email includes "Pay Online & Get Labels Instantly" button
- Button links to Stripe checkout
- Checkout pre-filled with publisher email
- Payment triggers label generation and delivery

---

## Part 2: Digital Accession Reports

### Requirements
Generate a **ONE-PAGE** printable PDF report for **all accessions** (internal stock receipts) and email to management, regardless of who the accession is for.

### Specifications
- **Format:** PDF, **MUST fit on ONE page** (8.5" x 11")
- **Data Source:** Google Form responses (has ALL fields)
- **Recipient:** robert.zippoli@pathwaybook.com
- **Trigger:** When accession stock receipt runs (any accession)
- **Content:** ALL form fields condensed (small font OK per Robert)
- **Note:** Google Forms built-in print = 6-7 pages ❌. We need custom 1-page PDF ✅

### Implementation Instructions

**Location:** `C:\Users\lucam\OneDrive\Documents\Desktop\EMS - Work\BISGLabels.com\Context\Stock-Receipts\`

**Google Form Responses Sheet ID:** `1Bzdrw6lKHd_Cx-8Nt1IQykz3PSbPbbBh6tQvzd-SoDA`

#### Step 1: Create PDF Report Generator (One-Page Condensed)

**New File:** `app/reports/accession_report.py`

```python
"""
Ultra-Condensed One-Page Accession Report Generator
Fetches data from Google Form Responses Sheet and creates single-page PDF
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

class AccessionReportGenerator:
    """Generates PDF reports for accessions."""

    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator.

        Args:
            output_dir: Directory to save generated reports
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Set up custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='AccessionTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='AccessionSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=10,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=10,
            spaceBefore=15
        ))

    def generate_report(self, receipt: StockReceipt) -> str:
        """
        Generate PDF report for a single accession.

        Args:
            receipt: StockReceipt object to generate report for

        Returns:
            str: Path to generated PDF file
        """
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"accession_{receipt.isbn}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )

        # Build content
        story = []

        # Header
        story.append(Paragraph("PATHWAY BOOK SERVICE", self.styles['AccessionTitle']))
        story.append(Paragraph("Stock Receipt / Accession Report", self.styles['AccessionSubtitle']))
        story.append(Spacer(1, 0.3*inch))

        # Receipt Information Section
        story.append(Paragraph("Receipt Information", self.styles['SectionHeader']))

        receipt_data = [
            ['Date:', receipt.date or 'N/A', 'Time:', receipt.time or 'N/A'],
            ['Carrier:', receipt.carrier or 'N/A', 'Received By:', receipt.who or 'N/A'],
            ['Publisher:', receipt.publisher or 'N/A', 'Publisher Email:', receipt.publisher_email or 'N/A'],
        ]

        receipt_table = Table(receipt_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2*inch])
        receipt_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0'))
        ]))

        story.append(receipt_table)
        story.append(Spacer(1, 0.3*inch))

        # Book Details Section
        story.append(Paragraph("Book Details", self.styles['SectionHeader']))

        book_data = [
            ['Title:', receipt.title or 'N/A'],
            ['ISBN-13:', receipt.isbn or 'N/A'],
            ['Publication Date:', receipt.pub_date or 'N/A'],
            ['Country of Origin:', receipt.country or 'N/A'],
        ]

        book_table = Table(book_data, colWidths=[2*inch, 5.5*inch])
        book_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0'))
        ]))

        story.append(book_table)
        story.append(Spacer(1, 0.3*inch))

        # Quantity Information Section
        story.append(Paragraph("Quantity & Condition", self.styles['SectionHeader']))

        qty_data = [
            ['Number of Cartons:', receipt.carton_qty or 'N/A', 'Full Case Qty:', receipt.full_case_qty or 'N/A'],
            ['Accession Qty:', receipt.acc_qty or 'N/A', 'Damaged:', receipt.damaged_qty or '0'],
            ['Net Qty:', receipt.net_qty or 'N/A', '', ''],
        ]

        qty_table = Table(qty_data, colWidths=[2*inch, 2.5*inch, 1.5*inch, 1.5*inch])
        qty_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0'))
        ]))

        story.append(qty_table)
        story.append(Spacer(1, 0.3*inch))

        # Label Status Section
        story.append(Paragraph("Label Status", self.styles['SectionHeader']))

        missing_book = receipt.missing_book_label or 'No'
        missing_carton = receipt.missing_carton_label or 'No'

        # Color code based on status
        book_color = colors.HexColor('#dc2626') if missing_book.lower() in ['yes', 'y'] else colors.HexColor('#16a34a')
        carton_color = colors.HexColor('#dc2626') if missing_carton.lower() in ['yes', 'y'] else colors.HexColor('#16a34a')

        label_data = [
            ['Missing Book Label:', missing_book],
            ['Missing Carton Label:', missing_carton],
        ]

        label_table = Table(label_data, colWidths=[3*inch, 4.5*inch])
        label_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (1, 0), (1, 0), book_color),
            ('TEXTCOLOR', (1, 1), (1, 1), carton_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0'))
        ]))

        story.append(label_table)
        story.append(Spacer(1, 0.5*inch))

        # Footer
        footer_style = ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#94a3b8'),
            alignment=TA_CENTER
        )

        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            footer_style
        ))

        # Build PDF
        doc.build(story)

        return filepath

    def generate_daily_summary(self, receipts: List[StockReceipt]) -> str:
        """
        Generate summary report for multiple receipts.

        Args:
            receipts: List of StockReceipt objects

        Returns:
            str: Path to generated PDF file
        """
        # Create filename with date
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"daily_accessions_{date_str}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )

        story = []

        # Header
        story.append(Paragraph("PATHWAY BOOK SERVICE", self.styles['AccessionTitle']))
        story.append(Paragraph(
            f"Daily Accessions Summary - {datetime.now().strftime('%B %d, %Y')}",
            self.styles['AccessionSubtitle']
        ))
        story.append(Spacer(1, 0.3*inch))

        # Summary table
        summary_data = [['Time', 'Title', 'ISBN', 'Publisher', 'Qty', 'Missing Labels']]

        for receipt in receipts:
            labels = []
            if receipt.missing_book_label and receipt.missing_book_label.lower() in ['yes', 'y']:
                labels.append('Book')
            if receipt.missing_carton_label and receipt.missing_carton_label.lower() in ['yes', 'y']:
                labels.append('Carton')
            label_status = ', '.join(labels) if labels else 'None'

            summary_data.append([
                receipt.time or 'N/A',
                (receipt.title or 'N/A')[:40] + '...' if len(receipt.title or '') > 40 else (receipt.title or 'N/A'),
                receipt.isbn or 'N/A',
                (receipt.publisher or 'N/A')[:20] + '...' if len(receipt.publisher or '') > 20 else (receipt.publisher or 'N/A'),
                receipt.net_qty or 'N/A',
                label_status
            ])

        summary_table = Table(summary_data, colWidths=[0.7*inch, 2.2*inch, 1.3*inch, 1.5*inch, 0.6*inch, 1.2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
        ]))

        story.append(summary_table)

        # Build PDF
        doc.build(story)

        return filepath
```

#### Step 2: Update Receipt Processor to Generate Reports

**File:** `app/processors/receipt_processor.py`

Add report generation after processing each receipt:

```python
from app.reports.accession_report import AccessionReportGenerator

class ReceiptProcessor:
    def __init__(self, gmail_service, sheets_service, spreadsheet_id: str, test_mode: bool = False):
        self.gmail_service = gmail_service
        self.spreadsheet_handler = SpreadsheetHandler(sheets_service, spreadsheet_id)
        self.template_manager = TemplateManager()
        self.report_generator = AccessionReportGenerator()  # Add this
        self.test_mode = test_mode
        self.load_config()
```

Then add report generation and emailing in `process_daily_receipts`:

```python
def process_daily_receipts(self, range_name: str) -> None:
    """Process all receipts for today."""
    try:
        receipts = self.spreadsheet_handler.get_todays_receipts(range_name)

        if not receipts:
            logger.info("No new receipts to process for today")
            return

        draft_details = []

        # Process each receipt
        for receipt in receipts:
            try:
                self.receipt = receipt

                # Generate PDF report for this accession
                report_path = self.report_generator.generate_report(receipt)
                logger.info(f"Generated report: {report_path}")

                # Email report to management
                self._email_report_to_management(receipt, report_path)

                # Continue with normal processing
                if self._should_create_draft(receipt):
                    draft = self._create_draft(receipt)
                    draft_details.append(draft)
                    self.spreadsheet_handler.write_log_entry(
                        receipt=receipt,
                        status="Draft Due to Damage",
                        message="Draft created for damaged items"
                    )
                else:
                    self._send_email(receipt)
                    self.spreadsheet_handler.write_log_entry(
                        receipt=receipt,
                        status="Sent",
                        message="Email sent successfully"
                    )

            except Exception as e:
                logger.error(f"Error processing receipt {receipt.title}: {e}")
                self.spreadsheet_handler.write_log_entry(
                    receipt=receipt,
                    status="Failed",
                    message=str(e)
                )
                continue

        if draft_details:
            self._send_summary_email(draft_details)

    except Exception as e:
        logger.error(f"Error in process_daily_receipts: {e}")
        raise
```

#### Step 3: Add Email Report Method

**File:** `app/processors/receipt_processor.py`

Add this new method:

```python
def _email_report_to_management(self, receipt: StockReceipt, report_path: str) -> None:
    """
    Email accession report PDF to management.

    Args:
        receipt: StockReceipt object
        report_path: Path to generated PDF report
    """
    try:
        management_email = 'robert.zippoli@pathwaybook.com'

        # Create message
        message = MIMEMultipart()
        message['to'] = management_email
        message['from'] = self.sender
        message['subject'] = f"Accession Report - {receipt.title} ({receipt.isbn})"

        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Accession Report</h2>
            <p>A new accession has been processed:</p>
            <ul>
                <li><strong>Title:</strong> {receipt.title}</li>
                <li><strong>ISBN:</strong> {receipt.isbn}</li>
                <li><strong>Publisher:</strong> {receipt.publisher}</li>
                <li><strong>Date:</strong> {receipt.date}</li>
                <li><strong>Net Quantity:</strong> {receipt.net_qty}</li>
            </ul>
            <p>Please see the attached PDF for complete details.</p>
        </body>
        </html>
        """

        message.attach(MIMEText(body, 'html'))

        # Attach PDF report
        with open(report_path, 'rb') as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
            pdf_attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=os.path.basename(report_path)
            )
            message.attach(pdf_attachment)

        # Send email
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        self.gmail_service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        logger.info(f"Emailed report to {management_email}")

    except Exception as e:
        logger.error(f"Failed to email report to management: {e}")
        # Don't raise - this shouldn't stop the main process
```

#### Step 4: Add ReportLab Dependency

**File:** `requirements.txt`

Add:
```
reportlab>=4.0.0
```

Then reinstall:
```bash
pip install -r requirements.txt
```

#### Step 5: Create Reports Directory

```bash
mkdir -p app/reports
touch app/reports/__init__.py
```

---

## Testing Instructions

### Test PBS Integration
1. Create test receipt with missing labels
2. Run Stock Receipts program
3. Verify email includes Stripe payment button
4. Click button and complete test payment
5. Verify labels are emailed back

### Test Accession Reports
1. Create test accession in Stock Receipts sheet
2. Run Stock Receipts program
3. Check `reports/` directory for PDF
4. Verify robert.zippoli@pathwaybook.com receives email with PDF attachment
5. Open PDF and verify all data is readable and fits on 8.5x11 page

---

## Important Notes

- **Environment Variables:** Ensure all API keys are set in Railway/production
- **Email Permissions:** Ensure Gmail API has send permissions for both systems
- **Error Handling:** Both features include error logging - check logs if issues occur
- **PDF Storage:** Reports are saved in `reports/` directory - consider periodic cleanup

---

## Support

For issues or questions:
- BISG Labels API: https://app.bisglabels.com/health
- Stock Receipts: Check logs in Stock-Receipts/logs/
- Railway Logs: https://railway.app → Your Project → Deployments → View Logs

---

**Document Created:** October 3, 2025
**Author:** Claude Code
**Version:** 1.0
