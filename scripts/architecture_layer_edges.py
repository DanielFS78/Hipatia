#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grafo de imports entre capas de primer nivel (ui, controllers, core, database, features).

Escanea AST de todos los .py bajo esos directorios, clasifica aristas por capa origen/destino,
lista violaciones de arquitectura (reglas del plan Hipatia) y detecta ciclos simples
entre capas (2- y 3-ciclos explícitos).

Uso:
  python3 scripts/architecture_layer_edges.py
  python3 scripts/architecture_layer_edges.py --json reports/architecture_layer_edges.json
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict

LAYERS = frozenset({"ui", "controllers", "core", "database", "features"})
SCAN_DIRS = ("ui", "database", "core", "controllers", "features")

# Violaciones duras: invertir requiere refactor arquitectónico claro.
VIOLATIONS_HARD: tuple[tuple[str, str], ...] = (
    ("database", "ui"),
    ("database", "controllers"),
    ("core", "ui"),
)

# Advertencias: acoplamiento a vigilar o reducir con DTO / DI / presenters.
VIOLATIONS_SOFT: tuple[tuple[str, str], ...] = (
    ("ui", "database"),
    ("controllers", "ui"),
    ("features", "ui"),
    ("features", "controllers"),
    ("features", "database"),
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def path_to_module(py_file: Path, root: Path) -> str:
    rel = py_file.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


def collect_import_targets(tree: ast.AST) -> set[str]:
    """Nombres de módulo completos importados (sin relativos)."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
    return names


def module_layer(module_name: str) -> str | None:
    root_pkg = module_name.split(".")[0]
    return root_pkg if root_pkg in LAYERS else None


def scan_layers(root: Path) -> dict[str, set[str]]:
    """module_name -> conjunto de strings importados (módulos)."""
    modules: dict[str, set[str]] = {}
    for dirname in SCAN_DIRS:
        base = root / dirname
        if not base.is_dir():
            continue
        for py in sorted(base.rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            try:
                text = py.read_text(encoding="utf-8")
                tree = ast.parse(text, filename=str(py))
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
            mod = path_to_module(py, root)
            raw = collect_import_targets(tree)
            modules[mod] = {i for i in raw if i and not i.startswith(".")}
    return modules


def build_layer_edge_list(
    modules_to_imports: dict[str, set[str]],
) -> DefaultDict[tuple[str, str], list[tuple[str, str]]]:
    """(from_layer, to_layer) -> [(source_module, imported_module), ...]."""
    edges: DefaultDict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for src_mod, imports in modules_to_imports.items():
        src_l = module_layer(src_mod)
        if src_l is None:
            continue
        for imp in imports:
            tgt_l = module_layer(imp)
            if tgt_l is None or tgt_l == src_l:
                continue
            edges[(src_l, tgt_l)].append((src_mod, imp))
    return edges


def layer_adjacency_set(
    edges: DefaultDict[tuple[str, str], list[tuple[str, str]]],
) -> set[tuple[str, str]]:
    return {k for k, v in edges.items() if v}


def find_simple_cycles(adj_edges: set[tuple[str, str]]) -> list[list[str]]:
    """2-ciclos y 3-ciclos entre capas (suficiente para N pequeño)."""
    adj: dict[str, set[str]] = defaultdict(set)
    nodes: set[str] = set()
    for a, b in adj_edges:
        nodes.add(a)
        nodes.add(b)
        adj[a].add(b)

    cycles: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()

    def add_cycle(c: list[str]) -> None:
        key = tuple(c)
        if key not in seen:
            seen.add(key)
            cycles.append(c)

    for a in nodes:
        for b in adj[a]:
            if a in adj[b]:
                pair = tuple(sorted([a, b]))
                if pair not in seen:
                    seen.add(pair)
                    cycles.append([a, b, a])
            for c in adj[b]:
                if c in adj and a in adj[c]:
                    add_cycle([a, b, c, a])
    return cycles


def render_markdown(
    edges: DefaultDict[tuple[str, str], list[tuple[str, str]]],
    cycles: list[list[str]],
) -> str:
    lines = [
        "# Arquitectura — aristas entre capas (imports AST)",
        "",
        "Generado por `scripts/architecture_layer_edges.py`.",
        "",
        "## Matriz resumen (conteo de aristas módulo→módulo por capa)",
        "",
        "| Desde \\ Hacia | " + " | ".join(sorted(LAYERS)) + " |",
        "|:--|" + "|".join([":--:"] * len(LAYERS)) + "|",
    ]
    for src in sorted(LAYERS):
        row = [f"| **{src}** |"]
        for dst in sorted(LAYERS):
            n = len(edges.get((src, dst), []))
            row.append(f" {n} |")
        lines.append("".join(row))
    lines.append("")

    lines.extend(["## Violaciones duras (reglas arquitectura)", ""])
    for pair in VIOLATIONS_HARD:
        items = edges.get(pair, [])
        lines.append(f"### `{pair[0]}` → `{pair[1]}` ({len(items)} aristas)")
        if not items:
            lines.append("- *(ninguna)*")
        else:
            for sm, im in sorted(set(items))[:80]:
                lines.append(f"- `{sm}` importa `{im}`")
            if len(items) > 80:
                lines.append(f"- … *y {len(items) - 80} más*")
        lines.append("")

    lines.extend(["## Advertencias (revisar / reducir acoplamiento)", ""])
    for pair in VIOLATIONS_SOFT:
        items = edges.get(pair, [])
        lines.append(f"### `{pair[0]}` → `{pair[1]}` ({len(items)} aristas)")
        if not items:
            lines.append("- *(ninguna)*")
        else:
            for sm, im in sorted(set(items))[:40]:
                lines.append(f"- `{sm}` importa `{im}`")
            if len(items) > 40:
                lines.append(f"- … *y {len(items) - 40} más*")
        lines.append("")

    lines.extend(["## Ciclos simples entre capas (2- y 3-aristas)", ""])
    if not cycles:
        lines.append("- *(no detectados en este análisis)*")
    else:
        for c in cycles:
            lines.append(f"- `{' → '.join(c)}`")
    lines.append("")
    return "\n".join(lines)


def build_json_payload(
    modules_to_imports: dict[str, set[str]],
    edges: DefaultDict[tuple[str, str], list[tuple[str, str]]],
    cycles: list[list[str]],
) -> dict:
    edge_list = [
        {"from_layer": a, "to_layer": b, "source": sm, "imported": im}
        for (a, b), pairs in sorted(edges.items())
        for sm, im in pairs
    ]
    return {
        "layers": sorted(LAYERS),
        "module_count": len(modules_to_imports),
        "layer_edges": edge_list,
        "cycles_layer": cycles,
        "violations_hard_counts": {
            f"{a}->{b}": len(edges.get((a, b), [])) for a, b in VIOLATIONS_HARD
        },
        "violations_soft_counts": {
            f"{a}->{b}": len(edges.get((a, b), [])) for a, b in VIOLATIONS_SOFT
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Layer import graph for Hipatia")
    parser.add_argument(
        "--out-md",
        type=Path,
        default=None,
        help="Salida Markdown (default: reports/architecture_layer_edges.md)",
    )
    parser.add_argument("--json", type=Path, default=None, help="Salida JSON opcional")
    args = parser.parse_args()

    root = repo_root()
    modules = scan_layers(root)
    edges = build_layer_edge_list(modules)
    adj = layer_adjacency_set(edges)
    cycles = find_simple_cycles(adj)

    out_md = args.out_md if args.out_md is not None else root / "reports" / "architecture_layer_edges.md"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(edges, cycles), encoding="utf-8")
    print(f"Wrote {out_md}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        payload = build_json_payload(modules, edges, cycles)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
