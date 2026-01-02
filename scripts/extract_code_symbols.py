#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
EXTRACTOR DE SÍMBOLOS DE CÓDIGO - FASE 4
=============================================================================
Este script extrae y documenta todos los símbolos (clases, funciones, métodos,
variables) de los archivos implementados en la Fase 4.

Uso:
    python scripts/extract_code_symbols.py

Salida:
    - Archivo JSON con todos los símbolos extraídos
    - Archivo Markdown con documentación legible
"""

import ast
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class CodeSymbolExtractor:
    """
    Extractor de símbolos de código Python usando AST.
    
    Extrae:
    - Clases con sus métodos y atributos
    - Funciones globales
    - Variables de módulo (constantes)
    - Imports
    """
    
    def __init__(self, file_path: str):
        """
        Inicializa el extractor.
        
        Args:
            file_path: Ruta al archivo Python a analizar
        """
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.symbols: Dict[str, Any] = {
            "file": file_path,
            "filename": self.filename,
            "classes": [],
            "functions": [],
            "constants": [],
            "imports": []
        }
    
    def extract(self) -> Dict[str, Any]:
        """
        Extrae todos los símbolos del archivo.
        
        Returns:
            Diccionario con todos los símbolos encontrados
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            self._process_module(tree)
            
        except Exception as e:
            self.symbols["error"] = str(e)
        
        return self.symbols
    
    def _process_module(self, tree: ast.Module):
        """Procesa el módulo completo."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._process_class(node)
            elif isinstance(node, ast.FunctionDef) and self._is_top_level(node, tree):
                self._process_function(node)
            elif isinstance(node, ast.AsyncFunctionDef) and self._is_top_level(node, tree):
                self._process_function(node)
            elif isinstance(node, ast.Import):
                self._process_import(node)
            elif isinstance(node, ast.ImportFrom):
                self._process_import_from(node)
            elif isinstance(node, ast.Assign) and self._is_top_level(node, tree):
                self._process_constant(node)
    
    def _is_top_level(self, node: ast.AST, tree: ast.Module) -> bool:
        """Verifica si un nodo está a nivel de módulo."""
        return node in tree.body
    
    def _get_docstring(self, node: ast.AST) -> Optional[str]:
        """Extrae el docstring de un nodo."""
        return ast.get_docstring(node)
    
    def _process_class(self, node: ast.ClassDef):
        """Procesa una definición de clase."""
        class_info = {
            "name": node.name,
            "lineno": node.lineno,
            "docstring": self._get_docstring(node),
            "bases": [self._get_name(base) for base in node.bases],
            "methods": [],
            "class_attributes": [],
            "instance_attributes": []
        }
        
        # Procesar métodos y atributos
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._process_method(item)
                class_info["methods"].append(method_info)
                
                # Buscar atributos de instancia en __init__
                if item.name == "__init__":
                    class_info["instance_attributes"] = self._extract_init_attributes(item)
                    
            elif isinstance(item, ast.Assign):
                # Atributos de clase
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_info["class_attributes"].append({
                            "name": target.id,
                            "lineno": item.lineno
                        })
        
        self.symbols["classes"].append(class_info)
    
    def _process_method(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Procesa un método de clase."""
        args = []
        for arg in node.args.args:
            arg_info = {"name": arg.arg}
            if arg.annotation:
                arg_info["type"] = self._get_annotation(arg.annotation)
            args.append(arg_info)
        
        method_info = {
            "name": node.name,
            "lineno": node.lineno,
            "docstring": self._get_docstring(node),
            "args": args,
            "is_property": any(
                isinstance(d, ast.Name) and d.id == "property" 
                for d in (node.decorator_list or [])
            ),
            "is_static": any(
                isinstance(d, ast.Name) and d.id == "staticmethod" 
                for d in (node.decorator_list or [])
            ),
            "is_classmethod": any(
                isinstance(d, ast.Name) and d.id == "classmethod" 
                for d in (node.decorator_list or [])
            ),
            "decorators": [self._get_name(d) for d in (node.decorator_list or [])]
        }
        
        if node.returns:
            method_info["return_type"] = self._get_annotation(node.returns)
        
        return method_info
    
    def _extract_init_attributes(self, init_node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Extrae atributos de instancia del método __init__."""
        attributes = []
        for node in ast.walk(init_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == "self":
                            attributes.append({
                                "name": target.attr,
                                "lineno": node.lineno
                            })
        return attributes
    
    def _process_function(self, node: ast.FunctionDef):
        """Procesa una función global."""
        args = []
        for arg in node.args.args:
            arg_info = {"name": arg.arg}
            if arg.annotation:
                arg_info["type"] = self._get_annotation(arg.annotation)
            args.append(arg_info)
        
        func_info = {
            "name": node.name,
            "lineno": node.lineno,
            "docstring": self._get_docstring(node),
            "args": args,
            "decorators": [self._get_name(d) for d in (node.decorator_list or [])]
        }
        
        if node.returns:
            func_info["return_type"] = self._get_annotation(node.returns)
        
        self.symbols["functions"].append(func_info)
    
    def _process_import(self, node: ast.Import):
        """Procesa un import."""
        for alias in node.names:
            self.symbols["imports"].append({
                "type": "import",
                "module": alias.name,
                "alias": alias.asname,
                "lineno": node.lineno
            })
    
    def _process_import_from(self, node: ast.ImportFrom):
        """Procesa un from ... import."""
        module = node.module or ""
        for alias in node.names:
            self.symbols["imports"].append({
                "type": "from",
                "module": module,
                "name": alias.name,
                "alias": alias.asname,
                "lineno": node.lineno
            })
    
    def _process_constant(self, node: ast.Assign):
        """Procesa una constante de módulo."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                # Considerar como constante si está en UPPERCASE o es tipo específico
                name = target.id
                if name.isupper() or not name.startswith("_"):
                    self.symbols["constants"].append({
                        "name": name,
                        "lineno": node.lineno
                    })
    
    def _get_name(self, node: ast.AST) -> str:
        """Obtiene el nombre de un nodo."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return str(node)
    
    def _get_annotation(self, node: ast.AST) -> str:
        """Convierte una anotación de tipo a string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_annotation(node.value)}[{self._get_annotation(node.slice)}]"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Tuple):
            return ", ".join(self._get_annotation(e) for e in node.elts)
        return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)


def generate_markdown_report(all_symbols: List[Dict[str, Any]], output_path: str):
    """
    Genera un informe en Markdown con todos los símbolos extraídos.
    
    Args:
        all_symbols: Lista de diccionarios con símbolos de cada archivo
        output_path: Ruta del archivo de salida
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Extracción de Símbolos de Código - Fase 4\n\n")
        f.write(f"**Fecha de generación:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        # Resumen
        total_classes = sum(len(s["classes"]) for s in all_symbols)
        total_functions = sum(len(s["functions"]) for s in all_symbols)
        total_methods = sum(
            sum(len(c["methods"]) for c in s["classes"]) 
            for s in all_symbols
        )
        
        f.write("## Resumen\n\n")
        f.write(f"| Métrica | Cantidad |\n")
        f.write(f"|---------|----------|\n")
        f.write(f"| Archivos analizados | {len(all_symbols)} |\n")
        f.write(f"| Clases | {total_classes} |\n")
        f.write(f"| Métodos | {total_methods} |\n")
        f.write(f"| Funciones globales | {total_functions} |\n\n")
        
        f.write("---\n\n")
        
        # Detalle por archivo
        for symbols in all_symbols:
            f.write(f"## {symbols['filename']}\n\n")
            f.write(f"**Ruta:** `{symbols['file']}`\n\n")
            
            if symbols.get("error"):
                f.write(f"⚠️ **Error:** {symbols['error']}\n\n")
                continue
            
            # Clases
            if symbols["classes"]:
                f.write("### Clases\n\n")
                for cls in symbols["classes"]:
                    bases_str = f" (hereda de: {', '.join(cls['bases'])})" if cls['bases'] else ""
                    f.write(f"#### `{cls['name']}`{bases_str}\n\n")
                    
                    if cls.get("docstring"):
                        f.write(f"> {cls['docstring'][:200]}{'...' if len(cls.get('docstring', '')) > 200 else ''}\n\n")
                    
                    # Atributos de instancia
                    if cls["instance_attributes"]:
                        f.write("**Atributos de instancia:**\n")
                        for attr in cls["instance_attributes"]:
                            f.write(f"- `self.{attr['name']}` (línea {attr['lineno']})\n")
                        f.write("\n")
                    
                    # Atributos de clase
                    if cls["class_attributes"]:
                        f.write("**Atributos de clase:**\n")
                        for attr in cls["class_attributes"]:
                            f.write(f"- `{attr['name']}` (línea {attr['lineno']})\n")
                        f.write("\n")
                    
                    # Métodos
                    if cls["methods"]:
                        f.write("**Métodos:**\n\n")
                        f.write("| Método | Línea | Args | Decoradores |\n")
                        f.write("|--------|-------|------|-------------|\n")
                        for method in cls["methods"]:
                            args = ", ".join(a["name"] for a in method["args"])
                            decorators = ", ".join(method.get("decorators", []))
                            f.write(f"| `{method['name']}` | {method['lineno']} | {args} | {decorators or '-'} |\n")
                        f.write("\n")
            
            # Funciones globales
            if symbols["functions"]:
                f.write("### Funciones Globales\n\n")
                f.write("| Función | Línea | Args |\n")
                f.write("|---------|-------|------|\n")
                for func in symbols["functions"]:
                    args = ", ".join(a["name"] for a in func["args"])
                    f.write(f"| `{func['name']}` | {func['lineno']} | {args} |\n")
                f.write("\n")
            
            # Constantes
            if symbols["constants"]:
                f.write("### Variables/Constantes de Módulo\n\n")
                for const in symbols["constants"]:
                    f.write(f"- `{const['name']}` (línea {const['lineno']})\n")
                f.write("\n")
            
            f.write("---\n\n")


def main():
    """Punto de entrada principal del script."""
    # Directorio base del proyecto
    base_dir = Path(__file__).parent.parent
    
    # Archivos de Fase 4 a analizar
    phase4_files = [
        base_dir / "core" / "production_context.py",
        base_dir / "core" / "tracking_dtos.py",
        base_dir / "core" / "qr_scanner.py",
        base_dir / "features" / "worker_controller.py",
        base_dir / "database" / "repositories" / "tracking_repository.py",
        base_dir / "ui" / "dialogs" / "tracking_dialogs.py",
    ]
    
    print("=" * 70)
    print("EXTRACTOR DE SÍMBOLOS DE CÓDIGO - FASE 4")
    print("=" * 70)
    print()
    
    all_symbols = []
    
    for file_path in phase4_files:
        if file_path.exists():
            print(f"📄 Analizando: {file_path.name}")
            extractor = CodeSymbolExtractor(str(file_path))
            symbols = extractor.extract()
            all_symbols.append(symbols)
            
            # Mostrar resumen
            num_classes = len(symbols.get("classes", []))
            num_methods = sum(len(c.get("methods", [])) for c in symbols.get("classes", []))
            num_functions = len(symbols.get("functions", []))
            print(f"   ├── Clases: {num_classes}")
            print(f"   ├── Métodos: {num_methods}")
            print(f"   └── Funciones: {num_functions}")
            print()
        else:
            print(f"⚠️  Archivo no encontrado: {file_path}")
            all_symbols.append({
                "file": str(file_path),
                "filename": file_path.name,
                "error": "Archivo no encontrado"
            })
    
    # Directorio de salida
    output_dir = base_dir / "Documentacion" / "Fase 4" / "code_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar JSON
    json_path = output_dir / "phase4_symbols.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_symbols, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON guardado: {json_path}")
    
    # Guardar Markdown
    md_path = output_dir / "phase4_symbols_report.md"
    generate_markdown_report(all_symbols, str(md_path))
    print(f"✅ Markdown guardado: {md_path}")
    
    print()
    print("=" * 70)
    print("EXTRACCIÓN COMPLETADA")
    print("=" * 70)


if __name__ == "__main__":
    main()
