# BISG Labels Service

Automated label generation service for publishers who need BISG-compliant book and carton labels. Monetizes the missing label workflow from Pathway Book Service through Stripe payments.

## Overview

When publishers receive books with missing BISG-compliant labels, they can purchase and receive labels automatically via Stripe. The service integrates with existing Google Sheets data and generates professional PDF labels.

## Features

- **Stripe Checkout Integration**: Automated payment processing with custom line items
- **Dual Label Types**: Book labels (2" x 1.25") and Carton labels (6" x 4")
- **Google Sheets Integration**: Pulls book data from Form Responses and Stock Receipts sheets
- **Webhook Processing**: Automatic label generation after successful payment
- **Email Delivery**: Labels sent to publishers (stub for now, Gmail API to be configured)

## Tech Stack

- **Backend**: Python Flask
- **Payment**: Stripe (checkout sessions + webhooks)
- **Data Source**: Google Sheets API
- **PDF Generation**: ReportLab
- **Hosting**: Railway.app (deployment ready)

## Project Structure (NEW - Reorganized)

```
bisg-labels/
├── app/                       # Main application package
│   ├── main.py               # Flask application entry point
│   ├── routes/               # API endpoint handlers (future)
│   ├── services/             # Business logic layer
│   │   ├── stripe_service.py    # Stripe checkout & webhooks
│   │   ├── sheets_service.py    # Google Sheets data access
│   │   ├── label_service.py     # PDF generation
│   │   └── email_service.py     # Gmail delivery
│   ├── utils/                # Utilities
│   │   ├── validation.py        # Input validation
│   │   └── helpers.py           # Helper functions
│   └── static/               # Frontend assets
│       └── index.html
├── scripts/                   # Utility scripts
│   ├── generate_gmail_token.py
│   └── generate_sheets_token.py
├── tests/                     # Test suite
│   ├── test_stripe.py
│   └── test_new_features.py
├── config/                    # Configuration
│   ├── .env                  # Environment variables (gitignored)
│   ├── .env.example          # Template
│   └── credentials/          # API credentials (gitignored)
├── docs/                      # Documentation
│   ├── CLAUDE.md             # Implementation guide
│   ├── UPDATE.md             # Integration instructions
│   ├── CHANGELOG.md          # Version history
│   └── reference/            # Reference implementations
│       ├── Stock-Receipts/
│       ├── Accessions-Transfer/
│       └── label-generators/
├── outputs/                   # Generated PDFs (gitignored)
├── requirements.txt           # Python dependencies
├── Procfile                   # Railway deployment config
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Installation

### Prerequisites

- Python 3.9+
- Stripe account (test mode for development)
- Google Cloud project with Sheets API enabled
- Service account credentials for Google Sheets

### Local Setup

1. **Clone and navigate to the project:**
   ```bash
   cd "C:\Users\lucam\OneDrive\Documents\Desktop\EMS - Work\BISGLabels.com\bisg-labels"
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   copy config\.env.example config\.env
   # Edit config/.env and add your API keys
   ```

5. **Run the application:**
   ```bash
   python app/main.py
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Flask
FLASK_SECRET_KEY=your-secret-key
FLASK_DEBUG=False
PORT=5000

# Stripe (get from https://dashboard.stripe.com/test/apikeys)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Google Sheets
STOCK_SHEET_ID=1JxXMa2U5aY05UrkdBVAzBfAl2FyD_y8c3ahfJmAsKe0
FORM_SHEET_ID=1VplvZtm6Oiy1KWUlKiiR8JC93RSrPzcVgI0GltgFGiU
GOOGLE_SHEETS_CREDS={"type":"service_account",...}

# Email (to be configured)
SENDER_EMAIL=labels@bisglabels.com
```

### Google Sheets Setup

1. Create a service account in Google Cloud Console
2. Enable Google Sheets API
3. Share both sheets with the service account email
4. Download credentials JSON and paste into `GOOGLE_SHEETS_CREDS`

## API Endpoints

### `POST /create-checkout`

Create a Stripe checkout session for label purchase.

**Request Body:**
```json
{
  "isbn": "9780985347024",
  "date": "10/2/2025",
  "label_type": "both",
  "customer_type": "pbs"
}
```

**Parameters:**
- `isbn` (string): ISBN-13 of the book
- `date` (string): Shipment date (format: MM/DD/YYYY)
- `label_type` (string): `"book"`, `"carton"`, or `"both"`
- `customer_type` (string): `"pbs"` or `"direct"`

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/..."
}
```

### `POST /webhook`

Stripe webhook endpoint for payment processing.

**Headers:**
- `Stripe-Signature`: Webhook signature for verification

**Behavior:**
1. Verifies webhook signature
2. Extracts payment metadata
3. Looks up book data from Google Sheets
4. Generates PDF labels
5. Sends labels via email

### `GET /health`

Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "service": "BISG Labels",
  "version": "1.0.0"
}
```

## Pricing

- Book labels only: **$50**
- Carton labels only: **$50**
- Both labels: **$100**

## Data Flow

```
1. Stock Receipt Sheet (detects missing labels)
   ↓
2. Stock Receipts Program (sends email with Stripe link)
   ↓ (API call to /create-checkout)
3. Flask App generates Stripe Checkout Session
   ↓
4. Publisher pays via Stripe
   ↓
5. Stripe Webhook → Flask App (/webhook)
   ↓
6. Generate PDF Labels (using ISBN data from sheets)
   ↓
7. Email labels to publisher and/or Pathway
```

## Label Specifications

### Book Labels (2" x 1.25")
- Bookland EAN-13 barcode (from ISBN)
- Price add-on (EAN-5)
- Placed on back of book

### Carton Labels (6" x 4")
- Title, Author, Publisher info
- ISBN-10 and ISBN-13 barcodes
- Carton quantity (AI 30)
- Carton weight (AI 3401)
- GTIN-14 barcode (AI 01)
- Cover price (AI 9012Q)

## Testing

### Local Webhook Testing

1. Install Stripe CLI:
   ```bash
   stripe listen --forward-to localhost:5000/webhook
   ```

2. Use the webhook secret provided by Stripe CLI in your `.env` file

3. Trigger test events:
   ```bash
   stripe trigger checkout.session.completed
   ```

### Manual API Testing

```bash
# Test checkout creation
curl -X POST http://localhost:5000/create-checkout \
  -H "Content-Type: application/json" \
  -d '{
    "isbn": "9780985347024",
    "date": "10/2/2025",
    "label_type": "both",
    "customer_type": "pbs"
  }'
```

## Deployment

### Railway.app

1. **Connect Repository:**
   - Link your GitHub repo to Railway
   - Railway will auto-detect the Flask app

2. **Add Environment Variables:**
   - Go to Railway dashboard
   - Add all variables from `.env.example`
   - Use production Stripe keys

3. **Deploy:**
   - Railway auto-deploys on `git push`
   - Get your production URL from Railway dashboard

4. **Configure Stripe Webhook:**
   - Add Railway URL to Stripe webhooks: `https://your-app.up.railway.app/webhook`
   - Use the webhook secret in environment variables

## Frontend

A professional HTML frontend is available at `Frontend.html` in the project root. Features include:

### Features
- **Landing Page**: Service description, value proposition, and branding
- **Why BISG Section**: Compliance benefits and industry standards
- **Services Overview**: Book labels, carton labels, and pricing options
- **Pricing Section**: Clear pricing cards ($50/$50/$100)
- **Order Form**: Interactive form with validation
  - ISBN-13 input with checksum validation
  - Date picker for shipment date
  - Label type selection (book/carton/both)
  - Customer type selection (PBS client/Direct publisher)
- **Mobile Responsive**: Optimized for all screen sizes
- **Modern Design**: Professional publishing industry aesthetic

### Configuration
Update the API endpoint in the JavaScript section of `Frontend.html`:

```javascript
// For production, update the API_BASE_URL
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:5000'
    : 'https://your-production-api-url.com';
```

### Deployment
- Host the `Frontend.html` file on any static hosting service (Netlify, Vercel, GitHub Pages, etc.)
- Update the production API URL to point to your Railway deployment
- Configure CORS on the Flask backend if needed

## Integration with Stock Receipts

Update the Stock Receipts program to call the `/create-checkout` endpoint:

```python
import requests

response = requests.post('https://your-railway-app.up.railway.app/create-checkout', json={
    'isbn': '9780985347024',
    'date': '10/2/2025',
    'label_type': 'both',
    'customer_type': 'pbs'
})

stripe_url = response.json()['checkout_url']
# Include stripe_url in email template
```

## Google Sheets Data Structure

### Form Responses Sheet (Book Data)
- Column M: Title
- Column N: ISBN-13
- Column O: Publisher
- Column R: Country of Origin
- Column S: Pub Date
- Column T: Missing Book Label
- Column U: Missing Carton

### Stock Receipts Sheet (Publisher Email)
- Column A: Date
- Column F: ISBN
- Column H: Publisher Email
- Column I: Missing Book Label (Y/N)
- Column J: Missing Carton Label (Y/N)

## TODO

- [ ] Configure Gmail API for email delivery
- [ ] Add authentication for API endpoints (optional)
- [ ] Implement logging and monitoring
- [ ] Add retry logic for failed operations
- [ ] Create admin dashboard for tracking orders
- [ ] Add support for bulk label generation

## Development Notes

- Start with Stripe **test mode** for all development
- Keep generated PDFs in `outputs/` directory temporarily
- Match records between sheets using ISBN + Date
- Focus on core functionality first: checkout → webhook → label generation

## Support

For issues or questions:
- Check Railway logs for debugging
- Review Stripe dashboard for payment issues
- Verify Google Sheets permissions for data access

## License

Internal use for Pathway Book Service / BISGLabels.com
