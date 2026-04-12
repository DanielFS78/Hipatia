"""
Nombre del Módulo: scripts.analysis.analyze_structure

Descripción: Script ejecutable (`analyze_structure`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import ast
import os
import sys

def analyze_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    report = []
    report.append(f"# Analysis of {os.path.basename(file_path)}\n")
    report.append(f"**Path**: `{file_path}`\n")

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            report.append(f"## Class: {node.name}")
            # Get bases
            bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
            if bases:
                report.append(f"- Inherits from: {', '.join(bases)}")
            
            # Get methods
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    args = [a.arg for a in item.args.args]
                    report.append(f"- Method: `{item.name}({', '.join(args)})`")
                    docstring = ast.get_docstring(item)
                    if docstring is not None:
                        doc = docstring.split("\n")[0]
                        report.append(f"  - Doc: {doc}")
            report.append("")

        elif isinstance(node, ast.FunctionDef):
            # Check if it's a top-level function (not inside a class)
            # This is a bit simplified, ast.walk is depth-first but doesn't track parent interaction easily
            # However, for a summary report, listing all functions is okay, or we can just skip if inside class (handled above)
            pass 

    return "\n".join(report)

def main():
    target_files = [
        "/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/core/qr_scanner.py",
        "/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/controllers/app_controller.py",
        "/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/core/app_model.py",
        "/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/database/repositories/tracking_repository.py",
        "/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/database/models.py",
        "/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/ui/widgets/calculate_times_widget.py"
    ]

    output_dir = "/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/Documentacion/Fase 4"
    os.makedirs(output_dir, exist_ok=True)

    for file_path in target_files:
        if os.path.exists(file_path):
            print(f"Analyzing {file_path}...")
            content = analyze_file(file_path)
            output_filename = f"analysis_{os.path.basename(file_path).replace('.py', '')}.md"
            with open(os.path.join(output_dir, output_filename), "w", encoding="utf-8") as f:
                f.write(content)
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()
