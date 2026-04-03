"""
Script ejecutable (`verify_naming_conventions`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import os
import ast
import re
from typing import List, Tuple

def get_python_files(root_dir: str) -> List[str]:
    """Recursively find all Python files in the directory."""
    python_files = []
    for root, _, files in os.walk(root_dir):
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files

def is_snake_case(name: str) -> bool:
    """Check if string is snake_case."""
    return re.match(r'^[a-z_][a-z0-9_]*$', name) is not None

def is_camel_case(name: str) -> bool:
    """Check if string is CamelCase (PascalCase)."""
    return re.match(r'^[A-Z][a-zA-Z0-9]*$', name) is not None

def check_file_conventions(file_path: str) -> List[str]:
    """Check naming conventions in a single file."""
    issues = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not is_camel_case(node.name):
                    issues.append(f"Class '{node.name}' should be CamelCase")
            elif isinstance(node, ast.FunctionDef):
                if not is_snake_case(node.name) and not node.name.startswith("__"):
                    issues.append(f"Function '{node.name}' should be snake_case")
            # Variable checks are harder at AST level for global/local context, skipping for simplicity
            
    except Exception as e:
        issues.append(f"Error parsing file: {e}")
        
    return issues

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    print(f"Verifying naming conventions in: {root_dir}")
    
    python_files = get_python_files(root_dir)
    print(f"Found {len(python_files)} Python files.")
    
    total_issues = 0
    files_with_issues = 0
    
    for file in python_files:
        issues = check_file_conventions(file)
        if issues:
            rel_path = os.path.relpath(file, root_dir)
            print(f"\\nFile: {rel_path}")
            for issue in issues:
                print(f"  - {issue}")
            total_issues += len(issues)
            files_with_issues += 1
            
    print(f"\\nTotal issues found: {total_issues} in {files_with_issues} files.")

if __name__ == "__main__":
    main()
