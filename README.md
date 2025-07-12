# InventorySync - Advanced Shopify Inventory Management

A sophisticated inventory management system for Shopify stores with real-time synchronization, multi-location support, custom fields, and advanced analytics. Built with FastAPI and React for optimal performance and user experience.

## 📋 Table of Contents
- [Current Status](#-current-status)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [PostgreSQL Database Setup](#-postgresql-database-setup)
- [Authentication Configuration](#-authentication-configuration)
- [Custom Fields API](#-custom-fields-api)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

## 🚀 Current Status

**Development Environment**: ✅ Running Successfully
- Backend API: http://localhost:8000
- Frontend App: http://localhost:3000
- Database: PostgreSQL/SQLite (configurable)
- API Documentation: http://localhost:8000/docs
- Monitoring Dashboard: http://localhost:3001

**Recent Updates**:
- ✅ Fixed authentication flow for development environment
- ✅ Implemented auto-authentication for local development
- ✅ Resolved shop domain resolution issues
- ✅ Added custom fields API with industry templates
- ✅ Database schema optimizations

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed status and next steps.

## ✨ Features

### Core Functionality
- 📦 **Real-time Inventory Sync** - Bidirectional synchronization with Shopify
- 🏪 **Multi-location Support** - Manage inventory across unlimited locations
- 📊 **Advanced Analytics Dashboard** - Real-time insights and KPIs
- 🔔 **Smart Alert System** - Customizable notifications and thresholds
- 🏷️ **Custom Fields Manager** - Flexible product metadata with templates
- 🔄 **Bulk Operations** - Efficient mass updates with progress tracking
- 📈 **AI-Powered Forecasting** - Machine learning demand prediction
- 🛡️ **Enterprise Security** - JWT authentication, RBAC, audit logs
- 🔧 **Workflow Automation** - Rule-based triggers and actions
- 💳 **Shopify Billing Integration** - Subscription management via Shopify API

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **PostgreSQL** - Primary database with JSONB for custom fields
- **SQLAlchemy** - ORM with async support
- **Redis** - Caching and session management
- **Alembic** - Database migrations
- **JWT** - Secure authentication
- **Prometheus** - Metrics and monitoring
- **Grafana** - Visualization and alerting
- **Sentry** - Error tracking and performance monitoring

### Frontend  
- **React 18** - Modern UI framework
- **Shopify Polaris** - Native Shopify design system
- **Vite** - Lightning-fast build tool
- **React Router** - Client-side routing
- **Axios** - HTTP client with interceptors

## 📦 Installation

### Prerequisites

- Python 3.10+ with pip
- Node.js 18+ with npm
- PostgreSQL 13+ (or use SQLite for development)
- Redis 6+ (optional for caching)
- Git for version control

### Detailed Installation Steps

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/inventorysync-shopify-app.git
cd inventorysync-shopify-app
```

#### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# For development, the defaults should work
```

#### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Create development environment file
cp .env.example .env
```

#### 5. Initialize Development Database

```bash
# Navigate back to backend
cd ../backend

# Run database migrations
alembic upgrade head

# Create test data (optional)
python scripts/init_dev_data.py
```

## 🗄️ PostgreSQL Database Setup

### Option 1: PostgreSQL (Recommended for Production)

#### Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download installer from [PostgreSQL official site](https://www.postgresql.org/download/windows/)

#### Create Database and User

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database
CREATE DATABASE inventorysync_dev;

# Create user with password
CREATE USER inventorysync WITH ENCRYPTED PASSWORD 'devpassword123';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE inventorysync_dev TO inventorysync;

# Enable extensions
\c inventorysync_dev
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# Exit PostgreSQL
\q
```

#### Update .env File

```env
# backend/.env
DATABASE_URL=postgresql://inventorysync:devpassword123@localhost:5432/inventorysync_dev
DATABASE_URL_ASYNC=postgresql+asyncpg://inventorysync:devpassword123@localhost:5432/inventorysync_dev
```

### Option 2: SQLite (Development Only)

For quick development setup, SQLite is used by default:

```env
# backend/.env
DATABASE_URL=sqlite:///./inventorysync_dev.db
```

No additional setup required - the database file will be created automatically.

## 🔍 Monitoring and Logging

### Monitoring Setup
- **Prometheus** is integrated for comprehensive metrics collection.
- **Grafana** dashboards provide visual insights and alerting.
- **Sentry** is configured for error tracking and performance monitoring.

### Logging Setup
- Structured logging with request ID tracing and various log levels.

## 🚀 Quick Start Guide

### Start Development Environment

1. **Using the convenience script (Recommended)**:
   ```bash
   # Make scripts executable
   chmod +x scripts/*.sh
   
   # Start both backend and frontend
   ./scripts/start_servers.sh
   ```

2. **Manual startup**:
   
   Terminal 1 - Backend:
   ```bash
   cd backend
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   Terminal 2 - Frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Verify Installation

1. **Check backend health**:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy"}
   ```

2. **Check frontend**:
   - Open http://localhost:3000
   - You should see the InventorySync dashboard
   - Red "Development Mode" banner should be visible

3. **Test API endpoints**:
   ```bash
   # Get custom field templates
   curl http://localhost:8000/api/custom-fields/templates
   ```

## 🔐 Authentication Configuration

### Development Mode Authentication

The app includes automatic authentication for development:

1. **Auto-Authentication**: When running locally, the app automatically authenticates with a test shop domain
2. **Test Shop Domain**: `inventorysync-dev.myshopify.com`
3. **Development Token**: Generated automatically

### Recent Authentication Fixes

- ✅ Fixed shop domain resolution across components
- ✅ Added development authentication helper (`frontend/src/utils/devAuth.js`)
- ✅ Implemented auto-login for localhost environment
- ✅ Added localStorage fallbacks for shop domain

### Production Authentication Setup

1. **Configure JWT Settings**
```env
# backend/.env
SECRET_KEY=your-256-bit-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```

2. **Generate Secure Keys**
```bash
# Generate secret keys
python generate_secrets.py
```

3. **Shopify OAuth Configuration**
```env
SHOPIFY_API_KEY=your-shopify-api-key
SHOPIFY_API_SECRET=your-shopify-api-secret
SHOPIFY_WEBHOOK_SECRET=your-webhook-secret
```

### Authentication Flow

1. Shop installs app via Shopify App Store
2. OAuth redirect to your app URL
3. App validates OAuth request
4. Creates/updates store record in database
5. Generates JWT access token
6. Returns token to frontend
7. Frontend stores token in localStorage
8. All API requests include JWT in headers

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

## 📁 Project Structure

```
inventorysync-shopify-app/
├── backend/                    # FastAPI Backend Application
│   ├── api/                   # API Route Handlers
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── inventory.py      # Inventory management
│   │   ├── custom_fields.py  # Custom fields API
│   │   ├── dashboard.py      # Analytics & statistics
│   │   ├── alerts.py         # Alert management
│   │   ├── shopify_sync.py   # Shopify synchronization
│   │   └── webhooks.py       # Webhook handlers
│   ├── core/                  # Core Application Logic
│   │   ├── security.py       # JWT & authentication
│   │   ├── permissions.py    # RBAC implementation
│   │   └── exceptions.py     # Custom exceptions
│   ├── models/               # Database Models
│   │   ├── __init__.py
│   │   ├── store.py         # Store model
│   │   ├── product.py       # Product model
│   │   ├── inventory.py     # Inventory model
│   │   └── custom_field.py  # Custom field models
│   ├── schemas/              # Pydantic Schemas
│   │   ├── store.py
│   │   ├── product.py
│   │   └── custom_field.py
│   ├── services/             # Business Logic Services
│   │   ├── shopify.py       # Shopify API client
│   │   ├── inventory.py     # Inventory service
│   │   └── forecasting.py   # ML forecasting
│   ├── utils/                # Utility Functions
│   │   ├── cache.py         # Redis caching
│   │   ├── logger.py        # Logging configuration
│   │   └── validators.py    # Input validators
│   ├── alembic/             # Database Migrations
│   │   ├── versions/        # Migration files
│   │   └── alembic.ini      # Alembic config
│   ├── tests/               # Test Suite
│   │   ├── unit/           # Unit tests
│   │   ├── integration/    # Integration tests
│   │   └── conftest.py     # Test fixtures
│   ├── scripts/             # Utility Scripts
│   │   ├── init_db.py      # Database initialization
│   │   └── seed_data.py    # Seed test data
│   ├── .env                 # Environment variables
│   ├── .env.example         # Environment template
│   ├── config.py            # Configuration management
│   ├── database.py          # Database setup
│   ├── main.py              # FastAPI app entry
│   ├── models.py            # Legacy models file
│   └── requirements.txt     # Python dependencies
│
├── frontend/                 # React Frontend Application
│   ├── public/              # Static Assets
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── src/                 # Source Code
│   │   ├── components/      # React Components
│   │   │   ├── common/     # Shared components
│   │   │   │   ├── Header.jsx
│   │   │   │   ├── Footer.jsx
│   │   │   │   └── Loading.jsx
│   │   │   ├── dashboard/  # Dashboard components
│   │   │   │   ├── Dashboard.jsx
│   │   │   │   ├── StatsCard.jsx
│   │   │   │   └── Charts.jsx
│   │   │   ├── inventory/  # Inventory components
│   │   │   │   ├── Inventory.jsx
│   │   │   │   ├── ProductList.jsx
│   │   │   │   └── BulkActions.jsx
│   │   │   ├── custom-fields/
│   │   │   │   ├── CustomFieldsManager.jsx
│   │   │   │   ├── FieldForm.jsx
│   │   │   │   └── TemplateSelector.jsx
│   │   │   └── alerts/     # Alert components
│   │   │       ├── AlertManager.jsx
│   │   │       └── RuleBuilder.jsx
│   │   ├── context/        # React Context
│   │   │   ├── AuthContext.jsx
│   │   │   ├── ShopContext.jsx
│   │   │   └── ThemeContext.jsx
│   │   ├── hooks/          # Custom Hooks
│   │   │   ├── useAuth.js
│   │   │   ├── useShopify.js
│   │   │   └── useApi.js
│   │   ├── services/       # API Services
│   │   │   ├── api.js      # Axios instance
│   │   │   ├── auth.js     # Auth service
│   │   │   └── inventory.js # Inventory service
│   │   ├── utils/          # Utility Functions
│   │   │   ├── devAuth.js  # Dev authentication
│   │   │   ├── helpers.js  # Helper functions
│   │   │   └── constants.js # App constants
│   │   ├── styles/         # CSS/SCSS Files
│   │   │   ├── globals.css
│   │   │   └── components/
│   │   ├── App.jsx         # Main App Component
│   │   ├── App.css         # App styles
│   │   └── main.jsx        # React entry point
│   ├── tests/              # Frontend Tests
│   │   ├── unit/
│   │   └── e2e/
│   ├── .env                # Environment variables
│   ├── .env.example        # Environment template
│   ├── .gitignore          # Git ignore file
│   ├── package.json        # NPM dependencies
│   ├── package-lock.json   # Dependency lock
│   ├── vite.config.js      # Vite configuration
│   └── README.md           # Frontend readme
│
├── docs/                    # Documentation
│   ├── api/                # API documentation
│   ├── deployment/         # Deployment guides
│   └── development/        # Development guides
│
├── scripts/                 # Project Scripts
│   ├── start_backend.sh    # Start backend server
│   ├── start_frontend.sh   # Start frontend dev
│   ├── start_servers.sh    # Start both servers
│   └── generate_secrets.py # Generate secret keys
│
├── monitoring/              # Monitoring Config
│   ├── prometheus.yml      # Prometheus config
│   └── grafana/           # Grafana dashboards
│
├── .github/                # GitHub Configuration
│   └── workflows/         # GitHub Actions
│       ├── ci.yml         # CI pipeline
│       └── deploy.yml     # Deploy pipeline
│
├── docker-compose.yml      # Docker Compose config
├── Dockerfile.backend      # Backend Dockerfile
├── Dockerfile.frontend     # Frontend Dockerfile
├── .env.example           # Root environment template
├── .gitignore             # Git ignore file
├── LICENSE                # MIT License
├── README.md              # This file
└── PROJECT_STATUS.md      # Current project status
```

## 🏷️ Custom Fields API

The Custom Fields API provides flexible product metadata management with industry-specific templates.

### Features
- **Industry Templates**: Pre-built field sets for different business types
- **Field Types**: text, number, date, select, boolean, json
- **Validation Rules**: Min/max values, regex patterns, required fields
- **Bulk Operations**: Apply fields to multiple products efficiently

### Available Templates

**Apparel Industry:**
- Size (select: XS, S, M, L, XL, XXL)
- Color (text)
- Material (text)
- Season (select: Spring, Summer, Fall, Winter)

**Electronics:**
- Warranty Period (number - months)
- Technical Specifications (json)
- Compatibility (text)

**Food & Beverage:**
- Expiration Date (date)
- Batch Number (text)
- Storage Temperature (number - °C)
- Ingredients (text)

### API Endpoints

```http
# Get all available templates
GET /api/custom-fields/templates

# Create a custom field
POST /api/custom-fields/{shop_domain}
Content-Type: application/json
{
  "field_name": "size",
  "field_type": "select",
  "display_name": "Size",
  "required": true,
  "options": ["S", "M", "L", "XL"]
}

# List all custom fields for a store
GET /api/custom-fields/{shop_domain}

# Update custom field
PUT /api/custom-fields/{shop_domain}/{field_id}

# Delete custom field
DELETE /api/custom-fields/{shop_domain}/{field_id}

# Apply custom field to products
POST /api/custom-fields/{shop_domain}/apply
{
  "field_id": 123,
  "product_ids": [456, 789],
  "value": "Large"
}
```

### Usage Example

```javascript
// Frontend: Create a custom field
const response = await fetch('/api/custom-fields/mystore.myshopify.com', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    field_name: 'warranty_months',
    field_type: 'number',
    display_name: 'Warranty (Months)',
    required: true,
    validation_rules: {
      min: 0,
      max: 60
    }
  })
});
```

## 📁 Project Structure

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

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Frontend Connection Issues

**Problem**: Frontend can't connect to backend API
```
Failed to fetch
net::ERR_CONNECTION_REFUSED
```

**Solutions**:
1. Verify backend is running:
   ```bash
   # Check if backend is running
   curl http://localhost:8000/health
   ```
2. Check Vite proxy configuration in `vite.config.js`
3. Clear browser cache and cookies
4. Ensure CORS is properly configured in backend

#### Authentication Issues

**Problem**: "No shop domain found" error

**Solutions**:
1. Clear localStorage:
   ```javascript
   localStorage.clear()
   window.location.reload()
   ```
2. Check if running in development mode (should see red banner)
3. Manually set shop domain:
   ```javascript
   localStorage.setItem('shopDomain', 'inventorysync-dev.myshopify.com')
   ```

#### Database Connection Errors

**Problem**: SQLAlchemy connection error
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
```

**Solutions**:
1. Verify PostgreSQL service:
   ```bash
   # Linux/macOS
   sudo systemctl status postgresql
   # or
   brew services list | grep postgresql
   ```
2. Check database exists:
   ```bash
   psql -U postgres -l | grep inventorysync_dev
   ```
3. Verify credentials in `.env`:
   ```env
   DATABASE_URL=postgresql://inventorysync:devpassword123@localhost:5432/inventorysync_dev
   ```
4. Test connection:
   ```bash
   psql -U inventorysync -d inventorysync_dev -h localhost
   ```

#### Import/Module Errors

**Problem**: Module not found or import errors
```
Module not found: Error: Can't resolve '@shopify/polaris'
```

**Solutions**:
1. Clear Vite cache:
   ```bash
   rm -rf node_modules/.vite
   rm -rf node_modules
   npm install
   ```
2. Check for case sensitivity issues (especially on Linux)
3. Verify all dependencies are installed:
   ```bash
   npm list @shopify/polaris
   ```

#### Port Already in Use

**Problem**: Port 8000 or 3000 already in use

**Solutions**:
1. Find process using port:
   ```bash
   # Linux/macOS
   lsof -i :8000
   # Windows
   netstat -ano | findstr :8000
   ```
2. Kill the process:
   ```bash
   # Linux/macOS
   kill -9 <pid>
   # Windows
   taskkill /PID <pid> /F
   ```
3. Or use different ports:
   ```bash
   # Backend
   uvicorn main:app --port 8001
   # Frontend - update vite.config.js proxy
   ```

#### Shopify API Errors

**Problem**: 401 Unauthorized from Shopify

**Solutions**:
1. Verify Shopify credentials in `.env`
2. Check if access token is expired
3. Ensure shop domain is correct
4. For development, use test credentials:
   ```env
   SHOPIFY_API_KEY=test_api_key
   SHOPIFY_API_SECRET=test_api_secret
   ```

#### Custom Fields Not Saving

**Problem**: Custom fields created but not persisting

**Solutions**:
1. Check database migrations:
   ```bash
   alembic current
   alembic upgrade head
   ```
2. Verify table exists:
   ```sql
   SELECT * FROM custom_field_definitions LIMIT 1;
   ```
3. Check API response for errors
4. Ensure proper authentication token

#### Performance Issues

**Problem**: Slow page loads or API responses

**Solutions**:
1. Enable Redis caching:
   ```bash
   redis-server
   ```
2. Check for N+1 query problems
3. Enable database query logging:
   ```python
   # In config.py
   SQLALCHEMY_ECHO = True
   ```
4. Use Chrome DevTools Performance tab

### Development Environment Reset

If all else fails, perform a complete reset:

```bash
# Stop all services
pkill -f uvicorn
pkill -f "npm run dev"

# Clear all caches
rm -rf frontend/node_modules/.vite
rm -rf backend/__pycache__
rm -rf backend/.pytest_cache

# Reset database
dropdb inventorysync_dev
createdb inventorysync_dev
cd backend && alembic upgrade head

# Reinstall dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm ci

# Start fresh
./scripts/start_servers.sh
```

### Getting Help

If you're still experiencing issues:

1. Check the logs:
   - Backend: Look for errors in terminal running uvicorn
   - Frontend: Check browser console (F12)
   - Database: Check PostgreSQL logs

2. Enable debug mode:
   ```env
   # backend/.env
   DEBUG=True
   LOG_LEVEL=DEBUG
   ```

3. Create an issue with:
   - Error message/screenshot
   - Steps to reproduce
   - Environment details (OS, Python version, Node version)
   - Relevant log files

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
