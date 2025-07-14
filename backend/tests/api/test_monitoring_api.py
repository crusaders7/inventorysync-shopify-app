"""
API integration tests for monitoring endpoints
Tests health checks, metrics, and system monitoring
"""

import pytest
import json
from unittest.mock import patch, Mock

from api.monitoring import router


class TestMonitoringAPI:
    """Test monitoring API endpoints"""
    
    def test_health_check(self, client):
        """Test basic health check endpoint"""
        response = client.get("/api/v1/monitoring/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "database" in data
        assert "memory_usage_percent" in data
        assert "cpu_usage_percent" in data
        
        # Status should be one of the valid values
        assert data["status"] in ["healthy", "degraded", "critical", "error"]
    
    def test_simple_health_check(self, client):
        """Test simple health check for load balancers"""
        response = client.get("/api/v1/monitoring/health/simple")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    def test_health_check_with_database_failure(self, client):
        """Test health check when database is down"""
        with patch('database.check_database_health') as mock_db_health:
            mock_db_health.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/v1/monitoring/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["degraded", "error"]
            assert data["database"] == "error"
    
    def test_health_check_high_resource_usage(self, client):
        """Test health check with high resource usage"""
        with patch('psutil.virtual_memory') as mock_memory:
            with patch('psutil.cpu_percent') as mock_cpu:
                # Simulate high resource usage
                mock_memory.return_value.percent = 95.0
                mock_cpu.return_value = 95.0
                
                response = client.get("/api/v1/monitoring/health")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "critical"
                assert data["memory_usage_percent"] == 95.0
                assert data["cpu_usage_percent"] == 95.0


class TestMetricsAPI:
    """Test metrics API endpoints"""
    
    def test_get_performance_metrics_requires_auth(self, client):
        """Test performance metrics requires admin authentication"""
        response = client.get("/api/v1/monitoring/metrics")
        
        assert response.status_code == 422  # Missing header
    
    def test_get_performance_metrics_with_auth(self, client, admin_headers):
        """Test performance metrics with admin authentication"""
        with patch('utils.logging.logger.get_performance_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "uptime_seconds": 3600,
                "average_response_time_ms": 250.5,
                "error_rate_percent": 2.5,
                "memory_usage_percent": 45.0,
                "cpu_usage_percent": 30.0,
                "total_requests": 1500,
                "total_errors": 37,
                "active_alerts": [],
                "recent_alerts": []
            }
            
            response = client.get("/api/v1/monitoring/metrics", headers=admin_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["uptime_seconds"] == 3600
            assert data["average_response_time_ms"] == 250.5
            assert data["error_rate_percent"] == 2.5
            assert data["total_requests"] == 1500
    
    def test_get_performance_metrics_monitoring_disabled(self, client, admin_headers):
        """Test performance metrics when monitoring is disabled"""
        with patch('utils.logging.logger.get_performance_metrics') as mock_metrics:
            mock_metrics.return_value = {"monitoring": "disabled"}
            
            response = client.get("/api/v1/monitoring/metrics", headers=admin_headers)
            
            assert response.status_code == 503
            data = response.json()
            assert "Monitoring is disabled" in data["detail"]
    
    def test_get_metrics_summary_no_auth(self, client):
        """Test metrics summary without authentication"""
        with patch('utils.logging.logger.get_performance_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "uptime_seconds": 3600,
                "average_response_time_ms": 250.5,
                "memory_usage_percent": 45.0,
                "error_rate_percent": 1.0
            }
            
            response = client.get("/api/v1/monitoring/metrics/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert "uptime_seconds" in data
            assert "average_response_time_ms" in data
            assert "status" in data
            # Should not include sensitive data
            assert "total_requests" not in data
    
    def test_metrics_summary_monitoring_disabled(self, client):
        """Test metrics summary when monitoring is disabled"""
        with patch('utils.logging.logger.get_performance_metrics') as mock_metrics:
            mock_metrics.return_value = {"monitoring": "disabled"}
            
            response = client.get("/api/v1/monitoring/metrics/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert data["monitoring"] == "disabled"


class TestAlertsAPI:
    """Test alerts API endpoints"""
    
    def test_get_alerts_requires_auth(self, client):
        """Test alerts endpoint requires authentication"""
        response = client.get("/api/v1/monitoring/alerts")
        
        assert response.status_code == 422  # Missing header
    
    def test_get_recent_alerts(self, client, admin_headers):
        """Test getting recent alerts"""
        mock_alerts = [
            {
                "type": "high_response_time",
                "severity": "warning",
                "message": "High average response time: 5500ms",
                "timestamp": "2024-01-15T10:30:00Z"
            },
            {
                "type": "high_error_rate",
                "severity": "critical",
                "message": "High error rate: 8.5%",
                "timestamp": "2024-01-15T10:25:00Z"
            }
        ]
        
        with patch('utils.logging.logger.alert_manager.get_recent_alerts') as mock_get_alerts:
            mock_get_alerts.return_value = mock_alerts
            
            response = client.get("/api/v1/monitoring/alerts", headers=admin_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "alerts" in data
            assert len(data["alerts"]) == 2
            assert data["alerts"][0]["type"] == "high_response_time"
            assert data["alerts"][1]["severity"] == "critical"
    
    def test_get_alerts_with_limit(self, client, admin_headers):
        """Test getting alerts with limit parameter"""
        with patch('utils.logging.logger.alert_manager.get_recent_alerts') as mock_get_alerts:
            mock_get_alerts.return_value = []
            
            response = client.get("/api/v1/monitoring/alerts?limit=5", headers=admin_headers)
            
            assert response.status_code == 200
            # Verify limit was passed to the function
            mock_get_alerts.assert_called_once_with(5)


class TestSystemInfoAPI:
    """Test system information API endpoints"""
    
    def test_get_system_info_requires_auth(self, client):
        """Test system info requires authentication"""
        response = client.get("/api/v1/monitoring/system")
        
        assert response.status_code == 422  # Missing header
    
    def test_get_system_info(self, client, admin_headers):
        """Test getting system information"""
        with patch('psutil.virtual_memory') as mock_memory:
            with patch('psutil.disk_usage') as mock_disk:
                with patch('psutil.net_io_counters') as mock_network:
                    with patch('psutil.Process') as mock_process:
                        with patch('psutil.cpu_count') as mock_cpu_count:
                            with patch('psutil.cpu_percent') as mock_cpu_percent:
                                # Mock system data
                                mock_memory.return_value.total = 8 * 1024**3  # 8GB
                                mock_memory.return_value.available = 4 * 1024**3  # 4GB
                                mock_memory.return_value.percent = 50.0
                                
                                mock_disk.return_value.total = 100 * 1024**3  # 100GB
                                mock_disk.return_value.free = 70 * 1024**3   # 70GB
                                mock_disk.return_value.used = 30 * 1024**3   # 30GB
                                
                                mock_network.return_value.bytes_sent = 1024 * 1024
                                mock_network.return_value.bytes_recv = 2048 * 1024
                                mock_network.return_value.packets_sent = 1000
                                mock_network.return_value.packets_recv = 1500
                                
                                mock_cpu_count.return_value = 4
                                mock_cpu_percent.return_value = 25.0
                                
                                # Mock process data
                                mock_proc = Mock()
                                mock_proc.pid = 12345
                                mock_proc.memory_info.return_value.rss = 256 * 1024**2  # 256MB
                                mock_proc.cpu_percent.return_value = 15.0
                                mock_proc.create_time.return_value = 1642248000
                                mock_proc.num_threads.return_value = 8
                                mock_proc.num_fds.return_value = 25
                                mock_process.return_value = mock_proc
                                
                                response = client.get("/api/v1/monitoring/system", headers=admin_headers)
                                
                                assert response.status_code == 200
                                data = response.json()
                                
                                # Check system data
                                assert "system" in data
                                assert data["system"]["cpu_count"] == 4
                                assert data["system"]["memory"]["total_gb"] == 8.0
                                
                                # Check process data
                                assert "process" in data
                                assert data["process"]["pid"] == 12345
                                assert data["process"]["num_threads"] == 8


class TestLogsAPI:
    """Test logs API endpoints"""
    
    def test_get_recent_errors_requires_auth(self, client):
        """Test recent errors requires authentication"""
        response = client.get("/api/v1/monitoring/logs/errors")
        
        assert response.status_code == 422  # Missing header
    
    def test_get_recent_errors_no_log_file(self, client, admin_headers):
        """Test getting recent errors when no log file exists"""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            
            response = client.get("/api/v1/monitoring/logs/errors", headers=admin_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["errors"] == []
            assert data["total_count"] == 0
    
    def test_get_recent_errors_with_log_file(self, client, admin_headers):
        """Test getting recent errors from log file"""
        mock_log_lines = [
            '{"timestamp": "2024-01-15T10:30:00Z", "level": "ERROR", "message": "Test error 1"}',
            '{"timestamp": "2024-01-15T10:31:00Z", "level": "ERROR", "message": "Test error 2"}',
            '2024-01-15 10:32:00 - ERROR - Plain text error'
        ]
        
        with patch('pathlib.Path.exists') as mock_exists:
            with patch('builtins.open', mock_open_multiple_lines(mock_log_lines)):
                mock_exists.return_value = True
                
                response = client.get("/api/v1/monitoring/logs/errors", headers=admin_headers)
                
                assert response.status_code == 200
                data = response.json()
                assert len(data["errors"]) == 3
                assert data["errors"][0]["message"] == "Test error 1"
                assert data["errors"][2]["message"] == "Plain text error"


class TestConfigAPI:
    """Test configuration API endpoints"""
    
    def test_get_monitoring_config_requires_auth(self, client):
        """Test monitoring config requires authentication"""
        response = client.get("/api/v1/monitoring/config")
        
        assert response.status_code == 422  # Missing header
    
    def test_get_monitoring_config(self, client, admin_headers):
        """Test getting monitoring configuration"""
        with patch.dict('os.environ', {
            'MONITORING_ENABLED': 'true',
            'LOG_LEVEL': 'INFO',
            'ENVIRONMENT': 'production'
        }):
            response = client.get("/api/v1/monitoring/config", headers=admin_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["monitoring_enabled"] == True
            assert data["log_level"] == "INFO"
            assert data["environment"] == "production"
            assert "alert_thresholds" in data
            assert "retention" in data


class TestTestingEndpoints:
    """Test development testing endpoints"""
    
    def test_trigger_test_error_requires_auth(self, client):
        """Test trigger test error requires authentication"""
        response = client.post("/api/v1/monitoring/test/error")
        
        assert response.status_code == 422  # Missing header
    
    def test_trigger_test_error_in_development(self, client, admin_headers):
        """Test triggering test error in development"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'development'}):
            with patch('utils.logging.logger.error') as mock_error:
                with patch('utils.logging.logger.performance_monitor.record_error') as mock_record:
                    response = client.post("/api/v1/monitoring/test/error", headers=admin_headers)
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "Test error triggered successfully" in data["message"]
                    
                    # Verify error was logged and recorded
                    mock_error.assert_called_once()
                    mock_record.assert_called_once_with("test_error")
    
    def test_trigger_test_error_in_production(self, client, admin_headers):
        """Test triggering test error is disabled in production"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'production'}):
            response = client.post("/api/v1/monitoring/test/error", headers=admin_headers)
            
            assert response.status_code == 403
            data = response.json()
            assert "Test endpoints disabled in production" in data["detail"]
    
    def test_trigger_test_alert(self, client, admin_headers):
        """Test triggering test alert"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'development'}):
            with patch('utils.logging.logger.alert_manager.check_performance_alerts') as mock_alerts:
                mock_alerts.return_value = [
                    {
                        "type": "high_response_time",
                        "severity": "warning",
                        "message": "High average response time: 10000ms",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                ]
                
                response = client.post("/api/v1/monitoring/test/alert", headers=admin_headers)
                
                assert response.status_code == 200
                data = response.json()
                assert data["alerts_generated"] == 1
                assert len(data["alerts"]) == 1
                assert data["alerts"][0]["type"] == "high_response_time"


class TestMonitoringIntegration:
    """Test monitoring API integration scenarios"""
    
    def test_health_to_metrics_flow(self, client, admin_headers):
        """Test flow from health check to detailed metrics"""
        # First check health
        health_response = client.get("/api/v1/monitoring/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        
        # If system is healthy, get detailed metrics
        if health_data["status"] == "healthy":
            with patch('utils.logging.logger.get_performance_metrics') as mock_metrics:
                mock_metrics.return_value = {
                    "uptime_seconds": 3600,
                    "average_response_time_ms": 200.0,
                    "error_rate_percent": 1.0,
                    "memory_usage_percent": 40.0,
                    "cpu_usage_percent": 25.0,
                    "total_requests": 1000,
                    "total_errors": 10,
                    "active_alerts": [],
                    "recent_alerts": []
                }
                
                metrics_response = client.get("/api/v1/monitoring/metrics", headers=admin_headers)
                assert metrics_response.status_code == 200
    
    def test_alert_generation_and_retrieval(self, client, admin_headers):
        """Test generating alerts and retrieving them"""
        # Trigger test alert
        with patch.dict('os.environ', {'ENVIRONMENT': 'development'}):
            trigger_response = client.post("/api/v1/monitoring/test/alert", headers=admin_headers)
            assert trigger_response.status_code == 200
            
            # Get alerts
            alerts_response = client.get("/api/v1/monitoring/alerts", headers=admin_headers)
            assert alerts_response.status_code == 200


# =============================================================================
# UTILITY FUNCTIONS FOR TESTS
# =============================================================================

def mock_open_multiple_lines(lines):
    """Mock open() for multiple lines"""
    from unittest.mock import mock_open
    return mock_open(read_data='\n'.join(lines))


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestMonitoringPerformance:
    """Test monitoring API performance"""
    
    def test_health_check_performance(self, client, performance_timer):
        """Test health check response time"""
        performance_timer.start()
        response = client.get("/api/v1/monitoring/health")
        performance_timer.stop()
        
        assert response.status_code == 200
        # Health check should be very fast
        assert performance_timer.elapsed() < 0.5  # Less than 500ms
    
    def test_metrics_summary_performance(self, client, performance_timer):
        """Test metrics summary response time"""
        performance_timer.start()
        response = client.get("/api/v1/monitoring/metrics/summary")
        performance_timer.stop()
        
        assert response.status_code == 200
        # Metrics summary should be fast
        assert performance_timer.elapsed() < 1.0  # Less than 1 second


# =============================================================================
# SECURITY TESTS
# =============================================================================

class TestMonitoringSecurity:
    """Test monitoring API security"""
    
    def test_admin_endpoints_require_auth(self, client):
        """Test all admin endpoints require authentication"""
        admin_endpoints = [
            "/api/v1/monitoring/metrics",
            "/api/v1/monitoring/alerts",
            "/api/v1/monitoring/system",
            "/api/v1/monitoring/logs/errors",
            "/api/v1/monitoring/config"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 422  # Missing auth header
    
    def test_sensitive_data_not_exposed(self, client):
        """Test sensitive data is not exposed in public endpoints"""
        response = client.get("/api/v1/monitoring/metrics/summary")
        
        if response.status_code == 200:
            data = response.json()
            # Should not contain sensitive information
            sensitive_fields = ["total_requests", "total_errors", "active_alerts"]
            for field in sensitive_fields:
                assert field not in data or data[field] is None
    
    def test_test_endpoints_disabled_in_production(self, client, admin_headers):
        """Test endpoints are disabled in production"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'production'}):
            test_endpoints = [
                "/api/v1/monitoring/test/error",
                "/api/v1/monitoring/test/alert"
            ]
            
            for endpoint in test_endpoints:
                response = client.post(endpoint, headers=admin_headers)
                assert response.status_code == 403