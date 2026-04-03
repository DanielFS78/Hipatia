#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reordena el docstring de módulo inmediatamente **antes** del bloque ``from __future__``.

Homogeneidad con PEP 236 (docstring antes de future). Idempotente si ya está bien ordenado.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("core", "database", "controllers", "ui", "scripts", "tools", "features")
SKIP_DIR_NAMES = frozenset(
    {
        "__pycache__",
        "tests",
        "Documentacion",
        "venv",
        ".git",
        ".agents",
        "htmlcov",
        "test_reports",
        ".venv",
        "migrations",
        "Backup",
        "data",
        "logs",
    }
)


def _iter_py_files() -> list[Path]:
    import os

    out: list[Path] = []
    for name in SCAN_DIRS:
        base = PROJECT_ROOT / name
        if not base.is_dir():
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = [
                d
                for d in sorted(dirs)
                if d not in SKIP_DIR_NAMES and not d.startswith(".") and not d.startswith("test_")
            ]
            for fname in sorted(files):
                if fname.endswith(".py"):
                    out.append(Path(root) / fname)
    return sorted(out)


def _leading_future_count(body: list[ast.stmt]) -> int:
    k = 0
    while k < len(body):
        stmt = body[k]
        if not isinstance(stmt, ast.ImportFrom) or stmt.module != "__future__":
            break
        k += 1
    return k


def _is_string_expr(node: ast.stmt) -> ast.Constant | None:
    if not isinstance(node, ast.Expr):
        return None
    v = node.value
    if isinstance(v, ast.Constant) and isinstance(v.value, str):
        return v
    return None


def reorder_source(src: str) -> str | None:
    """
    Devuelve texto reordenado o None si no aplica.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None

    body = tree.body
    k = _leading_future_count(body)
    if k == 0:
        return None

    # Ya cumple PEP: primer nodo es docstring (no future primero).
    if ast.get_docstring(tree):
        return None

    doc_idx = k
    if doc_idx >= len(body):
        return None
    if _is_string_expr(body[doc_idx]) is None:
        return None

    lines = src.splitlines(keepends=True)
    fut_first = body[0]
    fut_last = body[k - 1]
    doc_node = body[doc_idx]

    fs, fe = fut_first.lineno, fut_last.end_lineno or fut_last.lineno
    ds, de = doc_node.lineno, doc_node.end_lineno or doc_node.lineno

    # 1-based → slices 0-based [start-1 : end) para bloque future
    i0, i1 = fs - 1, fe
    j0, j1 = ds - 1, de

    if not (0 <= i0 <= i1 <= len(lines) and 0 <= j0 <= j1 <= len(lines) and i1 <= j0):
        return None

    header = lines[:i0]
    future_block = lines[i0:i1]
    between = lines[i1:j0]
    doc_block = lines[j0:j1]
    tail = lines[j1:]

    # Un solo salto entre doc y future; entre future y tail conservar un \n mínimo
    sep_doc_fut = "\n" if not doc_block[-1].endswith("\n") else ""
    # Quitar between (suelen ser líneas en blanco entre future y doc)
    sep_fut_tail = "\n"
    if tail and not tail[0].strip():
        sep_fut_tail = ""

    new_src = (
        "".join(header)
        + "".join(doc_block)
        + sep_doc_fut
        + "".join(future_block)
        + sep_fut_tail
        + "".join(tail)
    )
    if new_src == src:
        return None
    return new_src


def main() -> int:
    parser = argparse.ArgumentParser(description="Docstring antes de __future__ (PEP 236)")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    changed = 0
    skipped = 0
    for path in _iter_py_files():
        raw = path.read_text(encoding="utf-8")
        new = reorder_source(raw)
        if new is None:
            skipped += 1
            continue
        rel = path.relative_to(PROJECT_ROOT)
        if args.apply:
            path.write_text(new, encoding="utf-8")
            print(f"OK {rel}")
            changed += 1
        else:
            print(f"would: {rel}")
            changed += 1

    print(f"# changed={changed} skipped={skipped}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
