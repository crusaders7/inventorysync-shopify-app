#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    InventorySync App Store Submission Preparation      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Change to script directory
cd "$(dirname "$0")"
cd ..

# Step 1: Install dependencies
echo -e "${YELLOW}📦 Step 1: Installing dependencies...${NC}"

# Check and install ImageMagick
if ! command -v convert &> /dev/null; then
    echo "Installing ImageMagick..."
    sudo apt-get update -qq && sudo apt-get install -y imagemagick
else
    echo "✓ ImageMagick already installed"
fi

# Check and install Node dependencies
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
else
    echo "✓ Frontend dependencies already installed"
fi
cd ..

# Step 2: Create asset directories
echo -e "\n${YELLOW}📁 Step 2: Creating asset directories...${NC}"
mkdir -p app-submission-assets/{screenshots,icons,banners}
echo "✓ Asset directories created"

# Step 3: Convert SVG icons to PNG
echo -e "\n${YELLOW}🎨 Step 3: Converting icons to PNG format...${NC}"

# Convert app icon to multiple sizes
convert -background none -resize 1024x1024 \
    frontend/public/app-icon.svg \
    app-submission-assets/icons/app-icon-1024.png
echo "✓ Created app-icon-1024.png (for App Store)"

convert -background none -resize 512x512 \
    frontend/public/app-icon.svg \
    app-submission-assets/icons/app-icon-512.png
echo "✓ Created app-icon-512.png"

convert -background none -resize 256x256 \
    frontend/public/app-icon.svg \
    app-submission-assets/icons/app-icon-256.png
echo "✓ Created app-icon-256.png"

convert -background none -resize 128x128 \
    frontend/public/app-icon.svg \
    app-submission-assets/icons/app-icon-128.png
echo "✓ Created app-icon-128.png"

# Convert favicon
convert -background none -resize 32x32 \
    frontend/public/favicon.svg \
    app-submission-assets/icons/favicon.ico
echo "✓ Created favicon.ico"

# Step 4: Generate app banner
echo -e "\n${YELLOW}🖼️  Step 4: Generating app banner...${NC}"

# Check if Chrome is installed for banner generation
if command -v google-chrome &> /dev/null; then
    google-chrome --headless --disable-gpu --window-size=1920,1080 \
        --screenshot=app-submission-assets/banners/app-banner.png \
        file://${PWD}/app-submission-assets/app-banner-preview.html 2>/dev/null
    echo "✓ App banner generated (1920x1080)"
else
    echo -e "${YELLOW}⚠ Chrome not found. Skipping automatic banner generation.${NC}"
    echo "  You can manually open app-submission-assets/app-banner-preview.html and take a screenshot"
fi

# Step 5: Start servers for screenshots
echo -e "\n${YELLOW}🚀 Step 5: Starting development servers...${NC}"

# Kill any existing servers
pkill -f "uvicorn" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 2

# Start backend
echo "Starting backend server..."
cd backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi
python -m uvicorn app.main:app --reload --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Start frontend
echo "Starting frontend server..."
cd frontend
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for servers to start
echo "Waiting for servers to start..."
sleep 8

# Check if servers are running
BACKEND_RUNNING=false
FRONTEND_RUNNING=false

if curl -s http://localhost:8000 > /dev/null 2>&1; then
    BACKEND_RUNNING=true
    echo "✓ Backend server is running"
else
    echo -e "${RED}✗ Backend server failed to start. Check /tmp/backend.log${NC}"
fi

if curl -s http://localhost:5173 > /dev/null 2>&1; then
    FRONTEND_RUNNING=true
    echo "✓ Frontend server is running"
else
    echo -e "${RED}✗ Frontend server failed to start. Check /tmp/frontend.log${NC}"
fi

# Step 6: Screenshot instructions
if [ "$BACKEND_RUNNING" = true ] && [ "$FRONTEND_RUNNING" = true ]; then
    echo -e "\n${GREEN}════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Servers are running! Time to take screenshots${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}The app is now running at: ${GREEN}http://localhost:5173${NC}"
    echo ""
    echo -e "${YELLOW}📸 SCREENSHOT INSTRUCTIONS:${NC}"
    echo ""
    echo "Please take screenshots of these pages:"
    echo "1. Dashboard - ${BLUE}http://localhost:5173/${NC}"
    echo "2. Custom Fields Manager - ${BLUE}http://localhost:5173/custom-fields${NC}"
    echo "3. Product Edit (showing custom fields)"
    echo "4. Bulk Operations"
    echo "5. Industry Templates"
    echo "6. Search & Filter"
    echo "7. Analytics/Reports"
    echo ""
    echo -e "${YELLOW}IMPORTANT: Save all screenshots to:${NC}"
    echo -e "${GREEN}$(pwd)/app-submission-assets/screenshots/${NC}"
    echo ""
    echo "Name them EXACTLY as:"
    echo "• 01-dashboard.png"
    echo "• 02-field-builder.png"
    echo "• 03-product-edit.png"
    echo "• 04-bulk-operations.png"
    echo "• 05-templates.png"
    echo "• 06-search-filter.png"
    echo "• 07-analytics.png"
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Option 1: Manual Screenshots${NC}"
    echo "Take screenshots manually using your browser's screenshot tool"
    echo ""
    echo -e "${YELLOW}Option 2: Automated Screenshots${NC}"
    echo "Run: ${GREEN}node scripts/capture-screenshots.js${NC}"
    echo "(This will use Puppeteer to automatically capture all screenshots)"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo ""
    read -p "Press ENTER when you've saved all screenshots to continue..."
else
    echo -e "\n${RED}⚠ Servers are not running properly. Cannot proceed with screenshots.${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 1
fi

# Step 7: Process screenshots
echo -e "\n${YELLOW}🖼️  Step 7: Processing screenshots...${NC}"

SCREENSHOT_DIR="app-submission-assets/screenshots"
SCREENSHOTS_FOUND=false

for i in {1..7}; do
    FILENAME="0${i}-*.png"
    if ls $SCREENSHOT_DIR/$FILENAME 1> /dev/null 2>&1; then
        SCREENSHOTS_FOUND=true
        break
    fi
done

if [ "$SCREENSHOTS_FOUND" = true ]; then
    echo "Processing screenshots to ensure correct dimensions..."
    
    # Process each screenshot to ensure it's exactly 1280x800
    for file in $SCREENSHOT_DIR/*.png; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            # Create a properly sized version
            convert "$file" -resize 1280x800^ -gravity center -extent 1280x800 "$SCREENSHOT_DIR/final-$filename"
            echo "✓ Processed: $filename"
        fi
    done
    
    echo -e "${GREEN}✓ Screenshots processed successfully${NC}"
else
    echo -e "${YELLOW}⚠ No screenshots found in $SCREENSHOT_DIR${NC}"
fi

# Step 8: Clean up
echo -e "\n${YELLOW}🧹 Step 8: Cleaning up...${NC}"

# Kill the development servers
kill $BACKEND_PID 2>/dev/null
kill $FRONTEND_PID 2>/dev/null
echo "✓ Development servers stopped"

# Step 9: Generate final report
echo -e "\n${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✨ APP SUBMISSION ASSETS READY!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📁 Asset Locations:${NC}"
echo "• Icons: $(pwd)/app-submission-assets/icons/"
echo "• Banner: $(pwd)/app-submission-assets/banners/"
echo "• Screenshots: $(pwd)/app-submission-assets/screenshots/"
echo "• App Listing Content: $(pwd)/app-submission-assets/app-listing-content.json"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Review the app listing content in app-listing-content.json"
echo "2. Upload the 1024x1024 icon to Shopify Partners"
echo "3. Upload the app banner (1920x1080)"
echo "4. Upload all 7 screenshots (use the 'final-' versions)"
echo "5. Copy the app description and benefits from the JSON file"
echo ""
echo -e "${YELLOW}💡 Tip: Double-check all images meet Shopify's requirements:${NC}"
echo "• App icon: 1024x1024px PNG"
echo "• App banner: 1920x1080px PNG"
echo "• Screenshots: 1280x800px PNG (exactly)"
echo ""
echo -e "${GREEN}Good luck with your submission! 🚀${NC}"
