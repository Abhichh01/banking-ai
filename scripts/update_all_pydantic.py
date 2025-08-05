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
    if 'orm_mode =' in content or 'schema_extra =' in content or 'allow_population_by_field_name =' in content:
        # Perform replacements
        content = content.replace('orm_mode =', 'from_attributes =')
        content = content.replace('allow_population_by_field_name =', 'validate_by_name =')
        content = content.replace('schema_extra =', 'json_schema_extra =')
        
        # Write the updated content back to the file
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
