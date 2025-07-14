# Test Installation Guide

## 1. Test OAuth Flow

To test the installation flow, use this URL format:

```
https://inventorysync-shopify-app-production.up.railway.app/api/v1/auth/install?shop=YOUR-SHOP.myshopify.com
```

Replace `YOUR-SHOP` with your development store subdomain.

### Alternative endpoints to test:
- `/api/auth/install?shop=YOUR-SHOP.myshopify.com`
- `/auth/install?shop=YOUR-SHOP.myshopify.com`

## 2. Test API Endpoints

After installation, test these key endpoints:

### Health Check
```bash
curl https://inventorysync-shopify-app-production.up.railway.app/health
```

### API Root
```bash
curl https://inventorysync-shopify-app-production.up.railway.app/api
```

### Get Products (requires auth)
```bash
curl -H "X-Shopify-Shop-Domain: YOUR-SHOP.myshopify.com" \
     -H "X-Shopify-Access-Token: YOUR-ACCESS-TOKEN" \
     https://inventorysync-shopify-app-production.up.railway.app/api/inventory/items
```

## 3. Test Webhook Registration

Check if webhooks are properly registered:

```bash
curl -X GET \
  -H "X-Shopify-Shop-Domain: YOUR-SHOP.myshopify.com" \
  -H "X-Shopify-Access-Token: YOUR-ACCESS-TOKEN" \
  https://inventorysync-shopify-app-production.up.railway.app/api/webhooks/
```

## 4. Common Issues & Solutions

### Issue: 404 on install
- Check that the auth router is properly registered
- Verify the URL path matches exactly

### Issue: Invalid redirect URI
- Ensure the redirect URL in Partners Dashboard matches exactly
- Include all variations (with and without /v1)

### Issue: CORS errors
- The security headers should handle this
- Check browser console for specific blocked origins

## 5. Verification Checklist

- [ ] OAuth flow completes successfully
- [ ] Access token is stored
- [ ] Webhooks are registered
- [ ] API endpoints return data
- [ ] GDPR webhooks respond with 200 OK
- [ ] Rate limiting headers present
- [ ] Security headers present
