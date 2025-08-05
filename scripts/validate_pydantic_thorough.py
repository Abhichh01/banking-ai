#!/usr/bin/env python3

import os
import re
from pathlib import Path

# Define the schemas directory
schemas_dir = '/home/azureuser/cloudfiles/code/Users/Abhishek.Chhetri/banking-ai-hackathon/app/schemas'

# Track files that need updating
files_to_update = []

# Check all Python files in the schemas directory
for file_path in Path(schemas_dir).glob('*.py'):
    file_path_str = str(file_path)
    with open(file_path, 'r') as file:
        content = file.read()
        
        # Prepare patterns for checking
        patterns = [
            r'\borm_mode\b', 
            r'\bschema_extra\b', 
            r'\ballow_population_by_field_name\b',
            r'Config\.schema_extra',
            r'json_json_schema_extra'
        ]
        
        # Check for any deprecated patterns
        for pattern in patterns:
            if re.search(pattern, content):
                if file_path_str not in files_to_update:
                    files_to_update.append(file_path_str)
                print(f"Found pattern '{pattern}' in {file_path_str}")

# Report findings
if files_to_update:
    print(f"\nFound {len(files_to_update)} files that need updating:")
    for file in files_to_update:
        print(f"  - {file}")
else:
    print("All schema files are using Pydantic v2 configurations!")
