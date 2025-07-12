#!/bin/bash
#
# InventorySync Database Backup Script
# Automated PostgreSQL backup with rotation
#

set -e

# Configuration
DB_NAME="inventorysync"
DB_USER="inventorysync_user"
DB_HOST="postgres"
BACKUP_DIR="/backups"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/inventorysync_backup_$TIMESTAMP.sql"

echo "Starting database backup..."
echo "Backup file: $BACKUP_FILE"

# Create backup
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    --no-password \
    --verbose \
    --format=plain \
    --no-owner \
    --no-privileges \
    > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"
BACKUP_FILE_GZ="${BACKUP_FILE}.gz"

echo "Backup created: $BACKUP_FILE_GZ"

# Calculate backup size
BACKUP_SIZE=$(du -h "$BACKUP_FILE_GZ" | cut -f1)
echo "Backup size: $BACKUP_SIZE"

# Clean up old backups (keep only last 30 days)
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "inventorysync_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# List current backups
echo "Current backups:"
ls -lh "$BACKUP_DIR"/inventorysync_backup_*.sql.gz 2>/dev/null || echo "No backups found"

echo "Backup completed successfully!"

# Optional: Send backup notification
if [ -n "$BACKUP_WEBHOOK_URL" ]; then
    curl -X POST "$BACKUP_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"InventorySync backup completed\", \"size\": \"$BACKUP_SIZE\", \"timestamp\": \"$TIMESTAMP\"}" \
        || echo "Failed to send backup notification"
fi