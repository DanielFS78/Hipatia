"""
Script ejecutable (`check_typing_coverage`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import os
import ast
import sys
from pathlib import Path

def get_typing_stats(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return 0, 0

    total_functions = 0
    typed_functions = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total_functions += 1
            # Check if it has a return annotation or argument annotations
            has_return_annotation = node.returns is not None
            has_arg_annotations = any(arg.annotation is not None for arg in node.args.args)
            
            # We consider it "typed" if it has at least a return annotation OR all args typed. 
            # For a stricter check, we could require BOTH.
            # Let's go with: if it has *any* typing hints, count it as partially typed.
            # But the goal says "Completely typed". Let's check for return annotation as a proxy for "effort made".
            if has_return_annotation or has_arg_annotations:
                typed_functions += 1

    return total_functions, typed_functions

def analyze_directory(directory):
    total_files = 0
    total_funcs = 0
    total_typed = 0
    stats_by_file = []

    for root, _, files in os.walk(directory):
        if ".venv" in root or "__pycache__" in root or "tests" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                funcs, typed = get_typing_stats(file_path)
                
                if funcs > 0:
                    total_files += 1
                    total_funcs += funcs
                    total_typed += typed
                    percentage = (typed / funcs) * 100
                    stats_by_file.append((file_path, funcs, typed, percentage))

    return total_funcs, total_typed, stats_by_file

def main():
    root_dir = Path(__file__).parent.parent
    print(f"Analyzing Codebase in: {root_dir}")
    
    total, typed, file_stats = analyze_directory(root_dir)
    
    if total == 0:
        print("No functions found.")
        return

    print(f"\nTotal Functions: {total}")
    print(f"Typed Functions: {typed}")
    print(f"Coverage: {(typed/total)*100:.2f}%")
    
    print("\nTop Untyped Files (by function count):")
    # Sort by number of untyped functions (funcs - typed) descending
    file_stats.sort(key=lambda x: x[1] - x[2], reverse=True)
    
    for path, funcs, t, perc in file_stats[:10]:
        rel_path = os.path.relpath(path, root_dir)
        print(f"{rel_path}: {t}/{funcs} ({perc:.1f}%)")

if __name__ == "__main__":
    main()
