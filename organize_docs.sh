#!/bin/bash

echo "📂 Organizing documentation for production readiness..."

# Create archive directory for old docs
mkdir -p docs/archive

# Move outdated development logs and reports to archive
echo "📦 Archiving outdated documentation..."
mv -v CLEANUP_REPORT.md docs/archive/ 2>/dev/null || true
mv -v DEVELOPMENT_LOG.md docs/archive/ 2>/dev/null || true
mv -v FIXES_APPLIED.md docs/archive/ 2>/dev/null || true
mv -v HANDOVER.md docs/archive/ 2>/dev/null || true
mv -v ISSUE_RESOLUTION_SUMMARY.md docs/archive/ 2>/dev/null || true
mv -v LAUNCH_READY.md docs/archive/ 2>/dev/null || true
mv -v PRODUCTION_UI_IMPROVEMENTS.md docs/archive/ 2>/dev/null || true
mv -v PROJECT_STATUS.md docs/archive/ 2>/dev/null || true
mv -v PROJECT_SUMMARY.md docs/archive/ 2>/dev/null || true
mv -v README_OLD.md docs/archive/ 2>/dev/null || true
mv -v TIMELINE.md docs/archive/ 2>/dev/null || true
mv -v INTEGRATION_SUMMARY.md docs/archive/ 2>/dev/null || true
mv -v database.md docs/archive/ 2>/dev/null || true
mv -v deployment.md docs/archive/ 2>/dev/null || true

# Keep essential production docs in root
echo "✅ Keeping essential production documentation..."
echo "   - README.md (main documentation)"
echo "   - RAILWAY_SETUP_GUIDE.md (deployment guide)"
echo "   - PRODUCTION_CHECKLIST.md (launch checklist)"
echo "   - SHOPIFY_SUBMISSION_CHECKLIST.md (app store requirements)"
echo "   - DEPLOYMENT_GUIDE.md (deployment process)"
echo "   - CURRENT_STATUS.md (current state)"
echo "   - NEXT_STEPS.md (development roadmap)"

# Create a consolidated PRODUCTION_README.md
cat > PRODUCTION_README.md << 'EOF'
# InventorySync Production Deployment

## 🚀 Current Status
- **Environment**: Production (Railway)
- **Project**: aussie_legal
- **Service**: Inventorysync
- **Status**: Ready for final deployment steps

## 📋 Required Actions Before Launch

### 1. Railway Configuration
- [ ] Add PostgreSQL database to Railway project
- [ ] Add Redis to Railway project
- [ ] Configure all environment variables (see RAILWAY_SETUP_GUIDE.md)
- [ ] Set Shopify API credentials from Partners dashboard

### 2. Shopify App Setup
- [ ] Complete OAuth configuration
- [ ] Test webhook endpoints
- [ ] Verify GDPR compliance
- [ ] Prepare app listing content

### 3. Production Deployment
```bash
# Deploy to Railway
railway up

# Check deployment status
railway logs

# Open production app
railway open
```

## 📁 Documentation Structure
- **README.md** - Complete project documentation
- **RAILWAY_SETUP_GUIDE.md** - Step-by-step deployment guide
- **PRODUCTION_CHECKLIST.md** - Pre-launch verification
- **SHOPIFY_SUBMISSION_CHECKLIST.md** - App store requirements
- **docs/archive/** - Historical development documentation

## 🔗 Quick Links
- Railway Project: https://railway.com/project/de832abe-3d73-40ef-9fc5-c4054e8af06c
- Shopify Partners: https://partners.shopify.com
- API Documentation: `/api/docs` (disabled in production)

## ⚡ Next Immediate Steps
1. Complete Railway database setup
2. Configure production environment variables
3. Deploy application
4. Test all endpoints
5. Submit to Shopify App Store

---
Ready for production deployment! 🎉
EOF

echo "✅ Created PRODUCTION_README.md"

# Create quick reference guide
cat > QUICK_REFERENCE.md << 'EOF'
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
EOF

echo "✅ Created QUICK_REFERENCE.md"
echo ""
echo "📂 Documentation organized successfully!"
echo ""
echo "Essential docs remain in root directory:"
ls -la *.md | grep -E "(README|RAILWAY|PRODUCTION|SHOPIFY|DEPLOYMENT|CURRENT|NEXT|QUICK)" | awk '{print "  ✓", $9}'
echo ""
echo "Archived docs moved to docs/archive/:"
ls -la docs/archive/*.md 2>/dev/null | awk '{print "  📦", $9}' | head -5
echo "  ... and more"
echo ""
echo "🎯 Ready for production deployment!"
