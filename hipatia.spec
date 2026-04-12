# -*- mode: python ; coding: utf-8 -*-
"""
Especificación PyInstaller para Hipatia (modo onedir, Windows de referencia).

Ejecutar en Windows: ``build_windows.bat`` o ``pyinstaller hipatia.spec``.
Los datos de usuario (SQLite, logs, ``config/config.ini`` editable) se crean junto al ``.exe``
gracias a ``core.paths.get_writable_app_root``.
"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

# SPECPATH (PyInstaller) = directorio que contiene este .spec, no el padre del repo.
ROOT = Path(SPECPATH).resolve()
_root = str(ROOT)
if _root not in sys.path:
    sys.path.insert(0, _root)

block_cipher = None

# Diálogos/widgets cargados con ``importlib`` (p. ej. ``controllers.ui_class_loader.ui_class``):
# el análisis estático de PyInstaller no los incluye si no están en el grafo de imports.
_hidden_ui_dynamic = (
    collect_submodules("ui.dialogs")
    + collect_submodules("ui.widgets")
    + collect_submodules("ui.worker")
)

datas = []
for folder, dest in (
    ("config", "config"),
    ("resources", "resources"),
    ("migrations", "migrations"),
):
    src = ROOT / folder
    if src.is_dir():
        datas.append((str(src), dest))

alembic_ini = ROOT / "alembic.ini"
if alembic_ini.is_file():
    datas.append((str(alembic_ini), "."))

a = Analysis(
    [str(ROOT / "app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "sqlalchemy.dialects.sqlite",
        "sqlalchemy.sql.default_comparator",
        "bcrypt",
        "cv2",
        "pandas",
        "openpyxl",
        "PIL",
        "PIL.Image",
        "docx",
        "reportlab",
        "alembic",
        "jinja2",
        *_hidden_ui_dynamic,
    ],
    hookspath=[str(ROOT / "pyinstaller_hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Hipatia",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Hipatia",
)
