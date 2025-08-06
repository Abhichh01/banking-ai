#!/usr/bin/env python3
"""
Fix malformed f-strings in repository files.

This script finds and fixes incorrectly nested f-strings in the form:
f"Error: {{f"Some message {var}"}}"

It replaces them with properly formatted strings:
f"Some message {var}"
"""

import sys
import re
import os

def fix_malformed_fstrings(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Pattern to match malformed f-strings like: f"Error: {{f"Message {var}"}}"
    pattern = r'f"Error: \{\{f"([^"]*?)"\}\}"'
    replacement = r'f"\1"'
    
    # Pattern to match malformed f-strings with unclosed braces like: f"Error: {{f"Message {var}"}}
    pattern2 = r'f"Error: \{\{f"([^"]*?)"\}\}'
    
    # Pattern to match malformed f-strings with unclosed quotes
    pattern3 = r'logger\.error\(f"([^"]*?)\{\{f"([^"]*?)\{str\(e\}\}")'
    replacement3 = r'logger.error(f"\2{str(e)}")'
    
    # Apply fixes
    modified_content = re.sub(pattern, replacement, content)
    modified_content = re.sub(pattern3, replacement3, modified_content)
    
    # Fix the pattern: return None # dict
    modified_content = modified_content.replace('return None # dict', 'return {}')
    
    # Fix 'return None' to 'return {}' in methods that should return Dict
    pattern4 = r'return None(\s+# dict)?'
    replacement4 = r'return {}'
    modified_content = re.sub(pattern4, replacement4, modified_content)
    
    # Fix malformed try/except blocks
    # This is a simplified approach - a complete solution would require a parser
    lines = modified_content.split('\n')
    i = 0
    while i < len(lines):
        if 'try:' in lines[i] and i+1 < len(lines) and 'return' in lines[i+1] and not '    ' in lines[i+1]:
            # Likely a malformed try block with return right after
            lines[i+1] = '    ' + lines[i+1]
        i += 1
    
    modified_content = '\n'.join(lines)
    
    if content != modified_content:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(modified_content)
        print(f"Fixed malformed f-strings in {file_path}")
        return True
    else:
        print(f"No changes needed in {file_path}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_fstrings.py <file_path_or_directory>")
        sys.exit(1)
    
    path = sys.argv[1]
    
    if os.path.isfile(path):
        fix_malformed_fstrings(path)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.py'):
                    fix_malformed_fstrings(os.path.join(root, file))
    else:
        print(f"Path not found: {path}")
        sys.exit(1)
