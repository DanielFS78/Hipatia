#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grafo de imports entre capas: controladores / servicios / database.

Genera un informe Markdown (y JSON opcional) con aristas ``controllers.*``
que importan ``core.services.*`` (y referencias cruzadas útiles para revisión).

Para el mapa **completo** por capa (``ui``, ``database``, ``core``, ``controllers``,
``features``), violaciones y ciclos simples, usar ``scripts/architecture_layer_edges.py``.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import defaultdict
from pathlib import Path

PREFIXES = ("core.services.", "core.", "database.", "controllers.", "features.", "ui.")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _path_to_module(py_file: Path, root: Path) -> str:
    rel = py_file.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


def _collect_imports(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
            else:
                names.add("*relative*")
    return names


def _interesting(target: str) -> bool:
    return any(target == p.rstrip(".") or target.startswith(p) for p in PREFIXES)


def build_controller_to_services(
    edges: dict[str, list[tuple[str, str]]],
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for mod, imps in sorted(edges.items()):
        if not mod.startswith("controllers."):
            continue
        for imp, _ in imps:
            if imp.startswith("core.services"):
                rows.append((mod, imp))
    return sorted(set(rows))


def render_markdown(
    controller_services: list[tuple[str, str]],
    edges: dict[str, list[tuple[str, str]]],
) -> str:
    lines = [
        "# Audit import graph — controllers ↔ core.services",
        "",
        "Generado por `scripts/audit_import_graph.py`.",
        "",
        "## `controllers.*` → `core.services.*`",
        "",
        "| Módulo controlador | Importa |",
        "|:--|:--|",
    ]
    for src, dst in controller_services:
        lines.append(f"| `{src}` | `{dst}` |")
    if not controller_services:
        lines.append("| — | *(ninguno explícito)* |")

    lines.extend(
        [
            "",
            "## Resumen por prefijo (módulos escaneados)",
            "",
        ]
    )
    prefix_counts: dict[str, int] = defaultdict(int)
    for mod, imps in edges.items():
        for imp, _ in imps:
            for p in PREFIXES:
                p_clean = p.rstrip(".")
                if imp.startswith(p_clean):
                    prefix_counts[p_clean] += 1
                    break
    for pref, n in sorted(prefix_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- `{pref}.*`: **{n}** referencias desde imports nominales")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit import graph between layers")
    parser.add_argument(
        "--out-md",
        type=Path,
        default=None,
        help="Escribir Markdown (default: reports/import_graph_audit.md)",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Escribir JSON con aristas completas",
    )
    args = parser.parse_args()

    root = _repo_root()
    dirs = ("controllers", "core/services", "features")
    flat_edges: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for dirname in dirs:
        base = root / dirname
        if not base.is_dir():
            continue
        for py in sorted(base.rglob("*.py")):
            try:
                text = py.read_text(encoding="utf-8")
                tree = ast.parse(text, filename=str(py))
            except (OSError, SyntaxError):
                continue
            mod = _path_to_module(py, root)
            for imp in _collect_imports(tree):
                if imp != "*relative*" and _interesting(imp):
                    flat_edges[mod].append((imp, mod))

    cs = build_controller_to_services(dict(flat_edges))
    md_default = root / "reports" / "import_graph_audit.md"
    out_md = args.out_md if args.out_md is not None else md_default
    out_md.parent.mkdir(parents=True, exist_ok=True)
    body = render_markdown(cs, dict(flat_edges))
    out_md.write_text(body, encoding="utf-8")
    print(f"Wrote {out_md}")

    if args.json:
        payload = {
            "controllers_to_core_services": [{"from": a, "to": b} for a, b in cs],
            "imports_by_module": {k: sorted({i for i, _ in v}) for k, v in sorted(flat_edges.items())},
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
