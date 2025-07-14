/**
 * Clear Cache Utility
 * Clears all caching mechanisms to ensure old API endpoints are not used
 * 
 * Features:
 * - Service Worker cache clearing
 * - Custom API response cache clearing
 * - Browser storage clearing (localStorage, sessionStorage, cookies)
 * - IndexedDB clearing
 * - Command-line triggerable via Node.js script
 */

// Clear all browser storage
export const clearAllStorage = () => {
  console.log('Clearing all browser storage...');
  
  // Clear localStorage
  try {
    localStorage.clear();
    console.log('✓ localStorage cleared');
  } catch (e) {
    console.error('Failed to clear localStorage:', e);
  }
  
  // Clear sessionStorage
  try {
    sessionStorage.clear();
    console.log('✓ sessionStorage cleared');
  } catch (e) {
    console.error('Failed to clear sessionStorage:', e);
  }
  
  // Clear cookies for current domain
  try {
    document.cookie.split(";").forEach((c) => {
      document.cookie = c
        .replace(/^ +/, "")
        .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
    });
    console.log('✓ Cookies cleared');
  } catch (e) {
    console.error('Failed to clear cookies:', e);
  }
};

// Clear all caches including Cache API
export const clearAllCaches = async () => {
  console.log('Clearing all caches...');
  
  // Clear Cache API (used by service workers and fetch)
  if ('caches' in window) {
    try {
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames.map((cacheName) => {
          console.log(`Deleting cache: ${cacheName}`);
          return caches.delete(cacheName);
        })
      );
      console.log('✓ Cache API cleared');
    } catch (e) {
      console.error('Failed to clear Cache API:', e);
    }
  }
};

// Clear service worker caches specifically
export const clearServiceWorkerCaches = async () => {
  console.log('Clearing service worker caches...');
  
  if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
    try {
      // Send message to service worker to clear its caches
      navigator.serviceWorker.controller.postMessage({
        type: 'CLEAR_CACHE'
      });
      
      // Also clear all caches from the main thread
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        const swCaches = cacheNames.filter(name => 
          name.includes('workbox') || 
          name.includes('sw-') || 
          name.includes('api-cache') ||
          name.includes('static-cache')
        );
        
        await Promise.all(
          swCaches.map((cacheName) => {
            console.log(`Deleting SW cache: ${cacheName}`);
            return caches.delete(cacheName);
          })
        );
      }
      
      console.log('✓ Service worker caches cleared');
    } catch (e) {
      console.error('Failed to clear service worker caches:', e);
    }
  }
};

// Clear custom API response caches
export const clearAPIResponseCaches = async () => {
  console.log('Clearing API response caches...');
  
  try {
    // Clear any cached API responses from localStorage
    const keys = Object.keys(localStorage);
    const apiCacheKeys = keys.filter(key => 
      key.startsWith('api-cache-') || 
      key.startsWith('cache-') ||
      key.includes('apiResponse') ||
      key.includes('fetchCache')
    );
    
    apiCacheKeys.forEach(key => {
      localStorage.removeItem(key);
      console.log(`Removed API cache: ${key}`);
    });
    
    // Clear any cached API responses from sessionStorage
    const sessionKeys = Object.keys(sessionStorage);
    const sessionApiCacheKeys = sessionKeys.filter(key => 
      key.startsWith('api-cache-') || 
      key.startsWith('cache-') ||
      key.includes('apiResponse') ||
      key.includes('fetchCache')
    );
    
    sessionApiCacheKeys.forEach(key => {
      sessionStorage.removeItem(key);
      console.log(`Removed session API cache: ${key}`);
    });
    
    // Clear API caches from Cache API
    if ('caches' in window) {
      const cacheNames = await caches.keys();
      const apiCaches = cacheNames.filter(name => 
        name.includes('api') || 
        name.includes('data') ||
        name.includes('fetch')
      );
      
      await Promise.all(
        apiCaches.map((cacheName) => {
          console.log(`Deleting API cache: ${cacheName}`);
          return caches.delete(cacheName);
        })
      );
    }
    
    console.log('✓ API response caches cleared');
  } catch (e) {
    console.error('Failed to clear API response caches:', e);
  }
};

// Unregister all service workers
export const unregisterServiceWorkers = async () => {
  console.log('Unregistering service workers...');
  
  if ('serviceWorker' in navigator) {
    try {
      const registrations = await navigator.serviceWorker.getRegistrations();
      await Promise.all(
        registrations.map((registration) => {
          console.log(`Unregistering service worker: ${registration.scope}`);
          return registration.unregister();
        })
      );
      console.log('✓ Service workers unregistered');
    } catch (e) {
      console.error('Failed to unregister service workers:', e);
    }
  }
};

// Force reload without cache
export const forceReload = () => {
  console.log('Force reloading without cache...');
  window.location.reload(true);
};

// Clear IndexedDB
export const clearIndexedDB = async () => {
  console.log('Clearing IndexedDB...');
  
  if ('indexedDB' in window) {
    try {
      const databases = await indexedDB.databases();
      await Promise.all(
        databases.map((db) => {
          console.log(`Deleting IndexedDB: ${db.name}`);
          return indexedDB.deleteDatabase(db.name);
        })
      );
      console.log('✓ IndexedDB cleared');
    } catch (e) {
      console.error('Failed to clear IndexedDB:', e);
    }
  }
};

// Clear all caching mechanisms
export const clearAllCachingMechanisms = async () => {
  console.log('=== Starting complete cache clear ===');
  
  try {
    // Clear storage
    clearAllStorage();
    
    // Clear all caches
    await clearAllCaches();
    
    // Clear service worker caches specifically
    await clearServiceWorkerCaches();
    
    // Clear API response caches
    await clearAPIResponseCaches();
    
    // Unregister service workers
    await unregisterServiceWorkers();
    
    // Clear IndexedDB
    await clearIndexedDB();
    
    console.log('=== Cache clear complete ===');
    console.log('Note: You may need to hard refresh (Ctrl+Shift+R or Cmd+Shift+R) to ensure all caches are cleared.');
    
    return { success: true, message: 'All caches cleared successfully' };
  } catch (error) {
    console.error('Error during cache clear:', error);
    return { success: false, error: error.message };
  }
};

// Function to be called from Node.js command line script
export const clearCacheFromCLI = async () => {
  // This function is designed to be called from a Node.js environment
  // It returns a promise that resolves with the result
  return await clearAllCachingMechanisms();
};

// Auto-clear on module load if query parameter is present
if (typeof window !== 'undefined') {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('clearCache') === 'true') {
    clearAllCachingMechanisms().then(() => {
      // Remove the clearCache parameter from URL
      urlParams.delete('clearCache');
      const newUrl = window.location.pathname + 
        (urlParams.toString() ? '?' + urlParams.toString() : '') + 
        window.location.hash;
      window.history.replaceState({}, '', newUrl);
    });
  }
}

export default {
  clearAllStorage,
  clearAllCaches,
  clearServiceWorkerCaches,
  clearAPIResponseCaches,
  unregisterServiceWorkers,
  forceReload,
  clearIndexedDB,
  clearAllCachingMechanisms,
  clearCacheFromCLI
};
