"""
Temporary fix for the JSONB error in account.py.

Run this script to modify the Card class in account.py
to use JSON instead of JSONB.
"""

from pathlib import Path
import sys

# Find the account.py file in the execution environment
account_file_path = "/mnt/batch/tasks/shared/LS_root/mounts/clusters/hackathon-ai/code/Users/Abhishek.Chhetri/banking-ai-hackathon/app/models/account.py"

if not Path(account_file_path).exists():
    print(f"Error: Could not find {account_file_path}")
    sys.exit(1)

# Read the file
with open(account_file_path, 'r') as f:
    content = f.read()

# Replace JSONB with JSON in the file
modified_content = content.replace('JSONB,', 'JSON,')

# Write the file back
with open(account_file_path, 'w') as f:
    f.write(modified_content)

print(f"Successfully replaced JSONB with JSON in {account_file_path}")
print("Please try importing the Account model again.")
