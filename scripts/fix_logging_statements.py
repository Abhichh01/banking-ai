#!/usr/bin/env python3
"""
Script to fix remaining exception references in logging statements.
This cleans up exception class names that were added to f-strings during conversion.
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

# Exception class names to look for
EXCEPTION_CLASSES = [
    "AccountError", "TransactionError", "FraudDetectionError", "AlertProcessingError",
    "UserError", "AuthenticationError", "CardError", "MerchantError", 
    "BranchError", "RecommendationError", "DatabaseError", "AIModelError",
    "BehavioralPatternError"
]

def fix_logging_statements(content):
    """Fix logging statements that contain exception class references."""
    # Pattern to match logger.error calls with exception class references
    pattern = r'logger\.error\(f"{{(\w+Error)}}:(.*?)"\)'
    
    # Replace with simpler error messages
    for match in re.finditer(pattern, content):
        exception_class = match.group(1)
        message = match.group(2)
        
        # Create replacement without the exception class reference
        replacement = f'logger.error(f"Error:{message}")'
        content = content.replace(match.group(0), replacement)
    
    return content

def process_file(file_path):
    """Process a single repository file to fix remaining exception references."""
    logger.info(f"Processing {file_path.name}")
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Fix logging statements
        updated_content = fix_logging_statements(content)
        
        # Remove any remaining import statements for exceptions
        for exception_class in EXCEPTION_CLASSES:
            updated_content = re.sub(
                rf'\s+{exception_class},\s*\n', 
                '\n', 
                updated_content
            )
        
        # Only write if changes were made
        if content != updated_content:
            with open(file_path, 'w') as file:
                file.write(updated_content)
            logger.info(f"Updated logging statements in {file_path.name}")
        else:
            logger.info(f"No changes needed in {file_path.name}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error processing {file_path.name}: {str(e)}")
        return False

def main():
    """Main function to process all repository files."""
    logger.info("Starting cleanup of remaining exception references")
    
    # Find all repository files
    repository_files = []
    for file in REPOSITORIES_DIR.glob("enhanced_*.py"):
        repository_files.append(file)
    
    logger.info(f"Found {len(repository_files)} enhanced repository files")
    
    # Process each file
    success_count = 0
    for file_path in repository_files:
        if process_file(file_path):
            success_count += 1
    
    logger.info(f"Successfully processed {success_count} out of {len(repository_files)} files")
    logger.info("Cleanup completed")

if __name__ == "__main__":
    main()
