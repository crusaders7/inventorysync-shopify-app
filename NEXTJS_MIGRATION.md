# Next.js Migration Guide

## Overview
This document describes the migration from Vite to Next.js for the InventorySync frontend.

## Key Changes

### Directory Structure
```
/frontend-next/
├── src/
│   ├── app/                 # Next.js app router
│   │   ├── api/            # API routes
│   │   ├── custom-fields/  # Custom fields page
│   │   ├── layout.tsx     # Root layout with Polaris provider
│   │   └── page.tsx       # Root page (redirects to custom-fields)
│   └── components/         # React components
```

### Features
1. **File-based Routing**
   - Pages defined by directory structure
   - API routes in `app/api` directory
   - Automatic route handling

2. **API Integration**
   - API routes proxy to backend
   - Type-safe API endpoints
   - Improved error handling

3. **Authentication**
   - Retains existing OAuth flow
   - Shopify App Bridge integration
   - Session management

### Running the Application

1. Start the backend:
   ```bash
   cd ../backend
   source venv/bin/activate
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Start the Next.js frontend:
   ```bash
   cd frontend-next
   npm run dev
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - API: http://localhost:3000/api/*
   - Backend: http://localhost:8000

### Environment Variables
```env
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_SHOPIFY_API_KEY=development_key
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Benefits of Next.js
1. **Better Performance**
   - Server-side rendering
   - Automatic code splitting
   - Image optimization

2. **Developer Experience**
   - TypeScript support
   - File-based routing
   - API routes

3. **Polaris Compatibility**
   - Improved modal handling
   - Better component rendering
   - Consistent styling

4. **Built-in Features**
   - API routes
   - Environment variables
   - TypeScript support
   - Static file serving

### Future Improvements
1. Add more API routes
2. Implement server-side rendering for SEO
3. Add static page generation
4. Implement middleware for auth
5. Add error boundaries
6. Improve type safety

## Notes
- The backend API remains unchanged
- OAuth flow remains the same
- Existing authentication still works
- API routes proxy to backend
