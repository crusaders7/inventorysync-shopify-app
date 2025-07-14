#!/usr/bin/env node

/**
 * Browser Cache Clearing CLI Tool
 * Uses Puppeteer to open a headless browser and execute cache clearing functions
 * 
 * Usage:
 *   node clear-browser-cache.js [options]
 * 
 * Options:
 *   --url <url>     URL of the app (default: http://localhost:3000)
 *   --headless      Run in headless mode (default)
 *   --no-headless   Run with visible browser
 *   --verbose       Show detailed logs
 *   --help          Show help
 */

const puppeteer = require('puppeteer');
const chalk = require('chalk');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

// Parse command line arguments
const argv = yargs(hideBin(process.argv))
  .option('url', {
    alias: 'u',
    type: 'string',
    description: 'URL of the app',
    default: process.env.FRONTEND_URL || 'http://localhost:3000'
  })
  .option('headless', {
    type: 'boolean',
    description: 'Run in headless mode',
    default: true
  })
  .option('verbose', {
    alias: 'v',
    type: 'boolean',
    description: 'Show detailed logs',
    default: false
  })
  .help()
  .alias('help', 'h')
  .argv;

// Logging helper
const log = {
  info: (msg) => console.log(chalk.blue('ℹ'), msg),
  success: (msg) => console.log(chalk.green('✓'), msg),
  error: (msg) => console.log(chalk.red('✗'), msg),
  warning: (msg) => console.log(chalk.yellow('⚠'), msg),
  verbose: (msg) => argv.verbose && console.log(chalk.gray('  →'), msg)
};

// Main function to clear browser cache
async function clearBrowserCache() {
  let browser;
  
  try {
    log.info('Starting browser cache clearing process...');
    
    // Launch browser
    log.verbose('Launching Puppeteer browser...');
    browser = await puppeteer.launch({
      headless: argv.headless,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu'
      ]
    });
    
    // Create a new page
    const page = await browser.newPage();
    
    // Enable console log capture
    if (argv.verbose) {
      page.on('console', msg => {
        const type = msg.type();
        const text = msg.text();
        if (type === 'error') {
          log.error(`Browser console: ${text}`);
        } else {
          log.verbose(`Browser console: ${text}`);
        }
      });
    }
    
    // Navigate to the app
    log.info(`Navigating to ${argv.url}...`);
    await page.goto(argv.url, {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    
    // Check if the clearCache utility is available
    log.verbose('Checking for clearCache utility...');
    const hasClearCache = await page.evaluate(() => {
      return typeof window.clearAllCachingMechanisms === 'function' ||
             (window.clearCache && typeof window.clearCache.clearAllCachingMechanisms === 'function');
    });
    
    if (!hasClearCache) {
      // Try to load the clearCache module
      log.warning('clearCache utility not found in global scope, attempting to import...');
      
      const clearCacheResult = await page.evaluate(async () => {
        try {
          // Try to dynamically import the clearCache module
          const module = await import('/src/utils/clearCache.js');
          window.clearCacheModule = module;
          return { success: true };
        } catch (error) {
          return { success: false, error: error.message };
        }
      });
      
      if (!clearCacheResult.success) {
        throw new Error(`Failed to load clearCache module: ${clearCacheResult.error}`);
      }
    }
    
    // Execute cache clearing functions
    log.info('Executing cache clearing functions...');
    
    const results = await page.evaluate(async () => {
      const results = {
        storage: { success: false, error: null },
        caches: { success: false, error: null },
        serviceWorker: { success: false, error: null },
        apiCache: { success: false, error: null },
        indexedDB: { success: false, error: null },
        overall: { success: false, error: null }
      };
      
      try {
        // Get the clearCache functions
        const clearCache = window.clearCacheModule || window.clearCache || window;
        
        // Clear localStorage and sessionStorage
        if (typeof clearCache.clearAllStorage === 'function') {
          try {
            clearCache.clearAllStorage();
            results.storage.success = true;
          } catch (e) {
            results.storage.error = e.message;
          }
        }
        
        // Clear all caches
        if (typeof clearCache.clearAllCaches === 'function') {
          try {
            await clearCache.clearAllCaches();
            results.caches.success = true;
          } catch (e) {
            results.caches.error = e.message;
          }
        }
        
        // Clear service worker caches
        if (typeof clearCache.clearServiceWorkerCaches === 'function') {
          try {
            await clearCache.clearServiceWorkerCaches();
            results.serviceWorker.success = true;
          } catch (e) {
            results.serviceWorker.error = e.message;
          }
        }
        
        // Clear API response caches
        if (typeof clearCache.clearAPIResponseCaches === 'function') {
          try {
            await clearCache.clearAPIResponseCaches();
            results.apiCache.success = true;
          } catch (e) {
            results.apiCache.error = e.message;
          }
        }
        
        // Clear IndexedDB
        if (typeof clearCache.clearIndexedDB === 'function') {
          try {
            await clearCache.clearIndexedDB();
            results.indexedDB.success = true;
          } catch (e) {
            results.indexedDB.error = e.message;
          }
        }
        
        // Clear all caching mechanisms
        if (typeof clearCache.clearAllCachingMechanisms === 'function') {
          try {
            const result = await clearCache.clearAllCachingMechanisms();
            results.overall = result;
          } catch (e) {
            results.overall.error = e.message;
          }
        }
        
      } catch (error) {
        results.overall.error = error.message;
      }
      
      return results;
    });
    
    // Display results
    console.log('\n' + chalk.bold('Cache Clearing Results:'));
    console.log(chalk.gray('─'.repeat(40)));
    
    // Storage
    if (results.storage.success) {
      log.success('Browser storage cleared (localStorage, sessionStorage, cookies)');
    } else if (results.storage.error) {
      log.error(`Browser storage clearing failed: ${results.storage.error}`);
    }
    
    // Caches
    if (results.caches.success) {
      log.success('Cache API cleared');
    } else if (results.caches.error) {
      log.error(`Cache API clearing failed: ${results.caches.error}`);
    }
    
    // Service Worker
    if (results.serviceWorker.success) {
      log.success('Service Worker caches cleared');
    } else if (results.serviceWorker.error) {
      log.error(`Service Worker cache clearing failed: ${results.serviceWorker.error}`);
    }
    
    // API Cache
    if (results.apiCache.success) {
      log.success('API response caches cleared');
    } else if (results.apiCache.error) {
      log.error(`API cache clearing failed: ${results.apiCache.error}`);
    }
    
    // IndexedDB
    if (results.indexedDB.success) {
      log.success('IndexedDB cleared');
    } else if (results.indexedDB.error) {
      log.error(`IndexedDB clearing failed: ${results.indexedDB.error}`);
    }
    
    console.log(chalk.gray('─'.repeat(40)));
    
    // Overall status
    if (results.overall.success) {
      log.success(chalk.bold('All caches cleared successfully!'));
    } else {
      log.warning('Some cache clearing operations may have failed');
    }
    
    // Additional browser cache clearing
    log.info('Clearing browser-level caches...');
    
    // Clear cookies for the domain
    const cookies = await page.cookies();
    await page.deleteCookie(...cookies);
    log.success(`Cleared ${cookies.length} cookies`);
    
    // Clear browser cache via CDP
    const client = await page.target().createCDPSession();
    await client.send('Network.clearBrowserCache');
    await client.send('Network.clearBrowserCookies');
    log.success('Browser-level cache cleared');
    
    log.info('\n' + chalk.bold.green('Cache clearing complete!'));
    log.info('Note: You may need to restart your app or hard refresh (Ctrl+Shift+R) to see changes.');
    
  } catch (error) {
    log.error(`Error: ${error.message}`);
    if (argv.verbose) {
      console.error(error.stack);
    }
    process.exit(1);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Check if puppeteer is installed
try {
  require.resolve('puppeteer');
} catch (e) {
  log.error('Puppeteer is not installed. Please run:');
  console.log(chalk.cyan('  npm install puppeteer chalk yargs'));
  process.exit(1);
}

// Check if other dependencies are installed
try {
  require.resolve('chalk');
  require.resolve('yargs');
} catch (e) {
  log.error('Required dependencies are missing. Please run:');
  console.log(chalk.cyan('  npm install puppeteer chalk yargs'));
  process.exit(1);
}

// Run the main function
clearBrowserCache().catch(error => {
  log.error('Unexpected error:', error.message);
  process.exit(1);
});
