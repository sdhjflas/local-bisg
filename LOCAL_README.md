# BISG Label Generator - Local Version

Simple, standalone label generator that runs locally without any external dependencies (no Stripe, Google Sheets, or Gmail required).

## Features

- ✅ Generate BISG-compliant book labels (2" x 1.25")
- ✅ Generate BISG-compliant carton labels (6" x 4")
- ✅ Multiple format options (single labels, sheets of 30, two-up)
- ✅ Support for standard ISBN-13 and custom alphanumeric UPCs
- ✅ Runs entirely locally - no internet connection needed
- ✅ Simple web interface
- ✅ Instant PDF downloads

## Quick Start

### 1. Install Python

Make sure you have Python 3.9 or higher installed:

```bash
python --version
```

### 2. Install Dependencies

```bash
pip install -r requirements_local.txt
```

Or install manually:

```bash
pip install Flask==3.0.0 Flask-CORS==4.0.0 reportlab==4.0.7 Werkzeug==3.0.1
```

### 3. Run the Application

```bash
python local_app.py
```

You should see:

```
============================================================
🏷️  BISG Labels - Local Label Generator
============================================================
✅ Server running at: http://localhost:5000
📁 Labels will be saved to: /tmp/bisg-labels-local
============================================================

🎯 Open your browser and go to:
   http://localhost:5000
```

### 4. Generate Labels

1. Open your browser and go to `http://localhost:5000`
2. Fill in the form with your book information:
   - **Book Title** (required)
   - **Author** (required)
   - **Publisher** (required)
   - **ISBN-13** (required) - 13 digits
   - **Price** (required)
   - **Currency** - USD, CAD, GBP, EUR, AUD, NZD
   - **Publication Date** (optional)
   - **Books per Carton** (default: 10)
   - **Carton Weight** (default: 25 lbs)
   - **Country of Origin** (default: USA)

3. Choose your label options:
   - **Label Type**: Book only, Carton only, or Both
   - **Book Format**: Single label, Sheet of 30, or Both
   - **Carton Format**: Single label, Two-up, or Both

4. Click **Generate Labels**

5. Download your PDFs!

## Label Types

### Book Labels

- **Single Label**: One 2" x 1.25" label with Bookland EAN-13 barcode and price add-on
- **Sheet of 30**: Letter-size page with 30 labels (3 rows × 10 columns) for easy printing on label sheets

### Carton Labels

- **Single Label**: One 6" x 4" label with:
  - Title, Author, Publisher information
  - ISBN-10 and ISBN-13 barcodes
  - GTIN-14 barcode with AI 01
  - Carton quantity (AI 30)
  - Carton weight (AI 3401)
  - Cover price (AI 9012Q)

- **Two-up**: Two 6" × 4" labels on a letter-size page for efficient printing

## Custom Alphanumeric UPCs

If your ISBN contains letters (e.g., "9780985347024HAT"), check the "Use custom alphanumeric UPC" option. This will generate Code 128 barcodes instead of EAN-13.

## File Locations

Generated PDFs are saved to:
- **Linux/Mac**: `/tmp/bisg-labels-local/`
- **Windows**: `C:\Users\<YourUsername>\AppData\Local\Temp\bisg-labels-local\`

Files are named: `label_<ISBN>_<type>.pdf`

For example:
- `label_9780985347024_book.pdf`
- `label_9780985347024_book_sheet.pdf`
- `label_9780985347024_carton.pdf`
- `label_9780985347024_carton_twoup.pdf`

## Troubleshooting

### Port Already in Use

If port 5000 is already in use, you can change it:

1. Edit `.env.local` and change `PORT=5000` to another port (e.g., `PORT=5001`)
2. Or set it when running: `PORT=5001 python local_app.py`

### Installation Issues

If you get errors installing dependencies, try:

```bash
# Upgrade pip first
pip install --upgrade pip

# Then install dependencies
pip install -r requirements_local.txt
```

### Barcode Generation Issues

If barcodes don't generate properly:
- Make sure your ISBN is exactly 13 digits (for standard ISBNs)
- For custom UPCs with letters, check the "Use custom alphanumeric UPC" checkbox
- Verify the price is a valid number (e.g., "24.99" not "$24.99")

## Differences from Production Version

This local version:
- ❌ No payment processing (Stripe)
- ❌ No Google Sheets integration
- ❌ No email delivery (Gmail)
- ❌ No authentication required
- ✅ Pure label generation only
- ✅ Instant downloads
- ✅ No internet connection required

## Project Structure

```
local-bisg/
├── local_app.py              # Simplified Flask app (no external services)
├── simple_form.html          # Simple web form for label input
├── requirements_local.txt    # Minimal dependencies
├── .env.local               # Local configuration (optional)
├── app/
│   └── services/
│       └── label_service.py  # Core label generation logic (unchanged)
└── LOCAL_README.md          # This file
```

## Need Help?

The label generation code is unchanged from the production version, so labels generated locally will be identical to those generated in production. This is purely a simplified interface without payment/integration overhead.

## Advanced Usage

### API Endpoint

You can also generate labels programmatically:

```bash
curl -X POST http://localhost:5000/generate-labels \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Book",
    "author": "John Doe",
    "publisher": "Acme Publishing",
    "isbn": "9780985347024",
    "price": "24.99",
    "currency": "USD",
    "label_type": "both",
    "book_format": "both",
    "carton_format": "both"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Labels generated successfully",
  "files": {
    "book_label_single": {
      "filename": "label_9780985347024_book.pdf",
      "download_url": "/download/label_9780985347024_book.pdf"
    },
    "book_label_sheet": {
      "filename": "label_9780985347024_book_sheet.pdf",
      "download_url": "/download/label_9780985347024_book_sheet.pdf"
    },
    ...
  }
}
```

### Batch Generation

To generate labels for multiple books, you can write a simple Python script:

```python
import requests

books = [
    {"isbn": "9780985347024", "title": "Book 1", ...},
    {"isbn": "9781234567890", "title": "Book 2", ...},
]

for book in books:
    response = requests.post(
        "http://localhost:5000/generate-labels",
        json={**book, "label_type": "both"}
    )
    print(f"Generated labels for {book['title']}")
```

## License

Internal use for Pathway Book Service / BISGLabels.com
