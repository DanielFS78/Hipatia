# scripts/analyze_pila_controller.py
"""
Nombre del Módulo: scripts.analyze_pila_controller

Descripción: Script ejecutable (`analyze_pila_controller`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import ast
import os

def analyze(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} no existe.")
        return
        
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read(), filename=filepath)
    
    self_attributes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'self':
            self_attributes.add(node.attr)
    
    print(f"--- Atributos 'self.*' en {filepath} ---")
    for attr in sorted(self_attributes):
        print(f" - self.{attr}")

if __name__ == "__main__":
    analyze("controllers/pila_controller.py")
