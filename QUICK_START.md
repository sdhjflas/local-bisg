# BISG Labels - Quick Start Guide

## 🚀 Getting to Production in 30 Minutes

This guide gets you from code to live production deployment with real Stripe payments.

---

## Prerequisites (5 min)

- [ ] Railway account ([railway.app](https://railway.app))
- [ ] Stripe account ([stripe.com](https://stripe.com)) - verified
- [ ] Google Cloud project with Sheets & Gmail APIs enabled
- [ ] Repository pushed to GitHub

---

## Step 1: Deploy to Railway (5 min)

1. **Connect Repository**
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `BISGLabels.com/bisg-labels`

2. **Railway Auto-Detects**
   - Python buildpack
   - Uses `Procfile` (already configured)
   - Installs from `requirements.txt`

3. **Wait for Build**
   - First build takes ~3-5 minutes
   - Watch logs for completion

---

## Step 2: Configure Environment Variables (10 min)

In Railway dashboard > Variables tab, add:

### Required Variables

```bash
# Flask
FLASK_SECRET_KEY=<generate-new-secret>  # Run: python -c "import secrets; print(secrets.token_hex(32))"
FLASK_ENV=production
PORT=5000

# Stripe (TEST FIRST, then switch to LIVE)
STRIPE_SECRET_KEY=sk_test_YOUR_TEST_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_TEST_SECRET

# Google Sheets
STOCK_SHEET_ID=<your-sheet-id>
FORM_SHEET_ID=<your-sheet-id>
GOOGLE_SHEETS_CREDS={"installed":{...}}  # Paste full JSON on one line

# Gmail
GMAIL_TOKEN={"token":"...","refresh_token":"..."}  # From token generation
SENDER_EMAIL=your-email@domain.com

# Output
LABEL_OUTPUT_DIR=/tmp/bisg-labels

# Security
ALLOWED_ORIGINS=https://app.bisglabels.com,https://bisglabels.com
ENABLE_RATE_LIMITING=True
LOG_LEVEL=INFO
```

### Generate Secrets

```bash
# Flask Secret Key
python -c "import secrets; print(secrets.token_hex(32))"

# Copy output and paste as FLASK_SECRET_KEY
```

---

## Step 3: Configure Stripe Webhook (5 min)

### Test Mode Webhook

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/test/webhooks) (TEST mode)
2. Click "+ Add endpoint"
3. Endpoint URL: `https://your-railway-url.railway.app/webhook`
4. Events: Select `checkout.session.completed`
5. Add endpoint
6. Copy webhook signing secret (starts with `whsec_`)
7. Add to Railway as `STRIPE_WEBHOOK_SECRET`

**Save your Railway URL**: You'll need it for the frontend

---

## Step 4: Test with Test Mode (5 min)

1. **Visit Your App**
   ```
   https://your-railway-url.railway.app
   ```

2. **Fill Out Form**
   - Use test ISBN: `9780985347024`
   - Fill all fields with test data

3. **Test Payment**
   - Card: `4242 4242 4242 4242`
   - Expiry: Any future date (e.g., `12/25`)
   - CVC: Any 3 digits (e.g., `123`)
   - ZIP: Any 5 digits (e.g., `12345`)

4. **Verify Success**
   - Payment succeeds
   - Check Railway logs for webhook receipt
   - Email received with PDF labels

**✅ If everything works, you're ready for live mode!**

---

## Step 5: Switch to Live Mode (5 min)

**⚠️ Only do this when you're ready for real payments!**

Follow the detailed guide: [STRIPE_MIGRATION.md](STRIPE_MIGRATION.md)

### Quick Version

1. In Stripe Dashboard, switch to **Live mode**
2. Get live API keys (Developers > API keys)
3. Create live webhook endpoint
4. Update Railway variables:
   ```
   STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_KEY
   STRIPE_WEBHOOK_SECRET=whsec_YOUR_LIVE_SECRET
   ```
5. Test with small real transaction
6. Refund test transaction
7. Monitor for 24 hours

---

## Step 6: Configure Custom Domain (Optional)

### Railway Domain Setup

1. Railway Dashboard > Settings
2. Add custom domain: `app.bisglabels.com`
3. Add DNS records (Railway provides instructions)
4. Wait for DNS propagation (~10-60 min)
5. Update `ALLOWED_ORIGINS` in Railway variables

---

## Troubleshooting

### App won't start

**Check Railway logs** (Deployments > Latest > View Logs)

Common issues:
- Missing environment variables
- Invalid JSON in Google credentials
- Malformed Stripe keys

### Webhook not working

1. Check Stripe Dashboard > Webhooks
2. Look for failed deliveries
3. Verify webhook URL matches Railway URL
4. Check `STRIPE_WEBHOOK_SECRET` matches

### Emails not sending

1. Verify `GMAIL_TOKEN` is valid
2. Check Gmail API quota
3. Ensure sender email matches Gmail account
4. Check Railway logs for email errors

---

## Next Steps

Once production is running:

1. **Monitor**: Check Railway logs daily for first week
2. **Document**: Keep track of successful deployments
3. **Backup**: Export Google Sheets regularly
4. **Scale**: Upgrade Railway plan if needed
5. **Secure**: Review security settings monthly

---

## Important Files

- [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md) - Full deployment checklist
- [STRIPE_MIGRATION.md](STRIPE_MIGRATION.md) - Detailed Stripe migration guide
- [.env.example](.env.example) - Environment variable template

---

## Support

- **Railway**: https://railway.app/help
- **Stripe**: https://support.stripe.com
- **Google Cloud**: https://cloud.google.com/support

---

**You're all set! 🎉**

Your BISG Labels service is now running in production with:
- ✅ Secure payment processing
- ✅ Automated label generation
- ✅ Email delivery
- ✅ Rate limiting & security
- ✅ Production monitoring

Monitor closely and enjoy your automated label service!
