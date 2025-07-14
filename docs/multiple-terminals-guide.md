# Multiple Terminal Workflows Guide

This guide covers effective strategies for managing multiple terminal sessions, including terminal multiplexers, Warp's built-in features, process management, and integration with development tools.

## Table of Contents
1. [Terminal Multiplexers](#terminal-multiplexers)
   - [tmux Setup and Usage](#tmux-setup-and-usage)
   - [GNU Screen Setup and Usage](#gnu-screen-setup-and-usage)
2. [Warp Terminal Features](#warp-terminal-features)
   - [Split Panes](#split-panes)
   - [Tabs](#tabs)
3. [Process Management and Job Control](#process-management-and-job-control)
4. [Running Background Processes](#running-background-processes)
5. [Monitoring Multiple Processes](#monitoring-multiple-processes)
6. [Best Practices for Terminal Organization](#best-practices-for-terminal-organization)
7. [VS Code Terminal Integration](#vs-code-terminal-integration)

## Terminal Multiplexers

Terminal multiplexers allow you to manage multiple terminal sessions within a single window, persist sessions across connections, and organize your workflow efficiently.

### tmux Setup and Usage

#### Installation
```bash
# Ubuntu/Debian
sudo apt-get install tmux

# macOS
brew install tmux

# Check version
tmux -V
```

#### Basic tmux Commands
```bash
# Start new session
tmux new -s myproject

# Start new named session
tmux new -s inventory-sync

# List sessions
tmux ls

# Attach to session
tmux attach -t inventory-sync

# Detach from session
# Press: Ctrl+b, then d

# Kill session
tmux kill-session -t inventory-sync
```

#### tmux Key Bindings (Default prefix: Ctrl+b)
```
# Session Management
Ctrl+b s     # List sessions
Ctrl+b $     # Rename session
Ctrl+b d     # Detach from session

# Window Management
Ctrl+b c     # Create new window
Ctrl+b n     # Next window
Ctrl+b p     # Previous window
Ctrl+b 0-9   # Switch to window by number
Ctrl+b ,     # Rename window
Ctrl+b &     # Kill window

# Pane Management
Ctrl+b %     # Split vertically
Ctrl+b "     # Split horizontally
Ctrl+b arrow # Navigate panes
Ctrl+b o     # Cycle through panes
Ctrl+b x     # Kill pane
Ctrl+b z     # Toggle pane zoom
Ctrl+b {/}   # Move pane left/right
```

#### tmux Configuration (~/.tmux.conf)
```bash
# Enable mouse support
set -g mouse on

# Set scrollback buffer size
set -g history-limit 10000

# Start window numbering at 1
set -g base-index 1

# Reload config
bind r source-file ~/.tmux.conf \; display "Config reloaded!"

# Better splitting shortcuts
bind | split-window -h
bind - split-window -v

# Status bar customization
set -g status-bg black
set -g status-fg white
set -g status-left '#[fg=green]#S '
set -g status-right '#[fg=yellow]%H:%M %d-%b-%y'
```

### GNU Screen Setup and Usage

#### Installation
```bash
# Ubuntu/Debian
sudo apt-get install screen

# macOS
brew install screen
```

#### Basic Screen Commands
```bash
# Start new session
screen

# Start named session
screen -S inventory-sync

# List sessions
screen -ls

# Reattach to session
screen -r inventory-sync

# Detach from session
# Press: Ctrl+a, then d
```

#### Screen Key Bindings (Default prefix: Ctrl+a)
```
# Session Management
Ctrl+a d     # Detach
Ctrl+a :quit # Quit screen

# Window Management
Ctrl+a c     # Create new window
Ctrl+a n     # Next window
Ctrl+a p     # Previous window
Ctrl+a 0-9   # Switch to window by number
Ctrl+a A     # Rename window
Ctrl+a k     # Kill window

# Split Screen
Ctrl+a S     # Split horizontally
Ctrl+a |     # Split vertically
Ctrl+a Tab   # Move between regions
Ctrl+a X     # Remove current region
```

## Warp Terminal Features

Warp provides built-in features for managing multiple terminal sessions without external multiplexers.

### Split Panes

#### Creating Split Panes
```
# Keyboard shortcuts
Cmd+D        # Split pane vertically
Cmd+Shift+D  # Split pane horizontally

# Or use the command palette
Cmd+P → "Split Pane"
```

#### Navigating Split Panes
```
Cmd+Option+Arrow  # Move between panes
Cmd+[/]          # Focus previous/next pane
```

#### Managing Split Panes
```
Cmd+W            # Close current pane
Cmd+Shift+W      # Close all panes in tab
Drag borders     # Resize panes
```

### Tabs

#### Tab Management
```
Cmd+T            # New tab
Cmd+Shift+T      # Reopen closed tab
Cmd+1-9          # Switch to tab by number
Cmd+Tab          # Cycle through tabs
Cmd+Shift+[/]    # Move to previous/next tab
```

#### Tab Organization
- Name tabs descriptively (right-click → Rename)
- Group related processes in the same tab
- Use color coding for different projects

## Process Management and Job Control

### Basic Job Control
```bash
# Run command in background
npm run dev &

# List jobs
jobs

# Bring job to foreground
fg %1

# Send job to background
bg %1

# Suspend current process
Ctrl+Z

# Kill job
kill %1
```

### Process Management Commands
```bash
# List all processes
ps aux

# List processes in tree format
pstree

# Find process by name
pgrep node

# Kill process by name
pkill node

# Monitor processes in real-time
top
htop  # Enhanced version (install separately)

# Show process details
ps aux | grep node
```

## Running Background Processes

### Using nohup
```bash
# Run process that survives terminal closure
nohup npm run dev > output.log 2>&1 &

# Check if still running
ps aux | grep npm
```

### Using disown
```bash
# Start process
npm run dev &

# Disown the process
disown %1

# Or disown all background jobs
disown -a
```

### Using systemd (for services)
```bash
# Create service file
sudo nano /etc/systemd/system/inventory-sync.service

# Service content example:
[Unit]
Description=Inventory Sync Service
After=network.target

[Service]
Type=simple
User=brend
WorkingDirectory=/home/brend/inventorysync-shopify-app
ExecStart=/usr/bin/npm run start
Restart=on-failure

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable inventory-sync
sudo systemctl start inventory-sync
sudo systemctl status inventory-sync
```

### Using PM2 (for Node.js apps)
```bash
# Install PM2
npm install -g pm2

# Start application
pm2 start npm --name "inventory-sync" -- run start

# List processes
pm2 list

# Monitor processes
pm2 monit

# View logs
pm2 logs inventory-sync

# Save process list
pm2 save

# Setup startup script
pm2 startup
```

## Monitoring Multiple Processes

### Using watch
```bash
# Monitor command output
watch -n 2 'ps aux | grep node'

# Monitor file changes
watch -n 1 'ls -la /var/log/'
```

### Using tail for logs
```bash
# Follow single log
tail -f app.log

# Follow multiple logs
tail -f app.log error.log

# With colors (using multitail)
multitail app.log -i error.log
```

### Process Monitoring Tools
```bash
# htop - Interactive process viewer
htop

# iotop - I/O monitoring
sudo iotop

# nethogs - Network traffic by process
sudo nethogs

# glances - System overview
glances
```

### Custom Monitoring Script
```bash
#!/bin/bash
# monitor.sh - Monitor multiple services

clear
while true; do
    echo "=== System Status ==="
    echo "Date: $(date)"
    echo ""
    
    echo "=== Memory Usage ==="
    free -h | grep -E "Mem:|Swap:"
    echo ""
    
    echo "=== Node Processes ==="
    ps aux | grep node | grep -v grep
    echo ""
    
    echo "=== Port Usage ==="
    netstat -tuln | grep -E "3000|8080|5432"
    echo ""
    
    sleep 5
    clear
done
```

## Best Practices for Terminal Organization

### 1. Naming Conventions
```bash
# tmux sessions
tmux new -s project-frontend
tmux new -s project-backend
tmux new -s project-database

# Screen sessions
screen -S dev-server
screen -S test-runner
screen -S log-monitor
```

### 2. Window/Pane Organization
```
Layout Example:
┌─────────────────┬─────────────────┐
│ Dev Server      │ Test Runner     │
│ npm run dev     │ npm test:watch  │
├─────────────────┼─────────────────┤
│ Git Status      │ Logs            │
│ watch git status│ tail -f app.log │
└─────────────────┴─────────────────┘
```

### 3. Color Coding
- Use different terminal themes for different environments
- Set PS1 prompt colors based on environment
- Use tmux status bar colors for visual distinction

### 4. Workspace Templates

Create reusable tmux scripts:
```bash
#!/bin/bash
# dev-workspace.sh

tmux new-session -d -s dev
tmux rename-window -t dev:0 'main'
tmux send-keys -t dev:0 'cd ~/inventorysync-shopify-app' C-m

tmux new-window -t dev:1 -n 'server'
tmux send-keys -t dev:1 'cd ~/inventorysync-shopify-app && npm run dev' C-m

tmux new-window -t dev:2 -n 'tests'
tmux send-keys -t dev:2 'cd ~/inventorysync-shopify-app && npm run test:watch' C-m

tmux new-window -t dev:3 -n 'logs'
tmux split-window -t dev:3 -h
tmux send-keys -t dev:3.0 'tail -f logs/app.log' C-m
tmux send-keys -t dev:3.1 'tail -f logs/error.log' C-m

tmux attach-session -t dev
```

### 5. Session Persistence
```bash
# Save tmux session state
tmux-resurrect  # Plugin for saving/restoring sessions

# Create session backup script
#!/bin/bash
tmux list-windows -t dev -F "#{window_index} #{window_name} #{pane_current_path}" > ~/.tmux-session-backup
```

## VS Code Terminal Integration

### Built-in Terminal Features
```
# Keyboard shortcuts
Ctrl+`           # Toggle terminal
Ctrl+Shift+`     # Create new terminal
Ctrl+Shift+5     # Split terminal
Alt+Arrow        # Navigate between terminals
```

### Terminal Profiles
Add to VS Code settings.json:
```json
{
  "terminal.integrated.profiles.linux": {
    "bash": {
      "path": "bash",
      "args": []
    },
    "tmux": {
      "path": "tmux",
      "args": ["new-session", "-A", "-s", "vscode"]
    },
    "zsh": {
      "path": "zsh",
      "args": []
    }
  },
  "terminal.integrated.defaultProfile.linux": "bash"
}
```

### Task Runner Integration
Create `.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Dev Server",
      "type": "shell",
      "command": "npm run dev",
      "group": "build",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "npm test",
      "group": "test",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Watch Logs",
      "type": "shell",
      "command": "tail -f logs/*.log",
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    }
  ]
}
```

### Extensions for Terminal Enhancement
- **Terminal Tabs**: Better terminal tab management
- **Shell Launcher**: Quick access to different shells
- **Remote - SSH**: Manage remote terminals
- **Live Share**: Share terminal sessions

### Workspace-specific Terminal Setup
`.vscode/settings.json`:
```json
{
  "terminal.integrated.env.linux": {
    "PROJECT_ROOT": "${workspaceFolder}",
    "NODE_ENV": "development"
  },
  "terminal.integrated.cwd": "${workspaceFolder}",
  "terminal.integrated.shell.linux": "/bin/bash",
  "terminal.integrated.shellArgs.linux": ["-l"]
}
```

## Quick Reference

### Essential Commands Cheatsheet
```bash
# tmux
tmux new -s name          # New session
tmux ls                   # List sessions
tmux attach -t name       # Attach to session
Ctrl+b d                  # Detach

# Screen
screen -S name            # New session
screen -ls                # List sessions
screen -r name            # Reattach
Ctrl+a d                  # Detach

# Job Control
command &                 # Run in background
jobs                      # List jobs
fg %1                     # Foreground job 1
bg %1                     # Background job 1
Ctrl+Z                    # Suspend current job

# Process Management
ps aux | grep process     # Find process
kill -9 PID              # Force kill process
pkill process_name       # Kill by name
htop                     # Interactive process viewer
```

### Common Workflows

1. **Development Setup**
   - Terminal 1: Development server
   - Terminal 2: Test runner
   - Terminal 3: Git operations
   - Terminal 4: Log monitoring

2. **Debugging Setup**
   - Terminal 1: Application with debug flags
   - Terminal 2: Log tail
   - Terminal 3: Database client
   - Terminal 4: System monitoring

3. **Deployment Setup**
   - Terminal 1: Local development
   - Terminal 2: SSH to staging
   - Terminal 3: SSH to production
   - Terminal 4: Monitoring dashboard

Remember: The key to effective multi-terminal workflow is consistency in organization and using the right tool for your specific needs. Whether you prefer tmux, screen, Warp's built-in features, or VS Code's integrated terminal, establish patterns that work for your development style.
