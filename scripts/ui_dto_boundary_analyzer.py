#!/usr/bin/env python3
"""
Nombre del Módulo: ui_dto_boundary_analyzer
Descripcion: Audita la frontera UI/DTO para detectar accesos tipo diccionario
             dentro de `ui/` (p.ej. `obj["campo"]`, `obj.get("campo")`) que suelen
             indicar datos sin tipar o mezclas DTO vs dict. Ignora `os.environ.get`
             (variables de entorno, no DTO). Genera informes para la Fase 12C.

             Las variables en INTERNAL_UI_DICT_VARS (p. ej. `data`) se ignoran salvo que la
             clave literal esté en DOMAIN_DICT_KEYS_FORCE_REPORT (campos típicos de entidad/BD),
             para reducir falsos negativos en `data["id"]` sin reabrir todo el ruido de estado UI.

Uso:
    python3 scripts/ui_dto_boundary_analyzer.py
    python3 scripts/ui_dto_boundary_analyzer.py --json-only
    python3 scripts/ui_dto_boundary_analyzer.py --md-only
    python3 scripts/ui_dto_boundary_analyzer.py --enforce-zero   # CI: falla si hay hallazgos
    python3 scripts/ui_dto_boundary_analyzer.py --max-findings 5
    python3 scripts/ui_dto_boundary_analyzer.py --baseline ruta/baseline.json

Salida (por defecto):
    Documentacion/Refactorizacion_Completa/Fase_12C/ui_dto_boundary_report.json
    Documentacion/Refactorizacion_Completa/Fase_12C/ui_dto_boundary_report.md
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIR = BASE_DIR / "ui"
EXCLUDE_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules"}
DEFAULT_EXCLUDE_SUBDIRS = {
    # Producción: aquí los dicts son configuración serializable del canvas/flujo
    str(Path("ui") / "dialogs" / "production_flow"),
    str(Path("ui") / "widgets" / "production_flow"),
}

DEFAULT_EXCLUDE_FILES = {
    # Estructuras internas de UI que usan dict como payload/configuración
    str(Path("ui") / "dialogs" / "canvas_widget.py"),
    str(Path("ui") / "dialogs" / "card_widget.py"),
}

# Atributos/variables de UI que son diccionarios internos por diseño.
# No representan frontera UI/DTO (son estado/estructuras de widgets).
INTERNAL_UI_DICT_ATTRS = {
    "buttons",
    "pages",
    "_tests_section",
    "_db_section",
    "_summary_section",
    "form_widgets",
    "lote_content",
    "current_selected_task",
}

INTERNAL_UI_DICT_VARS = {
    "pila_data",
    # Variables locales frecuentes en widgets (estructuras internas/transitorias).
    # Nota: se excluyen para permitir que el analizador se centre en frontera UI/DTO real,
    # no en diccionarios de formulario/estado interno.
    "data",
    "item",
    "step_data",
    "preproceso",
    "d",
    "pd",
    "content",
    "task",
    "task_data",
    "brk",
    "x",
    "r",
}

# Claves que suelen alinear con columnas o atributos de DTO: no omitir aunque el receptor
# sea un nombre en INTERNAL_UI_DICT_VARS (evita falsos negativos tipo data["id"]).
DOMAIN_DICT_KEYS_FORCE_REPORT: frozenset[str] = frozenset({
    "id",
    "pk",
    "uuid",
    "codigo",
    "nombre",
    "descripcion",
    "producto_codigo",
    "producto_descripcion",
    "producto_id",
    "fabricacion_id",
    "lote_id",
    "maquina_id",
    "trabajador_id",
    "orden_fabricacion",
    "tipo_proceso",
    "departamento",
    "activa",
    "email",
    "username",
    "user_id",
    "role_id",
    "permission",
    "cantidad",
    "fecha",
    "estado",
})

_TYPING_NAME_IDS = frozenset({
    "Optional",
    "List",
    "Dict",
    "Tuple",
    "Set",
    "Sequence",
    "Mapping",
    "Iterable",
})


def should_report_name_dict_access(receiver_id: str, key: str) -> bool:
    """
    False: el acceso se considera estado interno UI (receptor en INTERNAL_UI_DICT_VARS y
    clave no es de dominio forzado). True: incluir en el informe.
    """
    if receiver_id not in INTERNAL_UI_DICT_VARS:
        return True
    if key in DOMAIN_DICT_KEYS_FORCE_REPORT:
        return True
    return False


@dataclass(frozen=True)
class Finding:
    """Hallazgo de acceso tipo diccionario dentro de UI."""

    file: str
    line: int
    col: int
    kind: str  # subscript | get_call
    key: str
    context: str


def _iter_ui_files() -> list[Path]:
    """Devuelve todos los `.py` bajo `ui/` (sin venv/git)."""
    if not UI_DIR.is_dir():
        return []
    files: list[Path] = []
    for p in UI_DIR.rglob("*.py"):
        if EXCLUDE_DIRS.isdisjoint(p.parts):
            files.append(p)
    return sorted(files)


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []


def _context_line(lines: list[str], lineno: int, max_len: int = 140) -> str:
    if lineno <= 0 or lineno > len(lines):
        return ""
    s = lines[lineno - 1].rstrip("\n")
    return (s[: max_len - 1] + "…") if len(s) > max_len else s


def _extract_constant_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _is_os_environ_access(value: ast.AST) -> bool:
    """True si la expresión es `os.environ` (no es frontera UI/DTO)."""
    return (
        isinstance(value, ast.Attribute)
        and isinstance(value.value, ast.Name)
        and value.value.id == "os"
        and value.attr == "environ"
    )


def analyze_file(path: Path) -> list[Finding]:
    """
    Analiza un archivo UI y devuelve hallazgos de acceso dict-like.

    - Subscript: `x["campo"]` o `x['campo']`
    - get_call: `x.get("campo", ...)`
    """
    lines = _read_lines(path)
    try:
        tree = ast.parse("\n".join(lines))
    except Exception:
        return []

    rel = str(path.relative_to(BASE_DIR))
    findings: list[Finding] = []

    for node in ast.walk(tree):
        # x["key"]
        if isinstance(node, ast.Subscript):
            # Ignorar diccionarios internos de la propia UI: self.<attr>["k"] / var["k"]
            if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name):
                if node.value.value.id == "self" and node.value.attr in INTERNAL_UI_DICT_ATTRS:
                    continue
            # Ignorar subscripts usados en type hints: Optional["X"], List[int], Dict[str, Any], etc.
            if isinstance(node.value, ast.Name) and node.value.id in _TYPING_NAME_IDS:
                continue
            key = _extract_constant_str(node.slice)
            if not key:
                continue
            if isinstance(node.value, ast.Name) and not should_report_name_dict_access(
                node.value.id, key
            ):
                continue
            findings.append(
                Finding(
                    file=rel,
                    line=getattr(node, "lineno", 1),
                    col=getattr(node, "col_offset", 0),
                    kind="subscript",
                    key=key,
                    context=_context_line(lines, getattr(node, "lineno", 1)),
                )
            )

        # x.get("key", default)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            # Ignorar diccionarios internos de la propia UI: self.<attr>.get("k") / var.get("k")
            if isinstance(node.func.value, ast.Attribute) and isinstance(node.func.value.value, ast.Name):
                if node.func.value.value.id == "self" and node.func.value.attr in INTERNAL_UI_DICT_ATTRS:
                    continue
            if _is_os_environ_access(node.func.value):
                continue
            if not node.args:
                continue
            key = _extract_constant_str(node.args[0])
            if not key:
                continue
            if isinstance(node.func.value, ast.Name) and not should_report_name_dict_access(
                node.func.value.id, key
            ):
                continue
            findings.append(
                Finding(
                    file=rel,
                    line=getattr(node, "lineno", 1),
                    col=getattr(node, "col_offset", 0),
                    kind="get_call",
                    key=key,
                    context=_context_line(lines, getattr(node, "lineno", 1)),
                )
            )

    return findings


def build_report(*, include_production_flow: bool) -> dict[str, Any]:
    """Construye el reporte completo de hallazgos en `ui/`."""
    all_findings: list[Finding] = []
    for p in _iter_ui_files():
        rel = str(p.relative_to(BASE_DIR))
        if not include_production_flow:
            if any(rel.startswith(prefix) for prefix in DEFAULT_EXCLUDE_SUBDIRS):
                continue
            if rel in DEFAULT_EXCLUDE_FILES:
                continue
        all_findings.extend(analyze_file(p))

    by_file: dict[str, list[Finding]] = {}
    for f in all_findings:
        by_file.setdefault(f.file, []).append(f)

    # Heurística: preferimos arreglar primero subscript con keys conocidas (más "dict-like")
    summary = {
        "total_findings": len(all_findings),
        "subscript": sum(1 for f in all_findings if f.kind == "subscript"),
        "get_call": sum(1 for f in all_findings if f.kind == "get_call"),
        "files_affected": len(by_file),
    }

    items = [
        {
            "file": f.file,
            "line": f.line,
            "col": f.col,
            "kind": f.kind,
            "key": f.key,
            "context": f.context,
        }
        for f in sorted(all_findings, key=lambda x: (x.file, x.line, x.col))
    ]

    return {
        "generated_at": datetime.now().isoformat(),
        "base_dir": str(BASE_DIR),
        "summary": summary,
        "items": items,
    }


def generate_md(report: dict[str, Any]) -> str:
    """Genera un informe legible en Markdown para Fase 12C."""
    s = report["summary"]
    items: list[dict[str, Any]] = report["items"]

    md: list[str] = []
    md.append("# Fase 12C — Auditoría de Frontera UI/DTO")
    md.append("")
    md.append(f"> **Fecha:** {report['generated_at'][:19].replace('T', ' ')}")
    md.append("> **Generado por:** `scripts/ui_dto_boundary_analyzer.py`")
    md.append("")
    md.append("## Resumen")
    md.append("")
    md.append("| Métrica | Valor |")
    md.append("|--------|-------|")
    md.append(f"| Total hallazgos | {s['total_findings']} |")
    md.append(f"| Subscript (`obj[\"k\"]`) | {s['subscript']} |")
    md.append(f"| get_call (`obj.get(\"k\")`) | {s['get_call']} |")
    md.append(f"| Archivos afectados | {s['files_affected']} |")
    md.append("")

    if not items:
        md.append("✅ No se detectaron accesos tipo diccionario en `ui/`.")
        return "\n".join(md)

    md.append("## Hallazgos (primeros 200)")
    md.append("")
    md.append("| Archivo | Línea | Tipo | Key | Contexto |")
    md.append("|--------|------:|------|-----|----------|")
    for it in items[:200]:
        ctx = str(it["context"]).replace("|", "\\|")
        md.append(f"| `{it['file']}` | {it['line']} | {it['kind']} | `{it['key']}` | `{ctx}` |")
    if len(items) > 200:
        md.append(f"| ... |  |  |  | *(+{len(items) - 200} más)* |")

    md.append("")
    md.append("## Recomendación de actuación (Fase 12C)")
    md.append("")
    md.append("- Sustituir accesos tipo dict por **atributos de DTO** cuando el objeto sea DTO.")
    md.append("- Si el objeto viene como dict desde presenter/servicio, convertirlo a DTO **antes** de llegar a UI.")
    md.append("- Mantener contrato: UI consume DTOs; solo componentes de construcción/serialización manipulan dicts.")
    md.append(
        "- Variables locales típicas (`data`, `item`, …) se filtran salvo claves en "
        "`DOMAIN_DICT_KEYS_FORCE_REPORT` del script (p. ej. `id`, `codigo`): revisar esos hallazgos con prioridad."
    )
    md.append("- Tras cada cambio: `pytest <scope> -x -q` y `python3 run_tests.py`.")

    return "\n".join(md)


def _gate_exit_code(
    total_findings: int,
    *,
    enforce_zero: bool,
    max_findings: int | None,
    baseline_path: Path | None,
) -> tuple[int, str]:
    """
    Devuelve (código_salida, mensaje_vacío_o_error).
    Prioridad: --enforce-zero > --baseline > --max-findings.
    """
    if enforce_zero:
        if total_findings > 0:
            return (
                1,
                f"UI DTO boundary: se exigen 0 hallazgos; hay {total_findings}.",
            )
        return 0, ""
    if baseline_path is not None:
        if not baseline_path.is_file():
            return 1, f"Baseline no encontrado: {baseline_path}"
        try:
            raw = json.loads(baseline_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return 1, f"Baseline JSON inválido ({baseline_path}): {e}"
        cap = int(raw.get("total_findings", 0))
        if total_findings > cap:
            return (
                1,
                f"UI DTO boundary: regresión ({total_findings} > baseline {cap}).",
            )
        return 0, ""
    if max_findings is not None:
        if total_findings > max_findings:
            return (
                1,
                f"UI DTO boundary: {total_findings} hallazgos > máximo permitido {max_findings}.",
            )
        return 0, ""
    return 0, ""


def main() -> int:
    """Punto de entrada CLI."""
    parser = argparse.ArgumentParser(description="Auditoría UI/DTO (Fase 12C)")
    parser.add_argument(
        "--include-production-flow",
        action="store_true",
        help="Incluir hallazgos en ui/**/production_flow (dicts de configuración deliberados).",
    )
    parser.add_argument("--json-only", action="store_true", help="Solo generar JSON")
    parser.add_argument("--md-only", action="store_true", help="Solo generar Markdown")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=str(BASE_DIR / "Documentacion" / "Refactorizacion_Completa" / "Fase_12C"),
        help="Directorio de salida",
    )
    parser.add_argument(
        "--enforce-zero",
        action="store_true",
        help="Salir con código 1 si hay algún hallazgo (misma heurística que el informe).",
    )
    parser.add_argument(
        "--max-findings",
        type=int,
        default=None,
        metavar="N",
        help="Salir con 1 si total_findings > N (omitir si se usa --enforce-zero o --baseline).",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default=None,
        metavar="PATH",
        help="JSON con clave total_findings; falla si el run actual supera ese total.",
    )
    args = parser.parse_args()

    report = build_report(include_production_flow=args.include_production_flow)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "ui_dto_boundary_report.json"

    if not args.md_only:
        json_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    if not args.json_only:
        (out_dir / "ui_dto_boundary_report.md").write_text(generate_md(report), encoding="utf-8")

    print(str(json_path))
    total = report["summary"]["total_findings"]
    print(f"Total hallazgos: {total}")

    baseline_p = Path(args.baseline) if args.baseline else None
    max_f = args.max_findings
    if args.enforce_zero:
        max_f = None
        baseline_p = None
    elif baseline_p is not None:
        max_f = None

    code, err = _gate_exit_code(
        total,
        enforce_zero=args.enforce_zero,
        max_findings=max_f,
        baseline_path=baseline_p,
    )
    if code != 0 and err:
        print(err, file=sys.stderr)
        print(f"Informe: {json_path}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())

