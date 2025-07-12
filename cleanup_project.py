#!/usr/bin/env python3
"""
Clean up unused files and optimize the codebase for Shopify marketplace
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Files to definitely keep
KEEP_FILES = {
    # Core backend files
    'backend/main.py',
    'backend/models.py',
    'backend/database.py',
    'backend/config.py',
    'backend/requirements.txt',
    'backend/.env',
    'backend/alembic.ini',
    
    # API endpoints
    'backend/api/',
    
    # Core utilities
    'backend/utils/',
    
    # Frontend core
    'frontend/src/App.jsx',
    'frontend/src/main.jsx',
    'frontend/src/components/',
    'frontend/package.json',
    'frontend/vite.config.js',
    
    # Documentation
    'README.md',
    '.gitignore',
}

# Files that are likely test/development only
CLEANUP_PATTERNS = [
    # Test files
    r'test_.*\.py$',
    r'.*_test\.py$',
    r'oauth_test\.py$',
    
    # Fix/migration scripts
    r'fix_.*\.py$',
    r'create_test_.*\.py$',
    
    # Old/simple versions
    r'.*_simple\.py$',
    r'simple_.*\.py$',
    
    # Database setup scripts (keep migrations)
    r'database_setup\.py$',
    r'init_db\.py$',
    r'setup_store\.py$',
    
    # Sync scripts (if redundant)
    r'sync_.*\.py$',
    r'update_.*\.py$',
]

# Files to move to a scripts/dev folder
DEV_SCRIPTS = [
    'configure_shopify_webhooks.py',
    'create_webhook_handlers.py',
    'database_manager.py',
    'industry_templates.py',
    'multi_location_sync.py',
]

def analyze_imports(file_path):
    """Analyze Python imports to understand dependencies"""
    imports = set()
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            # Find all imports
            import_matches = re.findall(r'(?:from|import)\s+(\w+)', content)
            imports.update(import_matches)
    except:
        pass
    return imports

def find_unused_files(root_dir):
    """Find potentially unused files"""
    unused_files = []
    dev_files = []
    test_files = []
    
    for root, dirs, files in os.walk(root_dir):
        # Skip node_modules and .git
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', '.vite']]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, root_dir)
            
            # Skip if in keep list
            if any(keep in rel_path for keep in KEEP_FILES):
                continue
            
            # Check if it matches cleanup patterns
            for pattern in CLEANUP_PATTERNS:
                if re.search(pattern, file):
                    if 'test' in file.lower():
                        test_files.append(rel_path)
                    else:
                        unused_files.append(rel_path)
                    break
            
            # Check if it's a dev script
            if file in DEV_SCRIPTS:
                dev_files.append(rel_path)
    
    return unused_files, dev_files, test_files

def generate_cleanup_report(root_dir):
    """Generate a report of files to clean up"""
    unused, dev, test = find_unused_files(root_dir)
    
    report = []
    report.append("# InventorySync Cleanup Report\n")
    report.append(f"Total files to review: {len(unused) + len(dev) + len(test)}\n")
    
    if unused:
        report.append("\n## Potentially Unused Files (can be deleted):")
        for f in sorted(unused):
            report.append(f"  - {f}")
    
    if dev:
        report.append("\n\n## Development Scripts (move to scripts/dev):")
        for f in sorted(dev):
            report.append(f"  - {f}")
    
    if test:
        report.append("\n\n## Test Files (move to tests/ or remove if not needed):")
        for f in sorted(test):
            report.append(f"  - {f}")
    
    # Analyze JavaScript files
    report.append("\n\n## Frontend Analysis:")
    fix_scripts = []
    for root, dirs, files in os.walk(os.path.join(root_dir, 'frontend')):
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', '.vite']]
        for file in files:
            if file.startswith('fix-') and file.endswith('.py'):
                fix_scripts.append(os.path.relpath(os.path.join(root, file), root_dir))
    
    if fix_scripts:
        report.append("\n### Fix Scripts in Frontend (can be deleted):")
        for f in sorted(fix_scripts):
            report.append(f"  - {f}")
    
    return '\n'.join(report)

if __name__ == "__main__":
    root_dir = "/home/brend/inventorysync-shopify-app"
    report = generate_cleanup_report(root_dir)
    
    # Save report
    with open(os.path.join(root_dir, "CLEANUP_REPORT.md"), 'w') as f:
        f.write(report)
    
    print(report)
    print(f"\n✅ Report saved to CLEANUP_REPORT.md")
