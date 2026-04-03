#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inyecta docstrings de módulo donde faltan (criterio doc_audit_common), sin tocar
archivos que ya tienen docstring aceptable.

Uso::

    python3 scripts/inject_module_docstrings.py --dry-run
    python3 scripts/inject_module_docstrings.py --apply
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

# Mismo criterio que audit / Daniel doc
sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_audit_common import module_docstring_is_acceptable  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOP_DIRS = ("core", "database", "controllers", "ui", "scripts", "tools", "features")
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


def _iter_py_files(top_dirs: tuple[str, ...]) -> list[Path]:
    import os

    out: list[Path] = []
    for name in top_dirs:
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


def _describe_module(rel: str) -> str:
    """Una o dos frases en español; suficientemente específicas para no caer en frases genéricas prohibidas."""
    parts = rel.replace("\\", "/").split("/")
    stem = Path(rel).stem
    area = parts[0] if parts else "módulo"

    if area == "controllers":
        return (
            f"Coordinación y señales del subsistema «{stem}»: enlaza UI, servicios y "
            f"persistencia para este ámbito de la aplicación Hipatia."
        )
    if area == "core":
        return (
            f"Lógica o utilidades del núcleo (`{stem}`): tipos, servicios auxiliares o "
            f"infraestructura compartida fuera de la capa de interfaz."
        )
    if area == "database":
        return (
            f"Capa de datos (`{stem}`): modelos, repositorios o acceso SQLAlchemy "
            f"relacionado con este módulo."
        )
    if area == "ui":
        return (
            f"Interfaz PyQt6 (`{stem}`): widgets, diálogos o recursos visuales "
            f"conectados al flujo de usuario."
        )
    if area == "scripts":
        return (
            f"Script ejecutable (`{stem}`): automatización, informes o mantenimiento "
            f"del proyecto (no forma parte del runtime de la app)."
        )
    if area == "tools":
        return (
            f"Herramienta de consola (`{stem}`): análisis estático o asistencia "
            f"al desarrollo."
        )
    if area == "features":
        return (
            f"Funcionalidad encapsulada (`{stem}`): reglas de dominio o integración "
            f"opcional usada por controladores o servicios."
        )
    return f"Módulo `{rel}` del proyecto Hipatia."


def _insert_docstring(src: str, rel: str) -> str | None:
    tree, err = parse_module_from_source(src)
    if tree is None or err:
        return None
    if module_docstring_is_acceptable(tree):
        return None

    body = tree.body
    if not body:
        # Módulo vacío o solo comentarios → ast puede tener body vacío
        doc = _format_doc_block(rel)
        return doc + src.lstrip("\ufeff")

    # PEP 236: el docstring de módulo va antes de ``from __future__`` (línea = primer nodo del AST).
    insert_at_line = body[0].lineno

    lines = src.splitlines(keepends=True)
    # lineno 1-based
    pos = insert_at_line - 1
    if pos < 0:
        pos = 0
    if pos > len(lines):
        pos = len(lines)

    doc = _format_doc_block(rel)
    # Mantener una línea en blanco tras docstring si la siguiente línea no es vacía
    block = doc
    if pos < len(lines) and lines[pos].strip() != "":
        block = doc + "\n"

    return "".join(lines[:pos]) + block + "".join(lines[pos:])


def parse_module_from_source(src: str) -> tuple[ast.Module | None, str | None]:
    try:
        tree = ast.parse(src)
        assert isinstance(tree, ast.Module)
        return tree, None
    except SyntaxError as e:
        return None, str(e)


def _format_docblock_lines(rel: str) -> list[str]:
    text = _describe_module(rel)
    return ['"""', text, '"""', ""]


def _format_doc_block(rel: str) -> str:
    return "\n".join(_format_docblock_lines(rel))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Escribir cambios en disco")
    parser.add_argument("--dry-run", action="store_true", help="Solo listar (por defecto si no --apply)")
    parser.add_argument(
        "--max",
        type=int,
        default=0,
        help="Máximo de archivos a tocar (0 = sin límite)",
    )
    args = parser.parse_args()
    dry = not args.apply

    files = _iter_py_files(DEFAULT_TOP_DIRS)
    touched = 0
    skipped = 0
    errors: list[str] = []

    for full in files:
        if args.max and touched >= args.max:
            break
        rel = str(full.relative_to(PROJECT_ROOT)).replace("\\", "/")
        raw = full.read_text(encoding="utf-8")
        tree, perr = parse_module_from_source(raw)
        if tree is None:
            errors.append(f"{rel}: {perr}")
            continue
        if module_docstring_is_acceptable(tree):
            skipped += 1
            continue

        new_src = _insert_docstring(raw, rel)
        if new_src is None or new_src == raw:
            skipped += 1
            continue

        if dry:
            print(f"would patch: {rel}")
        else:
            full.write_text(new_src, encoding="utf-8")
            print(f"patched: {rel}")
        touched += 1

    print(f"# touched={touched} skipped_ok={skipped} errors={len(errors)}", file=sys.stderr)
    for e in errors[:20]:
        print(e, file=sys.stderr)
    if len(errors) > 20:
        print(f"... y {len(errors) - 20} errores más", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
