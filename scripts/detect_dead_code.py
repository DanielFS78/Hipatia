#!/usr/bin/env python3
"""
Script de Detección de Código Muerto en ui/dialogs.py
=====================================================
Fase 3.7: Identifica métodos que no son llamados desde ningún lugar
del proyecto (código muerto) para su posterior eliminación.

Estrategia:
1. Extrae todos los métodos de dialogs.py
2. Busca referencias a cada método en todo el proyecto
3. Clasifica métodos como:
   - USADO: Tiene referencias externas o es público (__init__, sin underscore)
   - INTERNO: Es privado pero llamado internamente
   - MUERTO: Sin referencias detectables
   
Genera un archivo Markdown con el análisis.
"""

import ast
import os
import re
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DIALOGS_PATH = BASE_DIR / "ui" / "dialogs.py"
OUTPUT_PATH = BASE_DIR / "Documentacion" / "Fase 3" / "Fase_3_7_Codigo_Muerto_Dialogs.md"

# Directorios a buscar referencias
SEARCH_DIRS = [
    BASE_DIR / "app.py",
    BASE_DIR / "ui",
    BASE_DIR / "controllers",
    BASE_DIR / "core",
    BASE_DIR / "tests",
]

# Archivos a excluir de la búsqueda
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".pyc",
    "analyze_dialogs.py",
    "detect_dead_code.py",
]


class MethodExtractor(ast.NodeVisitor):
    """Extrae todos los métodos de cada clase."""
    
    def __init__(self):
        self.classes: Dict[str, dict] = {}
        self.current_class: Optional[str] = None
        
    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes[node.name] = {
            "methods": {},
            "line_start": node.lineno,
            "line_end": node.end_lineno,
        }
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.current_class:
            # Extraer llamadas internas a self.method()
            internal_calls = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Attribute):
                        if isinstance(child.func.value, ast.Name):
                            if child.func.value.id == "self":
                                internal_calls.add(child.func.attr)
            
            self.classes[self.current_class]["methods"][node.name] = {
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "is_private": node.name.startswith("_") and not node.name.startswith("__"),
                "is_dunder": node.name.startswith("__") and node.name.endswith("__"),
                "internal_calls": internal_calls,
            }
        self.generic_visit(node)


def find_references_in_file(file_path: Path, method_names: Set[str], class_names: Set[str]) -> Dict[str, List[dict]]:
    """
    Busca referencias a métodos y clases en un archivo.
    Retorna un diccionario con las referencias encontradas.
    """
    references = defaultdict(list)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.splitlines()
    except Exception:
        return references
    
    # Para cada clase, buscar instanciaciones
    for class_name in class_names:
        # Patrones de uso de clase
        patterns = [
            rf'\b{class_name}\s*\(',  # Instanciación: ClassName(
            rf'isinstance\s*\([^,]+,\s*{class_name}\)',  # isinstance check
            rf':\s*{class_name}\b',  # Type hint
            rf'from\s+.*import.*\b{class_name}\b',  # Import
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line):
                    references[class_name].append({
                        "file": str(file_path.relative_to(BASE_DIR)),
                        "line": line_num,
                        "type": "class_usage",
                        "context": line.strip()[:100]
                    })
                    break
    
    # Para cada método, buscar llamadas (más difícil de detectar)
    for method_name in method_names:
        if method_name.startswith("__") and method_name.endswith("__"):
            continue  # Omitir dunders, siempre se usan implícitamente
            
        # Patrones de llamada a método
        patterns = [
            rf'\.{method_name}\s*\(',  # Llamada: obj.method(
            rf'\.{method_name}\b(?!\s*\()',  # Referencia sin llamada: obj.method
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line):
                    references[method_name].append({
                        "file": str(file_path.relative_to(BASE_DIR)),
                        "line": line_num,
                        "type": "method_call",
                        "context": line.strip()[:100]
                    })
                    break
    
    return references


def find_all_references(method_names: Set[str], class_names: Set[str]) -> Dict[str, List[dict]]:
    """Busca referencias en todo el proyecto."""
    all_references = defaultdict(list)
    
    def should_skip(path: Path) -> bool:
        path_str = str(path)
        return any(exc in path_str for exc in EXCLUDE_PATTERNS)
    
    files_searched = 0
    
    for search_path in SEARCH_DIRS:
        if not search_path.exists():
            continue
            
        if search_path.is_file():
            if not should_skip(search_path):
                refs = find_references_in_file(search_path, method_names, class_names)
                for name, ref_list in refs.items():
                    all_references[name].extend(ref_list)
                files_searched += 1
        else:
            for file_path in search_path.rglob("*.py"):
                if should_skip(file_path):
                    continue
                refs = find_references_in_file(file_path, method_names, class_names)
                for name, ref_list in refs.items():
                    all_references[name].extend(ref_list)
                files_searched += 1
    
    print(f"   Archivos analizados: {files_searched}")
    return all_references


def analyze_dead_code(classes: Dict[str, dict], references: Dict[str, List[dict]]) -> dict:
    """
    Analiza y clasifica métodos según su uso.
    """
    analysis = {
        "used_classes": [],
        "unused_classes": [],
        "dead_methods": [],
        "internal_only_methods": [],
        "used_methods": [],
        "dunder_methods": [],
    }
    
    # Recopilar todos los métodos llamados internamente
    all_internal_calls = set()
    for class_name, class_info in classes.items():
        for method_name, method_info in class_info["methods"].items():
            all_internal_calls.update(method_info["internal_calls"])
    
    # Analizar cada clase
    for class_name, class_info in classes.items():
        class_refs = references.get(class_name, [])
        # Filtrar auto-referencias (definición en dialogs.py)
        external_refs = [r for r in class_refs if r["file"] != "ui/dialogs.py"]
        
        if external_refs:
            analysis["used_classes"].append({
                "name": class_name,
                "ref_count": len(external_refs),
                "refs": external_refs[:5]  # Mostrar máximo 5 referencias
            })
        else:
            # Verificar si alguno de sus métodos es usado externamente
            has_external_usage = False
            for method_name in class_info["methods"]:
                method_refs = references.get(method_name, [])
                ext_refs = [r for r in method_refs if r["file"] != "ui/dialogs.py"]
                if ext_refs:
                    has_external_usage = True
                    break
            
            if not has_external_usage:
                analysis["unused_classes"].append({
                    "name": class_name,
                    "lines": class_info["line_end"] - class_info["line_start"],
                    "method_count": len(class_info["methods"])
                })
    
    # Analizar cada método
    for class_name, class_info in classes.items():
        for method_name, method_info in class_info["methods"].items():
            full_name = f"{class_name}.{method_name}"
            
            # Dunders se consideran usados implícitamente
            if method_info["is_dunder"]:
                analysis["dunder_methods"].append({
                    "class": class_name,
                    "method": method_name,
                    "lines": method_info["line_end"] - method_info["line_start"]
                })
                continue
            
            method_refs = references.get(method_name, [])
            # Filtrar auto-definición
            external_refs = [r for r in method_refs if not (
                r["file"] == "ui/dialogs.py" and 
                "def " + method_name in r["context"]
            )]
            
            is_called_internally = method_name in all_internal_calls
            has_external_refs = len(external_refs) > 0
            
            if has_external_refs:
                analysis["used_methods"].append({
                    "class": class_name,
                    "method": method_name,
                    "ref_count": len(external_refs),
                    "refs": external_refs[:3]
                })
            elif is_called_internally:
                analysis["internal_only_methods"].append({
                    "class": class_name,
                    "method": method_name,
                    "lines": method_info["line_end"] - method_info["line_start"],
                    "is_private": method_info["is_private"]
                })
            else:
                # Métodos públicos sin referencias son sospechosos pero podrían ser API
                if method_info["is_private"]:
                    analysis["dead_methods"].append({
                        "class": class_name,
                        "method": method_name,
                        "line_start": method_info["line_start"],
                        "line_end": method_info["line_end"],
                        "lines": method_info["line_end"] - method_info["line_start"],
                        "confidence": "Alta"  # Privado sin referencias = probablemente muerto
                    })
                else:
                    # Métodos públicos podrían ser parte de la API, menor confianza
                    analysis["dead_methods"].append({
                        "class": class_name,
                        "method": method_name,
                        "line_start": method_info["line_start"],
                        "line_end": method_info["line_end"],
                        "lines": method_info["line_end"] - method_info["line_start"],
                        "confidence": "Media"  # Público sin referencias = podría ser API
                    })
    
    return analysis


def generate_report(classes: Dict[str, dict], analysis: dict) -> str:
    """Genera el reporte en formato Markdown."""
    
    md = []
    md.append("# Fase 3.7: Análisis de Código Muerto en `ui/dialogs.py`")
    md.append("")
    md.append(f"> **Fecha de análisis:** {datetime.now().strftime('%d de %B de %Y, %H:%M')}")
    md.append("> **Generado por:** `scripts/detect_dead_code.py`")
    md.append("")
    md.append("---")
    md.append("")
    
    # Resumen ejecutivo
    total_methods = sum(len(c["methods"]) for c in classes.values())
    dead_count = len(analysis["dead_methods"])
    internal_count = len(analysis["internal_only_methods"])
    used_count = len(analysis["used_methods"])
    dunder_count = len(analysis["dunder_methods"])
    
    dead_lines = sum(m["lines"] for m in analysis["dead_methods"])
    
    md.append("## 1. Resumen Ejecutivo")
    md.append("")
    md.append("| Categoría | Cantidad | Porcentaje |")
    md.append("|-----------|----------|------------|")
    md.append(f"| **Métodos totales** | {total_methods} | 100% |")
    md.append(f"| Usados externamente | {used_count} | {used_count*100//total_methods}% |")
    md.append(f"| Solo uso interno | {internal_count} | {internal_count*100//total_methods}% |")
    md.append(f"| Dunders (implícitos) | {dunder_count} | {dunder_count*100//total_methods}% |")
    md.append(f"| **⚠️ Potencialmente muertos** | {dead_count} | {dead_count*100//total_methods}% |")
    md.append("")
    
    md.append(f"> **Líneas de código potencialmente eliminables:** ~{dead_lines} líneas")
    md.append("")
    md.append("---")
    md.append("")
    
    # Clases sin uso externo
    if analysis["unused_classes"]:
        md.append("## 2. Clases sin Uso Externo Detectado")
        md.append("")
        md.append("> [!WARNING]")
        md.append("> Estas clases no tienen instanciaciones detectadas fuera de `dialogs.py`.")
        md.append("> Podrían ser usadas dinámicamente o a través de imports indirectos.")
        md.append("")
        md.append("| Clase | Líneas | Métodos |")
        md.append("|-------|--------|---------|")
        for cls in sorted(analysis["unused_classes"], key=lambda x: -x["lines"]):
            md.append(f"| `{cls['name']}` | {cls['lines']} | {cls['method_count']} |")
        md.append("")
        md.append("---")
        md.append("")
    
    # Código muerto - Alta confianza
    high_confidence = [m for m in analysis["dead_methods"] if m["confidence"] == "Alta"]
    if high_confidence:
        md.append("## 3. Métodos Muertos - Alta Confianza")
        md.append("")
        md.append("> [!CAUTION]")
        md.append("> Estos métodos privados (`_nombre`) no tienen referencias detectables.")
        md.append("> Son candidatos seguros para eliminación.")
        md.append("")
        md.append("| Clase | Método | Líneas | Rango |")
        md.append("|-------|--------|--------|-------|")
        for m in sorted(high_confidence, key=lambda x: -x["lines"]):
            md.append(f"| `{m['class']}` | `{m['method']}` | {m['lines']} | L{m['line_start']}-{m['line_end']} |")
        md.append("")
        
        total_high = sum(m["lines"] for m in high_confidence)
        md.append(f"**Total eliminable con alta confianza: ~{total_high} líneas**")
        md.append("")
        md.append("---")
        md.append("")
    
    # Código muerto - Media confianza
    medium_confidence = [m for m in analysis["dead_methods"] if m["confidence"] == "Media"]
    if medium_confidence:
        md.append("## 4. Métodos Sin Referencias - Media Confianza")
        md.append("")
        md.append("> [!IMPORTANT]")
        md.append("> Estos métodos públicos no tienen referencias directas detectadas.")
        md.append("> Podrían ser parte de la API pública del diálogo o usados vía connect().")
        md.append("> **Revisar manualmente antes de eliminar.**")
        md.append("")
        md.append("| Clase | Método | Líneas | Rango |")
        md.append("|-------|--------|--------|-------|")
        for m in sorted(medium_confidence, key=lambda x: -x["lines"])[:30]:  # Limitar a 30
            md.append(f"| `{m['class']}` | `{m['method']}` | {m['lines']} | L{m['line_start']}-{m['line_end']} |")
        
        if len(medium_confidence) > 30:
            md.append(f"| ... | *{len(medium_confidence) - 30} más* | - | - |")
        
        md.append("")
        md.append("---")
        md.append("")
    
    # Métodos con uso interno
    md.append("## 5. Métodos con Solo Uso Interno")
    md.append("")
    md.append("Estos métodos son llamados solo desde dentro de `dialogs.py`:")
    md.append("")
    md.append("| Clase | Método | Líneas | Es Privado |")
    md.append("|-------|--------|--------|------------|")
    for m in sorted(analysis["internal_only_methods"], key=lambda x: x["class"])[:40]:
        private = "✓" if m["is_private"] else ""
        md.append(f"| `{m['class']}` | `{m['method']}` | {m['lines']} | {private} |")
    
    if len(analysis["internal_only_methods"]) > 40:
        md.append(f"| ... | *{len(analysis['internal_only_methods']) - 40} más* | - | - |")
    
    md.append("")
    md.append("---")
    md.append("")
    
    # Recomendaciones
    md.append("## 6. Recomendaciones")
    md.append("")
    md.append("### Paso 1: Eliminar Código Muerto de Alta Confianza")
    md.append("")
    
    if high_confidence:
        md.append("Métodos a eliminar primero (privados sin referencias):")
        md.append("")
        md.append("```python")
        md.append("# Eliminar estos métodos:")
        for m in high_confidence[:10]:
            md.append(f"# - {m['class']}.{m['method']}()  # Líneas {m['line_start']}-{m['line_end']}")
        md.append("```")
        md.append("")
    
    md.append("### Paso 2: Verificar Manualmente Métodos de Media Confianza")
    md.append("")
    md.append("Antes de eliminar métodos públicos, verificar:")
    md.append("")
    md.append("1. ¿Son slots conectados via `signal.connect(self.metodo)`?")
    md.append("2. ¿Son llamados desde UI via eventos (`clicked`, `textChanged`, etc.)?")
    md.append("3. ¿Son parte de la API pública que devuelve datos al controlador?")
    md.append("")
    
    md.append("### Paso 3: Ejecutar Tests Después de Cada Eliminación")
    md.append("")
    md.append("```bash")
    md.append("source .venv/bin/activate && python -m pytest tests/ -v --tb=short")
    md.append("```")
    md.append("")
    md.append("---")
    md.append("")
    md.append(f"*Documento generado automáticamente - {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
    
    return "\n".join(md)


def main():
    """Función principal."""
    print("=" * 60)
    print("Detector de Código Muerto - ui/dialogs.py - Fase 3.7")
    print("=" * 60)
    
    # Verificar archivo
    if not DIALOGS_PATH.exists():
        print(f"❌ Error: No se encuentra {DIALOGS_PATH}")
        sys.exit(1)
    
    # Leer código
    print(f"\n📂 Leyendo: {DIALOGS_PATH}")
    with open(DIALOGS_PATH, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # Parsear
    print("🔍 Extrayendo métodos y clases...")
    tree = ast.parse(source_code)
    extractor = MethodExtractor()
    extractor.visit(tree)
    
    total_classes = len(extractor.classes)
    total_methods = sum(len(c["methods"]) for c in extractor.classes.values())
    print(f"   Clases: {total_classes}")
    print(f"   Métodos: {total_methods}")
    
    # Recopilar nombres
    all_method_names = set()
    class_names = set(extractor.classes.keys())
    for class_info in extractor.classes.values():
        all_method_names.update(class_info["methods"].keys())
    
    # Buscar referencias
    print("\n🔎 Buscando referencias en el proyecto...")
    references = find_all_references(all_method_names, class_names)
    
    # Analizar
    print("\n📊 Analizando uso de código...")
    analysis = analyze_dead_code(extractor.classes, references)
    
    dead_count = len(analysis["dead_methods"])
    print(f"   Métodos potencialmente muertos: {dead_count}")
    
    # Generar reporte
    print("\n📝 Generando reporte...")
    report = generate_report(extractor.classes, analysis)
    
    # Guardar
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Reporte guardado en: {OUTPUT_PATH}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
