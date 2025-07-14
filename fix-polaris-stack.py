#!/usr/bin/env python3
"""
Fix Shopify Polaris Stack component deprecation issues
Replaces deprecated Stack with BlockStack and InlineStack
"""

import os
import re
import glob

def fix_polaris_imports(content):
    """Fix import statements to use new components"""
    # Add BlockStack and InlineStack to imports if Stack is present
    if 'Stack' in content and '@shopify/polaris' in content:
        # Find the import statement
        import_pattern = r'(import\s*{[^}]*)(Stack)([^}]*}[^;]*from\s*[\'"]@shopify/polaris[\'"])'
        
        def replace_import(match):
            before = match.group(1)
            after = match.group(3)
            
            # Remove Stack and add BlockStack, InlineStack if not already present
            components = before + after
            if 'BlockStack' not in components:
                components = components.replace('{', '{\n  BlockStack,')
            if 'InlineStack' not in components:
                components = components.replace('BlockStack,', 'BlockStack,\n  InlineStack,')
            
            # Remove the old Stack import
            components = re.sub(r',?\s*Stack,?', '', components)
            
            return components
        
        content = re.sub(import_pattern, replace_import, content, flags=re.MULTILINE | re.DOTALL)
    
    return content

def fix_stack_usage(content):
    """Replace Stack component usage with BlockStack/InlineStack"""
    
    # Replace <Stack vertical> with <BlockStack>
    content = re.sub(
        r'<Stack\s+vertical\s*(?:spacing=["\'](\w+)["\'])?([^>]*)>',
        lambda m: f'<BlockStack gap="{convert_spacing(m.group(1))}">', 
        content
    )
    
    # Replace <Stack> (horizontal) with <InlineStack>
    content = re.sub(
        r'<Stack\s*(?:spacing=["\'](\w+)["\'])?([^>]*)>',
        lambda m: f'<InlineStack gap="{convert_spacing(m.group(1))}">', 
        content
    )
    
    # Replace closing tags
    content = re.sub(r'</Stack>', '</BlockStack>', content)
    content = re.sub(r'</InlineStack>', '</InlineStack>', content)
    
    return content

def convert_spacing(spacing):
    """Convert old spacing values to new gap values"""
    if not spacing:
        return "400"
    
    spacing_map = {
        'extraTight': '100',
        'tight': '200', 
        'loose': '500',
        'extraLoose': '600'
    }
    
    return spacing_map.get(spacing, '400')

def fix_file(file_path):
    """Fix a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_polaris_imports(content)
        content = fix_stack_usage(content)
        
        # Only write if changes were made
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
    print("🔧 Fixing Shopify Polaris Stack deprecation issues...")
    
    # Find all React files in frontend/src
    frontend_path = "/home/brend/inventorysync-shopify-app/frontend/src"
    if not os.path.exists(frontend_path):
        print(f"❌ Frontend path not found: {frontend_path}")
        return
    
    # Get all .jsx and .js files
    react_files = []
    for ext in ['*.jsx', '*.js']:
        react_files.extend(glob.glob(f"{frontend_path}/**/{ext}", recursive=True))
    
    print(f"📁 Found {len(react_files)} React files")
    
    fixed_count = 0
    for file_path in react_files:
        if fix_file(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files!")
    print("\n📝 Manual fixes still needed:")
    print("   - Review complex Stack usage with nested components")
    print("   - Check for spacing/alignment issues")
    print("   - Test components in browser")

if __name__ == "__main__":
    main()