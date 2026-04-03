#!/usr/bin/env python3
"""
Analizador de Código Legacy — Proyecto Hipatia
==============================================
Fase 4 del Plan de Mejora de Calidad: detecta patrones legacy para su
eliminación o sustitución (print → logger, marcadores deprecated, docstrings
obsoletos, delegaciones/shim y código muerto candidato).

Genera:
- legacy_report.json: datos estructurados para el agente
- legacy_report.md: informe legible en Documentacion/Refactorizacion_Completa/Legacy/

Uso:
  python3 scripts/legacy_analyzer.py [--json-only] [--md-only]
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Directorios de código de producción (aquí print() debe ser reemplazado por logger)
PRODUCTION_DIRS = ["controllers", "core", "database", "features", "ui"]
PRODUCTION_FILES_TOP = ["app.py"]

# Patrones en docstrings/comentarios que marcan legacy
LEGACY_KEYWORDS = ["obsoleto", "legacy", "deprecated", "deprecado", "mantenido temporalmente", "re-export"]

# Excluir de búsqueda
EXCLUDE_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules"}
EXCLUDE_FILES = {"legacy_analyzer.py", "detect_dead_code.py"}


def get_production_python_files() -> list[Path]:
    """Lista todos los archivos .py en directorios de producción."""
    files: list[Path] = []
    for name in PRODUCTION_DIRS:
        d = BASE_DIR / name
        if d.is_dir():
            for p in d.rglob("*.py"):
                if EXCLUDE_DIRS.isdisjoint(p.parts) and p.name not in EXCLUDE_FILES:
                    files.append(p)
    for name in PRODUCTION_FILES_TOP:
        p = BASE_DIR / name
        if p.is_file():
            files.append(p)
    return sorted(set(files))


def get_all_python_files() -> list[Path]:
    """Lista todos los .py del proyecto (excepto venv/git)."""
    files: list[Path] = []
    for p in BASE_DIR.rglob("*.py"):
        if EXCLUDE_DIRS.isdisjoint(p.parts) and p.name not in EXCLUDE_FILES:
            files.append(p)
    return sorted(set(files))


def find_print_statements(files: list[Path]) -> list[dict[str, Any]]:
    """Detecta llamadas a print() en archivos de producción."""
    results = []
    pattern = re.compile(r"\bprint\s*\(")
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = path.relative_to(BASE_DIR)
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line) and not line.strip().startswith("#"):
                results.append({
                    "file": str(rel),
                    "line": i,
                    "context": line.strip()[:100],
                    "category": "print_en_produccion",
                })
    return results


def find_bare_except(files: list[Path]) -> list[dict[str, Any]]:
    """Detecta except: sin tipo (bare except)."""
    results = []
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        rel = path.relative_to(BASE_DIR)
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                results.append({
                    "file": str(rel),
                    "line": node.lineno,
                    "context": "except:",
                    "category": "bare_except",
                })
    return results


def find_deprecated_markers(files: list[Path]) -> list[dict[str, Any]]:
    """Busca líneas con marcadores @deprecated, TODO: Remove, DEPRECATED."""
    results = []
    for path in files:
        rel = path.relative_to(BASE_DIR)
        if "detect_obsolete_code.py" in str(rel):
            continue  # Evitar autoreferencia del script que busca deprecated
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            lower = line.lower()
            stripped = line.strip()
            if "@deprecated" in lower or "todo: remove" in lower:
                results.append({
                    "file": str(rel),
                    "line": i,
                    "context": line.strip()[:120],
                    "category": "deprecated_marker",
                })
            elif stripped.startswith("#") and "deprecated" in lower:
                results.append({
                    "file": str(rel),
                    "line": i,
                    "context": line.strip()[:120],
                    "category": "deprecated_marker",
                })
    return results


def find_legacy_in_docstrings(files: list[Path]) -> list[dict[str, Any]]:
    """Busca docstrings que mencionan obsoleto/legacy/deprecated."""
    results = []
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        rel = path.relative_to(BASE_DIR)

        for node in ast.walk(tree):
            doc = None
            name = None
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node)
                name = node.name
            if not doc:
                continue
            doc_lower = doc.lower()
            for kw in LEGACY_KEYWORDS:
                if kw in doc_lower:
                    # `doc` solo se asigna para nodos de tipo Function/Class (incl. AsyncFunctionDef),
                    # pero mypy no puede inferirlo; se hace narrowing explícito.
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                        kind = "class" if isinstance(node, ast.ClassDef) else "function"
                        results.append({
                            "file": str(rel),
                            "line": node.lineno,
                            "symbol": name,
                            "kind": kind,
                            "keyword": kw,
                            "doc_excerpt": doc[:200].replace("\n", " "),
                            "category": "docstring_legacy",
                        })
                    break
    return results


def _is_simple_delegation(node: ast.FunctionDef) -> tuple[bool, str | None]:
    """
    Comprueba si la función solo delega en otra (return other() o self.other()).
    Devuelve (True, nombre_delegado) o (False, None).
    """
    if len(node.body) != 1:
        return False, None
    only = node.body[0]
    if isinstance(only, ast.Return) and only.value is not None:
        if isinstance(only.value, ast.Call):
            func = only.value.func
            if isinstance(func, ast.Attribute):
                return True, func.attr
            if isinstance(func, ast.Name):
                return True, func.id
    if isinstance(only, ast.Expr) and isinstance(only.value, ast.Call):
        func = only.value.func
        if isinstance(func, ast.Attribute):
            return True, func.attr
        if isinstance(func, ast.Name):
            return True, func.id
    return False, None


def find_simple_delegations(files: list[Path]) -> list[dict[str, Any]]:
    """Detecta funciones que solo delegan en otra (posibles shims/aliases legacy)."""
    results = []
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        rel = path.relative_to(BASE_DIR)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                is_delegation, target = _is_simple_delegation(node)
                if is_delegation and target and target != node.name:
                    results.append({
                        "file": str(rel),
                        "line": node.lineno,
                        "symbol": node.name,
                        "delegates_to": target,
                        "category": "simple_delegation",
                    })
    return results


def _count_symbol_mentions(files: list[Path], symbol: str) -> int:
    """
    Cuenta menciones literales de un símbolo en una lista de archivos Python.

    Nota: Heurística basada en regex. Es suficiente para detectar shims no usados
    sin introducir dependencias externas.
    """
    pattern = re.compile(rf"\b{re.escape(symbol)}\b")
    total = 0
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        total += len(pattern.findall(text))
    return total


def filter_unused_delegations(delegations: list[dict[str, Any]], all_files: list[Path]) -> list[dict[str, Any]]:
    """
    Filtra delegaciones simples dejando solo las que no tienen uso externo detectable.

    Criterio: si el símbolo aparece 1 vez en todo el proyecto (su propia definición),
    lo tratamos como candidato a eliminación.
    """
    by_file: dict[str, Path] = {str(p.relative_to(BASE_DIR)): p for p in all_files}
    unused: list[dict[str, Any]] = []

    for item in delegations:
        symbol = str(item["symbol"])
        defining_rel = str(item["file"])
        defining_path = by_file.get(defining_rel)

        mentions = _count_symbol_mentions(all_files, symbol)
        # Intentar descontar explícitamente la definición en su propio archivo (si existe)
        if defining_path is not None:
            try:
                text = defining_path.read_text(encoding="utf-8", errors="ignore")
                if re.search(rf"^\\s*def\\s+{re.escape(symbol)}\\b", text, flags=re.MULTILINE):
                    mentions -= 1
            except Exception:
                pass

        if mentions <= 0:
            unused.append(item)

    return unused


def find_legacy_re_exports(files: list[Path]) -> list[dict[str, Any]]:
    """Busca comentarios que indican re-exports o métodos legacy (ej. app_controller)."""
    results = []
    pattern = re.compile(
        r"#.*(?:legacy|re-export|reexport|mantenido temporalmente)",
        re.IGNORECASE,
    )
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        rel = path.relative_to(BASE_DIR)
        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                results.append({
                    "file": str(rel),
                    "line": i,
                    "context": line.strip()[:120],
                    "category": "legacy_comment",
                })
    return results


def build_report() -> dict[str, Any]:
    """Construye el informe completo de código legacy."""
    production_files = get_production_python_files()
    all_files = get_all_python_files()

    print_statements = find_print_statements(production_files)
    bare_except = find_bare_except(all_files)
    deprecated_markers = find_deprecated_markers(all_files)
    docstring_legacy = find_legacy_in_docstrings(all_files)
    simple_delegations = filter_unused_delegations(find_simple_delegations(production_files), all_files)
    legacy_comments = find_legacy_re_exports(all_files)

    return {
        "generated_at": datetime.now().isoformat(),
        "base_dir": str(BASE_DIR),
        "summary": {
            "print_en_produccion": len(print_statements),
            "bare_except": len(bare_except),
            "deprecated_markers": len(deprecated_markers),
            "docstring_legacy": len(docstring_legacy),
            "simple_delegation": len(simple_delegations),
            "legacy_comment": len(legacy_comments),
        },
        "items": {
            "print_en_produccion": print_statements,
            "bare_except": bare_except,
            "deprecated_markers": deprecated_markers,
            "docstring_legacy": docstring_legacy,
            "simple_delegation": simple_delegations,
            "legacy_comment": legacy_comments,
        },
    }


def generate_md(report: dict[str, Any]) -> str:
    """Genera el informe en Markdown."""
    summary = report["summary"]
    items = report["items"]
    lines = [
        "# Informe de Código Legacy — Fase 4",
        "",
        f"> **Fecha:** {report['generated_at'][:19].replace('T', ' ')}",
        "> **Generado por:** `scripts/legacy_analyzer.py`",
        "",
        "---",
        "",
        "## 1. Resumen",
        "",
        "| Categoría | Cantidad |",
        "|-----------|----------|",
    ]
    for key, count in summary.items():
        lines.append(f"| {key} | {count} |")
    lines.extend(["", "---", ""])

    # Print en producción
    if items["print_en_produccion"]:
        lines.extend([
            "## 2. `print()` en código de producción",
            "",
            "Sustituir por `logger.debug()` o `logger.info()` según corresponda.",
            "",
            "| Archivo | Línea | Contexto |",
            "|---------|-------|----------|",
        ])
        for r in items["print_en_produccion"][:50]:
            ctx = r["context"].replace("|", "\\|")
            lines.append(f"| {r['file']} | {r['line']} | `{ctx[:60]}...` |")
        if len(items["print_en_produccion"]) > 50:
            lines.append(f"| ... | *{len(items['print_en_produccion']) - 50} más* | |")
        lines.extend(["", "---", ""])

    # Bare except
    if items["bare_except"]:
        lines.extend([
            "## 3. Bare `except:`",
            "",
            "Sustituir por `except Exception as e:` y registrar con logger.",
            "",
            "| Archivo | Línea |",
            "|---------|-------|",
        ])
        for r in items["bare_except"]:
            lines.append(f"| {r['file']} | {r['line']} |")
        lines.extend(["", "---", ""])

    # Marcadores deprecated
    if items["deprecated_markers"]:
        lines.extend([
            "## 4. Marcadores @deprecated / TODO: Remove",
            "",
            "| Archivo | Línea | Contexto |",
            "|---------|-------|----------|",
        ])
        for r in items["deprecated_markers"][:30]:
            ctx = r["context"].replace("|", "\\|")
            lines.append(f"| {r['file']} | {r['line']} | `{ctx[:70]}` |")
        lines.extend(["", "---", ""])

    # Docstrings legacy
    if items["docstring_legacy"]:
        lines.extend([
            "## 5. Docstrings con obsoleto/legacy/deprecated",
            "",
            "Revisar si el símbolo debe eliminarse o actualizar el docstring.",
            "",
            "| Archivo | Línea | Símbolo | Tipo | Palabra clave |",
            "|---------|-------|---------|------|---------------|",
        ])
        for r in items["docstring_legacy"][:40]:
            lines.append(f"| {r['file']} | {r['line']} | `{r['symbol']}` | {r['kind']} | {r['keyword']} |")
        if len(items["docstring_legacy"]) > 40:
            lines.append(f"| ... | *{len(items['docstring_legacy']) - 40} más* | | | |")
        lines.extend(["", "---", ""])

    # Delegaciones simples
    if items["simple_delegation"]:
        lines.extend([
            "## 6. Delegaciones simples (posibles shims)",
            "",
            "Verificar si hay callers; si no, eliminar y usar el destino directo.",
            "",
            "| Archivo | Línea | Función | Delega en |",
            "|---------|-------|---------|-----------|",
        ])
        for r in items["simple_delegation"][:30]:
            lines.append(f"| {r['file']} | {r['line']} | `{r['symbol']}` | `{r['delegates_to']}` |")
        lines.extend(["", "---", ""])

    # Comentarios legacy
    if items["legacy_comment"]:
        lines.extend([
            "## 7. Comentarios legacy / re-export",
            "",
            "| Archivo | Línea | Contexto |",
            "|---------|-------|----------|",
        ])
        for r in items["legacy_comment"][:20]:
            ctx = r["context"].replace("|", "\\|")
            lines.append(f"| {r['file']} | {r['line']} | `{ctx[:70]}` |")
        lines.extend(["", "---", ""])

    lines.extend([
        "## 8. Orden de actuación recomendado",
        "",
        "1. **print → logger** en producción (evitar falsos positivos en scripts/tests).",
        "2. **Bare except** → `except Exception` + logging.",
        "3. **Docstrings legacy**: actualizar o eliminar API obsoleta.",
        "4. **Delegaciones**: comprobar referencias; si no hay usos, eliminar y redirigir.",
        "5. **Marcadores y comentarios**: eliminar código marcado o actualizar documentación.",
        "",
        "Tras cada cambio: ejecutar `python3 -m pytest <scope> -x -q` y `python3 run_tests.py`.",
        "",
        f"*Generado — {report['generated_at'][:10]}*",
    ])
    return "\n".join(lines)


def main() -> int:
    """Punto de entrada."""
    parser = argparse.ArgumentParser(description="Analizador de código legacy (Fase 4)")
    parser.add_argument("--json-only", action="store_true", help="Solo generar JSON")
    parser.add_argument("--md-only", action="store_true", help="Solo generar MD")
    parser.add_argument(
        "-o", "--output-dir",
        default=str(BASE_DIR / "Documentacion" / "Refactorizacion_Completa" / "Legacy"),
        help="Directorio de salida para JSON y MD",
    )
    args = parser.parse_args()
    out_dir = Path(args.output_dir)

    report = build_report()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.md_only:
        json_path = out_dir / "legacy_report.json"
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"JSON: {json_path}")

    if not args.json_only:
        md_path = out_dir / "legacy_report.md"
        md_path.write_text(generate_md(report), encoding="utf-8")
        print(f"MD:   {md_path}")

    total = sum(report["summary"].values())
    print(f"Total ítems legacy: {total}")
    return 0 if total >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
