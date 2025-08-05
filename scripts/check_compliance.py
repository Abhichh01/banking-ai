#!/usr/bin/env python3
"""Project Compliance Checker"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Pattern

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComplianceChecker:
    """Checks project compliance with established rules."""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        self.app_dir = self.root_dir / 'app'
        self.issues: List[Dict] = []
        
    def check_structure(self) -> None:
        """Check project directory structure."""
        required_dirs = [
            'app/api/v1/endpoints',
            'app/services',
            'app/models',
            'app/schemas',
            'app/repositories',
            'app/utils'
        ]
        
        for dir_path in required_dirs:
            full_path = self.root_dir / dir_path
            if not full_path.exists():
                self._add_issue("MISSING_DIRECTORY", f"Required directory not found: {dir_path}")
    
    def check_naming_conventions(self) -> None:
        """Check file and directory naming conventions."""
        patterns = {
            'endpoints': r'^[a-z][a-z0-9_]*\.py$',
            'services': r'^[a-z][a-z0-9_]*_service\.py$',
            'repositories': r'^[a-z][a-z0-9_]*_repository\.py$',
        }
        
        for dir_name, pattern in patterns.items():
            dir_path = self.app_dir / dir_name
            if dir_path.exists():
                self._check_files_in_dir(dir_path, pattern, f"{dir_name.upper()}_NAMING")
    
    def check_security(self) -> None:
        """Check for security issues."""
        sensitive_terms = [
            'password', 'secret', 'key', 'token', 'credential',
            'api[_-]?key', 'auth[_-]?token', 'private[_-]?key'
        ]
        
        for root, _, files in os.walk(self.root_dir):
            # Skip virtual environments and other ignored directories
            if any(ignore in root for ignore in ['venv', '__pycache__', '.git']):
                continue
                
            for file in files:
                if file.endswith('.py') or file.endswith('.env'):
                    self._check_file_for_sensitive_data(
                        Path(root) / file, 
                        sensitive_terms
                    )
    
    def _check_files_in_dir(self, dir_path: Path, pattern: str, issue_type: str) -> None:
        """Check files in directory against naming pattern."""
        try:
            for file in dir_path.glob('*.py'):
                if not re.match(pattern, file.name):
                    self._add_issue(
                        issue_type,
                        f"File '{file.relative_to(self.root_dir)}' doesn't match pattern '{pattern}'"
                    )
        except Exception as e:
            logger.error(f"Error checking files in {dir_path}: {e}")
    
    def _check_file_for_sensitive_data(self, file_path: Path, terms: List[str]) -> None:
        """Check file for sensitive information."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore').lower()
            
            for term in terms:
                if re.search(term, content, re.IGNORECASE):
                    self._add_issue(
                        "SENSITIVE_DATA",
                        f"Potential sensitive data found in {file_path.relative_to(self.root_dir)}: {term}"
                    )
        except Exception as e:
            logger.error(f"Error checking {file_path}: {e}")
    
    def _add_issue(self, issue_type: str, message: str) -> None:
        """Add an issue to the issues list."""
        self.issues.append({
            'type': issue_type,
            'message': message
        })
        logger.warning(f"[{issue_type}] {message}")
    
    def run_checks(self) -> bool:
        """Run all compliance checks."""
        logger.info("Starting compliance checks...")
        
        self.check_structure()
        self.check_naming_conventions()
        self.check_security()
        
        if not self.issues:
            logger.info("All compliance checks passed!")
            return True
        
        logger.warning(f"Found {len(self.issues)} compliance issues")
        return False

def main() -> int:
    """Run compliance checker."""
    checker = ComplianceChecker('.')
    success = checker.run_checks()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
