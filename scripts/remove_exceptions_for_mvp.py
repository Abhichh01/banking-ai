#!/usr/bin/env python3
"""
Script to remove custom exceptions from repository files and replace with logging.
This script is part of the MVP preparation process to simplify the codebase.
"""

import os
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path to the repository files
REPO_DIR = Path(__file__).parent.parent
REPOSITORIES_DIR = REPO_DIR / "app" / "repositories"
CORE_DIR = REPO_DIR / "app" / "core"

# Exception import patterns to remove
EXCEPTION_IMPORT_PATTERNS = [
    r'from app\.core\.exceptions import \w+(?:, \w+)*',
    r'from app\.core import exceptions',
    r'from app\.core\.exceptions import \*'
]

# Exception usage patterns to replace
EXCEPTION_PATTERNS = {
    # Pattern for raising custom exceptions
    r'raise (\w+)\(([^)]*)\)': r'logger.error(f"{{\1}}: {{\2}}")\n        return None',
    
    # Pattern for raising custom exceptions with more complex arguments
    r'raise (\w+)\("([^"]+)"\s*\+\s*([^)]+)\)': r'logger.error(f"{\1}: {\2} {{\3}}")\n        return None',
    
    # Custom handling for specific methods based on return type
    r'raise (\w+Error)\(([^)]*)\)\s+# list': r'logger.error(f"{{\1}}: {{\2}}")\n        return []',
    r'raise (\w+Error)\(([^)]*)\)\s+# dict': r'logger.error(f"{{\1}}: {{\2}}")\n        return {}',
    r'raise (\w+Error)\(([^)]*)\)\s+# bool': r'logger.error(f"{{\1}}: {{\2}}")\n        return False',
}

def find_repository_files():
    """Find all enhanced repository files in the repository directory."""
    repository_files = []
    for file in REPOSITORIES_DIR.glob("enhanced_*.py"):
        repository_files.append(file)
    
    logger.info(f"Found {len(repository_files)} enhanced repository files")
    return repository_files

def remove_exception_imports(content):
    """Remove imports of custom exceptions from the file content."""
    for pattern in EXCEPTION_IMPORT_PATTERNS:
        content = re.sub(pattern, '# Exception imports removed for MVP', content)
    
    # Add import for logging if not already present
    if 'import logging' not in content:
        content = re.sub(
            r'import .*?\n', 
            r'\g<0>import logging\n', 
            content, 
            count=1
        )
    
    # Add logger configuration if not already present
    if 'logger = logging.getLogger' not in content:
        content = re.sub(
            r'class .*?:', 
            r'# Configure logger\nlogger = logging.getLogger(__name__)\n\n\g<0>', 
            content, 
            count=1
        )
        
    return content

def replace_exception_raising(content):
    """Replace all custom exception raising with logging and appropriate returns."""
    # First add comments to help with replacing specific return types
    content = add_return_type_comments(content)
    
    # Now replace exceptions with the appropriate patterns
    for pattern, replacement in EXCEPTION_PATTERNS.items():
        content = re.sub(pattern, replacement, content)
    
    # Generic catch for any remaining exception raises
    remaining_exceptions = re.findall(r'raise \w+Error\([^)]*\)', content)
    if remaining_exceptions:
        logger.warning(f"Some exception patterns may not have been replaced: {remaining_exceptions}")
        # Try a more generic replacement
        content = re.sub(
            r'raise (\w+Error)\(([^)]*)\)', 
            r'logger.error(f"{\1}: {\2}")\n        return None', 
            content
        )
    
    return content

def add_return_type_comments(content):
    """Add comments to exception raises to indicate return type based on method context."""
    # Find methods that return lists
    list_methods = re.findall(r'def (\w+)[^:]*:(?:\s+""".*?""")?\s+.*?return \[', content, re.DOTALL)
    for method in list_methods:
        content = re.sub(
            rf'(def {method}.*?raise \w+Error\([^)]*\))', 
            r'\1 # list', 
            content, 
            flags=re.DOTALL
        )
    
    # Find methods that return dictionaries
    dict_methods = re.findall(r'def (\w+)[^:]*:(?:\s+""".*?""")?\s+.*?return \{', content, re.DOTALL)
    for method in dict_methods:
        content = re.sub(
            rf'(def {method}.*?raise \w+Error\([^)]*\))', 
            r'\1 # dict', 
            content, 
            flags=re.DOTALL
        )
    
    # Find methods that return booleans
    bool_methods = re.findall(r'def (\w+)[^:]*:(?:\s+""".*?""")?\s+.*?return (?:True|False)', content, re.DOTALL)
    for method in bool_methods:
        content = re.sub(
            rf'(def {method}.*?raise \w+Error\([^)]*\))', 
            r'\1 # bool', 
            content, 
            flags=re.DOTALL
        )
    
    return content

def process_file(file_path):
    """Process a single repository file to remove exceptions."""
    logger.info(f"Processing {file_path.name}")
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Remove exception imports
        updated_content = remove_exception_imports(content)
        
        # Replace exception raising with logging
        updated_content = replace_exception_raising(updated_content)
        
        # Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.write(updated_content)
        
        logger.info(f"Successfully updated {file_path.name}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing {file_path.name}: {str(e)}")
        return False

def add_extend_existing_to_models():
    """Add 'extend_existing=True' to all SQLAlchemy models to prevent redefinition errors."""
    models_dir = REPO_DIR / "app" / "models"
    success_count = 0
    
    for model_file in models_dir.glob("*.py"):
        if model_file.name == "__init__.py" or model_file.name == "base.py":
            continue
        
        logger.info(f"Processing model {model_file.name}")
        
        try:
            with open(model_file, 'r') as file:
                content = file.read()
            
            # Check if the file has __table_args__ definition
            if "__table_args__" in content:
                # Check if extend_existing is already in table_args
                if "'extend_existing': True" in content or '"extend_existing": True' in content:
                    logger.info(f"{model_file.name} already has extend_existing=True")
                    continue
                
                # Add extend_existing to existing __table_args__
                updated_content = re.sub(
                    r'__table_args__\s*=\s*(\{[^}]*\})',
                    r'__table_args__ = {\1[:-1], "extend_existing": True}',
                    content
                )
                
                # If the replacement didn't work, try another pattern
                if updated_content == content:
                    updated_content = re.sub(
                        r'__table_args__\s*=\s*(\{)',
                        r'__table_args__ = {\n        "extend_existing": True,',
                        content
                    )
            else:
                # Add new __table_args__ with extend_existing
                updated_content = re.sub(
                    r'(class \w+\([^)]*\):)',
                    r'\1\n    __table_args__ = {"extend_existing": True}',
                    content
                )
            
            # Write the updated content back to the file
            with open(model_file, 'w') as file:
                file.write(updated_content)
            
            success_count += 1
            logger.info(f"Successfully updated model {model_file.name}")
        
        except Exception as e:
            logger.error(f"Error processing model {model_file.name}: {str(e)}")
    
    logger.info(f"Added extend_existing=True to {success_count} model files")

def main():
    """Main function to process all repository files."""
    logger.info("Starting exception removal process for MVP preparation")
    
    # Find all repository files
    repository_files = find_repository_files()
    
    # Process each file
    success_count = 0
    for file_path in repository_files:
        if process_file(file_path):
            success_count += 1
    
    logger.info(f"Successfully processed {success_count} out of {len(repository_files)} files")
    
    # Add extend_existing=True to all models
    logger.info("Adding extend_existing=True to all models")
    add_extend_existing_to_models()
    
    logger.info("MVP preparation completed")

if __name__ == "__main__":
    main()
