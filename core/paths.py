# -*- coding: utf-8 -*-
"""
Nombre del Módulo: paths
Descripción: Rutas de aplicación: desarrollo frente a ejecutable PyInstaller (``sys.frozen``).

- Solo lectura embebida: usar ``core.utils.helpers.resource_path`` (``_MEIPASS``).
- Escritura (SQLite, logs, backups, copia de usuario de ``config.ini``): directorio del
  ejecutable en frozen; raíz del repositorio en desarrollo.
- Evitar situar esa carpeta de datos escribibles bajo sincronización en la nube
  (iCloud, OneDrive, etc.): para estabilidad del SQLite y trazabilidad, preferir
  backup/restauración explícitos en lugar de sync transparente del directorio.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Callable


def get_writable_app_root() -> Path:
    """
    Directorio donde la app puede crear ``data/``, ``logs/``, etc.

    En binario PyInstaller (``onedir``/``onefile``) coincide con la carpeta del ``.exe``.
    En desarrollo, la raíz del repositorio (padre de ``core/``).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def resolve_user_config_ini(resource_path_fn: Callable[[str], str]) -> str:
    """
    Ruta efectiva de ``config/config.ini``.

    En desarrollo lee el fichero del repo. En frozen copia una vez desde el bundle
    a ``<exe_dir>/config/config.ini`` para que la conexión recordada sea escribible.
    """
    bundled = resource_path_fn("config/config.ini")
    if not getattr(sys, "frozen", False):
        return bundled

    user_dir = get_writable_app_root() / "config"
    user_dir.mkdir(parents=True, exist_ok=True)
    user_ini = user_dir / "config.ini"
    if not user_ini.is_file() and os.path.isfile(bundled):
        try:
            shutil.copy2(bundled, user_ini)
        except OSError:
            return bundled
    return str(user_ini if user_ini.is_file() else bundled)
