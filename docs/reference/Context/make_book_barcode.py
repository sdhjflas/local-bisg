# make_book_barcode.py – Bookland EAN + Price Add-On (back of book label)
# Run: python make_book_barcode.py

import os
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics import renderPDF

OUTPUT_PATH = r"C:\Users\SageJ\Documents\labels\book_barcode_label.pdf"

# -------- ORDER DATA --------
data = {
    "ISBN13": "9780985347024",
    "Price": "49.95",     # leave "" for “no price” (will encode 90000)
    "Currency": "USD",    # USD, CAD, GBP, EUR, AUD, NZD
}

# -------- Helpers --------
def only_digits(s):
    return "".join(ch for ch in (s or "") if s and ch.isdigit())

def format_isbn13(isbn):
    d = only_digits(isbn)
    if len(d) != 13:
        return isbn
    return f"{d[0:3]}-{d[3]}-{d[4:7]}-{d[7:12]}-{d[12]}"

def price_to_cents(price):
    try:
        return int(round(float(price) * 100))
    except:
        return None

def addon_from_price(price_cents, currency="USD"):
    currency_digit = {
        "USD": "5",
        "CAD": "6",
        "GBP": "0",
        "EUR": "3",
        "AUD": "4",
        "NZD": "4",
    }.get(currency.upper(), "5")
    if price_cents is None:
        return "90000"  # “no price” code
    return currency_digit + f"{price_cents:04d}"[-4:]

def human_price(price_cents, currency="USD"):
    if price_cents is None:
        return ""
    major, minor = divmod(price_cents, 100)
    sym = {"USD":"$", "CAD":"C$", "GBP":"£", "EUR":"€", "AUD":"A$", "NZD":"NZ$"}.get(currency.upper(), "$")
    suffix = {"USD":"US", "CAD":"CAN", "GBP":"UK", "EUR":"EUR", "AUD":"AUD", "NZD":"NZ"}.get(currency.upper(), currency.upper())
    return f"{sym}{major}.{minor:02d} {suffix}"

# -------- Main --------
def make_book_barcode(output_path=OUTPUT_PATH):
    WIDTH, HEIGHT = 2.0*inch, 1.25*inch   # standard block size
    c = canvas.Canvas(output_path, pagesize=(WIDTH, HEIGHT))

    isbn = only_digits(data["ISBN13"])
    price_c = price_to_cents(data["Price"])
    addon = addon_from_price(price_c, data["Currency"])

    ean13 = createBarcodeDrawing("EAN13", value=isbn, barHeight=0.55*inch, humanReadable=True)
    ean5  = createBarcodeDrawing("EAN5",  value=addon, barHeight=0.50*inch, humanReadable=True)

    # Draw top line (ISBN + price)
    c.setFont("Helvetica", 8)
    top_text = f"ISBN {format_isbn13(isbn)}"
    hp = human_price(price_c, data["Currency"])
    if hp:
        top_text += "    " + hp
    c.drawCentredString(WIDTH/2, HEIGHT - 0.18*inch, top_text)

    # Position EAN13 left, EAN5 right
    ean13_x = 0.25*inch
    ean_y   = 0.25*inch
    renderPDF.draw(ean13, c, ean13_x, ean_y)
    renderPDF.draw(ean5,  c, ean13_x + ean13.width + 0.10*inch, ean_y)

    c.showPage()
    c.save()
    print(f"✅ Book barcode saved to {output_path}")

# -------- Run --------
if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    make_book_barcode()
