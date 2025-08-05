#!/usr/bin/env python3

file_path = '/home/azureuser/cloudfiles/code/Users/Abhishek.Chhetri/banking-ai-hackathon/app/schemas/ai.py'

with open(file_path, 'r') as file:
    content = file.read()

# Fix json_json_schema_extra
content = content.replace('json_json_schema_extra', 'json_schema_extra')

with open(file_path, 'w') as file:
    file.write(content)

print("Fixed json_json_schema_extra issue")
