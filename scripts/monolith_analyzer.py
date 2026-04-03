#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analizador de monolitos y dependencias (Hipatia).

Genera:
- Ranking de archivos Python por tamaño (LOC) y acoplamiento (in/out degree).
- Grafo de imports por módulo (package-level) y por archivo (file-level).
- Detección básica de ciclos (SCC) en el grafo.
- Reporte Markdown + JSON para alimentar la fase "Monolitos".

Uso:
  python3 scripts/monolith_analyzer.py
  python3 scripts/monolith_analyzer.py --min-loc 500 --top 30
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SCAN_DIRS = (
    "controllers",
    "core",
    "database",
    "features",
    "ui",
)

DEFAULT_EXCLUDE_DIR_PARTS = (
    "__pycache__",
    ".venv",
    "htmlcov",
    "temp_chunks",
    "migration",
    "migrations",
)


@dataclass(frozen=True)
class FileNode:
    rel_path: str
    loc: int
    imports: list[str]


@dataclass(frozen=True)
class GraphStats:
    nodes: int
    edges: int
    scc_count: int
    cyclic_scc_count: int


def _iter_py_files(scan_dirs: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for d in scan_dirs:
        base = (REPO_ROOT / d).resolve()
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if any(part in DEFAULT_EXCLUDE_DIR_PARTS for part in p.parts):
                continue
            files.append(p)
    return sorted(files)


def _count_loc(text: str) -> int:
    # LOC "simple": líneas no vacías. (Suficiente para ranking; no intenta ser perfecto.)
    return sum(1 for line in text.splitlines() if line.strip())


class _ImportCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: set[str] = set()
        self._skip_depth: int = 0

    @staticmethod
    def _is_type_checking_guard(test: ast.expr) -> bool:
        # if TYPE_CHECKING:
        if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
            return True
        # if typing.TYPE_CHECKING:
        if isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
            if isinstance(test.value, ast.Name) and test.value.id in {"typing", "t"}:
                return True
        return False

    def visit_If(self, node: ast.If) -> None:  # noqa: N802
        """
        Ignora imports dentro de:
          if TYPE_CHECKING:
        ya que no forman parte del grafo de dependencias en runtime.
        """
        if self._is_type_checking_guard(node.test):
            self._skip_depth += 1
            # visitar solo orelse (puede contener imports runtime)
            for n in node.orelse:
                self.visit(n)
            self._skip_depth -= 1
            return
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        if self._skip_depth:
            return
        for alias in node.names:
            if alias.name:
                self.imports.add(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if self._skip_depth:
            return
        if node.module:
            self.imports.add(node.module)


def _module_name_for_path(py_file: Path) -> str:
    rel = py_file.relative_to(REPO_ROOT).with_suffix("")
    return ".".join(rel.parts)


def _safe_read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")
    except OSError:
        return None


def _parse_imports(py_file: Path) -> list[str]:
    text = _safe_read_text(py_file)
    if text is None:
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    v = _ImportCollector()
    v.visit(tree)
    return sorted(v.imports)


def _build_nodes(py_files: list[Path]) -> dict[str, FileNode]:
    nodes: dict[str, FileNode] = {}
    for p in py_files:
        text = _safe_read_text(p)
        if text is None:
            continue
        rel = str(p.relative_to(REPO_ROOT))
        nodes[rel] = FileNode(rel_path=rel, loc=_count_loc(text), imports=_parse_imports(p))
    return nodes


def _resolve_internal_target(import_str: str, module_to_file: dict[str, str]) -> Optional[str]:
    """
    Resuelve un import a un archivo del repo si coincide con un módulo interno.
    Heurística: intenta el módulo completo y prefijos.
    """
    if import_str in module_to_file:
        return module_to_file[import_str]
    # prefijos: "a.b.c" -> intenta "a.b"
    parts = import_str.split(".")
    while len(parts) > 1:
        parts.pop()
        candidate = ".".join(parts)
        if candidate in module_to_file:
            return module_to_file[candidate]
    return None


def _build_edges(nodes: dict[str, FileNode]) -> dict[str, set[str]]:
    module_to_file: dict[str, str] = {}
    for rel, node in nodes.items():
        module_to_file[_module_name_for_path(REPO_ROOT / rel)] = rel

    edges: dict[str, set[str]] = {rel: set() for rel in nodes}
    for rel, node in nodes.items():
        for imp in node.imports:
            target = _resolve_internal_target(imp, module_to_file)
            if target and target in nodes and target != rel:
                edges[rel].add(target)
    return edges


def _reverse_edges(edges: dict[str, set[str]]) -> dict[str, set[str]]:
    rev: dict[str, set[str]] = {n: set() for n in edges}
    for src, dsts in edges.items():
        for dst in dsts:
            rev[dst].add(src)
    return rev


def _scc_kosaraju(nodes: list[str], edges: dict[str, set[str]]) -> list[list[str]]:
    """
    SCC por Kosaraju (sin dependencias externas).
    """
    visited: set[str] = set()
    order: list[str] = []

    def dfs1(u: str) -> None:
        visited.add(u)
        for v in edges.get(u, set()):
            if v not in visited:
                dfs1(v)
        order.append(u)

    for n in nodes:
        if n not in visited:
            dfs1(n)

    rev = _reverse_edges(edges)
    visited.clear()
    sccs: list[list[str]] = []

    def dfs2(u: str, acc: list[str]) -> None:
        visited.add(u)
        acc.append(u)
        for v in rev.get(u, set()):
            if v not in visited:
                dfs2(v, acc)

    for n in reversed(order):
        if n not in visited:
            comp: list[str] = []
            dfs2(n, comp)
            sccs.append(comp)

    return sccs


def _rank(nodes: dict[str, FileNode], edges: dict[str, set[str]], min_loc: int) -> list[dict]:
    rev = _reverse_edges(edges)
    ranked: list[dict] = []
    for rel, node in nodes.items():
        if node.loc < min_loc:
            continue
        ranked.append(
            {
                "rel_path": rel,
                "loc": node.loc,
                "out_degree": len(edges.get(rel, set())),
                "in_degree": len(rev.get(rel, set())),
                "imports_internal": sorted(edges.get(rel, set())),
                "imported_by": sorted(rev.get(rel, set())),
            }
        )
    ranked.sort(key=lambda r: (r["loc"], r["in_degree"], r["out_degree"]), reverse=True)
    return ranked


def _write_outputs(
    *,
    out_dir: Path,
    min_loc: int,
    top: int,
    nodes: dict[str, FileNode],
    edges: dict[str, set[str]],
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    sccs = _scc_kosaraju(list(nodes.keys()), edges)
    cyclic = [c for c in sccs if len(c) > 1]

    ranked = _rank(nodes, edges, min_loc=min_loc)[:top]

    generated_at = datetime.now().isoformat(timespec="seconds")
    payload_stats: dict[str, int] = {
        "nodes": len(nodes),
        "edges": sum(len(v) for v in edges.values()),
        "scc_count": len(sccs),
        "cyclic_scc_count": len(cyclic),
    }
    cyclic_sccs: list[list[str]] = sorted((sorted(c) for c in cyclic), key=len, reverse=True)[
        :20
    ]

    payload = {
        "generated_at": generated_at,
        "repo_root": str(REPO_ROOT),
        "scan_dirs": list(DEFAULT_SCAN_DIRS),
        "min_loc": min_loc,
        "top": top,
        "graph": {
            "nodes": {k: asdict(v) for k, v in nodes.items()},
            "edges": {k: sorted(list(v)) for k, v in edges.items()},
        },
        "stats": payload_stats,
        "ranked_monoliths": ranked,
        "cyclic_sccs": cyclic_sccs,
    }

    json_path = out_dir / "monolith_report.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    md_lines: list[str] = []
    md_lines.append("# Reporte de Monolitos — Hipatia\n")
    md_lines.append(f"- Generado: **{generated_at}**\n")
    md_lines.append(f"- Rutas escaneadas: `{', '.join(DEFAULT_SCAN_DIRS)}`\n")
    md_lines.append(f"- Umbral monolito (LOC): **{min_loc}+**\n")
    md_lines.append(
        f"- Nodos/edges: **{payload_stats['nodes']} / {payload_stats['edges']}**\n"
    )
    md_lines.append(f"- SCC cíclicas: **{payload_stats['cyclic_scc_count']}**\n")
    md_lines.append("\n## Ranking (top)\n")
    md_lines.append("| Archivo | LOC | In | Out |\n")
    md_lines.append("|---|---:|---:|---:|\n")
    for r in ranked:
        md_lines.append(f"| `{r['rel_path']}` | {r['loc']} | {r['in_degree']} | {r['out_degree']} |\n")

    if cyclic_sccs:
        md_lines.append("\n## Ciclos detectados (SCC > 1)\n")
        for i, comp in enumerate(cyclic_sccs, start=1):
            md_lines.append(f"\n### Ciclo {i} (tamaño {len(comp)})\n")
            for n in comp:
                md_lines.append(f"- `{n}`\n")

    md_path = out_dir / "monolith_report.md"
    md_path.write_text("".join(md_lines), encoding="utf-8")
    return md_path, json_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--min-loc",
        type=int,
        default=250,
        help="Umbral LOC para considerar monolito (recomendado 250 en este repo).",
    )
    parser.add_argument("--top", type=int, default=30, help="Número de archivos a mostrar en ranking.")
    parser.add_argument(
        "--out-dir",
        type=str,
        default=str(REPO_ROOT / "Documentacion" / "Refactorizacion_Completa" / "Monolitos"),
        help="Directorio de salida para los reportes.",
    )
    args = parser.parse_args()

    py_files = _iter_py_files(DEFAULT_SCAN_DIRS)
    nodes = _build_nodes(py_files)
    edges = _build_edges(nodes)

    md_path, json_path = _write_outputs(
        out_dir=Path(args.out_dir),
        min_loc=args.min_loc,
        top=args.top,
        nodes=nodes,
        edges=edges,
    )

    print(f"OK: reporte generado en {md_path}")
    print(f"OK: datos JSON en {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

