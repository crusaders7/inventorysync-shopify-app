#!/bin/bash

# InventorySync Cleanup Script
# This script removes unused development files to optimize the codebase

echo "🧹 Starting InventorySync cleanup..."

# Create backup directory
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backend cleanup
echo "📦 Cleaning backend files..."

# Move test files to backup
find backend -name "test_*.py" -o -name "*_test.py" -o -name "oauth_test.py" | while read file; do
    mkdir -p "$BACKUP_DIR/$(dirname "$file")"
    mv "$file" "$BACKUP_DIR/$file" 2>/dev/null && echo "  Moved: $file"
done

# Move fix scripts to backup
find backend -name "fix_*.py" | while read file; do
    mkdir -p "$BACKUP_DIR/$(dirname "$file")"
    mv "$file" "$BACKUP_DIR/$file" 2>/dev/null && echo "  Moved: $file"
done

# Move simple versions to backup
find backend -name "*_simple.py" -o -name "simple_*.py" | while read file; do
    mkdir -p "$BACKUP_DIR/$(dirname "$file")"
    mv "$file" "$BACKUP_DIR/$file" 2>/dev/null && echo "  Moved: $file"
done

# Move setup scripts to backup
for file in backend/database_setup.py backend/init_db.py backend/setup_store.py backend/create_test_products.py; do
    if [ -f "$file" ]; then
        mkdir -p "$BACKUP_DIR/$(dirname "$file")"
        mv "$file" "$BACKUP_DIR/$file" && echo "  Moved: $file"
    fi
done

# Move sync scripts to backup
find backend -name "sync_*.py" -o -name "update_*.py" | while read file; do
    mkdir -p "$BACKUP_DIR/$(dirname "$file")"
    mv "$file" "$BACKUP_DIR/$file" 2>/dev/null && echo "  Moved: $file"
done

# Frontend cleanup
echo "🎨 Cleaning frontend files..."

# Remove fix scripts from frontend
find frontend -name "fix-*.py" | while read file; do
    mkdir -p "$BACKUP_DIR/$(dirname "$file")"
    mv "$file" "$BACKUP_DIR/$file" 2>/dev/null && echo "  Moved: $file"
done

# Root directory cleanup
echo "📁 Cleaning root directory..."

# Move fix scripts from root
find . -maxdepth 1 -name "fix*.py" -o -name "cleanup_project.py" | while read file; do
    mv "$file" "$BACKUP_DIR/" 2>/dev/null && echo "  Moved: $file"
done

# Clean Python cache
echo "🗑️  Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Clean node_modules cache
echo "🗑️  Cleaning Vite cache..."
rm -rf frontend/node_modules/.vite 2>/dev/null

# Create scripts/dev directory for development scripts
echo "📂 Organizing development scripts..."
mkdir -p backend/scripts/dev

# Move development scripts
for file in backend/configure_shopify_webhooks.py backend/create_webhook_handlers.py backend/database_manager.py backend/industry_templates.py backend/multi_location_sync.py; do
    if [ -f "$file" ]; then
        mv "$file" backend/scripts/dev/ 2>/dev/null && echo "  Moved to scripts/dev: $(basename "$file")"
    fi
done

echo "✅ Cleanup complete!"
echo "📦 Backup created in: $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "1. Review the backup directory to ensure no important files were moved"
echo "2. Run 'rm -rf $BACKUP_DIR' to permanently delete the backup"
echo "3. Commit the cleaned up codebase"
