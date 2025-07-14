# Final Deployment Steps for InventorySync

## ✅ Current Status
- ✅ App deployed to Railway: https://inventorysync-production.up.railway.app
- ✅ Sentry configured for error tracking
- ✅ All environment variables set
- ✅ Dockerfile configured for production

## 🌐 Custom Domain Setup

### 1. Add Custom Domain in Railway Dashboard
1. Go to your Railway project: https://railway.com/project/de832abe-3d73-40ef-9fc5-c4054e8af06c
2. Click on your service (Inventorysync)
3. Go to "Settings" → "Domains"
4. Click "Add Custom Domain"
5. Enter: `inventorysync.prestigecorp.au`
6. Railway will provide DNS records

### 2. Configure DNS Records
Add these records to your domain's DNS (prestigecorp.au):

```
Type: CNAME
Name: inventorysync
Value: inventorysync-production.up.railway.app
TTL: 300
```

Or if Railway provides an A record:
```
Type: A
Name: inventorysync
Value: [Railway's IP]
TTL: 300
```

### 3. Update Shopify App URLs
Once DNS propagates (5-30 minutes), update in Shopify Partners Dashboard:

1. Go to: https://partners.shopify.com/4377870/apps/[your-app-id]/edit
2. Update these URLs:
   - App URL: `https://inventorysync.prestigecorp.au`
   - Redirect URLs:
     ```
     https://inventorysync.prestigecorp.au/api/v1/auth/callback
     https://inventorysync.prestigecorp.au/auth/callback
     ```

## 🧪 Testing Your Deployment

### 1. Check API Health
```bash
curl https://inventorysync-production.up.railway.app/health
```

### 2. Check Metrics
```bash
curl https://inventorysync-production.up.railway.app/metrics
```

### 3. Test Sentry Integration
```bash
curl https://inventorysync-production.up.railway.app/test-sentry
```
(This will create a test error in Sentry)

## 📋 Pre-Submission Checklist

### Technical Requirements ✅
- [x] OAuth flow implemented
- [x] GDPR webhooks configured
- [x] Webhook signature verification
- [x] Rate limiting enabled
- [x] HTTPS enabled (via Railway)
- [x] Error tracking (Sentry)
- [x] Structured logging

### Remaining Tasks
1. [ ] Create app listing assets:
   - [ ] App icon (1024x1024px)
   - [ ] Banner image (1920x1080px)
   - [ ] Screenshots (min 3, 1280x800px)

2. [ ] Write app listing content:
   - [ ] App description
   - [ ] Key benefits
   - [ ] Pricing details

3. [ ] Test on development store:
   - [ ] Install flow
   - [ ] All features working
   - [ ] Webhook delivery

## 🚀 Submission Process

1. **Create Development Store** (for testing)
   ```
   1. Go to Partners Dashboard
   2. Click "Stores" → "Add store"
   3. Choose "Development store"
   4. Install your app for testing
   ```

2. **Submit for Review**
   ```
   1. Complete all app listing fields
   2. Upload assets
   3. Add test instructions for reviewers
   4. Click "Submit for review"
   ```

## 📊 Monitoring Your App

### Sentry Dashboard
- URL: https://prestige-corp.sentry.io
- Monitor errors and performance
- Set up alerts for critical issues

### Railway Metrics
- URL: https://railway.com/project/de832abe-3d73-40ef-9fc5-c4054e8af06c
- Monitor deployments
- Check resource usage
- View logs

### Health Endpoints
- Health: https://inventorysync.prestigecorp.au/health
- Status: https://inventorysync.prestigecorp.au/health/status
- Metrics: https://inventorysync.prestigecorp.au/metrics

## 🎉 Congratulations!

Your app is now:
- ✅ Deployed to production
- ✅ Monitored with Sentry
- ✅ Ready for Shopify marketplace submission

Next steps:
1. Set up custom domain DNS
2. Create marketing assets
3. Submit to Shopify for review

Estimated review time: 5-10 business days

---

**Support**: If you encounter any issues, check:
- Railway logs: `railway logs`
- Sentry dashboard for errors
- API health endpoint
