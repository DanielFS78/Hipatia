"""
Nombre del Módulo: scripts.build_executable

Descripción: Limpia ``build/`` y ``dist/`` y ejecuta PyInstaller con ``hipatia.spec``
             (misma configuración que CI «Build Windows EXE» y que ``build_windows.bat``).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def clean_build_environment() -> None:
    """Limpia compilaciones anteriores para evitar basura o conflictos."""
    print("[*] Limpiando directorios 'build' y 'dist'...")
    for folder in ("build", "dist"):
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"    - {folder}/ eliminado.")


def build_hipatia() -> None:
    """Invoca ``pyinstaller hipatia.spec`` desde la raíz del repositorio."""
    print("\n[*] Compilando con hipatia.spec (alineado con GitHub Actions)...")
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "hipatia.spec"]
    print("[*]", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] PyInstaller terminó con código {e.returncode}")
        sys.exit(e.returncode or 1)
    print("\n[+] Compilación completada.")
    print("[+] Salida: dist/Hipatia/Hipatia.exe (modo onedir)")


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    clean_build_environment()
    build_hipatia()
