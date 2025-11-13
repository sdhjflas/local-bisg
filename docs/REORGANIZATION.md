# Codebase Reorganization - October 2025

## Overview

The BISGLabels.com codebase has been reorganized from a flat structure into a modular, maintainable architecture following Python best practices.

## What Changed

### Directory Structure

**Before:**
```
bisg-labels/
├── app.py
├── stripe_handler.py
├── sheets_handler.py
├── label_generator.py
├── email_sender.py
├── validation.py
├── utils.py
├── test_stripe.py
├── test_new_features.py
├── generate_gmail_token.py
├── generate_sheets_token.py
├── index.html
├── credentials.json
├── token.json
├── token.pickle
├── .env
├── README.md
└── (various markdown docs)
```

**After:**
```
bisg-labels/
├── app/                       # Application package
│   ├── main.py               # Entry point (was: app.py)
│   ├── services/             # Business logic
│   │   ├── stripe_service.py    # (was: stripe_handler.py)
│   │   ├── sheets_service.py    # (was: sheets_handler.py)
│   │   ├── label_service.py     # (was: label_generator.py)
│   │   └── email_service.py     # (was: email_sender.py)
│   ├── utils/                # Utilities
│   │   ├── validation.py        # (moved from root)
│   │   └── helpers.py           # (was: utils.py)
│   └── static/               # Frontend
│       └── index.html           # (moved from root)
├── scripts/                   # Utility scripts
│   ├── generate_gmail_token.py  # (moved from root)
│   └── generate_sheets_token.py # (moved from root)
├── tests/                     # Tests
│   ├── test_stripe.py           # (moved from root)
│   └── test_new_features.py     # (moved from root)
├── config/                    # Configuration
│   ├── .env                     # (moved from root)
│   ├── .env.example
│   └── credentials/             # Secure credentials
│       ├── credentials.json     # (moved from root)
│       ├── token.json           # (moved from root)
│       └── token.pickle         # (moved from root)
├── docs/                      # Documentation
│   ├── CLAUDE.md                # (was: claude.md)
│   ├── UPDATE.md
│   ├── CHANGELOG.md
│   ├── REORGANIZATION.md        # (this file)
│   └── reference/               # Reference code
│       ├── Stock-Receipts/      # (was: ../Context/...)
│       ├── Accessions-Transfer/
│       └── label-generators/
├── outputs/                   # Generated PDFs
├── requirements.txt
├── Procfile
├── .gitignore
└── README.md
```

## Key Improvements

### 1. **Modular Architecture**
- **Services Layer**: Business logic separated into focused modules
- **Routes Layer**: Prepared for future endpoint organization
- **Utils Layer**: Shared utilities and validation

### 2. **Security**
- Credentials moved to `config/credentials/` (gitignored)
- Environment files in `config/` directory
- Comprehensive `.gitignore` for sensitive files

### 3. **Documentation**
- All docs consolidated in `docs/`
- Reference implementations in `docs/reference/`
- Clear separation of active code vs. reference code

### 4. **Testing**
- Tests in dedicated `tests/` directory
- Easier to run test suite: `pytest tests/`

### 5. **Deployment**
- Updated `Procfile`: `gunicorn app.main:app`
- Clear entry point: `app/main.py`
- Environment config in `config/` directory

## Migration Guide

### For Local Development

**Old way:**
```bash
python app.py
```

**New way:**
```bash
python app/main.py
```

### For Environment Variables

**Old location:** `.env` in root

**New location:** `config/.env`

**Update your imports:**
```python
# The new main.py automatically loads from config/.env
# No changes needed to your .env file content
```

### For API Credentials

**Old location:** Root directory
- `credentials.json`
- `token.json`
- `token.pickle`

**New location:** `config/credentials/`

These files are automatically detected from the new location.

### For Railway Deployment

**Updated Procfile:**
```
OLD: web: gunicorn app:app
NEW: web: gunicorn app.main:app
```

This change is already committed. Railway will automatically use the new entry point on next deployment.

## What You Need to Do

### 1. Update Local Environment

If you're running locally:

```bash
cd bisg-labels

# Move your credentials if they're still in root
mv credentials.json config/credentials/ 2>/dev/null || true
mv token.json config/credentials/ 2>/dev/null || true
mv token.pickle config/credentials/ 2>/dev/null || true

# Move your .env if it's still in root
mv .env config/ 2>/dev/null || true

# Reinstall dependencies (recommended)
pip install -r requirements.txt

# Run the app with new entry point
python app/main.py
```

### 2. Railway Deployment

**No action needed!** The reorganization is deployment-ready:
- ✅ Procfile updated
- ✅ Import paths corrected
- ✅ Environment variables work from config/
- ✅ Service imports updated

Just push to GitHub and Railway will auto-deploy.

### 3. Stock Receipts Integration

**No changes needed** to your Stock Receipts API calls. The `/create-checkout` endpoint remains identical:

```python
response = requests.post('https://app.bisglabels.com/create-checkout', json={
    'isbn': '9780985347024',
    'date': '10/2/2025',
    'label_type': 'both',
    'customer_type': 'pbs'
})
```

## Old Files

The following files are **duplicates** and can be safely removed once you verify the new structure works:

**In root directory:**
- `app.py` → Now: `app/main.py`
- `stripe_handler.py` → Now: `app/services/stripe_service.py`
- `sheets_handler.py` → Now: `app/services/sheets_service.py`
- `label_generator.py` → Now: `app/services/label_service.py`
- `email_sender.py` → Now: `app/services/email_service.py`
- `validation.py` → Now: `app/utils/validation.py`
- `utils.py` → Now: `app/utils/helpers.py`
- `test_stripe.py` → Now: `tests/test_stripe.py`
- `test_new_features.py` → Now: `tests/test_new_features.py`
- `generate_gmail_token.py` → Now: `scripts/generate_gmail_token.py`
- `generate_sheets_token.py` → Now: `scripts/generate_sheets_token.py`
- `index.html` → Now: `app/static/index.html`

**Cleanup command** (after verifying everything works):
```bash
cd bisg-labels
rm app.py stripe_handler.py sheets_handler.py label_generator.py \
   email_sender.py validation.py utils.py test_stripe.py \
   test_new_features.py generate_gmail_token.py generate_sheets_token.py \
   index.html
```

## Benefits

### For Development
- **Clearer organization**: Find code faster
- **Better imports**: `from app.services import stripe_service`
- **Easier testing**: Isolated modules, clear dependencies
- **Type hints**: Future-ready for better IDE support

### For Deployment
- **Scalability**: Easy to add new routes/services
- **Security**: Credentials properly isolated
- **Maintainability**: Standard Python package structure
- **Documentation**: Everything in `docs/`

### For Collaboration
- **Onboarding**: Clear project structure
- **Standards**: Follows Python best practices
- **Reference code**: Separated from active code
- **Version control**: Better git diffs with organized files

## Testing Checklist

After reorganization, verify:

- [ ] Health check works: `curl http://localhost:5000/health`
- [ ] Checkout creation works
- [ ] Webhook processing works
- [ ] Labels generate correctly
- [ ] Emails send properly
- [ ] Railway deployment succeeds
- [ ] Environment variables load from config/
- [ ] Credentials load from config/credentials/

## Rollback Plan

If needed, the old flat structure is preserved in git history:

```bash
git log --all --oneline | grep "before reorganization"
git checkout <commit-hash>
```

## Questions?

- Check updated [README.md](../README.md)
- Review [docs/CLAUDE.md](CLAUDE.md) for architecture
- Review [docs/UPDATE.md](UPDATE.md) for integration

---

**Reorganization Date:** October 8, 2025
**Status:** Complete ✅
**Backward Compatible:** Yes (old API endpoints unchanged)
