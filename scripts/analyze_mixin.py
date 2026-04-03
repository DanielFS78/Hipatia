"""
Analiza un archivo Python (clase grande o módulo acoplado): lista atributos y llamadas vía self.*
Útil para planificar extracción a composición o a gestores independientes.
"""

import ast
import sys
import os

def analyze(filepath):
    if not os.path.exists(filepath):
        print(f"Error: El archivo {filepath} no existe.")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=filepath)
    
    self_attributes = set()
    self_calls = set()
    
    for node in ast.walk(tree):
        # Detectar usos de self.atributo
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'self':
            self_attributes.add(node.attr)
        
        # Detectar llamadas a self.metodo(...)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
           isinstance(node.func.value, ast.Name) and node.func.value.id == 'self':
            self_calls.add(node.func.attr)
    
    print(f"\n--- Análisis de {os.path.basename(filepath)} ---")
    print(f"Ruta: {filepath}")
    
    print("\n[Dependencias de Atributos (self.attr)]")
    attrs = sorted(list(self_attributes - self_calls))
    if attrs:
        for attr in attrs:
            print(f" - {attr}")
    else:
        print(" (Ninguno detectado directamente)")

    print("\n[Llamadas Internas/Externas (self.method())]")
    calls = sorted(list(self_calls))
    if calls:
        for call in calls:
            print(f" - {call}")
    else:
        print(" (Ninguno detectado directamente)")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            analyze(path)
    else:
        print("Uso: python3 scripts/analyze_mixin.py <ruta_archivo1.py> [ruta_archivo2.py ...]")
