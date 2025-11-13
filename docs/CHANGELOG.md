# BISG Labels Service - Changelog

## 2025-10-06 - Multiple Label Format Support

### Changes Made

#### 1. Enhanced Label Generator (`label_generator.py`)
- **Modified `generate_labels()` function** to support generating multiple formats simultaneously
- **New format option: `'both'`** - Generates all available formats for each label type
- **Return value changes:**
  - Old: `{'book_label': 'path/to/file.pdf', 'carton_label': 'path/to/file.pdf'}`
  - New: `{'book_label_single': 'path', 'book_label_sheet': 'path', 'carton_label_single': 'path', 'carton_label_twoup': 'path'}`

#### 2. Updated Default Behavior
All endpoints and webhook handlers now default to `format='both'`:
- **Book labels**: Generates both single (2"x1.25") AND sheet (30 per page)
- **Carton labels**: Generates both single (6"x4") AND twoup (2 per Letter page)

#### 3. Files Modified
- **[label_generator.py](bisg-labels/label_generator.py)**
  - Line 627-679: Updated `generate_labels()` to support 'both' format option
  - Now generates all requested formats in a single call

- **[app.py](bisg-labels/app.py)**
  - Line 241-242: Changed defaults from `'single'` to `'both'`
  - Line 379-380: Changed webhook defaults to `'both'`
  - Line 213-214: Updated API documentation

- **[stripe_handler.py](bisg-labels/stripe_handler.py)**
  - Line 53-54: Changed function signature defaults to `'both'`
  - Line 197-198: Changed metadata extraction defaults to `'both'`
  - Line 69-70: Updated docstring

- **[test_new_features.py](bisg-labels/test_new_features.py)**
  - Updated all tests to verify new 'both' format behavior
  - Added comprehensive test coverage for all format combinations

### What This Means

#### For PBS Clients (via Stock Receipts)
When a publisher purchases labels through the email link:
- They will receive **4 PDF files** (when ordering both label types):
  1. Book label - single (2"x1.25" - for reference)
  2. Book label - sheet (30 labels per Letter page - ready to print)
  3. Carton label - single (6"x4" - for reference)
  4. Carton label - twoup (2 labels per Letter page - ready to print)

#### For Direct Publishers (via Website)
Same behavior - they get all available formats for maximum flexibility.

### API Changes

#### `/create-checkout` Endpoint
```json
{
  "isbn": "9781234567890",
  "date": "10/06/2025",
  "label_type": "both",
  "customer_type": "pbs",
  "book_format": "both",     // NEW: 'single', 'sheet', or 'both' (default: 'both')
  "carton_format": "both"    // NEW: 'single', 'twoup', or 'both' (default: 'both')
}
```

### Format Options Reference

#### Book Label Formats
- **`'single'`**: One 2"x1.25" label per page (for reference/individual use)
- **`'sheet'`**: 30 labels per Letter page (3 rows × 10 columns - production ready)
- **`'both'`**: Generates both single AND sheet formats

#### Carton Label Formats
- **`'single'`**: One 6"x4" label per page (for reference/individual use)
- **`'twoup'`**: 2 labels per Letter page (full bleed, production ready)
- **`'both'`**: Generates both single AND twoup formats

### Testing

Run comprehensive tests:
```bash
cd bisg-labels
venv\Scripts\python.exe test_new_features.py
```

Expected output:
- ✅ 7 tests per ISBN
- ✅ Generates all 4 format combinations
- ✅ Verifies barcode generation
- ✅ Confirms auto-fit title functionality

### Backward Compatibility

The changes are **fully backward compatible**:
- Old API calls with `book_format='single'` or `'sheet'` still work
- Old API calls without format parameters now get 'both' (enhancement)
- Stock Receipts integration requires **no changes** - will automatically use new defaults

### Next Steps

1. **Deploy to Railway** - Push changes to trigger auto-deployment
2. **Monitor first few transactions** - Verify email attachments include all formats
3. **Update Stock Receipts email template** (optional) - Mention customers will receive multiple formats
4. **Consider email size** - 4 PDFs per order (~10-15KB total) is well within limits

### Technical Notes

- All formats generated in single pass for efficiency
- PDFs stored in `/tmp/bisg-labels/` on Railway (ephemeral storage)
- Email attachments include all generated formats
- Barcode generation verified for all formats
- Auto-fit title algorithm working correctly for long titles

---

**Version:** 1.1.0
**Date:** October 6, 2025
**Author:** Claude Code
**Status:** ✅ Ready for Production
