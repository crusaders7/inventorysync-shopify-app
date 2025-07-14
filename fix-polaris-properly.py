#!/usr/bin/env python3
"""
Properly fix all Polaris components - ensure imports match usage
"""

import os
import re
import glob

def get_polaris_components_used(content):
    """Extract all Polaris components actually used in JSX"""
    # Find all <ComponentName> tags
    component_pattern = r'<([A-Z][a-zA-Z]+)(?:\s|>|/)'
    components = set(re.findall(component_pattern, content))
    
    # Filter to only known Polaris components
    polaris_components = {
        'Page', 'Layout', 'Card', 'Button', 'TextField', 'Select', 
        'DataTable', 'Badge', 'Icon', 'Text', 'Modal', 'Form', 
        'FormLayout', 'Checkbox', 'Toast', 'Frame', 'Banner',
        'Tabs', 'EmptyState', 'Spinner', 'Loading', 'Divider',
        'List', 'Popover', 'RadioButton', 'ChoiceList', 'Filters',
        'Stack', 'BlockStack', 'InlineStack', 'ButtonGroup', 'Tag',
        'TextContainer', 'ProgressBar', 'Pagination', 'ResourceList',
        'ResourceItem', 'Thumbnail', 'DisplayText', 'Caption',
        'DatePicker', 'ColorPicker', 'RangeSlider', 'Grid'
    }
    
    return components.intersection(polaris_components)

def fix_polaris_file(file_path):
    """Fix a single file - ensure imports match actual usage"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if no Polaris imports
        if '@shopify/polaris' not in content:
            return False
            
        original_content = content
        
        # First, fix any lowercase component usage in JSX
        content = re.sub(r'<blockStack\b', '<BlockStack', content)
        content = re.sub(r'</blockStack>', '</BlockStack>', content)
        content = re.sub(r'<inlineStack\b', '<InlineStack', content) 
        content = re.sub(r'</inlineStack>', '</InlineStack>', content)
        
        # Replace Stack with BlockStack in JSX (Stack is not a valid component)
        content = re.sub(r'<Stack\b', '<BlockStack', content)
        content = re.sub(r'</Stack>', '</BlockStack>', content)
        
        # Replace Inline with InlineStack in JSX
        content = re.sub(r'<Inline\b', '<InlineStack', content)
        content = re.sub(r'</Inline>', '</InlineStack>', content)
        
        # Now find what components are actually used
        components_used = get_polaris_components_used(content)
        
        # Find existing import statement
        import_match = re.search(r'import\s*{([^}]+)}\s*from\s*[\'"]@shopify/polaris[\'"];', content)
        
        if import_match and components_used:
            # Get currently imported components
            current_imports = import_match.group(1)
            imported = set(comp.strip() for comp in current_imports.split(','))
            
            # Remove invalid imports
            invalid = {'Block', 'Inline', 'Stack'}
            imported = imported - invalid
            
            # Add all components that are used
            imported.update(components_used)
            
            # Build new import statement
            sorted_imports = sorted(imported)
            new_import = f"import {{ {', '.join(sorted_imports)} }} from '@shopify/polaris';"
            
            # Replace the import
            content = re.sub(
                r'import\s*{[^}]+}\s*from\s*[\'"]@shopify/polaris[\'"];',
                new_import,
                content
            )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {os.path.basename(file_path)}")
            return True
        
        return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all React component files"""
    print("🔧 Properly fixing all Polaris components and imports...")
    
    frontend_path = "/home/brend/inventorysync-shopify-app/frontend/src"
    react_files = []
    for pattern in ['**/*.jsx', '**/*.js']:
        react_files.extend(glob.glob(os.path.join(frontend_path, pattern), recursive=True))
    
    fixed_count = 0
    for file_path in react_files:
        if fix_polaris_file(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files!")
    
    # Verify no issues remain
    print("\n🔍 Verifying all files...")
    issues = []
    
    for file_path in react_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if '@shopify/polaris' not in content:
                continue
                
            # Check for components used but not imported
            import_match = re.search(r'import\s*{([^}]+)}\s*from\s*[\'"]@shopify/polaris[\'"];', content)
            if import_match:
                imported = set(comp.strip() for comp in import_match.group(1).split(','))
                used = get_polaris_components_used(content)
                
                missing = used - imported
                if missing:
                    issues.append(f"{os.path.basename(file_path)}: Missing imports: {', '.join(missing)}")
                
                # Check for invalid imports
                invalid = imported.intersection({'Block', 'Inline', 'Stack'})
                if invalid:
                    issues.append(f"{os.path.basename(file_path)}: Invalid imports: {', '.join(invalid)}")
                    
        except Exception as e:
            issues.append(f"{os.path.basename(file_path)}: Error checking: {e}")
    
    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ All files are properly configured!")

if __name__ == "__main__":
    main()
