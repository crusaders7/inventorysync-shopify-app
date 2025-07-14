#!/bin/bash
# Setup cron job for automatic PostgreSQL backups

# Path to the backup script
BACKUP_SCRIPT="/home/brend/inventorysync-shopify-app/backend/scripts/backup_postgresql.py"
VENV_PATH="/home/brend/inventorysync-shopify-app/backend/venv"

# Create a cron entry (runs daily at 2 AM)
CRON_CMD="0 2 * * * cd /home/brend/inventorysync-shopify-app/backend && source $VENV_PATH/bin/activate && python $BACKUP_SCRIPT >> /home/brend/inventorysync-shopify-app/backups/cron.log 2>&1"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -F "$BACKUP_SCRIPT") || {
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ Backup cron job added successfully!"
    echo "   Backups will run daily at 2:00 AM"
}

# Show current crontab
echo ""
echo "Current crontab:"
crontab -l | grep postgres || echo "No PostgreSQL backup jobs found"
