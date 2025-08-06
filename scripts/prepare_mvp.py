#!/usr/bin/env python3
"""
Main script to orchestrate the MVP preparation process by removing custom exceptions
and simplifying error handling across the codebase.
"""

import os
import logging
import subprocess
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mvp_preparation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Path to the scripts
SCRIPT_DIR = Path(__file__).parent
REPO_DIR = Path(__file__).parent.parent

def install_requirements():
    """Install required packages for the scripts."""
    logger.info("Installing required packages")
    try:
        # Check if astunparse is installed
        try:
            import astunparse
            logger.info("astunparse is already installed")
        except ImportError:
            logger.info("Installing astunparse")
            subprocess.run([sys.executable, "-m", "pip", "install", "astunparse"], check=True)
        
        return True
    except Exception as e:
        logger.error(f"Error installing requirements: {str(e)}")
        return False

def run_script(script_name):
    """Run a script and log the output."""
    script_path = SCRIPT_DIR / script_name
    logger.info(f"Running {script_name}")
    
    try:
        # Make the script executable
        os.chmod(script_path, 0o755)
        
        # Run the script
        process = subprocess.run(
            [sys.executable, str(script_path)], 
            capture_output=True, 
            text=True,
            check=True
        )
        
        # Log the output
        for line in process.stdout.splitlines():
            logger.info(f"{script_name} output: {line}")
        
        logger.info(f"Successfully ran {script_name}")
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_name}: {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return False
    
    except Exception as e:
        logger.error(f"Error running {script_name}: {str(e)}")
        return False

def check_codebase_for_exceptions():
    """Check the codebase for any remaining custom exceptions."""
    logger.info("Checking for remaining custom exceptions in the codebase")
    
    # List of exception classes to look for
    exception_classes = [
        "AccountError", "TransactionError", "FraudDetectionError", "AlertProcessingError",
        "UserError", "AuthenticationError", "CardError", "MerchantError", 
        "BranchError", "RecommendationError", "DatabaseError", "AIModelError",
        "BehavioralPatternError"
    ]
    
    # Build grep pattern
    pattern = "|".join(exception_classes)
    
    try:
        # Run grep to find any remaining exceptions
        process = subprocess.run(
            [
                "grep", 
                "-r", 
                "--include=*.py", 
                "-E", 
                pattern, 
                str(REPO_DIR / "app" / "repositories")
            ], 
            capture_output=True, 
            text=True
        )
        
        # Check if any exceptions were found
        if process.stdout:
            logger.warning("Found remaining custom exceptions:")
            for line in process.stdout.splitlines():
                logger.warning(line)
            return False
        else:
            logger.info("No remaining custom exceptions found")
            return True
    
    except Exception as e:
        logger.error(f"Error checking for remaining exceptions: {str(e)}")
        return False

def main():
    """Main function to orchestrate the MVP preparation process."""
    logger.info("Starting MVP preparation process")
    
    # Install required packages
    if not install_requirements():
        logger.error("Failed to install requirements, aborting")
        return
    
    # Scripts to run in order
    scripts = [
        "remove_exceptions_for_mvp.py",   # First remove exception imports and basic raises
        "fix_remaining_exceptions.py",    # Then fix any remaining complex raises
        "fix_try_except_blocks.py"        # Finally fix try/except blocks
    ]
    
    # Run each script in sequence
    for script in scripts:
        if not run_script(script):
            logger.error(f"Failed to run {script}, continuing with next script")
    
    # Check if any exceptions remain
    if not check_codebase_for_exceptions():
        logger.warning("Some custom exceptions may remain in the codebase")
    
    logger.info("MVP preparation process completed")

if __name__ == "__main__":
    main()
