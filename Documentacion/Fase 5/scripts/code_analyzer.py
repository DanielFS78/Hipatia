# -*- coding: utf-8 -*-
"""
Script para analizar archivos Python y extraer información estructural.
Extrae clases, funciones, métodos y variables de módulo.
"""
import ast
import sys
import os
from pathlib import Path
from typing import List, Dict, Any


class CodeAnalyzer(ast.NodeVisitor):
    """Analiza un archivo Python y extrae su estructura."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.classes: List[Dict[str, Any]] = []
        self.functions: List[Dict[str, Any]] = []
        self.module_variables: List[Dict[str, Any]] = []
        self.imports: List[str] = []
        self.current_class = None
    
    def analyze(self, source_code: str) -> Dict[str, Any]:
        """Analiza el código fuente y retorna la estructura."""
        try:
            tree = ast.parse(source_code)
            self.visit(tree)
            return {
                "filename": self.filename,
                "classes": self.classes,
                "functions": self.functions,
                "module_variables": self.module_variables,
                "imports": self.imports
            }
        except SyntaxError as e:
            return {"filename": self.filename, "error": str(e)}
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            self.imports.append(f"{module}.{alias.name}")
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        class_info = {
            "name": node.name,
            "lineno": node.lineno,
            "end_lineno": getattr(node, 'end_lineno', None),
            "bases": [self._get_name(base) for base in node.bases],
            "docstring": ast.get_docstring(node),
            "methods": [],
            "class_variables": []
        }
        
        old_class = self.current_class
        self.current_class = class_info
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._extract_function(item)
                class_info["methods"].append(method_info)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_info["class_variables"].append({
                            "name": target.id,
                            "lineno": item.lineno
                        })
        
        self.classes.append(class_info)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node):
        if self.current_class is None:
            func_info = self._extract_function(node)
            self.functions.append(func_info)
    
    def visit_AsyncFunctionDef(self, node):
        if self.current_class is None:
            func_info = self._extract_function(node)
            func_info["is_async"] = True
            self.functions.append(func_info)
    
    def visit_Assign(self, node):
        if self.current_class is None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.module_variables.append({
                        "name": target.id,
                        "lineno": node.lineno
                    })
    
    def _extract_function(self, node) -> Dict[str, Any]:
        args = []
        for arg in node.args.args:
            arg_info = {"name": arg.arg}
            if arg.annotation:
                arg_info["type"] = self._get_name(arg.annotation)
            args.append(arg_info)
        
        return {
            "name": node.name,
            "lineno": node.lineno,
            "end_lineno": getattr(node, 'end_lineno', None),
            "args": args,
            "docstring": ast.get_docstring(node),
            "decorators": [self._get_name(d) for d in node.decorator_list],
            "returns": self._get_name(node.returns) if node.returns else None
        }
    
    def _get_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[{self._get_name(node.slice)}]"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Tuple):
            return ", ".join(self._get_name(e) for e in node.elts)
        return str(type(node).__name__)


def format_markdown(analysis: Dict[str, Any]) -> str:
    """Convierte el análisis a formato Markdown."""
    lines = []
    filename = Path(analysis['filename']).name
    lines.append(f"# Análisis de `{filename}`\n")
    lines.append(f"**Ruta completa:** `{analysis['filename']}`\n")
    
    if "error" in analysis:
        lines.append(f"\n> **Error de sintaxis:** {analysis['error']}\n")
        return "\n".join(lines)
    
    # Imports
    if analysis['imports']:
        lines.append("\n## Importaciones")
        for imp in sorted(set(analysis['imports'])):
            lines.append(f"- `{imp}`")
    
    # Variables de módulo
    if analysis['module_variables']:
        lines.append("\n## Variables de Módulo")
        for var in analysis['module_variables']:
            lines.append(f"- `{var['name']}` (línea {var['lineno']})")
    
    # Funciones
    if analysis['functions']:
        lines.append("\n## Funciones")
        for func in analysis['functions']:
            sig = _format_signature(func)
            lines.append(f"\n### `{func['name']}`")
            lines.append(f"- **Línea:** {func['lineno']}")
            lines.append(f"- **Firma:** `{sig}`")
            if func['docstring']:
                lines.append(f"- **Docstring:** {func['docstring'][:200]}...")
    
    # Clases
    if analysis['classes']:
        lines.append("\n## Clases")
        for cls in analysis['classes']:
            lines.append(f"\n### Clase `{cls['name']}`")
            lines.append(f"- **Línea:** {cls['lineno']}")
            if cls['bases']:
                lines.append(f"- **Hereda de:** {', '.join(f'`{b}`' for b in cls['bases'])}")
            if cls['docstring']:
                lines.append(f"- **Docstring:** {cls['docstring'][:200]}...")
            
            if cls['class_variables']:
                lines.append("\n#### Variables de Clase")
                for var in cls['class_variables']:
                    lines.append(f"- `{var['name']}`")
            
            if cls['methods']:
                lines.append("\n#### Métodos")
                for method in cls['methods']:
                    sig = _format_signature(method)
                    lines.append(f"- `{method['name']}`({sig})")
                    if method['docstring']:
                        doc_preview = method['docstring'].split('\n')[0][:80]
                        lines.append(f"  - _{doc_preview}_")
    
    return "\n".join(lines)


def _format_signature(func: Dict[str, Any]) -> str:
    """Formatea la firma de una función."""
    args = []
    for arg in func['args']:
        if 'type' in arg:
            args.append(f"{arg['name']}: {arg['type']}")
        else:
            args.append(arg['name'])
    return ", ".join(args)


def analyze_file(filepath: str) -> Dict[str, Any]:
    """Analiza un archivo Python."""
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    analyzer = CodeAnalyzer(filepath)
    return analyzer.analyze(source)


def main():
    if len(sys.argv) < 2:
        print("Uso: python code_analyzer.py <archivo.py> [<archivo2.py> ...]")
        print("     python code_analyzer.py --dir <directorio>")
        sys.exit(1)
    
    files_to_analyze = []
    
    if sys.argv[1] == "--dir":
        directory = Path(sys.argv[2])
        files_to_analyze = list(directory.rglob("*.py"))
    else:
        files_to_analyze = [Path(f) for f in sys.argv[1:]]
    
    for filepath in files_to_analyze:
        if not filepath.exists():
            print(f"Archivo no encontrado: {filepath}")
            continue
        
        analysis = analyze_file(str(filepath))
        markdown = format_markdown(analysis)
        
        # Guardar resultado
        output_name = filepath.stem + "_analysis.md"
        output_path = filepath.parent / output_name
        
        print(f"Analizando: {filepath}")
        print(markdown)
        print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
