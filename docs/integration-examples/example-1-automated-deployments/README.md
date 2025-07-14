# Example 1: Automated Deployments with Warp + MCP

This example demonstrates how to set up automated deployments using Warp terminal with MCP integration for AI-assisted monitoring, validation, and rollback capabilities.

## Overview

In this tutorial, you'll learn to:
- Configure MCP for deployment automation
- Create deployment scripts with AI assistance
- Set up automated health checks
- Implement intelligent rollback mechanisms
- Monitor deployments in real-time

## Prerequisites

- Docker and Docker Compose installed
- Access to a deployment target (staging/production server)
- Basic understanding of CI/CD concepts
- MCP server running with appropriate permissions

## Step-by-Step Tutorial

### Step 1: Set Up MCP Configuration

Create the MCP configuration for deployment automation:

```bash
# Create MCP config directory
mkdir -p ~/.config/mcp
```

Create `~/.config/mcp/deployment.json`:

```json
{
  "server": {
    "url": "http://localhost:3000",
    "auth": {
      "type": "bearer",
      "token": "${MCP_AUTH_TOKEN}"
    }
  },
  "agents": {
    "deployment": {
      "capabilities": [
        "shell_execution",
        "file_manipulation",
        "process_monitoring",
        "log_analysis"
      ],
      "prompts": {
        "pre_deployment": "Analyze the deployment plan and identify potential issues",
        "health_check": "Monitor application health and report anomalies",
        "rollback_decision": "Analyze metrics and decide if rollback is needed"
      }
    }
  }
}
```

### Step 2: Create Deployment Scripts

Create the main deployment script:

```bash
# Create scripts directory
mkdir -p scripts
```

Create `scripts/deploy.sh`:

```bash
#!/bin/bash
# Automated deployment script with MCP integration

set -e

# Configuration
ENVIRONMENT=${1:-staging}
SERVICE_NAME="inventorysync-app"
DEPLOY_DIR="/opt/deployments/${SERVICE_NAME}"
HEALTH_CHECK_URL="http://localhost:3000/health"
ROLLBACK_THRESHOLD=3

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# MCP Integration Functions
mcp_pre_check() {
    echo -e "${YELLOW}Running MCP pre-deployment analysis...${NC}"
    mcp analyze --config deployment.json --prompt pre_deployment \
        --context "environment=${ENVIRONMENT}" \
        --context "service=${SERVICE_NAME}" \
        --context "changes=$(git diff HEAD~1)"
}

mcp_health_monitor() {
    echo -e "${YELLOW}Starting MCP health monitoring...${NC}"
    mcp monitor --config deployment.json --prompt health_check \
        --url "${HEALTH_CHECK_URL}" \
        --duration 300 \
        --interval 10 &
    echo $! > /tmp/mcp_monitor.pid
}

mcp_rollback_check() {
    local metrics_file=$1
    echo -e "${YELLOW}Analyzing deployment metrics...${NC}"
    
    mcp analyze --config deployment.json --prompt rollback_decision \
        --metrics "${metrics_file}" \
        --threshold "${ROLLBACK_THRESHOLD}"
}

# Deployment Functions
build_application() {
    echo -e "${GREEN}Building application...${NC}"
    docker build -t ${SERVICE_NAME}:${ENVIRONMENT} .
    docker tag ${SERVICE_NAME}:${ENVIRONMENT} ${SERVICE_NAME}:latest-${ENVIRONMENT}
}

deploy_application() {
    echo -e "${GREEN}Deploying to ${ENVIRONMENT}...${NC}"
    
    # Stop existing container
    docker stop ${SERVICE_NAME}-${ENVIRONMENT} || true
    docker rm ${SERVICE_NAME}-${ENVIRONMENT} || true
    
    # Start new container
    docker run -d \
        --name ${SERVICE_NAME}-${ENVIRONMENT} \
        --restart unless-stopped \
        -p 3000:3000 \
        -e NODE_ENV=${ENVIRONMENT} \
        -v ${DEPLOY_DIR}/logs:/app/logs \
        ${SERVICE_NAME}:${ENVIRONMENT}
}

health_check() {
    echo -e "${GREEN}Running health checks...${NC}"
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f ${HEALTH_CHECK_URL} > /dev/null 2>&1; then
            echo -e "${GREEN}Health check passed!${NC}"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo "Health check attempt ${attempt}/${max_attempts}..."
        sleep 2
    done
    
    echo -e "${RED}Health check failed!${NC}"
    return 1
}

rollback() {
    echo -e "${RED}Initiating rollback...${NC}"
    
    # Stop current deployment
    docker stop ${SERVICE_NAME}-${ENVIRONMENT} || true
    docker rm ${SERVICE_NAME}-${ENVIRONMENT} || true
    
    # Restore previous version
    docker run -d \
        --name ${SERVICE_NAME}-${ENVIRONMENT} \
        --restart unless-stopped \
        -p 3000:3000 \
        -e NODE_ENV=${ENVIRONMENT} \
        ${SERVICE_NAME}:previous-${ENVIRONMENT}
}

# Main Deployment Flow
main() {
    echo -e "${GREEN}Starting deployment to ${ENVIRONMENT}${NC}"
    
    # Pre-deployment checks
    if ! mcp_pre_check; then
        echo -e "${RED}Pre-deployment checks failed. Aborting.${NC}"
        exit 1
    fi
    
    # Tag current version as previous
    docker tag ${SERVICE_NAME}:latest-${ENVIRONMENT} ${SERVICE_NAME}:previous-${ENVIRONMENT} || true
    
    # Build and deploy
    build_application
    deploy_application
    
    # Start monitoring
    mcp_health_monitor
    
    # Health checks
    if ! health_check; then
        rollback
        kill $(cat /tmp/mcp_monitor.pid) 2>/dev/null || true
        exit 1
    fi
    
    # Monitor for 5 minutes
    echo -e "${GREEN}Monitoring deployment for 5 minutes...${NC}"
    sleep 300
    
    # Stop monitoring and analyze
    kill $(cat /tmp/mcp_monitor.pid) 2>/dev/null || true
    
    # Check if rollback is needed
    if mcp_rollback_check "/tmp/deployment_metrics.json"; then
        echo -e "${GREEN}Deployment successful!${NC}"
    else
        echo -e "${RED}Deployment metrics indicate issues. Rolling back...${NC}"
        rollback
        exit 1
    fi
}

# Run main function
main
```

### Step 3: Create Docker Configuration

Create `Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node healthcheck.js

EXPOSE 3000

CMD ["node", "server.js"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: inventorysync-${ENVIRONMENT:-staging}
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=${ENVIRONMENT:-staging}
      - DATABASE_URL=${DATABASE_URL}
      - MCP_SERVER_URL=http://mcp-server:8080
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    networks:
      - app-network
    depends_on:
      - mcp-server

  mcp-server:
    image: mcp/server:latest
    container_name: mcp-server
    ports:
      - "8080:8080"
    environment:
      - MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN}
    volumes:
      - ./mcp-config:/config
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

### Step 4: Set Up Monitoring Configuration

Create `monitoring/deployment-monitor.js`:

```javascript
const axios = require('axios');
const fs = require('fs');

class DeploymentMonitor {
    constructor(config) {
        this.config = config;
        this.metrics = {
            responseTime: [],
            errorRate: 0,
            totalRequests: 0,
            failedRequests: 0,
            startTime: Date.now()
        };
    }

    async checkHealth() {
        const start = Date.now();
        try {
            const response = await axios.get(this.config.healthCheckUrl, {
                timeout: 5000
            });
            
            this.metrics.responseTime.push(Date.now() - start);
            this.metrics.totalRequests++;
            
            return response.status === 200;
        } catch (error) {
            this.metrics.failedRequests++;
            this.metrics.totalRequests++;
            this.metrics.errorRate = this.metrics.failedRequests / this.metrics.totalRequests;
            return false;
        }
    }

    async monitor(duration, interval) {
        const endTime = Date.now() + duration * 1000;
        
        while (Date.now() < endTime) {
            await this.checkHealth();
            await new Promise(resolve => setTimeout(resolve, interval * 1000));
        }
        
        this.saveMetrics();
    }

    calculateStats() {
        const avgResponseTime = this.metrics.responseTime.reduce((a, b) => a + b, 0) / this.metrics.responseTime.length;
        const maxResponseTime = Math.max(...this.metrics.responseTime);
        const minResponseTime = Math.min(...this.metrics.responseTime);
        
        return {
            avgResponseTime,
            maxResponseTime,
            minResponseTime,
            errorRate: this.metrics.errorRate,
            uptime: ((this.metrics.totalRequests - this.metrics.failedRequests) / this.metrics.totalRequests) * 100,
            duration: Date.now() - this.metrics.startTime
        };
    }

    saveMetrics() {
        const stats = this.calculateStats();
        fs.writeFileSync('/tmp/deployment_metrics.json', JSON.stringify({
            metrics: this.metrics,
            statistics: stats,
            timestamp: new Date().toISOString()
        }, null, 2));
    }
}

// CLI usage
if (require.main === module) {
    const monitor = new DeploymentMonitor({
        healthCheckUrl: process.env.HEALTH_CHECK_URL || 'http://localhost:3000/health'
    });
    
    const duration = parseInt(process.argv[2]) || 300; // 5 minutes default
    const interval = parseInt(process.argv[3]) || 10;  // 10 seconds default
    
    monitor.monitor(duration, interval).then(() => {
        console.log('Monitoring complete. Metrics saved to /tmp/deployment_metrics.json');
    });
}

module.exports = DeploymentMonitor;
```

### Step 5: Create MCP Integration Scripts

Create `mcp-scripts/analyze.js`:

```javascript
#!/usr/bin/env node

const { MCPClient } = require('@mcp/client');
const fs = require('fs');

async function analyzeDeployment(prompt, context) {
    const client = new MCPClient({
        serverUrl: process.env.MCP_SERVER_URL || 'http://localhost:8080',
        authToken: process.env.MCP_AUTH_TOKEN
    });

    try {
        const result = await client.analyze({
            prompt: prompt,
            context: context,
            model: 'gpt-4',
            temperature: 0.3
        });

        console.log('Analysis Result:', result.analysis);
        
        if (result.recommendations) {
            console.log('\nRecommendations:');
            result.recommendations.forEach((rec, i) => {
                console.log(`${i + 1}. ${rec}`);
            });
        }

        return result.approved;
    } catch (error) {
        console.error('MCP Analysis Error:', error);
        return false;
    }
}

// CLI interface
if (require.main === module) {
    const args = process.argv.slice(2);
    const prompt = args[0];
    const contextFile = args[1];
    
    let context = {};
    if (contextFile && fs.existsSync(contextFile)) {
        context = JSON.parse(fs.readFileSync(contextFile, 'utf8'));
    }

    analyzeDeployment(prompt, context).then(approved => {
        process.exit(approved ? 0 : 1);
    });
}

module.exports = { analyzeDeployment };
```

### Step 6: Create Warp Workflows

Create `.warp/workflows/deployment.yml`:

```yaml
name: Automated Deployment Workflow
description: Deploy application with AI-assisted monitoring

steps:
  - name: Pre-deployment Check
    command: |
      echo "🔍 Running pre-deployment checks..."
      ./scripts/deploy.sh check
    ai_assist: true
    ai_prompt: "Review the deployment plan and identify any potential issues"

  - name: Build Application
    command: |
      echo "🔨 Building application..."
      docker build -t inventorysync:latest .
    continue_on_error: false

  - name: Run Tests
    command: |
      echo "🧪 Running tests..."
      npm test
    continue_on_error: false

  - name: Deploy to Staging
    command: |
      echo "🚀 Deploying to staging..."
      ./scripts/deploy.sh staging
    ai_monitor: true
    ai_monitor_config:
      duration: 300
      alerts:
        - type: error_rate
          threshold: 0.05
        - type: response_time
          threshold: 1000

  - name: Validate Deployment
    command: |
      echo "✅ Validating deployment..."
      curl -f http://localhost:3000/health
    retries: 3
    retry_delay: 10

shortcuts:
  deploy-prod:
    description: "Deploy to production with full validation"
    steps:
      - "warp run deployment --env production"
  
  rollback:
    description: "Rollback to previous version"
    command: "./scripts/rollback.sh"
```

### Step 7: Usage Instructions

1. **Initial Setup**:
   ```bash
   # Install dependencies
   npm install
   
   # Set up environment variables
   export MCP_AUTH_TOKEN="your-token-here"
   export DATABASE_URL="your-database-url"
   
   # Make scripts executable
   chmod +x scripts/*.sh
   ```

2. **Deploy to Staging**:
   ```bash
   # Using the deployment script
   ./scripts/deploy.sh staging
   
   # Or using Warp workflow
   warp run deployment --env staging
   ```

3. **Deploy to Production**:
   ```bash
   # With extra validation
   ./scripts/deploy.sh production
   
   # Using Warp shortcut
   warp deploy-prod
   ```

4. **Monitor Deployment**:
   ```bash
   # Real-time monitoring
   node monitoring/deployment-monitor.js 300 10
   
   # View logs
   docker logs -f inventorysync-production
   ```

5. **Rollback if Needed**:
   ```bash
   # Automatic rollback (triggered by monitoring)
   # Or manual rollback
   ./scripts/rollback.sh production
   ```

## Advanced Features

### Custom Health Checks

Create `healthcheck.js`:

```javascript
const http = require('http');
const { checkDatabase, checkRedis, checkExternalAPI } = require('./utils/health');

async function performHealthCheck() {
    const checks = {
        database: await checkDatabase(),
        redis: await checkRedis(),
        api: await checkExternalAPI(),
        memory: process.memoryUsage().heapUsed < 500 * 1024 * 1024, // 500MB limit
        uptime: process.uptime() > 10 // At least 10 seconds up
    };

    const healthy = Object.values(checks).every(check => check === true);
    
    return {
        status: healthy ? 'healthy' : 'unhealthy',
        checks,
        timestamp: new Date().toISOString()
    };
}

// Health check endpoint
const server = http.createServer(async (req, res) => {
    if (req.url === '/health') {
        const health = await performHealthCheck();
        res.writeHead(health.status === 'healthy' ? 200 : 503, {
            'Content-Type': 'application/json'
        });
        res.end(JSON.stringify(health));
    }
});

server.listen(3001);
```

### Deployment Notifications

Create `scripts/notify.sh`:

```bash
#!/bin/bash

# Send deployment notifications via various channels

DEPLOYMENT_STATUS=$1
ENVIRONMENT=$2
VERSION=$3

# Slack notification
if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST $SLACK_WEBHOOK_URL \
        -H 'Content-Type: application/json' \
        -d "{
            \"text\": \"Deployment ${DEPLOYMENT_STATUS}: ${ENVIRONMENT} - v${VERSION}\",
            \"color\": \"$([ "$DEPLOYMENT_STATUS" = "success" ] && echo "good" || echo "danger")\"
        }"
fi

# Email notification
if [ ! -z "$EMAIL_RECIPIENT" ]; then
    echo "Deployment ${DEPLOYMENT_STATUS} for ${ENVIRONMENT} (v${VERSION})" | \
        mail -s "Deployment Notification" $EMAIL_RECIPIENT
fi

# MCP notification for AI analysis
mcp notify --event "deployment.${DEPLOYMENT_STATUS}" \
    --data "{\"environment\": \"${ENVIRONMENT}\", \"version\": \"${VERSION}\"}"
```

## Troubleshooting

### Common Issues

1. **MCP Connection Failed**
   - Check if MCP server is running: `docker ps | grep mcp-server`
   - Verify authentication token: `echo $MCP_AUTH_TOKEN`
   - Check network connectivity: `curl http://localhost:8080/health`

2. **Deployment Timeout**
   - Increase health check timeout in `deploy.sh`
   - Check application logs: `docker logs inventorysync-staging`
   - Verify resource availability: `docker system df`

3. **Rollback Failed**
   - Ensure previous image exists: `docker images | grep previous`
   - Check disk space: `df -h`
   - Manual rollback: `docker run -d --name app-recovery previous-image`

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Enable debug mode
export DEBUG=true
export MCP_DEBUG=true

# Run deployment with verbose output
./scripts/deploy.sh staging --verbose
```

## Best Practices

1. **Always Test in Staging First**
   - Never deploy directly to production
   - Ensure staging environment mirrors production

2. **Monitor Key Metrics**
   - Response time
   - Error rate
   - Resource usage
   - Business metrics

3. **Implement Gradual Rollouts**
   - Use canary deployments for critical changes
   - Monitor subset of traffic before full rollout

4. **Document Everything**
   - Keep deployment logs
   - Document configuration changes
   - Track deployment history

## Next Steps

- Explore [Example 2: Multi-Terminal Workflow](../example-2-multi-terminal-workflow/) for complex development setups
- Learn about [Example 3: AI Agents](../example-3-ai-agents-project-management/) for autonomous project management
- Set up [Example 4: Full-Stack Development](../example-4-fullstack-concurrent/) for concurrent process management
