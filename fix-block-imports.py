#!/usr/bin/env python3
"""
Remove invalid Block imports from React components
"""

import os
import re
import glob

def fix_block_imports(content):
    """Remove Block from imports since it's not a valid Polaris component"""
    # Pattern to match imports that include Block
    pattern = r"(import\s*{\s*[^}]*?)\s*,?\s*Block\s*,?\s*([^}]*}\s*from\s*['\"]@shopify/polaris['\"];)"
    
    def fix_import(match):
        before = match.group(1).strip()
        after = match.group(2).strip()
        
        # Clean up any double commas
        full_import = before + ", " + after
        full_import = re.sub(r',\s*,', ',', full_import)
        full_import = re.sub(r'{\s*,', '{', full_import)
        full_import = re.sub(r',\s*}', '}', full_import)
        
        return full_import
    
    content = re.sub(pattern, fix_import, content)
    
    # Also fix any lowercase blockStack to BlockStack
    content = re.sub(r'<blockStack', '<BlockStack', content)
    content = re.sub(r'</blockStack>', '</BlockStack>', content)
    
    return content

def fix_file(file_path):
    """Fix a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content = fix_block_imports(content)
        
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
    print("🔧 Removing invalid Block imports from React components...")
    
    # Find all React component files
    frontend_path = "/home/brend/inventorysync-shopify-app/frontend/src"
    react_files = []
    for pattern in ['**/*.jsx', '**/*.js']:
        react_files.extend(glob.glob(os.path.join(frontend_path, pattern), recursive=True))
    
    fixed_count = 0
    for file_path in react_files:
        if fix_file(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files!")

if __name__ == "__main__":
    main()
