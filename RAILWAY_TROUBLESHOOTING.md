# Railway Deployment Troubleshooting

## Check Deployment Status

1. Go to your Railway dashboard
2. Click on your project
3. Check the deployment status (should be green/active)
4. Click on the deployment to see logs

## Get Your Actual URL

In Railway:
1. Click on your service
2. Go to "Settings" tab
3. Under "Domains", you'll see your URL
4. It might be something like:
   - `inventorysync-shopify-app.up.railway.app`
   - `inventorysync-shopify-app-production.up.railway.app`
   - Or a custom generated URL

## Common Issues

### 1. Application Not Found (404)
- Check if the deployment is active
- Verify the exact URL from Railway dashboard
- Ensure the service is not sleeping (on free tier)

### 2. Build Failed
Check build logs for:
- Missing dependencies
- Docker build errors
- Environment variable issues

### 3. Application Crashes on Start
Check runtime logs for:
- Missing environment variables
- Database connection issues
- Port binding problems

## Quick Fixes

### 1. Restart the Service
```bash
# In Railway dashboard
Click "Redeploy" on the latest deployment
```

### 2. Check Environment Variables
Ensure these are set:
- DATABASE_URL (auto-provided by Railway)
- PORT (auto-provided by Railway)
- All variables from RAILWAY_ENV_VARS.txt

### 3. Check Logs
```bash
# Install Railway CLI if not already installed
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# View logs
railway logs
```

## Test Endpoints Once Fixed

```bash
# Replace YOUR_URL with actual Railway URL
curl https://YOUR_URL/health
curl https://YOUR_URL/api
curl https://YOUR_URL/docs
```

## Need to Redeploy?

```bash
cd /home/brend/inventorysync-shopify-app
railway up
```
