import React, { useState, useEffect } from 'react';
import { AppProvider, Badge, Button, Card, DataTable, Frame, Layout, Page, Text, Toast } from '@shopify/polaris';
import enTranslations from '@shopify/polaris/locales/en.json';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { Provider as AppBridgeProvider } from '@shopify/app-bridge-react';
import { DataProvider } from './context/DataContext';
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';
import Inventory from './components/Inventory';
import Settings from './components/Settings';
import ShopifyInstall from './components/ShopifyInstall';
import AuthCallback from './components/AuthCallback';
import BillingSetup from './components/BillingSetup';
import CustomFieldsManager from './components/CustomFieldsManager';
import { setupDevAuth } from './utils/devAuth';

function App() {
  const [activeToast, setActiveToast] = useState(false);
  const [toastContent, setToastContent] = useState('');
  const [shopDomain, setShopDomain] = useState('');

  // Get shop domain and setup App Bridge
  useEffect(() => {
    // Setup development authentication if in development mode
    if (import.meta.env.DEV) {
      const devAuth = setupDevAuth();
      setShopDomain(devAuth.shop);
      localStorage.setItem('shopify_authenticated', 'true');
    }
    
    const params = new URLSearchParams(window.location.search);
    const shop = params.get('shop') || localStorage.getItem('shopify_shop_domain') || localStorage.getItem('shopDomain');
    
    if (shop) {
      setShopDomain(shop);
      localStorage.setItem('shopify_shop_domain', shop);
    }

    console.log('App loaded with params:', Object.fromEntries(params));
    
    if (params.get('authenticated') === 'true') {
      showToast('Successfully authenticated with Shopify!');
    }
    
    if (params.get('billing') === 'success') {
      showToast('Subscription activated successfully!');
    } else if (params.get('billing') === 'declined') {
      showToast('Subscription was declined. Please try again.', true);
    }

    // Handle billing setup redirect
    if (params.get('setup') === 'billing') {
      // Show billing setup flow
    }
  }, []);

  const showToast = (content, isError = false) => {
    setToastContent(content);
    setActiveToast(true);
  };

  const toastMarkup = activeToast ? (
    <Toast content={toastContent} onDismiss={() => setActiveToast(false)} />
  ) : null;

  // Check if user is authenticated
  const isAuthenticated = localStorage.getItem('shopify_authenticated') === 'true';

  // App Bridge configuration
  const appBridgeConfig = {
    apiKey: import.meta.env.VITE_SHOPIFY_API_KEY || 'your-api-key',
    host: shopDomain ? btoa(shopDomain + '/admin') : '',
    forceRedirect: true
  };

  // If running inside Shopify admin (embedded)
  const isEmbedded = window.top !== window.self;

  if (isEmbedded && shopDomain) {
    return (
      <AppBridgeProvider config={appBridgeConfig}>
        <AppProvider i18n={enTranslations}>
          <DataProvider>
            <Frame>
              <Routes>
                {/* Embedded routes - no navigation needed */}
                <Route path="/" element={<Dashboard showToast={showToast} />} />
                <Route path="/custom-fields" element={<CustomFieldsManager shop={shopDomain} showToast={showToast} />} />
                <Route path="/inventory" element={<Inventory showToast={showToast} />} />
                <Route path="/settings" element={<Settings showToast={showToast} />} />
              </Routes>
              {toastMarkup}
            </Frame>
          </DataProvider>
        </AppProvider>
      </AppBridgeProvider>
    );
  }

  // Standalone mode (outside Shopify admin)
  return (
    <AppProvider i18n={enTranslations}>
      <DataProvider>
        <Router>
          <Frame>
            {isAuthenticated && <Navigation />}
            <Routes>
              {/* Public routes */}
              <Route path="/install" element={<ShopifyInstall />} />
              <Route path="/auth/callback" element={<AuthCallback />} />
              <Route path="/billing/setup" element={<BillingSetup shop={shopDomain} />} />
              
              {/* Protected routes */}
              <Route path="/" element={isAuthenticated ? <Dashboard showToast={showToast} /> : <Navigate to="/install" />} />
              <Route path="/custom-fields" element={isAuthenticated ? <CustomFieldsManager shop={shopDomain} showToast={showToast} /> : <Navigate to="/install" />} />
              <Route path="/inventory" element={isAuthenticated ? <Inventory showToast={showToast} /> : <Navigate to="/install" />} />
              <Route path="/settings" element={isAuthenticated ? <Settings showToast={showToast} /> : <Navigate to="/install" />} />
            </Routes>
            {toastMarkup}
          </Frame>
        </Router>
      </DataProvider>
    </AppProvider>
  );
}

export default App;