# InventorySync Logging System Deployment Guide

## Overview

This guide covers the deployment and configuration of the comprehensive logging system for InventorySync in production environments.

## 1. Environment Configuration

### Required Environment Variables

```bash
# Basic Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_DIR=/var/log/inventorysync

# Sentry Configuration (Error Tracking)
ENABLE_SENTRY=true
SENTRY_DSN=https://your-project-key@sentry.io/your-project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1

# Performance Monitoring
ENABLE_APM=true
ENABLE_PERFORMANCE_LOGGING=true

# Log Aggregation (Choose one)
LOG_AGGREGATION_TYPE=elasticsearch  # or cloudwatch, datadog
```

### Log Aggregation Options

#### Option 1: Elasticsearch (ELK Stack)
```bash
LOG_AGGREGATION_TYPE=elasticsearch
ELASTICSEARCH_HOSTS=elasticsearch.example.com:9200
ES_BULK_SIZE=1000
ES_FLUSH_INTERVAL=5
```

#### Option 2: AWS CloudWatch
```bash
LOG_AGGREGATION_TYPE=cloudwatch
AWS_DEFAULT_REGION=us-east-1
CLOUDWATCH_STREAM_NAME=inventorysync-api
```

#### Option 3: Datadog
```bash
LOG_AGGREGATION_TYPE=datadog
DATADOG_API_KEY=your_datadog_api_key
DATADOG_SITE=datadoghq.com
```

## 2. Log Directory Setup

### Create log directories with proper permissions:
```bash
sudo mkdir -p /var/log/inventorysync
sudo chown -R inventorysync:inventorysync /var/log/inventorysync
sudo chmod 755 /var/log/inventorysync
```

## 3. Log Rotation Configuration

### Using logrotate (recommended for Linux):
Create `/etc/logrotate.d/inventorysync`:

```
/var/log/inventorysync/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 inventorysync inventorysync
    sharedscripts
    postrotate
        # Signal the app to reopen log files if needed
        /usr/bin/killall -SIGUSR1 gunicorn 2>/dev/null || true
    endscript
}
```

## 4. Sentry Setup

1. **Create a Sentry Project**:
   - Go to https://sentry.io
   - Create a new project for InventorySync
   - Select "FastAPI" as the platform

2. **Get Your DSN**:
   - Navigate to Settings → Projects → Your Project → Client Keys
   - Copy the DSN

3. **Configure Release Tracking**:
   ```bash
   export APP_VERSION=$(git rev-parse --short HEAD)
   ```

## 5. Monitoring Dashboard Setup

### Key Metrics to Monitor

1. **Error Rate**:
   - Track 5xx errors
   - Monitor error types and frequencies
   - Set up alerts for error spikes

2. **Performance Metrics**:
   - API response times (p50, p95, p99)
   - Database query performance
   - Cache hit rates

3. **Business Metrics**:
   - Authentication failures
   - Inventory update volumes
   - Webhook processing times

### Sample Elasticsearch Queries

**Error Analysis**:
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"level": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  },
  "aggs": {
    "error_types": {
      "terms": {"field": "error_type.keyword"}
    }
  }
}
```

**Performance Analysis**:
```json
{
  "query": {
    "term": {"logger": "inventorysync.performance"}
  },
  "aggs": {
    "avg_response_time": {
      "avg": {"field": "value"}
    },
    "response_time_percentiles": {
      "percentiles": {
        "field": "value",
        "percents": [50, 95, 99]
      }
    }
  }
}
```

## 6. Security Considerations

### Log Sanitization
- Sensitive data is automatically redacted
- PII is not logged by default
- API keys and passwords are masked

### Audit Log Retention
- Keep audit logs for at least 90 days
- Consider longer retention for compliance
- Encrypt logs at rest

### Access Control
- Restrict log file access to authorized personnel
- Use role-based access for log aggregation systems
- Enable audit logging for log access

## 7. Testing the Logging System

### Pre-deployment Checklist

- [ ] All environment variables are set correctly
- [ ] Log directories exist with proper permissions
- [ ] Sentry integration is tested
- [ ] Log rotation is configured
- [ ] Log aggregation is connected
- [ ] Monitoring alerts are set up
- [ ] Security policies are in place

### Test Commands

1. **Test log writing**:
   ```bash
   python test_logging_setup.py
   ```

2. **Verify Sentry integration**:
   ```bash
   curl -X POST http://localhost:8000/test-sentry
   ```

3. **Check log rotation**:
   ```bash
   sudo logrotate -f /etc/logrotate.d/inventorysync
   ```

## 8. Troubleshooting

### Common Issues

1. **Permission Denied Errors**:
   ```bash
   sudo chown -R inventorysync:inventorysync /var/log/inventorysync
   ```

2. **Sentry Not Receiving Events**:
   - Check SENTRY_DSN is correct
   - Verify network connectivity
   - Check Sentry rate limits

3. **Log Files Growing Too Large**:
   - Verify log rotation is working
   - Adjust LOG_LEVEL if too verbose
   - Check for log spam from specific components

### Debug Mode

For troubleshooting, temporarily enable debug logging:
```bash
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

## 9. Performance Impact

### Expected Overhead
- Structured logging: ~1-2% CPU overhead
- Sentry integration: <1% with sampling
- Log aggregation: Minimal with batching

### Optimization Tips
- Use appropriate log levels
- Enable sampling for high-volume logs
- Batch log shipments to aggregation services
- Consider async logging for high-throughput scenarios

## 10. Compliance and Regulations

### GDPR Compliance
- No PII in logs by default
- Audit logs for data access
- Log retention policies aligned with GDPR

### SOC2 Compliance
- Comprehensive audit trail
- Secure log storage
- Access controls and monitoring

### Industry Standards
- Follows OWASP logging guidelines
- Implements structured logging best practices
- Supports common log aggregation formats

## Conclusion

The InventorySync logging system provides comprehensive monitoring, debugging, and compliance capabilities. Regular review of logs and metrics will help maintain system health and security.

For questions or issues, contact the DevOps team or refer to the internal documentation.
