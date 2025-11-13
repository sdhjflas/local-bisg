"""
Label Generation Module for BISG Labels Service
Refactored from make_labels.py and make_book_barcode.py
Generates BISG-compliant carton labels (6"x4") and book barcodes (2"x1.25")
"""

import os
import re
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128, createBarcodeDrawing, eanbc
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.pdfbase.pdfmetrics import stringWidth


# ==================== HELPER FUNCTIONS ====================

def digits(s):
    """Extract only digits from string"""
    return re.sub(r"\D", "", s or "")


def only_digits(s):
    """Extract only digits (alternative implementation)"""
    return "".join(ch for ch in (s or "") if ch.isdigit())


def isbn10_from_13(isbn13):
    """Convert ISBN-13 to ISBN-10 with check digit"""
    d = digits(isbn13)
    if len(d) != 13 or not d.startswith("978"):
        return None
    core9 = d[3:12]
    total = sum((10 - i) * int(core9[i]) for i in range(9))
    chk = 11 - (total % 11)
    return core9 + ("X" if chk == 10 else "0" if chk == 11 else str(chk))


def format_isbn13(isbn13):
    """Format ISBN-13 with dashes"""
    d = digits(isbn13)
    return f"{d[0:3]}-{d[3]}-{d[4:7]}-{d[7:12]}-{d[12]}" if len(d) == 13 else isbn13


def format_isbn10(isbn10):
    """Format ISBN-10 with dashes"""
    return f"{isbn10[0]}-{isbn10[1:4]}-{isbn10[4:9]}-{isbn10[9]}" if isbn10 and len(isbn10) == 10 else isbn10


def price_to_cents(price_str):
    """Convert price string to cents (integer)"""
    try:
        return int(round(float(price_str) * 100))
    except:
        return None


def gs1_check_digit(num_without_check: str) -> str:
    """Calculate GS1 check digit"""
    s = 0
    for i, ch in enumerate(num_without_check[::-1]):
        s += (3 if i % 2 == 0 else 1) * int(ch)
    return str((10 - (s % 10)) % 10)


def gtin14_from_isbn13(isbn13: str, indicator: str = "1") -> str:
    """Generate GTIN-14 from ISBN-13"""
    d = digits(isbn13)
    if len(d) != 13:
        d = (d + "0" * 13)[:13]
    body13 = indicator + d[:12]
    return body13 + gs1_check_digit(body13)


def fit_scale_x(natural_w, max_w):
    """Calculate X-axis scale factor to fit width"""
    if not natural_w or natural_w <= 0:
        return 1.0
    return min(1.0, max_w / float(natural_w))


def draw_code128_fit(c: canvas.Canvas, value: str, x_left: float, base_y: float,
                     col_width: float, bar_h: float, narrow_bar: float):
    """Draw Code128 barcode scaled to fit X; return scaled width for centering captions/HRI."""
    bc = code128.Code128(value, barWidth=narrow_bar, barHeight=bar_h)
    natural_w = getattr(bc, "width", col_width)
    sx = fit_scale_x(natural_w, col_width)
    scaled_w = natural_w * sx
    c.saveState()
    c.translate(x_left, base_y)
    c.scale(sx, 1.0)
    bc.drawOn(c, 0, 0)
    c.restoreState()
    return scaled_w


def addon_from_price(price_cents, currency="USD"):
    """Generate EAN-5 add-on code from price"""
    currency_digit = {
        "USD": "5",
        "CAD": "6",
        "GBP": "0",
        "EUR": "3",
        "AUD": "4",
        "NZD": "4",
    }.get(currency.upper(), "5")
    if price_cents is None:
        return "90000"  # "no price" code
    return currency_digit + f"{price_cents:04d}"[-4:]


def human_price(price_cents, currency="USD"):
    """Format price for human reading"""
    if price_cents is None or price_cents == 0:
        return ""
    major, minor = divmod(price_cents, 100)
    sym = {"USD": "$", "CAD": "C$", "GBP": "£", "EUR": "€", "AUD": "A$", "NZD": "NZ$"}.get(currency.upper(), "$")
    suffix = {"USD": "US", "CAD": "CAN", "GBP": "UK", "EUR": "EUR", "AUD": "AUD", "NZD": "NZ"}.get(currency.upper(), currency.upper())
    return f"{sym}{major}.{minor:02d} {suffix}"


def draw_centered_autofit(c, text, center_x, y, font_name="Helvetica-Bold",
                          max_size=15, min_size=8, max_width_pts=400):
    """
    Shrinks font size until 'text' fits within max_width_pts.
    If still too wide at min_size, truncates with an ellipsis.
    """
    txt = str(text or "")
    size = max_size
    # shrink to fit
    while size > min_size and stringWidth(txt, font_name, size) > max_width_pts:
        size -= 0.5

    # if still too wide at min size, truncate with ellipsis
    if stringWidth(txt, font_name, size) > max_width_pts:
        ell = "…"
        # keep as many characters as fit with ellipsis
        while txt and stringWidth(txt + ell, font_name, size) > max_width_pts:
            txt = txt[:-1]
        txt = txt.rstrip() + ell

    c.setFont(font_name, size)
    c.drawCentredString(center_x, y, txt)


# ==================== CARTON LABEL GENERATOR ====================

def generate_carton_label(data: dict, output_path: str) -> str:
    """
    Generate BISG-compliant carton label (6" x 4")

    Args:
        data: Dictionary containing:
            - Title: Book title
            - Author: Author name
            - Publisher: Publisher name
            - OnSale: On sale date (optional)
            - PrintedIn: Country of origin (default: USA)
            - CTN_QTY: Carton quantity
            - CTN_WGT: Carton weight in lbs
            - ISBN13: ISBN-13
            - Price: Cover price
        output_path: Path to save PDF

    Returns:
        Path to generated PDF file
    """
    WIDTH, HEIGHT = 6 * inch, 4 * inch
    c = canvas.Canvas(output_path, pagesize=(WIDTH, HEIGHT))

    # Frame & dividers
    MARGIN = 0.10 * inch
    header_h, middle_h = 0.95 * inch, 0.85 * inch
    header_bottom = HEIGHT - header_h
    middle_bottom = header_bottom - middle_h

    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(MARGIN, MARGIN, WIDTH - 2 * MARGIN, HEIGHT - 2 * MARGIN)
    c.setLineWidth(1)
    c.line(MARGIN, header_bottom, WIDTH - MARGIN, header_bottom)
    c.line(MARGIN, middle_bottom, WIDTH - MARGIN, middle_bottom)

    # Header
    c.setFillColor(colors.black)
    # Auto-fit title within the inner frame
    left_pad = MARGIN + 0.10 * inch
    right_pad = MARGIN + 0.10 * inch
    max_title_width = (WIDTH - left_pad - right_pad)
    draw_centered_autofit(
        c,
        f"TITLE: {data.get('Title', '')}",
        WIDTH / 2,
        HEIGHT - 0.40 * inch,
        font_name="Helvetica-Bold",
        max_size=15,
        min_size=8,
        max_width_pts=max_title_width
    )
    c.setFont("Helvetica", 10)
    c.drawString(0.20 * inch, HEIGHT - 0.60 * inch, f"AUTHOR: {data.get('Author', '')}")
    right_on_sale = f"ON SALE: {data.get('OnSale', '')}".strip()
    if right_on_sale != "ON SALE:":
        c.drawRightString(WIDTH - 0.20 * inch, HEIGHT - 0.60 * inch, right_on_sale)
    c.drawString(0.20 * inch, HEIGHT - 0.80 * inch, f"PUBLISHER: {data.get('Publisher', '')}")
    c.drawRightString(WIDTH - 0.20 * inch, HEIGHT - 0.80 * inch, f"PRINTED IN {data.get('PrintedIn', 'USA')}")

    # Center heading
    c.setFont("Helvetica", 10)
    c.drawCentredString(WIDTH / 2, header_bottom - 0.25 * inch, "BARCODE")
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(WIDTH / 2, header_bottom - 0.65 * inch, "EAN")

    # Lower grid geometry
    INNER_PAD = 0.20 * inch
    COL_GAP = 0.40 * inch
    left_edge = MARGIN + INNER_PAD
    right_edge = WIDTH - (MARGIN + INNER_PAD)
    col_w = (right_edge - left_edge - COL_GAP) / 2.0
    left_x = left_edge
    right_x = left_edge + col_w + COL_GAP

    # Sizes & baselines
    TOP_H, TOP_W = 0.35 * inch, 0.013 * inch
    BOT_H, BOT_W = 0.50 * inch, 0.0125 * inch
    GAP_LABEL_TO_TOPBAR = 0.12 * inch
    BOTTOM_BARS_BASE = MARGIN + 0.18 * inch

    # Small bars (CTN QTY & CTN WGT)
    row1_label_nominal_y = middle_bottom - 0.18 * inch
    row1_bar_base = row1_label_nominal_y - GAP_LABEL_TO_TOPBAR - TOP_H

    qty_val = f"(30) {int(data.get('CTN_QTY', 0))}"
    qty_w = draw_code128_fit(c, qty_val, left_x, row1_bar_base, col_w, TOP_H, TOP_W)
    wgt_val = f"(3401) {int(float(data.get('CTN_WGT', 0))):05d}"
    wgt_w = draw_code128_fit(c, wgt_val, right_x, row1_bar_base, col_w, TOP_H, TOP_W)

    qty_cx = left_x + qty_w / 2.0
    wgt_cx = right_x + wgt_w / 2.0

    c.setFont("Helvetica-Bold", 10)
    cap_y = row1_bar_base + TOP_H + 0.06 * inch
    c.drawCentredString(qty_cx, cap_y, f"CTN QTY: {data.get('CTN_QTY', 0)}")
    c.drawCentredString(wgt_cx, cap_y, f"CTN WGT: {float(data.get('CTN_WGT', 0)):.1f} lbs.")

    c.setFont("Helvetica", 8)
    c.drawCentredString(qty_cx, row1_bar_base - 10, qty_val)
    c.drawCentredString(wgt_cx, row1_bar_base - 10, wgt_val)

    # Big bars (GTIN-14 & Price)
    row3_bar_base = BOTTOM_BARS_BASE

    ai01_val = f"(01) {gtin14_from_isbn13(data.get('ISBN13', ''), '1')}"
    ai01_w = draw_code128_fit(c, ai01_val, left_x, row3_bar_base, col_w, BOT_H, BOT_W)
    price_cents = price_to_cents(data.get("Price", "0"))
    price_val = f"(9012Q) {price_cents}USD"
    price_w = draw_code128_fit(c, price_val, right_x, row3_bar_base, col_w, BOT_H, BOT_W)

    ai01_cx = left_x + ai01_w / 2.0
    price_cx = right_x + price_w / 2.0

    # ISBN block centered over left bottom barcode
    c.setFont("Helvetica", 9)
    ISBN_EXTRA_UP = 0.02 * inch
    isbn_block_y = row3_bar_base + BOT_H + 0.12 * inch + ISBN_EXTRA_UP
    isbn10 = isbn10_from_13(data.get("ISBN13", ""))
    if isbn10:
        c.drawCentredString(ai01_cx, isbn_block_y, f"ISBN-10: {format_isbn10(isbn10)}")
        c.drawCentredString(ai01_cx, isbn_block_y - 0.13 * inch, f"ISBN-13: {format_isbn13(data.get('ISBN13', ''))}")
    else:
        c.drawCentredString(ai01_cx, isbn_block_y, f"ISBN-13: {format_isbn13(data.get('ISBN13', ''))}")

    # COVER PRICE caption centered over right big barcode
    c.setFont("Helvetica-Bold", 10)
    price_caption_y = row3_bar_base + BOT_H + 0.12 * inch
    c.drawCentredString(price_cx, price_caption_y, f"COVER PRICE: ${data.get('Price', '0')} USD")

    # HRI under big bars
    c.setFont("Helvetica", 8)
    c.drawCentredString(ai01_cx, row3_bar_base - 10, ai01_val)
    c.drawCentredString(price_cx, row3_bar_base - 10, price_val)

    c.save()
    return output_path


# ==================== BOOK BARCODE GENERATOR ====================

def generate_book_label(data: dict, output_path: str) -> str:
    """
    Generate Bookland EAN barcode with price add-on (2.25" x 1.10")
    OR Code 128 barcode for custom alphanumeric UPCs

    Args:
        data: Dictionary containing:
            - ISBN13: ISBN-13 (or custom alphanumeric UPC)
            - Price: Cover price (optional, use "" for no price)
            - Currency: Currency code (USD, CAD, GBP, EUR, AUD, NZD) - default USD
            - is_custom_upc: Boolean flag for custom UPC (default: False)
        output_path: Path to save PDF

    Returns:
        Path to generated PDF file
    """
    WIDTH, HEIGHT = 2.25 * inch, 1.10 * inch
    c = canvas.Canvas(output_path, pagesize=(WIDTH, HEIGHT))

    is_custom_upc = data.get("is_custom_upc", False)
    raw_code = data.get("ISBN13", "")
    price_cents = price_to_cents(data.get("Price", ""))
    currency = data.get("Currency", "USD")
    price_text = human_price(price_cents, currency)

    if is_custom_upc:
        # Custom UPC with alphanumeric characters - use Code 128
        upc_code = raw_code.strip().upper()

        # Top line: UPC label
        c.setFont("Helvetica", 8)
        upc_text = f"ISBN {upc_code}"
        c.drawString(0.10 * inch, HEIGHT - 0.29 * inch, upc_text)

        # Price text
        if price_text:
            c.drawRightString(WIDTH - 0.35 * inch, HEIGHT - 0.45 * inch, price_text)

        # Create Code 128 barcode for alphanumeric UPC
        barcode_y = 0.30 * inch
        main_x = 0.10 * inch
        bar_width = draw_code128_fit(c, upc_code, main_x, barcode_y, WIDTH - 0.20 * inch, 0.50 * inch, 0.0104 * inch)

        # Human-readable UPC below barcode
        c.setFont("Helvetica", 9)
        upc_center = main_x + bar_width / 2
        c.drawCentredString(upc_center, barcode_y - 0.10 * inch, upc_code)

        # Price below
        if price_text:
            c.setFont("Helvetica", 8)
            c.drawCentredString(upc_center, 0.10 * inch, price_text)

    else:
        # Standard ISBN-13 - use EAN-13 with price add-on
        isbn = only_digits(raw_code)
        addon_code = addon_from_price(price_cents, currency)

        # Top line: ISBN - preserve full raw_code (includes suffix like "HAT")
        c.setFont("Helvetica", 8)
        isbn_text = f"ISBN {raw_code.strip()}"
        c.drawString(0.10 * inch, HEIGHT - 0.29 * inch, isbn_text)

        # Price text - positioned independently
        if price_text:
            c.drawRightString(WIDTH - 0.35 * inch, HEIGHT - 0.45 * inch, price_text)

        # Create barcodes - use digits only for barcode generation
        main_barcode = eanbc.Ean13BarcodeWidget(
            value=isbn,
            barHeight=0.50 * inch,
            barWidth=0.0104 * inch,
            humanReadable=False
        )

        addon_barcode = eanbc.Ean5BarcodeWidget(
            value=addon_code,
            barHeight=0.48 * inch,
            barWidth=0.0104 * inch,
            humanReadable=False
        )

        # Position barcodes
        main_x = 0.10 * inch
        barcode_y = 0.30 * inch

        # Draw main barcode
        d_main = Drawing()
        d_main.add(main_barcode)
        renderPDF.draw(d_main, c, main_x, barcode_y)

        # Draw addon barcode
        addon_x = main_x + main_barcode.width + 0.03 * inch
        addon_y = barcode_y - 0.14 * inch
        d_addon = Drawing()
        d_addon.add(addon_barcode)
        renderPDF.draw(d_addon, c, addon_x, addon_y)

        # Human-readable numbers
        c.setFont("Helvetica", 9)

        # ISBN number
        isbn_hr = f"{isbn[0]} {isbn[1:7]} {isbn[7:13]}"
        isbn_center = main_x + (main_barcode.width / 2)
        c.drawCentredString(isbn_center, barcode_y - 0.10 * inch, isbn_hr)

        # Price addon
        addon_hr = f"{addon_code[0]} {addon_code[1:]}"
        addon_center = addon_x + (addon_barcode.width / 2) + 0.10 * inch
        c.drawCentredString(addon_center, 0.20 * inch, addon_hr)

    c.showPage()
    c.save()
    return output_path


# ==================== BOOK BARCODE SHEET GENERATOR (30 per page) ====================

def draw_single_book_barcode(c, x_offset, y_offset, data):
    """Draw a single book barcode at the given position for sheet layout"""
    is_custom_upc = data.get("is_custom_upc", False)
    raw_code = data.get("ISBN13", "")
    price_cents = price_to_cents(data.get("Price", ""))
    currency = data.get("Currency", "USD")
    price_text = human_price(price_cents, currency)

    # Barcode dimensions
    LABEL_WIDTH = 2.25 * inch
    LABEL_HEIGHT = 1.10 * inch

    if is_custom_upc:
        # Custom UPC with alphanumeric characters - use Code 128
        upc_code = raw_code.strip().upper()

        # Top line: UPC
        c.setFont("Helvetica", 8)
        upc_text = f"ISBN {upc_code}"
        c.drawString(x_offset + 0.10 * inch, y_offset + LABEL_HEIGHT - 0.29 * inch, upc_text)

        # Price text
        if price_text:
            c.drawRightString(x_offset + LABEL_WIDTH - 0.35 * inch, y_offset + LABEL_HEIGHT - 0.45 * inch, price_text)

        # Create Code 128 barcode
        barcode_y = y_offset + 0.30 * inch
        main_x = x_offset + 0.10 * inch
        bar_width = draw_code128_fit(c, upc_code, main_x, barcode_y, LABEL_WIDTH - 0.20 * inch, 0.50 * inch, 0.0104 * inch)

        # Human-readable UPC below barcode
        c.setFont("Helvetica", 9)
        upc_center = main_x + bar_width / 2
        c.drawCentredString(upc_center, barcode_y - 0.10 * inch, upc_code)

        # Price below
        if price_text:
            c.setFont("Helvetica", 8)
            c.drawCentredString(upc_center, y_offset + 0.10 * inch, price_text)

    else:
        # Standard ISBN-13 - use EAN-13 with price add-on
        isbn = only_digits(raw_code)
        addon_code = addon_from_price(price_cents, currency)

        # Top line: ISBN - preserve full raw_code (includes suffix like "HAT")
        c.setFont("Helvetica", 8)
        isbn_text = f"ISBN {raw_code.strip()}"
        c.drawString(x_offset + 0.10 * inch, y_offset + LABEL_HEIGHT - 0.29 * inch, isbn_text)

        # Price text
        if price_text:
            c.drawRightString(x_offset + LABEL_WIDTH - 0.35 * inch, y_offset + LABEL_HEIGHT - 0.45 * inch, price_text)

        # Create barcodes - use digits only for barcode generation
        main_barcode = eanbc.Ean13BarcodeWidget(
            value=isbn,
            barHeight=0.50 * inch,
            barWidth=0.0104 * inch,
            humanReadable=False
        )

        addon_barcode = eanbc.Ean5BarcodeWidget(
            value=addon_code,
            barHeight=0.48 * inch,
            barWidth=0.0104 * inch,
            humanReadable=False
        )

        # Position barcodes
        main_x = x_offset + 0.10 * inch
        barcode_y = y_offset + 0.30 * inch

        # Draw main barcode
        d_main = Drawing()
        d_main.add(main_barcode)
        renderPDF.draw(d_main, c, main_x, barcode_y)

        # Draw addon barcode
        addon_x = main_x + main_barcode.width + 0.03 * inch
        addon_y = barcode_y - 0.14 * inch
        d_addon = Drawing()
        d_addon.add(addon_barcode)
        renderPDF.draw(d_addon, c, addon_x, addon_y)

        # Human-readable numbers
        c.setFont("Helvetica", 9)

        # ISBN number
        isbn_hr = f"{isbn[0]} {isbn[1:7]} {isbn[7:13]}"
        isbn_center = main_x + (main_barcode.width / 2)
        c.drawCentredString(isbn_center, barcode_y - 0.10 * inch, isbn_hr)

        # Price addon
        addon_hr = f"{addon_code[0]} {addon_code[1:]}"
        addon_center = addon_x + (addon_barcode.width / 2) + 0.10 * inch
        c.drawCentredString(addon_center, y_offset + 0.20 * inch, addon_hr)


def generate_book_label_sheet(data: dict, output_path: str) -> str:
    """
    Generate sheet of 30 book barcodes (3 rows x 10 columns) on Letter paper

    Args:
        data: Dictionary containing:
            - ISBN13: ISBN-13
            - Price: Cover price (optional)
            - Currency: Currency code (default: USD)
        output_path: Path to save PDF

    Returns:
        Path to generated PDF file
    """
    # Letter size page
    PAGE_WIDTH = 8.5 * inch
    PAGE_HEIGHT = 11 * inch

    c = canvas.Canvas(output_path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    # Label dimensions
    LABEL_WIDTH = 2.25 * inch
    LABEL_HEIGHT = 1.10 * inch

    # Layout: 3 ROWS (horizontal) x 10 COLUMNS (vertical)
    ROWS = 3  # across the page
    COLS = 10  # down the page

    # Calculate spacing
    H_MARGIN = 0.25 * inch
    V_MARGIN = 0.25 * inch

    usable_width = PAGE_WIDTH - (2 * H_MARGIN)
    usable_height = PAGE_HEIGHT - (2 * V_MARGIN)

    h_spacing = (usable_width - (ROWS * LABEL_WIDTH)) / (ROWS - 1)
    v_spacing = (usable_height - (COLS * LABEL_HEIGHT)) / (COLS - 1)

    # Draw grid of barcodes
    for col in range(COLS):  # 10 down
        for row in range(ROWS):  # 3 across
            x = H_MARGIN + row * (LABEL_WIDTH + h_spacing)
            y = PAGE_HEIGHT - V_MARGIN - LABEL_HEIGHT - col * (LABEL_HEIGHT + v_spacing)

            draw_single_book_barcode(c, x, y, data)

    c.showPage()
    c.save()
    return output_path


# ==================== TWO-UP CARTON LABEL GENERATOR ====================

BASE_W, BASE_H = 6 * inch, 4 * inch  # Base carton label size

def draw_single_carton_label(c: canvas.Canvas, data: dict):
    """Draw a single carton label at current origin (used for two-up layout)"""
    WIDTH, HEIGHT = BASE_W, BASE_H

    # Frame & dividers
    MARGIN = 0.10 * inch
    header_h, middle_h = 0.95 * inch, 0.85 * inch
    header_bottom = HEIGHT - header_h
    middle_bottom = header_bottom - middle_h

    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(MARGIN, MARGIN, WIDTH - 2 * MARGIN, HEIGHT - 2 * MARGIN)
    c.setLineWidth(1)
    c.line(MARGIN, header_bottom, WIDTH - MARGIN, header_bottom)
    c.line(MARGIN, middle_bottom, WIDTH - MARGIN, middle_bottom)

    # Header
    c.setFillColor(colors.black)
    # Auto-fit title
    left_pad = MARGIN + 0.10 * inch
    right_pad = MARGIN + 0.10 * inch
    max_title_width = (WIDTH - left_pad - right_pad)
    draw_centered_autofit(
        c,
        f"TITLE: {data.get('Title', '')}",
        WIDTH / 2,
        HEIGHT - 0.40 * inch,
        font_name="Helvetica-Bold",
        max_size=15,
        min_size=8,
        max_width_pts=max_title_width
    )

    c.setFont("Helvetica", 10)
    c.drawString(0.20 * inch, HEIGHT - 0.60 * inch, f"AUTHOR: {data.get('Author', '')}")
    right_on_sale = f"ON SALE: {data.get('OnSale', '')}".strip()
    if right_on_sale != "ON SALE:":
        c.drawRightString(WIDTH - 0.20 * inch, HEIGHT - 0.60 * inch, right_on_sale)
    c.drawString(0.20 * inch, HEIGHT - 0.80 * inch, f"PUBLISHER: {data.get('Publisher', '')}")
    c.drawRightString(WIDTH - 0.20 * inch, HEIGHT - 0.80 * inch, f"PRINTED IN {data.get('PrintedIn', 'USA')}")

    # Center heading
    c.setFont("Helvetica", 10)
    c.drawCentredString(WIDTH / 2, header_bottom - 0.25 * inch, "BARCODE")
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(WIDTH / 2, header_bottom - 0.65 * inch, "EAN")

    # Lower grid geometry
    INNER_PAD = 0.20 * inch
    COL_GAP = 0.40 * inch
    left_edge = MARGIN + INNER_PAD
    right_edge = WIDTH - (MARGIN + INNER_PAD)
    col_w = (right_edge - left_edge - COL_GAP) / 2.0
    left_x = left_edge
    right_x = left_edge + col_w + COL_GAP

    # Sizes & baselines
    TOP_H, TOP_W = 0.35 * inch, 0.013 * inch
    BOT_H, BOT_W = 0.50 * inch, 0.0125 * inch
    GAP_LABEL_TO_TOPBAR = 0.12 * inch
    BOTTOM_BARS_BASE = MARGIN + 0.18 * inch

    # Small bars
    row1_label_nominal_y = middle_bottom - 0.18 * inch
    row1_bar_base = row1_label_nominal_y - GAP_LABEL_TO_TOPBAR - TOP_H

    qty_val = f"(30) {int(data.get('CTN_QTY', 0))}"
    qty_w = draw_code128_fit(c, qty_val, left_x, row1_bar_base, col_w, TOP_H, TOP_W)
    wgt_val = f"(3401) {int(float(data.get('CTN_WGT', 0))):05d}"
    wgt_w = draw_code128_fit(c, wgt_val, right_x, row1_bar_base, col_w, TOP_H, TOP_W)

    qty_cx = left_x + qty_w / 2.0
    wgt_cx = right_x + wgt_w / 2.0

    c.setFont("Helvetica-Bold", 10)
    cap_y = row1_bar_base + TOP_H + 0.06 * inch
    c.drawCentredString(qty_cx, cap_y, f"CTN QTY: {data.get('CTN_QTY', 0)}")
    c.drawCentredString(wgt_cx, cap_y, f"CTN WGT: {float(data.get('CTN_WGT', 0)):.1f} lbs.")

    c.setFont("Helvetica", 8)
    c.drawCentredString(qty_cx, row1_bar_base - 10, qty_val)
    c.drawCentredString(wgt_cx, row1_bar_base - 10, wgt_val)

    # Big bars
    row3_bar_base = BOTTOM_BARS_BASE
    ai01_val = f"(01) {gtin14_from_isbn13(data.get('ISBN13', ''), '1')}"
    ai01_w = draw_code128_fit(c, ai01_val, left_x, row3_bar_base, col_w, BOT_H, BOT_W)
    price_cents = price_to_cents(data.get("Price", "0"))
    price_val = f"(9012Q) {price_cents}USD"
    price_w = draw_code128_fit(c, price_val, right_x, row3_bar_base, col_w, BOT_H, BOT_W)

    ai01_cx = left_x + ai01_w / 2.0
    price_cx = right_x + price_w / 2.0

    # ISBN block
    c.setFont("Helvetica", 9)
    ISBN_EXTRA_UP = 0.02 * inch
    isbn_block_y = row3_bar_base + BOT_H + 0.12 * inch + ISBN_EXTRA_UP
    isbn10 = isbn10_from_13(data.get("ISBN13", ""))
    if isbn10:
        c.drawCentredString(ai01_cx, isbn_block_y, f"ISBN-10: {format_isbn10(isbn10)}")
        c.drawCentredString(ai01_cx, isbn_block_y - 0.13 * inch, f"ISBN-13: {format_isbn13(data.get('ISBN13', ''))}")
    else:
        c.drawCentredString(ai01_cx, isbn_block_y, f"ISBN-13: {format_isbn13(data.get('ISBN13', ''))}")

    # Cover price caption
    c.setFont("Helvetica-Bold", 10)
    price_caption_y = row3_bar_base + BOT_H + 0.12 * inch
    c.drawCentredString(price_cx, price_caption_y, f"COVER PRICE: ${data.get('Price', '0')} USD")

    # HRI under big bars
    c.setFont("Helvetica", 8)
    c.drawCentredString(ai01_cx, row3_bar_base - 10, ai01_val)
    c.drawCentredString(price_cx, row3_bar_base - 10, price_val)


def generate_carton_label_twoup(data: dict, output_path: str) -> str:
    """
    Generate 2 carton labels on Letter page (full-bleed, no margins)

    Args:
        data: Dictionary containing carton label data
        output_path: Path to save PDF

    Returns:
        Path to generated PDF file
    """
    PAGE_W, PAGE_H = 8.5 * inch, 11 * inch
    c = canvas.Canvas(output_path, pagesize=(PAGE_W, PAGE_H))

    # Full-bleed: no margins, no center gap
    max_w = PAGE_W
    max_h_each = PAGE_H / 2.0

    # Uniform scale so two labels fit vertically and the width fits page
    sx = max_w / BASE_W
    sy = max_h_each / BASE_H
    scale = min(sx, sy)

    label_w = BASE_W * scale
    label_h = BASE_H * scale

    # Center horizontally; top label flush to top, bottom label flush to bottom
    x_left = (PAGE_W - label_w) / 2.0
    y_bottom_top = PAGE_H - label_h       # top label touches top edge
    y_bottom_bottom = 0                   # bottom label touches bottom edge

    # Draw top label
    c.saveState()
    c.translate(x_left, y_bottom_top)
    c.scale(scale, scale)
    draw_single_carton_label(c, data)
    c.restoreState()

    # Draw bottom label
    c.saveState()
    c.translate(x_left, y_bottom_bottom)
    c.scale(scale, scale)
    draw_single_carton_label(c, data)
    c.restoreState()

    c.save()
    return output_path


# ==================== COMBINED GENERATOR ====================

def generate_labels(data: dict, label_type: str, output_dir: str = "outputs",
                    book_format: str = "both", carton_format: str = "both") -> dict:
    """
    Generate requested label types and return file paths

    Args:
        data: Dictionary with book/shipment data
        label_type: 'book', 'carton', or 'both'
        output_dir: Directory to save PDFs (default: 'outputs')
        book_format: 'single', 'sheet', or 'both' (default: 'both' generates single + sheet)
        carton_format: 'single', 'twoup', or 'both' (default: 'both' generates single + twoup)

    Returns:
        Dictionary with keys containing file paths:
        - 'book_label_single' (if book_format is 'single' or 'both')
        - 'book_label_sheet' (if book_format is 'sheet' or 'both')
        - 'carton_label_single' (if carton_format is 'single' or 'both')
        - 'carton_label_twoup' (if carton_format is 'twoup' or 'both')
    """
    os.makedirs(output_dir, exist_ok=True)

    isbn = digits(data.get("ISBN13", ""))
    base_filename = f"label_{isbn}"

    result = {}

    if label_type in ["book", "both"]:
        # Generate single book label
        if book_format in ["single", "both"]:
            book_path_single = os.path.join(output_dir, f"{base_filename}_book.pdf")
            generate_book_label(data, book_path_single)
            result["book_label_single"] = book_path_single

        # Generate sheet (30 per page)
        if book_format in ["sheet", "both"]:
            book_path_sheet = os.path.join(output_dir, f"{base_filename}_book_sheet.pdf")
            generate_book_label_sheet(data, book_path_sheet)
            result["book_label_sheet"] = book_path_sheet

    if label_type in ["carton", "both"]:
        # Generate single carton label
        if carton_format in ["single", "both"]:
            carton_path_single = os.path.join(output_dir, f"{base_filename}_carton.pdf")
            generate_carton_label(data, carton_path_single)
            result["carton_label_single"] = carton_path_single

        # Generate twoup (2 per page)
        if carton_format in ["twoup", "both"]:
            carton_path_twoup = os.path.join(output_dir, f"{base_filename}_carton_twoup.pdf")
            generate_carton_label_twoup(data, carton_path_twoup)
            result["carton_label_twoup"] = carton_path_twoup

    return result
