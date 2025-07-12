#!/usr/bin/env python3
"""
Automated Backup Script
Runs scheduled backups and maintenance tasks
Designed to be run via cron or task scheduler
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.backup_manager import BackupManager, DisasterRecoveryManager
from utils.logging import logger


class AutomatedBackupScheduler:
    """Handles automated backup scheduling and execution"""
    
    def __init__(self):
        self.backup_manager = BackupManager()
        self.disaster_recovery = DisasterRecoveryManager(self.backup_manager)
        
        # Backup schedule configuration
        self.schedule_config = {
            'hourly_enabled': os.getenv('BACKUP_HOURLY_ENABLED', 'true').lower() == 'true',
            'daily_enabled': os.getenv('BACKUP_DAILY_ENABLED', 'true').lower() == 'true',
            'weekly_enabled': os.getenv('BACKUP_WEEKLY_ENABLED', 'true').lower() == 'true',
            'monthly_enabled': os.getenv('BACKUP_MONTHLY_ENABLED', 'true').lower() == 'true',
            
            # Backup windows (UTC hours)
            'hourly_minutes': [0, 30],  # Every 30 minutes
            'daily_hour': 2,    # 2 AM UTC
            'weekly_day': 0,    # Sunday (0 = Monday, 6 = Sunday)
            'monthly_day': 1,   # 1st of month
            
            # Cleanup settings
            'auto_cleanup_enabled': os.getenv('BACKUP_AUTO_CLEANUP', 'true').lower() == 'true',
            'cleanup_hour': 3,  # 3 AM UTC
            
            # Health check settings
            'health_check_enabled': os.getenv('BACKUP_HEALTH_CHECK', 'true').lower() == 'true',
            'health_check_days': [1, 15],  # Check on 1st and 15th of month
        }
        
        # Notification settings
        self.notification_config = {
            'slack_webhook': os.getenv('BACKUP_SLACK_WEBHOOK'),
            'email_enabled': os.getenv('BACKUP_EMAIL_NOTIFICATIONS', 'false').lower() == 'true',
            'email_recipients': os.getenv('BACKUP_EMAIL_RECIPIENTS', '').split(','),
            'notify_on_success': os.getenv('BACKUP_NOTIFY_SUCCESS', 'false').lower() == 'true',
            'notify_on_failure': True,
        }
    
    def should_run_hourly_backup(self) -> bool:
        """Check if hourly backup should run"""
        if not self.schedule_config['hourly_enabled']:
            return False
        
        now = datetime.utcnow()
        return now.minute in self.schedule_config['hourly_minutes']
    
    def should_run_daily_backup(self) -> bool:
        """Check if daily backup should run"""
        if not self.schedule_config['daily_enabled']:
            return False
        
        now = datetime.utcnow()
        return now.hour == self.schedule_config['daily_hour'] and now.minute == 0
    
    def should_run_weekly_backup(self) -> bool:
        """Check if weekly backup should run"""
        if not self.schedule_config['weekly_enabled']:
            return False
        
        now = datetime.utcnow()
        return (now.weekday() == self.schedule_config['weekly_day'] and 
                now.hour == self.schedule_config['daily_hour'] and 
                now.minute == 0)
    
    def should_run_monthly_backup(self) -> bool:
        """Check if monthly backup should run"""
        if not self.schedule_config['monthly_enabled']:
            return False
        
        now = datetime.utcnow()
        return (now.day == self.schedule_config['monthly_day'] and 
                now.hour == self.schedule_config['daily_hour'] and 
                now.minute == 0)
    
    def should_run_cleanup(self) -> bool:
        """Check if cleanup should run"""
        if not self.schedule_config['auto_cleanup_enabled']:
            return False
        
        now = datetime.utcnow()
        return now.hour == self.schedule_config['cleanup_hour'] and now.minute == 0
    
    def should_run_health_check(self) -> bool:
        """Check if health check should run"""
        if not self.schedule_config['health_check_enabled']:
            return False
        
        now = datetime.utcnow()
        return (now.day in self.schedule_config['health_check_days'] and 
                now.hour == self.schedule_config['cleanup_hour'] and 
                now.minute == 30)  # 30 minutes after cleanup
    
    def run_scheduled_backup(self, backup_type: str) -> dict:
        """Run a scheduled backup"""
        logger.info(f"Starting {backup_type} backup")
        
        try:
            # Create database backup
            backup_result = self.backup_manager.create_database_backup(backup_type)
            
            # For weekly and monthly backups, also backup application config
            if backup_type in ['weekly', 'monthly']:
                app_backup = self.backup_manager.create_application_backup()
                backup_result['application_backup'] = app_backup
            
            logger.info(f"{backup_type} backup completed successfully")
            
            # Send success notification if configured
            if self.notification_config['notify_on_success']:
                self._send_notification(
                    f"✅ {backup_type.title()} backup completed successfully",
                    backup_result,
                    is_error=False
                )
            
            return {
                'success': True,
                'backup_type': backup_type,
                'result': backup_result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_msg = f"{backup_type} backup failed: {str(e)}"
            logger.error(error_msg)
            
            # Send failure notification
            self._send_notification(
                f"❌ {backup_type.title()} backup failed",
                {'error': str(e), 'backup_type': backup_type},
                is_error=True
            )
            
            return {
                'success': False,
                'backup_type': backup_type,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def run_scheduled_cleanup(self) -> dict:
        """Run scheduled backup cleanup"""
        logger.info("Starting scheduled backup cleanup")
        
        try:
            cleanup_stats = self.backup_manager.cleanup_old_backups()
            
            logger.info(f"Cleanup completed: {cleanup_stats['total_cleaned']} backups removed")
            
            return {
                'success': True,
                'cleanup_stats': cleanup_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Backup cleanup failed: {str(e)}"
            logger.error(error_msg)
            
            self._send_notification(
                "❌ Backup cleanup failed",
                {'error': str(e)},
                is_error=True
            )
            
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def run_health_check(self) -> dict:
        """Run backup system health check"""
        logger.info("Starting backup system health check")
        
        try:
            # Get backup status
            status = self.backup_manager.get_backup_status()
            
            # Check for recent backups
            health_issues = []
            
            if status['total_backups'] == 0:
                health_issues.append("No backups found")
            elif status['latest_backup']:
                latest_time = datetime.fromisoformat(status['latest_backup']['created_at'])
                age_hours = (datetime.utcnow() - latest_time).total_seconds() / 3600
                
                if age_hours > 48:  # No backup in 48 hours
                    health_issues.append(f"Latest backup is {age_hours:.1f} hours old")
            
            # Check backup integrity for recent backups
            recent_backups = [b for b in self.backup_manager.list_backups() 
                            if (datetime.utcnow() - datetime.fromisoformat(b['created_at'])).days <= 7]
            
            integrity_issues = 0
            for backup in recent_backups[:5]:  # Check latest 5 backups
                verification = self.backup_manager.verify_backup_integrity(backup['local_path'])
                if not verification['checksum_valid'] or not verification['readable']:
                    integrity_issues += 1
            
            if integrity_issues > 0:
                health_issues.append(f"{integrity_issues} backup(s) failed integrity check")
            
            # Test disaster recovery procedure
            dr_test_result = self.disaster_recovery.test_recovery_procedure()
            if not dr_test_result['success']:
                health_issues.append("Disaster recovery test failed")
            
            # Determine overall health
            health_status = 'healthy' if not health_issues else 'warning'
            if len(health_issues) > 2:
                health_status = 'critical'
            
            health_report = {
                'success': True,
                'health_status': health_status,
                'issues': health_issues,
                'backup_status': status,
                'disaster_recovery_test': dr_test_result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send notification if there are issues
            if health_issues:
                self._send_notification(
                    f"⚠️ Backup System Health Check - {health_status.upper()}",
                    health_report,
                    is_error=(health_status == 'critical')
                )
            
            logger.info(f"Health check completed: {health_status}")
            return health_report
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            
            self._send_notification(
                "❌ Backup system health check failed",
                {'error': str(e)},
                is_error=True
            )
            
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _send_notification(self, message: str, details: dict, is_error: bool = False):
        """Send notification via configured channels"""
        try:
            # Slack notification
            if self.notification_config['slack_webhook']:
                self._send_slack_notification(message, details, is_error)
            
            # Email notification
            if self.notification_config['email_enabled'] and self.notification_config['email_recipients']:
                self._send_email_notification(message, details, is_error)
                
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
    
    def _send_slack_notification(self, message: str, details: dict, is_error: bool):
        """Send Slack notification"""
        import requests
        
        color = "danger" if is_error else "good"
        
        payload = {
            "text": f"InventorySync Backup System",
            "attachments": [
                {
                    "color": color,
                    "title": message,
                    "fields": [
                        {
                            "title": "Timestamp",
                            "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": True
                        },
                        {
                            "title": "Environment",
                            "value": os.getenv('ENVIRONMENT', 'unknown'),
                            "short": True
                        }
                    ]
                }
            ]
        }
        
        # Add relevant details
        if 'backup_type' in details:
            payload["attachments"][0]["fields"].append({
                "title": "Backup Type",
                "value": details['backup_type'],
                "short": True
            })
        
        if 'error' in details:
            payload["attachments"][0]["fields"].append({
                "title": "Error",
                "value": details['error'][:200] + "..." if len(details['error']) > 200 else details['error'],
                "short": False
            })
        
        response = requests.post(
            self.notification_config['slack_webhook'],
            json=payload,
            timeout=10
        )
        response.raise_for_status()
    
    def _send_email_notification(self, message: str, details: dict, is_error: bool):
        """Send email notification"""
        # This would integrate with your email service
        # For now, just log the notification
        logger.info(f"Email notification: {message}")
    
    def run_all_scheduled_tasks(self) -> dict:
        """Run all scheduled tasks that should execute now"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'tasks_run': [],
            'total_success': 0,
            'total_failed': 0
        }
        
        # Check and run backup tasks
        if self.should_run_monthly_backup():
            result = self.run_scheduled_backup('monthly')
            results['tasks_run'].append(result)
            if result['success']:
                results['total_success'] += 1
            else:
                results['total_failed'] += 1
        
        elif self.should_run_weekly_backup():
            result = self.run_scheduled_backup('weekly')
            results['tasks_run'].append(result)
            if result['success']:
                results['total_success'] += 1
            else:
                results['total_failed'] += 1
        
        elif self.should_run_daily_backup():
            result = self.run_scheduled_backup('daily')
            results['tasks_run'].append(result)
            if result['success']:
                results['total_success'] += 1
            else:
                results['total_failed'] += 1
        
        elif self.should_run_hourly_backup():
            result = self.run_scheduled_backup('hourly')
            results['tasks_run'].append(result)
            if result['success']:
                results['total_success'] += 1
            else:
                results['total_failed'] += 1
        
        # Check and run cleanup
        if self.should_run_cleanup():
            result = self.run_scheduled_cleanup()
            results['tasks_run'].append(result)
            if result['success']:
                results['total_success'] += 1
            else:
                results['total_failed'] += 1
        
        # Check and run health check
        if self.should_run_health_check():
            result = self.run_health_check()
            results['tasks_run'].append(result)
            if result['success']:
                results['total_success'] += 1
            else:
                results['total_failed'] += 1
        
        return results


def main():
    """Main entry point for automated backup script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated backup and maintenance')
    parser.add_argument('--force-backup', choices=['hourly', 'daily', 'weekly', 'monthly'],
                       help='Force a specific backup type')
    parser.add_argument('--force-cleanup', action='store_true',
                       help='Force backup cleanup')
    parser.add_argument('--force-health-check', action='store_true',
                       help='Force health check')
    parser.add_argument('--output', help='Save results to JSON file')
    
    args = parser.parse_args()
    
    scheduler = AutomatedBackupScheduler()
    
    try:
        if args.force_backup:
            # Force specific backup
            result = scheduler.run_scheduled_backup(args.force_backup)
            
        elif args.force_cleanup:
            # Force cleanup
            result = scheduler.run_scheduled_cleanup()
            
        elif args.force_health_check:
            # Force health check
            result = scheduler.run_health_check()
            
        else:
            # Run scheduled tasks
            result = scheduler.run_all_scheduled_tasks()
        
        # Save results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
        
        # Exit with appropriate code
        if isinstance(result, dict):
            if 'total_failed' in result:
                return 1 if result['total_failed'] > 0 else 0
            else:
                return 0 if result.get('success', True) else 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Automated backup script failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())