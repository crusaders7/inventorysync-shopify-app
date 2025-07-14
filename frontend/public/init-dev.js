// Development Environment Initialization
// This script sets up the development environment automatically

(function() {
  console.log('🚀 Initializing InventorySync Development Environment...');
  
  // Set development shop domain
  const DEV_SHOP = 'inventorysync-dev.myshopify.com';
  
  // Set up localStorage with development credentials
  if (!localStorage.getItem('shopDomain')) {
    localStorage.setItem('shopDomain', DEV_SHOP);
    localStorage.setItem('shopify_shop_domain', DEV_SHOP);
    localStorage.setItem('shopify_authenticated', 'true');
    localStorage.setItem('accessToken', 'dev-token-' + Date.now());
    
    const devUser = {
      id: 'dev-user-1',
      email: 'dev@inventorysync.com',
      shop: DEV_SHOP,
      name: 'Development User'
    };
    localStorage.setItem('userInfo', JSON.stringify(devUser));
    
    console.log('✅ Development credentials set:');
    console.log('   Shop:', DEV_SHOP);
    console.log('   User:', devUser.email);
    console.log('   Auth:', 'Enabled');
  } else {
    console.log('✅ Development credentials already set');
    console.log('   Shop:', localStorage.getItem('shopDomain'));
  }
  
  // Add development banner
  window.addEventListener('DOMContentLoaded', function() {
    const banner = document.createElement('div');
    banner.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; background: #ff6b6b; color: white; padding: 8px; text-align: center; z-index: 9999; font-family: -apple-system, BlinkMacSystemFont, San Francisco, Segoe UI, Roboto, Helvetica Neue, sans-serif;';
    banner.innerHTML = '🔧 Development Mode - Shop: ' + DEV_SHOP + ' | <a href="#" onclick="localStorage.clear(); location.reload();" style="color: white; text-decoration: underline;">Clear Auth</a>';
    document.body.insertBefore(banner, document.body.firstChild);
  });
  
  console.log('✅ Development environment ready!');
  console.log('📝 To clear auth, run: localStorage.clear()');
})();
