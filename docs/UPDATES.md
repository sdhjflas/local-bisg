# BISGLabels.com - Latest Updates

## Summary
Updated label generation system with latest layouts and features from the labels repository.

## Changes Implemented

### 1. ✅ Auto-Fit Title Feature (Carton Labels)
- **What**: Automatically shrinks long titles to fit within label boundaries
- **How**: Uses `stringWidth` to dynamically adjust font size (15pt → 8pt min)
- **Fallback**: Truncates with ellipsis (…) if still too long at minimum size
- **Benefit**: Handles extremely long book titles without manual intervention

### 2. ✅ Updated COVER PRICE Caption Positioning
- **What**: Aligned COVER PRICE caption positioning with latest version
- **Change**: Moved from `0.06*inch` to `0.12*inch` above barcode
- **Benefit**: Better visual alignment with ISBN block

### 3. ✅ Book Label Sheet Generator (NEW)
- **What**: Generate 30 book barcodes on a single Letter page
- **Layout**: 3 rows × 10 columns (2.25" × 1.10" each)
- **Use Case**: Publishers needing multiple copies of the same label
- **Format Option**: `book_format: "sheet"`
- **Implementation**: Uses `eanbc.Ean13BarcodeWidget` and `eanbc.Ean5BarcodeWidget`

### 4. ✅ Two-Up Carton Label Generator (NEW)
- **What**: 2 carton labels per Letter page (full-bleed)
- **Layout**: Vertically stacked, no margins/gaps
- **Use Case**: Multi-carton shipments, cost-effective printing
- **Format Option**: `carton_format: "twoup"`
- **Benefit**: Saves paper, reduces printing costs

## Updated API Endpoints

### POST `/create-checkout`

**New Optional Parameters:**
```json
{
  "isbn": "9780985347024",
  "date": "10/2/2025",
  "label_type": "both",
  "customer_type": "pbs",
  "book_format": "single",   // NEW: "single" or "sheet" (default: "single")
  "carton_format": "single"  // NEW: "single" or "twoup" (default: "single")
}
```

### Label Format Options

| Parameter | Values | Description |
|-----------|--------|-------------|
| `book_format` | `single` | One 2"×1.25" label per page (default) |
| | `sheet` | 30 labels on Letter page (3×10 grid) |
| `carton_format` | `single` | One 6"×4" label per page (default) |
| | `twoup` | Two 6"×4" labels on Letter page |

## Updated Functions

### `label_generator.py`

**New Functions:**
- `draw_centered_autofit()` - Auto-fit text to specified width
- `draw_single_book_barcode()` - Draw individual barcode for sheet layout
- `generate_book_label_sheet()` - Generate 30-up book label sheet
- `draw_single_carton_label()` - Reusable carton label drawer
- `generate_carton_label_twoup()` - Generate 2-up carton labels

**Updated Functions:**
- `generate_carton_label()` - Now uses auto-fit title
- `generate_labels()` - Added `book_format` and `carton_format` parameters

### `stripe_handler.py`

**Updated Functions:**
- `create_checkout_session()` - Added `book_format` and `carton_format` parameters
- `handle_payment_success()` - Extracts format options from metadata

### `app.py`

**Updated Endpoints:**
- `/create-checkout` - Accepts and passes format options
- `/webhook` - Uses format options when generating labels

## Testing

All features tested successfully:

```
✅ Single book label generation
✅ Book label sheet (30 per page)
✅ Single carton label (with auto-fit title)
✅ Two-up carton label (2 per page)
✅ Combined generation (both label types with different formats)
```

Test files available in: `bisg-labels/test_outputs/`

## Pricing

Pricing remains unchanged:
- Book labels only: $50
- Carton labels only: $50
- Both labels: $100

*Note: Format options (sheet vs single, twoup vs single) do not affect pricing*

## Migration Notes

**Backwards Compatible**: All changes are backwards compatible. Existing API calls without the new parameters will default to `"single"` format for both label types.

**Stock Receipts Integration**: The stock receipts program can now optionally specify format preferences:

```python
response = requests.post('https://app.bisglabels.com/create-checkout', json={
    'isbn': '9780985347024',
    'date': '10/2/2025',
    'label_type': 'both',
    'customer_type': 'pbs',
    'book_format': 'sheet',    # Optional: for bulk printing
    'carton_format': 'twoup'   # Optional: for multi-carton shipments
})
```

## Files Modified

- ✅ `bisg-labels/label_generator.py` - Added new generators and auto-fit
- ✅ `bisg-labels/stripe_handler.py` - Added format parameters
- ✅ `bisg-labels/app.py` - Updated endpoints

## Example Use Cases

### 1. Publisher Receives 10-Carton Shipment
```json
{
  "label_type": "carton",
  "carton_format": "twoup",
  "isbn": "9780985347024"
}
```
**Result**: 5 pages with 2 labels each = 10 labels total

### 2. Publisher Needs Labels for 30 Books
```json
{
  "label_type": "book",
  "book_format": "sheet",
  "isbn": "9780985347024"
}
```
**Result**: 1 page with 30 labels

### 3. Standard Single Shipment
```json
{
  "label_type": "both",
  "isbn": "9780985347024"
}
```
**Result**: 1 book label + 1 carton label (original behavior)

---

**Updated**: October 6, 2025
**Version**: 1.1.0
**Status**: ✅ All features tested and working
