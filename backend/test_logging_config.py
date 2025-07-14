#!/usr/bin/env python3
"""
Test script to verify logging configuration works with and without optional dependencies
"""

import sys
import os
import subprocess
import tempfile
import shutil

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_logging_without_dependencies():
    """Test logging without optional dependencies"""
    print("\n=== Testing logging WITHOUT optional dependencies ===")
    
    # Create a test script that imports our logging module
    test_script = """
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure optional dependencies are not available
sys.modules['pythonjsonlogger'] = None
sys.modules['structlog'] = None
sys.modules['sentry_sdk'] = None

from app.core.logging import LoggingConfig, get_logger, log_performance_metric, log_audit_event, log_security_event

# Test basic logging
logger = get_logger('test.basic')
logger.info("Test info message")
logger.warning("Test warning message")
logger.error("Test error message")

# Test performance metric logging
log_performance_metric('test_metric', 123.45, 'ms', {'tag': 'test'})

# Test audit logging
log_audit_event(
    action='test_action',
    user_id='test_user',
    resource_type='test_resource',
    resource_id='12345',
    changes={'field': 'value'},
    ip_address='127.0.0.1'
)

# Test security logging
log_security_event(
    event_type='test_security_event',
    severity='warning',
    user_id='test_user',
    ip_address='127.0.0.1',
    details={'test': 'data'}
)

print("All logging tests passed without optional dependencies!")
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        temp_file = f.name
    
    try:
        # Run the test script
        result = subprocess.run([sys.executable, temp_file], capture_output=True, text=True)
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
        
        if result.returncode == 0:
            print("✓ Logging works without optional dependencies")
        else:
            print("✗ Logging failed without optional dependencies")
    finally:
        os.unlink(temp_file)


def test_logging_with_dependencies():
    """Test logging with optional dependencies installed"""
    print("\n=== Testing logging WITH optional dependencies ===")
    
    # First check if dependencies are available
    deps_available = []
    try:
        import pythonjsonlogger
        deps_available.append("python-json-logger")
    except ImportError:
        pass
    
    try:
        import structlog
        deps_available.append("structlog")
    except ImportError:
        pass
    
    try:
        import sentry_sdk
        deps_available.append("sentry-sdk")
    except ImportError:
        pass
    
    print(f"Available dependencies: {deps_available if deps_available else 'None'}")
    
    # Test with actual imports
    from app.core.logging import LoggingConfig, get_logger, log_performance_metric, log_audit_event, log_security_event
    
    # Test basic logging
    logger = get_logger('test.with_deps')
    logger.info("Test info message with dependencies")
    logger.warning("Test warning message with dependencies")
    logger.error("Test error message with dependencies")
    
    # Test performance metric logging
    log_performance_metric('test_metric_deps', 456.78, 'ms', {'tag': 'test_deps'})
    
    # Test audit logging
    log_audit_event(
        action='test_action_deps',
        user_id='test_user_deps',
        resource_type='test_resource_deps',
        resource_id='67890',
        changes={'field': 'value_deps'},
        ip_address='192.168.1.1'
    )
    
    # Test security logging
    log_security_event(
        event_type='test_security_event_deps',
        severity='error',
        user_id='test_user_deps',
        ip_address='192.168.1.1',
        details={'test': 'data_deps'}
    )
    
    print("✓ Logging works with available dependencies")


def test_log_file_creation():
    """Test that log files are created properly"""
    print("\n=== Testing log file creation ===")
    
    # Set a specific log directory for testing
    test_log_dir = tempfile.mkdtemp(prefix='test_logs_')
    os.environ['LOG_DIR'] = test_log_dir
    
    try:
        # Re-import to use new log directory
        import importlib
        import app.core.logging as logging_module
        importlib.reload(logging_module)
        
        logger = logging_module.get_logger('test.files')
        logger.info("Test log file creation")
        logger.error("Test error log file creation")
        
        # Check if log files were created
        log_files = os.listdir(test_log_dir)
        print(f"Created log files: {log_files}")
        
        if 'app.log' in log_files:
            print("✓ Application log file created")
        else:
            print("✗ Application log file not created")
        
        if 'error.log' in log_files:
            print("✓ Error log file created")
        else:
            print("✗ Error log file not created")
            
    finally:
        # Clean up
        shutil.rmtree(test_log_dir, ignore_errors=True)
        # Reset environment
        if 'LOG_DIR' in os.environ:
            del os.environ['LOG_DIR']


def test_environment_configuration():
    """Test different environment configurations"""
    print("\n=== Testing environment configurations ===")
    
    configs = [
        {'ENVIRONMENT': 'development', 'LOG_LEVEL': 'DEBUG', 'LOG_FORMAT': 'console'},
        {'ENVIRONMENT': 'production', 'LOG_LEVEL': 'INFO', 'LOG_FORMAT': 'json'},
        {'ENVIRONMENT': 'staging', 'LOG_LEVEL': 'WARNING', 'LOG_FORMAT': 'console'},
    ]
    
    for config in configs:
        print(f"\nTesting config: {config}")
        
        # Set environment variables
        for key, value in config.items():
            os.environ[key] = value
        
        try:
            # Re-import to use new configuration
            import importlib
            import app.core.logging as logging_module
            importlib.reload(logging_module)
            
            logger = logging_module.get_logger('test.env')
            logger.info(f"Test with config: {config}")
            
            print(f"✓ Configuration works: {config}")
        except Exception as e:
            print(f"✗ Configuration failed: {config} - Error: {e}")
        finally:
            # Reset environment
            for key in config:
                if key in os.environ:
                    del os.environ[key]


if __name__ == "__main__":
    print("Testing InventorySync Logging Configuration")
    print("=" * 50)
    
    try:
        test_logging_without_dependencies()
        test_logging_with_dependencies()
        test_log_file_creation()
        test_environment_configuration()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
