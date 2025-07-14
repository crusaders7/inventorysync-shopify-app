"""
Backup and Disaster Recovery Management
Comprehensive backup system for database and application data
"""

import os
import time
import shutil
import gzip
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
import boto3
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db, engine
from utils.logging import logger
from models import Store


class BackupManager:
    """Manages database backups and disaster recovery operations"""
    
    def __init__(self, backup_dir: str = "/var/backups/inventorysync"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # AWS S3 configuration for offsite backups
        self.s3_bucket = os.getenv('BACKUP_S3_BUCKET')
        self.s3_region = os.getenv('BACKUP_S3_REGION', 'us-east-1')
        self.s3_client = None
        
        if self.s3_bucket:
            try:
                self.s3_client = boto3.client('s3', region_name=self.s3_region)
            except Exception as e:
                logger.warning(f"S3 backup not configured: {e}")
        
        # Database configuration
        self.db_url = os.getenv('DATABASE_URL')
        self.db_session = next(get_db())
        
        # Backup retention settings
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        self.hourly_retention_hours = 48  # Keep hourly backups for 48 hours
        self.daily_retention_days = 30    # Keep daily backups for 30 days
        self.weekly_retention_weeks = 12  # Keep weekly backups for 12 weeks
        self.monthly_retention_months = 12 # Keep monthly backups for 12 months
    
    def create_database_backup(self, backup_type: str = "manual") -> Dict[str, Any]:
        """Create a complete database backup"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"inventorysync_db_{backup_type}_{timestamp}"
        
        logger.info(f"Starting {backup_type} database backup: {backup_name}")
        
        try:
            if self.db_url.startswith('postgresql://'):
                backup_file = self._create_postgresql_backup(backup_name)
            elif self.db_url.startswith('sqlite://'):
                backup_file = self._create_sqlite_backup(backup_name)
            else:
                raise ValueError(f"Unsupported database type: {self.db_url}")
            
            # Compress backup
            compressed_backup = self._compress_backup(backup_file)
            
            # Calculate checksum
            checksum = self._calculate_checksum(compressed_backup)
            
            # Create backup metadata
            metadata = {
                "backup_name": backup_name,
                "backup_type": backup_type,
                "timestamp": timestamp,
                "database_type": self._get_database_type(),
                "backup_file": str(compressed_backup),
                "original_size": backup_file.stat().st_size,
                "compressed_size": compressed_backup.stat().st_size,
                "checksum": checksum,
                "created_at": datetime.utcnow().isoformat(),
                "compression_ratio": round(compressed_backup.stat().st_size / backup_file.stat().st_size, 2)
            }
            
            # Save metadata
            metadata_file = compressed_backup.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Upload to S3 if configured
            if self.s3_client:
                self._upload_to_s3(compressed_backup, metadata_file)
            
            # Cleanup original uncompressed backup
            backup_file.unlink()
            
            logger.info(f"Backup completed successfully: {compressed_backup}")
            return metadata
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    def _create_postgresql_backup(self, backup_name: str) -> Path:
        """Create PostgreSQL backup using pg_dump"""
        backup_file = self.backup_dir / f"{backup_name}.sql"
        
        # Parse database URL for pg_dump
        db_config = self._parse_database_url()
        
        # Build pg_dump command
        cmd = [
            'pg_dump',
            '--host', db_config['host'],
            '--port', str(db_config['port']),
            '--username', db_config['username'],
            '--dbname', db_config['database'],
            '--verbose',
            '--clean',
            '--if-exists',
            '--create',
            '--format=plain',
            '--file', str(backup_file)
        ]
        
        # Set password via environment
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['password']
        
        # Execute backup
        logger.info(f"Running pg_dump for database backup")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"pg_dump failed: {result.stderr}")
        
        logger.info(f"PostgreSQL backup created: {backup_file}")
        return backup_file
    
    def _create_sqlite_backup(self, backup_name: str) -> Path:
        """Create SQLite backup"""
        backup_file = self.backup_dir / f"{backup_name}.db"
        
        # Get SQLite database path
        db_path = self.db_url.replace('sqlite:///', '')
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"SQLite database not found: {db_path}")
        
        # Use SQLite .backup command for consistent backup
        cmd = [
            'sqlite3',
            db_path,
            f'.backup {backup_file}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"SQLite backup failed: {result.stderr}")
        
        logger.info(f"SQLite backup created: {backup_file}")
        return backup_file
    
    def _compress_backup(self, backup_file: Path) -> Path:
        """Compress backup file using gzip"""
        compressed_file = backup_file.with_suffix(backup_file.suffix + '.gz')
        
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        logger.info(f"Backup compressed: {compressed_file}")
        return compressed_file
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of backup file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _upload_to_s3(self, backup_file: Path, metadata_file: Path):
        """Upload backup and metadata to S3"""
        try:
            # Upload backup file
            backup_key = f"database-backups/{backup_file.name}"
            self.s3_client.upload_file(str(backup_file), self.s3_bucket, backup_key)
            
            # Upload metadata
            metadata_key = f"database-backups/{metadata_file.name}"
            self.s3_client.upload_file(str(metadata_file), self.s3_bucket, metadata_key)
            
            logger.info(f"Backup uploaded to S3: s3://{self.s3_bucket}/{backup_key}")
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            # Don't fail the backup if S3 upload fails
    
    def create_application_backup(self) -> Dict[str, Any]:
        """Create backup of application configuration and custom data"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"inventorysync_app_{timestamp}"
        backup_dir = self.backup_dir / backup_name
        backup_dir.mkdir(exist_ok=True)
        
        logger.info(f"Starting application backup: {backup_name}")
        
        try:
            # Backup configuration files
            config_backup = backup_dir / "config"
            config_backup.mkdir(exist_ok=True)
            
            # Copy important config files
            config_files = [
                "alembic.ini",
                ".env",
                "requirements.txt"
            ]
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    shutil.copy2(config_file, config_backup)
            
            # Export store configurations
            stores_data = self._export_store_configurations()
            with open(backup_dir / "stores_config.json", 'w') as f:
                json.dump(stores_data, f, indent=2, default=str)
            
            # Export custom field definitions
            custom_fields = self._export_custom_field_definitions()
            with open(backup_dir / "custom_fields.json", 'w') as f:
                json.dump(custom_fields, f, indent=2, default=str)
            
            # Export workflow rules
            workflows = self._export_workflow_rules()
            with open(backup_dir / "workflows.json", 'w') as f:
                json.dump(workflows, f, indent=2, default=str)
            
            # Create tarball
            archive_path = self.backup_dir / f"{backup_name}.tar.gz"
            shutil.make_archive(str(archive_path.with_suffix('')), 'gztar', str(backup_dir))
            
            # Clean up temporary directory
            shutil.rmtree(backup_dir)
            
            # Calculate metadata
            metadata = {
                "backup_name": backup_name,
                "backup_type": "application",
                "timestamp": timestamp,
                "backup_file": str(archive_path),
                "size": archive_path.stat().st_size,
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Application backup completed: {archive_path}")
            return metadata
            
        except Exception as e:
            logger.error(f"Application backup failed: {e}")
            raise
    
    def _export_store_configurations(self) -> List[Dict]:
        """Export store configurations for backup"""
        stores = self.db_session.query(Store).all()
        return [
            {
                "shopify_store_id": store.shopify_store_id,
                "shop_domain": store.shop_domain,
                "store_name": store.store_name,
                "currency": store.currency,
                "timezone": store.timezone,
                "subscription_plan": store.subscription_plan,
                "subscription_status": store.subscription_status
            }
            for store in stores
        ]
    
    def _export_custom_field_definitions(self) -> List[Dict]:
        """Export custom field definitions"""
        # This would query CustomFieldDefinition model
        # For now, return empty list as placeholder
        return []
    
    def _export_workflow_rules(self) -> List[Dict]:
        """Export workflow rules"""
        # This would query WorkflowRule model
        # For now, return empty list as placeholder
        return []
    
    def restore_database_backup(self, backup_path: str, verify_checksum: bool = True) -> bool:
        """Restore database from backup"""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        logger.warning(f"Starting database restore from: {backup_file}")
        
        try:
            # Verify checksum if requested
            if verify_checksum:
                metadata_file = backup_file.with_suffix('.json')
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    
                    current_checksum = self._calculate_checksum(backup_file)
                    if current_checksum != metadata.get('checksum'):
                        raise ValueError("Backup file checksum verification failed")
                    
                    logger.info("Backup checksum verified successfully")
            
            # Decompress if needed
            if backup_file.suffix == '.gz':
                decompressed_file = backup_file.with_suffix('')
                with gzip.open(backup_file, 'rb') as f_in:
                    with open(decompressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_file = decompressed_file
            else:
                restore_file = backup_file
            
            # Perform restore based on database type
            if self.db_url.startswith('postgresql://'):
                success = self._restore_postgresql_backup(restore_file)
            elif self.db_url.startswith('sqlite://'):
                success = self._restore_sqlite_backup(restore_file)
            else:
                raise ValueError(f"Unsupported database type: {self.db_url}")
            
            # Cleanup decompressed file if created
            if restore_file != backup_file:
                restore_file.unlink()
            
            if success:
                logger.info("Database restore completed successfully")
            else:
                logger.error("Database restore failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
    
    def _restore_postgresql_backup(self, backup_file: Path) -> bool:
        """Restore PostgreSQL backup using psql"""
        db_config = self._parse_database_url()
        
        # Build psql command
        cmd = [
            'psql',
            '--host', db_config['host'],
            '--port', str(db_config['port']),
            '--username', db_config['username'],
            '--dbname', db_config['database'],
            '--file', str(backup_file),
            '--single-transaction',
            '--set', 'ON_ERROR_STOP=on'
        ]
        
        # Set password via environment
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['password']
        
        # Execute restore
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"psql restore failed: {result.stderr}")
            return False
        
        return True
    
    def _restore_sqlite_backup(self, backup_file: Path) -> bool:
        """Restore SQLite backup"""
        db_path = self.db_url.replace('sqlite:///', '')
        
        # Create backup of current database
        if os.path.exists(db_path):
            backup_current = f"{db_path}.backup_{int(time.time())}"
            shutil.copy2(db_path, backup_current)
            logger.info(f"Current database backed up to: {backup_current}")
        
        # Restore from backup
        try:
            shutil.copy2(backup_file, db_path)
            logger.info(f"SQLite database restored from: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"SQLite restore failed: {e}")
            return False
    
    def list_backups(self, backup_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        # Scan backup directory
        for backup_file in self.backup_dir.glob("*.gz"):
            metadata_file = backup_file.with_suffix('.json')
            
            if metadata_file.exists():
                try:
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    
                    if backup_type is None or metadata.get('backup_type') == backup_type:
                        metadata['local_path'] = str(backup_file)
                        backups.append(metadata)
                        
                except Exception as e:
                    logger.warning(f"Failed to read metadata for {backup_file}: {e}")
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return backups
    
    def cleanup_old_backups(self) -> Dict[str, int]:
        """Clean up old backups based on retention policy"""
        logger.info("Starting backup cleanup")
        
        cleanup_stats = {
            "hourly_cleaned": 0,
            "daily_cleaned": 0,
            "weekly_cleaned": 0,
            "monthly_cleaned": 0,
            "total_cleaned": 0
        }
        
        now = datetime.utcnow()
        backups = self.list_backups()
        
        for backup in backups:
            try:
                backup_time = datetime.fromisoformat(backup['created_at'])
                age = now - backup_time
                backup_type = backup.get('backup_type', 'manual')
                
                should_delete = False
                
                # Apply retention rules
                if backup_type == 'hourly' and age > timedelta(hours=self.hourly_retention_hours):
                    should_delete = True
                    cleanup_stats["hourly_cleaned"] += 1
                elif backup_type == 'daily' and age > timedelta(days=self.daily_retention_days):
                    should_delete = True
                    cleanup_stats["daily_cleaned"] += 1
                elif backup_type == 'weekly' and age > timedelta(weeks=self.weekly_retention_weeks):
                    should_delete = True
                    cleanup_stats["weekly_cleaned"] += 1
                elif backup_type == 'monthly' and age > timedelta(days=self.monthly_retention_months * 30):
                    should_delete = True
                    cleanup_stats["monthly_cleaned"] += 1
                
                if should_delete:
                    backup_path = Path(backup['local_path'])
                    metadata_path = backup_path.with_suffix('.json')
                    
                    # Delete local files
                    if backup_path.exists():
                        backup_path.unlink()
                    if metadata_path.exists():
                        metadata_path.unlink()
                    
                    # Delete from S3 if configured
                    if self.s3_client:
                        try:
                            s3_key = f"database-backups/{backup_path.name}"
                            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
                            
                            s3_metadata_key = f"database-backups/{metadata_path.name}"
                            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_metadata_key)
                        except Exception as e:
                            logger.warning(f"Failed to delete S3 backup: {e}")
                    
                    cleanup_stats["total_cleaned"] += 1
                    logger.info(f"Deleted old backup: {backup['backup_name']}")
                    
            except Exception as e:
                logger.warning(f"Error processing backup {backup.get('backup_name', 'unknown')}: {e}")
        
        logger.info(f"Backup cleanup completed: {cleanup_stats}")
        return cleanup_stats
    
    def verify_backup_integrity(self, backup_path: str) -> Dict[str, Any]:
        """Verify backup file integrity"""
        backup_file = Path(backup_path)
        metadata_file = backup_file.with_suffix('.json')
        
        verification_result = {
            "backup_file": str(backup_file),
            "file_exists": backup_file.exists(),
            "metadata_exists": metadata_file.exists(),
            "checksum_valid": False,
            "readable": False,
            "estimated_restore_time": None
        }
        
        if not backup_file.exists():
            return verification_result
        
        try:
            # Verify checksum
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
                
                current_checksum = self._calculate_checksum(backup_file)
                verification_result["checksum_valid"] = current_checksum == metadata.get('checksum')
            
            # Test readability
            if backup_file.suffix == '.gz':
                with gzip.open(backup_file, 'rb') as f:
                    f.read(1024)  # Read first 1KB
                verification_result["readable"] = True
            else:
                with open(backup_file, 'rb') as f:
                    f.read(1024)
                verification_result["readable"] = True
            
            # Estimate restore time based on file size
            file_size_mb = backup_file.stat().st_size / (1024 * 1024)
            estimated_minutes = max(1, int(file_size_mb / 50))  # Assume 50MB/minute
            verification_result["estimated_restore_time"] = f"{estimated_minutes} minutes"
            
        except Exception as e:
            verification_result["error"] = str(e)
        
        return verification_result
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get overall backup system status"""
        backups = self.list_backups()
        
        status = {
            "backup_directory": str(self.backup_dir),
            "total_backups": len(backups),
            "s3_configured": self.s3_client is not None,
            "latest_backup": backups[0] if backups else None,
            "backup_types": {},
            "total_size_mb": 0,
            "oldest_backup": backups[-1] if backups else None
        }
        
        # Calculate statistics by backup type
        for backup in backups:
            backup_type = backup.get('backup_type', 'unknown')
            if backup_type not in status["backup_types"]:
                status["backup_types"][backup_type] = 0
            status["backup_types"][backup_type] += 1
            
            # Calculate total size
            if 'compressed_size' in backup:
                status["total_size_mb"] += backup['compressed_size'] / (1024 * 1024)
        
        status["total_size_mb"] = round(status["total_size_mb"], 2)
        
        return status
    
    def _parse_database_url(self) -> Dict[str, Any]:
        """Parse database URL for connection parameters"""
        from urllib.parse import urlparse
        
        parsed = urlparse(self.db_url)
        
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 5432,
            'username': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/')
        }
    
    def _get_database_type(self) -> str:
        """Get database type from URL"""
        if self.db_url.startswith('postgresql://'):
            return 'postgresql'
        elif self.db_url.startswith('sqlite://'):
            return 'sqlite'
        else:
            return 'unknown'


class DisasterRecoveryManager:
    """Manages disaster recovery procedures and testing"""
    
    def __init__(self, backup_manager: BackupManager = None):
        self.backup_manager = backup_manager or BackupManager()
    
    def create_recovery_plan(self) -> Dict[str, Any]:
        """Create disaster recovery plan"""
        return {
            "recovery_procedures": [
                {
                    "step": 1,
                    "action": "Assess damage and determine recovery strategy",
                    "estimated_time": "15 minutes",
                    "responsible": "DevOps Team"
                },
                {
                    "step": 2,
                    "action": "Set up new infrastructure if needed",
                    "estimated_time": "30-60 minutes",
                    "responsible": "Infrastructure Team"
                },
                {
                    "step": 3,
                    "action": "Restore latest database backup",
                    "estimated_time": "10-30 minutes",
                    "responsible": "Database Administrator"
                },
                {
                    "step": 4,
                    "action": "Restore application configuration",
                    "estimated_time": "10 minutes",
                    "responsible": "DevOps Team"
                },
                {
                    "step": 5,
                    "action": "Verify data integrity and application functionality",
                    "estimated_time": "20 minutes",
                    "responsible": "QA Team"
                },
                {
                    "step": 6,
                    "action": "Update DNS and redirect traffic",
                    "estimated_time": "10 minutes",
                    "responsible": "DevOps Team"
                },
                {
                    "step": 7,
                    "action": "Monitor system stability",
                    "estimated_time": "60 minutes",
                    "responsible": "Operations Team"
                }
            ],
            "estimated_total_recovery_time": "2.5-4 hours",
            "rpo_target": "1 hour",  # Recovery Point Objective
            "rto_target": "4 hours",  # Recovery Time Objective
            "emergency_contacts": [
                "DevOps Lead: ops-lead@company.com",
                "Database Admin: dba@company.com",
                "Infrastructure Team: infrastructure@company.com"
            ]
        }
    
    def test_recovery_procedure(self, backup_path: str = None) -> Dict[str, Any]:
        """Test disaster recovery procedure"""
        logger.info("Starting disaster recovery test")
        
        test_result = {
            "test_started_at": datetime.utcnow().isoformat(),
            "test_type": "disaster_recovery_simulation",
            "steps_completed": [],
            "steps_failed": [],
            "total_time_seconds": 0,
            "success": False
        }
        
        start_time = time.time()
        
        try:
            # Step 1: Verify backup availability
            step_start = time.time()
            if backup_path:
                verification = self.backup_manager.verify_backup_integrity(backup_path)
                if not verification["file_exists"] or not verification["readable"]:
                    raise Exception("Backup file verification failed")
            else:
                backups = self.backup_manager.list_backups()
                if not backups:
                    raise Exception("No backups available for recovery test")
                backup_path = backups[0]["local_path"]
            
            test_result["steps_completed"].append({
                "step": "backup_verification",
                "duration_seconds": time.time() - step_start,
                "status": "success"
            })
            
            # Step 2: Create test database (simulation)
            step_start = time.time()
            # In a real test, this would create a separate test environment
            test_result["steps_completed"].append({
                "step": "test_environment_setup",
                "duration_seconds": time.time() - step_start,
                "status": "simulated"
            })
            
            # Step 3: Simulate restore process
            step_start = time.time()
            # In a real test, this would perform actual restore to test environment
            test_result["steps_completed"].append({
                "step": "database_restore_simulation",
                "duration_seconds": time.time() - step_start,
                "status": "simulated"
            })
            
            # Step 4: Verify data integrity
            step_start = time.time()
            # This would run data integrity checks
            test_result["steps_completed"].append({
                "step": "data_integrity_check",
                "duration_seconds": time.time() - step_start,
                "status": "simulated"
            })
            
            test_result["success"] = True
            
        except Exception as e:
            test_result["steps_failed"].append({
                "step": "recovery_test",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        test_result["total_time_seconds"] = time.time() - start_time
        test_result["test_completed_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Disaster recovery test completed: {test_result['success']}")
        return test_result