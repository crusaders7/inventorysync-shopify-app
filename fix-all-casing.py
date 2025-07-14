#!/usr/bin/env python3
"""Fix all lowercase JSX component tags across all files"""

import os
import re
from pathlib import Path

def fix_jsx_casing(file_path):
    """Fix lowercase component tags to proper casing"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  ❌ Error reading {file_path}: {e}")
        return False
    
    original_content = content
    changes_made = []
    
    # Fix lowercase tags
    patterns = [
        (r'<blockStack(\s|>)', r'<BlockStack\1'),
        (r'</blockStack>', r'</BlockStack>'),
        (r'<inlineStack(\s|>)', r'<InlineStack\1'),
        (r'</inlineStack>', r'</InlineStack>'),
        (r'<formLayout(\s|>)', r'<FormLayout\1'),
        (r'</formLayout>', r'</FormLayout>'),
    ]
    
    for pattern, replacement in patterns:
        matches = re.findall(pattern, content)
        if matches:
            changes_made.append(f"Found {len(matches)} instances of pattern: {pattern}")
            content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed JSX casing in {file_path}")
            for change in changes_made:
                print(f"  - {change}")
            return True
        except Exception as e:
            print(f"  ❌ Error writing {file_path}: {e}")
            return False
    return False

def find_jsx_files(root_dir):
    """Find all JSX and JS files in the project"""
    jsx_files = []
    for path in Path(root_dir).rglob('*.jsx'):
        if 'node_modules' not in str(path) and '.vite' not in str(path):
            jsx_files.append(path)
    for path in Path(root_dir).rglob('*.js'):
        if 'node_modules' not in str(path) and '.vite' not in str(path):
            jsx_files.append(path)
    return jsx_files

if __name__ == "__main__":
    root_dir = "/home/brend/inventorysync-shopify-app/frontend"
    print(f"🔍 Searching for JSX files in {root_dir}...")
    
    jsx_files = find_jsx_files(root_dir)
    print(f"📁 Found {len(jsx_files)} JSX/JS files to check\n")
    
    fixed_count = 0
    for file_path in jsx_files:
        if fix_jsx_casing(file_path):
            fixed_count += 1
    
    print(f"\n✨ Fixed {fixed_count} files with casing issues")
