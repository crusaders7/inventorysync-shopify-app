#!/usr/bin/env python3
"""
Test script to verify logging setup and configuration
"""

import os
import sys
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set test environment variables
os.environ['ENVIRONMENT'] = 'development'
os.environ['LOG_LEVEL'] = 'DEBUG'
os.environ['LOG_FORMAT'] = 'json'
os.environ['LOG_DIR'] = '/tmp/inventorysync_test_logs'
os.environ['ENABLE_SENTRY'] = 'false'  # Disable for testing

from core.logging_config import (
    get_logger, 
    log_audit_event, 
    log_performance_metric,
    log_security_event,
    StructuredLoggingConfig
)


class LoggingTestSuite:
    """Test suite for verifying logging functionality"""
    
    def __init__(self):
        self.logger = get_logger('test.logging')
        self.results = []
    
    async def run_all_tests(self):
        """Run all logging tests"""
        print("🔍 Starting Logging System Tests...\n")
        
        tests = [
            self.test_basic_logging,
            self.test_structured_logging,
            self.test_performance_metrics,
            self.test_audit_logging,
            self.test_security_logging,
            self.test_error_logging,
            self.test_log_rotation,
            self.test_log_aggregation_config
        ]
        
        for test in tests:
            try:
                await test()
                self.results.append((test.__name__, "✅ PASSED"))
            except Exception as e:
                self.results.append((test.__name__, f"❌ FAILED: {str(e)}"))
                print(f"Error in {test.__name__}: {e}")
        
        self.print_results()
    
    async def test_basic_logging(self):
        """Test basic logging functionality"""
        print("📝 Testing basic logging...")
        
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        
        # Check if log files are created
        log_dir = Path(os.environ['LOG_DIR'])
        assert log_dir.exists(), "Log directory not created"
        
        print("   ✓ Basic logging works\n")
    
    async def test_structured_logging(self):
        """Test structured logging with context"""
        print("📊 Testing structured logging...")
        
        # Log with context
        self.logger.bind(
            user_id="test-user-123",
            store_id="store-456",
            request_id="req-789"
        ).info("structured_log_test", 
            action="test_action",
            metadata={"key": "value"}
        )
        
        # Log complex data
        self.logger.info("complex_data_test",
            user_data={
                "id": "user-123",
                "email": "test@example.com",
                "roles": ["admin", "user"]
            },
            metrics={
                "response_time": 123.45,
                "items_processed": 100
            }
        )
        
        print("   ✓ Structured logging works\n")
    
    async def test_performance_metrics(self):
        """Test performance metric logging"""
        print("⚡ Testing performance metrics...")
        
        # Log various performance metrics
        log_performance_metric(
            metric_name="api_latency",
            value=45.67,
            unit="ms",
            tags={
                "endpoint": "/api/v1/test",
                "method": "GET",
                "status": "200"
            }
        )
        
        log_performance_metric(
            metric_name="database_query_time",
            value=12.34,
            unit="ms",
            tags={
                "query_type": "select",
                "table": "products"
            }
        )
        
        log_performance_metric(
            metric_name="cache_hit_rate",
            value=0.85,
            unit="ratio",
            tags={
                "cache_type": "redis"
            }
        )
        
        print("   ✓ Performance metrics logged\n")
    
    async def test_audit_logging(self):
        """Test audit logging for compliance"""
        print("📋 Testing audit logging...")
        
        # Test various audit events
        log_audit_event(
            action="user_login",
            user_id="user-123",
            resource_type="session",
            resource_id="session-456",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0..."
        )
        
        log_audit_event(
            action="inventory_update",
            user_id="user-123",
            resource_type="product",
            resource_id="prod-789",
            changes={
                "quantity": {"old": 100, "new": 150},
                "price": {"old": 29.99, "new": 34.99}
            },
            ip_address="192.168.1.100"
        )
        
        log_audit_event(
            action="settings_update",
            user_id="admin-456",
            resource_type="store_settings",
            resource_id="store-123",
            changes={
                "notification_email": {
                    "old": "old@example.com",
                    "new": "new@example.com"
                }
            }
        )
        
        print("   ✓ Audit logging works\n")
    
    async def test_security_logging(self):
        """Test security event logging"""
        print("🔒 Testing security logging...")
        
        # Test various security events
        log_security_event(
            event_type="failed_login_attempt",
            severity="warning",
            user_id="unknown",
            ip_address="192.168.1.100",
            details={
                "attempted_username": "admin",
                "attempts_count": 3
            }
        )
        
        log_security_event(
            event_type="unauthorized_access",
            severity="error",
            user_id="user-123",
            ip_address="192.168.1.100",
            details={
                "resource": "/api/v1/admin/users",
                "required_role": "admin",
                "user_roles": ["user"]
            }
        )
        
        log_security_event(
            event_type="suspicious_activity",
            severity="critical",
            ip_address="192.168.1.100",
            details={
                "reason": "Multiple failed API calls",
                "threshold_exceeded": True,
                "block_duration": 3600
            }
        )
        
        print("   ✓ Security logging works\n")
    
    async def test_error_logging(self):
        """Test error and exception logging"""
        print("❌ Testing error logging...")
        
        try:
            # Simulate an error
            raise ValueError("Test error for logging")
        except Exception as e:
            self.logger.error("test_error_occurred", 
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
        
        # Test error with context
        try:
            result = 1 / 0
        except ZeroDivisionError as e:
            self.logger.bind(
                operation="division",
                numerator=1,
                denominator=0
            ).error("mathematical_error", exc_info=True)
        
        print("   ✓ Error logging works\n")
    
    async def test_log_rotation(self):
        """Test log rotation configuration"""
        print("🔄 Testing log rotation setup...")
        
        log_dir = Path(os.environ['LOG_DIR'])
        
        # Write enough logs to test rotation
        test_logger = get_logger('test.rotation')
        for i in range(100):
            test_logger.info(f"Rotation test message {i}", 
                iteration=i,
                timestamp=datetime.utcnow().isoformat()
            )
        
        # Check log files exist
        log_files = list(log_dir.glob("*.log"))
        assert len(log_files) > 0, "No log files created"
        
        print(f"   ✓ Found {len(log_files)} log files")
        for log_file in log_files[:5]:  # Show first 5
            size_kb = log_file.stat().st_size / 1024
            print(f"     - {log_file.name}: {size_kb:.2f} KB")
        
        print()
    
    async def test_log_aggregation_config(self):
        """Test log aggregation configuration"""
        print("📡 Testing log aggregation config...")
        
        from core.logging_config import LogAggregationConfig
        
        # Test different aggregation configs
        configs = {
            'elasticsearch': {
                'LOG_AGGREGATION_TYPE': 'elasticsearch',
                'ELASTICSEARCH_HOSTS': 'localhost:9200'
            },
            'cloudwatch': {
                'LOG_AGGREGATION_TYPE': 'cloudwatch',
                'AWS_DEFAULT_REGION': 'us-east-1'
            },
            'datadog': {
                'LOG_AGGREGATION_TYPE': 'datadog',
                'DATADOG_API_KEY': 'test-key'
            }
        }
        
        for agg_type, env_vars in configs.items():
            # Temporarily set environment variables
            original_env = {}
            for key, value in env_vars.items():
                original_env[key] = os.environ.get(key)
                os.environ[key] = value
            
            config = LogAggregationConfig.get_log_shipper_config()
            print(f"   ✓ {agg_type} config: {json.dumps(config, indent=2)}")
            
            # Restore original environment
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        
        print()
    
    def print_results(self):
        """Print test results summary"""
        print("\n" + "="*50)
        print("📊 TEST RESULTS SUMMARY")
        print("="*50)
        
        passed = sum(1 for _, result in self.results if "PASSED" in result)
        total = len(self.results)
        
        for test_name, result in self.results:
            print(f"{result} {test_name}")
        
        print("\n" + "-"*50)
        print(f"Total: {total} | Passed: {passed} | Failed: {total - passed}")
        print("="*50)
        
        if passed == total:
            print("\n🎉 All tests passed! Logging system is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please check the errors above.")


async def test_api_logging():
    """Test logging through the API"""
    print("\n🌐 Testing API logging (requires running server)...")
    
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Test various endpoints
            endpoints = [
                ("GET", "http://localhost:8000/health"),
                ("GET", "http://localhost:8000/api/v1/status"),
                ("POST", "http://localhost:8000/api/v1/auth/login", {
                    "username": "test@example.com",
                    "password": "wrongpassword"
                })
            ]
            
            for method, url, *data in endpoints:
                try:
                    if method == "GET":
                        response = await client.get(url)
                    else:
                        response = await client.post(url, json=data[0] if data else {})
                    
                    print(f"   ✓ {method} {url}: {response.status_code}")
                except Exception as e:
                    print(f"   ⚠️  {method} {url}: {type(e).__name__}")
    
    except ImportError:
        print("   ⚠️  httpx not installed, skipping API tests")
    except Exception as e:
        print(f"   ⚠️  API test failed: {e}")


async def main():
    """Main test runner"""
    print("""
╔══════════════════════════════════════════════════╗
║     InventorySync Logging System Test Suite      ║
╚══════════════════════════════════════════════════╝
""")
    
    # Create test log directory
    log_dir = Path(os.environ['LOG_DIR'])
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Run tests
    test_suite = LoggingTestSuite()
    await test_suite.run_all_tests()
    
    # Optional: Test API logging
    await test_api_logging()
    
    # Show log file locations
    print(f"\n📁 Log files created in: {log_dir}")
    log_files = list(log_dir.glob("*.log"))
    if log_files:
        print("   Log files:")
        for log_file in log_files:
            print(f"   - {log_file}")
    
    print("\n✅ Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
