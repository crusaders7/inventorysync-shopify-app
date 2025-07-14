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
