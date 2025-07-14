# Monitoring Setup Guide

## Option 1: Deploy to Railway

### 1. Add Monitoring Services to Railway

```bash
# In your Railway project dashboard:
# 1. Click "New Service"
# 2. Select "Empty Service" 
# 3. Name it "alertmanager"
# 4. Add these environment variables:
#    - SLACK_API_URL = your-slack-webhook-url
# 5. Deploy using the Docker image:
#    - Image: prom/alertmanager:latest
#    - Start Command: --config.file=/etc/alertmanager/alertmanager.yml
```

### 2. Configure via Railway CLI

```bash
# Add AlertManager service
railway service create alertmanager

# Set environment variables
railway variables set SLACK_API_URL="your-slack-webhook-url" -s alertmanager

# Deploy the service
railway up -s alertmanager
```

## Option 2: Use Managed Services (Recommended for Production)

### 1. **Grafana Cloud** (Free tier available)
- Sign up at: https://grafana.com/products/cloud/
- Includes Prometheus, Grafana, and AlertManager
- No infrastructure to manage

### 2. **Better Stack** (formerly Logtail)
- Sign up at: https://betterstack.com/
- Excellent for logs and alerts
- Great Slack integration

### 3. **Sentry** (Already configured)
- For error tracking and performance monitoring
- Add alert rules in Sentry dashboard
- Configure Slack integration in Sentry settings

## Setting Up Slack Notifications with Sentry

Since you already have Sentry configured, this is the easiest option:

1. **In Sentry Dashboard:**
   - Go to Settings → Integrations
   - Search for "Slack"
   - Click "Install" or "Configure"
   - Authorize with your Slack workspace
   - Select channels for notifications

2. **Create Alert Rules:**
   - Go to Alerts → Create Alert Rule
   - Choose "Issue Alert" or "Metric Alert"
   - Set conditions (e.g., error rate > 5%)
   - Add Slack as notification action
   - Select your channel (#alerts-critical)

3. **Test the Integration:**
   ```python
   # Add this temporary endpoint to test
   @app.get("/test-sentry-alert")
   async def test_sentry():
       # This will trigger a Sentry alert
       raise Exception("Test alert for Slack integration")
   ```

## Quick Setup with Railway + Sentry

Since you're deploying to Railway and already have Sentry:

1. **Set Sentry Environment Variables in Railway:**
   ```bash
   railway variables set SENTRY_DSN="your-sentry-dsn"
   railway variables set ENABLE_SENTRY="true"
   railway variables set SENTRY_ENVIRONMENT="production"
   ```

2. **Configure Slack in Sentry:**
   - Log into your Sentry account
   - Go to Settings → Integrations → Slack
   - Add your Slack workspace
   - Configure alert channels

3. **Create Alert Rules in Sentry:**
   ```
   - High Error Rate: > 10 errors in 5 minutes → #alerts-critical
   - Performance Issues: P95 > 3s → #alerts-warning  
   - New Issues: First occurrence → #alerts-warning
   ```

## Testing Your Alerts

### 1. Test Slack Webhook (if using webhooks)
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Hello from InventorySync Monitoring!"}' \
  YOUR_SLACK_WEBHOOK_URL
```

### 2. Test via API endpoint
```bash
# Trigger a test error
curl https://your-api.railway.app/test-sentry-alert
```

### 3. Monitor Real Metrics
- API response time > 2s
- Error rate > 5%
- Database connection failures
- Memory usage > 90%

## Environment Variables for Railway

Add these to your Railway backend service:

```env
# Monitoring
SENTRY_DSN=your-sentry-dsn
ENABLE_SENTRY=true
LOG_LEVEL=INFO
LOG_FORMAT=json

# Optional: Direct Slack webhook for critical alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#alerts-critical
```

## Next Steps

1. Choose your monitoring approach (Sentry is easiest since it's already set up)
2. Configure Slack integration
3. Create alert rules
4. Test the alerts
5. Monitor your production deployment

For Railway deployment, Sentry + Slack is the recommended approach as it requires no additional infrastructure.
