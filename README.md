# InventorySync Frontend (Next.js)

## Overview
Frontend for InventorySync, a Shopify inventory management app, built with Next.js and Polaris.

## Quick Start

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your settings
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

4. Access the app:
   - Frontend: http://localhost:3000
   - API docs: http://localhost:8000/docs

## Features

### Custom Fields
- Create and manage custom fields
- Field validation
- Template management
- Real-time updates

### Inventory Management
- Stock level tracking
- Multi-location support
- Automatic syncing
- Low stock alerts

### Dashboard
- Real-time stats
- Performance metrics
- Custom reports
- Analytics

## Tech Stack

- Next.js 14
- Shopify Polaris
- TypeScript
- React 18
- App Router
- API Routes

## Development

### File Structure
```
/src
  /app             # Next.js pages and API routes
  /components      # React components
  /utils           # Utility functions
  /types          # TypeScript types
  /hooks          # Custom React hooks
  /context        # React context providers
```

### API Routes
- `/api/custom-fields/*` - Custom fields management
- `/api/inventory/*` - Inventory operations
- `/api/auth/*` - Authentication endpoints

### Components
- CustomFieldsManager
- InventoryManager
- Dashboard
- Settings

## Contributing

1. Create feature branch
2. Make changes
3. Run tests
4. Submit PR

## Testing
```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage
```

## Deployment
```bash
# Build production
npm run build

# Start production server
npm start
```

## Environment Variables

Required variables:
- `BACKEND_URL`
- `NEXT_PUBLIC_SHOPIFY_API_KEY`
- `NEXT_PUBLIC_APP_URL`

Optional:
- `NODE_ENV`
- `PORT`

## Documentation

- [Next.js Migration Guide](./NEXTJS_MIGRATION.md)
- [API Documentation](../backend/docs/API_DOCUMENTATION.md)
- [Architecture Overview](../ARCHITECTURE.md)
