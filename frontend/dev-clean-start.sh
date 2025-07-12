#!/bin/bash

echo "=== Clean Development Start ==="
echo "This script will clear all caches and restart the development server"
echo ""

# Run the Vite cache clear script
echo "1. Clearing Vite cache..."
./clear-vite-cache.sh

# Clear npm cache
echo ""
echo "2. Clearing npm cache..."
npm cache clean --force

# Remove and reinstall node_modules (optional but thorough)
read -p "Do you want to reinstall node_modules? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Removing node_modules..."
    rm -rf node_modules
    echo "Running npm install..."
    npm install
fi

# Kill any existing dev server processes
echo ""
echo "3. Killing any existing dev server processes..."
pkill -f "vite" || echo "No existing Vite processes found"

# Start the dev server
echo ""
echo "4. Starting development server with clean cache..."
echo "The server will start in a new process. You can access it at http://localhost:3000"
echo "Add ?clearCache=true to the URL to clear browser caches on first load"
echo ""
npm run dev
