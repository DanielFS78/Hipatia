# -*- coding: utf-8 -*-
"""Criterios compartidos para auditoría de docstrings de módulo (Daniel doc + audit_module_docstrings)."""

from __future__ import annotations

import ast
from typing import Any

# Mantener alineado con la lógica histórica de generate_daniel_doc.py
FRASES_IGNORADAS: frozenset[str] = frozenset(
    {
        "",
        "None",
        "Sin descripción disponible",
        "Sin descripción disponible.",
        "None.",
    }
)


def _string_from_expr_node(node: ast.AST) -> str | None:
    if isinstance(node, ast.Expr):
        v = node.value
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            return v.value
    return None


def module_docstring_raw(tree: ast.Module) -> str:
    """
    Texto del docstring de módulo.

    Incluye el caso frecuente ``from __future__ ...`` seguido de un literal ``\"\"\"...\"\"\"``,
    que **no** expone ``ast.get_docstring`` pero es doc de módulo válido en tiempo de ejecución.
    """
    d = ast.get_docstring(tree)
    if d is not None and d.strip():
        return d
    i = 0
    while i < len(tree.body):
        stmt = tree.body[i]
        if not isinstance(stmt, ast.ImportFrom) or stmt.module != "__future__":
            break
        i += 1
    if i < len(tree.body):
        s = _string_from_expr_node(tree.body[i])
        if s is not None:
            return s
    return ""


def module_docstring_is_acceptable(tree: ast.Module) -> bool:
    """
    True si el módulo tiene docstring de módulo no trivial según FRASES_IGNORADAS.
    Equivale a 'doc_valid' en generate_daniel_doc para el nodo raíz.
    """
    doc = module_docstring_raw(tree).strip()
    return doc not in FRASES_IGNORADAS


def parse_module(path: str) -> tuple[ast.Module | None, str | None]:
    """Parsea un archivo UTF-8; devuelve (tree, None) o (None, mensaje de error)."""
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        tree = ast.parse(src)
        assert isinstance(tree, ast.Module)
        return tree, None
    except Exception as e:
        return None, str(e)


def summarize_module_for_audit(rel_path: str, tree: ast.Module) -> dict[str, Any]:
    """Resumen para informes JSON (clases/funcs top-level sin depender del docstring)."""
    classes: list[str] = []
    functions: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
    return {
        "rel_path": rel_path.replace("\\", "/"),
        "module_doc_ok": module_docstring_is_acceptable(tree),
        "module_doc_preview": (module_docstring_raw(tree) or "")[:200],
        "top_level_classes": classes,
        "top_level_functions": functions,
    }
