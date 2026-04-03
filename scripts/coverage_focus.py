#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cobertura enfocada a archivos modificados (Hipatia).

Objetivo: exigir 100% de cobertura en un conjunto de archivos/rutas concretas
sin forzar 100% del proyecto completo.

Requiere: pytest + pytest-cov instalados (ya se usa cobertura en el proyecto).

Uso:
  python3 scripts/coverage_focus.py --paths ui/widgets/reports/order_list.py core/app_model.py
  python3 scripts/coverage_focus.py --paths controllers --tests tests/unit/test_main_window.py

Notas:
- Este script ejecuta pytest con `--cov` y lee un `coverage.json` temporal.
- Por defecto omite `tests/*` y `scripts/*` del cálculo global de cobertura.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_temp_coveragerc(tmp_path: Path) -> None:
    tmp_path.write_text(
        "[run]\n"
        "omit =\n"
        "    tests/*\n"
        "    scripts/*\n",
        encoding="utf-8",
    )


def _run_pytest_with_coverage(tests: list[str], coveragerc: Path, out_json: Path) -> int:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=.",
        f"--cov-report=json:{out_json}",
        f"--cov-config={coveragerc}",
        "-q",
    ]
    if tests:
        cmd.extend(tests)
    proc = subprocess.run(cmd, text=True)
    # pytest devuelve 1 si fallan tests. Aun así puede haber json; pero lo tratamos como fallo.
    return proc.returncode


def _normalize_input_paths(paths: list[str]) -> list[str]:
    rels: list[str] = []
    for p in paths:
        rp = (REPO_ROOT / p).resolve()
        try:
            rel = rp.relative_to(REPO_ROOT)
        except ValueError:
            rel = Path(p)
        rels.append(str(rel))
    return rels


def _path_matches(target: str, needle: str) -> bool:
    # needle puede ser archivo o directorio relativo
    if target == needle:
        return True
    if needle.endswith("/"):
        return target.startswith(needle)
    if os.path.isdir(REPO_ROOT / needle):
        return target.startswith(needle.rstrip("/") + "/")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="+", required=True, help="Archivos o directorios a exigir 100%% cobertura.")
    ap.add_argument("--tests", nargs="*", default=[], help="Subset de tests a ejecutar (por defecto: toda la suite).")
    args = ap.parse_args()

    needles = _normalize_input_paths(args.paths)
    coveragerc = REPO_ROOT / ".coveragerc.focus.tmp"
    out_json = REPO_ROOT / "coverage.focus.tmp.json"

    try:
        _write_temp_coveragerc(coveragerc)
        rc = _run_pytest_with_coverage(args.tests, coveragerc, out_json)
        if rc != 0:
            print("FAIL: pytest falló; no se valida cobertura.")
            return rc

        data = json.loads(out_json.read_text(encoding="utf-8"))
        files: dict = data.get("files", {})
        if not files:
            print("FAIL: coverage.json no contiene datos de archivos.")
            return 2

        # Calcula % por archivo y agrega los que entren en el filtro.
        selected = []
        for filename, stats in files.items():
            if not filename.endswith(".py"):
                continue
            if any(_path_matches(filename, n) for n in needles):
                summary = stats.get("summary", {})
                stmts = int(summary.get("num_statements", 0))
                covered = int(summary.get("covered_lines", 0))
                missing = int(summary.get("missing_lines", 0))
                percent = (covered / stmts * 100.0) if stmts else 100.0
                selected.append((filename, percent, stmts, missing))

        if not selected:
            print("FAIL: no se seleccionó ningún archivo de cobertura (revisar --paths).")
            return 3

        bad = [s for s in selected if s[1] < 100.0]
        if bad:
            print("FAIL: cobertura < 100% en archivos objetivo:")
            for fn, pct, stmts, miss in sorted(bad, key=lambda x: x[1]):
                print(f"  - {fn}: {pct:.2f}% (stmts={stmts}, missing={miss})")
            return 4

        print("OK: cobertura 100% en todos los archivos objetivo.")
        return 0
    finally:
        for p in (coveragerc, out_json):
            try:
                p.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())

