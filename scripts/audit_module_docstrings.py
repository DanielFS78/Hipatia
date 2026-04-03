#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoría de docstrings de módulo: lista archivos .py sin descripción útil al nivel de módulo.

Salida: informe JSON bajo reports/ y resumen por stdout. Criterios alineados con
doc_audit_common / generate_daniel_doc.py.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from doc_audit_common import parse_module, summarize_module_for_audit, module_docstring_is_acceptable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
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


def iter_py_files(top_dirs: tuple[str, ...]) -> list[Path]:
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
                if not fname.endswith(".py"):
                    continue
                out.append(Path(root) / fname)
    return sorted(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit module-level docstrings.")
    parser.add_argument(
        "--json-out",
        default=str(REPORTS_DIR / "module_docstring_audit.json"),
        help="Ruta del informe JSON",
    )
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Imprimir solo rutas sin docstring de módulo aceptable",
    )
    args = parser.parse_args()

    files = iter_py_files(DEFAULT_TOP_DIRS)
    rows: list[dict] = []
    missing: list[str] = []
    errors: list[dict] = []

    for full in files:
        rel = str(full.relative_to(PROJECT_ROOT)).replace("\\", "/")
        tree, err = parse_module(str(full))
        if tree is None:
            errors.append({"rel_path": rel, "error": err})
            continue
        row = summarize_module_for_audit(rel, tree)
        rows.append(row)
        if not row["module_doc_ok"]:
            missing.append(rel)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.json_out)
    payload = {
        "total_scanned": len(rows),
        "module_doc_missing": len(missing),
        "parse_errors": len(errors),
        "files": rows,
        "missing_paths": missing,
        "errors": errors,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.only_missing:
        for p in missing:
            print(p)
    else:
        print(f"Escaneados: {len(rows)} archivos en {', '.join(DEFAULT_TOP_DIRS)}")
        print(f"Sin docstring de módulo aceptable: {len(missing)}")
        print(f"Errores de parseo: {len(errors)}")
        print(f"Informe: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
