#!/usr/bin/env python3

file_path = '/home/azureuser/cloudfiles/code/Users/Abhishek.Chhetri/banking-ai-hackathon/app/schemas/ai.py'

with open(file_path, 'r') as file:
    content = file.read()

# Update all 'orm_mode' to 'from_attributes'
content = content.replace('orm_mode =', 'from_attributes =')

# Update all 'allow_population_by_field_name' to 'validate_by_name'
content = content.replace('allow_population_by_field_name =', 'validate_by_name =')

with open(file_path, 'w') as file:
    file.write(content)

print("Updated orm_mode and allow_population_by_field_name")
