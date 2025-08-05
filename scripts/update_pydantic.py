#!/usr/bin/env python3

import re

file_path = '/home/azureuser/cloudfiles/code/Users/Abhishek.Chhetri/banking-ai-hackathon/app/schemas/ai.py'

with open(file_path, 'r') as file:
    content = file.read()

# Update all 'schema_extra' to 'json_schema_extra'
content = re.sub(r'schema_extra\s*=', 'json_schema_extra =', content)

# Update all references to Config.schema_extra to Config.json_schema_extra
content = re.sub(r'Config\.schema_extra', 'Config.json_schema_extra', content)

# Update all allow_population_by_field_name to validate_by_name
content = re.sub(r'allow_population_by_field_name\s*=', 'validate_by_name =', content)

# Update all orm_mode to from_attributes
content = re.sub(r'orm_mode\s*=', 'from_attributes =', content)

with open(file_path, 'w') as file:
    file.write(content)

print("File updated successfully!")
