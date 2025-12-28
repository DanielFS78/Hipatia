
import os
import ast
import sys

def analyze_file(filepath):
    """Parses a python file and extracts class and method defs, specifically looking for materials/components usage."""
    with open(filepath, 'r') as f:
        try:
            tree = ast.parse(f.read())
        except Exception:
            return {}
            
    analysis = {
        'classes': {},
        'imports': []
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            # rudimentary import capture
            if isinstance(node, ast.Import):
                for n in node.names:
                    analysis['imports'].append(n.name)
            else:
                module = node.module or ''
                for n in node.names:
                    analysis['imports'].append(f"{module}.{n.name}")

        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    args = [a.arg for a in item.args.args]
                    methods.append(f"{item.name}({', '.join(args)})")
            
            analysis['classes'][node.name] = methods
            
    return analysis

def scan_repository(root_dir):
    relevant_files = [
        'database/repositories/material_repository.py',
        'database/repositories/product_repository.py',
        'database/repositories/preproceso_repository.py',
        'controllers/product_controller.py',
        'ui/dialogs/prep_dialogs.py',
        'core/dtos.py',
        'core/app_model.py'
    ]
    
    print("# Análisis de Arquitectura: Materiales y Componentes\n")
    
    for rel_path in relevant_files:
        full_path = os.path.join(root_dir, rel_path)
        if os.path.exists(full_path):
            print(f"## Archivo: `{rel_path}`")
            data = analyze_file(full_path)
            
            if data['imports']:
                print("**Imports Relevantes:**")
                for imp in data['imports']:
                    if 'ui' in imp or 'database' in imp or 'core' in imp:
                        print(f"- {imp}")
            
            if data['classes']:
                print("\n**Clases y Métodos:**")
                for cls, methods in data['classes'].items():
                    print(f"- **{cls}**")
                    for method in methods:
                        # Highlight relevant methods
                        if any(k in method.lower() for k in ['material', 'componente', 'preproceso', 'dialog']):
                            print(f"  - `{method}` 👈")
                        else:
                            print(f"  - `{method}`")
            print("\n" + "="*50 + "\n")
        else:
            print(f"Warning: File not found: {rel_path}")

if __name__ == "__main__":
    scan_repository(os.getcwd())
