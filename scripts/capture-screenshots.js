#!/usr/bin/env node

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// Ensure screenshot directory exists
const screenshotDir = path.join(__dirname, '../app-submission-assets/screenshots');
if (!fs.existsSync(screenshotDir)) {
  fs.mkdirSync(screenshotDir, { recursive: true });
}

// Screenshot configurations
const screenshots = [
  {
    name: '01-dashboard',
    url: 'http://localhost:5173/',
    title: 'Dashboard Overview',
    waitFor: 3000
  },
  {
    name: '02-field-builder',
    url: 'http://localhost:5173/custom-fields',
    title: 'Custom Fields Manager',
    waitFor: 3000
  },
  {
    name: '03-product-edit',
    url: 'http://localhost:5173/inventory',
    title: 'Product Edit with Custom Fields',
    waitFor: 3000
  },
  {
    name: '04-bulk-operations',
    url: 'http://localhost:5173/inventory',
    title: 'Bulk Operations',
    waitFor: 3000,
    actions: async (page) => {
      // Try to click on bulk operations button if it exists
      try {
        await page.click('[data-testid="bulk-operations"]');
      } catch (e) {
        console.log('Bulk operations button not found');
      }
    }
  },
  {
    name: '05-templates',
    url: 'http://localhost:5173/custom-fields',
    title: 'Industry Templates',
    waitFor: 3000,
    actions: async (page) => {
      // Try to open templates modal
      try {
        await page.click('[data-testid="templates-button"]');
      } catch (e) {
        console.log('Templates button not found');
      }
    }
  },
  {
    name: '06-search-filter',
    url: 'http://localhost:5173/inventory',
    title: 'Search & Filter',
    waitFor: 3000
  },
  {
    name: '07-analytics',
    url: 'http://localhost:5173/reports',
    title: 'Analytics & Reports',
    waitFor: 3000
  }
];

async function captureScreenshots() {
  console.log('🚀 Starting automated screenshot capture...\n');

  // Launch browser
  const browser = await puppeteer.launch({
    headless: false, // Set to true for headless mode
    defaultViewport: {
      width: 1280,
      height: 800
    },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    for (const screenshot of screenshots) {
      console.log(`📸 Capturing: ${screenshot.title}`);
      
      const page = await browser.newPage();
      
      // Set viewport to Shopify's required dimensions
      await page.setViewport({ width: 1280, height: 800 });
      
      // Navigate to the page
      await page.goto(screenshot.url, { waitUntil: 'networkidle2' });
      
      // Wait for content to load
      await page.waitForTimeout(screenshot.waitFor);
      
      // Execute any custom actions
      if (screenshot.actions) {
        await screenshot.actions(page);
        await page.waitForTimeout(2000); // Wait for action results
      }
      
      // Add some demo data styling (optional)
      await page.evaluate(() => {
        // Add a subtle watermark or demo indicator if needed
        const style = document.createElement('style');
        style.textContent = `
          /* Ensure polaris components look good */
          .Polaris-Frame { background: #f4f6f8 !important; }
        `;
        document.head.appendChild(style);
      });
      
      // Take screenshot
      const screenshotPath = path.join(screenshotDir, `${screenshot.name}.png`);
      await page.screenshot({ 
        path: screenshotPath,
        fullPage: false // Ensure we capture only viewport
      });
      
      console.log(`✅ Saved: ${screenshotPath}`);
      
      await page.close();
    }

    console.log('\n✨ All screenshots captured successfully!');
    console.log(`📁 Screenshots saved to: ${screenshotDir}`);

  } catch (error) {
    console.error('❌ Error capturing screenshots:', error);
  } finally {
    await browser.close();
  }
}

// Add some demo content generators
async function generateDemoData() {
  console.log('\n🎨 Generating demo data for better screenshots...\n');
  
  // This would normally interact with your API to create demo data
  // For now, we'll just log what would be created
  
  const demoData = {
    products: [
      { name: "Premium Cotton T-Shirt", customFields: { material: "100% Organic Cotton", care: "Machine wash cold" } },
      { name: "Wireless Bluetooth Headphones", customFields: { battery: "40 hours", warranty: "2 years" } },
      { name: "Artisan Coffee Blend", customFields: { origin: "Colombia", roast: "Medium", notes: "Chocolate, Caramel" } }
    ],
    customFields: [
      { name: "material", type: "text", category: "Fashion" },
      { name: "battery_life", type: "number", category: "Electronics" },
      { name: "ingredients", type: "multiline", category: "Food & Beverage" }
    ]
  };
  
  console.log('Demo data that would be created:', JSON.stringify(demoData, null, 2));
  console.log('\n💡 Tip: Make sure your app has some sample data for better screenshots!\n');
}

// Main execution
async function main() {
  // Check if servers are running
  try {
    const http = require('http');
    
    // Check backend
    await new Promise((resolve, reject) => {
      http.get('http://localhost:8000', (res) => {
        if (res.statusCode === 200 || res.statusCode === 307) {
          console.log('✅ Backend server is running');
          resolve();
        } else {
          reject(new Error('Backend not responding correctly'));
        }
      }).on('error', reject);
    }).catch(() => {
      console.log('⚠️  Backend server not running. Please start it first!');
      console.log('   Run: cd backend && python -m uvicorn app.main:app --reload --port 8000');
      process.exit(1);
    });
    
    // Check frontend
    await new Promise((resolve, reject) => {
      http.get('http://localhost:5173', (res) => {
        if (res.statusCode === 200 || res.statusCode === 404) {
          console.log('✅ Frontend server is running');
          resolve();
        } else {
          reject(new Error('Frontend not responding correctly'));
        }
      }).on('error', reject);
    }).catch(() => {
      console.log('⚠️  Frontend server not running. Please start it first!');
      console.log('   Run: cd frontend && npm run dev');
      process.exit(1);
    });
    
  } catch (error) {
    console.error('Error checking servers:', error);
    process.exit(1);
  }
  
  // Generate demo data info
  await generateDemoData();
  
  // Capture screenshots
  await captureScreenshots();
}

// Run the script
main().catch(console.error);
