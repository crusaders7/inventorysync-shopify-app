#!/usr/bin/env python3
"""Fix lowercase JSX component tags in CustomFieldsManager.jsx"""

import re

def fix_jsx_casing(file_path):
    """Fix lowercase component tags to proper casing"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # Fix lowercase opening tags
    patterns = [
        (r'<blockStack(\s|>)', r'<BlockStack\1'),
        (r'</blockStack>', r'</BlockStack>'),
        (r'<inlineStack(\s|>)', r'<InlineStack\1'),
        (r'</inlineStack>', r'</InlineStack>'),
    ]
    
    for pattern, replacement in patterns:
        matches = re.findall(pattern, content)
        if matches:
            changes_made.append(f"Found {len(matches)} instances of pattern: {pattern}")
            content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed JSX casing in {file_path}")
        for change in changes_made:
            print(f"  - {change}")
    else:
        print(f"✅ No lowercase component tags found in {file_path}")

if __name__ == "__main__":
    file_path = "/home/brend/inventorysync-shopify-app/frontend/src/components/CustomFieldsManager.jsx"
    fix_jsx_casing(file_path)
