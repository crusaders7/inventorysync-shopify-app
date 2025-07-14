# InventorySync Shopify App Architecture

## Overview
InventorySync is a full-stack Shopify application built with a React frontend and FastAPI (Python) backend. The app provides inventory management, custom fields, forecasting, and multi-location support for Shopify stores.

## Technology Stack

### Frontend
- **Framework**: React 18.2.0 with Vite build tool
- **UI Library**: Shopify Polaris v12.0.0
- **Routing**: React Router v6.20.0
- **State Management**: Custom React Context API (DataContext)
- **HTTP Client**: Axios for API calls
- **Charts**: Chart.js and Recharts for data visualization
- **Shopify Integration**: @shopify/app-bridge-react for embedded app functionality

### Backend
- **Framework**: FastAPI (Python) v0.104.1
- **Server**: Uvicorn with Gunicorn for production
- **Database**: PostgreSQL with SQLAlchemy ORM v2.0.23
- **Async Support**: asyncpg for async database operations
- **Authentication**: JWT tokens with python-jose
- **Background Tasks**: Celery with Redis as message broker
- **Caching**: Redis with hiredis
- **Monitoring**: Sentry SDK, Prometheus client
- **Data Processing**: Pandas and NumPy
- **Forecasting**: scikit-learn and statsmodels

## Architecture Components

### Backend Structure (`/backend/`)

#### API Endpoints (`/backend/api/`)
The backend implements a modular API structure with the following key endpoints:

1. **Authentication** (`auth.py`, `auth_simple.py`)
   - OAuth 2.0 flow for Shopify authentication
   - JWT token generation and validation
   - Shop installation and callback handling

2. **Inventory Management** (`inventory.py`, `inventory_simple.py`, `inventory_enhanced.py`)
   - CRUD operations for inventory items
   - Stock level tracking and updates
   - Multi-location inventory support

3. **Custom Fields** (`custom_fields.py`, `custom_fields_simple.py`, `custom_fields_enhanced.py`)
   - Core feature for adding custom product fields
   - Template management for industry-specific fields
   - Bulk field operations

4. **Webhooks** (`webhooks.py`, `webhooks_simple.py`)
   - Product create/update/delete handlers
   - Inventory level update handlers
   - App uninstalled handler
   - GDPR compliance webhooks

5. **Metafields Integration** (`metafields.py`, `metafields_bulk.py`)
   - Direct Shopify metafield management
   - Bulk operations for performance
   - Custom field to metafield synchronization

6. **Other Features**:
   - **Billing** (`billing.py`): Shopify billing API integration
   - **Alerts** (`alerts.py`): Low stock and custom alerts
   - **Reports** (`reports.py`): Inventory reports and analytics
   - **Forecasting** (`forecasting.py`): Demand forecasting with ML
   - **Dashboard** (`dashboard.py`): Analytics and stats
   - **Locations** (`locations.py`): Multi-location management
   - **Workflows** (`workflows.py`): Automation workflows
   - **Monitoring** (`monitoring.py`): System health and metrics

#### Database Models (`/backend/models.py`)
SQLAlchemy models with relationships:

```python
- Store: Shopify store information, subscription details
- Location: Store locations (warehouses, retail stores)
- Product: Shopify products with custom data support
- ProductVariant: Product variants with inventory settings
- InventoryItem: Inventory levels per variant per location
- InventoryMovement: Stock movement history
- Alert: Inventory alerts and notifications
- CustomField: Field definitions and configurations
- Workflow: Automation workflow definitions
```

#### Main Application (`/backend/main.py`)
- FastAPI application setup
- CORS configuration for frontend communication
- Router registration with graceful fallbacks
- Security middleware integration
- WebhookVerification, RateLimiting, SecurityHeaders

### Frontend Structure (`/frontend/`)

#### Main Components (`/frontend/src/components/`)

1. **Core Components**:
   - `Dashboard.jsx`: Main dashboard with stats and charts
   - `Inventory.jsx`: Inventory management interface
   - `Navigation.jsx`: App navigation structure

2. **Custom Fields Components** (Core Feature):
   - `CustomFieldsManager.jsx`: Main custom fields interface
   - `CustomFieldsEnhanced.jsx`: Enhanced field management
   - `ProductMetafields.jsx`: Product-specific field management
   - `ProductMetafieldsEnhanced.jsx`: Advanced metafield operations
   - `BulkMetafieldEditor.jsx`: Bulk field editing interface

3. **Other Key Components**:
   - `ShopifyInstall.jsx`: App installation flow
   - `AuthCallback.jsx`: OAuth callback handler
   - `BillingSetup.jsx`: Subscription management
   - `AlertsManager.jsx`: Alert management system
   - `ForecastingDashboard.jsx`: Demand forecasting UI
   - `MultiLocationManager.jsx`: Multi-location inventory
   - `WorkflowManager.jsx`: Automation workflows
   - `ReportsBuilder.jsx`: Custom report generation

#### State Management (`/frontend/src/context/DataContext.jsx`)
- Centralized state using React Context API
- Real-time data updates with 30-second auto-refresh
- Actions for inventory updates, alerts, and stats
- Simulated real-time updates for demo purposes

#### App Entry (`/frontend/src/App.jsx`)
- Routing configuration for embedded and standalone modes
- App Bridge integration for Shopify admin embedding
- Protected routes with authentication checks
- Toast notifications for user feedback

### Configuration Files

#### Shopify App Configuration (`shopify.app.toml`)
```toml
- Client ID: b9e83419bf510cff0b85cf446b4a7750
- App Name: InventorySync
- Handle: inventorysync-15
- Application URL: https://inventorysync.prestigecorp.au/
- Embedded: true
- Webhook subscriptions for all inventory events
- OAuth redirect URLs
- App proxy configuration
```

#### Frontend Build (`frontend/vite.config.js`)
- Development server with API proxy to backend
- Production optimizations:
  - Code splitting with manual chunks
  - Gzip and Brotli compression
  - Image optimization
  - Source maps for debugging

#### Backend Environment (`backend/.env.production.example`)
- Database configuration (PostgreSQL)
- Shopify API credentials
- JWT authentication settings
- Redis configuration for caching
- Monitoring and logging setup
- Feature flags for modular functionality

## Data Flow and Interactions

### Authentication Flow
1. Shop installs app → Redirected to `/install`
2. OAuth initiation → Shopify authorization
3. Callback to `/auth/callback` → Token exchange
4. Store credentials saved → User redirected to dashboard

### Inventory Sync Flow
1. Shopify webhooks → Backend webhook handlers
2. Product/inventory updates → Database synchronization
3. Frontend polls for updates → Real-time UI updates
4. User actions → API calls → Shopify API updates

### Custom Fields Flow (Core Feature)
1. User defines custom fields → Saved to database
2. Fields mapped to Shopify metafields → Sync via API
3. Bulk operations for efficiency → Batch processing
4. Templates for quick setup → Industry-specific presets

### Key Integrations

1. **Shopify Admin**:
   - Embedded app using App Bridge
   - Direct metafield management
   - Webhook event processing
   - Billing API integration

2. **External Services**:
   - PostgreSQL for data persistence
   - Redis for caching and queues
   - Sentry for error tracking
   - Monitoring webhooks for alerts

## Deployment Architecture

### Production Setup
- Backend: FastAPI with Gunicorn workers
- Frontend: Static files served via CDN
- Database: PostgreSQL with connection pooling
- Cache: Redis with persistence
- Queue: Celery with Redis broker

### Scalability Features
- Horizontal scaling with multiple workers
- Database connection pooling
- Redis caching for performance
- Bulk operations for large datasets
- Async processing for long-running tasks

## Security Measures
- JWT token authentication
- Webhook signature verification
- Rate limiting middleware
- Security headers (CORS, CSP, etc.)
- GDPR compliance endpoints
- Environment-based configuration

## Monitoring and Observability
- Health check endpoints
- Prometheus metrics export
- Sentry error tracking
- Structured logging with JSON format
- Performance monitoring hooks
- Custom alert system

<citations>
<document>
<document_type>RULE</document_type>
<document_id>GI03EHuZD8E8bcNvNwN7MG</document_id>
</document>
</citations>
