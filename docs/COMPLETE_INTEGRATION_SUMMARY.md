# Complete PBS Integration Summary

## What You're Implementing

### 1. Stripe Payment Links in Stock Receipts Emails ✅
**Goal:** Add "Pay Online" buttons to emails when labels are missing

**Three Email Templates Get Updated:**
- `missing_book_label.html` → Stripe link for book labels ($50)
- `missing_carton_label.html` → Stripe link for carton labels ($50)
- `missing_both_label.html` → Stripe link for both ($100)

**How It Works:**
1. Stock Receipts detects missing labels (columns I & J)
2. Calls `https://app.bisglabels.com/create-checkout`
3. Gets Stripe checkout URL back
4. Includes payment button in email template
5. Publisher clicks → pays → labels auto-generated → emailed

**Minimal Friction:**
- Publishers see payment option, can choose it or not
- Existing internal billing still works
- Only adds new option, doesn't remove anything

---

### 2. One-Page PDF Accession Reports ✅
**Goal:** Email condensed PDF with ALL form data to Robert for every accession

**Data Source:**
- Google Form Responses Sheet: `1Bzdrw6lKHd_Cx-8Nt1IQykz3PSbPbbBh6tQvzd-SoDA`
- Has ALL fields (30+ fields including dimensions, weights, etc.)

**How It Works:**
1. Stock Receipts processes accession
2. Looks up ISBN in Form Responses Sheet
3. Fetches ALL form data
4. Generates ultra-condensed PDF (7pt font, 2-column layout)
5. Emails to robert.zippoli@pathwaybook.com
6. PDF fits on ONE 8.5x11 page (not 6-7 pages like Google Forms print)

**PDF Contains:**
```
Timestamp, Date, Counted By, Delivered By, Title, Author,
ISBN, Publisher, Format, Price, Country, Pub Date, Cartons,
Books/Carton, Total Books, Damaged, Missing Barcodes,
Missing Carton Labels, Book Weight, Case Weight, Dimensions
(Height/Width/Depth), Carton Dimensions, Slot, Skid, etc.
```

---

## Implementation Files

### Primary Changes:
1. **`app/processors/receipt_processor.py`**
   - Add `_generate_stripe_link()` method
   - Add `_email_pdf_to_robert()` method
   - Update `process_daily_receipts()` to call both

2. **`app/processors/template_manager.py`**
   - Update `build_email_body()` to accept `stripe_link` parameter
   - Inject payment button HTML into templates

3. **`app/reports/form_pdf_generator.py`** (NEW FILE)
   - Fetches from Form Responses Sheet
   - Generates one-page condensed PDF
   - Returns PDF path

### New Dependencies:
```bash
pip install requests reportlab
```

---

## Key Details

### Form Responses Sheet Columns:
```
A: Timestamp
B: Email Address
C: Date Received
D: Counted By
E: Delivered By
F: Pallet number
G: Number of Cartons
H: Books Per Carton
I: Books Per Skid
J: Total Books
K: Damaged Books
L: Book Title
M: Book ISBN-13
N: Publisher
O: Format
P: Book Price
Q: Country of Origin
R: Pub Date
S: Missing Barcodes
T: Missing Carton Labels
U: Book Weight
V: Slot
W: Case Weight
X: Book Height
Y: Book Width
Z: Book Depth
AA: Carton Width
AB: Carton Length
AC: Carton Height
AD: Author
... (adjust based on actual columns)
```

### Stock Receipts Sheet Columns:
```
A: Date
B: Time
C: Carrier
D: Who
E: Title
F: ISBN
G: Publisher
H: Pub Email
I: Missing Book Label (Y/N)
J: Missing Carton Label (Y/N)
K-Q: Quantities, dates, etc.
```

---

## Testing Checklist

### Test Stripe Integration:
- [ ] Create test receipt with missing book label
- [ ] Verify email includes payment button
- [ ] Click button, complete Stripe test payment
- [ ] Verify labels emailed back

### Test PDF Reports:
- [ ] Create test accession
- [ ] Run Stock Receipts
- [ ] Check `reports/` folder for PDF
- [ ] Verify PDF is ONE page
- [ ] Verify Robert receives email with PDF
- [ ] Print PDF to verify it fits on one page

---

## What Makes This Work

### Stripe Integration:
- BISG Labels API already built at `https://app.bisglabels.com`
- Stock Receipts just calls it to get checkout URL
- Payment triggers webhook → labels auto-generated → emailed
- Zero manual work once set up

### PDF Reports:
- Fetches from Form Responses (has ALL data)
- Matches by ISBN
- 7pt font + 2-column layout = fits on one page
- Auto-emails to Robert for EVERY accession

---

## Reference Documents

1. **UPDATE.md** - Full Stripe integration code
2. **ACCESSION_REPORT_IMPLEMENTATION.md** - One-page PDF implementation
3. **This file** - High-level summary

---

**Ready to implement!** Use UPDATE.md and ACCESSION_REPORT_IMPLEMENTATION.md in a new Claude Code instance in the Stock-Receipts directory.

**Created:** October 3, 2025
