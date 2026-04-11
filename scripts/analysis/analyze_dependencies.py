"""
Nombre del Módulo: scripts.analysis.analyze_dependencies

Descripción: Funciones puras de apoyo (sin estado de proceso): ``get_imports``, ``analyze_dependencies``. Integración típica con: ``ast``, ``os``, ``sys``.
"""

import ast
import os
import sys
import collections
from typing import Dict, List, Set, Tuple

def get_imports(filepath: str) -> List[str]:
    imports = []
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports

def analyze_dependencies(root_dir: str):
    dependency_graph = collections.defaultdict(set)
    file_map = {} # filename -> full path

    # Build the graph
    for root, dirs, files in os.walk(root_dir):
        if any(d in root for d in ['.venv', 'venv', '.git', '__pycache__', 'env', '.idea']):
            continue
        
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                module_name = os.path.relpath(filepath, root_dir).replace(os.path.sep, ".").replace(".py", "")
                
                # Normalize module name for __init__ files
                if module_name.endswith(".__init__"):
                    module_name = module_name[:-9]
                
                file_map[module_name] = filepath
                
                imports = get_imports(filepath)
                for imp in imports:
                    # Filter for internal imports only
                    if imp.startswith(("core", "controllers", "ui", "database", "app", "config")):
                        dependency_graph[module_name].add(imp)

    # Detect Cycles (DFS)
    cycles = []
    visited = set()
    path: list[str] = []

    def visit(node):
        if node in path:
            cycle_start_index = path.index(node)
            cycles.append(path[cycle_start_index:])
            return
        if node in visited:
            return
        
        visited.add(node)
        path.append(node)
        
        for neighbor in dependency_graph.get(node, []):
             # Try to resolve neighbor to a known internal module
             # (Simple resolution, might miss some cases but good enough for now)
             if neighbor in file_map:
                 visit(neighbor)
             else:
                 # Check sub-packages
                 for known_module in file_map:
                     if neighbor.startswith(known_module + "."):
                         visit(known_module)
        
        path.pop()

    for module in list(dependency_graph.keys()):
        visit(module)
        
    # Analyze Most Imported Modules
    import_counts: collections.Counter[str] = collections.Counter()
    for module, deps in dependency_graph.items():
        for dep in deps:
             import_counts[dep] += 1

    return dependency_graph, cycles, import_counts

if __name__ == "__main__":
    project_root = "/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion"
    graph, cycles, counts = analyze_dependencies(project_root)
    
    print("--- Dependency Analysis Report ---")
    print(f"Total Internal Modules Tracked: {len(graph)}")
    print(f"Total Potential Circular Dependencies Detected: {len(cycles)}")
    
    if cycles:
        print("\n--- Detected Cycles (First 5) ---")
        for i, cycle in enumerate(cycles[:5]):
            print(f"{i+1}. {' -> '.join(cycle)} -> {cycle[0]}")
            
    print("\n--- Top 10 Most Imported Modules ---")
    for module, count in counts.most_common(10):
        print(f"{module}: imported {count} times")
