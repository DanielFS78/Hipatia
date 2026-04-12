#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: refine_module_descriptions

Descripción: Sustituye el párrafo ``Descripción:`` del docstring de módulo usando heurísticas
             sobre imports, clases y constantes de nivel superior; conserva ``Nombre del Módulo``.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from doc_audit_common import module_docstring_raw, parse_module  # noqa: E402
from docstrings_queue import _iter_scope_py_files  # noqa: E402

# Reutiliza mismas reglas que el auditor
import audit_module_description_quality as audit_mod  # noqa: E402


def _is_string_expr(node: ast.AST) -> bool:
    if not isinstance(node, ast.Expr):
        return False
    v = node.value
    return isinstance(v, ast.Constant) and isinstance(v.value, str)


def _docstring_line_range(tree: ast.Module) -> tuple[int, int] | None:
    i = 0
    while (
        i < len(tree.body)
        and isinstance(tree.body[i], ast.ImportFrom)
        and tree.body[i].module == "__future__"
    ):
        i += 1
    if i < len(tree.body) and _is_string_expr(tree.body[i]):
        n = tree.body[i]
        el = getattr(n, "end_lineno", None)
        if el is None:
            return None
        return n.lineno - 1, el
    if tree.body and _is_string_expr(tree.body[0]):
        n = tree.body[0]
        el = getattr(n, "end_lineno", None)
        if el is None:
            return None
        return n.lineno - 1, el
    return None


def _leading_special_lines(lines: list[str]) -> int:
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


def _top_import_roots(tree: ast.Module) -> list[str]:
    roots: list[str] = []
    for node in tree.body:
        if _is_string_expr(node):
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
    skip = frozenset({"typing", "abc", "enum", "logging", "dataclasses", "functools", "itertools", "collections"})
    out: list[str] = []
    for r in roots:
        if r not in skip and r not in out:
            out.append(r)
    return out[:8]


def _top_level_names(tree: ast.Module) -> tuple[list[str], list[str], list[str]]:
    classes: list[str] = []
    funcs: list[str] = []
    consts: list[str] = []
    for node in tree.body:
        if _is_string_expr(node):
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    consts.append(t.id)
                elif isinstance(t, ast.Name):
                    consts.append(t.id)
    return classes, funcs, consts[:10]


def _first_class_summary(tree: ast.Module) -> str:
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            d = ast.get_docstring(node)
            if d:
                line = d.strip().split("\n", 1)[0].strip()
                if len(line) > 12:
                    return line[:200]
    return ""


def _extract_nombre(doc: str) -> str:
    m = re.search(r"Nombre del Módulo:\s*([^\n]+)", doc)
    if m:
        return m.group(1).strip()
    return ""


def _body_skip_docstring(nodes: list[ast.stmt]) -> list[ast.stmt]:
    out: list[ast.stmt] = []
    for node in nodes:
        if _is_string_expr(node):
            continue
        out.append(node)
    return out


def _mostly_reexports_from_single_module(tree: ast.Module) -> tuple[bool, str | None]:
    """True si el módulo solo importa y reexporta (p. ej. shim ``core.dtos``)."""
    body = _body_skip_docstring(tree.body)
    body = [
        n
        for n in body
        if not (isinstance(n, ast.ImportFrom) and n.module == "__future__")
    ]
    if not body:
        return False, None
    mod: str | None = None
    for node in body:
        if isinstance(node, ast.ImportFrom) and node.module:
            if mod is None:
                mod = node.module
            elif node.module.split(".")[0] != mod.split(".")[0]:
                return False, None
        elif isinstance(node, ast.Import):
            return False, None
        elif isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            continue
        elif isinstance(node, ast.AnnAssign):
            continue
        else:
            return False, None
    return bool(mod), mod


def build_description(rel: str, tree: ast.Module, old_doc: str) -> str:
    classes, funcs, consts = _top_level_names(tree)
    imods = _top_import_roots(tree)
    cls_hint = _first_class_summary(tree)

    parts: list[str] = []

    shim, shim_mod = _mostly_reexports_from_single_module(tree)
    if shim and shim_mod and rel.endswith("core/dtos.py"):
        return (
            f"Módulo shim que reexporta los DTOs definidos en ``{shim_mod}`` bajo el import estable "
            f"``core.dtos``, para que el resto del código no acople nombres internos del paquete de modelos."
        )

    if "facade" in rel.lower() or (classes and "Facade" in classes[0]):
        fac = classes[0] if classes else "Facade"
        parts.append(
            f"Expone ``{fac}`` como API estable de aplicación sobre servicios ya inyectados; "
            f"no contiene reglas de persistencia directa."
        )
    elif classes and not consts:
        parts.append(
            "Define protocolos o tipos principales: "
            + ", ".join(f"``{c}``" for c in classes[:5])
            + "."
        )
        if cls_hint and cls_hint.lower() not in old_doc.lower():
            parts.append(cls_hint.rstrip(".") + ".")
    elif consts and not classes:
        parts.append(
            "Concentra datos de configuración o catálogos estáticos: "
            + ", ".join(f"``{c}``" for c in consts[:8])
            + ", consumidos por la UI y controladores."
        )
    elif funcs and not classes:
        parts.append(
            "Funciones puras de apoyo (sin estado de proceso): "
            + ", ".join(f"``{f}``" for f in funcs[:6])
            + "."
        )
    else:
        parts.append(
            "Funciones y datos de apoyo del paquete; conviene enlazar qué controlador o servicio las consume "
            "y qué estructuras devuelven (ver firmas al inicio del archivo)."
        )

    if imods:
        parts.append(
            "Integración típica con: " + ", ".join(f"``{m}``" for m in imods[:6]) + "."
        )

    text = " ".join(parts)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 90 and "protocolos" in rel.lower():
        text = (
            "Agrupa ``Protocol`` y tipos auxiliares para el subpaquete; "
            "alinea contratos de vista/servicio sin acoplar PyQt ni la BD. "
            + text
        )
    if "Paquete:" in old_doc and "Descripción:" not in old_doc:
        m = re.search(r"Paquete:\s*([^\n]+)", old_doc)
        if m:
            text = m.group(1).strip().rstrip(".") + ". " + text
    return text[:420].strip()


def _apply_file(path: Path, dry_run: bool) -> bool:
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    src = path.read_text(encoding="utf-8")
    tree, err = parse_module(str(path))
    if tree is None:
        print(f"SKIP parse {rel}: {err}", file=sys.stderr)
        return False
    old_doc = module_docstring_raw(tree)
    if not old_doc or "Nombre del Módulo" not in old_doc:
        return False
    reasons = audit_mod.audit_one(rel, old_doc)
    # Normalizar ficheros con Paquete: sin Descripción:
    needs = bool(reasons) or ("Paquete:" in old_doc and "Descripción:" not in old_doc)
    if not needs:
        return False

    nombre = _extract_nombre(old_doc)
    if not nombre:
        return False
    new_desc = build_description(rel, tree, old_doc)
    new_block = f'"""\nNombre del Módulo: {nombre}\n\nDescripción: {new_desc}\n"""\n'

    lines = src.splitlines(keepends=True)
    bounds = _docstring_line_range(tree)
    if bounds is None:
        print(f"SKIP bounds {rel}", file=sys.stderr)
        return False
    a, b = bounds
    n_lead = _leading_special_lines(lines)
    out = lines[:n_lead]
    if n_lead < a:
        out.extend(lines[n_lead:a])
    out.append(new_block)
    if b < len(lines):
        out.extend(lines[b:])
    new_src = "".join(out)
    if dry_run:
        print(f"WOULD {rel}")
        return True
    path.write_text(new_src, encoding="utf-8")
    print(f"OK {rel}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--path", type=str, default="", help="Solo una ruta relativa")
    args = ap.parse_args()
    paths = [PROJECT_ROOT / args.path] if args.path else list(_iter_scope_py_files())
    n = 0
    for path in paths:
        if path.is_file() and _apply_file(path, args.dry_run):
            n += 1
    print(f"Total: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
