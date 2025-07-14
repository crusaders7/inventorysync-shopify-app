#!/bin/bash

echo "Starting Frontend Server..."
echo "=========================="

# Navigate to frontend directory
cd /home/brend/inventorysync-shopify-app/frontend

# Run the development server
echo "Starting server on http://localhost:3001"
npm run dev
