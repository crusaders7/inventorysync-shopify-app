# InventorySync - Advanced Shopify Inventory Management

A sophisticated inventory management system for Shopify stores with multi-location support, custom fields, and advanced analytics.

## 🚀 Current Status

**Development Environment**: ✅ Running Successfully
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Database: PostgreSQL (configured and running)

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed status and next steps.

## Features

- 📦 **Real-time Inventory Sync** - Automatic synchronization with Shopify
- 🏪 **Multi-location Support** - Manage inventory across multiple locations
- 📊 **Advanced Analytics** - Forecasting, trends, and insights
- 🔔 **Smart Alerts** - Low stock warnings and custom notifications
- 🏷️ **Custom Fields** - Industry-specific templates and flexible data fields
- 🔄 **Bulk Operations** - Update multiple items efficiently
- 📈 **Forecasting** - ML-powered demand prediction
- 🛡️ **Enterprise Security** - JWT auth, rate limiting, audit logs
- 🔧 **Workflow Automation** - Custom rules and automated actions
- 💳 **Shopify Billing API** - Integrated subscription management

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **PostgreSQL** - Primary database with JSONB for custom fields
- **SQLAlchemy** - ORM with async support
- **Redis** - Caching and session management
- **Alembic** - Database migrations
- **JWT** - Secure authentication

### Frontend  
- **React 18** - Modern UI framework
- **Shopify Polaris** - Native Shopify design system
- **Vite** - Lightning-fast build tool
- **React Router** - Client-side routing
- **Axios** - HTTP client with interceptors

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+ (optional for development)

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/inventorysync-shopify-app.git
cd inventorysync-shopify-app
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Database Setup**
```bash
# Create PostgreSQL database and user
sudo -u postgres psql
CREATE DATABASE inventorysync_dev;
CREATE USER inventorysync WITH PASSWORD 'devpassword123';
GRANT ALL PRIVILEGES ON DATABASE inventorysync_dev TO inventorysync;
\q
```

4. **Frontend Setup**
```bash
cd ../frontend
npm install
```

5. **Start Development Servers**

Backend (Terminal 1):
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend (Terminal 2):
```bash
cd frontend
npm run dev
```

## Configuration

### Backend Environment Variables

The backend `.env` file is already configured for development. For production, update:

```env
# Shopify App Credentials
SHOPIFY_API_KEY=your_production_api_key
SHOPIFY_API_SECRET=your_production_api_secret
SHOPIFY_WEBHOOK_SECRET=generate_webhook_secret

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Security
SECRET_KEY=generate-strong-256-bit-key

# Optional Services
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=your-sentry-dsn
```

### Frontend Configuration

Frontend uses Vite proxy for development. For production, configure:

```javascript
// vite.config.js - already configured for development
export default {
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
}
```

## Project Structure

```
inventorysync-shopify-app/
├── backend/
│   ├── api/              # FastAPI route handlers
│   │   ├── inventory.py  # Inventory management
│   │   ├── custom_fields.py # Custom fields API
│   │   ├── dashboard.py  # Analytics endpoints
│   │   └── alerts.py     # Alert management
│   ├── models.py         # SQLAlchemy models
│   ├── database.py       # Database configuration
│   ├── main.py           # FastAPI application
│   ├── config.py         # Settings management
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # Reusable React components
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Inventory.jsx
│   │   │   └── CustomFieldsManager.jsx
│   │   ├── context/      # React Context providers
│   │   ├── App.jsx       # Main application
│   │   └── main.jsx      # Entry point
│   ├── package.json      # Node dependencies
│   └── vite.config.js    # Vite configuration
└── docs/                 # Additional documentation
```

## API Documentation

### Interactive Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key API Endpoints

```
# Inventory Management
GET    /api/v1/inventory/products
POST   /api/v1/inventory/sync
PUT    /api/v1/inventory/bulk-update

# Custom Fields
GET    /api/v1/custom-fields/{shop_domain}
POST   /api/v1/custom-fields/{shop_domain}
GET    /api/v1/custom-fields/templates

# Analytics
GET    /api/v1/dashboard/stats/{shop_domain}
GET    /api/v1/dashboard/charts/{shop_domain}

# Alerts
GET    /api/v1/alerts/{shop_domain}
POST   /api/v1/alerts/rules/{shop_domain}
```

## Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### E2E Tests
```bash
npm run test:e2e
```

## Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

### Production Checklist

- [ ] Update all environment variables
- [ ] Enable HTTPS (required by Shopify)
- [ ] Configure domain and SSL certificates
- [ ] Set up database backups
- [ ] Configure monitoring (Sentry, etc.)
- [ ] Enable rate limiting
- [ ] Set up GDPR webhooks
- [ ] Configure Shopify billing

## Shopify App Submission

### Requirements Checklist

- [ ] OAuth 2.0 implementation
- [ ] Webhook handlers for app/uninstalled
- [ ] GDPR compliance webhooks
- [ ] Billing API integration
- [ ] App Bridge for embedded experience
- [ ] Polaris design compliance
- [ ] Performance requirements (<3s load time)
- [ ] Security review passed

### Testing on Development Store

1. Create a development store at partners.shopify.com
2. Install ngrok: `npm install -g ngrok`
3. Expose local server: `ngrok http 8000`
4. Update app URLs in Partner Dashboard
5. Install app on development store

## Troubleshooting

### Common Issues

**Frontend can't connect to backend:**
- Check if backend is running on port 8000
- Verify Vite proxy configuration
- Clear browser cache

**Database connection errors:**
- Verify PostgreSQL is running
- Check credentials in .env
- Ensure database exists

**Import errors in frontend:**
- Clear Vite cache: `rm -rf node_modules/.vite`
- Restart development server

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Follow code style (Black for Python, ESLint for JS)
4. Write tests for new features
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## Support

- 📧 Email: support@inventorysync.com
- 💬 Discord: [Join our community](https://discord.gg/inventorysync)
- 📖 Docs: [docs.inventorysync.com](https://docs.inventorysync.com)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/inventorysync-shopify-app/issues)

---

**Note**: This is a development version. For production deployment, please follow the security checklist and update all credentials.
