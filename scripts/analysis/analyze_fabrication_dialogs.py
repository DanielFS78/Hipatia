"""
Nombre del Módulo: scripts.analysis.analyze_fabrication_dialogs

Descripción: Script ejecutable (`analyze_fabrication_dialogs`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import ast
import os
import sys

def analyze_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)

    print(f"Analysis of {file_path}")
    print("=" * 40)

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            print(f"\nClass: {node.name}")
            print("-" * 20)
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    args = [a.arg for a in item.args.args]
                    print(f"  Method: {item.name}")
                    print(f"    Args: {args}")
                    
                    # Check for 'Any' in annotation
                    has_any = False
                    if item.args.args:
                        for arg in item.args.args:
                            if arg.annotation and isinstance(arg.annotation, ast.Name) and arg.annotation.id == 'Any':
                                has_any = True
                    if item.returns and isinstance(item.returns, ast.Name) and item.returns.id == 'Any':
                        has_any = True
                    
                    if has_any:
                        print(f"    [!] Uses 'Any' in signature")

if __name__ == "__main__":
    analyze_file("ui/dialogs/fabrication_dialogs.py")
