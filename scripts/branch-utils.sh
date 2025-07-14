#!/bin/bash

# Branch management utility script for InventorySync Shopify App

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to create a new feature branch
create_feature() {
    if [ -z "$1" ]; then
        echo -e "${RED}Error: Please provide a feature name${NC}"
        echo "Usage: ./branch-utils.sh create-feature <feature-name>"
        return 1
    fi
    
    echo -e "${YELLOW}Creating feature branch: feature/$1${NC}"
    git checkout main
    git pull origin main
    git checkout -b "feature/$1"
    echo -e "${GREEN}✓ Feature branch created: feature/$1${NC}"
}

# Function to create a new bugfix branch
create_bugfix() {
    if [ -z "$1" ]; then
        echo -e "${RED}Error: Please provide a bugfix name${NC}"
        echo "Usage: ./branch-utils.sh create-bugfix <bugfix-name>"
        return 1
    fi
    
    echo -e "${YELLOW}Creating bugfix branch: bugfix/$1${NC}"
    git checkout main
    git pull origin main
    git checkout -b "bugfix/$1"
    echo -e "${GREEN}✓ Bugfix branch created: bugfix/$1${NC}"
}

# Function to create a new hotfix branch
create_hotfix() {
    if [ -z "$1" ]; then
        echo -e "${RED}Error: Please provide a hotfix name${NC}"
        echo "Usage: ./branch-utils.sh create-hotfix <hotfix-name>"
        return 1
    fi
    
    echo -e "${YELLOW}Creating hotfix branch: hotfix/$1${NC}"
    git checkout main
    git pull origin main
    git checkout -b "hotfix/$1"
    echo -e "${GREEN}✓ Hotfix branch created: hotfix/$1${NC}"
}

# Function to clean up merged branches
cleanup_branches() {
    echo -e "${YELLOW}Cleaning up merged branches...${NC}"
    
    # Get all merged branches except main and master
    merged_branches=$(git branch --merged main | grep -vE "^\*|main|master")
    
    if [ -z "$merged_branches" ]; then
        echo -e "${GREEN}No merged branches to clean up${NC}"
        return 0
    fi
    
    echo "The following branches will be deleted:"
    echo "$merged_branches"
    echo ""
    read -p "Proceed with deletion? (y/n): " confirm
    
    if [ "$confirm" = "y" ]; then
        echo "$merged_branches" | xargs -n 1 git branch -d
        echo -e "${GREEN}✓ Merged branches cleaned up${NC}"
    else
        echo -e "${YELLOW}Cleanup cancelled${NC}"
    fi
}

# Function to show branch status
show_status() {
    echo -e "${YELLOW}Branch Status:${NC}"
    echo ""
    echo -e "${GREEN}Current branch:${NC}"
    git branch --show-current
    echo ""
    echo -e "${GREEN}All branches:${NC}"
    git branch -a
    echo ""
    echo -e "${GREEN}Recent commits on current branch:${NC}"
    git log --oneline -5
}

# Function to sync with main
sync_with_main() {
    current_branch=$(git branch --show-current)
    
    if [ "$current_branch" = "main" ]; then
        echo -e "${RED}Error: Already on main branch${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Syncing $current_branch with main...${NC}"
    git checkout main
    git pull origin main
    git checkout "$current_branch"
    git merge main
    echo -e "${GREEN}✓ Branch synced with main${NC}"
}

# Help function
show_help() {
    echo "Branch Management Utility"
    echo ""
    echo "Usage: ./branch-utils.sh <command> [arguments]"
    echo ""
    echo "Commands:"
    echo "  create-feature <name>  Create a new feature branch"
    echo "  create-bugfix <name>   Create a new bugfix branch"
    echo "  create-hotfix <name>   Create a new hotfix branch"
    echo "  cleanup                Clean up merged branches"
    echo "  status                 Show branch status"
    echo "  sync                   Sync current branch with main"
    echo "  help                   Show this help message"
}

# Main script logic
case "$1" in
    "create-feature")
        create_feature "$2"
        ;;
    "create-bugfix")
        create_bugfix "$2"
        ;;
    "create-hotfix")
        create_hotfix "$2"
        ;;
    "cleanup")
        cleanup_branches
        ;;
    "status")
        show_status
        ;;
    "sync")
        sync_with_main
        ;;
    "help"|"")
        show_help
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        show_help
        exit 1
        ;;
esac
