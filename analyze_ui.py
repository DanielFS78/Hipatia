"""
Nombre del Módulo: analyze_ui.py
Descripción: Script para analizar la complejidad y estructura de los archivos de la interfaz de usuario (UI).
             Extrae clases, métodos, complejidad ciclomática aproximada y uso de señales/conexiones.
"""
import ast
import os
import json


def analyze_file(filepath):
    """
    Analiza un archivo Python individual para extraer métricas de estructura y complejidad.

    Args:
        filepath: Ruta absoluta o relativa al archivo .py que se desea analizar.

    Returns:
        Un diccionario con el recuento de líneas, ruta del archivo y una lista de clases encontradas
        con sus métodos y métricas asociadas.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    num_lines = len(lines)
    
    try:
        tree = ast.parse(content)
    except Exception as e:
        return {"error": str(e), "file": filepath, "lines": num_lines}

    class Visitor(ast.NodeVisitor):
        """
        Visitante AST para extraer información específica de clases y métodos de la UI.
        """
        def __init__(self):
            self.classes = []
            self.functions = []
            self.current_class = None
            
        def visit_ClassDef(self, node):
            """Procesa una definición de clase para recolectar sus métricas base."""
            class_info = {
                'name': node.name,
                'docstring': ast.get_docstring(node) or "Sin descripción disponible",
                'methods': [],
                'line_start': node.lineno,
                'line_end': node.end_lineno,
                'connections': 0,
                'signals_emitted': 0
            }
            self.current_class = class_info
            self.generic_visit(node)
            self.classes.append(class_info)
            self.current_class = None
        def visit_FunctionDef(self, node):
            """Analiza un método o función para calcular su complejidad ciclomática aproximada."""
            if self.current_class:
                branches = sum(1 for n in ast.walk(node) if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match)))
                self.current_class['methods'].append({
                    'name': node.name,
                    'docstring': ast.get_docstring(node) or "Sin descripción disponible",
                    'complexity': branches,
                    'lines': node.end_lineno - node.lineno
                })
            else:
                # Función global
                branches = sum(1 for n in ast.walk(node) if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match)))
                self.functions.append({
                    'name': node.name,
                    'docstring': ast.get_docstring(node) or "Sin descripción disponible",
                    'complexity': branches,
                    'lines': node.end_lineno - node.lineno
                })
            self.generic_visit(node)
            
        def visit_Call(self, node):
            """Detecta llamadas a 'connect' y 'emit' para medir la interactividad de la UI."""
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == 'connect':
                    if self.current_class:
                        self.current_class['connections'] += 1
                elif node.func.attr == 'emit':
                    if self.current_class:
                        self.current_class['signals_emitted'] += 1
            self.generic_visit(node)

    v = Visitor()
    v.visit(tree)
    
    # Calculate total complexity per class
    for c in v.classes:
        c['total_complexity'] = sum(m['complexity'] for m in c['methods'])
        c['total_methods'] = len(c['methods'])
    
    return {
        "file": filepath,
        "lines": num_lines,
        "module_docstring": ast.get_docstring(tree) or "Sin descripción disponible",
        "classes": v.classes,
        "functions": v.functions
    }

def main():
    """
    Punto de entrada principal del script. 
    Escanea los directorios de UI y genera un informe en formato JSON.
    """
    target_dirs = ['ui/dialogs', 'ui/widgets']
    results = []
    
    for d in target_dirs:
        for root, _, files in os.walk(d):
            for f in files:
                if f.endswith('.py') and f != '__init__.py':
                    filepath = os.path.join(root, f)
                    res = analyze_file(filepath)
                    results.append(res)
                    
    results.sort(key=lambda x: x.get('lines', 0), reverse=True)
    
    with open('ui_analysis_report.json', 'w') as json_file:
        json.dump(results, json_file, indent=2)
        
    print(f"Analysis complete. Found {len(results)} files. Wrote ui_analysis_report.json")

if __name__ == '__main__':
    main()
