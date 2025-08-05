#!/usr/bin/env python3

import os
from pathlib import Path

# Define the schemas directory
schemas_dir = '/home/azureuser/cloudfiles/code/Users/Abhishek.Chhetri/banking-ai-hackathon/app/schemas'

# Track files updated
files_updated = []

# Fix all Python files in the schemas directory
for file_path in Path(schemas_dir).glob('*.py'):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Check if file needs updating
    if 'json_json_schema_extra' in content:
        # Fix the double json prefix
        content = content.replace('json_json_schema_extra', 'json_schema_extra')
        
        # Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.write(content)
        
        files_updated.append(str(file_path))

# Report results
if files_updated:
    print(f"Fixed {len(files_updated)} files:")
    for file in files_updated:
        print(f"  - {file}")
else:
    print("No files needed fixing.")
