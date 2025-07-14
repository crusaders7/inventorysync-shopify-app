#!/usr/bin/env python3
"""
Fix broken imports in React components
"""

import os
import re
import glob

def fix_broken_imports(content):
    """Fix the broken import statements"""
    # Pattern to match broken imports with "Block\n  Inline" pattern
    pattern = r'import\s*{\s*Block\s*Inline\s*(.*?)\s*}\s*from\s*[\'"]@shopify/polaris[\'"];'
    
    def fix_import(match):
        # Extract the components after "Inline "
        components = match.group(1).strip()
        # Remove duplicate "Block" if it exists at the end
        components = re.sub(r',\s*Block\s*$', '', components)
        # Build the correct import statement
        return f"import {{ {components} }} from '@shopify/polaris';"
    
    # Fix the broken pattern
    content = re.sub(pattern, fix_import, content, flags=re.MULTILINE | re.DOTALL)
    
    # Also fix cases where Block appears on its own line followed by Inline on the next
    pattern2 = r'(import\s*{\s*[^}]*?)\s*Block\s*\n\s*Inline\s*([^}]*}\s*from\s*[\'"]@shopify/polaris[\'"];)'
    
    def fix_import2(match):
        before = match.group(1).strip()
        after = match.group(2).strip()
        # Clean up the components list
        components = before.replace('import {', '').strip()
        if components and not components.endswith(','):
            components += ','
        components += ' ' + after.replace("} from '@shopify/polaris';", '').strip()
        # Remove any duplicate commas or spaces
        components = re.sub(r',\s*,', ',', components)
        components = re.sub(r'\s+', ' ', components)
        # Remove duplicate Block if present
        components = re.sub(r'Block,?\s*Block', 'Block', components)
        return f"import {{ {components} }} from '@shopify/polaris';"
    
    content = re.sub(pattern2, fix_import2, content, flags=re.MULTILINE | re.DOTALL)
    
    return content

def fix_file(file_path):
    """Fix a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content = fix_broken_imports(content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            print(f"⏭️  Skipped: {file_path} (no changes needed)")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Main function to fix all React files"""
    print("🔧 Fixing broken imports in React components...")
    
    # Find all React files with issues
    frontend_path = "/home/brend/inventorysync-shopify-app/frontend/src/components"
    
    # List of files we know have issues
    problem_files = [
        "Dashboard.jsx",
        "Inventory.jsx",
        "Alerts.jsx",
        "AlertsManager.jsx",
        "Settings.jsx",
        "Reports.jsx",
        "Navigation.jsx",
        "BillingSetup.jsx",
        "WorkflowManager.jsx",
        "IndustryTemplates.jsx",
        "ReportsBuilder.jsx"
    ]
    
    fixed_count = 0
    for filename in problem_files:
        file_path = os.path.join(frontend_path, filename)
        if os.path.exists(file_path):
            if fix_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n🎉 Fixed {fixed_count} files!")

if __name__ == "__main__":
    main()
