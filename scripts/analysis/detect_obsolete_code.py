"""
Script ejecutable (`detect_obsolete_code`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import os
import ast
import re
from typing import Set, Dict, List, Tuple
from pathlib import Path

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

def extract_definitions(file_path: str) -> Tuple[Set[str], Set[str]]:
    """Extract class and function names defined in a file."""
    defined_classes = set()
    defined_functions = set()
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                defined_classes.add(node.name)
            elif isinstance(node, ast.FunctionDef):
                # Ignore private methods and special methods
                if not node.name.startswith("_"):
                    defined_functions.add(node.name)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        
    return defined_classes, defined_functions

def search_usages(root_dir: str, target_names: Set[str]) -> Dict[str, int]:
    """Count usages of target names in all files."""
    usages = {name: 0 for name in target_names}
    
    for root, _, files in os.walk(root_dir):
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if not file.endswith(".py"):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                for name in target_names:
                    # Simple regex to find usages, avoiding definition sites
                    # This is a heuristic and might have false positives/negatives
                    # We define usage as the name preceded by not 'class ' or 'def '
                    if re.search(r'\b' + re.escape(name) + r'\b', content):
                        # Simple check: if defined in file A, and appears in file B
                        # Or appears in file A but not as definition (hard to distinguish with simple regex)
                        # Here we just count literal occurrences. 
                        # To be more precise, we subtract 1 for the definition itself if it's in this file.
                        usages[name] += len(re.findall(r'\b' + re.escape(name) + r'\b', content))
            except Exception:
                continue
                
    return usages

def check_deprecated(file_path: str) -> List[str]:
    """Busca decoradores de deprecación y comentarios TODO: Remove."""
    issues = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            if "@deprecated" in line or "TODO: Remove" in line or "DEPRECATED" in line:
                issues.append(f"Line {i+1}: {line.strip()}")
    except Exception:
        pass
    return issues

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    print(f"Analyzing project definition at: {root_dir}")
    
    python_files = get_python_files(root_dir)
    print(f"Found {len(python_files)} Python files.")
    
    # Check for definitions
    all_classes = set()
    all_functions = set()
    file_definitions = {}
    
    for file in python_files:
        c, f = extract_definitions(file)
        all_classes.update(c)
        all_functions.update(f)
        file_definitions[file] = (c, f)
        
    print(f"Found {len(all_classes)} classes and {len(all_functions)} public functions.")
    
    # Check for obsolete/deprecated markers
    print("\\n--- Deprecated/Obsolete Code Markers ---")
    found_deprecated = False
    for file in python_files:
        issues = check_deprecated(file)
        if issues:
            found_deprecated = True
            rel_path = os.path.relpath(file, root_dir)
            print(f"\\nFile: {rel_path}")
            for issue in issues:
                print(f"  - {issue}")
                
    if not found_deprecated:
        print("No explicit @deprecated or 'TODO: Remove' markers found.")

    # Note: Usage analysis is computationally expensive and prone to false positives with simple regex.
    # For a robust analysis, we would need a full language server or static analysis tool like vulture.
    # We will just list the files that might be candidates for deletion based on common naming patterns.
    
    print("\\n--- Potential Cleanup Candidates (File Naming) ---")
    candidates = []
    for file in python_files:
        filename = os.path.basename(file)
        if "temp" in filename.lower() or "old" in filename.lower() or "historical" in filename.lower():
            rel_path = os.path.relpath(file, root_dir)
            candidates.append(rel_path)
            
    if candidates:
        for candidate in candidates:
            print(f"  - {candidate}")
    else:
        print("No files with 'temp', 'legacy', or 'old' in name found.")

if __name__ == "__main__":
    main()
