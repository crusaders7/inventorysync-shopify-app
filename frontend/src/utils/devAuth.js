/**
 * Development authentication helper
 * This file provides mock authentication for development purposes
 */

const DEV_SHOP_DOMAIN = 'inventorysync-dev.myshopify.com';
const DEV_ACCESS_TOKEN = 'dev-access-token-' + Date.now();

export function setupDevAuth() {
  // Set development shop domain in localStorage
  if (!localStorage.getItem('shopDomain')) {
    localStorage.setItem('shopDomain', DEV_SHOP_DOMAIN);
    console.log('✅ Development shop domain set:', DEV_SHOP_DOMAIN);
  }

  // Set development access token
  if (!localStorage.getItem('accessToken')) {
    localStorage.setItem('accessToken', DEV_ACCESS_TOKEN);
    console.log('✅ Development access token set');
  }

  // Set development user info
  if (!localStorage.getItem('userInfo')) {
    const devUser = {
      id: 'dev-user-1',
      email: 'dev@inventorysync.com',
      shop: DEV_SHOP_DOMAIN,
      name: 'Development User'
    };
    localStorage.setItem('userInfo', JSON.stringify(devUser));
    console.log('✅ Development user info set');
  }

  return {
    shop: DEV_SHOP_DOMAIN,
    token: DEV_ACCESS_TOKEN
  };
}

export function getDevShop() {
  return DEV_SHOP_DOMAIN;
}

export function clearDevAuth() {
  localStorage.removeItem('shopDomain');
  localStorage.removeItem('accessToken');
  localStorage.removeItem('userInfo');
  console.log('✅ Development auth cleared');
}
