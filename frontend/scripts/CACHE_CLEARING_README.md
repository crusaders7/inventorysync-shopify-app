# Cache Clearing Utility Documentation

## Overview

The cache clearing utility provides comprehensive cache management for the InventorySync Shopify app. It ensures that old API endpoints and cached data are properly cleared to prevent stale data issues.

## Features

1. **Service Worker Cache Clearing** - Clears all service worker caches including workbox, sw-, api-cache, and static-cache prefixed caches
2. **Custom API Response Cache Clearing** - Removes cached API responses from localStorage, sessionStorage, and Cache API
3. **Browser Storage Clearing** - Clears localStorage, sessionStorage, and cookies
4. **IndexedDB Clearing** - Removes all IndexedDB databases
5. **Command-line Support** - Can be triggered via Node.js CLI script

## Usage

### From the Browser

The cache clearing utility automatically runs when the app is loaded with the `?clearCache=true` query parameter:

```
http://localhost:3000?clearCache=true
```

### From the Command Line

Use npm scripts:

```bash
# Clear cache via browser (opens browser with clearCache parameter)
npm run clear-cache

# Clear cache via API endpoint
npm run clear-cache:api

# Clear both browser and API caches
npm run clear-cache:all
```

Or run the script directly:

```bash
# Show help
node scripts/clear-cache-cli.js --help

# Clear via browser
node scripts/clear-cache-cli.js --browser

# Clear via API
node scripts/clear-cache-cli.js --api

# Clear both
node scripts/clear-cache-cli.js --browser --api
```

### Programmatically in JavaScript

```javascript
import clearCache from '../utils/clearCache';

// Clear all caches
await clearCache.clearAllCachingMechanisms();

// Clear specific cache types
await clearCache.clearServiceWorkerCaches();
await clearCache.clearAPIResponseCaches();
clearCache.clearAllStorage();
await clearCache.clearIndexedDB();
```

## Cache Types Cleared

### Service Worker Caches
- Workbox caches (workbox-*)
- Service worker caches (sw-*)
- API caches (api-cache-*)
- Static caches (static-cache-*)

### API Response Caches
- localStorage keys starting with: api-cache-, cache-, or containing apiResponse, fetchCache
- sessionStorage keys with the same patterns
- Cache API caches containing: api, data, or fetch

### Browser Storage
- All localStorage entries
- All sessionStorage entries
- All cookies for the current domain

### IndexedDB
- All IndexedDB databases

## Implementation Details

### Async Operation Handling

All cache clearing operations are properly wrapped in try-catch blocks and use async/await for proper error handling:

```javascript
export const clearAllCachingMechanisms = async () => {
  try {
    // Clear operations...
    return { success: true, message: 'All caches cleared successfully' };
  } catch (error) {
    console.error('Error during cache clear:', error);
    return { success: false, error: error.message };
  }
};
```

### Service Worker Communication

The utility sends messages to active service workers to trigger cache clearing:

```javascript
navigator.serviceWorker.controller.postMessage({
  type: 'CLEAR_CACHE'
});
```

## Environment Variables

The CLI script supports the following environment variables:

- `FRONTEND_URL` - Frontend app URL (default: http://localhost:3000)
- `API_URL` - Backend API URL (default: http://localhost:5001)

## Notes

- After clearing caches, a hard refresh (Ctrl+Shift+R or Cmd+Shift+R) may still be required
- The browser-based clearing only works when the app is running
- API-based clearing requires the backend server to implement a `/api/cache/clear` endpoint
