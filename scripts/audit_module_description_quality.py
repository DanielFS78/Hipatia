#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: audit_module_description_quality

Descripción: Detecta ``Descripción`` de módulo débiles (genéricas, cortas o con frases prohibidas)
             en el alcance Daniel y escribe un informe Markdown bajo ``reports/``.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from doc_audit_common import module_docstring_raw, parse_module  # noqa: E402
from docstrings_queue import _iter_scope_py_files  # noqa: E402

BANNED_SUBSTRINGS = (
    "piezas de dominio",
    "piezas mixtas de dominio",
    "ver implementación",
    "lógica o utilidades del núcleo",
    "interfaz pyqt6",
    "este módulo",
    "pendiente de descripción",
    "sin resumen previo",
    "documentar:",
)

# Descripciones que solo rotulan sin sustancia (patrones al inicio, insensibles a mayúsculas)
WEAK_START_RE = re.compile(
    r"^(módulo de|modulo de|utilidades|helpers genéricos|script de|fichero de)\s",
    re.IGNORECASE,
)

MIN_DESC_LEN = 72


def _extract_descripcion_block(doc: str) -> str:
    if "Descripción:" not in doc and "Descripcion:" not in doc:
        return ""
    key = "Descripción:" if "Descripción:" in doc else "Descripcion:"
    i = doc.find(key)
    rest = doc[i + len(key) :].strip()
    # quitar líneas que parecen otro campo (no debería ocurrir)
    lines: list[str] = []
    for line in rest.splitlines():
        stripped = line.strip()
        if stripped.startswith("Nombre del Módulo"):
            break
        if stripped.startswith('"""') or stripped.startswith("'''"):
            break
        lines.append(line)
    joined = "\n".join(lines).strip()
    one_line = " ".join(x.strip() for x in joined.split())
    return one_line


def audit_one(rel: str, doc: str) -> list[str]:
    reasons: list[str] = []
    if "Nombre del Módulo" not in doc:
        reasons.append("sin_Nombre_del_Modulo_en_doc")
        return reasons
    desc = _extract_descripcion_block(doc)
    if not desc:
        reasons.append("sin_Descripcion")
        return reasons
    low = desc.lower()
    for b in BANNED_SUBSTRINGS:
        if b in low:
            reasons.append(f"prohibido:{b[:24]}")
    if len(desc) < MIN_DESC_LEN:
        reasons.append(f"corta_lt_{MIN_DESC_LEN}")
    if WEAK_START_RE.search(desc.strip()):
        reasons.append("inicio_debil_rotulo")
    # Tautología: solo repite el nombre del módulo con puntuación mínima
    if len(desc.split()) < 10 and "``" not in desc and "(" not in desc:
        reasons.append("muy_pocas_palabras_sin_detalle")
    return reasons


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        type=Path,
        default=PROJECT_ROOT / "reports" / "module_description_quality.md",
        help="Ruta del informe Markdown",
    )
    ap.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit 1 si hay al menos un hallazgo",
    )
    args = ap.parse_args()

    rows: list[tuple[str, str, list[str]]] = []
    for path in _iter_scope_py_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        tree, err = parse_module(str(path))
        if tree is None:
            rows.append((rel, f"parse:{err}", ["parse_error"]))
            continue
        doc = module_docstring_raw(tree)
        reasons = audit_one(rel, doc)
        if reasons:
            preview = (doc or "")[:160].replace("\n", " ")
            rows.append((rel, preview, reasons))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Auditoría: calidad de `Descripción` (módulo)",
        "",
        f"**Hallazgos:** {len(rows)}",
        f"Umbral mínimo: {MIN_DESC_LEN} caracteres en el texto de `Descripción` (una línea lógica).",
        "",
    ]
    for rel, preview, reasons in sorted(rows, key=lambda x: x[0]):
        lines.append(f"- `{rel}` — {', '.join(reasons)}")
        if preview:
            lines.append(f"  - _Vista_: {preview}…")
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Escrito {args.out} ({len(rows)} hallazgos)")
    if args.fail_on_issues and rows:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
