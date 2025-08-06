#!/usr/bin/env python3
"""
Script to identify and fix remaining exception usages after the main exception removal.
This script handles more complex patterns and corner cases.
"""

import os
import re
import logging
from pathlib import Path
import ast
import astunparse

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

class ExceptionUsageVisitor(ast.NodeVisitor):
    """AST visitor to find and track exception usage patterns."""
    
    def __init__(self):
        self.exception_raises = []
        self.method_returns = {}
        self.current_method = None
    
    def visit_FunctionDef(self, node):
        """Visit function definition nodes to track method context."""
        self.current_method = node.name
        self.method_returns[self.current_method] = []
        self.generic_visit(node)
        self.current_method = None
    
    def visit_Return(self, node):
        """Visit return statements to determine method return types."""
        if self.current_method:
            if isinstance(node.value, ast.List):
                self.method_returns[self.current_method].append("list")
            elif isinstance(node.value, ast.Dict):
                self.method_returns[self.current_method].append("dict")
            elif isinstance(node.value, ast.NameConstant) and node.value.value in (True, False):
                self.method_returns[self.current_method].append("bool")
            elif isinstance(node.value, ast.Constant) and isinstance(node.value.value, bool):  # Python 3.8+
                self.method_returns[self.current_method].append("bool")
        self.generic_visit(node)
    
    def visit_Raise(self, node):
        """Visit raise statements to find exception usages."""
        if isinstance(node.exc, ast.Call):
            if hasattr(node.exc.func, 'id') and node.exc.func.id in EXCEPTION_CLASSES:
                # Get the method name, line number, and exception details
                info = {
                    'method': self.current_method,
                    'line': node.lineno,
                    'exception_class': node.exc.func.id,
                    'args': []
                }
                
                # Extract exception arguments
                for arg in node.exc.args:
                    if isinstance(arg, ast.Str) or isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        # Handle string literals
                        value = arg.s if hasattr(arg, 's') else arg.value
                        info['args'].append(f'"{value}"')
                    elif isinstance(arg, ast.Name):
                        # Handle variable names
                        info['args'].append(arg.id)
                    elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                        # Handle string concatenation
                        info['args'].append(astunparse.unparse(arg).strip())
                    else:
                        # For other expressions, use the unparsed source
                        info['args'].append(astunparse.unparse(arg).strip())
                
                self.exception_raises.append(info)
        
        self.generic_visit(node)

def get_method_return_type(visitor, method_name):
    """Determine the most likely return type for a method based on its return statements."""
    if method_name not in visitor.method_returns:
        return "None"
    
    return_types = visitor.method_returns[method_name]
    if not return_types:
        return "None"
    
    # Count occurrences of each return type
    type_counts = {}
    for rt in return_types:
        type_counts[rt] = type_counts.get(rt, 0) + 1
    
    # Return the most common type
    return max(type_counts.items(), key=lambda x: x[1])[0]

def analyze_repository_file(file_path):
    """Analyze a repository file to find exception usage patterns."""
    logger.info(f"Analyzing {file_path.name} for exception usages")
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Parse the file into an AST
        tree = ast.parse(content)
        
        # Visit all nodes to find exception usages
        visitor = ExceptionUsageVisitor()
        visitor.visit(tree)
        
        # Log the findings
        if visitor.exception_raises:
            logger.info(f"Found {len(visitor.exception_raises)} exception raises in {file_path.name}")
            for raise_info in visitor.exception_raises:
                method_return_type = get_method_return_type(visitor, raise_info['method'])
                logger.info(f"  Line {raise_info['line']}: {raise_info['exception_class']}({', '.join(raise_info['args'])}) in method {raise_info['method']} -> returns {method_return_type}")
                raise_info['return_type'] = method_return_type
        else:
            logger.info(f"No exception usages found in {file_path.name}")
        
        return visitor.exception_raises
    
    except Exception as e:
        logger.error(f"Error analyzing {file_path.name}: {str(e)}")
        return []

def replace_exceptions_in_file(file_path, exception_raises):
    """Replace exception raises with logging and appropriate return values."""
    if not exception_raises:
        logger.info(f"No exceptions to replace in {file_path.name}")
        return True
    
    logger.info(f"Replacing {len(exception_raises)} exceptions in {file_path.name}")
    
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        # Sort by line number in reverse order to avoid issues with line numbers changing
        exception_raises.sort(key=lambda x: x['line'], reverse=True)
        
        for raise_info in exception_raises:
            line_idx = raise_info['line'] - 1  # Convert to 0-based index
            if line_idx >= len(lines):
                logger.warning(f"Line number {raise_info['line']} out of range in {file_path.name}")
                continue
            
            # Get indentation
            original_line = lines[line_idx]
            indentation = re.match(r'^(\s*)', original_line).group(1)
            
            # Create replacement text based on return type
            exception_args = ", ".join(raise_info['args'])
            if raise_info['return_type'] == "list":
                replacement = f'{indentation}logger.error(f"{raise_info["exception_class"]}: {{{exception_args}}}")\n{indentation}return []\n'
            elif raise_info['return_type'] == "dict":
                replacement = f'{indentation}logger.error(f"{raise_info["exception_class"]}: {{{exception_args}}}")\n{indentation}return {{"error": "{raise_info["exception_class"]}", "message": {exception_args}}}\n'
            elif raise_info['return_type'] == "bool":
                replacement = f'{indentation}logger.error(f"{raise_info["exception_class"]}: {{{exception_args}}}")\n{indentation}return False\n'
            else:
                replacement = f'{indentation}logger.error(f"{raise_info["exception_class"]}: {{{exception_args}}}")\n{indentation}return None\n'
            
            # Replace the line
            lines[line_idx] = replacement
        
        # Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.writelines(lines)
        
        logger.info(f"Successfully replaced exceptions in {file_path.name}")
        return True
    
    except Exception as e:
        logger.error(f"Error replacing exceptions in {file_path.name}: {str(e)}")
        return False

def find_repository_files():
    """Find all enhanced repository files in the repository directory."""
    repository_files = []
    for file in REPOSITORIES_DIR.glob("enhanced_*.py"):
        repository_files.append(file)
    
    logger.info(f"Found {len(repository_files)} enhanced repository files")
    return repository_files

def process_file(file_path):
    """Process a single repository file to fix remaining exception usages."""
    # Analyze the file to find exception usages
    exception_raises = analyze_repository_file(file_path)
    
    # Replace the exceptions with logging and appropriate returns
    if exception_raises:
        return replace_exceptions_in_file(file_path, exception_raises)
    
    return True

def main():
    """Main function to process all repository files."""
    logger.info("Starting detailed exception usage analysis and replacement")
    
    # Find all repository files
    repository_files = find_repository_files()
    
    # Process each file
    success_count = 0
    for file_path in repository_files:
        if process_file(file_path):
            success_count += 1
    
    logger.info(f"Successfully processed {success_count} out of {len(repository_files)} files")
    logger.info("Exception usage analysis and replacement completed")

if __name__ == "__main__":
    main()
