"""
Nombre del Módulo: scripts.analyze_ui_state

Descripción: Script ejecutable (`analyze_ui_state`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import os
import ast

def analyze_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = len(content.split('\n'))
    
    try:
        tree = ast.parse(content)
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        return {
            'lines': lines,
            'classes': len(classes),
            'functions': len(functions)
        }
    except SyntaxError:
        return {'lines': lines, 'classes': -1, 'functions': -1}

def scan_directory(directory):
    results = []
    for root, _, files in os.walk(directory):
        if '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, directory)
                stats = analyze_file(filepath)
                results.append((rel_path, stats))
    
    # Sort by number of lines descending
    results.sort(key=lambda x: x[1]['lines'], reverse=True)
    return results

def main():
    base_dir = '/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion'
    ui_dir = os.path.join(base_dir, 'ui')
    
    print("--- Análisis de UI (Widgets y Dialogs) ---")
    results = scan_directory(ui_dir)
    
    print(f"{'Archivo':<40} | {'Líneas':<8} | {'Clases':<8} | {'Funciones':<10}")
    print("-" * 75)
    for path, stats in results:
        print(f"{path:<40} | {stats['lines']:<8} | {stats['classes']:<8} | {stats['functions']:<10}")
        
    # Guardar en archivo
    report_path = os.path.join(base_dir, 'Documentacion', 'Refactorizacion_UI_2', 'Analisis_Estado_Archivos_UI.md')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write("# Reporte de Análisis de UI (Estado Actual)\n\n")
        f.write("| Archivo | Líneas | Clases | Funciones |\n")
        f.write("|---------|--------|--------|-----------|\n")
        for path, stats in results:
            f.write(f"| `{path}` | {stats['lines']} | {stats['classes']} | {stats['functions']} |\n")
            
    print(f"\nReporte guardado en: {report_path}")

if __name__ == "__main__":
    main()
