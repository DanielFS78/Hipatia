#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: scripts.sync_worktree_to_icloud

Descripción: Copia archivos modificados o sin seguimiento desde SOURCE_ROOT a HIPATIA_ICLOUD.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git_porcelain(root: Path) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "-u"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as e:
        print(f"git no disponible: {e}", file=sys.stderr)
        return []
    if out.returncode != 0:
        print(out.stderr or "git status falló", file=sys.stderr)
        return []
    rels: list[str] = []
    for line in out.stdout.splitlines():
        if len(line) < 4:
            continue
        path_part = line[3:].strip()
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[-1].strip()
        if path_part.startswith('"') and path_part.endswith('"'):
            path_part = path_part[1:-1]
        rels.append(path_part)
    return rels


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync modified paths to HIPATIA_ICLOUD")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo listar; no copiar",
    )
    args = parser.parse_args()

    source = Path(os.environ.get("SOURCE_ROOT", str(_repo_root()))).resolve()
    dest_root = os.environ.get("HIPATIA_ICLOUD", "").strip()
    if not dest_root:
        print("Defina HIPATIA_ICLOUD (ruta del clon iCloud).", file=sys.stderr)
        return 1
    dest = Path(dest_root).expanduser().resolve()
    if source == dest:
        print("Sync N/A: SOURCE_ROOT es igual a HIPATIA_ICLOUD.")
        return 0

    rels = _git_porcelain(source)
    if not rels:
        print("No hay cambios en git status (o git falló).")
        return 0

    copied = 0
    for rel in rels:
        src = source / rel
        if not src.is_file():
            continue
        dst = dest / rel
        if args.dry_run:
            print(f"would copy: {rel}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        import shutil

        shutil.copy2(src, dst)
        copied += 1
        print(f"OK {rel}")

    if not args.dry_run:
        print(f"# Copiados: {copied} archivos → {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
