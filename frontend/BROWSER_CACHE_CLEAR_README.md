# Browser Cache Clearing CLI Tool

This Node.js CLI tool uses Puppeteer to open a headless browser and execute cache clearing functions directly in the browser environment.

## Installation

First, install the required dependencies:

```bash
npm install puppeteer chalk yargs
```

## Usage

### Basic Usage

Run the cache clearing tool with default settings:

```bash
node clear-browser-cache.js
```

Or use the npm script:

```bash
npm run clear-browser-cache
```

### Command Line Options

- `--url <url>` or `-u <url>`: Specify the URL of your app (default: http://localhost:3000)
- `--no-headless`: Run with a visible browser window instead of headless mode
- `--verbose` or `-v`: Show detailed logs including browser console output
- `--help` or `-h`: Show help information

### Examples

```bash
# Clear cache for app running on a different port
node clear-browser-cache.js --url http://localhost:5173

# Run with visible browser (useful for debugging)
node clear-browser-cache.js --no-headless

# Show detailed logs
node clear-browser-cache.js --verbose

# Combine options
node clear-browser-cache.js --url http://localhost:5173 --verbose --no-headless
```

## What Gets Cleared

The tool executes the following cache clearing operations:

1. **Browser Storage**
   - localStorage
   - sessionStorage
   - Cookies

2. **Cache API**
   - All caches registered in the Cache API

3. **Service Worker Caches**
   - Workbox caches
   - Custom service worker caches
   - API caches
   - Static caches

4. **API Response Caches**
   - Cached API responses in localStorage
   - Cached API responses in sessionStorage
   - API-specific caches in Cache API

5. **IndexedDB**
   - All IndexedDB databases

6. **Browser-Level Cache**
   - Browser cache via Chrome DevTools Protocol
   - Browser cookies via Chrome DevTools Protocol

## Feedback

The tool provides detailed feedback on what was cleared:

- ✓ Success messages for each cleared cache type
- ✗ Error messages if any clearing operation fails
- Summary of total cookies cleared
- Final status indicating if all operations were successful

## Troubleshooting

### Dependencies Not Installed

If you see an error about missing dependencies, run:

```bash
npm install puppeteer chalk yargs
```

### App Not Running

Make sure your frontend app is running before executing the cache clearing tool. The tool needs to navigate to your app to access the cache clearing utilities.

### Permission Issues

If you encounter permission issues on Linux/macOS, make the script executable:

```bash
chmod +x clear-browser-cache.js
```

### Headless Browser Issues

If the headless browser fails to launch, try:
- Running with `--no-headless` to see what's happening
- Checking if Chrome/Chromium is installed
- Installing missing system dependencies for Puppeteer

## Integration with Existing Cache Clearing Tools

This tool complements the existing cache clearing utilities:

- `npm run clear-cache`: Opens browser with cache clearing parameter
- `npm run clear-cache:api`: Clears cache via API endpoint
- `npm run clear-cache:all`: Combines browser and API clearing
- `npm run clear-browser-cache`: Uses Puppeteer to execute cache clearing functions

The Puppeteer-based tool is more comprehensive as it:
- Actually executes the JavaScript cache clearing functions
- Clears browser-level caches via Chrome DevTools Protocol
- Provides detailed feedback on each operation
- Can run in headless mode for automation

## Notes

- The tool requires the app to be running and accessible
- Browser caches may still require a hard refresh (Ctrl+Shift+R) after clearing
- Service workers will be unregistered and need to re-register on next visit
- All data in IndexedDB will be permanently deleted
