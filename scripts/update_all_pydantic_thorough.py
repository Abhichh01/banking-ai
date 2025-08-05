#!/usr/bin/env python3

import os
import re
from pathlib import Path

# Define the schemas directory
schemas_dir = '/home/azureuser/cloudfiles/code/Users/Abhishek.Chhetri/banking-ai-hackathon/app/schemas'

# Track files updated
files_updated = []

# Update all Python files in the schemas directory
for file_path in Path(schemas_dir).glob('*.py'):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Check if file needs updating
    original_content = content
    
    # Fix lines with Config class definitions and Pydantic configurations
    content = re.sub(r'orm_mode\s*=', 'from_attributes =', content)
    content = re.sub(r'allow_population_by_field_name\s*=', 'validate_by_name =', content)
    content = re.sub(r'schema_extra\s*=', 'json_schema_extra =', content)
    
    # Check for references to schema_extra in dictionaries
    content = re.sub(r'Config\.schema_extra', 'Config.json_schema_extra', content)
    
    # Only update if changes were made
    if content != original_content:
        with open(file_path, 'w') as file:
            file.write(content)
        files_updated.append(str(file_path))

# Report results
if files_updated:
    print(f"Updated {len(files_updated)} files:")
    for file in files_updated:
        print(f"  - {file}")
else:
    print("No files needed updating.")
