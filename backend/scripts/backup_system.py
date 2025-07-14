#!/usr/bin/env python3
"""
Backup System CLI Tool
Command-line interface for backup and disaster recovery operations
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.backup_manager import BackupManager, DisasterRecoveryManager
from utils.logging import logger


def create_backup(args):
    """Create database and/or application backup"""
    backup_manager = BackupManager(args.backup_dir)
    
    results = []
    
    try:
        if args.type in ['database', 'all']:
            logger.info("Creating database backup...")
            db_backup = backup_manager.create_database_backup(args.backup_type)
            results.append(db_backup)
            print(f"✅ Database backup created: {db_backup['backup_name']}")
            print(f"   Size: {db_backup['compressed_size'] / (1024*1024):.1f} MB")
            print(f"   Compression: {db_backup['compression_ratio']:.1f}x")
        
        if args.type in ['application', 'all']:
            logger.info("Creating application backup...")
            app_backup = backup_manager.create_application_backup()
            results.append(app_backup)
            print(f"✅ Application backup created: {app_backup['backup_name']}")
            print(f"   Size: {app_backup['size'] / (1024*1024):.1f} MB")
        
        # Save backup report
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Backup report saved to: {args.output}")
        
        return True
        
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        print(f"❌ Backup failed: {e}")
        return False


def list_backups(args):
    """List available backups"""
    backup_manager = BackupManager(args.backup_dir)
    
    try:
        backups = backup_manager.list_backups(args.backup_type)
        
        if not backups:
            print("📦 No backups found")
            return True
        
        print(f"\n📦 Available Backups ({len(backups)} found)")
        print("=" * 80)
        
        for backup in backups:
            backup_time = datetime.fromisoformat(backup['created_at'])
            size_mb = backup.get('compressed_size', backup.get('size', 0)) / (1024 * 1024)
            
            print(f"🗂️  {backup['backup_name']}")
            print(f"   Type: {backup['backup_type']}")
            print(f"   Created: {backup_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"   Size: {size_mb:.1f} MB")
            print(f"   File: {backup.get('local_path', 'N/A')}")
            
            if 'checksum' in backup:
                print(f"   Checksum: {backup['checksum'][:16]}...")
            
            print()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        print(f"❌ Failed to list backups: {e}")
        return False


def restore_backup(args):
    """Restore from backup"""
    backup_manager = BackupManager(args.backup_dir)
    
    if not args.backup_path:
        # List available backups for selection
        backups = backup_manager.list_backups()
        if not backups:
            print("❌ No backups available for restore")
            return False
        
        print("\n📦 Available backups:")
        for i, backup in enumerate(backups[:10]):  # Show latest 10
            backup_time = datetime.fromisoformat(backup['created_at'])
            print(f"  {i+1}. {backup['backup_name']} ({backup_time.strftime('%Y-%m-%d %H:%M')})")
        
        try:
            choice = int(input("\nSelect backup number to restore: ")) - 1
            if 0 <= choice < len(backups):
                args.backup_path = backups[choice]['local_path']
            else:
                print("❌ Invalid selection")
                return False
        except (ValueError, KeyboardInterrupt):
            print("❌ Restore cancelled")
            return False
    
    # Confirm restore operation
    if not args.force:
        print(f"\n⚠️  WARNING: This will restore the database from:")
        print(f"   {args.backup_path}")
        print(f"\n   This operation will OVERWRITE the current database!")
        
        confirm = input("\nType 'YES' to confirm restore: ")
        if confirm != 'YES':
            print("❌ Restore cancelled")
            return False
    
    try:
        logger.info(f"Starting restore from: {args.backup_path}")
        print(f"🔄 Restoring database from: {args.backup_path}")
        
        success = backup_manager.restore_database_backup(
            args.backup_path, 
            verify_checksum=not args.skip_checksum
        )
        
        if success:
            print("✅ Database restore completed successfully")
            print("🔍 Please verify application functionality")
        else:
            print("❌ Database restore failed")
        
        return success
        
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        print(f"❌ Restore failed: {e}")
        return False


def verify_backup(args):
    """Verify backup integrity"""
    backup_manager = BackupManager(args.backup_dir)
    
    try:
        if args.backup_path:
            backups_to_verify = [args.backup_path]
        else:
            # Verify all backups
            backups = backup_manager.list_backups()
            backups_to_verify = [b['local_path'] for b in backups]
        
        if not backups_to_verify:
            print("📦 No backups to verify")
            return True
        
        print(f"\n🔍 Verifying {len(backups_to_verify)} backup(s)")
        print("=" * 60)
        
        all_valid = True
        
        for backup_path in backups_to_verify:
            print(f"\n📄 Verifying: {Path(backup_path).name}")
            
            verification = backup_manager.verify_backup_integrity(backup_path)
            
            # File existence
            if verification['file_exists']:
                print("   ✅ File exists")
            else:
                print("   ❌ File missing")
                all_valid = False
                continue
            
            # Metadata
            if verification['metadata_exists']:
                print("   ✅ Metadata available")
            else:
                print("   ⚠️  No metadata file")
            
            # Checksum
            if verification['checksum_valid']:
                print("   ✅ Checksum valid")
            else:
                print("   ❌ Checksum invalid" if verification['metadata_exists'] else "   ⚠️  No checksum to verify")
                if verification['metadata_exists']:
                    all_valid = False
            
            # Readability
            if verification['readable']:
                print("   ✅ File readable")
            else:
                print("   ❌ File corrupted or unreadable")
                all_valid = False
            
            # Restore time estimate
            if verification['estimated_restore_time']:
                print(f"   📊 Estimated restore time: {verification['estimated_restore_time']}")
        
        print(f"\n📊 Verification Summary:")
        print(f"   Status: {'✅ All backups valid' if all_valid else '❌ Some backups have issues'}")
        
        return all_valid
        
    except Exception as e:
        logger.error(f"Backup verification failed: {e}")
        print(f"❌ Verification failed: {e}")
        return False


def cleanup_backups(args):
    """Clean up old backups based on retention policy"""
    backup_manager = BackupManager(args.backup_dir)
    
    try:
        print("🧹 Starting backup cleanup...")
        
        if not args.force:
            status = backup_manager.get_backup_status()
            print(f"\nCurrent backup status:")
            print(f"   Total backups: {status['total_backups']}")
            print(f"   Total size: {status['total_size_mb']} MB")
            print(f"   Backup types: {status['backup_types']}")
            
            confirm = input("\nProceed with cleanup? [y/N]: ")
            if confirm.lower() != 'y':
                print("❌ Cleanup cancelled")
                return False
        
        cleanup_stats = backup_manager.cleanup_old_backups()
        
        print(f"\n✅ Cleanup completed:")
        print(f"   Hourly backups cleaned: {cleanup_stats['hourly_cleaned']}")
        print(f"   Daily backups cleaned: {cleanup_stats['daily_cleaned']}")
        print(f"   Weekly backups cleaned: {cleanup_stats['weekly_cleaned']}")
        print(f"   Monthly backups cleaned: {cleanup_stats['monthly_cleaned']}")
        print(f"   Total backups removed: {cleanup_stats['total_cleaned']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")
        print(f"❌ Cleanup failed: {e}")
        return False


def show_status(args):
    """Show backup system status"""
    backup_manager = BackupManager(args.backup_dir)
    
    try:
        status = backup_manager.get_backup_status()
        
        print(f"\n📊 Backup System Status")
        print("=" * 40)
        print(f"Backup Directory: {status['backup_directory']}")
        print(f"Total Backups: {status['total_backups']}")
        print(f"Total Size: {status['total_size_mb']} MB")
        print(f"S3 Configured: {'✅ Yes' if status['s3_configured'] else '❌ No'}")
        
        print(f"\n📈 Backup Types:")
        for backup_type, count in status['backup_types'].items():
            print(f"   {backup_type}: {count}")
        
        if status['latest_backup']:
            latest = status['latest_backup']
            latest_time = datetime.fromisoformat(latest['created_at'])
            print(f"\n🕐 Latest Backup:")
            print(f"   Name: {latest['backup_name']}")
            print(f"   Type: {latest['backup_type']}")
            print(f"   Created: {latest_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        if status['oldest_backup']:
            oldest = status['oldest_backup']
            oldest_time = datetime.fromisoformat(oldest['created_at'])
            print(f"\n🕐 Oldest Backup:")
            print(f"   Name: {oldest['backup_name']}")
            print(f"   Created: {oldest_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        print(f"❌ Failed to get status: {e}")
        return False


def test_disaster_recovery(args):
    """Test disaster recovery procedures"""
    disaster_recovery = DisasterRecoveryManager()
    
    try:
        print("🧪 Starting disaster recovery test...")
        
        test_result = disaster_recovery.test_recovery_procedure(args.backup_path)
        
        print(f"\n📊 Disaster Recovery Test Results")
        print("=" * 50)
        print(f"Test Duration: {test_result['total_time_seconds']:.1f} seconds")
        print(f"Overall Status: {'✅ Success' if test_result['success'] else '❌ Failed'}")
        
        print(f"\n✅ Completed Steps:")
        for step in test_result['steps_completed']:
            print(f"   • {step['step']}: {step['duration_seconds']:.1f}s ({step['status']})")
        
        if test_result['steps_failed']:
            print(f"\n❌ Failed Steps:")
            for step in test_result['steps_failed']:
                print(f"   • {step['step']}: {step['error']}")
        
        # Show recovery plan
        if args.show_plan:
            plan = disaster_recovery.create_recovery_plan()
            print(f"\n📋 Disaster Recovery Plan")
            print("=" * 40)
            print(f"RTO Target: {plan['rto_target']}")
            print(f"RPO Target: {plan['rpo_target']}")
            print(f"Estimated Total Time: {plan['estimated_total_recovery_time']}")
            
            print(f"\n🔧 Recovery Procedures:")
            for procedure in plan['recovery_procedures']:
                print(f"   {procedure['step']}. {procedure['action']}")
                print(f"      Time: {procedure['estimated_time']}")
                print(f"      Owner: {procedure['responsible']}")
                print()
        
        return test_result['success']
        
    except Exception as e:
        logger.error(f"Disaster recovery test failed: {e}")
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="InventorySync Backup and Disaster Recovery Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create database backup
  python backup_system.py create --type database --backup-type daily
  
  # Create full backup (database + application)
  python backup_system.py create --type all --backup-type weekly
  
  # List all backups
  python backup_system.py list
  
  # Verify backup integrity
  python backup_system.py verify --backup-path /path/to/backup.sql.gz
  
  # Restore from backup (interactive)
  python backup_system.py restore
  
  # Clean up old backups
  python backup_system.py cleanup
  
  # Show backup system status
  python backup_system.py status
  
  # Test disaster recovery
  python backup_system.py test-dr --show-plan
        """
    )
    
    parser.add_argument('--backup-dir', default='/var/backups/inventorysync',
                       help='Backup directory path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create backup command
    create_parser = subparsers.add_parser('create', help='Create backup')
    create_parser.add_argument('--type', choices=['database', 'application', 'all'], 
                              default='database', help='Backup type')
    create_parser.add_argument('--backup-type', default='manual',
                              help='Backup category (manual, hourly, daily, weekly, monthly)')
    create_parser.add_argument('--output', help='Save backup report to file')
    
    # List backups command
    list_parser = subparsers.add_parser('list', help='List available backups')
    list_parser.add_argument('--backup-type', help='Filter by backup type')
    
    # Restore backup command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('--backup-path', help='Path to backup file')
    restore_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    restore_parser.add_argument('--skip-checksum', action='store_true', help='Skip checksum verification')
    
    # Verify backup command
    verify_parser = subparsers.add_parser('verify', help='Verify backup integrity')
    verify_parser.add_argument('--backup-path', help='Specific backup to verify (default: all)')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old backups')
    cleanup_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show backup system status')
    
    # Test disaster recovery command
    test_parser = subparsers.add_parser('test-dr', help='Test disaster recovery procedures')
    test_parser.add_argument('--backup-path', help='Backup to use for testing')
    test_parser.add_argument('--show-plan', action='store_true', help='Show recovery plan')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Ensure backup directory exists
    Path(args.backup_dir).mkdir(parents=True, exist_ok=True)
    
    # Route to appropriate function
    success = False
    if args.command == 'create':
        success = create_backup(args)
    elif args.command == 'list':
        success = list_backups(args)
    elif args.command == 'restore':
        success = restore_backup(args)
    elif args.command == 'verify':
        success = verify_backup(args)
    elif args.command == 'cleanup':
        success = cleanup_backups(args)
    elif args.command == 'status':
        success = show_status(args)
    elif args.command == 'test-dr':
        success = test_disaster_recovery(args)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())