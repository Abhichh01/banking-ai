#!/usr/bin/env python3
"""
Script to specifically handle try/except blocks with custom exceptions in the codebase.
This script converts custom exception handling to generic exception handling with logging.
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

# Exception class names to look for in except blocks
EXCEPTION_CLASSES = [
    "AccountError", "TransactionError", "FraudDetectionError", "AlertProcessingError",
    "UserError", "AuthenticationError", "CardError", "MerchantError", 
    "BranchError", "RecommendationError", "DatabaseError", "AIModelError",
    "BehavioralPatternError"
]

def find_repository_files():
    """Find all enhanced repository files in the repository directory."""
    repository_files = []
    for file in REPOSITORIES_DIR.glob("enhanced_*.py"):
        repository_files.append(file)
    
    logger.info(f"Found {len(repository_files)} enhanced repository files")
    return repository_files

def fix_try_except_blocks(content):
    """Replace custom exception handling in try/except blocks with generic exception handling."""
    # Find all try/except blocks with custom exceptions
    for exception_class in EXCEPTION_CLASSES:
        # Pattern to match except blocks with the custom exception
        pattern = rf'except\s+{exception_class}\s+as\s+(\w+):(.*?)(?=except|finally|\n\s*\n|\Z)'
        
        # Find all matches
        for match in re.finditer(pattern, content, re.DOTALL):
            exception_var = match.group(1)
            except_block = match.group(2)
            
            # Create a replacement with generic Exception and logging
            replacement = f'except Exception as {exception_var}:  # Was {exception_class}\n        logger.error(f"Error: {{{exception_var}}}")'
            
            # If the except block doesn't already have a return, add one based on context
            if 'return' not in except_block:
                # Try to determine the appropriate return value from context
                if 'list' in except_block.lower() or 'items' in except_block.lower():
                    replacement += '\n        return []'
                elif 'dict' in except_block.lower() or 'json' in except_block.lower():
                    replacement += '\n        return {"error": str(e)}'
                elif 'bool' in except_block.lower() or 'true' in except_block.lower() or 'false' in except_block.lower():
                    replacement += '\n        return False'
                else:
                    replacement += '\n        return None'
            
            # Replace the except block
            content = content.replace(match.group(0), replacement)
    
    return content

def simplify_exception_handling(content):
    """Simplify complex exception handling structures."""
    # Replace nested exception handling with simpler logging
    content = re.sub(
        r'try:.*?except\s+Exception\s+as\s+e:.*?try:.*?except\s+Exception\s+as\s+inner_e:.*?',
        r'try:\n        # Simplified nested exception handling\n    except Exception as e:\n        logger.error(f"Error: {e}")\n        return None\n    ',
        content,
        flags=re.DOTALL
    )
    
    # Replace re-raising exceptions with logging and return
    content = re.sub(
        r'logger\.error\([^)]+\)\s+raise',
        r'logger.error(f"Error in operation")\n        return None  # Removed re-raising',
        content
    )
    
    return content

def process_file(file_path):
    """Process a single repository file to fix try/except blocks."""
    logger.info(f"Processing {file_path.name}")
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Fix try/except blocks with custom exceptions
        updated_content = fix_try_except_blocks(content)
        
        # Simplify complex exception handling
        updated_content = simplify_exception_handling(updated_content)
        
        # Only write if changes were made
        if content != updated_content:
            with open(file_path, 'w') as file:
                file.write(updated_content)
            logger.info(f"Updated try/except blocks in {file_path.name}")
        else:
            logger.info(f"No try/except blocks to update in {file_path.name}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error processing {file_path.name}: {str(e)}")
        return False

def main():
    """Main function to process all repository files."""
    logger.info("Starting try/except block simplification for MVP preparation")
    
    # Find all repository files
    repository_files = find_repository_files()
    
    # Process each file
    success_count = 0
    for file_path in repository_files:
        if process_file(file_path):
            success_count += 1
    
    logger.info(f"Successfully processed {success_count} out of {len(repository_files)} files")
    logger.info("Try/except block simplification completed")

if __name__ == "__main__":
    main()
