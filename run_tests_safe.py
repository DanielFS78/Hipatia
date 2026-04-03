#!/usr/bin/env python3
"""
run_tests_safe.py — Ejecutor seguro de tests para proyectos con PyQt6.

Ejecuta cada archivo de test en un subproceso independiente para evitar
el segfault/abort que ocurre cuando se acumulan demasiados widgets Qt
en el mismo proceso.

Uso:
    python3 run_tests_safe.py                  # todos los tests
    python3 run_tests_safe.py tests/unit/      # solo una carpeta
    python3 run_tests_safe.py -k "nombre"      # filtro por nombre
    python3 run_tests_safe.py --fail-fast      # parar al primer fallo
"""

import sys
import os
import subprocess
import time
from pathlib import Path


# ── Colores ──────────────────────────────────────────────────────────────────

class C:
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"


# ── Helpers ───────────────────────────────────────────────────────────────────

def collect_test_files(paths: list[str]) -> list[Path]:
    """Devuelve todos los archivos test_*.py bajo los paths indicados."""
    files: list[Path] = []
    for p in paths:
        root = Path(p)
        if root.is_file() and root.name.startswith("test_"):
            files.append(root)
        elif root.is_dir():
            files.extend(sorted(root.rglob("test_*.py")))
    return files


def run_file(test_file: Path, extra_args: list[str]) -> tuple[bool, str, float]:
    """Ejecuta un archivo de test en subproceso aislado.

    Returns:
        (passed, output, duration_seconds)
    """
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"

    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "--tb=short", "-q", "--no-header",
        "--timeout=30",
        *extra_args,
    ]

    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
    duration = time.time() - t0

    output = result.stdout + result.stderr
    passed = result.returncode in (0, 5)  # 5 = all skipped (válido)
    return passed, output, duration


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]

    # Separar paths de flags
    paths: list[str] = []
    extra: list[str] = []
    fail_fast = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--fail-fast":
            fail_fast = True
        elif a.startswith("-"):
            extra.append(a)
            if a in ("-k", "-m", "--ignore") and i + 1 < len(args):
                i += 1
                extra.append(args[i])
        else:
            paths.append(a)
        i += 1

    if not paths:
        paths = ["tests"]

    test_files = collect_test_files(paths)
    if not test_files:
        print(f"{C.RED}No se encontraron archivos de test en: {paths}{C.RESET}")
        sys.exit(1)

    total = len(test_files)
    print(f"\n{C.BOLD}{'─'*70}{C.RESET}")
    print(f"{C.BOLD}  HIPATIA — Ejecutor seguro de tests  ({total} archivos){C.RESET}")
    print(f"{C.BOLD}{'─'*70}{C.RESET}\n")

    passed_files: list[str] = []
    failed_files: list[tuple[str, str]] = []
    t_global = time.time()

    for idx, tf in enumerate(test_files, 1):
        rel = str(tf.relative_to(Path.cwd()) if tf.is_absolute() else tf)
        print(f"  [{idx:>3}/{total}] {rel} ... ", end="", flush=True)

        try:
            ok, output, dur = run_file(tf, extra)
        except subprocess.TimeoutExpired:
            ok, output, dur = False, "TIMEOUT (>120s)", 120.0

        if ok:
            # Extraer conteo de tests del output
            count = ""
            for line in output.splitlines():
                if "passed" in line:
                    count = line.strip().split()[0]
                    break
            print(f"{C.GREEN}✓ {count} tests  ({dur:.2f}s){C.RESET}")
            passed_files.append(rel)
        else:
            print(f"{C.RED}✗ FALLO  ({dur:.2f}s){C.RESET}")
            failed_files.append((rel, output))
            if fail_fast:
                print(f"\n{C.YELLOW}--fail-fast: deteniendo ejecución.{C.RESET}")
                break

    # ── Resumen ───────────────────────────────────────────────────────────────
    elapsed = time.time() - t_global
    n_ok  = len(passed_files)
    n_err = len(failed_files)

    print(f"\n{C.BOLD}{'─'*70}{C.RESET}")
    print(f"  Archivos: {C.GREEN}{n_ok} OK{C.RESET}  /  {C.RED}{n_err} FALLIDOS{C.RESET}  "
          f"(total {total})   ⏱  {elapsed:.1f}s")

    if failed_files:
        print(f"\n{C.BOLD}{C.RED}ARCHIVOS CON FALLOS:{C.RESET}")
        for path, out in failed_files:
            print(f"\n  {C.BOLD}{path}{C.RESET}")
            # Mostrar solo las líneas relevantes del output
            lines = [l for l in out.splitlines() if l.strip()]
            relevant = [l for l in lines if any(
                kw in l for kw in ("FAILED", "ERROR", "assert", "Error:", "short test")
            )]
            for line in (relevant or lines)[-15:]:
                print(f"    {line}")

    print(f"{C.BOLD}{'─'*70}{C.RESET}\n")
    sys.exit(0 if n_err == 0 else 1)


if __name__ == "__main__":
    main()
