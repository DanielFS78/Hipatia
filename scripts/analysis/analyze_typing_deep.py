"""
Nombre del Módulo: scripts.analysis.analyze_typing_deep
Descripcion: Auditoría de cobertura de anotaciones de tipos por archivo/función.
"""

import ast
import os
import sys
from typing import Dict, List, Tuple

def analyze_file(filepath: str) -> Dict[str, int]:
    stats = {
        "functions": 0,
        "fully_typed": 0,
        "partially_typed": 0,
        "untyped": 0
    }
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
    except Exception:
        return stats

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stats["functions"] += 1
            
            # Check return annotation
            has_return = node.returns is not None
            
            # Check arguments
            args = node.args.args + node.args.kwonlyargs + node.args.posonlyargs
            # Filter out self/cls
            args = [a for a in args if a.arg not in ('self', 'cls')]
            
            total_args = len(args)
            typed_args = sum(1 for a in args if a.annotation is not None)
            
            if total_args == 0:
                is_fully_typed = has_return
            else:
                is_fully_typed = has_return and (typed_args == total_args)
                
            if is_fully_typed:
                stats["fully_typed"] += 1
            elif has_return or typed_args > 0:
                stats["partially_typed"] += 1
            else:
                stats["untyped"] += 1
                
    return stats

def analyze_directory(root_dir: str, target_dirs: List[str] | None = None):
    # If target_dirs is None, analyze everything. 
    # Otherwise only analyze files that start with one of the target_dirs
    
    summary = {
        "files": 0,
        "functions": 0,
        "fully_typed": 0,
        "partially_typed": 0,
        "untyped": 0
    }

    for root, dirs, files in os.walk(root_dir):
        # Exclusions
        if any(d in root for d in ['.venv', 'venv', '.git', '__pycache__', 'env', '.idea', 'migrations', 'tests']):
            continue

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, root_dir)
                
                # Check if file is in target_dirs
                if target_dirs:
                    if not any(rel_path.startswith(d) for d in target_dirs):
                        continue
                
                file_stats = analyze_file(filepath)
                
                summary["files"] += 1
                summary["functions"] += file_stats["functions"]
                summary["fully_typed"] += file_stats["fully_typed"]
                summary["partially_typed"] += file_stats["partially_typed"]
                summary["untyped"] += file_stats["untyped"]
                
    return summary

def print_summary(title: str, stats: Dict):
    total = stats["functions"]
    if total == 0:
        print(f"\n--- {title} ---")
        print("No functions found.")
        return

    print(f"\n--- {title} ---")
    print(f"Files analyzed: {stats['files']}")
    print(f"Total Functions: {total}")
    print(f"  ✅ Fully Typed:      {stats['fully_typed']} ({stats['fully_typed']/total*100:.1f}%)")
    print(f"  ⚠️ Partially Typed:  {stats['partially_typed']} ({stats['partially_typed']/total*100:.1f}%)")
    print(f"  ❌ Untyped:          {stats['untyped']} ({stats['untyped']/total*100:.1f}%)")

if __name__ == "__main__":
    current_dir = os.getcwd()
    
    # 1. Analyze Core
    core_stats = analyze_directory(current_dir, target_dirs=["core"])
    print_summary("Core Module", core_stats)
    
    # 2. Analyze Database/Repositories
    repo_stats = analyze_directory(current_dir, target_dirs=["database/repositories"])
    print_summary("Repositories", repo_stats)
    
    # 3. Analyze Controllers
    controller_stats = analyze_directory(current_dir, target_dirs=["controllers"])
    print_summary("Controllers", controller_stats)
    
    # 4. Analyze UI
    ui_stats = analyze_directory(current_dir, target_dirs=["ui"])
    print_summary("UI Layer", ui_stats)
    
    # 5. Global
    global_stats = analyze_directory(current_dir)
    print_summary("GLOBAL PROJECT", global_stats)
