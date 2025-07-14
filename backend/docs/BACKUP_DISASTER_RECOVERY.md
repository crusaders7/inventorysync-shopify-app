# Backup and Disaster Recovery Guide

Comprehensive backup and disaster recovery procedures for InventorySync to ensure data protection and business continuity.

## Overview

Our backup and disaster recovery strategy provides:
- **Automated multi-tier backups** (hourly, daily, weekly, monthly)
- **Point-in-time recovery** capabilities
- **Offsite backup storage** with AWS S3 integration
- **Disaster recovery testing** and validation
- **Data integrity verification** with checksums
- **Automated cleanup** and retention management

## Backup Strategy

### Backup Types

#### 1. Database Backups
- **PostgreSQL**: Uses `pg_dump` for consistent backups
- **SQLite**: Uses `.backup` command for development
- **Compression**: Gzip compression (typically 5-10x reduction)
- **Integrity**: SHA256 checksums for verification

#### 2. Application Backups
- Configuration files and settings
- Custom field definitions
- Workflow rules and automation
- Store configurations

### Backup Schedule

#### Production Schedule
```bash
# Hourly backups (database only)
0,30 * * * * /path/to/automated_backup.py

# Daily backups (database + cleanup)
0 2 * * * /path/to/automated_backup.py

# Weekly backups (full backup + application config)
0 2 * * 0 /path/to/automated_backup.py

# Monthly backups (full backup + health check)
0 2 1 * * /path/to/automated_backup.py
```

#### Retention Policy
- **Hourly**: 48 hours (48 backups)
- **Daily**: 30 days (30 backups)
- **Weekly**: 12 weeks (12 backups)
- **Monthly**: 12 months (12 backups)

### Storage Locations

#### Local Storage
- **Primary**: `/var/backups/inventorysync/`
- **Format**: Compressed `.sql.gz` or `.db.gz` files
- **Metadata**: JSON files with backup information

#### Offsite Storage (S3)
```bash
# S3 bucket structure
s3://your-backup-bucket/
├── database-backups/
│   ├── inventorysync_db_daily_20240115_020000.sql.gz
│   ├── inventorysync_db_daily_20240115_020000.json
│   └── ...
└── application-backups/
    ├── inventorysync_app_20240115_020000.tar.gz
    └── ...
```

## Setup Instructions

### 1. Environment Configuration

```bash
# Database backup settings
DATABASE_URL=postgresql://user:password@localhost/inventorysync

# Backup storage
BACKUP_S3_BUCKET=your-backup-bucket
BACKUP_S3_REGION=us-east-1
BACKUP_RETENTION_DAYS=30

# Backup schedule (optional overrides)
BACKUP_HOURLY_ENABLED=true
BACKUP_DAILY_ENABLED=true
BACKUP_WEEKLY_ENABLED=true
BACKUP_MONTHLY_ENABLED=true

# Cleanup settings
BACKUP_AUTO_CLEANUP=true

# Health monitoring
BACKUP_HEALTH_CHECK=true

# Notifications
BACKUP_SLACK_WEBHOOK=https://hooks.slack.com/services/...
BACKUP_EMAIL_NOTIFICATIONS=true
BACKUP_EMAIL_RECIPIENTS=admin@company.com,ops@company.com
BACKUP_NOTIFY_SUCCESS=false  # Only notify on failures by default
```

### 2. Install Dependencies

```bash
# System dependencies
sudo apt-get install postgresql-client sqlite3

# Python dependencies (if not in requirements.txt)
pip install boto3 requests
```

### 3. AWS S3 Setup

```bash
# Configure AWS credentials
aws configure
# or set environment variables:
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key

# Create S3 bucket with versioning
aws s3 mb s3://your-backup-bucket
aws s3api put-bucket-versioning --bucket your-backup-bucket --versioning-configuration Status=Enabled
```

### 4. Schedule Automated Backups

```bash
# Add to crontab
crontab -e

# Add these lines:
# Automated backup every 30 minutes
0,30 * * * * /usr/bin/python3 /path/to/inventorysync/backend/scripts/automated_backup.py >> /var/log/inventorysync/backup.log 2>&1

# Health check twice per month
30 3 1,15 * * /usr/bin/python3 /path/to/inventorysync/backend/scripts/automated_backup.py --force-health-check >> /var/log/inventorysync/backup.log 2>&1
```

## Manual Backup Operations

### Create Backups

```bash
# Create database backup
python scripts/backup_system.py create --type database --backup-type manual

# Create full backup (database + application)
python scripts/backup_system.py create --type all --backup-type weekly --output backup_report.json

# Create application configuration backup only
python scripts/backup_system.py create --type application
```

### List and Verify Backups

```bash
# List all backups
python scripts/backup_system.py list

# List only daily backups
python scripts/backup_system.py list --backup-type daily

# Verify all backups
python scripts/backup_system.py verify

# Verify specific backup
python scripts/backup_system.py verify --backup-path /var/backups/inventorysync/backup.sql.gz
```

### Backup System Status

```bash
# Check backup system status
python scripts/backup_system.py status

# Example output:
📊 Backup System Status
====================
Backup Directory: /var/backups/inventorysync
Total Backups: 45
Total Size: 2.8 GB
S3 Configured: ✅ Yes

📈 Backup Types:
   hourly: 24
   daily: 15
   weekly: 4
   monthly: 2

🕐 Latest Backup:
   Name: inventorysync_db_hourly_20240115_143000
   Type: hourly
   Created: 2024-01-15 14:30:00 UTC
```

## Restore Procedures

### Database Restore

#### Interactive Restore
```bash
# Interactive restore (shows backup list)
python scripts/backup_system.py restore

# Example session:
📦 Available backups:
  1. inventorysync_db_daily_20240115_020000 (2024-01-15 02:00)
  2. inventorysync_db_hourly_20240115_143000 (2024-01-15 14:30)
  3. inventorysync_db_weekly_20240114_020000 (2024-01-14 02:00)

Select backup number to restore: 1

⚠️  WARNING: This will restore the database from:
   /var/backups/inventorysync/inventorysync_db_daily_20240115_020000.sql.gz

   This operation will OVERWRITE the current database!

Type 'YES' to confirm restore: YES

🔄 Restoring database from backup...
✅ Database restore completed successfully
🔍 Please verify application functionality
```

#### Direct Restore
```bash
# Restore from specific backup file
python scripts/backup_system.py restore --backup-path /path/to/backup.sql.gz --force

# Skip checksum verification (not recommended)
python scripts/backup_system.py restore --backup-path /path/to/backup.sql.gz --skip-checksum --force
```

### Point-in-Time Recovery

For PostgreSQL with WAL archiving (advanced setup):

```bash
# Stop the application
sudo systemctl stop inventorysync

# Restore base backup
pg_restore -d inventorysync /path/to/base_backup.sql

# Apply WAL files up to specific time
# (requires WAL archiving to be configured)

# Start the application
sudo systemctl start inventorysync
```

## Disaster Recovery Procedures

### Recovery Time Objectives (RTO)
- **Database Restore**: 10-30 minutes
- **Application Setup**: 30-60 minutes
- **DNS/Traffic Redirect**: 10 minutes
- **Total Recovery Time**: 2-4 hours

### Recovery Point Objectives (RPO)
- **Standard**: 1 hour (hourly backups)
- **Critical Data**: 30 minutes (with increased backup frequency)

### Disaster Recovery Steps

#### 1. Assessment and Planning
```bash
# Assess the situation
- Determine scope of failure (database, application, infrastructure)
- Identify required recovery point
- Assemble recovery team

# Test disaster recovery procedure
python scripts/backup_system.py test-dr --show-plan
```

#### 2. Infrastructure Setup
```bash
# If new infrastructure is needed:
# 1. Provision new servers/containers
# 2. Install required software
# 3. Configure networking and security
# 4. Set up monitoring
```

#### 3. Database Recovery
```bash
# Choose appropriate backup
python scripts/backup_system.py list

# Restore database
python scripts/backup_system.py restore --backup-path /path/to/backup.sql.gz --force

# Verify data integrity
python scripts/optimize_database.py analyze
```

#### 4. Application Recovery
```bash
# Deploy application code
git clone https://github.com/your-org/inventorysync
cd inventorysync/backend

# Install dependencies
pip install -r requirements.txt

# Apply any pending migrations
alembic upgrade head

# Start application
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 5. Verification and Validation
```bash
# Health check
curl -f http://localhost:8000/api/v1/monitoring/health

# Functional testing
python -c "
import requests
response = requests.get('http://localhost:8000/api/v1/dashboard/test-store.myshopify.com')
print('✅ API functional' if response.status_code == 200 else '❌ API issue')
"

# Database integrity check
python scripts/optimize_database.py analyze
```

#### 6. Traffic Redirection
```bash
# Update DNS records
# Update load balancer configuration
# Notify users of service restoration
```

### Testing Disaster Recovery

#### Monthly DR Tests
```bash
# Run automated DR test
python scripts/backup_system.py test-dr --show-plan

# Example output:
🧪 Starting disaster recovery test...

📊 Disaster Recovery Test Results
==============================
Test Duration: 45.2 seconds
Overall Status: ✅ Success

✅ Completed Steps:
   • backup_verification: 2.1s (success)
   • test_environment_setup: 15.3s (simulated)
   • database_restore_simulation: 25.8s (simulated)
   • data_integrity_check: 2.0s (simulated)

📋 Disaster Recovery Plan
========================
RTO Target: 4 hours
RPO Target: 1 hour
Estimated Total Time: 2.5-4 hours
```

#### Full DR Drill (Quarterly)
1. **Schedule maintenance window**
2. **Create test environment**
3. **Perform actual restore**
4. **Run functional tests**
5. **Document lessons learned**
6. **Update procedures**

## Monitoring and Alerting

### Backup Monitoring

#### Health Checks
```bash
# Manual health check
python scripts/automated_backup.py --force-health-check

# Automated health checks (configured in cron)
# Runs on 1st and 15th of each month
```

#### Key Metrics
- **Backup Success Rate**: >99.5%
- **Backup Size Trend**: Monitor for unexpected changes
- **Backup Duration**: Alert if >30 minutes
- **Recovery Test Success**: Monthly validation

### Alerting Channels

#### Slack Integration
```json
{
  "text": "InventorySync Backup System",
  "attachments": [
    {
      "color": "danger",
      "title": "❌ Daily backup failed",
      "fields": [
        {"title": "Environment", "value": "production"},
        {"title": "Error", "value": "Database connection timeout"}
      ]
    }
  ]
}
```

#### Email Notifications
- **Recipients**: Operations team, database administrators
- **Frequency**: Immediate for failures, daily summary for success
- **Content**: Backup status, error details, recommended actions

### Log Monitoring

#### Log Locations
```bash
# Application logs
/var/log/inventorysync/backup.log

# System logs
journalctl -u inventorysync-backup

# Backup script output
/var/log/inventorysync/automated_backup.log
```

#### Log Analysis
```bash
# Check for backup failures in last 24 hours
grep -i "failed\|error" /var/log/inventorysync/backup.log | tail -20

# Monitor backup sizes
grep "compressed_size" /var/log/inventorysync/backup.log | tail -10

# Check cleanup operations
grep "cleanup" /var/log/inventorysync/backup.log | tail -5
```

## Maintenance and Best Practices

### Regular Maintenance Tasks

#### Weekly
- Review backup success rates
- Check storage usage and cleanup
- Verify latest backup integrity

#### Monthly
- Run disaster recovery test
- Review and update retention policies
- Analyze backup performance trends

#### Quarterly
- Full disaster recovery drill
- Review and update documentation
- Audit backup security and access

### Security Best Practices

#### Access Control
```bash
# Backup directory permissions
chmod 700 /var/backups/inventorysync
chown postgres:postgres /var/backups/inventorysync

# Script permissions
chmod 750 /path/to/scripts/backup_system.py
chmod 750 /path/to/scripts/automated_backup.py
```

#### Encryption
```bash
# Database backup encryption (GPG)
gpg --symmetric --cipher-algo AES256 backup.sql.gz

# S3 server-side encryption
aws s3 cp backup.sql.gz s3://bucket/backup.sql.gz --sse AES256
```

#### Audit Trail
- Log all backup and restore operations
- Monitor access to backup files
- Regular security reviews of backup procedures

### Performance Optimization

#### Backup Performance
```bash
# Parallel backup for large databases
pg_dump --jobs=4 --format=directory database_name

# Compressed backup with progress
pg_dump database_name | gzip | pv > backup.sql.gz

# Use local SSD for temporary backup files
export TMPDIR=/fast/ssd/tmp
```

#### Network Optimization
```bash
# S3 multipart upload for large files
aws configure set default.s3.multipart_threshold 64MB
aws configure set default.s3.multipart_chunksize 16MB

# Bandwidth limiting for off-hours
ionice -c 3 aws s3 sync /backups/ s3://bucket/
```

## Troubleshooting

### Common Issues

#### Backup Failures

**Issue**: `pg_dump: connection failed`
```bash
# Check database connectivity
pg_isready -h localhost -p 5432

# Verify credentials
psql -h localhost -U postgres -d inventorysync -c "SELECT 1;"

# Check logs
tail -f /var/log/postgresql/postgresql.log
```

**Issue**: `No space left on device`
```bash
# Check disk usage
df -h /var/backups

# Clean old backups
python scripts/backup_system.py cleanup --force

# Increase retention cleanup frequency
```

**Issue**: `S3 upload failed`
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify bucket permissions
aws s3 ls s3://your-backup-bucket/

# Test connectivity
aws s3 cp test.txt s3://your-backup-bucket/test.txt
```

#### Restore Issues

**Issue**: `Checksum verification failed`
```bash
# Download fresh copy from S3
aws s3 cp s3://bucket/backup.sql.gz ./backup.sql.gz

# Skip checksum verification (last resort)
python scripts/backup_system.py restore --skip-checksum --backup-path backup.sql.gz
```

**Issue**: `Database restore taking too long`
```bash
# Monitor restore progress
watch -n 5 'ps aux | grep psql'

# Check for blocking queries
SELECT pid, query FROM pg_stat_activity WHERE state = 'active';

# Optimize restore settings
psql -c "SET maintenance_work_mem = '2GB';"
```

### Emergency Procedures

#### Complete Data Loss
1. **Stop all application instances**
2. **Assess available backups**
3. **Set up new database instance**
4. **Restore from latest valid backup**
5. **Verify data integrity**
6. **Gradually bring application online**
7. **Monitor for issues**

#### Partial Data Corruption
1. **Identify affected tables/data**
2. **Create current database backup**
3. **Extract clean data from backup**
4. **Selectively restore affected portions**
5. **Verify referential integrity**
6. **Test application functionality**

#### Backup System Failure
1. **Switch to manual backup procedures**
2. **Investigate and fix automation issues**
3. **Ensure backup coverage continuity**
4. **Test restored automation**
5. **Document lessons learned**

## Compliance and Documentation

### Compliance Requirements
- **Data Retention**: Follow industry and legal requirements
- **Audit Trail**: Maintain logs of all backup/restore operations
- **Testing**: Regular disaster recovery testing and documentation
- **Security**: Encrypt backups and secure access

### Documentation Maintenance
- **Runbooks**: Keep disaster recovery procedures updated
- **Contact Lists**: Maintain current emergency contact information
- **Inventory**: Document all backup systems and dependencies
- **Testing Results**: Record DR test results and improvements

---

For questions or assistance with backup and disaster recovery procedures, contact the operations team or refer to the emergency contact list in the disaster recovery plan.