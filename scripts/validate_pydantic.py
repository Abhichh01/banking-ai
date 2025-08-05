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
    with open(file_path, 'r') as file:
        content = file.read()
        
        # Check for deprecated Pydantic v1 configurations
        if 'orm_mode =' in content or 'schema_extra =' in content or 'allow_population_by_field_name =' in content:
            files_to_update.append(str(file_path))

# Report findings
if files_to_update:
    print(f"Found {len(files_to_update)} files that need updating:")
    for file in files_to_update:
        print(f"  - {file}")
else:
    print("All schema files are using Pydantic v2 configurations!")
