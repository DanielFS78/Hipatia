#!/usr/bin/env python3
"""
Nombre del Módulo: ui_dto_findings_catalog
Descripcion: Inventario de hallazgos UI/DTO (subscript y .get con clave literal)
             con metadatos de conexion: receptor AST, agrupacion por archivo/receptor,
             imports del modulo y enlaces entre hallazgos del mismo grupo.

Uso:
    python3 scripts/ui_dto_findings_catalog.py
    python3 scripts/ui_dto_findings_catalog.py --no-production-flow
    python3 scripts/ui_dto_findings_catalog.py --json-only

Salida (por defecto):
    Documentacion/Refactorizacion_Completa/Fase_12C/ui_dto_findings_catalog.json
    Documentacion/Refactorizacion_Completa/Fase_12C/ui_dto_findings_catalog.md
    Documentacion/Refactorizacion_Completa/Fase_12C/ui_dto_findings_checklist.md
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import ui_dto_boundary_analyzer as uda  # noqa: E402


def _receiver_for_subscript(node: ast.Subscript) -> str:
    try:
        return ast.unparse(node.value)
    except Exception:
        return "?"


def _receiver_for_get_call(node: ast.Call) -> str:
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
    ):
        return "?"
    try:
        return ast.unparse(node.func.value)
    except Exception:
        return "?"


def _extract_constant_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _top_level_imports(lines: list[str]) -> list[str]:
    try:
        tree = ast.parse("\n".join(lines))
    except Exception:
        return []
    out: list[str] = []
    for n in tree.body:
        if isinstance(n, ast.Import):
            for alias in n.names:
                out.append(f"import {alias.name}")
        elif isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            names = ", ".join(a.name for a in n.names)
            out.append(f"from {mod} import {names}")
    return out[:40]


def _analyze_file_enriched(path: Path) -> list[dict[str, Any]]:
    lines = uda._read_lines(path)
    try:
        tree = ast.parse("\n".join(lines))
    except Exception:
        return []

    rel = str(path.relative_to(ROOT))
    raw: list[tuple[str, int, int, str, str, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name):
                if node.value.value.id == "self" and node.value.attr in uda.INTERNAL_UI_DICT_ATTRS:
                    continue
            if isinstance(node.value, ast.Name) and node.value.id in uda._TYPING_NAME_IDS:
                continue
            key = _extract_constant_str(node.slice)
            if not key:
                continue
            if isinstance(node.value, ast.Name) and not uda.should_report_name_dict_access(
                node.value.id, key
            ):
                continue
            recv = _receiver_for_subscript(node)
            raw.append(
                (
                    "subscript",
                    getattr(node, "lineno", 1),
                    getattr(node, "col_offset", 0),
                    key,
                    uda._context_line(lines, getattr(node, "lineno", 1)),
                    recv,
                )
            )

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            if isinstance(node.func.value, ast.Attribute) and isinstance(node.func.value.value, ast.Name):
                if node.func.value.value.id == "self" and node.func.value.attr in uda.INTERNAL_UI_DICT_ATTRS:
                    continue
            if uda._is_os_environ_access(node.func.value):
                continue
            if not node.args:
                continue
            key = _extract_constant_str(node.args[0])
            if not key:
                continue
            if isinstance(node.func.value, ast.Name) and not uda.should_report_name_dict_access(
                node.func.value.id, key
            ):
                continue
            recv = _receiver_for_get_call(node)
            raw.append(
                (
                    "get_call",
                    getattr(node, "lineno", 1),
                    getattr(node, "col_offset", 0),
                    key,
                    uda._context_line(lines, getattr(node, "lineno", 1)),
                    recv,
                )
            )

    imports = tuple(_top_level_imports(lines))
    out: list[dict[str, Any]] = []
    for row in raw:
        kind, line, col, key, context, recv = row
        gid = f"{rel}::{recv}"
        out.append(
            {
                "file": rel,
                "line": line,
                "col": col,
                "kind": kind,
                "key": key,
                "context": context,
                "receiver": recv,
                "group_id": gid,
                "imports_sample": imports,
                "status": "pendiente",
            }
        )
    return out


def build_catalog(*, include_production_flow: bool) -> dict[str, Any]:
    all_rows: list[dict[str, Any]] = []
    for p in uda._iter_ui_files():
        rel = str(p.relative_to(ROOT))
        if not include_production_flow:
            if any(rel.startswith(prefix) for prefix in uda.DEFAULT_EXCLUDE_SUBDIRS):
                continue
            if rel in uda.DEFAULT_EXCLUDE_FILES:
                continue
        all_rows.extend(_analyze_file_enriched(p))

    for i, row in enumerate(all_rows):
        row["id"] = f"F{i + 1:04d}"
        gid = row["group_id"]
        related = tuple(
            f"F{j + 1:04d}"
            for j, r in enumerate(all_rows)
            if r["group_id"] == gid and f"F{j + 1:04d}" != row["id"]
        )
        row["related_ids"] = related

    by_file: dict[str, int] = defaultdict(int)
    for r in all_rows:
        by_file[r["file"]] += 1

    summary = {
        "total": len(all_rows),
        "files_affected": len(by_file),
        "subscript": sum(1 for r in all_rows if r["kind"] == "subscript"),
        "get_call": sum(1 for r in all_rows if r["kind"] == "get_call"),
        "groups": len({r["group_id"] for r in all_rows}),
    }

    return {
        "generated_at": datetime.now().isoformat(),
        "base_dir": str(ROOT),
        "include_production_flow": include_production_flow,
        "summary": summary,
        "by_file_counts": dict(sorted(by_file.items(), key=lambda x: (-x[1], x[0]))),
        "items": all_rows,
    }


def _item_signature(it: dict[str, Any]) -> str:
    """Clave estable al cambiar numeración F0001 tras regenerar."""
    return f"{it['file']}|{it['kind']}|{it['key']}|{it['receiver']}"


def _load_existing_status_by_signature(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        prev = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, str] = {}
    for it in prev.get("items", []):
        sig = it.get("signature") or _item_signature(it)
        out[sig] = it.get("status", "pendiente")
    return out


def merge_status(catalog: dict[str, Any], previous_by_sig: dict[str, str]) -> None:
    for it in catalog["items"]:
        it["signature"] = _item_signature(it)
        if previous_by_sig.get(it["signature"]) == "hecho":
            it["status"] = "hecho"


def write_checklist_md(catalog: dict[str, Any], out: Path) -> None:
    lines: list[str] = []
    lines.append("# Fase 12C — Checklist de hallazgos UI/DTO")
    lines.append("")
    lines.append(f"> Generado: {catalog['generated_at'][:19].replace('T', ' ')}")
    lines.append("> Regenerar con: `python3 scripts/ui_dto_findings_catalog.py`")
    lines.append("")
    lines.append("Marcar **`[x]`** cuando el hallazgo quede corregido o documentado como dict deliberado.")
    lines.append("")
    lines.append("## Resumen por archivo")
    lines.append("")
    lines.append("| Archivo | Hallazgos |")
    lines.append("|---------|----------:|")
    for fpath, n in catalog["by_file_counts"].items():
        lines.append(f"| `{fpath}` | {n} |")
    lines.append("")
    lines.append("## Listado (orden F0001…)")
    lines.append("")
    lines.append("| OK | Id | Archivo | Línea | Tipo | Clave | Receptor | Relacionados |")
    lines.append("|----|-----|---------|------:|------|-------|----------|--------------|")
    for it in catalog["items"]:
        ok = "x" if it["status"] == "hecho" else " "
        rel = ", ".join(it["related_ids"][:6])
        if len(it["related_ids"]) > 6:
            rel += ", …"
        recv = str(it["receiver"]).replace("|", "\\|")[:48]
        lines.append(
            f"| [{ok}] | `{it['id']}` | `{it['file']}` | {it['line']} | {it['kind']} | `{it['key']}` | `{recv}` | {rel or '—'} |"
        )
    lines.append("")
    lines.append("## Conexiones (por grupo)")
    lines.append("")
    lines.append("Hallazgos con el mismo `group_id` comparten **receptor** y **archivo** (misma cadena de acceso AST). Conviene abordarlos juntos.")
    lines.append("")
    by_g: dict[str, list[str]] = defaultdict(list)
    for it in catalog["items"]:
        by_g[it["group_id"]].append(it["id"])
    for gid in sorted(by_g.keys(), key=lambda g: (by_g[g][0], len(by_g[g]))):
        ids = ", ".join(by_g[gid])
        lines.append(f"- **{gid}** → {ids}")
    out.write_text("\n".join(lines), encoding="utf-8")


def write_catalog_md(catalog: dict[str, Any], out: Path) -> None:
    s = catalog["summary"]
    lines: list[str] = []
    lines.append("# Catálogo UI/DTO — Hallazgos y conexiones")
    lines.append("")
    lines.append(f"- **Total:** {s['total']} | **Archivos:** {s['files_affected']} | **Grupos (receptor+archivo):** {s['groups']}")
    lines.append(f"- **include_production_flow:** {catalog['include_production_flow']}")
    lines.append("")
    lines.append("## Detalle por hallazgo (muestra 80)")
    lines.append("")
    for it in catalog["items"][:80]:
        lines.append(f"### {it['id']} — `{it['file']}`:{it['line']}")
        lines.append("")
        lines.append(f"- **Tipo:** {it['kind']} | **Clave:** `{it['key']}`")
        lines.append(f"- **Receptor:** `{it['receiver']}`")
        lines.append(f"- **Grupo:** `{it['group_id']}`")
        lines.append(f"- **Relacionados:** {', '.join(it['related_ids']) or '—'}")
        lines.append(f"- **Estado:** {it['status']}")
        lines.append(f"- **Contexto:** `{it['context']}`")
        if it["imports_sample"]:
            lines.append("- **Imports (muestra):**")
            for imp in it["imports_sample"][:12]:
                lines.append(f"  - `{imp}`")
        lines.append("")
    if len(catalog["items"]) > 80:
        lines.append(f"*(+{len(catalog['items']) - 80} hallazgos en JSON)*")
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Catálogo Fase 12C con conexiones")
    parser.add_argument(
        "--no-production-flow",
        action="store_true",
        help="Excluir ui/**/production_flow y archivos por defecto del analizador.",
    )
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=str(ROOT / "Documentacion" / "Refactorizacion_Completa" / "Fase_12C"),
    )
    args = parser.parse_args()
    include_pf = not args.no_production_flow
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "ui_dto_findings_catalog.json"
    prev_by_sig = _load_existing_status_by_signature(json_path)
    catalog = build_catalog(include_production_flow=include_pf)
    merge_status(catalog, prev_by_sig)

    if not args.json_only:
        write_catalog_md(catalog, out_dir / "ui_dto_findings_catalog.md")
        write_checklist_md(catalog, out_dir / "ui_dto_findings_checklist.md")

    json_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print(str(json_path))
    print(f"Total: {catalog['summary']['total']} | grupos: {catalog['summary']['groups']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
