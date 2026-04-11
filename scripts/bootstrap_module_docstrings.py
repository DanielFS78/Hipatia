#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: bootstrap_module_docstrings

Descripción: Inserta o sustituye el docstring inicial de módulo con ``Nombre del Módulo`` y
             ``Descripción``, reutilizando el primer párrafo del docstring existente cuando sea útil.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from docstrings_queue import (  # noqa: E402
    MARKER,
    PREFIX_BYTES,
    _iter_scope_py_files,
    _needs_docstring,
)


def _module_label(rel: Path) -> str:
    parts = rel.parts
    if parts[-1] == "__init__.py":
        return ".".join(parts[:-1]) if len(parts) > 1 else parts[0].replace(".py", "")
    stem = parts[-1].removesuffix(".py")
    if len(parts) == 1:
        return stem
    return ".".join(parts[:-1] + (stem,))


def _first_paragraph(text: str | None) -> str:
    if not text:
        return ""
    block = text.strip().split("\n\n", 1)[0].strip()
    one = " ".join(line.strip() for line in block.splitlines() if line.strip())
    if len(one) > 320:
        one = one[:317].rstrip() + "…"
    return one


def _build_description(old_doc: str | None, label: str) -> str:
    para = _first_paragraph(old_doc)
    if para and MARKER not in para and "Interfaz PyQt6" not in para and "Lógica o utilidades" not in para:
        return para
    if para and len(para) > 40:
        return para
    return (
        f"Resumen operativo pendiente de precisión para ``{label}``: ejecutar "
        f"``python3 scripts/refine_module_descriptions.py --path <ruta>`` tras revisar clases "
        f"públicas e imports (ver skill ``docstrings_oleada_secuencial``)."
    )


def _leading_special_lines(lines: list[str]) -> int:
    """Devuelve n líneas iniciales (shebang, coding, noqa de archivo) a conservar."""
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s == "" or s.startswith("#!") or s.startswith("# -*- coding") or s.startswith("# coding:"):
            i += 1
            continue
        if s.startswith("# noqa: ") and i < 3:
            i += 1
            continue
        break
    return i


def _is_string_expr(node: ast.AST) -> bool:
    if not isinstance(node, ast.Expr):
        return False
    v = node.value
    return isinstance(v, ast.Constant) and isinstance(v.value, str)


def _apply_one(path: Path, dry_run: bool) -> bool:
    rel = path.relative_to(PROJECT_ROOT)
    if not _needs_docstring(path):
        return False
    src = path.read_text(encoding="utf-8")
    if MARKER in src[:PREFIX_BYTES]:
        return False
    label = _module_label(rel)
    try:
        tree = ast.parse(src)
    except SyntaxError:
        print(f"SKIP syntax: {rel}", file=sys.stderr)
        return False
    old_doc = ast.get_docstring(tree, clean=False)
    desc = _build_description(old_doc, label)
    new_doc = f'"""\nNombre del Módulo: {label}\n\nDescripción: {desc}\n"""\n'

    lines = src.splitlines(keepends=True)
    n_lead = _leading_special_lines(lines)

    body0 = tree.body[0] if tree.body else None
    if body0 is not None and _is_string_expr(body0) and getattr(body0, "end_lineno", None) is not None:
        a = body0.lineno - 1
        b = body0.end_lineno
        out = lines[:n_lead]
        if n_lead < a:
            out.extend(lines[n_lead:a])
        out.append(new_doc)
        if b < len(lines):
            if not out[-1].endswith("\n"):
                out[-1] += "\n"
            out.extend(lines[b:])
        new_src = "".join(out)
    else:
        insert_at = n_lead
        if tree.body:
            first = tree.body[0]
            if isinstance(first, ast.ImportFrom) and first.module == "__future__":
                insert_at = first.lineno - 1
        new_src = "".join(lines[:insert_at]) + new_doc + "".join(lines[insert_at:])

    if dry_run:
        print(f"WOULD: {rel}")
        return True
    path.write_text(new_src, encoding="utf-8")
    print(f"OK: {rel}")
    return True


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--path", type=str, help="Solo un archivo relativo al repo")
    args = p.parse_args()
    if args.path:
        paths = [PROJECT_ROOT / args.path]
    else:
        paths = [x for x in _iter_scope_py_files() if _needs_docstring(x)]
    n = 0
    for path in paths:
        if path.is_file() and _apply_one(path, args.dry_run):
            n += 1
    print(f"Total procesados: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
