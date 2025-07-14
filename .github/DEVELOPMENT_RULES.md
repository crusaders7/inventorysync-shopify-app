# InventorySync Development Rules & Guidelines

## 🔐 Security Rules

### 1. Environment Variables
- **NEVER** commit `.env` files to git
- Use `.env.example` as a template
- All secrets must be in environment variables
- Use strong, randomly generated keys (minimum 256-bit)

### 2. Authentication
- Always use JWT tokens for API authentication
- Tokens must expire (default: 30 minutes)
- Implement refresh token mechanism
- Use HTTPS in production

### 3. Database
- Never store passwords in plain text
- Use parameterized queries (SQLAlchemy ORM)
- Implement row-level security where needed
- Regular backups in production

## 📁 File & Code Conventions

### 1. Naming Conventions
```
- Python files: snake_case.py
- React components: PascalCase.jsx
- CSS modules: component-name.module.css
- API endpoints: /api/v1/resource-name
- Database tables: plural_snake_case
- Environment variables: UPPER_SNAKE_CASE
```

### 2. Project Structure
```
backend/
  ├── api/          # Route handlers
  ├── models/       # Database models
  ├── services/     # Business logic
  ├── utils/        # Helper functions
  └── tests/        # Test files

frontend/
  ├── components/   # Reusable components
  ├── pages/        # Page components
  ├── hooks/        # Custom hooks
  ├── utils/        # Helper functions
  └── tests/        # Test files
```

### 3. Import Order
```python
# Python
import os  # Standard library
import sys

import requests  # Third-party
from fastapi import FastAPI

from models import User  # Local
from utils import helpers
```

```javascript
// JavaScript/React
import React from 'react';  // React
import { Card } from '@shopify/polaris';  // Third-party

import Dashboard from './components/Dashboard';  // Local
import { formatDate } from './utils/helpers';
```

## 🌿 Git Workflow

### 1. Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Emergency fixes

### 2. Commit Messages
```
feat: Add custom fields API endpoint
fix: Resolve inventory sync issue
docs: Update API documentation
style: Format code with Black
refactor: Optimize database queries
test: Add unit tests for auth
chore: Update dependencies
```

### 3. Pull Request Rules
- Must pass all tests
- Requires code review
- Update documentation
- No merge conflicts
- Follow PR template

## 🧪 Testing Requirements

### 1. Test Coverage
- Minimum 80% code coverage
- All new features must have tests
- Critical paths require integration tests

### 2. Test Types
```python
# Unit Tests
test_models.py
test_services.py
test_utils.py

# Integration Tests
test_api_endpoints.py
test_shopify_sync.py

# E2E Tests
test_user_workflows.py
```

## 📝 Documentation Standards

### 1. Code Documentation
```python
def calculate_reorder_point(
    lead_time: int,
    daily_usage: float,
    safety_stock: int = 0
) -> int:
    """
    Calculate the reorder point for inventory.
    
    Args:
        lead_time: Days to receive new inventory
        daily_usage: Average daily usage rate
        safety_stock: Buffer stock (default: 0)
        
    Returns:
        int: The reorder point quantity
        
    Example:
        >>> calculate_reorder_point(7, 10.5, 20)
        94
    """
    return int(lead_time * daily_usage + safety_stock)
```

### 2. API Documentation
- Use OpenAPI/Swagger annotations
- Include request/response examples
- Document all error codes
- Specify rate limits

## 🚀 Deployment Checklist

### Pre-deployment
- [ ] All tests passing
- [ ] Security scan completed
- [ ] Performance testing done
- [ ] Documentation updated
- [ ] Environment variables configured
- [ ] Database migrations ready

### Post-deployment
- [ ] Smoke tests passing
- [ ] Monitoring active
- [ ] Logs accessible
- [ ] Backups verified
- [ ] SSL certificates valid

## 🔧 Development Environment

### 1. Required Tools
- Python 3.10+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+
- Docker (for deployment)
- Git

### 2. VS Code Extensions
- Python (ms-python.python)
- ESLint (dbaeumer.vscode-eslint)
- Prettier (esbenp.prettier-vscode)
- GitLens (eamodio.gitlens)
- PostgreSQL (ckolkman.vscode-postgres)

### 3. Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.0.0
    hooks:
      - id: eslint
```

## 📊 Performance Guidelines

### 1. Backend
- Use database indexes on frequently queried fields
- Implement caching for expensive operations
- Paginate large result sets
- Use async operations where possible

### 2. Frontend
- Lazy load components
- Implement virtual scrolling for large lists
- Optimize images (WebP format)
- Use React.memo for expensive components

## 🔍 Monitoring & Logging

### 1. Logging Levels
```python
# Development
LOG_LEVEL = "DEBUG"

# Production
LOG_LEVEL = "INFO"  # or "WARNING"
```

### 2. What to Log
- API requests (method, path, duration)
- Database queries (slow queries)
- Error traces with context
- User actions (for audit trail)
- External API calls

### 3. What NOT to Log
- Passwords or tokens
- Personal information (PII)
- Credit card numbers
- API secrets

## 🛡️ Security Best Practices

1. **Input Validation**
   - Validate all user inputs
   - Use Pydantic models for validation
   - Sanitize data before storage

2. **Rate Limiting**
   - Implement per-user rate limits
   - Use Redis for distributed rate limiting
   - Return 429 status when exceeded

3. **CORS Policy**
   - Restrict origins in production
   - Use specific methods, not wildcards
   - Include credentials only when necessary

4. **SQL Injection Prevention**
   - Always use ORM or parameterized queries
   - Never concatenate SQL strings
   - Validate input types

## 📱 Shopify-Specific Rules

1. **API Compliance**
   - Respect rate limits (2 requests/second)
   - Use webhooks for real-time updates
   - Implement exponential backoff

2. **App Bridge**
   - Use App Bridge for embedded apps
   - Follow Polaris design guidelines
   - Ensure mobile responsiveness

3. **Billing**
   - Use Shopify Billing API
   - Clear pricing display
   - Handle subscription changes gracefully

## 🚨 Emergency Procedures

### 1. Security Breach
1. Rotate all API keys immediately
2. Audit recent access logs
3. Notify affected users
4. Document incident

### 2. Data Loss
1. Stop write operations
2. Restore from latest backup
3. Verify data integrity
4. Investigate root cause

### 3. Performance Crisis
1. Enable emergency caching
2. Increase server resources
3. Disable non-critical features
4. Monitor and optimize

---

**Last Updated**: July 12, 2025
**Version**: 1.0
