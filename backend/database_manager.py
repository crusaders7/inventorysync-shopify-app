"""
Database Management CLI
Production-ready database operations and management
"""

import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime

from database_setup import DatabaseSetup
from utils.logging import logger
from config import is_development, is_production


class DatabaseManager:
    """CLI interface for database management"""
    
    def __init__(self):
        self.db_setup = DatabaseSetup()
        self.logger = logger
    
    async def init_database(self, seed_data: bool = False):
        """Initialize database with schema and optional seed data"""
        try:
            self.logger.info("Initializing database...")
            
            await self.db_setup.setup_database(seed_data=seed_data)
            
            if seed_data:
                self.logger.info("Database initialized with development data")
            else:
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    async def health_check(self):
        """Run comprehensive database health check"""
        try:
            self.logger.info("Running database health check...")
            
            health = await self.db_setup.check_database_health()
            
            print("\n=== Database Health Check ===")
            print(f"Timestamp: {health['timestamp']}")
            print(f"Database Accessible: {'✓' if health['database_accessible'] else '✗'}")
            print(f"Tables Exist: {'✓' if health['tables_exist'] else '✗'}")
            print(f"Sample Query: {'✓' if health['sample_query'] else '✗'}")
            print(f"Connection Pool: {'✓' if health['connection_pool'] else '✗'}")
            
            if 'store_count' in health:
                print(f"Store Count: {health['store_count']}")
            
            if 'error' in health:
                print(f"Error: {health['error']}")
            
            overall_health = all([
                health['database_accessible'],
                health['tables_exist'],
                health['sample_query'],
                health['connection_pool']
            ])
            
            print(f"\nOverall Status: {'✓ HEALTHY' if overall_health else '✗ UNHEALTHY'}")
            
            return overall_health
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            print(f"Health check failed: {e}")
            return False
    
    async def reset_database(self):
        """Reset database (development only)"""
        if not is_development():
            print("❌ Database reset is only allowed in development environment")
            return False
        
        try:
            print("⚠️  WARNING: This will delete ALL data in the database!")
            confirm = input("Are you sure you want to continue? (yes/no): ")
            
            if confirm.lower() != 'yes':
                print("Operation cancelled")
                return False
            
            self.logger.warning("Resetting database...")
            await self.db_setup.reset_database()
            
            print("✓ Database reset completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Database reset failed: {e}")
            print(f"❌ Database reset failed: {e}")
            return False
    
    async def seed_data(self):
        """Seed database with development data"""
        if not is_development():
            print("❌ Data seeding is only allowed in development environment")
            return False
        
        try:
            self.logger.info("Seeding development data...")
            await self.db_setup.seed_development_data()
            
            print("✓ Development data seeded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Data seeding failed: {e}")
            print(f"❌ Data seeding failed: {e}")
            return False
    
    async def backup_database(self, backup_path: str = None):
        """Create database backup (SQLite only for now)"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_inventorysync_{timestamp}.db"
            
            # For SQLite databases
            import shutil
            from config import get_database_url
            
            db_url = get_database_url()
            if "sqlite" not in db_url:
                print("❌ Backup is currently only supported for SQLite databases")
                return False
            
            # Extract the database file path
            db_file = db_url.replace("sqlite:///", "")
            
            if not Path(db_file).exists():
                print(f"❌ Database file not found: {db_file}")
                return False
            
            shutil.copy2(db_file, backup_path)
            print(f"✓ Database backed up to: {backup_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Database backup failed: {e}")
            print(f"❌ Database backup failed: {e}")
            return False
    
    def print_environment_info(self):
        """Print current environment information"""
        from config import settings
        
        print("\n=== Environment Information ===")
        print(f"Environment: {'Development' if is_development() else 'Production' if is_production() else 'Unknown'}")
        print(f"Debug Mode: {settings.debug}")
        print(f"Database URL: {settings.database_url}")
        print(f"App Version: {settings.app_version}")
        
        if is_development():
            print("⚠️  Development mode - All operations allowed")
        elif is_production():
            print("🔒 Production mode - Limited operations")
        
        print()


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="InventorySync Database Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python database_manager.py --init                    # Initialize database
  python database_manager.py --init --seed            # Initialize with sample data
  python database_manager.py --health                 # Health check
  python database_manager.py --reset                  # Reset database (dev only)
  python database_manager.py --backup backup.db       # Backup database
        """
    )
    
    parser.add_argument("--init", action="store_true", 
                       help="Initialize database schema")
    parser.add_argument("--seed", action="store_true",
                       help="Seed database with development data")
    parser.add_argument("--health", action="store_true",
                       help="Run database health check")
    parser.add_argument("--reset", action="store_true",
                       help="Reset database (development only)")
    parser.add_argument("--backup", type=str, nargs='?', const=True,
                       help="Backup database to specified file")
    parser.add_argument("--info", action="store_true",
                       help="Show environment information")
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    db_manager = DatabaseManager()
    
    try:
        if args.info:
            db_manager.print_environment_info()
        
        if args.init:
            await db_manager.init_database(seed_data=args.seed)
        elif args.seed:
            await db_manager.seed_data()
        
        if args.health:
            await db_manager.health_check()
        
        if args.reset:
            await db_manager.reset_database()
        
        if args.backup:
            backup_file = args.backup if isinstance(args.backup, str) else None
            await db_manager.backup_database(backup_file)
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Database manager failed: {e}")
        print(f"❌ Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())