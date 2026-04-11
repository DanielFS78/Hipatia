"""
Nombre del Módulo: scripts.analysis.analyze_controller

Descripción: Funciones puras de apoyo (sin estado de proceso): ``analyze_file``. Integración típica con: ``ast``, ``os``, ``sys``.
"""

import ast
import os
import sys

def analyze_file(file_path):
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())

    print(f"Analysis of {file_path}")
    print("=" * 40)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            print(f"\nClass: {node.name}")
            print("-" * 20)
            methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
            for method in methods:
                args = [arg.arg for arg in method.args.args]
                # Check for explicit typing
                has_return_annotation = method.returns is not None
                args_missing_type = [arg.arg for arg in method.args.args if arg.annotation is None and arg.arg != 'self']
                
                print(f"  Method: {method.name}")
                print(f"    Args: {args}")
                if args_missing_type:
                     print(f"    ⚠️ Missing Arg Types: {args_missing_type}")
                if not has_return_annotation:
                     print(f"    ⚠️ Missing Return Type")
                
                # Check for 'Any' in annotations
                if method.returns and isinstance(method.returns, ast.Name) and method.returns.id == 'Any':
                    print(f"    ⚠️ Returns Any")

analyze_file('controllers/simulation_controller.py')
