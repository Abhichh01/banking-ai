"""
Quick fix script to replace JSONB with JSON in account.py.
This addresses the NameError related to JSONB.
"""

import re

# Path to the account.py file
file_path = "/home/azureuser/cloudfiles/code/Users/Abhishek.Chhetri/banking-ai-hackathon/app/models/account.py"

# Read the file content
with open(file_path, 'r') as file:
    content = file.read()

# Replace any occurrence of JSONB in column definitions with JSON
# This pattern looks for Column( followed by parameters including JSONB
modified_content = re.sub(r'Column\((.*?)JSONB(.*?)\)', r'Column(\1JSON\2)', content)

# Write back to the file
with open(file_path, 'w') as file:
    file.write(modified_content)

print("Fixed: Replaced JSONB with JSON in column definitions")
