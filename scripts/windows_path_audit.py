#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: windows_path_audit

Descripción: Recorre código de producto y lista patrones de rutas que pueden fallar en Windows
             (concatenación con ``/``, ``/tmp`` sin guard Darwin, etc.). Escribe ``reports/windows_path_audit.md``.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("core", "controllers", "database", "features", "ui")
EXTRA_FILES = (PROJECT_ROOT / "app.py",)
SKIP_DIR_NAMES = frozenset({"__pycache__", ".git", "venv", ".venv", "node_modules"})


@dataclass(frozen=True)
class Finding:
    rel: str
    line_no: int
    severity: str
    pattern: str
    hint: str
    line_text: str


def _is_whitelisted_line(s: str) -> bool:
    t = s.strip()
    if "sqlite:///" in t:
        return True
    if "http://" in t or "https://" in t:
        return True
    if "# noqa" in t and "path" in t.lower():
        return True
    if "video4linux" in t or "/sys/class/" in t:
        return True
    if "darwin" in t.lower() or "sys.platform" in t:
        return True
    # Workaround PyQt solo desarrollo macOS en ``app._fix_qt_macos``
    if "tmp_pyqt" in t and "/tmp/" in t:
        return True
    return False


PATTERNS: list[tuple[str, str, str]] = [
    (r"['\"]\s*\+\s*['\"]/['\"]\s*\+", "P1", "concat_slash", "Usar pathlib.Path / operator"),
    (r"\+ ['\"]/['\"] \+", "P1", "concat_slash", "Usar pathlib.Path"),
    (r"/tmp/", "P1", "posix_tmp", "Restringir a macOS o usar tempfile / get_writable_app_root"),
    (r"['\"][A-Za-z]:\\\\", "P2", "hardcoded_win_drive", "Suele ser ejemplo; confirmar que no sea lógica runtime"),
]


def scan_file(path: Path) -> list[Finding]:
    rel = str(path.relative_to(PROJECT_ROOT))
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return findings
    for i, line in enumerate(text.splitlines(), start=1):
        if _is_whitelisted_line(line):
            continue
        for rx, sev, pid, hint in PATTERNS:
            if re.search(rx, line):
                findings.append(
                    Finding(rel, i, sev, pid, hint, line.strip()[:200])
                )
                break
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        type=Path,
        default=PROJECT_ROOT / "reports" / "windows_path_audit.md",
        help="Ruta del informe Markdown",
    )
    args = ap.parse_args()
    all_findings: list[Finding] = []
    for d in SCAN_DIRS:
        base = PROJECT_ROOT / d
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            if any(p in path.parts for p in SKIP_DIR_NAMES):
                continue
            all_findings.extend(scan_file(path))
    for path in EXTRA_FILES:
        if path.is_file():
            all_findings.extend(scan_file(path))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    p0 = [f for f in all_findings if f.severity == "P0"]
    p1 = [f for f in all_findings if f.severity == "P1"]
    p2 = [f for f in all_findings if f.severity == "P2"]

    lines = [
        "# Auditoría de rutas (compatibilidad Windows)",
        "",
        "Generado por `scripts/windows_path_audit.py`. Prioridad: **P0** (rotura probable en Windows), **P1**, **P2**.",
        "",
        "## Resumen",
        "",
        f"- Hallazgos P0: **{len(p0)}**",
        f"- Hallazgos P1: **{len(p1)}**",
        f"- Hallazgos P2: **{len(p2)}**",
        "",
        "## Rutas canónicas en el proyecto",
        "",
        "- Escritura y SQLite: [`core/paths.py`](../core/paths.py) (`get_writable_app_root`, `resolve_user_config_ini`).",
        "- Recursos embebidos PyInstaller: `core.utils.helpers.resource_path`.",
        "- URLs SQLAlchemy `sqlite:///` con `.as_posix()` son válidas en Windows.",
        "",
    ]

    def section(title: str, items: list[Finding]) -> None:
        lines.append(f"## {title}")
        lines.append("")
        if not items:
            lines.append("*Sin hallazgos.*")
            lines.append("")
            return
        lines.append("| Archivo | Línea | Patrón | Severidad | Sugerencia |")
        lines.append("|---------|-------|--------|-----------|------------|")
        for f in sorted(items, key=lambda x: (x.rel, x.line_no)):
            esc = f.line_text.replace("|", "\\|")
            lines.append(
                f"| `{f.rel}` | {f.line_no} | `{f.pattern}` | {f.severity} | {f.hint} | `{esc}` |"
            )
        lines.append("")

    section("P0", p0)
    section("P1", p1)
    section("P2", p2)

    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Escrito {args.out} (P0={len(p0)}, P1={len(p1)}, P2={len(p2)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
