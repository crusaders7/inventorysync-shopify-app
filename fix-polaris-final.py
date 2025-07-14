#!/usr/bin/env python3
"""
Final comprehensive fix for all Polaris import and component issues
"""

import os
import re
import glob

def fix_polaris_completely(content):
    """Fix all invalid imports and components from Polaris"""
    
    # List of invalid imports to remove or replace
    replacements = {
        'Block': None,  # Remove completely
        'Inline': 'InlineStack',  # Replace with InlineStack
        'Stack': 'BlockStack',  # Replace with BlockStack (vertical stacks)
    }
    
    # First, let's fix the imports
    import_pattern = r"(import\s*{[^}]+}\s*from\s*['\"]@shopify/polaris['\"];)"
    
    def fix_import(match):
        import_statement = match.group(1)
        
        # Replace invalid imports
        for old, new in replacements.items():
            if new:
                # Replace with new component
                import_statement = re.sub(r'\b' + old + r'\b', new, import_statement)
            else:
                # Remove the component completely
                import_statement = re.sub(r',?\s*' + old + r'\s*,?', '', import_statement)
        
        # Clean up any double commas or leading/trailing commas
        import_statement = re.sub(r',\s*,', ',', import_statement)
        import_statement = re.sub(r'{\s*,', '{', import_statement)
        import_statement = re.sub(r',\s*}', '}', import_statement)
        # Clean up extra spaces
        import_statement = re.sub(r'\s+', ' ', import_statement)
        
        return import_statement
    
    content = re.sub(import_pattern, fix_import, content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix lowercase component names in JSX
    content = re.sub(r'<blockStack\b', '<BlockStack', content)
    content = re.sub(r'</blockStack>', '</BlockStack>', content)
    
    content = re.sub(r'<inlineStack\b', '<InlineStack', content)
    content = re.sub(r'</inlineStack>', '</InlineStack>', content)
    
    # Fix any Stack components to BlockStack
    content = re.sub(r'<Stack\b', '<BlockStack', content)
    content = re.sub(r'</Stack>', '</BlockStack>', content)
    
    # Fix any Inline components to InlineStack
    content = re.sub(r'<Inline\b', '<InlineStack', content)
    content = re.sub(r'</Inline>', '</InlineStack>', content)
    
    return content

def fix_file(file_path):
    """Fix a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content = fix_polaris_completely(content)
        
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
    print("🔧 Running final comprehensive fix for Polaris imports and components...")
    
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
    
    # Check for any remaining issues
    print("\n🔍 Checking for remaining issues...")
    issues_found = False
    
    for file_path in react_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if '@shopify/polaris' in content:
                    # Check for invalid imports
                    if re.search(r'\b(Block|Inline|Stack)\b.*from.*@shopify/polaris', content):
                        print(f"⚠️  Still has issues: {os.path.basename(file_path)}")
                        issues_found = True
                    # Check for lowercase components
                    if re.search(r'<(blockStack|inlineStack)\b', content):
                        print(f"⚠️  Has lowercase components: {os.path.basename(file_path)}")
                        issues_found = True
        except:
            pass
    
    if not issues_found:
        print("✅ All files are clean!")

if __name__ == "__main__":
    main()
