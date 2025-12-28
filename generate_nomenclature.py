
import ast
import os
from datetime import datetime

def generate_nomenclature(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    tree = ast.parse(source)
    lines = source.splitlines()
    total_lines = len(lines)
    
    class_node = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == 'AppController':
            class_node = node
            break
            
    if not class_node:
        print("AppController class not found")
        return

    public_methods = []
    private_methods = []
    
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef):
            method_name = node.name
            lineno = node.lineno
            args = [a.arg for a in node.args.args]
            
            # Extract local variables (simple heuristic)
            local_vars = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                    local_vars.add(child.id)
            
            # Remove args from local_vars
            for arg in args:
                if arg in local_vars:
                    local_vars.remove(arg)
            
            method_info = {
                'name': method_name,
                'line': lineno,
                'args': ", ".join(args),
                'vars': ", ".join(sorted(list(local_vars))[:5]) + (" (+...)" if len(local_vars) > 5 else "")
            }
            
            if method_name.startswith('_') and not method_name.startswith('__'):
                private_methods.append(method_info)
            elif not method_name.startswith('__'):
                public_methods.append(method_info)

    # Generate Markdown
    md = f"# Nomenclatura AppController\n\n"
    md += f"> Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    md += f"## Resumen\n\n"
    md += f"| Métrica | Valor |\n"
    md += f"|---------|-------|\n"
    md += f"| Total de líneas | {total_lines} |\n"
    md += f"| Clases | 1 |\n"
    md += f"| Métodos totales | {len(public_methods) + len(private_methods)} |\n\n"
    
    md += f"## Clase: `AppController`\n\n"
    md += f"**Línea de inicio**: {class_node.lineno}\n\n"
    
    md += f"### Métodos Públicos\n\n"
    md += f"| Método | Línea | Parámetros | Variables Locales |\n"
    md += f"|--------|-------|------------|-------------------|\n"
    for m in sorted(public_methods, key=lambda x: x['line']):
        md += f"| `{m['name']}` | {m['line']} | {m['args']} | {m['vars']} |\n"
        
    md += f"\n### Métodos Privados\n\n"
    md += f"| Método | Línea | Parámetros | Variables Locales |\n"
    md += f"|--------|-------|------------|-------------------|\n"
    for m in sorted(private_methods, key=lambda x: x['line']):
        md += f"| `{m['name']}` | {m['line']} | {m['args']} | {m['vars']} |\n"

    print(md)

if __name__ == "__main__":
    generate_nomenclature('controllers/app_controller.py')
