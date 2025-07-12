# Railway Setup Guide for InventorySync

## Prerequisites Completed ✅
- Railway CLI installed
- Logged in to Railway
- Project linked
- Docker configuration created
- Secure keys generated

## Next Steps - YOU NEED TO DO THESE:

### 1. Add PostgreSQL Database to Railway
1. Go to your Railway project: https://railway.com/project/de832abe-3d73-40ef-9fc5-c4054e8af06c
2. Click "+ New" → "Database" → "Add PostgreSQL"
3. Railway will automatically create the database and provide:
   - `DATABASE_URL` (automatically available as environment variable)

### 2. Add Redis to Railway
1. In your Railway project, click "+ New" → "Database" → "Add Redis"
2. Railway will automatically create Redis and provide:
   - `REDIS_URL` (automatically available as environment variable)

### 3. Get Shopify API Credentials
1. Go to https://partners.shopify.com
2. Navigate to "Apps" → "Your App" → "API credentials"
3. Copy these values:
   - API key → `SHOPIFY_API_KEY`
   - API secret key → `SHOPIFY_API_SECRET`
   - Create a webhook secret → `SHOPIFY_WEBHOOK_SECRET`

### 4. Set Environment Variables in Railway
1. Go to your InventorySync service in Railway
2. Click on "Variables" tab
3. Add all variables from `railway-env-template.txt`
4. Important variables to update:
   - `SHOPIFY_API_KEY` (from Shopify Partners)
   - `SHOPIFY_API_SECRET` (from Shopify Partners)
   - `SHOPIFY_WEBHOOK_SECRET` (from Shopify Partners)
   - `APP_URL` (your Railway app URL)
   - `FRONTEND_URL` (where your frontend will be hosted)

### 5. Reference Database Variables
In Railway Variables, add these references:
```
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
```

### 6. Optional: Set up Sentry for Error Tracking
1. Create account at https://sentry.io
2. Create a new project
3. Copy the DSN and add to `SENTRY_DSN` variable

## Deployment Commands

Once you've completed the above steps, run:

```bash
# Deploy to Railway
railway up

# Check deployment logs
railway logs

# Open your app
railway open
```

## Post-Deployment Checklist

- [ ] PostgreSQL database added
- [ ] Redis added
- [ ] All environment variables set
- [ ] Shopify API credentials configured
- [ ] Database migrations run automatically on startup
- [ ] Health check endpoint working: https://your-app.railway.app/health
- [ ] API docs disabled in production

## Troubleshooting

If deployment fails:
1. Check logs: `railway logs`
2. Verify all environment variables are set
3. Ensure PostgreSQL and Redis are provisioned
4. Check that Shopify credentials are correct

## Security Notes

- Never commit `.env` files to git
- Rotate JWT secrets regularly
- Use Railway's built-in SSL
- Keep dependencies updated
