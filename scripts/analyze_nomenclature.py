#!/usr/bin/env python3
"""
Script para analizar AppController y extraer su nomenclatura.
Genera un archivo Markdown con clases, funciones y variables.
"""
import ast
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def extract_variable_names(node):
    """Extrae nombres de variables de un nodo AST."""
    variables = set()
    
    for child in ast.walk(node):
        # Variables asignadas (Name en lado izquierdo de Assign)
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if isinstance(target, ast.Name):
                    variables.add(target.id)
                elif isinstance(target, ast.Tuple):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            variables.add(elt.id)
        # Variables asignadas con AugAssign (+=, -=, etc.)
        elif isinstance(child, ast.AugAssign):
            if isinstance(child.target, ast.Name):
                variables.add(child.target.id)
        # Variables en for loops
        elif isinstance(child, ast.For):
            if isinstance(child.target, ast.Name):
                variables.add(child.target.id)
            elif isinstance(child.target, ast.Tuple):
                for elt in child.target.elts:
                    if isinstance(elt, ast.Name):
                        variables.add(elt.id)
        # Variables en with statements
        elif isinstance(child, ast.With):
            for item in child.items:
                if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                    variables.add(item.optional_vars.id)
        # Variables en except handlers
        elif isinstance(child, ast.ExceptHandler):
            if child.name:
                variables.add(child.name)
        # Named expressions (walrus operator :=)
        elif isinstance(child, ast.NamedExpr):
            if isinstance(child.target, ast.Name):
                variables.add(child.target.id)
    
    return variables


def analyze_function(func_node):
    """Analiza una función y extrae su información."""
    # Extraer parámetros
    params = []
    for arg in func_node.args.args:
        params.append(arg.arg)
    for arg in func_node.args.kwonlyargs:
        params.append(arg.arg)
    if func_node.args.vararg:
        params.append(f"*{func_node.args.vararg.arg}")
    if func_node.args.kwarg:
        params.append(f"**{func_node.args.kwarg.arg}")
    
    # Extraer variables locales
    local_vars = extract_variable_names(func_node)
    
    # Filtrar parámetros de variables locales
    local_vars = local_vars - set(params) - {'self', 'cls'}
    
    # Extraer docstring si existe
    docstring = ast.get_docstring(func_node) or ""
    first_line = docstring.split('\n')[0] if docstring else ""
    
    return {
        'name': func_node.name,
        'params': params,
        'variables': sorted(local_vars),
        'docstring': first_line,
        'lineno': func_node.lineno,
        'end_lineno': getattr(func_node, 'end_lineno', func_node.lineno),
        'is_private': func_node.name.startswith('_'),
        'is_dunder': func_node.name.startswith('__') and func_node.name.endswith('__'),
    }


def analyze_class(class_node):
    """Analiza una clase y extrae su información."""
    methods = []
    class_variables = set()
    
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            methods.append(analyze_function(node))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    class_variables.add(target.id)
    
    docstring = ast.get_docstring(class_node) or ""
    first_line = docstring.split('\n')[0] if docstring else ""
    
    return {
        'name': class_node.name,
        'docstring': first_line,
        'methods': methods,
        'class_variables': sorted(class_variables),
        'lineno': class_node.lineno,
        'bases': [ast.unparse(base) if hasattr(ast, 'unparse') else str(base) for base in class_node.bases],
    }


def analyze_file(file_path):
    """Analiza un archivo Python y extrae toda su información."""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    tree = ast.parse(source, filename=str(file_path))
    
    classes = []
    module_functions = []
    module_variables = set()
    imports = []
    
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(analyze_class(node))
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            module_functions.append(analyze_function(node))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    module_variables.add(target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            else:
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
    
    return {
        'classes': classes,
        'module_functions': module_functions,
        'module_variables': sorted(module_variables),
        'imports': imports,
        'total_lines': len(source.splitlines()),
    }


def generate_markdown(analysis, output_path):
    """Genera el archivo Markdown con la nomenclatura."""
    lines = []
    
    lines.append("# Nomenclatura AppController")
    lines.append("")
    lines.append(f"> Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    
    # Resumen
    lines.append("## Resumen")
    lines.append("")
    total_methods = sum(len(c['methods']) for c in analysis['classes'])
    lines.append(f"| Métrica | Valor |")
    lines.append(f"|---------|-------|")
    lines.append(f"| Total de líneas | {analysis['total_lines']} |")
    lines.append(f"| Clases | {len(analysis['classes'])} |")
    lines.append(f"| Métodos totales | {total_methods} |")
    lines.append(f"| Funciones de módulo | {len(analysis['module_functions'])} |")
    lines.append(f"| Variables de módulo | {len(analysis['module_variables'])} |")
    lines.append("")
    
    # Variables de módulo
    if analysis['module_variables']:
        lines.append("## Variables de Módulo")
        lines.append("")
        for var in analysis['module_variables']:
            lines.append(f"- `{var}`")
        lines.append("")
    
    # Funciones de módulo
    if analysis['module_functions']:
        lines.append("## Funciones de Módulo")
        lines.append("")
        for func in analysis['module_functions']:
            params_str = ", ".join(func['params'][:5])
            if len(func['params']) > 5:
                params_str += ", ..."
            lines.append(f"### `{func['name']}({params_str})`")
            lines.append(f"- **Línea**: {func['lineno']}")
            if func['docstring']:
                lines.append(f"- **Descripción**: {func['docstring'][:100]}...")
            if func['variables']:
                lines.append(f"- **Variables**: `{'`, `'.join(func['variables'][:10])}`")
            lines.append("")
    
    # Clases
    for cls in analysis['classes']:
        lines.append(f"## Clase: `{cls['name']}`")
        lines.append("")
        if cls['bases']:
            lines.append(f"**Hereda de**: {', '.join(cls['bases'])}")
            lines.append("")
        if cls['docstring']:
            lines.append(f"**Descripción**: {cls['docstring']}")
            lines.append("")
        lines.append(f"**Línea de inicio**: {cls['lineno']}")
        lines.append(f"**Total de métodos**: {len(cls['methods'])}")
        lines.append("")
        
        # Variables de clase
        if cls['class_variables']:
            lines.append("### Variables de Clase")
            lines.append("")
            for var in cls['class_variables']:
                lines.append(f"- `{var}`")
            lines.append("")
        
        # Clasificar métodos
        dunder_methods = [m for m in cls['methods'] if m['is_dunder']]
        private_methods = [m for m in cls['methods'] if m['is_private'] and not m['is_dunder']]
        public_methods = [m for m in cls['methods'] if not m['is_private']]
        
        # Tabla de métodos públicos
        if public_methods:
            lines.append("### Métodos Públicos")
            lines.append("")
            lines.append("| Método | Línea | Parámetros | Variables Locales |")
            lines.append("|--------|-------|------------|-------------------|")
            for m in public_methods:
                params = ", ".join(m['params'][:3]) or "-"
                if len(m['params']) > 3:
                    params += ", ..."
                vars_str = ", ".join(m['variables'][:5]) or "-"
                if len(m['variables']) > 5:
                    vars_str += f" (+{len(m['variables'])-5})"
                lines.append(f"| `{m['name']}` | {m['lineno']} | {params} | {vars_str} |")
            lines.append("")
        
        # Tabla de métodos privados
        if private_methods:
            lines.append("### Métodos Privados")
            lines.append("")
            lines.append("| Método | Línea | Parámetros | Variables Locales |")
            lines.append("|--------|-------|------------|-------------------|")
            for m in private_methods:
                params = ", ".join(m['params'][:3]) or "-"
                if len(m['params']) > 3:
                    params += ", ..."
                vars_str = ", ".join(m['variables'][:5]) or "-"
                if len(m['variables']) > 5:
                    vars_str += f" (+{len(m['variables'])-5})"
                lines.append(f"| `{m['name']}` | {m['lineno']} | {params} | {vars_str} |")
            lines.append("")
        
        # Métodos dunder (más compacto)
        if dunder_methods:
            lines.append("### Métodos Especiales (Dunder)")
            lines.append("")
            dunder_names = [f"`{m['name']}`" for m in dunder_methods]
            lines.append(", ".join(dunder_names))
            lines.append("")
    
    # Escribir archivo
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return len(lines)


def main():
    # Rutas
    base_path = Path(__file__).parent.parent if __file__ else Path.cwd()
    app_controller_path = base_path / "controllers" / "app_controller.py"
    output_path = base_path / "Documentacion" / "Fase 3" / "Nomenclatura_AppController.md"
    
    # Si se pasa argumento, usar ese archivo
    if len(sys.argv) > 1:
        app_controller_path = Path(sys.argv[1])
    
    if not app_controller_path.exists():
        print(f"Error: No se encontró el archivo {app_controller_path}")
        return 1
    
    print(f"Analizando: {app_controller_path}")
    
    # Analizar
    analysis = analyze_file(app_controller_path)
    
    # Crear directorio si no existe
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generar Markdown
    lines_written = generate_markdown(analysis, output_path)
    
    print(f"\n✅ Análisis completado:")
    print(f"   - Clases encontradas: {len(analysis['classes'])}")
    for cls in analysis['classes']:
        print(f"     • {cls['name']}: {len(cls['methods'])} métodos")
    print(f"   - Funciones de módulo: {len(analysis['module_functions'])}")
    print(f"   - Variables de módulo: {len(analysis['module_variables'])}")
    print(f"\n📄 Archivo generado: {output_path}")
    print(f"   - Líneas escritas: {lines_written}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
