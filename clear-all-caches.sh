#!/bin/bash

# InventorySync Cache Clearing Script
# This script clears all caches and build artifacts for both development and production environments

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Environment flag
ENVIRONMENT="development"
VERBOSE=false

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -e, --env <environment>   Set environment (development/production) [default: development]"
    echo "  -v, --verbose            Enable verbose output"
    echo "  -h, --help               Show this help message"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "production" ]]; then
    echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'. Must be 'development' or 'production'.${NC}"
    exit 1
fi

# Start logging
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}InventorySync Cache Clearing Script${NC}"
echo -e "${BLUE}Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "${BLUE}Started at: $(date)${NC}"
echo -e "${BLUE}======================================${NC}"
echo

# Function to log actions
log_action() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Counter for cleared items
CLEARED_COUNT=0

# Function to remove directory and count
remove_directory() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        if $VERBOSE; then
            log_action "Removing $description: $dir"
        fi
        rm -rf "$dir"
        ((CLEARED_COUNT++))
        log_success "$description cleared"
    else
        if $VERBOSE; then
            log_warning "$description not found: $dir"
        fi
    fi
}

# Function to remove files by pattern
remove_files_pattern() {
    local pattern=$1
    local description=$2
    local dir=${3:-.}
    
    local files=$(find "$dir" -name "$pattern" -type f 2>/dev/null)
    if [ -n "$files" ]; then
        local count=$(echo "$files" | wc -l)
        if $VERBOSE; then
            log_action "Removing $count $description files"
            echo "$files" | while read -r file; do
                echo "  - $file"
            done
        fi
        echo "$files" | xargs rm -f
        ((CLEARED_COUNT++))
        log_success "$description cleared ($count files)"
    else
        if $VERBOSE; then
            log_warning "No $description found"
        fi
    fi
}

# 1. Clear Frontend/Vite caches
echo -e "${YELLOW}Clearing Frontend/Vite caches...${NC}"
cd "$SCRIPT_DIR/frontend" 2>/dev/null || {
    log_error "Frontend directory not found"
}

# Execute existing Vite cache clearing script if it exists
if [ -f "clear-vite-cache.sh" ]; then
    log_action "Executing existing Vite cache clearing script"
    bash clear-vite-cache.sh
    ((CLEARED_COUNT++))
else
    # Manual Vite cache clearing
    remove_directory "node_modules/.vite" "Vite cache"
    remove_directory "dist" "Frontend dist directory"
    remove_directory ".temp" "Frontend temp directory"
fi

# Additional frontend cache directories
remove_directory ".next" "Next.js cache"
remove_directory ".nuxt" "Nuxt.js cache"
remove_directory ".parcel-cache" "Parcel cache"

# 2. Clear npm cache
echo
echo -e "${YELLOW}Clearing npm cache...${NC}"
log_action "Clearing npm cache"
if command -v npm &> /dev/null; then
    npm cache clean --force 2>/dev/null
    ((CLEARED_COUNT++))
    log_success "npm cache cleared"
else
    log_warning "npm not found, skipping npm cache"
fi

# Clear pnpm cache if it exists
if command -v pnpm &> /dev/null; then
    log_action "Clearing pnpm cache"
    pnpm cache clean 2>/dev/null
    ((CLEARED_COUNT++))
    log_success "pnpm cache cleared"
fi

# Clear yarn cache if it exists
if command -v yarn &> /dev/null; then
    log_action "Clearing yarn cache"
    yarn cache clean 2>/dev/null
    ((CLEARED_COUNT++))
    log_success "yarn cache cleared"
fi

# 3. Clear Python caches and build artifacts
echo
echo -e "${YELLOW}Clearing Python caches and build artifacts...${NC}"
cd "$SCRIPT_DIR" || exit 1

# Remove Python cache directories
remove_directory "__pycache__" "Python cache directories"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Remove Python compiled files
remove_files_pattern "*.pyc" "Python compiled files"
remove_files_pattern "*.pyo" "Python optimized files"
remove_files_pattern "*.pyd" "Python DLL files"

# Remove Python build directories
remove_directory "build" "Python build directory"
remove_directory "dist" "Python dist directory"
remove_directory "*.egg-info" "Python egg-info directories"
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null

# Remove pytest cache
remove_directory ".pytest_cache" "Pytest cache"

# Remove coverage data
remove_directory ".coverage" "Coverage data"
remove_directory "htmlcov" "HTML coverage reports"
remove_files_pattern "coverage.xml" "Coverage XML files"

# 4. Clear build artifacts
echo
echo -e "${YELLOW}Clearing build artifacts...${NC}"

# Clear log files (but keep the logs directory)
if [ -d "logs" ]; then
    log_action "Clearing log files"
    find logs -name "*.log" -type f -delete 2>/dev/null
    ((CLEARED_COUNT++))
    log_success "Log files cleared"
fi

# Clear temporary directories
remove_directory "tmp" "Temporary directory"
remove_directory "temp" "Temp directory"

# Clear Shopify specific caches
remove_directory ".shopify" "Shopify cache"

# Clear Docker volumes (only in development)
if [ "$ENVIRONMENT" = "development" ]; then
    if command -v docker &> /dev/null; then
        log_action "Clearing Docker build cache"
        docker builder prune -f 2>/dev/null
        ((CLEARED_COUNT++))
        log_success "Docker build cache cleared"
    fi
fi

# 5. Environment-specific cleaning
echo
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${YELLOW}Production environment - performing careful cleanup...${NC}"
    log_warning "Skipping aggressive cleanup in production mode"
    log_warning "Node modules and virtual environments preserved"
else
    echo -e "${YELLOW}Development environment - performing aggressive cleanup...${NC}"
    
    # Option to clear node_modules (interactive in dev mode)
    read -p "Clear node_modules directories? This will require reinstallation. (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_action "Removing node_modules directories"
        find . -name "node_modules" -type d -prune -exec rm -rf {} + 2>/dev/null
        ((CLEARED_COUNT++))
        log_success "node_modules directories cleared"
    fi
    
    # Option to clear Python virtual environment
    read -p "Clear Python virtual environment? This will require reinstallation. (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        remove_directory "venv" "Python virtual environment"
        remove_directory ".venv" "Python virtual environment"
        remove_directory "env" "Python environment"
    fi
fi

# 6. Final cleanup
echo
echo -e "${YELLOW}Performing final cleanup...${NC}"

# Clear OS-specific files
remove_files_pattern ".DS_Store" "macOS metadata files"
remove_files_pattern "Thumbs.db" "Windows thumbnail files"

# Clear editor swap files
remove_files_pattern "*.swp" "Vim swap files"
remove_files_pattern "*.swo" "Vim swap files"
remove_files_pattern "*~" "Backup files"

# Summary
echo
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}Cache clearing completed!${NC}"
echo -e "${BLUE}Total items cleared: ${YELLOW}$CLEARED_COUNT${NC}"
echo -e "${BLUE}Completed at: $(date)${NC}"
echo -e "${BLUE}======================================${NC}"

# Provide next steps
echo
echo -e "${YELLOW}Next steps:${NC}"
if [ "$ENVIRONMENT" = "development" ]; then
    echo "1. Run 'npm install' in the frontend directory to reinstall dependencies"
    echo "2. Run 'pip install -r requirements.txt' to reinstall Python dependencies"
    echo "3. Run 'npm run dev' or './start-dev.sh' to start development server"
else
    echo "1. Restart your application services"
    echo "2. Monitor logs for any issues"
fi

exit 0
