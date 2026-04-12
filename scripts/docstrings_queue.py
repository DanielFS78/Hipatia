#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: docstrings_queue

Descripción: Genera la cola ordenada de módulos sin ``Nombre del Módulo`` (oleadas A–F) y
             permite verificar cuántos faltan; debe mantenerse alineado con ``generate_daniel_doc``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Debe coincidir con scripts/generate_daniel_doc.py (INCLUDE_DIRS + INCLUDE_ROOT_FILES).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INCLUDE_DIRS = ("controllers", "core", "database", "features", "ui", "scripts", "tools", "migrations")
INCLUDE_ROOT_FILES = (
    "app.py",
    "analyze_ui.py",
    "generate_ui_report.py",
    "run_tests.py",
    "run_tests_safe.py",
)
IGNORE_PARTS = frozenset(
    {
        "__pycache__",
        ".git",
        "venv",
        ".venv",
        "htmlcov",
        "tests",
        "Documentacion",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".agents",
    }
)

PREFIX_BYTES = 8000
MARKER = "Nombre del Módulo"

# Oleadas por prefijo (orden de trabajo). migrations antes que tools (plan E).
WAVE_ORDER = (
    ("A", "core", ("core",)),
    ("B", "controllers", ("controllers",)),
    ("C", "database", ("database",)),
    ("C2", "features", ("features",)),
    ("D", "ui", ("ui",)),
    ("E", "migrations + tools", ("migrations", "tools")),
    ("F", "scripts", ("scripts",)),
)


def _iter_scope_py_files() -> list[Path]:
    out: list[Path] = []
    for name in INCLUDE_ROOT_FILES:
        p = PROJECT_ROOT / name
        if p.is_file():
            out.append(p)
    for top in INCLUDE_DIRS:
        base = PROJECT_ROOT / top
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.py")):
            if set(p.parts) & IGNORE_PARTS:
                continue
            out.append(p)
    return sorted(set(out), key=lambda x: str(x).lower())


def _needs_docstring(path: Path) -> bool:
    try:
        head = path.read_text(encoding="utf-8")[:PREFIX_BYTES]
    except OSError:
        return True
    return MARKER not in head


def _wave_for_path(rel: str) -> str | None:
    for wave_id, _title, prefixes in WAVE_ORDER:
        for pref in prefixes:
            if rel == pref or rel.startswith(pref + "/"):
                return wave_id
    if "/" not in rel and rel in INCLUDE_ROOT_FILES:
        return None  # raíz: ya documentados en plan previo
    return "?"


def collect_missing_ordered() -> list[tuple[str, Path]]:
    """Lista (wave_id, path) en orden A→F, luego alfabético dentro de cada oleada."""
    missing_by_wave: dict[str, list[Path]] = {w[0]: [] for w in WAVE_ORDER}
    for path in _iter_scope_py_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if not _needs_docstring(path):
            continue
        wid = _wave_for_path(rel)
        if wid is None:
            continue
        if wid == "?":
            missing_by_wave.setdefault("?", []).append(path)
            continue
        missing_by_wave[wid].append(path)
    ordered: list[tuple[str, Path]] = []
    for wave_id, _title, _prefs in WAVE_ORDER:
        for p in sorted(missing_by_wave.get(wave_id, []), key=lambda x: str(x).lower()):
            ordered.append((wave_id, p))
    for p in sorted(missing_by_wave.get("?", []), key=lambda x: str(x).lower()):
        ordered.append(("?", p))
    return ordered


def write_queue_md(path: Path) -> int:
    rows = collect_missing_ordered()
    lines = [
        "# Cola oleada: docstrings de módulo (`Nombre del Módulo`)",
        "",
        "Generado con `python3 scripts/docstrings_queue.py --write`.",
        "Marcar `- [x]` al cerrar cada archivo (gates OK). **Un archivo por iteración** del agente.",
        "",
    ]
    if not rows:
        lines.append("*(No hay pendientes en el alcance Daniel. Tras nuevos `.py`, volver a ejecutar `--write`.)*")
        lines.append("")
    current_wave = ""
    for wave_id, p in rows:
        if wave_id != current_wave:
            for wid, title, _ in WAVE_ORDER:
                if wid == wave_id:
                    lines.append(f"## Oleada {wave_id} — {title}")
                    lines.append("")
                    break
            else:
                lines.append(f"## Oleada {wave_id}")
                lines.append("")
            current_wave = wave_id
        rel = p.relative_to(PROJECT_ROOT).as_posix()
        lines.append(f"- [ ] `{rel}`")
    lines.append("")
    lines.append(f"**Total pendientes:** {len(rows)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return len(rows)


def verify() -> tuple[int, int, list[str]]:
    """Devuelve (total_scope, missing_count, missing_rel_paths)."""
    all_paths = _iter_scope_py_files()
    missing: list[str] = []
    for p in all_paths:
        if _needs_docstring(p):
            missing.append(p.relative_to(PROJECT_ROOT).as_posix())
    return len(all_paths), len(missing), sorted(missing)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cola y verificación de docstrings de módulo.")
    parser.add_argument(
        "--write",
        action="store_true",
        help=f"Escribir {PROJECT_ROOT / 'Documentacion' / 'OLEADA_DOCSTRINGS_COLA.md'}",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Listar rutas pendientes (hasta 120) además del resumen",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit 1 si queda algún pendiente (útil en CI)",
    )
    args = parser.parse_args()
    total, n_miss, paths = verify()
    print(f"Alcance: {total} archivos .py")
    print(f"Sin '{MARKER}' en primeros {PREFIX_BYTES} bytes: {n_miss}")
    if args.write:
        out = PROJECT_ROOT / "Documentacion" / "OLEADA_DOCSTRINGS_COLA.md"
        n = write_queue_md(out)
        print(f"Escrito {out} ({n} entradas)")
    if args.verify and n_miss:
        for rel in paths[:120]:
            print(f"  {rel}")
        if len(paths) > 120:
            print(f"  ... y {len(paths) - 120} más")
    if args.fail_on_missing and n_miss:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
