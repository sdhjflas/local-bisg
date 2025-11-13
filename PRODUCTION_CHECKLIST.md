# Production Deployment Checklist

## Pre-Deployment Checks

### 1. Environment Variables (Railway Dashboard)

- [ ] `FLASK_SECRET_KEY` - Strong secret key generated
- [ ] `FLASK_ENV` - Set to `production`
- [ ] `STRIPE_SECRET_KEY` - **LIVE** key (`sk_live_...`)
- [ ] `STRIPE_WEBHOOK_SECRET` - Live webhook secret from Stripe dashboard
- [ ] `GOOGLE_SHEETS_CREDS` - Valid JSON credentials
- [ ] `STOCK_SHEET_ID` - Correct sheet ID
- [ ] `FORM_SHEET_ID` - Correct sheet ID
- [ ] `GMAIL_TOKEN` - Valid Gmail API token
- [ ] `SENDER_EMAIL` - Correct sender email address
- [ ] `ALLOWED_ORIGINS` - Set to `https://app.bisglabels.com,https://bisglabels.com`

### 2. Stripe Configuration

- [ ] Webhook endpoint configured in Stripe: `https://app.bisglabels.com/webhook`
- [ ] Webhook events enabled: `checkout.session.completed`
- [ ] Test webhook delivery works
- [ ] Pricing matches: Book=$50, Carton=$50, Both=$100
- [ ] Live mode enabled in Stripe dashboard
- [ ] Payment methods configured (credit cards enabled)

### 3. Google Services

- [ ] Gmail API enabled for project
- [ ] Google Sheets API enabled
- [ ] OAuth consent screen configured
- [ ] Service account has access to sheets
- [ ] Test email sending works

### 4. Security

- [ ] Rate limiting enabled (`ENABLE_RATE_LIMITING=True`)
- [ ] CORS configured for production domains only
- [ ] No sensitive data in console.log
- [ ] HTTPS enforced
- [ ] Security headers enabled (Talisman)
- [ ] Input sanitization active
- [ ] Honeypot field in frontend form

### 5. Frontend

- [ ] API URL points to production (`https://app.bisglabels.com`)
- [ ] No test/debug code active
- [ ] All links functional
- [ ] Mobile responsive
- [ ] Form validation working
- [ ] Error messages user-friendly

### 6. Testing

- [ ] Health check endpoint works: `GET /health`
- [ ] Frontend loads correctly
- [ ] Can create test checkout session
- [ ] Webhook receives events properly
- [ ] Labels generate correctly
- [ ] Emails send successfully
- [ ] Both customer types work (PBS & Direct)
- [ ] All label formats generate (single, sheet, twoup)

### 7. Monitoring & Logging

- [ ] Log level set appropriately (`INFO` or `WARNING`)
- [ ] Request logging enabled
- [ ] Error tracking configured (optional: Sentry)
- [ ] Railway deployment logs visible
- [ ] Stripe webhook logs monitored

## Deployment Steps

### Step 1: Update Dependencies

```bash
# On your local machine
cd bisg-labels
pip install -r requirements.txt
```

### Step 2: Set Railway Environment Variables

1. Go to Railway dashboard
2. Select your project
3. Click "Variables" tab
4. Add/update all environment variables from checklist above
5. **IMPORTANT**: Use LIVE Stripe keys for production

### Step 3: Deploy to Railway

```bash
# Railway will auto-deploy from git push, or manually trigger:
# Push your latest changes
git add .
git commit -m "Production-ready deployment with security enhancements"
git push origin main
```

### Step 4: Configure Stripe Webhook

1. Go to [Stripe Dashboard > Webhooks](https://dashboard.stripe.com/webhooks)
2. Click "+ Add endpoint"
3. Endpoint URL: `https://app.bisglabels.com/webhook`
4. Events to send: Select `checkout.session.completed`
5. Copy the **Signing secret** (starts with `whsec_`)
6. Add to Railway as `STRIPE_WEBHOOK_SECRET`

### Step 5: Test in Production

1. Visit `https://app.bisglabels.com`
2. Fill out the order form with test data
3. Use [Stripe test card](https://stripe.com/docs/testing): `4242 4242 4242 4242`
4. Verify:
   - Payment succeeds
   - Webhook received
   - Labels generated
   - Email sent
5. Check Railway logs for errors

### Step 6: Go Live

1. Switch Stripe to Live mode in dashboard
2. Update `STRIPE_SECRET_KEY` in Railway to live key (`sk_live_...`)
3. Update `STRIPE_WEBHOOK_SECRET` to live webhook secret
4. Restart Railway deployment
5. Test with real payment (small amount)
6. Monitor for 24 hours

## Post-Deployment

### Immediate Actions

- [ ] Monitor Railway logs for errors
- [ ] Check Stripe dashboard for payments
- [ ] Verify email delivery
- [ ] Test from multiple devices/browsers
- [ ] Set up uptime monitoring (optional)

### Ongoing Maintenance

- [ ] Weekly log review
- [ ] Monthly security updates
- [ ] Stripe reconciliation
- [ ] Backup Google Sheets regularly
- [ ] Monitor rate limiting (adjust if needed)

## Rollback Plan

If issues occur:

1. **Immediate**: Switch Stripe back to test mode
2. **In Railway**: Revert to previous deployment
3. **Environment**: Restore previous environment variables
4. **Notify**: Email customers if payments affected
5. **Debug**: Review logs to identify issue
6. **Fix**: Apply fix in development first
7. **Test**: Thoroughly test before re-deploying

## Common Issues & Solutions

### Issue: Webhook not receiving events

**Solution**:
- Check webhook URL in Stripe dashboard
- Verify `STRIPE_WEBHOOK_SECRET` matches Stripe
- Check Railway logs for signature verification errors
- Test webhook manually in Stripe dashboard

### Issue: Emails not sending

**Solution**:
- Verify `GMAIL_TOKEN` is valid and not expired
- Check Gmail API quota
- Review email service logs
- Ensure sender email matches authorized account

### Issue: "Missing environment variables" error

**Solution**:
- Verify all required vars in Railway dashboard
- Check for typos in variable names
- Ensure JSON variables are single-line strings
- Restart deployment after adding variables

### Issue: Rate limit errors

**Solution**:
- Increase limits in environment variables
- Check for bot traffic
- Review access logs for unusual patterns
- Consider Redis-based rate limiting for scale

## Support Contacts

- **Railway Support**: https://railway.app/help
- **Stripe Support**: https://support.stripe.com
- **Google Cloud Support**: https://cloud.google.com/support

---

**Last Updated**: 2025-10-08
**Next Review**: Before each deployment
