# BISG Labels Service - Development Guide

## Project Overview
BISGLabels.com is a label generation service that monetizes the missing label workflow from Pathway Book Service. When publishers receive books with missing BISG-compliant labels, they can purchase and receive labels automatically via Stripe.

## Business Model
- **Two customer types:**
  1. **Pathway Book Service clients** - Get emails about missing labels, purchase via Stripe, labels auto-sent to PBS
  2. **Direct publishers** - Can request labels directly, pay via Stripe, receive labels immediately

## Tech Stack
- **Hosting**: Railway.app
- **Backend**: Python Flask
- **Payment**: Stripe (checkout sessions + webhooks)
- **Data**: Google Sheets API
- **PDF Generation**: ReportLab
- **Email**: Gmail API (to be configured later)

## System Architecture

### Corrected Data Flow:
```
1. Employee fills out Google Form
   ↓
2. Form Responses Sheet (raw data with better book details)
   ID: 1VplvZtm6Oiy1KWUlKiiR8JC93RSrPzcVgI0GltgFGiU
   ↓
3. PM approves accession
   ↓
4. Accessions Transfer runs (accessions_transfer.py)
   - Reads from Form Responses Sheet
   - Calls publisher_database.py to get publisher email
   - Writes to Stock Receipts Sheet
   ↓
5. Stock Receipts Sheet (has publisher email + missing label flags)
   ID: 1JxXMa2U5aY05UrkdBVAzBfAl2FyD_y8c3ahfJmAsKe0
   ↓
6. Stock Receipts App runs (stock_receipts program)
   - Reads from Stock Receipts Sheet
   - Detects missing labels (Y/N in columns I & J)
   - Calls BISG Labels API to generate Stripe link
   - Sends emails with Stripe payment link
   ↓
7. Publisher pays via Stripe
   ↓
8. Stripe Webhook → BISG Labels Service
   ↓
9. Generate PDF Labels (using ISBN to lookup data from both sheets)
   ↓
10. Email labels to publisher and/or Pathway
```

### Key Components:

**1. Flask Endpoints:**
- `POST /create-checkout` - Generate Stripe checkout URL
  - Input: ISBN, date, label_type, customer_type
  - Looks up book data from Form Responses Sheet
  - Looks up publisher email from Stock Receipts Sheet
  - Returns: Stripe checkout URL
- `POST /webhook` - Handle Stripe payment webhooks
  - Validates webhook signature
  - Generates labels
  - Emails labels to appropriate recipients
- `GET /health` - Health check

**2. Label Generation:**
- Book labels (back cover barcode with price) - 2" x 1.25"
- Carton labels (BISG shipping labels) - 6" x 4"
- Uses existing label generation scripts refactored into functions

**3. Data Sources:**
- **Form Responses Sheet** (BETTER BOOK DATA): `1VplvZtm6Oiy1KWUlKiiR8JC93RSrPzcVgI0GltgFGiU`
  - Columns: Timestamp, Employee, Carrier, Title, ISBN, Publisher, Author, Price, Pub Date, Country, etc.
- **Stock Receipts Sheet** (HAS PUBLISHER EMAIL): `1JxXMa2U5aY05UrkdBVAzBfAl2FyD_y8c3ahfJmAsKe0`
  - Columns: Date, Time, Carrier, Who, Title, ISBN, Publisher, Pub Email, Missing Book Label, Missing Carton Label, Qty, etc.

**Data Lookup Strategy:**
- Match records using ISBN + Date
- Get book details (Title, Author, Price, etc.) from Form Responses Sheet
- Get publisher email from Stock Receipts Sheet

## Environment Variables Needed:
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
GOOGLE_SHEETS_CREDS=<json content from credentials.json>
STOCK_SHEET_ID=1JxXMa2U5aY05UrkdBVAzBfAl2FyD_y8c3ahfJmAsKe0
FORM_SHEET_ID=1VplvZtm6Oiy1KWUlKiiR8JC93RSrPzcVgI0GltgFGiU
SENDER_EMAIL=<to be configured later>
```

## Pricing:
- Book labels only: $50
- Carton labels only: $50
- Both labels: $100

## Checkout Features:
- Pre-filled customer email (from Stock Receipts Sheet)
- Custom line item showing book title + ISBN
- Metadata: shipment_id, isbn, label_type, customer_type, date
- Checkbox: "Send me a copy of the labels" (for PBS clients - labels auto-go to Pathway)
- Success page with order confirmation

## Project Directory:
```
C:\Users\lucam\OneDrive\Documents\Desktop\EMS - Work\BISGLabels.com\

bisg-labels/
├── app.py                 # Main Flask application
├── stripe_handler.py      # Stripe checkout + webhook logic
├── label_generator.py     # PDF generation (refactored from make_labels.py)
├── email_sender.py        # Gmail API integration (placeholder for now)
├── sheets_handler.py      # Google Sheets data lookups (queries both sheets)
├── utils.py               # Helper functions
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variable template
├── .gitignore            # Ignore secrets and temp files
├── outputs/              # Generated PDF labels (temp storage)
│   └── .gitkeep
└── README.md             # Setup instructions
```

## Development Workflow:

1. **Local Development:**
   ```bash
   cd "C:\Users\lucam\OneDrive\Documents\Desktop\EMS - Work\BISGLabels.com"
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   # Add your API keys to .env
   python app.py
   ```

2. **Testing Webhooks Locally:**
   ```bash
   stripe listen --forward-to localhost:5000/webhook
   # Use test mode keys and Stripe CLI for testing
   ```

3. **Deploy to Railway:**
   - Connect GitHub repo to Railway
   - Add environment variables in Railway dashboard
   - Railway auto-deploys on git push

## Integration with Stock Receipts:

**Modification needed in stock_receipts program:**
- When creating email about missing labels, make API call to generate Stripe link
- Include generated link in email template

**Example API call from stock_receipts:**
```python
import requests

response = requests.post('https://your-railway-app.up.railway.app/create-checkout', json={
    'isbn': '9780985347024',
    'date': '10/2/2025',
    'label_type': 'both',  # 'book', 'carton', or 'both'
    'customer_type': 'pbs'  # 'pbs' or 'direct'
})

stripe_url = response.json()['checkout_url']
# Include stripe_url in email template
```

## Label Generation Details:

**Book Labels (2" x 1.25"):**
- Bookland EAN-13 barcode (from ISBN)
- Price add-on (EAN-5)
- Goes on back of book

**Carton Labels (6" x 4"):**
- Title, Author, Publisher info
- ISBN-10 and ISBN-13 barcodes
- Carton quantity (AI 30)
- Carton weight (AI 3401)
- GTIN-14 barcode (AI 01)
- Cover price (AI 9012Q)

## Google Sheets Column Mappings:

**Form Responses Sheet Columns (better book data):**
- A: Timestamp
- E: Counted By
- F: Delivered By
- H: Number of Cartons
- I: Books per Carton
- K: Total Books Received
- L: Damaged Books
- M: Book Title
- N: ISBN-13
- O: Publisher
- R: Country of Origin
- S: Pub Date
- T: Missing Barcode (book label)
- U: Missing Carton

**Stock Receipts Sheet Columns (has publisher email):**
- A: Date
- B: Time
- C: Carrier
- D: Who
- E: Title
- F: ISBN
- G: Publisher
- H: Pub Email ← THIS IS THE KEY FIELD
- I: Missing Book Label (Y/N)
- J: Missing Carton Label (Y/N)
- K: # Ctns
- L: Full Case Qty
- M: Acc Qty
- N: Damaged
- O: Net
- P: Pub Date
- Q: Country of Origin

## Initial Build Tasks:

1. **Set up Flask app structure**
   - Create all files in project directory
   - Set up basic routing and error handling

2. **Implement sheets_handler.py**
   - Google Sheets authentication
   - Function to lookup book data by ISBN + date from Form Responses
   - Function to get publisher email by ISBN + date from Stock Receipts
   - Combine data into single record

3. **Implement stripe_handler.py**
   - Create checkout session with custom metadata
   - Handle webhook signature verification
   - Parse payment success events

4. **Implement label_generator.py**
   - Refactor make_labels.py into generate_carton_label(data) function
   - Refactor make_book_barcode.py into generate_book_label(data) function
   - Accept data dictionary instead of hardcoded values
   - Return file paths of generated PDFs

5. **Stub email_sender.py**
   - Placeholder functions for now
   - Will configure Gmail API later

6. **Create .env.example and requirements.txt**

## Notes:
- Start with Stripe test mode for all development
- Use Stripe CLI for local webhook testing
- Keep generated PDFs in outputs/ directory temporarily
- Match records between sheets using ISBN (column N in Form, column F in Stock) and Date
- Email configuration will be added later
- Focus on core functionality first: checkout generation → webhook → label generation

## Next Steps for Claude Code:
1. Create the project structure in the specified directory
2. Implement sheets_handler.py with Google Sheets integration
3. Implement stripe_handler.py for checkout sessions
4. Refactor label generation scripts into reusable functions
5. Wire everything together in app.py
6. Create requirements.txt with all dependencies
7. Test end-to-end with mock data# BISG Labels Service - Development Guide

## Project Overview
BISGLabels.com is a label generation service that monetizes the missing label workflow from Pathway Book Service. When publishers receive books with missing BISG-compliant labels, they can purchase and receive labels automatically via Stripe.

## Business Model
- **Two customer types:**
  1. **Pathway Book Service clients** - Get emails about missing labels, purchase via Stripe, labels auto-sent to PBS
  2. **Direct publishers** - Can request labels directly, pay via Stripe, receive labels immediately

## Tech Stack
- **Hosting**: Railway.app
- **Backend**: Python Flask
- **Payment**: Stripe (checkout sessions + webhooks)
- **Data**: Google Sheets API
- **PDF Generation**: ReportLab
- **Email**: Gmail API

## System Architecture

### Data Flow:
```
Stock Receipt Sheet (detects missing labels)
    ↓
Stock Receipts Program (sends email with Stripe link)
    ↓ (API call)
Flask App on Railway (/create-checkout)
    ↓ (generates)
Stripe Checkout Session (custom per shipment)
    ↓ (customer pays)
Stripe Webhook → Flask App (/webhook)
    ↓
Generate PDF Labels (using ISBN data from sheets)
    ↓
Email labels to publisher and/or Pathway
```

### Key Components:

**1. Flask Endpoints:**
- `POST /create-checkout` - Generate Stripe checkout URL
- `POST /webhook` - Handle Stripe payment webhooks  
- `GET /health` - Health check

**2. Label Generation:**
- Book labels (back cover barcode with price)
- Carton labels (BISG shipping labels)
- Uses existing label generation scripts refactored into functions

**3. Data Sources:**
- Stock Receipt Sheet: `1JxXMa2U5aY05UrkdBVAzBfAl2FyD_y8c3ahfJmAsKe0`
- Form Responses Sheet: `1Bzdrw6lKHd_Cx-8Nt1IQykz3PSbPbbBh6tQvzd-SoDA`

## Environment Variables Needed:
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
GOOGLE_SHEETS_CREDS=<json content from credentials.json>
STOCK_SHEET_ID=1JxXMa2U5aY05UrkdBVAzBfAl2FyD_y8c3ahfJmAsKe0
FORM_SHEET_ID=1Bzdrw6lKHd_Cx-8Nt1IQykz3PSbPbbBh6tQvzd-SoDA
SENDER_EMAIL=<to be configured>
```

## Pricing:
- Book labels only: $50
- Carton labels only: $50
- Both labels: $100

## Checkout Features:
- Pre-filled customer email (from publisher records)
- Custom line item showing book title + ISBN
- Metadata: shipment_id, isbn, label_type, customer_type
- Checkbox: "Send me a copy of the labels" (default: labels go to Pathway for PBS clients)
- Success page with order confirmation

## File Structure:
```
bisg-labels/
├── app.py                 # Main Flask application
├── stripe_handler.py      # Stripe checkout + webhook logic
├── label_generator.py     # PDF generation (refactored from make_labels.py)
├── email_sender.py        # Gmail API integration
├── sheets_handler.py      # Google Sheets data lookups
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variable template
├── .gitignore            # Ignore secrets and temp files
├── railway.json          # Railway deployment config (optional)
└── README.md             # Setup instructions
```

## Development Workflow:

1. **Local Development:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   cp .env.example .env
   # Add your API keys to .env
   python app.py
   ```

2. **Testing Webhooks Locally:**
   ```bash
   stripe listen --forward-to localhost:5000/webhook
   # Use test mode keys and Stripe CLI for testing
   ```

3. **Deploy to Railway:**
   - Connect GitHub repo to Railway
   - Add environment variables in Railway dashboard
   - Railway auto-deploys on git push

## Integration with Stock Receipts:

**Minimal modification needed:**
- Update email templates to replace old "we can make labels" text
- Add API call to `/create-checkout` endpoint to generate Stripe link
- Include generated link in email

**Example API call from stock_receipts:**
```python
import requests

response = requests.post('https://your-railway-app.up.railway.app/create-checkout', json={
    'isbn': '9780985347024',
    'publisher_email': 'publisher@example.com',
    'label_type': 'both',  # 'book', 'carton', or 'both'
    'customer_type': 'pbs',  # 'pbs' or 'direct'
    'book_title': 'The Oklahomans',
    'shipment_date': '10/2/2025'
})

stripe_url = response.json()['checkout_url']
# Include stripe_url in email template
```

## Label Generation Details:

**Book Labels:**
- Bookland EAN-13 barcode (from ISBN)
- Price add-on (EAN-5)
- 2" x 1.25" size
- Goes on back of book

**Carton Labels:**
- 6" x 4" shipping label
- Title, Author, Publisher info
- ISBN-10 and ISBN-13 barcodes
- Carton quantity (AI 30)
- Carton weight (AI 3401)
- GTIN-14 barcode (AI 01)
- Cover price (AI 9012Q)

## Next Steps:
1. Build Flask app with all endpoints
2. Refactor label generation scripts into functions
3. Set up Google Sheets API integration
4. Configure Stripe webhooks
5. Test end-to-end with Stripe test mode
6. Deploy to Railway
7. Update stock_receipts email templates
8. Go live with PBS customers

## Notes:
- Start with Stripe test mode for all development
- Use test mode webhook secret during development
- Keep production and test environments separate
- Monitor Railway logs for debugging
- Set up Stripe webhook signature verification for security