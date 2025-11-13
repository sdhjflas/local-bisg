# make_labels_twoup_fullbleed.py — 2 labels per Letter page, full-bleed (no margins, no center line)
# Run:  python make_labels_twoup_fullbleed.py

import os, re
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth  # <— for auto-fit

OUTPUT_PATH = r"C:\Users\SageJ\Documents\labels\output_labels_2up_fullbleed.pdf"

# -------- ORDER DATA (sample) --------
data = {
    "Title": "THE SUFI MESSAGE OF HAZRAT INAYAT KHAN VOL. 7 CENTENNIAL EDITION",
    "Author": "Hazrat Inayat Khan",
    "Publisher": "OMEGA PUB",
    "OnSale": "",
    "PrintedIn": "USA",
    "CTN_QTY": "20",
    "CTN_WGT": "30",
    "ISBN13": "9781941810521",
    "Price": "36.00",
}

# -------- Helpers --------
def digits(s): return re.sub(r"\D", "", s or "")

def isbn10_from_13(isbn13):
    d = digits(isbn13)
    if len(d) != 13 or not d.startswith("978"):
        return None
    core9 = d[3:12]
    total = sum((10 - i) * int(core9[i]) for i in range(9))
    chk = 11 - (total % 11)
    return core9 + ("X" if chk == 10 else "0" if chk == 11 else str(chk))

def format_isbn13(isbn13):
    d = digits(isbn13)
    return f"{d[0:3]}-{d[3]}-{d[4:7]}-{d[7:12]}-{d[12]}" if len(d)==13 else isbn13

def format_isbn10(isbn10):
    return f"{isbn10[0]}-{isbn10[1:4]}-{isbn10[4:9]}-{isbn10[9]}" if isbn10 and len(isbn10)==10 else isbn10

def price_to_cents(price_str):
    try: return int(round(float(price_str) * 100))
    except: return 0

def gs1_check_digit(num_without_check: str) -> str:
    s = 0
    for i, ch in enumerate(num_without_check[::-1]):
        s += (3 if i % 2 == 0 else 1) * int(ch)
    return str((10 - (s % 10)) % 10)

def gtin14_from_isbn13(isbn13: str, indicator: str = "1") -> str:
    d = digits(isbn13)
    if len(d) != 13: d = (d + "0"*13)[:13]
    body13 = indicator + d[:12]
    return body13 + gs1_check_digit(body13)

def fit_scale_x(natural_w, max_w):
    if not natural_w or natural_w <= 0: return 1.0
    return min(1.0, max_w / float(natural_w))

def draw_code128_fit(c: canvas.Canvas, value: str, x_left: float, base_y: float,
                     col_width: float, bar_h: float, narrow_bar: float):
    """Draw Code128 scaled to fit X; return scaled width for centering captions/HRI."""
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

# --- title auto-fit helper ---
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

# -------- Single-label drawer (same geometry) --------
BASE_W, BASE_H = 6*inch, 4*inch  # logical size the label is designed for

def draw_single_label(c: canvas.Canvas, data: dict):
    WIDTH, HEIGHT = BASE_W, BASE_H

    # Frame & dividers
    MARGIN = 0.10*inch
    header_h, middle_h = 0.95*inch, 0.85*inch
    header_bottom = HEIGHT - header_h
    middle_bottom = header_bottom - middle_h

    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(MARGIN, MARGIN, WIDTH-2*MARGIN, HEIGHT-2*MARGIN)
    c.setLineWidth(1)
    c.line(MARGIN, header_bottom, WIDTH-MARGIN, header_bottom)
    c.line(MARGIN, middle_bottom, WIDTH-MARGIN, middle_bottom)

    # Header
    c.setFillColor(colors.black)
    # auto-fit title within the inner frame (leave extra padding so it's not touching)
    left_pad  = MARGIN + 0.10*inch
    right_pad = MARGIN + 0.10*inch
    max_title_width = (WIDTH - left_pad - right_pad)
    draw_centered_autofit(
        c,
        f"TITLE: {data['Title']}",
        WIDTH/2,
        HEIGHT-0.40*inch,
        font_name="Helvetica-Bold",
        max_size=15,
        min_size=8,
        max_width_pts=max_title_width
    )

    c.setFont("Helvetica", 10)
    c.drawString(0.20*inch, HEIGHT-0.60*inch, f"AUTHOR: {data['Author']}")
    right_on_sale = f"ON SALE: {data['OnSale']}".strip()
    if right_on_sale != "ON SALE:":
        c.drawRightString(WIDTH-0.20*inch, HEIGHT-0.60*inch, right_on_sale)
    c.drawString(0.20*inch, HEIGHT-0.80*inch, f"PUBLISHER: {data['Publisher']}")
    c.drawRightString(WIDTH-0.20*inch, HEIGHT-0.80*inch, f"PRINTED IN {data['PrintedIn']}")

    # Center heading
    c.setFont("Helvetica", 10)
    c.drawCentredString(WIDTH/2, header_bottom-0.25*inch, "BARCODE")
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(WIDTH/2, header_bottom-0.65*inch, "EAN")

    # Lower grid geometry
    INNER_PAD = 0.20*inch
    COL_GAP   = 0.40*inch
    left_edge  = MARGIN + INNER_PAD
    right_edge = WIDTH  - (MARGIN + INNER_PAD)
    col_w      = (right_edge - left_edge - COL_GAP)/2.0
    left_x     = left_edge
    right_x    = left_edge + col_w + COL_GAP

    # Sizes & baselines
    TOP_H, TOP_W = 0.35*inch, 0.013*inch
    BOT_H, BOT_W = 0.50*inch, 0.0125*inch
    GAP_LABEL_TO_TOPBAR = 0.12*inch
    BOTTOM_BARS_BASE    = MARGIN + 0.18*inch

    # Small bars
    row1_label_nominal_y = middle_bottom - 0.18*inch
    row1_bar_base        = row1_label_nominal_y - GAP_LABEL_TO_TOPBAR - TOP_H

    qty_val = f"(30) {int(data['CTN_QTY'])}"
    qty_w   = draw_code128_fit(c, qty_val, left_x,  row1_bar_base, col_w, TOP_H, TOP_W)
    wgt_val = f"(3401) {int(float(data['CTN_WGT'])):05d}"
    wgt_w   = draw_code128_fit(c, wgt_val, right_x, row1_bar_base, col_w, TOP_H, TOP_W)

    qty_cx  = left_x  + qty_w/2.0
    wgt_cx  = right_x + wgt_w/2.0

    c.setFont("Helvetica-Bold", 10)
    cap_y = row1_bar_base + TOP_H + 0.06*inch
    c.drawCentredString(qty_cx, cap_y, f"CTN QTY: {data['CTN_QTY']}")
    c.drawCentredString(wgt_cx, cap_y, f"CTN WGT: {float(data['CTN_WGT']):.1f} lbs.")

    c.setFont("Helvetica", 8)
    c.drawCentredString(qty_cx, row1_bar_base - 10, qty_val)
    c.drawCentredString(wgt_cx, row1_bar_base - 10, wgt_val)

    # Big bars
    row3_bar_base = BOTTOM_BARS_BASE
    ai01_val = f"(01) {gtin14_from_isbn13(data['ISBN13'], '1')}"
    ai01_w   = draw_code128_fit(c, ai01_val, left_x,  row3_bar_base, col_w, BOT_H, BOT_W)
    price_cents = price_to_cents(data["Price"])
    price_val   = f"(9012Q) {price_cents}USD"
    price_w     = draw_code128_fit(c, price_val, right_x, row3_bar_base, col_w, BOT_H, BOT_W)

    ai01_cx  = left_x  + ai01_w/2.0
    price_cx = right_x + price_w/2.0

    # ISBN block
    c.setFont("Helvetica", 9)
    ISBN_EXTRA_UP = 0.02 * inch
    isbn_block_y = row3_bar_base + BOT_H + 0.12*inch + ISBN_EXTRA_UP
    isbn10 = isbn10_from_13(data["ISBN13"])
    if isbn10:
        c.drawCentredString(ai01_cx, isbn_block_y,                 f"ISBN-10: {format_isbn10(isbn10)}")
        c.drawCentredString(ai01_cx, isbn_block_y - 0.13*inch,     f"ISBN-13: {format_isbn13(data['ISBN13'])}")
    else:
        c.drawCentredString(ai01_cx, isbn_block_y,                 f"ISBN-13: {format_isbn13(data['ISBN13'])}")

    # Cover price caption
    c.setFont("Helvetica-Bold", 10)
    PRICE_CAPTION_Y = row3_bar_base + BOT_H + 0.12*inch
    c.drawCentredString(price_cx, PRICE_CAPTION_Y, f"COVER PRICE: ${data['Price']} USD")

    # HRI under big bars
    c.setFont("Helvetica", 8)
    c.drawCentredString(ai01_cx,  row3_bar_base - 10, ai01_val)
    c.drawCentredString(price_cx, row3_bar_base - 10, price_val)

# -------- Compose two-up full-bleed on Letter --------
def make_two_up_fullbleed(output_path=OUTPUT_PATH):
    PAGE_W, PAGE_H = 8.5*inch, 11*inch
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
    y_bottom_top    = PAGE_H - label_h       # top label touches top edge
    y_bottom_bottom = 0                      # bottom label touches bottom edge

    # Draw top label
    c.saveState()
    c.translate(x_left, y_bottom_top)
    c.scale(scale, scale)
    draw_single_label(c, data)
    c.restoreState()

    # Draw bottom label
    c.saveState()
    c.translate(x_left, y_bottom_bottom)
    c.scale(scale, scale)
    draw_single_label(c, data)
    c.restoreState()

    c.save()
    print(f"✅ 2-up full-bleed sheet saved to {output_path}")
    print(f"   Label size on page: {label_w/inch:.2f}\" × {label_h/inch:.2f}\" (scaled from 6\"×4\")")

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    make_two_up_fullbleed()
