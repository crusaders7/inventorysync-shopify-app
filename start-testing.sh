#!/bin/bash

echo "🚀 InventorySync Testing Setup"
echo "=============================="
echo ""

# Check if backend environment is ready
if [ ! -f "backend/.env" ]; then
    echo "❌ Backend .env file missing!"
    echo "Please configure backend/.env with your credentials"
    exit 1
fi

# Check if frontend environment is ready
if [ ! -f "frontend/.env" ]; then
    echo "❌ Frontend .env file missing!"
    echo "Creating frontend/.env..."
    echo "VITE_API_URL=http://localhost:8000" > frontend/.env
fi

echo "📋 Testing Checklist:"
echo ""
echo "1. Start Backend Server:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "2. Start Frontend Server (new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Start Shopify Dev Server (new terminal):"
echo "   npx shopify app dev"
echo ""
echo "4. Open Testing Guide:"
echo "   cat docs/TESTING_GUIDE.md"
echo ""
echo "5. Access Services:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Production: https://inventorysync.prestigecorp.au"
echo ""
echo "Ready to start? Follow the steps above!"
