# InventorySync Testing Guide

## 🚀 Step-by-Step Testing Process

### Phase 1: Local Development Testing

#### 1.1 Start Local Servers
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2 - Frontend  
cd frontend
npm run dev

# Terminal 3 - Shopify CLI
npx shopify app dev
```

#### 1.2 Configure Development Store
1. When prompted by Shopify CLI, select or create a development store
2. The CLI will provide a URL like: `https://[store-name].myshopify.com`
3. Install the app on your development store

### Phase 2: Core Feature Testing

#### 2.1 OAuth Flow Testing ✓
1. **Install App**
   - Click "Install app" from Partner Dashboard
   - Verify OAuth redirect works
   - Check permissions are correctly requested
   - Confirm app is installed in store admin

2. **Uninstall/Reinstall**
   - Uninstall app from store settings
   - Reinstall and verify data persistence

#### 2.2 Custom Fields Management ✓
1. **Create Fields**
   - Go to any product in Shopify admin
   - Look for "Custom Fields" section/button
   - Create fields of each type:
     - Text field
     - Number field
     - Date field
     - Boolean (checkbox)
     - JSON field
     - URL field
     - Color picker

2. **Test Auto-Save**
   - Edit a field value
   - Navigate away without saving
   - Return and verify value persisted

3. **Conditional Fields**
   - Create a field that only shows for specific product types
   - Test with different products

#### 2.3 Bulk Operations Testing ✓
1. **Bulk Editor**
   - Select multiple products (start with 10-20)
   - Open bulk editor
   - Edit fields across all products
   - Verify changes saved

2. **Large Catalog Test**
   - Import 1000+ test products (use CSV)
   - Test bulk operations performance
   - Monitor for timeouts

3. **Import/Export**
   - Export products with custom fields to CSV
   - Modify CSV file
   - Import back and verify changes

#### 2.4 Template Testing ✓
1. **Apply Templates**
   - Test each industry template:
     - Fashion
     - Electronics
     - Food & Beverage
   - Verify fields are created correctly

2. **Custom Templates**
   - Create a custom template
   - Save and apply to products

### Phase 3: API Testing

#### 3.1 REST API Endpoints
Test each endpoint using Postman or curl:

```bash
# Health check
curl https://inventorysync.prestigecorp.au/api/v1/health

# Get metafield definitions
curl https://inventorysync.prestigecorp.au/api/metafields/definitions

# Create a metafield
curl -X POST https://inventorysync.prestigecorp.au/api/metafields/definitions \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Shop-Domain: your-store.myshopify.com" \
  -d '{"key": "test_field", "type": "text", "namespace": "custom"}'
```

#### 3.2 Webhook Testing
1. **Product Updates**
   - Update a product in Shopify admin
   - Verify webhook fires and custom fields sync

2. **Bulk Updates**
   - Use Shopify bulk editor
   - Verify webhooks handle multiple updates

### Phase 4: Performance Testing

#### 4.1 Load Testing
```bash
# Install Apache Bench if needed
sudo apt-get install apache2-utils

# Test API endpoints
ab -n 1000 -c 10 https://inventorysync.prestigecorp.au/api/v1/health
```

#### 4.2 Database Performance
1. Create 10,000+ products with custom fields
2. Test query performance
3. Monitor response times

### Phase 5: Security Testing

#### 5.1 Authentication
- [ ] Test with invalid tokens
- [ ] Test session expiration
- [ ] Verify CORS headers

#### 5.2 Data Validation
- [ ] Test SQL injection attempts
- [ ] Test XSS in field values
- [ ] Verify input sanitization

### Phase 6: UI/UX Testing

#### 6.1 Responsive Design
- [ ] Test on mobile devices
- [ ] Test on tablets
- [ ] Test different browsers (Chrome, Firefox, Safari)

#### 6.2 Shopify Polaris Compliance
- [ ] Verify UI matches Shopify design standards
- [ ] Test keyboard navigation
- [ ] Test screen reader compatibility

### Phase 7: Production Testing

#### 7.1 Deployment Verification
```bash
# Check production endpoints
curl https://inventorysync.prestigecorp.au/
curl https://inventorysync.prestigecorp.au/api/v1/health
curl https://inventorysync.prestigecorp.au/docs
```

#### 7.2 SSL Certificate
```bash
# Verify SSL
openssl s_client -connect inventorysync.prestigecorp.au:443
```

### Phase 8: GDPR Compliance Testing

#### 8.1 Data Request
1. Trigger customer data request webhook
2. Verify response format
3. Check data completeness

#### 8.2 Data Deletion
1. Trigger customer redact webhook
2. Verify data is properly deleted
3. Confirm audit log entry

### Phase 9: Billing Testing

#### 9.1 Subscription Flow
1. Test free trial activation
2. Test plan selection
3. Test upgrade/downgrade
4. Test cancellation

#### 9.2 Usage Limits
1. Test plan limits enforcement
2. Test overage handling
3. Test billing notifications

## 📝 Testing Checklist Summary

### Critical Tests (Must Pass)
- [ ] OAuth installation flow
- [ ] Custom field CRUD operations
- [ ] Auto-save functionality
- [ ] Bulk operations (100+ products)
- [ ] Webhook processing
- [ ] GDPR compliance
- [ ] SSL/Security headers

### Important Tests
- [ ] Template functionality
- [ ] Import/Export
- [ ] API rate limiting
- [ ] Mobile responsiveness
- [ ] Cross-browser compatibility

### Nice to Have
- [ ] Load testing (1000+ concurrent users)
- [ ] Accessibility testing
- [ ] Internationalization

## 🐛 Known Issues to Test

1. **Large File Uploads**: Test CSV imports > 10MB
2. **Concurrent Edits**: Multiple users editing same product
3. **Network Interruptions**: Test auto-save during connection loss
4. **Theme Compatibility**: Test with popular themes

## 📊 Performance Benchmarks

Target metrics:
- Page load: < 2 seconds
- API response: < 200ms
- Bulk operations: 1000 products/minute
- Webhook processing: < 500ms

## 🚨 What to Do If Tests Fail

1. **Document the issue**:
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots/videos
   - Error messages

2. **Check logs**:
   ```bash
   # Backend logs
   tail -f backend/server.log
   
   # Frontend console
   # Open browser DevTools
   ```

3. **Common fixes**:
   - Clear cache: `npm run clean`
   - Restart services
   - Check environment variables
   - Verify database connection

## 📤 After Testing

1. **Update checklist**: Mark completed items in SHOPIFY_APP_STORE_CHECKLIST.md
2. **Fix critical issues**: Address any blockers
3. **Document results**: Create test report
4. **Prepare for submission**: Ensure all requirements met

---

## Manual Testing Instructions

Since I can't click buttons or interact with the UI, here's what you need to do:

1. **Start the local development servers** (follow commands above)
2. **Install the app on your development store**
3. **Go through each test scenario** and verify functionality
4. **Document any issues** you encounter
5. **Let me know the results** so I can help fix any problems

Ready to start? Begin with Phase 1 and work your way through!
