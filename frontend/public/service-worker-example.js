/**
 * Example Service Worker with Cache Clearing Support
 * 
 * This is an example of how to implement cache clearing in a service worker.
 * If you have a service worker in your app, add the message listener below.
 */

// Cache names
const CACHE_NAME = 'inventorysync-v1';
const API_CACHE_NAME = 'api-cache-v1';
const STATIC_CACHE_NAME = 'static-cache-v1';

// Listen for messages from the main thread
self.addEventListener('message', async (event) => {
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    console.log('[Service Worker] Received CLEAR_CACHE message');
    
    try {
      // Get all cache names
      const cacheNames = await caches.keys();
      
      // Delete all caches
      await Promise.all(
        cacheNames.map(cacheName => {
          console.log(`[Service Worker] Deleting cache: ${cacheName}`);
          return caches.delete(cacheName);
        })
      );
      
      // Send confirmation back to the main thread
      if (event.ports && event.ports[0]) {
        event.ports[0].postMessage({
          type: 'CACHE_CLEARED',
          success: true
        });
      }
      
      console.log('[Service Worker] All caches cleared successfully');
    } catch (error) {
      console.error('[Service Worker] Error clearing caches:', error);
      
      if (event.ports && event.ports[0]) {
        event.ports[0].postMessage({
          type: 'CACHE_CLEARED',
          success: false,
          error: error.message
        });
      }
    }
  }
});

// Example fetch event handler with caching
self.addEventListener('fetch', (event) => {
  // Skip cache for cache-busting requests
  if (event.request.url.includes('?clearCache=true')) {
    event.respondWith(fetch(event.request));
    return;
  }
  
  // Example caching strategy (you can customize this)
  if (event.request.url.includes('/api/')) {
    // Network first for API requests
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Clone the response before caching
          const responseToCache = response.clone();
          
          caches.open(API_CACHE_NAME).then(cache => {
            cache.put(event.request, responseToCache);
          });
          
          return response;
        })
        .catch(() => {
          // Fallback to cache if network fails
          return caches.match(event.request);
        })
    );
  } else {
    // Cache first for static assets
    event.respondWith(
      caches.match(event.request).then(response => {
        return response || fetch(event.request).then(fetchResponse => {
          return caches.open(STATIC_CACHE_NAME).then(cache => {
            cache.put(event.request, fetchResponse.clone());
            return fetchResponse;
          });
        });
      })
    );
  }
});

// Clean up old caches on activate
self.addEventListener('activate', (event) => {
  const cacheWhitelist = [CACHE_NAME, API_CACHE_NAME, STATIC_CACHE_NAME];
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (!cacheWhitelist.includes(cacheName)) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
