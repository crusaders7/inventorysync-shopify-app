#!/bin/bash

echo "Clearing Vite cache..."

# Clear Vite cache directory
if [ -d "node_modules/.vite" ]; then
    echo "Removing node_modules/.vite directory..."
    rm -rf node_modules/.vite
    echo "✓ Vite cache cleared"
else
    echo "No Vite cache directory found"
fi

# Clear dist directory (built files)
if [ -d "dist" ]; then
    echo "Removing dist directory..."
    rm -rf dist
    echo "✓ Dist directory cleared"
fi

# Clear any temp directories
if [ -d ".temp" ]; then
    echo "Removing .temp directory..."
    rm -rf .temp
    echo "✓ Temp directory cleared"
fi

echo "Cache clearing complete!"
echo "Run 'npm run dev' to restart the development server with a clean cache."
