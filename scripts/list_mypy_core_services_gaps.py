#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lista módulos bajo ``core/services`` que aún no aparecen en ``mypy.ini`` dentro
de un bloque ``[mypy-...]`` con ``disallow_untyped_defs = True``.

Uso::

    python3 scripts/list_mypy_core_services_gaps.py
    python3 scripts/list_mypy_core_services_gaps.py --json reports/mypy_core_services_gaps.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RE_SECTION = re.compile(r"^\[mypy-([^\]]+)\]\s*$")
RE_MODULE = re.compile(r"core\.services(?:\.[a-zA-Z_][a-zA-Z0-9_]*)+")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _discover_service_modules(services_dir: Path) -> list[str]:
    mods: list[str] = []
    for p in sorted(services_dir.rglob("*.py")):
        rel = p.relative_to(services_dir)
        if rel.name == "__init__.py":
            continue
        parts = list(rel.with_suffix("").parts)
        mods.append("core.services." + ".".join(parts))
    return mods


def _strict_modules_from_ini(ini_path: Path) -> set[str]:
    text = ini_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    strict: set[str] = set()
    i = 0
    while i < len(lines):
        m = RE_SECTION.match(lines[i].strip())
        if m:
            section_body = m.group(1)
            # siguiente línea puede ser disallow_untyped_defs = True (o False)
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("["):
                if lines[j].strip() == "disallow_untyped_defs = True":
                    for part in section_body.split(","):
                        part = part.strip()
                        for mod in RE_MODULE.findall(part):
                            strict.add(mod)
                j += 1
            i = j
            continue
        i += 1
    return strict


def main() -> int:
    parser = argparse.ArgumentParser(description="Gaps mypy core.services vs mypy.ini")
    parser.add_argument("--json", type=Path, default=None, help="Escribir salida JSON")
    args = parser.parse_args()

    root = _repo_root()
    services = root / "core" / "services"
    ini = root / "mypy.ini"
    if not services.is_dir():
        print("No existe core/services", file=sys.stderr)
        return 1
    discovered = _discover_service_modules(services)
    strict = _strict_modules_from_ini(ini)
    gaps = sorted(m for m in discovered if m not in strict)

    for m in gaps:
        print(m)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "total_modules": len(discovered),
            "strict_count": len(strict & set(discovered)),
            "gap_count": len(gaps),
            "gaps": gaps,
        }
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"# JSON: {args.json}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
