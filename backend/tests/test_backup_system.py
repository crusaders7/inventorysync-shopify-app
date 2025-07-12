"""
Test backup and disaster recovery systems
Tests backup creation, restoration, and disaster recovery procedures
"""

import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock

from utils.backup_manager import BackupManager, DisasterRecoveryManager
from scripts.automated_backup import AutomatedBackupScheduler
from models import Store


class TestBackupManager:
    """Test backup manager functionality"""
    
    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory"""
        temp_dir = tempfile.mkdtemp(prefix="test_backup_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def backup_manager(self, temp_backup_dir):
        """Create backup manager with temp directory"""
        return BackupManager(backup_dir=temp_backup_dir)
    
    def test_backup_manager_initialization(self, backup_manager, temp_backup_dir):
        """Test backup manager initialization"""
        assert backup_manager.backup_dir == Path(temp_backup_dir)
        assert backup_manager.backup_dir.exists()
        assert backup_manager.retention_days == 30  # Default
    
    @patch('subprocess.run')
    def test_sqlite_backup_creation(self, mock_subprocess, backup_manager):
        """Test SQLite database backup creation"""
        # Mock successful subprocess run
        mock_subprocess.return_value = Mock(returncode=0, stderr="")
        
        # Mock database URL
        backup_manager.db_url = "sqlite:///test.db"
        
        with patch('os.path.exists', return_value=True):
            backup_metadata = backup_manager.create_database_backup("test")
        
        assert backup_metadata['backup_type'] == "test"
        assert backup_metadata['database_type'] == "sqlite"
        assert 'checksum' in backup_metadata
        assert 'compressed_size' in backup_metadata
        
        # Verify subprocess was called with correct command
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert 'sqlite3' in call_args[0]
        assert '.backup' in call_args[2]
    
    @patch('subprocess.run')
    def test_postgresql_backup_creation(self, mock_subprocess, backup_manager):
        """Test PostgreSQL database backup creation"""
        # Mock successful subprocess run
        mock_subprocess.return_value = Mock(returncode=0, stderr="")
        
        # Mock PostgreSQL database URL
        backup_manager.db_url = "postgresql://user:pass@localhost:5432/testdb"
        
        backup_metadata = backup_manager.create_database_backup("daily")
        
        assert backup_metadata['backup_type'] == "daily"
        assert backup_metadata['database_type'] == "postgresql"
        
        # Verify pg_dump was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert 'pg_dump' in call_args[0]
        assert '--host' in call_args
        assert 'localhost' in call_args
    
    def test_backup_compression(self, backup_manager, temp_backup_dir):
        """Test backup file compression"""
        # Create a test file to compress
        test_file = Path(temp_backup_dir) / "test_backup.sql"
        test_content = "SELECT * FROM test;" * 1000  # Repeatable content for compression
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        compressed_file = backup_manager._compress_backup(test_file)
        
        assert compressed_file.exists()
        assert compressed_file.suffix == '.gz'
        assert compressed_file.stat().st_size < test_file.stat().st_size
    
    def test_checksum_calculation(self, backup_manager, temp_backup_dir):
        """Test backup checksum calculation"""
        # Create test file
        test_file = Path(temp_backup_dir) / "test.txt"
        test_content = "test backup content"
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        checksum1 = backup_manager._calculate_checksum(test_file)
        checksum2 = backup_manager._calculate_checksum(test_file)
        
        # Same file should produce same checksum
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA256 length
    
    def test_application_backup_creation(self, backup_manager, db_session, sample_store):
        """Test application configuration backup"""
        backup_metadata = backup_manager.create_application_backup()
        
        assert backup_metadata['backup_type'] == "application"
        assert 'backup_file' in backup_metadata
        
        # Check that backup file exists
        backup_file = Path(backup_metadata['backup_file'])
        assert backup_file.exists()
        assert backup_file.suffix == '.gz'
    
    def test_backup_listing(self, backup_manager, temp_backup_dir):
        """Test listing available backups"""
        # Create mock backup files with metadata
        backup_files = [
            ("backup1_daily_20240115.sql.gz", {"backup_type": "daily", "created_at": "2024-01-15T02:00:00"}),
            ("backup2_weekly_20240114.sql.gz", {"backup_type": "weekly", "created_at": "2024-01-14T02:00:00"}),
            ("backup3_hourly_20240115.sql.gz", {"backup_type": "hourly", "created_at": "2024-01-15T14:00:00"})
        ]
        
        for filename, metadata in backup_files:
            backup_path = Path(temp_backup_dir) / filename
            backup_path.touch()
            
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
        
        # Test listing all backups
        all_backups = backup_manager.list_backups()
        assert len(all_backups) == 3
        
        # Test filtering by backup type
        daily_backups = backup_manager.list_backups("daily")
        assert len(daily_backups) == 1
        assert daily_backups[0]['backup_type'] == "daily"
        
        # Test sorting (newest first)
        assert all_backups[0]['created_at'] > all_backups[-1]['created_at']
    
    def test_backup_integrity_verification(self, backup_manager, temp_backup_dir):
        """Test backup file integrity verification"""
        # Create test backup with metadata
        backup_file = Path(temp_backup_dir) / "test_backup.sql.gz"
        test_content = b"test backup content"
        
        with open(backup_file, 'wb') as f:
            f.write(test_content)
        
        # Calculate real checksum
        checksum = backup_manager._calculate_checksum(backup_file)
        
        # Create metadata
        metadata = {
            "backup_name": "test_backup",
            "checksum": checksum,
            "created_at": datetime.utcnow().isoformat()
        }
        
        metadata_file = backup_file.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        # Test verification
        verification = backup_manager.verify_backup_integrity(str(backup_file))
        
        assert verification['file_exists']
        assert verification['metadata_exists']
        assert verification['checksum_valid']
        assert verification['readable']
        assert 'estimated_restore_time' in verification
    
    def test_backup_cleanup(self, backup_manager, temp_backup_dir):
        """Test old backup cleanup"""
        # Create old backups
        old_backups = [
            ("old_hourly_1.sql.gz", "hourly", datetime.utcnow() - timedelta(days=3)),
            ("old_daily_1.sql.gz", "daily", datetime.utcnow() - timedelta(days=45)),
            ("recent_daily.sql.gz", "daily", datetime.utcnow() - timedelta(hours=1))
        ]
        
        for filename, backup_type, created_time in old_backups:
            backup_path = Path(temp_backup_dir) / filename
            backup_path.touch()
            
            metadata = {
                "backup_name": filename,
                "backup_type": backup_type,
                "created_at": created_time.isoformat()
            }
            
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
        
        # Set retention to trigger cleanup
        backup_manager.hourly_retention_hours = 24
        backup_manager.daily_retention_days = 30
        
        cleanup_stats = backup_manager.cleanup_old_backups()
        
        # Check that old backups were cleaned up
        assert cleanup_stats['total_cleaned'] >= 2
        
        # Recent backup should still exist
        recent_backup = Path(temp_backup_dir) / "recent_daily.sql.gz"
        assert recent_backup.exists()
    
    def test_backup_status(self, backup_manager, temp_backup_dir):
        """Test backup system status reporting"""
        # Create some test backups
        for i in range(3):
            backup_file = Path(temp_backup_dir) / f"backup_{i}.sql.gz"
            backup_file.write_text(f"backup content {i}")
            
            metadata = {
                "backup_name": f"backup_{i}",
                "backup_type": "daily",
                "compressed_size": backup_file.stat().st_size,
                "created_at": datetime.utcnow().isoformat()
            }
            
            metadata_file = backup_file.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)
        
        status = backup_manager.get_backup_status()
        
        assert status['total_backups'] == 3
        assert status['backup_directory'] == str(backup_manager.backup_dir)
        assert 'total_size_mb' in status
        assert 'latest_backup' in status
        assert 'backup_types' in status
    
    @patch('subprocess.run')
    def test_database_restore(self, mock_subprocess, backup_manager, temp_backup_dir):
        """Test database restoration"""
        # Mock successful restore
        mock_subprocess.return_value = Mock(returncode=0, stderr="")
        
        # Create test backup file
        backup_file = Path(temp_backup_dir) / "test_restore.sql"
        backup_file.write_text("SELECT 1;")
        
        # Mock database URL
        backup_manager.db_url = "sqlite:///test.db"
        
        with patch('os.path.exists', return_value=True):
            success = backup_manager.restore_database_backup(str(backup_file))
        
        assert success
        mock_subprocess.assert_called_once()


class TestDisasterRecoveryManager:
    """Test disaster recovery functionality"""
    
    @pytest.fixture
    def dr_manager(self):
        """Create disaster recovery manager"""
        return DisasterRecoveryManager()
    
    def test_recovery_plan_creation(self, dr_manager):
        """Test disaster recovery plan creation"""
        plan = dr_manager.create_recovery_plan()
        
        assert 'recovery_procedures' in plan
        assert 'estimated_total_recovery_time' in plan
        assert 'rpo_target' in plan
        assert 'rto_target' in plan
        assert 'emergency_contacts' in plan
        
        # Check that procedures are properly structured
        procedures = plan['recovery_procedures']
        assert len(procedures) > 0
        
        for procedure in procedures:
            assert 'step' in procedure
            assert 'action' in procedure
            assert 'estimated_time' in procedure
            assert 'responsible' in procedure
    
    def test_disaster_recovery_test(self, dr_manager):
        """Test disaster recovery test procedure"""
        test_result = dr_manager.test_recovery_procedure()
        
        assert 'test_started_at' in test_result
        assert 'test_completed_at' in test_result
        assert 'steps_completed' in test_result
        assert 'total_time_seconds' in test_result
        assert 'success' in test_result
        
        # Should have completed some steps
        assert len(test_result['steps_completed']) > 0
    
    def test_recovery_test_with_backup(self, dr_manager, temp_backup_dir):
        """Test disaster recovery with specific backup"""
        # Create test backup
        backup_file = Path(temp_backup_dir) / "test_backup.sql.gz"
        backup_file.write_bytes(b"test backup content")
        
        # Create metadata
        metadata = {
            "backup_name": "test_backup",
            "checksum": "dummy_checksum",
            "created_at": datetime.utcnow().isoformat()
        }
        
        metadata_file = backup_file.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        test_result = dr_manager.test_recovery_procedure(str(backup_file))
        
        assert test_result['success']
        assert len(test_result['steps_completed']) > 0


class TestAutomatedBackupScheduler:
    """Test automated backup scheduling"""
    
    @pytest.fixture
    def scheduler(self):
        """Create automated backup scheduler"""
        return AutomatedBackupScheduler()
    
    def test_scheduler_initialization(self, scheduler):
        """Test scheduler initialization"""
        assert hasattr(scheduler, 'backup_manager')
        assert hasattr(scheduler, 'schedule_config')
        assert hasattr(scheduler, 'notification_config')
    
    @patch('utils.backup_manager.BackupManager.create_database_backup')
    def test_scheduled_backup_execution(self, mock_backup, scheduler):
        """Test scheduled backup execution"""
        # Mock successful backup
        mock_backup.return_value = {
            "backup_name": "test_backup",
            "backup_type": "hourly",
            "compressed_size": 1024 * 1024,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = scheduler.run_scheduled_backup("hourly")
        
        assert result['success']
        assert result['backup_type'] == "hourly"
        assert 'result' in result
        
        mock_backup.assert_called_once_with("hourly")
    
    def test_backup_scheduling_logic(self, scheduler):
        """Test backup scheduling decision logic"""
        # Test different times and conditions
        with patch('datetime.datetime') as mock_datetime:
            # Test hourly backup (should run at :00 and :30)
            mock_datetime.utcnow.return_value = datetime(2024, 1, 15, 14, 0, 0)  # 14:00
            assert scheduler.should_run_hourly_backup()
            
            mock_datetime.utcnow.return_value = datetime(2024, 1, 15, 14, 30, 0)  # 14:30
            assert scheduler.should_run_hourly_backup()
            
            mock_datetime.utcnow.return_value = datetime(2024, 1, 15, 14, 15, 0)  # 14:15
            assert not scheduler.should_run_hourly_backup()
            
            # Test daily backup (should run at 2 AM)
            mock_datetime.utcnow.return_value = datetime(2024, 1, 15, 2, 0, 0)
            assert scheduler.should_run_daily_backup()
            
            mock_datetime.utcnow.return_value = datetime(2024, 1, 15, 3, 0, 0)
            assert not scheduler.should_run_daily_backup()
    
    def test_backup_schedule_configuration(self, scheduler):
        """Test backup schedule configuration"""
        # Test default configuration
        assert scheduler.schedule_config['hourly_enabled']
        assert scheduler.schedule_config['daily_enabled']
        assert scheduler.schedule_config['weekly_enabled']
        assert scheduler.schedule_config['monthly_enabled']
        
        # Test configuration overrides
        with patch.dict(os.environ, {'BACKUP_HOURLY_ENABLED': 'false'}):
            new_scheduler = AutomatedBackupScheduler()
            assert not new_scheduler.schedule_config['hourly_enabled']
    
    @patch('utils.backup_manager.BackupManager.cleanup_old_backups')
    def test_scheduled_cleanup(self, mock_cleanup, scheduler):
        """Test scheduled cleanup execution"""
        mock_cleanup.return_value = {
            'hourly_cleaned': 5,
            'daily_cleaned': 2,
            'total_cleaned': 7
        }
        
        result = scheduler.run_scheduled_cleanup()
        
        assert result['success']
        assert 'cleanup_stats' in result
        assert result['cleanup_stats']['total_cleaned'] == 7
    
    @patch('utils.backup_manager.BackupManager.get_backup_status')
    @patch('utils.backup_manager.DisasterRecoveryManager.test_recovery_procedure')
    def test_health_check(self, mock_dr_test, mock_status, scheduler):
        """Test backup system health check"""
        # Mock healthy system
        mock_status.return_value = {
            'total_backups': 10,
            'latest_backup': {
                'created_at': datetime.utcnow().isoformat()
            }
        }
        
        mock_dr_test.return_value = {'success': True}
        
        result = scheduler.run_health_check()
        
        assert result['success']
        assert 'health_status' in result
        assert 'backup_status' in result
        assert 'disaster_recovery_test' in result
    
    @patch('utils.backup_manager.BackupManager.get_backup_status')
    def test_health_check_with_issues(self, mock_status, scheduler):
        """Test health check with system issues"""
        # Mock system with no backups
        mock_status.return_value = {
            'total_backups': 0,
            'latest_backup': None
        }
        
        result = scheduler.run_health_check()
        
        assert result['success']
        assert result['health_status'] in ['warning', 'critical']
        assert len(result['issues']) > 0
    
    def test_notification_configuration(self, scheduler):
        """Test notification system configuration"""
        config = scheduler.notification_config
        
        assert 'slack_webhook' in config
        assert 'email_enabled' in config
        assert 'email_recipients' in config
        assert 'notify_on_failure' in config
        
        # Test with environment variables
        with patch.dict(os.environ, {
            'BACKUP_SLACK_WEBHOOK': 'https://hooks.slack.com/test',
            'BACKUP_EMAIL_NOTIFICATIONS': 'true',
            'BACKUP_EMAIL_RECIPIENTS': 'admin@test.com,ops@test.com'
        }):
            new_scheduler = AutomatedBackupScheduler()
            new_config = new_scheduler.notification_config
            
            assert new_config['slack_webhook'] == 'https://hooks.slack.com/test'
            assert new_config['email_enabled']
            assert 'admin@test.com' in new_config['email_recipients']


class TestBackupIntegration:
    """Integration tests for backup system"""
    
    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory"""
        temp_dir = tempfile.mkdtemp(prefix="test_backup_integration_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_full_backup_restore_cycle(self, temp_backup_dir, db_session, sample_store):
        """Test complete backup and restore cycle"""
        backup_manager = BackupManager(backup_dir=temp_backup_dir)
        
        # Mock SQLite database for testing
        backup_manager.db_url = "sqlite:///test_backup_integration.db"
        
        with patch('subprocess.run') as mock_subprocess:
            with patch('os.path.exists', return_value=True):
                # Mock successful backup
                mock_subprocess.return_value = Mock(returncode=0, stderr="")
                
                # Create backup
                backup_result = backup_manager.create_database_backup("integration_test")
                
                assert backup_result['success'] is not False  # Backup should succeed or be mocked
                assert 'backup_name' in backup_result
                
                # List backups
                backups = backup_manager.list_backups()
                assert len(backups) >= 1
                
                # Verify backup
                if backups:
                    verification = backup_manager.verify_backup_integrity(backups[0]['local_path'])
                    assert verification['file_exists']
    
    def test_automated_scheduler_integration(self, temp_backup_dir):
        """Test automated scheduler with actual backup manager"""
        scheduler = AutomatedBackupScheduler()
        scheduler.backup_manager = BackupManager(backup_dir=temp_backup_dir)
        
        # Mock database URL
        scheduler.backup_manager.db_url = "sqlite:///test_scheduler.db"
        
        with patch('subprocess.run') as mock_subprocess:
            with patch('os.path.exists', return_value=True):
                mock_subprocess.return_value = Mock(returncode=0, stderr="")
                
                # Test forced backup
                result = scheduler.run_scheduled_backup("test")
                
                # Should handle the backup attempt
                assert 'success' in result
                assert 'backup_type' in result
    
    def test_disaster_recovery_integration(self, temp_backup_dir):
        """Test disaster recovery with backup manager"""
        backup_manager = BackupManager(backup_dir=temp_backup_dir)
        dr_manager = DisasterRecoveryManager(backup_manager)
        
        # Create test backup file
        test_backup = Path(temp_backup_dir) / "test_dr.sql.gz"
        test_backup.write_bytes(b"test backup content for DR")
        
        # Create metadata
        metadata = {
            "backup_name": "test_dr",
            "backup_type": "test",
            "checksum": backup_manager._calculate_checksum(test_backup),
            "created_at": datetime.utcnow().isoformat()
        }
        
        metadata_file = test_backup.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        # Test DR procedure
        dr_result = dr_manager.test_recovery_procedure(str(test_backup))
        
        assert 'success' in dr_result
        assert 'steps_completed' in dr_result
        assert len(dr_result['steps_completed']) > 0


class TestBackupSecurity:
    """Test backup security features"""
    
    def test_checksum_verification(self, temp_backup_dir):
        """Test that checksum verification detects corruption"""
        backup_manager = BackupManager(backup_dir=temp_backup_dir)
        
        # Create backup file
        backup_file = Path(temp_backup_dir) / "security_test.sql.gz"
        original_content = b"original backup content"
        backup_file.write_bytes(original_content)
        
        # Calculate checksum
        original_checksum = backup_manager._calculate_checksum(backup_file)
        
        # Create metadata with original checksum
        metadata = {
            "backup_name": "security_test",
            "checksum": original_checksum,
            "created_at": datetime.utcnow().isoformat()
        }
        
        metadata_file = backup_file.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        # Verify original file
        verification = backup_manager.verify_backup_integrity(str(backup_file))
        assert verification['checksum_valid']
        
        # Corrupt the file
        backup_file.write_bytes(b"corrupted content")
        
        # Verify corrupted file
        verification_corrupted = backup_manager.verify_backup_integrity(str(backup_file))
        assert not verification_corrupted['checksum_valid']
    
    def test_backup_file_permissions(self, temp_backup_dir):
        """Test that backup files have appropriate permissions"""
        backup_manager = BackupManager(backup_dir=temp_backup_dir)
        
        # Create test backup
        backup_file = Path(temp_backup_dir) / "permission_test.sql"
        backup_file.write_text("test content")
        
        # Check directory permissions
        dir_permissions = oct(backup_manager.backup_dir.stat().st_mode)[-3:]
        # Directory should be restrictive (owner access only recommended)
        assert dir_permissions in ['755', '750', '700']
    
    def test_sensitive_data_handling(self, temp_backup_dir, db_session, sample_store):
        """Test that sensitive data is handled properly in backups"""
        backup_manager = BackupManager(backup_dir=temp_backup_dir)
        
        # Test store configuration export (should not include sensitive tokens)
        store_configs = backup_manager._export_store_configurations()
        
        if store_configs:
            for config in store_configs:
                # Should not include access tokens or sensitive data
                assert 'access_token' not in config
                assert 'password' not in config
                # Should include non-sensitive configuration
                assert 'shop_domain' in config
                assert 'store_name' in config