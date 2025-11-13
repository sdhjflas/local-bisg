# Stripe Test to Live Migration Guide

## Overview

This guide walks you through safely switching from Stripe test mode to live mode for production deployment.

## Prerequisites

- [ ] Stripe account verified and activated
- [ ] Bank account connected to Stripe
- [ ] Business details completed in Stripe
- [ ] Test environment working correctly
- [ ] At least one successful test transaction completed

---

## Step 1: Verify Test Mode Works

Before switching to live, ensure everything works in test mode:

### Test Checklist

1. **Create Test Order**
   - Visit your app
   - Fill out order form
   - Proceed to checkout

2. **Complete Test Payment**
   - Use test card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits
   - ZIP: Any 5 digits

3. **Verify Webhook**
   - Check Railway logs for webhook receipt
   - Confirm `checkout.session.completed` event processed
   - Verify no errors in logs

4. **Confirm Label Generation**
   - Labels generated successfully
   - All formats created (single, sheet, twoup)
   - No PDF generation errors

5. **Check Email Delivery**
   - Customer receives email with labels
   - PBS receives email (if PBS customer)
   - Attachments intact and readable

**✅ Only proceed if all tests pass**

---

## Step 2: Prepare Live Stripe Keys

### Get Your Live API Keys

1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. **Switch to Live Mode** (toggle in top right)
3. Navigate to **Developers > API Keys**
4. Copy your **Secret Key** (starts with `sk_live_...`)
   - ⚠️ **Keep this secret** - never commit to git
5. Copy your **Publishable Key** (starts with `pk_live_...`)

### Get Live Webhook Secret

1. In Stripe Dashboard (Live Mode)
2. Go to **Developers > Webhooks**
3. Click **"+ Add endpoint"**
4. Enter details:
   - **Endpoint URL**: `https://app.bisglabels.com/webhook`
   - **Description**: "BISG Labels Production Webhook"
   - **Events**: Select `checkout.session.completed`
5. Click **Add endpoint**
6. Click on the new webhook
7. Click **"Reveal"** next to Signing secret
8. Copy the webhook secret (starts with `whsec_...`)

---

## Step 3: Update Railway Environment Variables

### Critical Variables to Update

1. Open [Railway Dashboard](https://railway.app)
2. Select your BISG Labels project
3. Go to **Variables** tab
4. Update the following:

```
STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_SECRET_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_LIVE_WEBHOOK_SECRET
FLASK_ENV=production
```

### Recommended Additional Variables

```
ALLOWED_ORIGINS=https://app.bisglabels.com,https://bisglabels.com
ENABLE_RATE_LIMITING=True
LOG_LEVEL=INFO
```

### Save and Restart

1. Click **"Update Variables"**
2. Railway will automatically redeploy
3. Wait for deployment to complete (~2-3 minutes)
4. Check deployment logs for startup success

---

## Step 4: Verify Live Mode Configuration

### Check Stripe Dashboard

1. Ensure toggle is set to **"Live"** (not "Test")
2. Verify webhook endpoint shows:
   - ✅ Status: Enabled
   - ✅ URL: `https://app.bisglabels.com/webhook`
   - ✅ Events: `checkout.session.completed`

### Check Application Logs

1. In Railway, open **Deployments**
2. Click latest deployment
3. View logs
4. Look for:
   ```
   ✅ All required environment variables are set
   ⚠️  Using LIVE Stripe key - real charges will occur!
   🚀 Starting BISG Labels Service on port 5000
   ```

**⚠️ If you see "Using LIVE Stripe key" - you're in production mode!**

---

## Step 5: Test with Small Live Transaction

### ⚠️ Warning

**You are now in LIVE mode. Real money will be charged.**

### Recommended First Live Test

1. **Use the smallest amount**: Order a single book label ($50)
2. **Use a real credit card** you control
3. **Monitor in real-time**:
   - Stripe Dashboard > Payments
   - Railway logs
   - Your email inbox

### Test Procedure

1. Visit `https://app.bisglabels.com`
2. Fill out order form with minimal data:
   - Label Type: **Book Label Only** ($50)
   - Use real ISBN or test ISBN: `9780985347024`
   - Fill all required fields
3. Proceed to checkout
4. **Enter real payment details**
5. Complete payment

### Verify Success

Within 1-2 minutes:

- [ ] Payment appears in Stripe Dashboard > Payments
- [ ] Payment status: **Succeeded**
- [ ] Webhook event received (check Stripe > Developers > Events)
- [ ] Railway logs show successful processing
- [ ] Email received with PDF attachments
- [ ] Labels are correct and scannable

### If Test Fails

1. **Immediately**: Check Railway logs for errors
2. **Review**: Stripe Dashboard > Events for webhook failures
3. **Rollback**: If critical, switch back to test mode
4. **Debug**: Identify and fix issue
5. **Retest**: in test mode first

---

## Step 6: Issue Refund for Test Transaction

After successful test:

1. Go to Stripe Dashboard > Payments
2. Find your test payment
3. Click on it
4. Click **"Refund"** button
5. Refund full amount
6. Confirm refund

💡 *Refunds typically take 5-10 business days to appear on your card*

---

## Step 7: Monitor First Week

### Daily Checks (First 7 Days)

- [ ] Review all transactions in Stripe Dashboard
- [ ] Check Railway logs for errors
- [ ] Verify email delivery working
- [ ] Monitor webhook success rate
- [ ] Check for failed payments

### Key Metrics to Watch

| Metric | Expected | Action if Below |
|--------|----------|----------------|
| Webhook Success Rate | >99% | Check webhook logs |
| Email Delivery Rate | 100% | Verify Gmail API quota |
| Payment Success Rate | >95% | Review failed payments |
| Label Generation Rate | 100% | Check for PDF errors |

### Weekly Review

1. Reconcile Stripe payments with email confirmations
2. Review any customer complaints
3. Check for security alerts
4. Update documentation if needed

---

## Rollback Procedure

If you need to switch back to test mode:

### Emergency Rollback

1. **In Railway**: Update `STRIPE_SECRET_KEY` to test key (`sk_test_...`)
2. **In Railway**: Update `STRIPE_WEBHOOK_SECRET` to test webhook secret
3. **In Railway**: Set `FLASK_ENV=development`
4. **Restart**: Deployment will auto-restart
5. **Verify**: Check logs for "TEST" mode confirmation
6. **Notify**: Email affected customers if any payments failed

### Planned Rollback

1. Disable webhook in Stripe Dashboard (Live mode)
2. Update Railway variables to test keys
3. Enable webhook in Stripe Dashboard (Test mode)
4. Test thoroughly before re-enabling live mode

---

## Common Issues & Solutions

### Issue: "Invalid API key provided"

**Cause**: Wrong Stripe key format or test/live mismatch

**Solution**:
1. Verify key starts with `sk_live_` (not `sk_test_`)
2. Check for extra spaces or newlines
3. Ensure you copied the full key
4. Regenerate key in Stripe if needed

### Issue: Webhook signature verification failed

**Cause**: Webhook secret doesn't match

**Solution**:
1. Get webhook secret from Stripe Dashboard > Webhooks
2. Click on your endpoint
3. Reveal and copy the signing secret
4. Update `STRIPE_WEBHOOK_SECRET` in Railway
5. Restart deployment

### Issue: Payments succeed but no labels generated

**Cause**: Webhook not reaching app or processing error

**Solution**:
1. Check Stripe Dashboard > Webhooks > Your endpoint
2. Look for failed deliveries
3. Check Railway logs for webhook errors
4. Verify webhook URL is correct
5. Test webhook in Stripe Dashboard

### Issue: Customer charged but no email

**Cause**: Gmail API quota or authentication issue

**Solution**:
1. Check `GMAIL_TOKEN` is valid
2. Verify Gmail API quota not exceeded
3. Check Railway logs for email errors
4. Manually resend labels if needed

---

## Production Best Practices

### Do's ✅

- Monitor logs daily for first week
- Keep test mode configuration documented
- Test new features in test mode first
- Keep webhook secrets secure
- Review Stripe Dashboard regularly
- Respond to failed payments quickly

### Don'ts ❌

- Never commit live keys to git
- Don't ignore webhook failures
- Don't skip test transaction before going live
- Don't share webhook secrets
- Don't modify production without testing
- Don't disable security features

---

## Emergency Contacts

- **Stripe Support**: https://support.stripe.com/contact
- **Railway Support**: https://railway.app/help
- **Your Team**: [Add your contact info]

---

## Checklist: Complete Migration

Before marking migration complete:

- [ ] Live keys configured in Railway
- [ ] Webhook endpoint verified in Stripe
- [ ] Test live transaction completed successfully
- [ ] Test transaction refunded
- [ ] Monitoring configured
- [ ] Team notified of go-live
- [ ] Rollback plan documented
- [ ] First week monitoring scheduled

**Migration Date**: _________________

**Completed By**: _________________

**Verified By**: _________________

---

**Congratulations! You're now live with Stripe! 🎉**

Remember: Monitor closely for the first week, and don't hesitate to rollback if you encounter issues.
