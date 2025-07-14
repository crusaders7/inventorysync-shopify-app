# 📚 InventorySync - Comprehensive Documentation

> **Enterprise-level inventory management for Shopify stores at startup-friendly prices**

## 🎯 **Project Overview**

InventorySync is a revolutionary Shopify app that bridges the gap between manual spreadsheets and expensive enterprise solutions. Built with modern technologies, it offers unlimited customization, AI-powered features, and enterprise-level functionality at 90% less cost than competitors.

### **Key Value Proposition**
- **90% cost savings** vs TradeGecko ($2,500/mo), Cin7 ($325/mo), Unleashed ($380/mo)
- **10-minute setup** vs weeks/months for enterprise solutions
- **Unlimited custom fields** vs 5-10 max for competitors
- **AI forecasting included** vs extra cost add-ons
- **Visual workflow builder** vs code-required automation

---

## 🏗️ **Technical Architecture**

### **Technology Stack**

#### **Backend**
- **Framework**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL (production) / SQLite (development)
- **Authentication**: OAuth 2.0 with Shopify
- **API Design**: RESTful with OpenAPI documentation
- **Real-time Sync**: Shopify Webhooks
- **AI/ML**: HuggingFace Transformers, scikit-learn
- **Deployment**: Railway (production), Docker support

#### **Frontend**
- **Framework**: React 18 with Vite
- **UI Library**: Shopify Polaris v12.0.0
- **Routing**: React Router DOM v6
- **State Management**: Context API + Local State
- **Charts**: Chart.js, Recharts
- **Styling**: Shopify Polaris components
- **Build Tool**: Vite 5.0.8

#### **Shopify Integration**
- **App Bridge**: v3.7.9 for embedded experience
- **Polaris Icons**: v7.0.0 for consistent UI
- **OAuth 2.0**: Secure store authentication
- **Webhooks**: Real-time product/order sync
- **Billing API**: Subscription management

### **Project Structure**
```
inventorysync-shopify-app/
├── backend/                    # FastAPI backend
│   ├── api/                   # API endpoints
│   │   ├── auth.py           # OAuth & authentication
│   │   ├── custom_fields.py  # Custom fields management
│   │   ├── workflows.py      # Automation engine
│   │   ├── forecasting.py    # AI predictions
│   │   ├── webhooks.py       # Shopify webhooks
│   │   ├── billing.py        # Subscription management
│   │   └── reports.py        # Analytics & reporting
│   ├── models.py             # Database models
│   ├── database.py           # Database configuration
│   ├── main.py               # FastAPI application
│   ├── workflow_engine.py    # Automation rules
│   ├── forecasting_engine.py # ML predictions
│   └── requirements.txt      # Python dependencies
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── utils/           # Utility functions
│   │   ├── context/         # Context providers
│   │   └── main.jsx         # App entry point
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration
├── docs/                     # Documentation
├── shopify.app.toml         # Shopify app config
└── README.md                # Project overview
```

---

## 🚀 **Core Features**

### **1. Custom Fields System**
- **Unlimited fields** per product/variant/location
- **11 field types**: text, number, date, select, multi-select, boolean, JSON, file, URL, email, phone
- **Validation rules**: required, min/max length, regex patterns
- **Conditional logic**: show/hide fields based on other values
- **Industry templates**: Pre-built field sets for 6 industries

**Technical Implementation:**
- JSONB storage in PostgreSQL for flexible schema
- Dynamic form generation based on field definitions
- Type-safe validation on both frontend and backend
- Indexed search capabilities on custom field data

### **2. AI-Powered Forecasting**
- **Machine Learning**: Uses scikit-learn for demand prediction
- **Seasonal Analysis**: Detects and adjusts for seasonal patterns
- **Confidence Intervals**: Risk assessment for predictions
- **Reorder Points**: Automated calculation with safety stock
- **Anomaly Detection**: Identifies unusual demand patterns

**Models Used:**
- Linear Regression for trend analysis
- Seasonal Decomposition for pattern recognition
- ARIMA for time series forecasting
- Random Forest for complex pattern detection

### **3. Workflow Automation**
- **Visual Builder**: Drag-and-drop rule creation
- **Event Triggers**: Inventory changes, orders, time-based
- **Complex Conditions**: AND/OR logic with nested rules
- **Actions**: Email alerts, reorder suggestions, price updates
- **Priority System**: Rule execution order management

**Rule Engine:**
```python
# Example workflow rule
{
  "trigger": "inventory_low",
  "conditions": [
    {"field": "quantity", "operator": "<=", "value": "reorder_point"},
    {"field": "category", "operator": "equals", "value": "electronics"}
  ],
  "actions": [
    {"type": "email", "recipient": "manager@store.com"},
    {"type": "reorder", "quantity": "suggested_order_qty"}
  ]
}
```

### **4. Multi-Location Intelligence**
- **Smart Distribution**: AI-powered stock allocation
- **Transfer Suggestions**: ROI-based recommendations
- **Performance Metrics**: Location-specific analytics
- **Utilization Optimization**: Efficient space usage
- **FIFO/LIFO**: Configurable inventory methods

### **5. Industry Templates**

#### **Apparel**
- Size, Color, Material, Season, Care Instructions, Brand

#### **Electronics**
- Warranty Period, Compatibility, Certifications, Model Number, Condition

#### **Food & Beverage**
- Expiration Date, Allergens, Storage Requirements, Nutrition Info, Batch Number

#### **Jewelry**
- Metal Type, Stone Type, Certification, Carat Weight, Setting Style

#### **Automotive**
- OEM Number, Fitment, Condition, Year Range, Brand

#### **Health & Beauty**
- Ingredients, FDA Approval, Skin Type, Expiration, Safety Warnings

---

## 🔧 **Setup & Installation**

### **Prerequisites**
- Node.js 18+ (for Shopify CLI and frontend)
- Python 3.12+ (for backend)
- PostgreSQL 14+ (for production)
- Shopify Partner Account
- Development store

### **1. Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### **2. Frontend Setup**
```bash
cd frontend
npm install
```

### **3. Environment Configuration**
Create `.env` file in backend directory:
```env
# Shopify Configuration
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret
SHOPIFY_SCOPES=read_products,write_products,read_inventory,write_inventory,read_locations,read_orders

# Database
DATABASE_URL=postgresql://user:password@localhost/inventorysync
# or for development:
DATABASE_URL=sqlite:///inventorysync_dev.db

# Application
SECRET_KEY=your_secret_key
DEBUG=True
CORS_ORIGINS=*

# Webhooks
WEBHOOK_SECRET=your_webhook_secret
```

### **4. Database Setup**
```bash
# For PostgreSQL
python3 -m alembic upgrade head

# For SQLite (development)
python3 init_db.py
```

### **5. Start Development Servers**
```bash
# Backend (Terminal 1)
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (Terminal 2)
cd frontend
npm run dev
```

---

## 🧪 **Testing**

### **Automated Testing**
```bash
# Run all tests
./test-complete-app.sh

# Individual test suites
cd backend
python3 -m pytest tests/

# Frontend tests
cd frontend
npm test
```

### **Manual Testing Checklist**
- [ ] OAuth flow with development store
- [ ] Product sync from Shopify
- [ ] Custom field creation and validation
- [ ] Workflow rule execution
- [ ] Webhook delivery and processing
- [ ] Forecasting with sample data
- [ ] Multi-location transfer suggestions
- [ ] Billing subscription flow

---

## 🐛 **Known Issues & Fixes**

### **Issue: Shopify Polaris Stack Import Error**
**Error:** `The requested module '/node_modules/.vite/deps/@shopify_polaris.js?v=0486c104' does not provide an export named 'Stack'`

**Cause:** Polaris v12+ deprecated `Stack` component

**Fix:** Replace with `BlockStack` and `InlineStack`:
```jsx
// Before (deprecated)
import { Stack } from '@shopify/polaris';
<Stack vertical spacing="loose">
  <Stack spacing="tight">

// After (v12+)
import { BlockStack, InlineStack } from '@shopify/polaris';
<BlockStack gap="500">
  <InlineStack gap="200">
```

**Files to update:**
- `frontend/src/components/CacheManager.jsx` ✅ Fixed
- `frontend/src/components/CustomFieldsManager.jsx`
- `frontend/src/components/Inventory.jsx`
- `frontend/src/components/Settings.jsx`
- `frontend/src/components/Navigation.jsx`
- And others...

### **Issue: Webhook Authentication Failures**
**Fix:** Ensure HMAC verification is properly implemented:
```python
def verify_webhook(data, hmac_header):
    digest = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        data,
        digestmod=hashlib.sha256
    ).digest()
    computed_hmac = base64.b64encode(digest)
    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))
```

---

## 💰 **Pricing & Business Model**

### **Subscription Tiers**

#### **Starter Plan - $29/month**
- Up to 1,000 products
- 5 custom fields per product
- Basic workflow automation
- Email support
- 1 industry template

#### **Growth Plan - $99/month** ⭐ Most Popular
- Up to 10,000 products
- Unlimited custom fields
- Advanced workflow automation
- AI forecasting included
- Live chat support
- All industry templates
- Multi-location support

#### **Pro Plan - $299/month**
- Unlimited products
- Unlimited everything
- Custom workflow development
- Priority support
- API access
- Custom integrations
- Dedicated account manager

### **Revenue Projections**
- **Month 1**: 10 customers × $50 avg = $500 MRR
- **Month 6**: 150 customers × $60 avg = $9,000 MRR
- **Month 12**: 300 customers × $65 avg = $19,500 MRR
- **Target**: 1,000 customers = $65,000 MRR ($780K ARR)

---

## 🏆 **Competitive Analysis**

| Feature | InventorySync | TradeGecko | Cin7 | Unleashed |
|---------|---------------|------------|------|-----------|
| **Monthly Price** | $29-99 | $299+ | $325+ | $380+ |
| **Custom Fields** | ✅ Unlimited | ❌ Limited | ❌ 10 max | ❌ 5 max |
| **AI Forecasting** | ✅ Included | 💰 Extra cost | 💰 Extra cost | ❌ None |
| **Setup Time** | ⚡ 10 minutes | ⏳ 2-3 days | ⏳ 1-2 weeks | ⏳ 1-2 weeks |
| **Industry Templates** | ✅ 6 templates | ❌ None | ❌ None | ❌ None |
| **Workflow Automation** | ✅ Visual builder | ⚠️ Code required | ⚠️ Limited | ❌ None |
| **Shopify Native** | ✅ Yes | ❌ Third-party | ❌ Third-party | ❌ Third-party |

---

## 📊 **API Documentation**

### **Authentication Endpoints**
```
GET  /api/auth/install       # Initiate OAuth flow
GET  /api/auth/callback      # Handle OAuth callback
POST /api/auth/verify        # Verify session token
GET  /api/auth/status        # Check authentication status
```

### **Product Management**
```
GET    /api/v1/products              # List products
POST   /api/v1/products              # Create product
GET    /api/v1/products/{id}         # Get product details
PUT    /api/v1/products/{id}         # Update product
DELETE /api/v1/products/{id}         # Delete product
POST   /api/v1/products/sync         # Sync from Shopify
```

### **Custom Fields**
```
GET    /api/v1/custom-fields         # List field definitions
POST   /api/v1/custom-fields         # Create field definition
PUT    /api/v1/custom-fields/{id}    # Update field definition
DELETE /api/v1/custom-fields/{id}    # Delete field definition
POST   /api/v1/custom-fields/validate # Validate field data
```

### **Workflows**
```
GET    /api/v1/workflows             # List workflow rules
POST   /api/v1/workflows             # Create workflow rule
PUT    /api/v1/workflows/{id}        # Update workflow rule
DELETE /api/v1/workflows/{id}        # Delete workflow rule
POST   /api/v1/workflows/{id}/test   # Test workflow rule
```

### **Forecasting**
```
GET    /api/v1/forecasts/{product_id}    # Get demand forecast
POST   /api/v1/forecasts/generate        # Generate new forecasts
GET    /api/v1/forecasts/accuracy        # Get forecast accuracy
PUT    /api/v1/forecasts/settings        # Update forecast settings
```

---

## 🚀 **Deployment**

### **Production Deployment (Railway)**
1. Connect GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Configure PostgreSQL addon
4. Deploy with automatic builds on push

### **Docker Deployment**
```bash
# Build backend
docker build -t inventorysync-backend ./backend

# Build frontend
docker build -t inventorysync-frontend ./frontend

# Run with docker-compose
docker-compose up -d
```

### **Environment Variables**
```env
# Production
SHOPIFY_API_KEY=your_production_key
SHOPIFY_API_SECRET=your_production_secret
DATABASE_URL=postgresql://prod_url
WEBHOOK_SECRET=your_production_secret
DEBUG=False
CORS_ORIGINS=https://your-domain.com
```

---

## 📈 **Performance Optimizations**

### **Database Optimizations**
- **Indexes**: Custom field queries, product searches
- **Connection Pooling**: SQLAlchemy connection management
- **Query Optimization**: N+1 query prevention
- **Caching**: Redis for frequently accessed data

### **Frontend Optimizations**
- **Code Splitting**: Lazy loading of components
- **Memoization**: React.memo for expensive renders
- **Virtual Scrolling**: Large product lists
- **Image Optimization**: WebP format, lazy loading

### **API Optimizations**
- **Pagination**: Cursor-based for large datasets
- **Rate Limiting**: Prevent API abuse
- **Compression**: Gzip response compression
- **CDN**: Static asset delivery

---

## 🔒 **Security**

### **Authentication & Authorization**
- **OAuth 2.0**: Shopify-standard authentication
- **HMAC Verification**: Webhook authenticity
- **Session Management**: Secure token handling
- **Role-based Access**: Admin/user permissions

### **Data Protection**
- **Encryption**: TLS 1.3 for data in transit
- **Input Validation**: All user inputs sanitized
- **SQL Injection**: Parameterized queries only
- **XSS Protection**: Content Security Policy
- **Rate Limiting**: DDoS protection

### **Compliance**
- **GDPR**: Data privacy compliance
- **SOC 2**: Security audit requirements
- **PCI DSS**: Payment data security
- **CCPA**: California privacy rights

---

## 🎯 **Roadmap**

### **Q1 2025**
- [ ] Fix all Polaris v12 compatibility issues
- [ ] Implement advanced forecasting models
- [ ] Add multi-currency support
- [ ] Create mobile-responsive dashboard

### **Q2 2025**
- [ ] Launch Shopify App Store
- [ ] Add integrations (Amazon, eBay, etc.)
- [ ] Implement advanced analytics
- [ ] Add team collaboration features

### **Q3 2025**
- [ ] AI-powered demand sensing
- [ ] Supplier integration API
- [ ] Advanced reporting suite
- [ ] White-label solution

### **Q4 2025**
- [ ] International expansion
- [ ] Enterprise features
- [ ] Advanced workflow automation
- [ ] Predictive maintenance

---

## 🤝 **Contributing**

### **Development Guidelines**
1. **Code Style**: Follow PEP 8 (Python), ESLint (JavaScript)
2. **Testing**: Minimum 80% code coverage
3. **Documentation**: Update docs for all changes
4. **Commits**: Conventional commit format

### **Pull Request Process**
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📞 **Support**

### **Documentation**
- **API Docs**: Available at `/docs` endpoint
- **User Guide**: Comprehensive setup instructions
- **Video Tutorials**: Coming soon

### **Contact**
- **Email**: support@prestigecorp.au
- **GitHub Issues**: For bug reports and feature requests
- **Business Inquiries**: contact@prestigecorp.au

---

**Created by Brendan Sumner and Claude Code**

*Last Updated: July 2025*