/**
 * API Utility Functions
 * Centralized API calls for frontend-backend communication
 * Includes versioning support and cache management
 */

// Get API version from environment or default to v1
const API_VERSION = import.meta.env.VITE_API_VERSION || 'v1';
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_BASE_URL = `${API_BASE}/api/${API_VERSION}`;

// Cache management
let deploymentId = null;
let cacheVersion = null;

// Initialize API version and cache info
const initializeAPIVersion = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/version`);
    if (response.ok) {
      const versionInfo = await response.json();
      deploymentId = versionInfo.version_details.deployment_id;
      cacheVersion = versionInfo.version_details.cache_version;
      
      // Store in localStorage for cache invalidation
      const lastDeploymentId = localStorage.getItem('api_deployment_id');
      if (lastDeploymentId && lastDeploymentId !== deploymentId) {
        // New deployment detected - clear caches
        console.log('New deployment detected, clearing caches');
        if ('caches' in window) {
          caches.keys().then(names => {
            names.forEach(name => caches.delete(name));
          });
        }
      }
      localStorage.setItem('api_deployment_id', deploymentId);
      localStorage.setItem('api_cache_version', cacheVersion);
    }
  } catch (error) {
    console.error('Failed to initialize API version:', error);
  }
};

// Initialize on load
initializeAPIVersion();

// Helper function to get shop domain
const getShopDomain = () => {
  const params = new URLSearchParams(window.location.search);
  return params.get('shop') || localStorage.getItem('shopify_shop_domain') || '';
};

// Helper function to get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('shopify_access_token');
  const headers = {
    'Content-Type': 'application/json',
    // Cache-busting headers to prevent caching of API responses
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0',
    // Version headers
    'X-API-Version': API_VERSION,
    'X-Client-Version': import.meta.env.VITE_APP_VERSION || '1.0.0',
  };
  
  // Add deployment info if available
  if (deploymentId) {
    headers['X-Deployment-ID'] = deploymentId;
  }
  if (cacheVersion) {
    headers['X-Cache-Version'] = cacheVersion;
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

// Generic API call function
const apiCall = async (endpoint, options = {}) => {
  // Add cache-busting query parameter with version
  const separator = endpoint.includes('?') ? '&' : '?';
  const cacheBuster = `_t=${Date.now()}&_v=${cacheVersion || 'init'}`;
  const url = `${API_BASE_URL}${endpoint}${separator}${cacheBuster}`;
  
  const defaultOptions = {
    headers: getAuthHeaders(),
    // Ensure fetch doesn't use cache
    cache: 'no-store',
  };
  
  try {
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || error.message || 'API request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
};

// Auth API calls
export const authAPI = {
  getInstallUrl: () => apiCall('/auth/shopify/install'),
  
  handleCallback: async (code, shop, state) => {
    const params = new URLSearchParams({ code, shop, state });
    return apiCall(`/auth/shopify/callback?${params}`);
  },
  
  checkAuth: () => apiCall('/auth/check'),
  
  logout: () => apiCall('/auth/logout', { method: 'POST' }),
};

// Dashboard API calls
export const dashboardAPI = {
  getStats: (shop = null) => {
    const shopDomain = shop || getShopDomain();
    const params = shopDomain ? `?shop=${encodeURIComponent(shopDomain)}` : '';
    return apiCall(`/dashboard/stats${params}`);
  },
  
  getAnalytics: (shop = null) => {
    const shopDomain = shop || getShopDomain();
    const params = shopDomain ? `?shop=${encodeURIComponent(shopDomain)}` : '';
    return apiCall(`/dashboard/analytics${params}`);
  },
};

// Inventory API calls
export const inventoryAPI = {
  getProducts: (shop = null, params = {}) => {
    const shopDomain = shop || getShopDomain();
    const queryParams = new URLSearchParams({ shop: shopDomain, ...params });
    return apiCall(`/inventory/products?${queryParams}`);
  },
  
  updateInventory: (productId, updates) => {
    return apiCall(`/inventory/products/${productId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  },
  
  syncProducts: () => {
    const shopDomain = getShopDomain();
    return apiCall('/inventory/sync', {
      method: 'POST',
      body: JSON.stringify({ shop: shopDomain }),
    });
  },
  
  bulkUpdate: (updates) => {
    return apiCall('/inventory/bulk-update', {
      method: 'POST',
      body: JSON.stringify(updates),
    });
  },
};

// Alerts API calls
export const alertsAPI = {
  getAlerts: (shop = null, params = {}) => {
    const shopDomain = shop || getShopDomain();
    const queryParams = new URLSearchParams({ ...params });
    return apiCall(`/alerts/${shopDomain}?${queryParams}`);
  },
  
  createAlert: (shop, alertData) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/alerts/${shopDomain}`, {
      method: 'POST',
      body: JSON.stringify(alertData),
    });
  },
  
  updateAlert: (alertId, updates, shop = null) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/alerts/${alertId}?shop_domain=${shopDomain}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  },
  
  getAnalytics: (shop = null) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/alerts/analytics/${shopDomain}`);
  },
};

// Custom Fields API calls
export const customFieldsAPI = {
  getDefinitions: (shop = null) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/custom-fields/${shopDomain}`);
  },
  
  createDefinition: (fieldData) => {
    const shopDomain = getShopDomain();
    return apiCall(`/custom-fields/${shopDomain}`, {
      method: 'POST',
      body: JSON.stringify(fieldData),
    });
  },
  
  updateDefinition: (fieldId, updates) => {
    const shopDomain = getShopDomain();
    return apiCall(`/custom-fields/${shopDomain}/${fieldId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  },
  
  deleteDefinition: (fieldId) => {
    const shopDomain = getShopDomain();
    return apiCall(`/custom-fields/${shopDomain}/${fieldId}`, {
      method: 'DELETE',
    });
  },
  
  getFieldValues: (productId) => {
    return apiCall(`/custom-fields/values/product/${productId}`);
  },
  
  updateFieldValues: (productId, values) => {
    return apiCall(`/custom-fields/values/product/${productId}`, {
      method: 'PUT',
      body: JSON.stringify(values),
    });
  },
};

// Workflows API calls
export const workflowsAPI = {
  getWorkflows: (shop = null, params = {}) => {
    const shopDomain = shop || getShopDomain();
    const queryParams = new URLSearchParams({ ...params });
    return apiCall(`/workflows/${shopDomain}?${queryParams}`);
  },
  
  createWorkflow: (shop, workflowData) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/workflows/${shopDomain}`, {
      method: 'POST',
      body: JSON.stringify(workflowData),
    });
  },
  
  updateWorkflow: (workflowId, updates, shop = null) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/workflows/${workflowId}?shop_domain=${shopDomain}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  },
  
  deleteWorkflow: (workflowId, shop = null) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/workflows/${workflowId}?shop_domain=${shopDomain}`, {
      method: 'DELETE',
    });
  },
  
  getExecutionHistory: (workflowId, shop = null) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/workflows/${workflowId}/executions?shop_domain=${shopDomain}`);
  },
};

// Reports API calls
export const reportsAPI = {
  getReports: (shop = null, params = {}) => {
    const shopDomain = shop || getShopDomain();
    const queryParams = new URLSearchParams({ ...params });
    return apiCall(`/reports/${shopDomain}?${queryParams}`);
  },
  
  createReport: (shop, reportData) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/reports/${shopDomain}`, {
      method: 'POST',
      body: JSON.stringify(reportData),
    });
  },
  
  runReport: (reportId, shop = null, params = {}) => {
    const shopDomain = shop || getShopDomain();
    const queryParams = new URLSearchParams({ shop_domain: shopDomain, ...params });
    return apiCall(`/reports/${reportId}/run?${queryParams}`, {
      method: 'POST',
    });
  },
  
  exportReport: (reportId, format = 'csv', shop = null) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/reports/${reportId}/export?shop_domain=${shopDomain}&format=${format}`);
  },
};

// Billing API calls
export const billingAPI = {
  getPlans: () => apiCall('/billing/plans'),
  
  getCurrentPlan: (shop = null) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/billing/current-plan/${shopDomain}`);
  },
  
  createCharge: (shop, planId) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/billing/create-charge/${shopDomain}`, {
      method: 'POST',
      body: JSON.stringify({ plan_id: planId }),
    });
  },
  
  confirmCharge: (chargeId) => {
    return apiCall(`/billing/confirm-charge/${chargeId}`, {
      method: 'POST',
    });
  },
};

// Templates API calls
export const templatesAPI = {
  getTemplates: (industry = null) => {
    const params = industry ? `?industry=${industry}` : '';
    return apiCall(`/templates${params}`);
  },
  
  applyTemplate: (templateId, shop = null) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/templates/${templateId}/apply`, {
      method: 'POST',
      body: JSON.stringify({ shop: shopDomain }),
    });
  },
};

// Forecasting API calls
export const forecastingAPI = {
  getForecast: (shop = null, params = {}) => {
    const shopDomain = shop || getShopDomain();
    const queryParams = new URLSearchParams({ shop: shopDomain, ...params });
    return apiCall(`/forecasting/forecast?${queryParams}`);
  },
  
  getInsights: (shop = null) => {
    const shopDomain = shop || getShopDomain();
    return apiCall(`/forecasting/insights/${shopDomain}`);
  },
};

// Version management API
export const versionAPI = {
  getCurrentVersion: () => API_VERSION,
  
  getVersionInfo: async () => {
    const response = await fetch(`${API_BASE}/api/version`);
    if (!response.ok) {
      throw new Error('Failed to get version info');
    }
    return response.json();
  },
  
  switchVersion: (newVersion) => {
    // This would require reloading the app with new version
    const url = new URL(window.location);
    url.searchParams.set('api_version', newVersion);
    localStorage.setItem('preferred_api_version', newVersion);
    window.location.href = url.toString();
  },
  
  getCacheVersion: () => cacheVersion,
  getDeploymentId: () => deploymentId,
  
  // Force cache refresh
  refreshCache: async () => {
    await initializeAPIVersion();
    if ('caches' in window) {
      const names = await caches.keys();
      await Promise.all(names.map(name => caches.delete(name)));
    }
    window.location.reload();
  }
};

// Export all APIs
export default {
  auth: authAPI,
  dashboard: dashboardAPI,
  inventory: inventoryAPI,
  alerts: alertsAPI,
  customFields: customFieldsAPI,
  workflows: workflowsAPI,
  reports: reportsAPI,
  billing: billingAPI,
  templates: templatesAPI,
  forecasting: forecastingAPI,
  version: versionAPI,
};
