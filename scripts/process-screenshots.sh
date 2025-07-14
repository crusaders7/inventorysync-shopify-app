#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Screenshot Processing Script ===${NC}"
echo ""

# Target directory
TARGET_DIR="/home/brend/inventorysync-shopify-app/app-submission-assets/screenshots"

# Create directory if it doesn't exist
mkdir -p "$TARGET_DIR"

echo -e "${YELLOW}This script will help you organize your screenshots for Shopify App Store submission.${NC}"
echo ""
echo "Please copy your screenshots to the target directory first."
echo -e "Target directory: ${GREEN}$TARGET_DIR${NC}"
echo ""
echo "Screenshot requirements:"
echo "- Format: PNG"
echo "- Dimensions: 1280x800px (exactly)"
echo "- Number: 3-7 screenshots"
echo ""
echo -e "${YELLOW}Suggested naming:${NC}"
echo "- 01-dashboard.png"
echo "- 02-custom-fields.png"
echo "- 03-product-edit.png"
echo "- 04-bulk-operations.png"
echo "- 05-templates.png"
echo "- 06-reports.png"
echo "- 07-settings.png"
echo ""
echo -e "${BLUE}If you have screenshots in Windows (D:\\wsl$\\Ubuntu\\...), copy them using:${NC}"
echo "cp /mnt/d/path/to/your/screenshot.png $TARGET_DIR/"
echo ""
read -p "Press ENTER when you've copied all screenshots to continue..."

# Check if files exist
echo -e "\n${YELLOW}Checking for screenshots...${NC}"
FILES_FOUND=false
for file in "$TARGET_DIR"/*.png; do
    if [ -f "$file" ]; then
        FILES_FOUND=true
        break
    fi
done

if [ "$FILES_FOUND" = false ]; then
    echo -e "${RED}No PNG files found in $TARGET_DIR${NC}"
    echo "Please copy your screenshots first and run this script again."
    exit 1
fi

# List found files
echo -e "\n${GREEN}Found screenshots:${NC}"
ls -la "$TARGET_DIR"/*.png

# Process screenshots
echo -e "\n${YELLOW}Processing screenshots to ensure correct dimensions (1280x800)...${NC}"

# Install ImageMagick if needed
if ! command -v convert &> /dev/null; then
    echo "Installing ImageMagick..."
    sudo apt-get update -qq && sudo apt-get install -y imagemagick
fi

# Process each PNG file
for file in "$TARGET_DIR"/*.png; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        
        # Get image dimensions
        dimensions=$(identify -format "%wx%h" "$file" 2>/dev/null)
        
        if [ "$dimensions" = "1280x800" ]; then
            echo "✓ $filename is already 1280x800"
        else
            echo "⚡ Resizing $filename from $dimensions to 1280x800..."
            # Create backup
            cp "$file" "$file.backup"
            
            # Resize to exactly 1280x800, cropping if necessary
            convert "$file" -resize 1280x800^ -gravity center -extent 1280x800 -quality 95 "$file"
            
            echo "✓ Resized $filename"
        fi
    fi
done

# Create optimized versions
echo -e "\n${YELLOW}Creating optimized versions...${NC}"
mkdir -p "$TARGET_DIR/optimized"

for file in "$TARGET_DIR"/*.png; do
    if [ -f "$file" ] && [[ ! "$file" =~ \.backup$ ]]; then
        filename=$(basename "$file")
        
        # Optimize PNG
        convert "$file" -strip -quality 95 "$TARGET_DIR/optimized/$filename"
        
        # Get file sizes
        original_size=$(du -h "$file" | cut -f1)
        optimized_size=$(du -h "$TARGET_DIR/optimized/$filename" | cut -f1)
        
        echo "✓ Optimized $filename: $original_size → $optimized_size"
    fi
done

# Generate index file
echo -e "\n${YELLOW}Generating screenshot index...${NC}"

cat > "$TARGET_DIR/screenshot-index.md" << EOF
# InventorySync App Screenshots

## Screenshot List

EOF

for file in "$TARGET_DIR"/*.png; do
    if [ -f "$file" ] && [[ ! "$file" =~ \.backup$ ]]; then
        filename=$(basename "$file")
        dimensions=$(identify -format "%wx%h" "$file" 2>/dev/null)
        size=$(du -h "$file" | cut -f1)
        
        echo "- **$filename** - $dimensions - $size" >> "$TARGET_DIR/screenshot-index.md"
    fi
done

echo -e "\n${GREEN}=== Screenshot Processing Complete ===${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "- Screenshots location: $TARGET_DIR"
echo "- Optimized versions: $TARGET_DIR/optimized/"
echo "- Index file: $TARGET_DIR/screenshot-index.md"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review the processed screenshots"
echo "2. Choose the best 3-7 screenshots for submission"
echo "3. Upload them to Shopify Partners dashboard"
echo ""
echo -e "${GREEN}✨ Your screenshots are ready for submission!${NC}"
