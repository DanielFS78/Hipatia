#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: check_documentation_omissions
Descripción: Verifica automáticamente que la documentación técnica generada
             no tenga archivos omitidos en el índice de código.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DOC_FILE = BASE_DIR / "Documentacion" / "Documentacion Daniel.md"
GENERATOR = BASE_DIR / "scripts" / "generate_daniel_doc.py"
OMITTED_PATTERN = re.compile(
    r"\| Omitidos \(reglas de docstrings/otros\) \| (\d+) \|"
)


def regenerate_docs() -> None:
    """Regenera la documentación técnica usando el script oficial."""
    result = subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("❌ Error regenerando documentación.")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        raise SystemExit(result.returncode)


def read_omitted_count() -> int:
    """
    Extrae el valor de "Omitidos (reglas de docstrings/otros)" del markdown.
    """
    if not DOC_FILE.exists():
        raise SystemExit(
            f"❌ No existe el archivo de documentación: {DOC_FILE}"
        )

    content = DOC_FILE.read_text(encoding="utf-8")
    match = OMITTED_PATTERN.search(content)
    if not match:
        raise SystemExit(
            "❌ No se encontró la métrica de omitidos en el documento generado."
        )
    return int(match.group(1))


def main() -> None:
    """Punto de entrada del chequeo de regresión documental."""
    parser = argparse.ArgumentParser(
        description="Verifica que no haya omitidos en la documentación técnica."
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenera documentación antes de verificar.",
    )
    args = parser.parse_args()

    if args.regenerate:
        regenerate_docs()

    omitted_count = read_omitted_count()
    if omitted_count > 0:
        print(
            f"❌ Regresión detectada: omitidos={omitted_count}. "
            "Debe ser 0 para pasar el control."
        )
        raise SystemExit(1)

    print("✅ Documentación validada: omitidos=0.")


if __name__ == "__main__":
    main()
