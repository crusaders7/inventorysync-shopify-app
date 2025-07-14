# Example 2: Multi-Terminal Development Workflow

This example demonstrates how to set up an efficient multi-terminal development environment using Warp with MCP, where different terminals handle specific tasks like testing, building, monitoring, and development.

## Overview

Learn how to:
- Configure multiple Warp terminals for specialized tasks
- Set up terminal profiles and layouts
- Synchronize work across terminals using MCP
- Create automated workflows for common development patterns
- Monitor and coordinate multiple processes

## Prerequisites

- Warp terminal with multiple pane support
- MCP server configured
- tmux or similar terminal multiplexer (optional)
- Project with test suite and build system

## Step-by-Step Tutorial

### Step 1: Create Terminal Profiles

First, let's create specialized terminal profiles for different tasks.

Create `.warp/profiles/`:

```bash
mkdir -p .warp/profiles
```

Create `.warp/profiles/development.json`:

```json
{
  "name": "Development Terminal",
  "theme": "dark-blue",
  "startupCommands": [
    "echo '🔧 Development Terminal Ready'",
    "git status",
    "npm run dev"
  ],
  "environment": {
    "TERMINAL_PURPOSE": "development",
    "NODE_ENV": "development",
    "DEBUG": "app:*"
  },
  "mcpConfig": {
    "role": "developer",
    "capabilities": ["code_completion", "error_detection", "refactoring"],
    "autoSuggest": true
  }
}
```

Create `.warp/profiles/testing.json`:

```json
{
  "name": "Testing Terminal",
  "theme": "dark-green",
  "startupCommands": [
    "echo '🧪 Testing Terminal Ready'",
    "npm run test:watch"
  ],
  "environment": {
    "TERMINAL_PURPOSE": "testing",
    "NODE_ENV": "test",
    "TEST_WATCH": "true"
  },
  "mcpConfig": {
    "role": "tester",
    "capabilities": ["test_generation", "coverage_analysis"],
    "autoRunTests": true
  }
}
```

Create `.warp/profiles/monitoring.json`:

```json
{
  "name": "Monitoring Terminal",
  "theme": "dark-purple",
  "startupCommands": [
    "echo '📊 Monitoring Terminal Ready'",
    "npm run monitor"
  ],
  "environment": {
    "TERMINAL_PURPOSE": "monitoring",
    "LOG_LEVEL": "verbose"
  },
  "mcpConfig": {
    "role": "monitor",
    "capabilities": ["log_analysis", "performance_tracking", "alert_management"],
    "alertThresholds": {
      "cpu": 80,
      "memory": 90,
      "errorRate": 0.05
    }
  }
}
```

Create `.warp/profiles/database.json`:

```json
{
  "name": "Database Terminal",
  "theme": "dark-orange",
  "startupCommands": [
    "echo '🗄️ Database Terminal Ready'",
    "docker-compose up -d postgres redis",
    "npm run db:migrate:status"
  ],
  "environment": {
    "TERMINAL_PURPOSE": "database",
    "DATABASE_URL": "${DATABASE_URL}"
  },
  "mcpConfig": {
    "role": "database",
    "capabilities": ["query_optimization", "migration_management"],
    "autoBackup": true
  }
}
```

### Step 2: Create Layout Configuration

Create `.warp/layouts/dev-workflow.yml`:

```yaml
name: Full Development Workflow
description: Multi-terminal setup for complete development workflow

layout:
  type: grid
  rows: 2
  columns: 2
  
panes:
  - position: [0, 0]
    profile: development
    size: large
    focus: true
    
  - position: [0, 1]
    profile: testing
    size: medium
    
  - position: [1, 0]
    profile: monitoring
    size: medium
    
  - position: [1, 1]
    profile: database
    size: medium

keybindings:
  - key: "cmd+1"
    action: "focus:development"
  - key: "cmd+2"
    action: "focus:testing"
  - key: "cmd+3"
    action: "focus:monitoring"
  - key: "cmd+4"
    action: "focus:database"
  - key: "cmd+r"
    action: "restart:current"
  - key: "cmd+shift+r"
    action: "restart:all"

synchronization:
  enabled: true
  mcpServer: "localhost:8080"
  shareContext: true
  events:
    - source: development
      target: testing
      trigger: "file:save"
      action: "run:tests"
    - source: testing
      target: monitoring
      trigger: "test:fail"
      action: "log:error"
```

### Step 3: Create Coordination Scripts

Create `scripts/terminal-coordinator.js`:

```javascript
#!/usr/bin/env node

const { MCPClient } = require('@mcp/client');
const { EventEmitter } = require('events');
const chokidar = require('chokidar');

class TerminalCoordinator extends EventEmitter {
    constructor(config) {
        super();
        this.config = config;
        this.terminals = new Map();
        this.mcpClient = new MCPClient({
            serverUrl: config.mcpServerUrl,
            authToken: process.env.MCP_AUTH_TOKEN
        });
    }

    async initialize() {
        // Connect to MCP server
        await this.mcpClient.connect();
        
        // Register terminals
        for (const terminal of this.config.terminals) {
            await this.registerTerminal(terminal);
        }
        
        // Set up file watchers
        this.setupFileWatchers();
        
        // Set up inter-terminal communication
        this.setupCommunication();
    }

    async registerTerminal(terminal) {
        const registration = await this.mcpClient.registerTerminal({
            id: terminal.id,
            purpose: terminal.purpose,
            capabilities: terminal.capabilities
        });
        
        this.terminals.set(terminal.id, {
            ...terminal,
            registration
        });
        
        console.log(`✅ Registered ${terminal.purpose} terminal`);
    }

    setupFileWatchers() {
        // Watch for source file changes
        const srcWatcher = chokidar.watch(['src/**/*.js', 'src/**/*.ts'], {
            ignored: /node_modules/,
            persistent: true
        });

        srcWatcher.on('change', (path) => {
            this.emit('file:changed', { path, type: 'source' });
            this.notifyTerminal('testing', 'run:affected-tests', { path });
        });

        // Watch for test file changes
        const testWatcher = chokidar.watch(['test/**/*.js', 'test/**/*.spec.js'], {
            ignored: /node_modules/,
            persistent: true
        });

        testWatcher.on('change', (path) => {
            this.emit('file:changed', { path, type: 'test' });
            this.notifyTerminal('testing', 'run:specific-test', { path });
        });
    }

    setupCommunication() {
        // Listen for MCP events
        this.mcpClient.on('terminal:event', (event) => {
            this.handleTerminalEvent(event);
        });

        // Set up terminal-specific handlers
        this.on('test:failed', (data) => {
            this.notifyTerminal('development', 'highlight:error', data);
            this.notifyTerminal('monitoring', 'log:test-failure', data);
        });

        this.on('build:complete', (data) => {
            this.notifyTerminal('testing', 'run:smoke-tests', data);
            this.notifyTerminal('monitoring', 'log:build-success', data);
        });

        this.on('performance:alert', (data) => {
            this.notifyAllTerminals('alert:performance', data);
        });
    }

    async notifyTerminal(terminalId, action, data) {
        const terminal = this.terminals.get(terminalId);
        if (!terminal) return;

        await this.mcpClient.sendCommand({
            terminalId,
            action,
            data,
            timestamp: new Date().toISOString()
        });
    }

    async notifyAllTerminals(action, data) {
        for (const [terminalId] of this.terminals) {
            await this.notifyTerminal(terminalId, action, data);
        }
    }

    handleTerminalEvent(event) {
        console.log(`📨 Event from ${event.terminalId}: ${event.type}`);
        
        switch (event.type) {
            case 'test:complete':
                this.handleTestComplete(event);
                break;
            case 'build:start':
                this.handleBuildStart(event);
                break;
            case 'error:detected':
                this.handleErrorDetected(event);
                break;
            default:
                this.emit(event.type, event.data);
        }
    }

    handleTestComplete(event) {
        const { passed, failed, coverage } = event.data;
        
        if (failed > 0) {
            this.emit('test:failed', event.data);
        } else {
            this.notifyTerminal('development', 'show:success', {
                message: `✅ All tests passed! Coverage: ${coverage}%`
            });
        }
    }

    handleBuildStart(event) {
        this.notifyTerminal('monitoring', 'track:build', {
            buildId: event.data.buildId,
            startTime: event.data.timestamp
        });
    }

    handleErrorDetected(event) {
        this.notifyAllTerminals('alert:error', {
            error: event.data.error,
            source: event.terminalId,
            severity: event.data.severity
        });
    }
}

// CLI Usage
if (require.main === module) {
    const config = {
        mcpServerUrl: process.env.MCP_SERVER_URL || 'http://localhost:8080',
        terminals: [
            {
                id: 'development',
                purpose: 'development',
                capabilities: ['edit', 'build', 'debug']
            },
            {
                id: 'testing',
                purpose: 'testing',
                capabilities: ['test', 'coverage']
            },
            {
                id: 'monitoring',
                purpose: 'monitoring',
                capabilities: ['log', 'metric', 'alert']
            },
            {
                id: 'database',
                purpose: 'database',
                capabilities: ['query', 'migrate', 'backup']
            }
        ]
    };

    const coordinator = new TerminalCoordinator(config);
    
    coordinator.initialize().then(() => {
        console.log('🚀 Terminal coordinator started');
    }).catch(err => {
        console.error('Failed to start coordinator:', err);
        process.exit(1);
    });
}

module.exports = TerminalCoordinator;
```

### Step 4: Create Terminal-Specific Scripts

Create `scripts/dev-terminal.sh`:

```bash
#!/bin/bash
# Development terminal startup script

# Source common functions
source ./scripts/common.sh

# Set terminal title
set_terminal_title "🔧 Development"

# Configure git hooks for auto-formatting
setup_git_hooks() {
    echo "Setting up git hooks..."
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
npm run lint:fix
npm run format
git add -u
EOF
    chmod +x .git/hooks/pre-commit
}

# Start development server with hot reload
start_dev_server() {
    echo "Starting development server..."
    
    # Export development environment
    export NODE_ENV=development
    export DEBUG=app:*
    export FORCE_COLOR=1
    
    # Start with nodemon for auto-restart
    npx nodemon \
        --watch src \
        --ext js,ts,json \
        --exec "node -r ts-node/register" \
        src/server.ts \
        | npx pino-pretty
}

# MCP integration for code assistance
enable_mcp_assistance() {
    echo "Enabling MCP code assistance..."
    
    # Start MCP agent for this terminal
    mcp agent start \
        --role developer \
        --capabilities "code_completion,error_detection,refactoring" \
        --terminal-id "$TERMINAL_ID" &
    
    # Store agent PID
    echo $! > /tmp/mcp-dev-agent.pid
}

# Main execution
main() {
    clear
    print_banner "Development Terminal"
    
    # Check prerequisites
    check_dependencies "node" "npm" "git"
    
    # Setup environment
    setup_git_hooks
    enable_mcp_assistance
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi
    
    # Start development server
    start_dev_server
}

# Cleanup on exit
cleanup() {
    echo "Cleaning up..."
    if [ -f /tmp/mcp-dev-agent.pid ]; then
        kill $(cat /tmp/mcp-dev-agent.pid) 2>/dev/null
        rm /tmp/mcp-dev-agent.pid
    fi
}

trap cleanup EXIT

# Run main function
main
```

Create `scripts/test-terminal.sh`:

```bash
#!/bin/bash
# Testing terminal startup script

# Source common functions
source ./scripts/common.sh

# Set terminal title
set_terminal_title "🧪 Testing"

# Configure test environment
setup_test_env() {
    export NODE_ENV=test
    export TEST_TIMEOUT=10000
    export FORCE_COLOR=1
    
    # Create test database if needed
    if [ ! -f ".test.db" ]; then
        echo "Creating test database..."
        npm run db:test:setup
    fi
}

# Start test watcher with coverage
start_test_watcher() {
    echo "Starting test watcher..."
    
    # Use Jest in watch mode with coverage
    npx jest \
        --watch \
        --coverage \
        --coverageReporters="text" \
        --coverageReporters="lcov" \
        --notify \
        --runInBand \
        --detectOpenHandles
}

# MCP integration for test assistance
enable_test_mcp() {
    echo "Enabling MCP test assistance..."
    
    mcp agent start \
        --role tester \
        --capabilities "test_generation,coverage_analysis,failure_diagnosis" \
        --terminal-id "$TERMINAL_ID" \
        --config test-agent.json &
    
    echo $! > /tmp/mcp-test-agent.pid
}

# Monitor test results and notify other terminals
monitor_test_results() {
    # Pipe test output through processor
    while IFS= read -r line; do
        echo "$line"
        
        # Detect test failures and notify
        if echo "$line" | grep -q "FAIL"; then
            mcp notify \
                --event "test:failed" \
                --data "{\"line\": \"$line\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
        fi
        
        # Detect test success and notify
        if echo "$line" | grep -q "PASS.*Test Suites:"; then
            mcp notify \
                --event "test:passed" \
                --data "{\"line\": \"$line\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
        fi
    done
}

# Main execution
main() {
    clear
    print_banner "Testing Terminal"
    
    # Setup environment
    setup_test_env
    enable_test_mcp
    
    # Start test watcher with monitoring
    start_test_watcher 2>&1 | monitor_test_results
}

# Cleanup on exit
cleanup() {
    echo "Cleaning up..."
    if [ -f /tmp/mcp-test-agent.pid ]; then
        kill $(cat /tmp/mcp-test-agent.pid) 2>/dev/null
        rm /tmp/mcp-test-agent.pid
    fi
}

trap cleanup EXIT

# Run main function
main
```

Create `scripts/monitor-terminal.sh`:

```bash
#!/bin/bash
# Monitoring terminal startup script

# Source common functions
source ./scripts/common.sh

# Set terminal title
set_terminal_title "📊 Monitoring"

# Setup monitoring dashboard
setup_monitoring() {
    export MONITOR_INTERVAL=5
    export LOG_LEVEL=verbose
    export ENABLE_METRICS=true
}

# Start multi-panel monitoring
start_monitoring() {
    # Use tmux to create monitoring panels
    tmux new-session -d -s monitor
    
    # Top panel - System metrics
    tmux send-keys -t monitor "htop" C-m
    
    # Bottom left - Application logs
    tmux split-window -v -t monitor
    tmux send-keys -t monitor "npm run logs:tail" C-m
    
    # Bottom right - Performance metrics
    tmux split-window -h -t monitor
    tmux send-keys -t monitor "npm run metrics:dashboard" C-m
    
    # Attach to session
    tmux attach-session -t monitor
}

# Alternative: Custom monitoring dashboard
custom_monitoring_dashboard() {
    node - << 'EOF'
const blessed = require('blessed');
const contrib = require('blessed-contrib');

// Create screen
const screen = blessed.screen({
    smartCSR: true,
    title: 'Development Monitor'
});

// Create grid
const grid = new contrib.grid({
    rows: 12,
    cols: 12,
    screen: screen
});

// CPU Line Chart
const cpuLine = grid.set(0, 0, 4, 6, contrib.line, {
    style: {
        line: "yellow",
        text: "green",
        baseline: "white"
    },
    xLabelPadding: 3,
    xPadding: 5,
    label: 'CPU Usage %'
});

// Memory Gauge
const memGauge = grid.set(0, 6, 4, 6, contrib.gauge, {
    label: 'Memory Usage',
    stroke: 'green',
    fill: 'white'
});

// Error Log
const errorLog = grid.set(4, 0, 4, 12, contrib.log, {
    fg: "red",
    selectedFg: "green",
    label: 'Error Log'
});

// Request Table
const requestTable = grid.set(8, 0, 4, 12, contrib.table, {
    keys: true,
    fg: 'white',
    selectedFg: 'white',
    selectedBg: 'blue',
    interactive: true,
    label: 'Recent Requests',
    width: '100%',
    height: '100%',
    border: {type: "line", fg: "cyan"},
    columnSpacing: 3,
    columnWidth: [10, 20, 20, 10]
});

// Set table headers
requestTable.setData({
    headers: ['Time', 'Endpoint', 'Method', 'Status'],
    data: []
});

// Update functions
let cpuHistory = [];
function updateCPU() {
    const usage = Math.random() * 100;
    cpuHistory.push(usage);
    if (cpuHistory.length > 50) cpuHistory.shift();
    
    cpuLine.setData([{
        title: 'CPU',
        x: Array.from({length: cpuHistory.length}, (_, i) => i.toString()),
        y: cpuHistory
    }]);
    screen.render();
}

function updateMemory() {
    const usage = Math.random() * 100;
    memGauge.setPercent(usage);
    screen.render();
}

function addError(message) {
    errorLog.log(`[${new Date().toISOString()}] ${message}`);
    screen.render();
}

function addRequest(data) {
    const table = requestTable.getData();
    table.data.unshift([
        new Date().toTimeString().split(' ')[0],
        data.endpoint || '/api/unknown',
        data.method || 'GET',
        data.status || '200'
    ]);
    if (table.data.length > 20) table.data.pop();
    requestTable.setData(table);
    screen.render();
}

// MCP Integration
const { MCPClient } = require('@mcp/client');
const mcpClient = new MCPClient({
    serverUrl: process.env.MCP_SERVER_URL || 'http://localhost:8080'
});

mcpClient.on('metric:cpu', (data) => {
    cpuHistory.push(data.value);
    if (cpuHistory.length > 50) cpuHistory.shift();
    cpuLine.setData([{
        title: 'CPU',
        x: Array.from({length: cpuHistory.length}, (_, i) => i.toString()),
        y: cpuHistory
    }]);
});

mcpClient.on('metric:memory', (data) => {
    memGauge.setPercent(data.value);
});

mcpClient.on('log:error', (data) => {
    addError(data.message);
});

mcpClient.on('http:request', (data) => {
    addRequest(data);
});

// Start intervals
setInterval(updateCPU, 1000);
setInterval(updateMemory, 2000);

// Simulate some events
setInterval(() => {
    if (Math.random() > 0.8) {
        addError('Random error occurred in module XYZ');
    }
}, 5000);

setInterval(() => {
    addRequest({
        endpoint: ['/api/users', '/api/products', '/api/orders'][Math.floor(Math.random() * 3)],
        method: ['GET', 'POST', 'PUT', 'DELETE'][Math.floor(Math.random() * 4)],
        status: ['200', '201', '400', '404', '500'][Math.floor(Math.random() * 5)]
    });
}, 1000);

// Key bindings
screen.key(['escape', 'q', 'C-c'], () => process.exit(0));

// Render
screen.render();

// Connect to MCP
mcpClient.connect().then(() => {
    console.log('Connected to MCP server');
}).catch(err => {
    addError(`Failed to connect to MCP: ${err.message}`);
});
EOF
}

# Main execution
main() {
    clear
    print_banner "Monitoring Terminal"
    
    # Setup environment
    setup_monitoring
    
    # Check if tmux is available
    if command -v tmux &> /dev/null; then
        start_monitoring
    else
        echo "tmux not found, using custom dashboard..."
        custom_monitoring_dashboard
    fi
}

# Run main function
main
```

### Step 5: Create Common Functions

Create `scripts/common.sh`:

```bash
#!/bin/bash
# Common functions for terminal scripts

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Print colored banner
print_banner() {
    local title=$1
    echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC} ${title}$(printf '%*s' $((36-${#title})) '') ${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
    echo ""
}

# Set terminal title
set_terminal_title() {
    echo -ne "\033]0;$1\007"
}

# Check dependencies
check_dependencies() {
    local missing=()
    
    for cmd in "$@"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [ ${#missing[@]} -ne 0 ]; then
        echo -e "${RED}Error: Missing dependencies: ${missing[*]}${NC}"
        echo "Please install them before continuing."
        exit 1
    fi
}

# Export terminal ID for MCP
export TERMINAL_ID=$(uuidgen 2>/dev/null || echo "terminal-$$")
export TERMINAL_START_TIME=$(date +%s)

# Log with timestamp
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        ERROR)   echo -e "${RED}[$timestamp] ERROR: $message${NC}" ;;
        WARN)    echo -e "${YELLOW}[$timestamp] WARN: $message${NC}" ;;
        INFO)    echo -e "${GREEN}[$timestamp] INFO: $message${NC}" ;;
        DEBUG)   echo -e "${BLUE}[$timestamp] DEBUG: $message${NC}" ;;
        *)       echo "[$timestamp] $level: $message" ;;
    esac
}
```

### Step 6: Create Warp Workflow Integration

Create `.warp/workflows/multi-terminal.yml`:

```yaml
name: Multi-Terminal Development
description: Launch complete development environment with multiple specialized terminals

variables:
  project_name: "${PROJECT_NAME:-myproject}"
  mcp_server: "${MCP_SERVER_URL:-http://localhost:8080}"

steps:
  - name: Start MCP Server
    command: |
      docker-compose up -d mcp-server
      sleep 5
      curl -f ${mcp_server}/health || exit 1
    description: "Ensure MCP server is running"

  - name: Launch Terminal Layout
    command: |
      warp launch layout .warp/layouts/dev-workflow.yml
    description: "Open multi-terminal layout"

  - name: Start Terminal Coordinator
    command: |
      node scripts/terminal-coordinator.js &
      echo $! > /tmp/coordinator.pid
    description: "Start coordination service"
    background: true

  - name: Initialize Terminals
    parallel: true
    steps:
      - command: "warp run profile development"
        terminal: 1
      - command: "warp run profile testing"
        terminal: 2
      - command: "warp run profile monitoring"
        terminal: 3
      - command: "warp run profile database"
        terminal: 4

  - name: Verify Setup
    command: |
      sleep 3
      mcp status --all-terminals
    description: "Verify all terminals are connected"

shortcuts:
  restart-all:
    description: "Restart all terminals"
    command: |
      pkill -f "node scripts/"
      warp restart all
  
  sync-terminals:
    description: "Sync terminal states"
    command: "mcp sync --all"
  
  save-session:
    description: "Save current terminal session"
    command: "warp save session --name dev-session-$(date +%Y%m%d-%H%M%S)"
```

### Step 7: Usage Instructions

1. **Initial Setup**:
   ```bash
   # Install dependencies
   npm install
   
   # Set up MCP server
   docker-compose up -d mcp-server
   
   # Initialize terminal profiles
   warp init profiles
   ```

2. **Launch Multi-Terminal Environment**:
   ```bash
   # Using workflow
   warp run workflow multi-terminal
   
   # Or manually
   warp launch layout .warp/layouts/dev-workflow.yml
   ```

3. **Working with Terminals**:
   ```bash
   # Switch between terminals
   # Cmd+1: Development
   # Cmd+2: Testing  
   # Cmd+3: Monitoring
   # Cmd+4: Database
   
   # Restart specific terminal
   warp restart terminal --id development
   
   # Sync all terminals
   warp sync all
   ```

4. **Coordinate Actions**:
   ```bash
   # Trigger test run from development terminal
   mcp trigger --target testing --action run-tests
   
   # Send notification to all terminals
   mcp broadcast --message "Deployment starting"
   
   # Share context between terminals
   mcp share --from development --to testing --data "$(git diff)"
   ```

## Advanced Features

### Custom Terminal Actions

Create `.warp/actions/custom-actions.yml`:

```yaml
actions:
  quick-fix:
    description: "Apply quick fix from test failure"
    trigger: "test:failed"
    steps:
      - terminal: development
        command: "git stash"
      - terminal: development
        command: "mcp fix --error '${error_message}'"
      - terminal: testing
        command: "npm test -- ${test_file}"

  performance-profile:
    description: "Start performance profiling"
    terminals: [development, monitoring]
    steps:
      - terminal: development
        command: "npm run profile:start"
      - terminal: monitoring
        command: "npm run metrics:profile"
    
  debug-session:
    description: "Start debugging session"
    steps:
      - terminal: development
        command: "npm run debug"
      - terminal: monitoring
        command: "tail -f logs/debug.log"
      - terminal: testing
        command: "npm run test:debug"
```

### Terminal Synchronization

Create `scripts/sync-terminals.js`:

```javascript
const { execSync } = require('child_process');
const fs = require('fs');

class TerminalSync {
    constructor() {
        this.stateFile = '/tmp/terminal-state.json';
        this.state = this.loadState();
    }

    loadState() {
        try {
            return JSON.parse(fs.readFileSync(this.stateFile, 'utf8'));
        } catch {
            return {
                terminals: {},
                lastSync: null
            };
        }
    }

    saveState() {
        fs.writeFileSync(this.stateFile, JSON.stringify(this.state, null, 2));
    }

    syncTerminal(terminalId, data) {
        this.state.terminals[terminalId] = {
            ...this.state.terminals[terminalId],
            ...data,
            lastUpdate: new Date().toISOString()
        };
        this.state.lastSync = new Date().toISOString();
        this.saveState();
        
        // Notify other terminals
        this.notifyOthers(terminalId, data);
    }

    notifyOthers(sourceId, data) {
        Object.keys(this.state.terminals).forEach(terminalId => {
            if (terminalId !== sourceId) {
                this.sendToTerminal(terminalId, {
                    source: sourceId,
                    data: data
                });
            }
        });
    }

    sendToTerminal(terminalId, message) {
        // Use MCP to send message
        try {
            execSync(`mcp send --terminal ${terminalId} --message '${JSON.stringify(message)}'`);
        } catch (err) {
            console.error(`Failed to send to ${terminalId}:`, err);
        }
    }
}

module.exports = TerminalSync;
```

## Troubleshooting

### Common Issues

1. **Terminal Not Responding**
   ```bash
   # Check terminal status
   mcp status --terminal development
   
   # Restart specific terminal
   warp restart terminal --id development
   
   # Check coordinator logs
   tail -f /tmp/coordinator.log
   ```

2. **Synchronization Issues**
   ```bash
   # Reset sync state
   rm /tmp/terminal-state.json
   
   # Restart coordinator
   kill $(cat /tmp/coordinator.pid)
   node scripts/terminal-coordinator.js &
   ```

3. **Performance Problems**
   ```bash
   # Check resource usage
   htop
   
   # Limit terminal resources
   export TERMINAL_CPU_LIMIT=50
   export TERMINAL_MEM_LIMIT=1G
   ```

## Best Practices

1. **Terminal Organization**
   - Keep each terminal focused on a single purpose
   - Use consistent color schemes for visual identification
   - Set up clear keyboard shortcuts for navigation

2. **Communication Patterns**
   - Use events for loose coupling between terminals
   - Implement proper error handling in coordination scripts
   - Log all inter-terminal communications

3. **Resource Management**
   - Monitor CPU and memory usage per terminal
   - Set up automatic cleanup for long-running processes
   - Use terminal pooling for resource-intensive operations

4. **Session Management**
   - Save terminal sessions regularly
   - Create templates for common workflows
   - Document custom configurations

## Next Steps

- Explore [Example 3: AI Agents](../example-3-ai-agents-project-management/) for autonomous project management
- Learn about [Example 4: Full-Stack Development](../example-4-fullstack-concurrent/) for concurrent process management
- Check out [Example 1: Automated Deployments](../example-1-automated-deployments/) for deployment automation
