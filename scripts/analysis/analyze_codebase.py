"""
Script ejecutable (`analyze_codebase`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import ast
import os
import sys
import collections
from typing import Dict, List, Set, Tuple, TypedDict


class FileStats(TypedDict):
    """Métricas por fichero (derivadas del AST) para análisis de tipado."""

    functions: int
    typed_functions: int
    partially_typed_functions: int
    untyped_functions: int
    classes: int
    imports: list[str]
    naming_issues: list[str]
    any_usage: int


class DirectorySummary(TypedDict):
    """Resumen agregado por directorio."""

    total_files: int
    total_functions: int
    total_typed: int
    total_partial: int
    total_untyped: int
    total_any_usage: int
    files_with_issues: dict[str, FileStats]

def analyze_file(filepath: str) -> FileStats | None:
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            return None

    stats: FileStats = {
        "functions": 0,
        "typed_functions": 0,
        "partially_typed_functions": 0,
        "untyped_functions": 0,
        "classes": 0,
        "imports": [],
        "naming_issues": [],
        "any_usage": 0
    }

    for node in ast.walk(tree):
        # Analyze Functions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stats["functions"] += 1
            has_return_annotation = node.returns is not None
            
            args = node.args.args + node.args.kwonlyargs + node.args.posonlyargs
            # Filter out 'self' and 'cls'
            args = [a for a in args if a.arg not in ('self', 'cls')]
            
            total_args = len(args)
            typed_args = sum(1 for a in args if a.annotation is not None)
            
            is_fully_typed = (has_return_annotation and typed_args == total_args) or (total_args == 0 and has_return_annotation)
            
            if is_fully_typed:
                stats["typed_functions"] += 1
            elif has_return_annotation or typed_args > 0:
                stats["partially_typed_functions"] += 1
            else:
                stats["untyped_functions"] += 1
                
            # Check naming convention (snake_case)
            if not node.name.islower() and node.name != "__init__":
                 stats["naming_issues"].append(f"Function '{node.name}' should be snake_case")


        # Analyze Classes
        elif isinstance(node, ast.ClassDef):
            stats["classes"] += 1
            # Check naming convention (PascalCase)
            if node.name[0].islower():
                stats["naming_issues"].append(f"Class '{node.name}' should be PascalCase")

        # Analyze Imports
        elif isinstance(node, ast.Import):
            for alias in node.names:
                stats["imports"].append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                stats["imports"].append(node.module)

        # Count 'Any' usage (rough check in annotations)
        elif isinstance(node, ast.Name) and node.id == 'Any':
             stats["any_usage"] += 1
        elif isinstance(node, ast.Attribute) and node.attr == 'Any':
             stats["any_usage"] += 1

    return stats

def analyze_directory(root_dir: str) -> DirectorySummary:
    summary: DirectorySummary = {
        "total_files": 0,
        "total_functions": 0,
        "total_typed": 0,
        "total_partial": 0,
        "total_untyped": 0,
        "total_any_usage": 0,
        "files_with_issues": {}
    }

    for root, dirs, files in os.walk(root_dir):
        # Exclude common non-project directories
        if any(d in root for d in ['.venv', 'venv', '.git', '__pycache__', 'env', '.idea']):
            continue

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                file_stats = analyze_file(filepath)
                
                if file_stats is None:
                    continue

                summary["total_files"] += 1
                summary["total_functions"] += file_stats["functions"]
                summary["total_typed"] += file_stats["typed_functions"]
                summary["total_partial"] += file_stats["partially_typed_functions"]
                summary["total_untyped"] += file_stats["untyped_functions"]
                summary["total_any_usage"] += file_stats["any_usage"]
                
                if file_stats["naming_issues"] or file_stats["untyped_functions"] > 0:
                    summary["files_with_issues"][filepath] = file_stats

    return summary

if __name__ == "__main__":
    project_root = "/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion"
    results = analyze_directory(project_root)
    
    print("--- Codebase Analysis Report ---")
    print(f"Total Python Files: {results['total_files']}")
    print(f"Total Functions/Methods: {results['total_functions']}")
    print(f"  - Fully Typed: {results['total_typed']} ({results['total_typed']/results['total_functions']*100:.1f}%)")
    print(f"  - Partially Typed: {results['total_partial']}")
    print(f"  - Untyped: {results['total_untyped']}")
    print(f"Total 'Any' usage detected: {results['total_any_usage']}")
    print("\n--- Files with most untyped functions ---")
    
    sorted_files = sorted(results["files_with_issues"].items(), key=lambda item: item[1]["untyped_functions"], reverse=True)
    
    for filepath, stats in sorted_files[:10]:
        rel_path = os.path.relpath(filepath, project_root)
        print(f"{rel_path}: {stats['untyped_functions']} untyped functions")
