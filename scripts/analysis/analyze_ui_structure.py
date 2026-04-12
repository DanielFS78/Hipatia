"""
Nombre del Módulo: scripts.analysis.analyze_ui_structure

Descripción: Script ejecutable (`analyze_ui_structure`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import ast
import os
import sys

def analyze_file(filepath):
    """
    Analyzes a Python file and produces a markdown report.
    """
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"Error parsing {filepath}: {e}")
        return

    report = []
    report.append(f"# Análisis Técnico de `{os.path.basename(filepath)}`")
    report.append(f"**Ruta:** `{filepath}`")
    report.append(f"**Líneas Totales:** {len(source.splitlines())}")
    report.append("")

    # Imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module if node.module else ""
            for n in node.names:
                imports.append(f"{module}.{n.name}")
    
    report.append("## Dependencias Detectadas")
    report.append("Lista de imports encontrados:")
    report.append("```")
    for imp in sorted(imports):
        report.append(imp)
    report.append("```")
    report.append("")

    # Classes and Functions
    report.append("## Estructura de Clases y Funciones")
    
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            analyze_class(node, report, source)
        elif isinstance(node, ast.FunctionDef):
            analyze_function(node, report, source, level=1)

    return "\n".join(report)

def analyze_class(node, report, source):
    """Analyzes a class node."""
    start_line = node.lineno
    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
    line_count = end_line - start_line + 1
    
    report.append(f"### Clase: `{node.name}`")
    report.append(f"- **Líneas:** {line_count} (L{start_line}-L{end_line})")
    
    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
    report.append(f"- **Métodos:** {len(methods)}")
    
    # Docstring
    docstring = ast.get_docstring(node)
    if docstring:
        report.append(f"- **Descripción:** {docstring.splitlines()[0]}")
    
    report.append("")
    report.append("| Método | Líneas | Args | Complejidad (Estimada) |")
    report.append("|---|---|---|---|")
    
    for method in methods:
        analyze_method_row(method, report)
    
    report.append("")

def analyze_method_row(node, report):
    """Analyzes a method and adds a table row."""
    start_line = node.lineno
    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
    line_count = end_line - start_line + 1
    args = [a.arg for a in node.args.args]
    
    # Simple complexity estimation: count of loops and ifs
    complexity = 0
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler)):
            complexity += 1
            
    complexity_str = str(complexity)
    if complexity > 10:
        complexity_str = f"**{complexity}** (Alta)"
    
    report.append(f"| `{node.name}` | {line_count} | {len(args)} | {complexity_str} |")

def analyze_function(node, report, source, level=1):
    """Analyzes a standalone function."""
    start_line = node.lineno
    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
    line_count = end_line - start_line + 1
    
    prefix = "#" * (level + 2)
    report.append(f"{prefix} Función Global: `{node.name}`")
    report.append(f"- **Líneas:** {line_count} (L{start_line}-L{end_line})")
    report.append("")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python analyze_ui_structure.py <archivo_py> [output_md]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = analyze_file(input_file)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Reporte guardado en {output_file}")
    else:
        print(result)
