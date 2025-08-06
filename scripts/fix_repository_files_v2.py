#!/usr/bin/env python3
"""
This script performs a thorough cleanup of all repository files in the banking-ai-hackathon project.
It fixes syntax errors, broken try-except blocks, incorrect return values, and other issues.
"""
import os
import re
import sys

# Repository directory
repo_dir = "/home/azureuser/cloudfiles/code/Users/Abhishek.Chhetri/banking-ai-hackathon/app/repositories"

# Get all Python files in the repository directory
repo_files = [os.path.join(repo_dir, f) for f in os.listdir(repo_dir) 
              if f.endswith('.py') and f != '__init__.py' and not os.path.isdir(os.path.join(repo_dir, f))]

def fix_file(file_path):
    """Fix issues in a single file"""
    print(f"Processing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Save original content for comparison
    original_content = content
    
    # Fix SQLAlchemy imports - add or_ if missing
    if 'from sqlalchemy import' in content and 'or_' not in content:
        content = re.sub(
            r'from sqlalchemy import ([^\n]+)',
            r'from sqlalchemy import \1, or_',
            content
        )
    
    # Fix broken error logging strings
    content = re.sub(
        r'logger\.error\(f"Error: \{\{f"([^"]+): \{str\(e\}\}")',
        r'logger.error(f"\1: {str(e)}")',
        content
    )
    
    # Fix multiple return statements in exception handling
    content = re.sub(
        r'(except Exception as e:.*?logger\.error\([^)]+\))\s+return None\s+logger\.error\([^)]+\)\s+return None',
        r'\1\n        return None',
        content,
        flags=re.DOTALL
    )
    
    # Fix return dict/list comments
    content = re.sub(
        r'return None # dict # list\}?"?\)?',
        r'return {}',
        content
    )
    
    # Fix return None with extra characters
    content = re.sub(
        r'return None\}?"?\)?',
        r'return None',
        content
    )
    
    # Fix incomplete method definition in enhanced_account.py
    if 'enhanced_account.py' in file_path and 'async def get_account_analytics(' in content:
        content = re.sub(
            r'async def get_account_analytics\([^)]*\)\s*:[\s\n]*try:',
            r'async def get_account_analytics(\n        self,\n        account_id: int,\n        time_range: str = "30d"\n    ) -> Dict[str, Any]:\n        try:',
            content
        )
    
    # Fix duplicate code in enhanced_account.py
    if 'enhanced_account.py' in file_path:
        content = re.sub(
            r'(return analytics_result\s+except Exception as e:[^}]*})\s+return analytics_result\s+return None\s+logger\.error\([^)]*\)\s+return None',
            r'\1\n            return {}',
            content
        )
    
    # Ensure Dict methods return {} on error
    content = re.sub(
        r'(async def \w+\([^)]*\)\s*->\s*Dict\[[^]]+\]:.*?)(except Exception as e:.*?logger\.error\([^)]*\))((\s+return None|\s*))',
        r'\1\2\n        return {}',
        content,
        flags=re.DOTALL
    )
    
    # Ensure List methods return [] on error
    content = re.sub(
        r'(async def \w+\([^)]*\)\s*->\s*List\[[^]]+\]:.*?)(except Exception as e:.*?logger\.error\([^)]*\))((\s+return None|\s*))',
        r'\1\2\n        return []',
        content,
        flags=re.DOTALL
    )
    
    # If content was modified, write it back to the file
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Fixed and saved: {file_path}")
    else:
        print(f"  No changes needed: {file_path}")

def main():
    """Main function to fix all repository files"""
    print(f"Found {len(repo_files)} repository files to process")
    
    for file_path in repo_files:
        fix_file(file_path)
    
    print("Repository cleanup complete!")

if __name__ == "__main__":
    main()
