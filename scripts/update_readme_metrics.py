#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: scripts.update_readme_metrics

Descripción: Actualiza el bloque de métricas del README entre los marcadores HIPATIA_METRICS.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
BEGIN = "<!-- HIPATIA_METRICS_BEGIN -->"
END = "<!-- HIPATIA_METRICS_END -->"

_FINDER_DUP_TEST = re.compile(r" \d+\.py$")


def _count_test_files() -> int:
    return len(
        sorted(
            p
            for p in (ROOT / "tests").rglob("test_*.py")
            if not (p.name.startswith("test_") and _FINDER_DUP_TEST.search(p.name))
        )
    )


def _pytest_collect_count() -> int | None:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "--collect-only", "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    out = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"(\d+)\s+tests?\s+collected", out, re.I)
    return int(m.group(1)) if m else None


def _compliance_stats() -> tuple[float | None, float | None, int | None, int | None, int | None]:
    p = ROOT / "test_reports" / "compliance_data.json"
    if not p.exists():
        return None, None, None, None, None
    data: list[dict] = json.loads(p.read_text(encoding="utf-8"))
    if not data:
        return None, None, None, None, None
    scores = [float(x.get("score", 0)) for x in data]
    ceilings = [float(x.get("ceiling_score", x.get("score", 0))) for x in data]
    at_ceiling = sum(1 for x in data if x.get("at_ceiling"))
    test_named = [x for x in data if str(x.get("name", "")).startswith("test_")]
    at_test = sum(1 for x in test_named if x.get("at_ceiling"))
    return (
        sum(scores) / len(scores),
        sum(ceilings) / len(ceilings),
        len(data),
        at_ceiling,
        at_test if test_named else None,
    )


def _coverage_percent() -> float | None:
    p = ROOT / "coverage.json"
    if not p.exists():
        return None
    try:
        totals = json.loads(p.read_text(encoding="utf-8")).get("totals") or {}
        raw = totals.get("percent_covered")
        if raw is None:
            return None
        return float(raw)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _build_block() -> str:
    today = date.today().isoformat()
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    n_collect = _pytest_collect_count()
    n_files = _count_test_files()
    cov = _coverage_percent()
    avg_s, avg_c, n_comp, at_all, at_tests = _compliance_stats()

    lines = [
        BEGIN,
        "",
        "> **Regeneración:** `python scripts/update_readme_metrics.py`  ",
        "> **Datos:** `test_reports/compliance_data.json` vía `python scripts/test_quality_analyzer.py`; "
        "`coverage.json` vía `pytest tests --cov=. --cov-report=json` (archivo en `.gitignore`).",
        "",
        "| Métrica | Valor |",
        "|---------|-------|",
        f"| Fecha de referencia | {today} |",
        f"| Python usado al generar | {py_ver} |",
    ]
    if n_collect is not None:
        lines.append(f"| Casos de test recogidos (pytest) | {n_collect} |")
    else:
        lines.append("| Casos de test recogidos (pytest) | — |")

    lines.append(f"| Archivos `test_*.py` (sin copias `* N.py`) | {n_files} |")

    if cov is not None:
        lines.append(f"| Cobertura global (`pytest tests --cov=.`) | {cov:.1f}% |")
    else:
        lines.append("| Cobertura global | — *(generar `coverage.json`)* |")

    if avg_s is not None and avg_c is not None:
        lines.append(f"| Score calidad medio (absoluto → techo medio) | {avg_s:.1f} → {avg_c:.1f} |")
    else:
        lines.append("| Score calidad medio | — *(ejecutar `test_quality_analyzer.py`)* |")

    if n_comp is not None:
        lines.append(f"| Entradas en analizador de calidad | {n_comp} |")
    if at_all is not None:
        lines.append(f"| Entradas marcadas «en techo» | {at_all} / {n_comp or 0} |")
    if at_tests is not None and n_comp is not None:
        lines.append(f"| …de ellas, archivos `test_*.py` en techo | {at_tests} |")

    lines.extend(["", END, ""])
    return "\n".join(lines)


def main() -> int:
    if not README.exists():
        print("README.md no encontrado", file=sys.stderr)
        return 1
    text = README.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        print("Faltan marcadores HIPATIA_METRICS en README.md", file=sys.stderr)
        return 1
    before, _, rest = text.partition(BEGIN)
    _, _, after = rest.partition(END)
    new_text = before + _build_block() + after
    README.write_text(new_text, encoding="utf-8")
    print(f"Actualizado: {README}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
