#!/usr/bin/env python3
"""
Detección de código muerto en el paquete ``ui/dialogs/``.
======================================================
Recorre cada ``*.py`` bajo ``ui/dialogs/``, extrae métodos por clase y
busca referencias en ``app.py``, ``ui/``, ``controllers/``, ``core/``, ``tests/``.

Clasificación heurística (revisar manualmente antes de borrar):
- USADO: referencias fuera del fichero de definición
- INTERNO: solo llamadas desde la misma clase/paquete
- MUERTO: sin referencias detectables (falsos positivos: slots Qt, getattr, etc.)

Genera un Markdown bajo ``Documentacion/``.
"""

import ast
import re
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Optional, cast
import logging

# Configurar logging para salida a consola
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("DetectDeadCode")

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DIALOGS_PACKAGE = BASE_DIR / "ui" / "dialogs"
# Compat tests / API antigua
DIALOGS_PATH = DIALOGS_PACKAGE
OUTPUT_PATH = BASE_DIR / "Documentacion" / "Analisis_Codigo_Muerto_ui_dialogs.md"

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

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if self.current_class:
            internal_calls: Set[str] = set()
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


def extract_package_classes(package_dir: Path) -> Dict[str, dict]:
    """Parsea todos los ``.py`` bajo ``package_dir`` y fusiona clases con clave ``rel/path.py::ClassName``."""
    merged: Dict[str, dict] = {}
    if not package_dir.is_dir():
        return merged
    for py_file in sorted(package_dir.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        rel = py_file.relative_to(BASE_DIR).as_posix()
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            logger.warning("   Saltando (syntax error): %s", rel)
            continue
        extractor = MethodExtractor()
        extractor.visit(tree)
        for cls_name, info in extractor.classes.items():
            key = f"{rel}::{cls_name}"
            merged[key] = {
                **info,
                "source_file": rel,
                "short_class_name": cls_name,
            }
    return merged


def find_references_in_file(file_path: Path, method_names: Set[str], class_names: Set[str]) -> Dict[str, List[dict]]:
    """
    Busca referencias a métodos y clases en un archivo.
    Retorna un diccionario con las referencias encontradas.
    """
    Reference = dict[str, object]
    references: Dict[str, List[Reference]] = cast(
        Dict[str, List[Reference]], defaultdict(list)
    )
    
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
    
    logger.info(f"   Archivos analizados: {files_searched}")
    return all_references


def _class_reference_key(class_key: str, class_info: dict) -> str:
    """Nombre corto de clase para coincidir con ``find_all_references``."""
    if "short_class_name" in class_info:
        return cast(str, class_info["short_class_name"])
    if "::" in class_key:
        return class_key.split("::", 1)[1]
    return class_key


def _definition_file(class_info: dict) -> str:
    return cast(str, class_info.get("source_file", "ui/dialogs.py"))


def analyze_dead_code(classes: Dict[str, dict], references: Dict[str, List[dict]]) -> dict:
    """
    Analiza y clasifica métodos según su uso.
    """
    analysis: dict[str, list[dict[str, object]]] = {
        "used_classes": [],
        "unused_classes": [],
        "dead_methods": [],
        "internal_only_methods": [],
        "used_methods": [],
        "dunder_methods": [],
    }
    
    # Recopilar todos los métodos llamados internamente
    all_internal_calls = set()
    for class_info in classes.values():
        for method_info in class_info["methods"].values():
            all_internal_calls.update(method_info["internal_calls"])
    
    # Analizar cada clase
    for class_key, class_info in classes.items():
        ref_key = _class_reference_key(class_key, class_info)
        src_file = _definition_file(class_info)
        class_refs = references.get(ref_key, [])
        external_refs = [r for r in class_refs if r["file"] != src_file]

        if external_refs:
            analysis["used_classes"].append({
                "name": class_key,
                "ref_count": len(external_refs),
                "refs": external_refs[:5]  # Mostrar máximo 5 referencias
            })
        else:
            has_external_usage = False
            for method_name in class_info["methods"]:
                method_refs = references.get(method_name, [])
                ext_refs = [r for r in method_refs if r["file"] != src_file]
                if ext_refs:
                    has_external_usage = True
                    break

            if not has_external_usage:
                analysis["unused_classes"].append({
                    "name": class_key,
                    "lines": class_info["line_end"] - class_info["line_start"],
                    "method_count": len(class_info["methods"])
                })
    
    # Analizar cada método
    for class_key, class_info in classes.items():
        src_file = _definition_file(class_info)
        for method_name, method_info in class_info["methods"].items():
            # Dunders se consideran usados implícitamente
            if method_info["is_dunder"]:
                analysis["dunder_methods"].append({
                    "class": class_key,
                    "method": method_name,
                    "lines": method_info["line_end"] - method_info["line_start"]
                })
                continue

            method_refs = references.get(method_name, [])
            external_refs = [r for r in method_refs if not (
                r["file"] == src_file and
                "def " + method_name in str(r.get("context", ""))
            )]
            
            is_called_internally = method_name in all_internal_calls
            has_external_refs = len(external_refs) > 0
            
            if has_external_refs:
                analysis["used_methods"].append({
                    "class": class_key,
                    "method": method_name,
                    "ref_count": len(external_refs),
                    "refs": external_refs[:3]
                })
            elif is_called_internally:
                analysis["internal_only_methods"].append({
                    "class": class_key,
                    "method": method_name,
                    "lines": method_info["line_end"] - method_info["line_start"],
                    "is_private": method_info["is_private"]
                })
            else:
                # Métodos públicos sin referencias son sospechosos pero podrían ser API
                if method_info["is_private"]:
                    analysis["dead_methods"].append({
                        "class": class_key,
                        "method": method_name,
                        "line_start": method_info["line_start"],
                        "line_end": method_info["line_end"],
                        "lines": method_info["line_end"] - method_info["line_start"],
                        "confidence": "Alta"  # Privado sin referencias = probablemente muerto
                    })
                else:
                    # Métodos públicos podrían ser parte de la API, menor confianza
                    analysis["dead_methods"].append({
                        "class": class_key,
                        "method": method_name,
                        "line_start": method_info["line_start"],
                        "line_end": method_info["line_end"],
                        "lines": method_info["line_end"] - method_info["line_start"],
                        "confidence": "Media"  # Público sin referencias = podría ser API
                    })
    
    return analysis


def generate_report(classes: Dict[str, dict], analysis: dict) -> str:
    """Genera el reporte en formato Markdown."""
    
    def _pct(n: int, total: int) -> int:
        return (n * 100 // total) if total else 0

    md = []
    md.append("# Fase 3.7: Análisis de código muerto — paquete `ui/dialogs/`")
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
    md.append(f"| Usados externamente | {used_count} | {_pct(used_count, total_methods)}% |")
    md.append(f"| Solo uso interno | {internal_count} | {_pct(internal_count, total_methods)}% |")
    md.append(f"| Dunders (implícitos) | {dunder_count} | {_pct(dunder_count, total_methods)}% |")
    md.append(f"| **⚠️ Potencialmente muertos** | {dead_count} | {_pct(dead_count, total_methods)}% |")
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
        md.append("> Estas clases no tienen instanciaciones detectadas fuera de su fichero en `ui/dialogs/`.")
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
    md.append("Estos métodos solo tienen llamadas detectadas dentro del mismo módulo o sin referencias externas claras:")
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

    if not analysis["dead_methods"]:
        md.append("## 7. Eliminaciones en esta pasada")
        md.append("")
        md.append(
            "La heurística no detectó métodos sin referencias (ni privados de alta confianza "
            "ni públicos de media confianza). **0 eliminaciones** automáticas recomendadas."
        )
        md.append("")

    md.append(f"*Documento generado automáticamente - {datetime.now().strftime('%d/%m/%Y %H:%M')}*")

    return "\n".join(md)


def main():
    """Función principal."""
    logger.info("=" * 60)
    logger.info("Detector de código muerto — paquete ui/dialogs/ (Fase 3.7)")
    logger.info("=" * 60)

    if not DIALOGS_PACKAGE.is_dir():
        logger.error("❌ Error: no existe el directorio %s", DIALOGS_PACKAGE)
        sys.exit(1)

    logger.info("\n📂 Analizando paquete: %s", DIALOGS_PACKAGE)
    logger.info("🔍 Extrayendo métodos y clases...")
    classes = extract_package_classes(DIALOGS_PACKAGE)

    total_classes = len(classes)
    total_methods = sum(len(c["methods"]) for c in classes.values())
    logger.info("   Clases: %s", total_classes)
    logger.info("   Métodos: %s", total_methods)

    all_method_names: Set[str] = set()
    class_short_names: Set[str] = set()
    for class_info in classes.values():
        class_short_names.add(cast(str, class_info["short_class_name"]))
        all_method_names.update(class_info["methods"].keys())

    logger.info("\n🔎 Buscando referencias en el proyecto...")
    references = find_all_references(all_method_names, class_short_names)

    logger.info("\n📊 Analizando uso de código...")
    analysis = analyze_dead_code(classes, references)
    
    dead_count = len(analysis["dead_methods"])
    logger.info(f"   Métodos potencialmente muertos: {dead_count}")
    
    # Generar reporte
    logger.info("\n📝 Generando reporte...")
    report = generate_report(classes, analysis)
    
    # Guardar
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"\n✅ Reporte guardado en: {OUTPUT_PATH}")
    logger.info("\n" + "=" * 60)


if __name__ == "__main__":
    main()
