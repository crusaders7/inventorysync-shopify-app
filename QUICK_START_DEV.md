# Quick Start Guide - Development

## Starting the Application

### Terminal 1 - Backend Server
```bash
cd /home/brend/inventorysync-shopify-app/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Terminal 2 - Frontend Server
```bash
cd /home/brend/inventorysync-shopify-app/frontend
npm run dev
```

## Access URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Test Store Credentials
- Shop Domain: `inventorysync-dev.myshopify.com`
- Email: `test@inventorysync.com`
- Status: Trial (14 days)

## Development Features
- ✅ Auto-authentication in dev mode
- ✅ Mock data for testing
- ✅ Hot reload enabled
- ✅ CORS configured for localhost
- ✅ PostgreSQL database connected

## Common Issues & Solutions

### "No shop domain found"
- The app now auto-sets development credentials
- Check localStorage for `shopDomain` key
- Clear browser cache if needed

### Database errors
- Run: `python fix_db_schema_quick.py`
- Check PostgreSQL is running: `sudo service postgresql status`

### Frontend not loading
- Clear Vite cache: `rm -rf node_modules/.vite`
- Reinstall dependencies: `npm install`

## Next Steps for Production
1. Generate production secrets
2. Set up SSL certificates
3. Configure production database
4. Run full test suite
5. Set up monitoring
