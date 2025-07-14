#!/usr/bin/env node

/**
 * Command-line cache clearing utility
 * 
 * Usage:
 *   node clear-cache-cli.js [options]
 * 
 * Options:
 *   --browser    Open browser with cache clearing parameter
 *   --api        Clear API-specific caches via HTTP request
 *   --help       Show help
 */

const http = require('http');
const https = require('https');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Parse command line arguments
const args = process.argv.slice(2);
const options = {
  browser: args.includes('--browser'),
  api: args.includes('--api'),
  help: args.includes('--help') || args.includes('-h'),
};

// Show help
if (options.help || args.length === 0) {
  console.log(`
Cache Clearing Utility for InventorySync Shopify App

Usage:
  node clear-cache-cli.js [options]

Options:
  --browser    Open browser with cache clearing parameter
  --api        Clear API caches via HTTP request to the app
  --help       Show this help message

Examples:
  node clear-cache-cli.js --browser
  node clear-cache-cli.js --api
  node clear-cache-cli.js --browser --api

Note: For browser-based clearing, ensure the app is running locally.
`);
  process.exit(0);
}

// Function to clear cache via browser
async function clearCacheViaBrowser() {
  console.log('Opening browser with cache clearing parameter...');
  
  // Try to find the app URL from environment or use default
  const appUrl = process.env.FRONTEND_URL || 'http://localhost:3000';
  const cacheUrl = `${appUrl}?clearCache=true`;
  
  console.log(`Opening: ${cacheUrl}`);
  
  // Determine the platform and open browser
  const platform = process.platform;
  let command;
  
  if (platform === 'darwin') {
    command = 'open';
  } else if (platform === 'win32') {
    command = 'start';
  } else {
    command = 'xdg-open';
  }
  
  try {
    spawn(command, [cacheUrl], { detached: true, stdio: 'ignore' }).unref();
    console.log('✓ Browser opened with cache clearing URL');
  } catch (error) {
    console.error('Failed to open browser:', error);
    console.log(`Please manually open: ${cacheUrl}`);
  }
}

// Function to clear cache via API endpoint
async function clearCacheViaAPI() {
  console.log('Clearing cache via API endpoint...');
  
  const apiUrl = process.env.API_URL || 'http://localhost:5001';
  const endpoint = `${apiUrl}/api/cache/clear`;
  
  const protocol = apiUrl.startsWith('https') ? https : http;
  
  return new Promise((resolve, reject) => {
    const req = protocol.request(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    }, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          console.log('✓ API cache cleared successfully');
          resolve();
        } else {
          console.error(`API returned status ${res.statusCode}: ${data}`);
          reject(new Error(`API error: ${res.statusCode}`));
        }
      });
    });
    
    req.on('error', (error) => {
      console.error('Failed to connect to API:', error.message);
      console.log('Make sure the backend server is running');
      reject(error);
    });
    
    req.end();
  });
}

// Function to clear local Node.js caches
function clearNodeCaches() {
  console.log('Clearing Node.js module caches...');
  
  try {
    // Clear require cache
    Object.keys(require.cache).forEach((key) => {
      if (key.includes('inventorysync-shopify-app')) {
        delete require.cache[key];
      }
    });
    
    console.log('✓ Node.js module cache cleared');
  } catch (error) {
    console.error('Failed to clear Node.js cache:', error);
  }
}

// Main execution
async function main() {
  console.log('=== InventorySync Cache Clearing Utility ===\n');
  
  try {
    // Always clear Node.js caches
    clearNodeCaches();
    
    // Clear via browser if requested
    if (options.browser) {
      await clearCacheViaBrowser();
    }
    
    // Clear via API if requested
    if (options.api) {
      await clearCacheViaAPI();
    }
    
    console.log('\n=== Cache clearing complete ===');
    console.log('Note: Browser caches may require a hard refresh (Ctrl+Shift+R)');
  } catch (error) {
    console.error('\nError during cache clearing:', error);
    process.exit(1);
  }
}

// Run the main function
main();
