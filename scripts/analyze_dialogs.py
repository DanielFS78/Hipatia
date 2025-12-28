#!/usr/bin/env python3
"""
Script de Análisis de ui/dialogs.py
====================================
Fase 3.7: Extrae todas las clases, métodos, atributos y nomenclatura
del archivo dialogs.py para documentación y posterior creación de tests.

Genera un archivo Markdown con el análisis completo.
"""

import ast
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DIALOGS_PATH = BASE_DIR / "ui" / "dialogs.py"
OUTPUT_PATH = BASE_DIR / "Documentacion" / "Fase 3" / "Fase_3_7_Analisis_Dialogs.md"


class DialogAnalyzer(ast.NodeVisitor):
    """Analiza un archivo Python y extrae información de clases y métodos."""
    
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.source_lines = source_code.splitlines()
        self.classes: Dict[str, dict] = {}
        self.imports: List[str] = []
        self.global_variables: List[dict] = []
        self.current_class: Optional[str] = None
        
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            self.imports.append(f"{module}.{alias.name}")
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Extrae información de cada clase."""
        class_info = {
            "name": node.name,
            "line_start": node.lineno,
            "line_end": node.end_lineno,
            "bases": [self._get_name(base) for base in node.bases],
            "docstring": ast.get_docstring(node) or "",
            "methods": [],
            "class_attributes": [],
            "instance_attributes": [],
            "signals": [],
            "decorators": [self._get_name(d) for d in node.decorator_list]
        }
        
        # Guardar contexto de clase actual
        self.current_class = node.name
        
        # Analizar el cuerpo de la clase
        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                method_info = self._analyze_method(item)
                class_info["methods"].append(method_info)
                
                # Extraer atributos de instancia desde __init__
                if item.name == "__init__":
                    class_info["instance_attributes"] = self._extract_instance_attrs(item)
                    
            elif isinstance(item, ast.Assign):
                # Atributos de clase
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_info = {
                            "name": target.id,
                            "line": item.lineno,
                            "is_signal": self._is_pyqt_signal(item.value)
                        }
                        if attr_info["is_signal"]:
                            class_info["signals"].append(attr_info)
                        else:
                            class_info["class_attributes"].append(attr_info)
        
        self.classes[node.name] = class_info
        self.current_class = None
        self.generic_visit(node)
        
    def _analyze_method(self, node: ast.FunctionDef) -> dict:
        """Analiza un método y extrae su información."""
        # Obtener argumentos
        args = []
        for arg in node.args.args:
            arg_name = arg.arg
            arg_annotation = ""
            if arg.annotation:
                arg_annotation = self._get_annotation(arg.annotation)
            args.append({"name": arg_name, "type": arg_annotation})
        
        # Obtener retorno
        return_type = ""
        if node.returns:
            return_type = self._get_annotation(node.returns)
        
        # Analizar complejidad básica (número de if, for, while, try)
        complexity = self._calculate_complexity(node)
        
        # Detectar dependencias externas (llamadas a otros métodos)
        dependencies = self._extract_dependencies(node)
        
        return {
            "name": node.name,
            "line_start": node.lineno,
            "line_end": node.end_lineno,
            "args": args,
            "return_type": return_type,
            "docstring": ast.get_docstring(node) or "",
            "decorators": [self._get_name(d) for d in node.decorator_list],
            "is_private": node.name.startswith("_") and not node.name.startswith("__"),
            "is_dunder": node.name.startswith("__") and node.name.endswith("__"),
            "complexity": complexity,
            "dependencies": dependencies,
            "lines": node.end_lineno - node.lineno + 1
        }
    
    def _extract_instance_attrs(self, init_node: ast.FunctionDef) -> List[dict]:
        """Extrae atributos de instancia definidos en __init__."""
        attrs = []
        for node in ast.walk(init_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == "self":
                            attrs.append({
                                "name": target.attr,
                                "line": node.lineno
                            })
        return attrs
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calcula complejidad ciclomática básica."""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, 
                                  ast.ExceptHandler, ast.With, ast.Assert,
                                  ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Cada 'and'/'or' añade complejidad
                complexity += len(child.values) - 1
        return complexity
    
    def _extract_dependencies(self, node: ast.FunctionDef) -> List[str]:
        """Extrae nombres de métodos llamados dentro de esta función."""
        dependencies = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if isinstance(child.func.value, ast.Name):
                        if child.func.value.id == "self":
                            dependencies.add(f"self.{child.func.attr}")
                        else:
                            dependencies.add(f"{child.func.value.id}.{child.func.attr}")
                    elif isinstance(child.func.value, ast.Attribute):
                        # self.widget.method()
                        if (isinstance(child.func.value.value, ast.Name) and 
                            child.func.value.value.id == "self"):
                            dependencies.add(f"self.{child.func.value.attr}.{child.func.attr}")
        return sorted(list(dependencies))
    
    def _is_pyqt_signal(self, node) -> bool:
        """Detecta si un valor es una señal de PyQt."""
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "pyqtSignal":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "pyqtSignal":
                return True
        return False
    
    def _get_name(self, node) -> str:
        """Obtiene el nombre de un nodo AST."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[...]"
        return str(type(node).__name__)
    
    def _get_annotation(self, node) -> str:
        """Convierte una anotación de tipo a string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[{self._get_annotation(node.slice)}]"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Tuple):
            return f"({', '.join(self._get_annotation(e) for e in node.elts)})"
        return "Any"


def generate_markdown_report(analyzer: DialogAnalyzer, file_path: Path) -> str:
    """Genera el reporte en formato Markdown."""
    
    # Estadísticas generales
    total_lines = len(analyzer.source_lines)
    total_classes = len(analyzer.classes)
    total_methods = sum(len(c["methods"]) for c in analyzer.classes.values())
    total_signals = sum(len(c["signals"]) for c in analyzer.classes.values())
    
    # Clasificar clases por tipo (basado en nombre de clase base)
    class_categories = defaultdict(list)
    for class_name, class_info in analyzer.classes.items():
        if "QDialog" in class_info["bases"]:
            class_categories["Diálogos (QDialog)"].append(class_name)
        elif "QWidget" in class_info["bases"]:
            class_categories["Widgets (QWidget)"].append(class_name)
        elif "QFrame" in class_info["bases"]:
            class_categories["Frames (QFrame)"].append(class_name)
        elif "QGraphicsEffect" in "".join(class_info["bases"]):
            class_categories["Efectos Gráficos"].append(class_name)
        else:
            class_categories["Otros"].append(class_name)
    
    # Generar markdown
    md = []
    md.append("# Fase 3.7: Análisis Completo de `ui/dialogs.py`")
    md.append("")
    md.append(f"> **Fecha de generación:** {datetime.now().strftime('%d de %B de %Y, %H:%M')}")
    md.append(f"> **Archivo analizado:** `{file_path}`")
    md.append("> **Generado por:** `scripts/analyze_dialogs.py`")
    md.append("")
    md.append("---")
    md.append("")
    
    # Resumen ejecutivo
    md.append("## 1. Resumen Ejecutivo")
    md.append("")
    md.append("| Métrica | Valor |")
    md.append("|---------|-------|")
    md.append(f"| **Líneas totales** | {total_lines:,} |")
    md.append(f"| **Clases definidas** | {total_classes} |")
    md.append(f"| **Métodos totales** | {total_methods} |")
    md.append(f"| **Señales PyQt** | {total_signals} |")
    md.append(f"| **Bytes** | {len(analyzer.source_code):,} |")
    md.append("")
    
    # Categorías de clases
    md.append("### 1.1 Clasificación por Tipo")
    md.append("")
    md.append("| Categoría | Cantidad | Clases |")
    md.append("|-----------|----------|--------|")
    for category, classes in sorted(class_categories.items()):
        classes_str = ", ".join(f"`{c}`" for c in sorted(classes)[:3])
        if len(classes) > 3:
            classes_str += f" (+{len(classes)-3} más)"
        md.append(f"| {category} | {len(classes)} | {classes_str} |")
    md.append("")
    
    # Top 10 clases más grandes
    md.append("### 1.2 Top 10 Clases por Tamaño")
    md.append("")
    sorted_classes = sorted(
        analyzer.classes.values(),
        key=lambda c: c["line_end"] - c["line_start"],
        reverse=True
    )[:10]
    
    md.append("| Clase | Líneas | Métodos | Complejidad Total |")
    md.append("|-------|--------|---------|-------------------|")
    for cls in sorted_classes:
        lines = cls["line_end"] - cls["line_start"]
        methods = len(cls["methods"])
        complexity = sum(m["complexity"] for m in cls["methods"])
        md.append(f"| `{cls['name']}` | {lines} | {methods} | {complexity} |")
    md.append("")
    
    md.append("---")
    md.append("")
    
    # Detalle de cada clase
    md.append("## 2. Detalle de Clases")
    md.append("")
    
    for class_name in sorted(analyzer.classes.keys()):
        class_info = analyzer.classes[class_name]
        
        md.append(f"### 2.{list(sorted(analyzer.classes.keys())).index(class_name)+1} `{class_name}`")
        md.append("")
        md.append(f"- **Líneas:** {class_info['line_start']} - {class_info['line_end']} ({class_info['line_end'] - class_info['line_start']} líneas)")
        md.append(f"- **Herencia:** {', '.join(f'`{b}`' for b in class_info['bases']) or 'Ninguna'}")
        
        if class_info["docstring"]:
            md.append(f"- **Descripción:** {class_info['docstring'][:200]}{'...' if len(class_info['docstring']) > 200 else ''}")
        
        # Señales
        if class_info["signals"]:
            md.append(f"- **Señales:** {', '.join(f'`{s['name']}`' for s in class_info['signals'])}")
        
        md.append("")
        
        # Tabla de métodos
        if class_info["methods"]:
            md.append("#### Métodos")
            md.append("")
            md.append("| Método | Líneas | Complejidad | Privado | Dependencias |")
            md.append("|--------|--------|-------------|---------|--------------|")
            
            for method in sorted(class_info["methods"], key=lambda m: m["line_start"]):
                deps = len(method["dependencies"])
                dep_str = f"{deps} deps" if deps > 0 else "-"
                private = "✓" if method["is_private"] else ""
                md.append(f"| `{method['name']}` | {method['lines']} | {method['complexity']} | {private} | {dep_str} |")
            
            md.append("")
        
        md.append("---")
        md.append("")
    
    # Nomenclatura y patrones
    md.append("## 3. Nomenclatura y Patrones Detectados")
    md.append("")
    
    # Prefijos de métodos más comunes
    method_prefixes = defaultdict(int)
    for class_info in analyzer.classes.values():
        for method in class_info["methods"]:
            name = method["name"]
            if name.startswith("_"):
                name = name[1:]  # Quitar un underscore
            if name.startswith("_"):
                name = name[1:]  # Quitar segundo underscore (dunder)
            
            parts = name.split("_")
            if len(parts) > 1:
                prefix = parts[0]
                if prefix not in ("init", "str", "repr"):
                    method_prefixes[prefix] += 1
    
    md.append("### 3.1 Prefijos de Métodos")
    md.append("")
    md.append("| Prefijo | Cantidad | Ejemplos de uso |")
    md.append("|---------|----------|-----------------|")
    
    for prefix, count in sorted(method_prefixes.items(), key=lambda x: -x[1])[:15]:
        # Encontrar ejemplos
        examples = []
        for class_info in analyzer.classes.values():
            for method in class_info["methods"]:
                if method["name"].lstrip("_").startswith(f"{prefix}_"):
                    examples.append(method["name"])
                    if len(examples) >= 2:
                        break
            if len(examples) >= 2:
                break
        
        examples_str = ", ".join(f"`{e}`" for e in examples[:2])
        md.append(f"| `{prefix}_*` | {count} | {examples_str} |")
    
    md.append("")
    
    # Atributos de instancia más comunes
    md.append("### 3.2 Atributos de Instancia Comunes")
    md.append("")
    
    attr_counts = defaultdict(int)
    for class_info in analyzer.classes.values():
        for attr in class_info["instance_attributes"]:
            attr_counts[attr["name"]] += 1
    
    md.append("| Atributo | Apariciones | Probable Propósito |")
    md.append("|----------|-------------|-------------------|")
    
    for attr, count in sorted(attr_counts.items(), key=lambda x: -x[1])[:15]:
        purpose = ""
        if "layout" in attr.lower():
            purpose = "Layout de UI"
        elif "btn" in attr.lower() or "button" in attr.lower():
            purpose = "Botón"
        elif "list" in attr.lower():
            purpose = "Lista/QListWidget"
        elif "table" in attr.lower():
            purpose = "Tabla/QTableWidget"
        elif "label" in attr.lower():
            purpose = "Etiqueta de texto"
        elif "input" in attr.lower() or "edit" in attr.lower():
            purpose = "Campo de entrada"
        elif "combo" in attr.lower():
            purpose = "ComboBox"
        elif "check" in attr.lower():
            purpose = "Checkbox"
        elif "canvas" in attr.lower():
            purpose = "Área de dibujo"
        elif "timer" in attr.lower():
            purpose = "Temporizador"
        
        md.append(f"| `self.{attr}` | {count} | {purpose} |")
    
    md.append("")
    md.append("---")
    md.append("")
    
    # Información para tests
    md.append("## 4. Información para Creación de Tests")
    md.append("")
    md.append("### 4.1 Clases Prioritarias para Testing")
    md.append("")
    md.append("Basado en complejidad y líneas de código:")
    md.append("")
    
    # Ordenar por complejidad total
    priority_classes = sorted(
        [(name, info, sum(m["complexity"] for m in info["methods"])) 
         for name, info in analyzer.classes.items()],
        key=lambda x: -x[2]
    )[:15]
    
    md.append("| Prioridad | Clase | Líneas | Complejidad | Categoría Sugerida |")
    md.append("|-----------|-------|--------|-------------|-------------------|")
    
    for i, (name, info, complexity) in enumerate(priority_classes, 1):
        lines = info["line_end"] - info["line_start"]
        category = "Alta" if complexity > 50 else "Media" if complexity > 20 else "Baja"
        md.append(f"| {i} | `{name}` | {lines} | {complexity} | {category} |")
    
    md.append("")
    
    # Dependencias entre clases
    md.append("### 4.2 Dependencias Internas")
    md.append("")
    md.append("Clases que llaman a otras clases del mismo módulo:")
    md.append("")
    
    internal_deps = defaultdict(set)
    all_class_names = set(analyzer.classes.keys())
    
    for class_name, class_info in analyzer.classes.items():
        for method in class_info["methods"]:
            for dep in method["dependencies"]:
                for other_class in all_class_names:
                    if other_class in dep and other_class != class_name:
                        internal_deps[class_name].add(other_class)
    
    if internal_deps:
        for class_name, deps in sorted(internal_deps.items())[:20]:
            deps_str = ", ".join(f"`{d}`" for d in sorted(deps))
            md.append(f"- `{class_name}` → {deps_str}")
    else:
        md.append("*No se detectaron dependencias internas significativas.*")
    
    md.append("")
    md.append("---")
    md.append("")
    
    # Lista completa para referencia
    md.append("## 5. Lista Completa de Clases y Métodos")
    md.append("")
    md.append("```")
    for class_name in sorted(analyzer.classes.keys()):
        class_info = analyzer.classes[class_name]
        md.append(f"class {class_name}({', '.join(class_info['bases'])}):")
        for method in sorted(class_info["methods"], key=lambda m: m["line_start"]):
            args_str = ", ".join(a["name"] for a in method["args"])
            md.append(f"    {method['name']}({args_str})")
        md.append("")
    md.append("```")
    md.append("")
    
    md.append("---")
    md.append("")
    md.append(f"*Documento generado automáticamente - {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
    
    return "\n".join(md)


def main():
    """Función principal."""
    print("=" * 60)
    print("Analizador de ui/dialogs.py - Fase 3.7")
    print("=" * 60)
    
    # Verificar que existe el archivo
    if not DIALOGS_PATH.exists():
        print(f"❌ Error: No se encuentra {DIALOGS_PATH}")
        sys.exit(1)
    
    print(f"\n📂 Leyendo: {DIALOGS_PATH}")
    
    # Leer el código fuente
    with open(DIALOGS_PATH, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    print(f"   Tamaño: {len(source_code):,} bytes")
    print(f"   Líneas: {len(source_code.splitlines()):,}")
    
    # Parsear el AST
    print("\n🔍 Analizando estructura del código...")
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en línea {e.lineno}: {e.msg}")
        sys.exit(1)
    
    # Analizar
    analyzer = DialogAnalyzer(source_code)
    analyzer.visit(tree)
    
    print(f"\n📊 Resultados del análisis:")
    print(f"   Clases encontradas: {len(analyzer.classes)}")
    total_methods = sum(len(c['methods']) for c in analyzer.classes.values())
    print(f"   Métodos totales: {total_methods}")
    
    # Generar reporte
    print("\n📝 Generando reporte Markdown...")
    report = generate_markdown_report(analyzer, DIALOGS_PATH)
    
    # Guardar
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Reporte guardado en: {OUTPUT_PATH}")
    print(f"   Tamaño del reporte: {len(report):,} bytes")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
