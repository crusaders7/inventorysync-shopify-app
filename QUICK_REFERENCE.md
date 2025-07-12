# InventorySync Quick Reference

## 🚀 Deployment Commands
```bash
# Deploy to production
railway up

# View logs
railway logs -n 100

# Open production URL
railway open

# Check environment variables
railway variables
```

## 🔧 Local Development
```bash
# Start backend
cd backend && uvicorn main:app --reload

# Start frontend
cd frontend && npm run dev
```

## 📊 Key Endpoints
- Health Check: `/health`
- API Docs: `/api/docs` (dev only)
- Auth Status: `/api/v1/auth/status`
- Inventory: `/api/v1/inventory/`
- Custom Fields: `/api/v1/custom-fields/`

## 🔐 Environment Variables
See `railway-env-template.txt` for complete list

## 📱 Shopify Requirements
- OAuth implementation ✅
- Webhook handlers ✅
- GDPR compliance ✅
- Billing API ✅
- App Bridge 3.x ✅
