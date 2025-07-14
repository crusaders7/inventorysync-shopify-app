#!/usr/bin/env python3
"""
PostgreSQL Backup Script with Rotation
Performs daily backups with weekly and monthly retention
"""

import os
import subprocess
import datetime
import gzip
import shutil
from pathlib import Path
from dotenv import load_dotenv
import urllib.parse
import logging

load_dotenv()

# Configuration
BACKUP_DIR = Path("/home/brend/inventorysync-shopify-app/backups")
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://inventorysync:devpassword123@localhost:5432/inventorysync_dev")

# Parse PostgreSQL URL
url = urllib.parse.urlparse(POSTGRES_URL)

# Backup retention settings
DAILY_RETENTION_DAYS = 7
WEEKLY_RETENTION_WEEKS = 4
MONTHLY_RETENTION_MONTHS = 12

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BACKUP_DIR / "backup.log"),
        logging.StreamHandler()
    ]
)


def ensure_backup_dirs():
    """Create backup directory structure"""
    dirs = [
        BACKUP_DIR / "daily",
        BACKUP_DIR / "weekly",
        BACKUP_DIR / "monthly",
        BACKUP_DIR / "logs"
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    logging.info(f"Backup directories ensured at {BACKUP_DIR}")


def perform_backup():
    """Perform PostgreSQL backup"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"inventorysync_backup_{timestamp}.sql"
    backup_path = BACKUP_DIR / "daily" / backup_filename
    
    # Set PostgreSQL password
    env = os.environ.copy()
    env['PGPASSWORD'] = url.password
    
    # Perform backup using pg_dump
    cmd = [
        'pg_dump',
        '-h', url.hostname,
        '-p', str(url.port or 5432),
        '-U', url.username,
        '-d', url.path[1:],  # Remove leading slash
        '--verbose',
        '--no-owner',
        '--no-privileges',
        '--format=plain',
        '--file=' + str(backup_path)
    ]
    
    try:
        logging.info(f"Starting backup to {backup_path}")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"Backup failed: {result.stderr}")
            raise Exception(f"pg_dump failed: {result.stderr}")
        
        # Compress the backup
        compressed_path = backup_path.with_suffix('.sql.gz')
        logging.info(f"Compressing backup to {compressed_path}")
        
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        backup_path.unlink()
        
        # Get file size
        size_mb = compressed_path.stat().st_size / (1024 * 1024)
        logging.info(f"Backup completed successfully: {compressed_path.name} ({size_mb:.2f} MB)")
        
        return compressed_path
        
    except Exception as e:
        logging.error(f"Backup failed: {str(e)}")
        raise


def promote_to_weekly(backup_path):
    """Copy daily backup to weekly folder if it's Sunday"""
    if datetime.datetime.now().weekday() == 6:  # Sunday
        weekly_path = BACKUP_DIR / "weekly" / backup_path.name
        shutil.copy2(backup_path, weekly_path)
        logging.info(f"Promoted to weekly backup: {weekly_path.name}")


def promote_to_monthly(backup_path):
    """Copy daily backup to monthly folder if it's the 1st"""
    if datetime.datetime.now().day == 1:
        monthly_path = BACKUP_DIR / "monthly" / backup_path.name
        shutil.copy2(backup_path, monthly_path)
        logging.info(f"Promoted to monthly backup: {monthly_path.name}")


def cleanup_old_backups():
    """Remove old backups according to retention policy"""
    now = datetime.datetime.now()
    
    # Clean daily backups
    for backup in (BACKUP_DIR / "daily").glob("*.sql.gz"):
        age_days = (now - datetime.datetime.fromtimestamp(backup.stat().st_mtime)).days
        if age_days > DAILY_RETENTION_DAYS:
            backup.unlink()
            logging.info(f"Removed old daily backup: {backup.name}")
    
    # Clean weekly backups
    for backup in (BACKUP_DIR / "weekly").glob("*.sql.gz"):
        age_weeks = (now - datetime.datetime.fromtimestamp(backup.stat().st_mtime)).days // 7
        if age_weeks > WEEKLY_RETENTION_WEEKS:
            backup.unlink()
            logging.info(f"Removed old weekly backup: {backup.name}")
    
    # Clean monthly backups
    for backup in (BACKUP_DIR / "monthly").glob("*.sql.gz"):
        age_months = (now - datetime.datetime.fromtimestamp(backup.stat().st_mtime)).days // 30
        if age_months > MONTHLY_RETENTION_MONTHS:
            backup.unlink()
            logging.info(f"Removed old monthly backup: {backup.name}")


def verify_backup(backup_path):
    """Verify backup integrity"""
    try:
        # Test if we can decompress the file
        with gzip.open(backup_path, 'rb') as f:
            # Read first few bytes to verify it's valid
            f.read(1024)
        logging.info(f"Backup verification passed: {backup_path.name}")
        return True
    except Exception as e:
        logging.error(f"Backup verification failed: {str(e)}")
        return False


def generate_backup_report():
    """Generate a report of all backups"""
    report = []
    report.append("=== PostgreSQL Backup Report ===")
    report.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    for folder in ["daily", "weekly", "monthly"]:
        backups = sorted((BACKUP_DIR / folder).glob("*.sql.gz"))
        report.append(f"\n{folder.upper()} BACKUPS ({len(backups)} files):")
        
        total_size = 0
        for backup in backups[-5:]:  # Show last 5
            size_mb = backup.stat().st_size / (1024 * 1024)
            total_size += size_mb
            mod_time = datetime.datetime.fromtimestamp(backup.stat().st_mtime)
            report.append(f"  - {backup.name}: {size_mb:.2f} MB (Modified: {mod_time.strftime('%Y-%m-%d %H:%M')})")
        
        if backups:
            report.append(f"  Total size: {total_size:.2f} MB")
    
    report_text = "\n".join(report)
    report_path = BACKUP_DIR / "backup_report.txt"
    report_path.write_text(report_text)
    
    return report_text


def main():
    """Main backup process"""
    logging.info("=== Starting PostgreSQL Backup Process ===")
    
    try:
        # Ensure backup directories exist
        ensure_backup_dirs()
        
        # Perform backup
        backup_path = perform_backup()
        
        # Verify backup
        if not verify_backup(backup_path):
            raise Exception("Backup verification failed")
        
        # Promote to weekly/monthly if applicable
        promote_to_weekly(backup_path)
        promote_to_monthly(backup_path)
        
        # Clean up old backups
        cleanup_old_backups()
        
        # Generate report
        report = generate_backup_report()
        print("\n" + report)
        
        logging.info("=== Backup Process Completed Successfully ===")
        
    except Exception as e:
        logging.error(f"Backup process failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
