"""
========================================================================
SCRIPT DE BACKUP - BASE DE DATOS
========================================================================
Este script crea una copia de seguridad de tu base de datos ANTES de
realizar cualquier modificación al esquema.

IMPORTANTE: Ejecuta este script ANTES de añadir los nuevos modelos.
========================================================================
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime

from database.config import DatabaseConfig


def create_backup(db_path: str | None = None) -> bool:
    """
    Crea una copia de seguridad de la base de datos.

    Args:
        db_path: Ruta a la base de datos (por defecto usa la config de entorno)
    """
    resolved_path: str | None = db_path
    if resolved_path is None:
        db_url = DatabaseConfig.get_db_url()
        if db_url.startswith("sqlite:///"):
            resolved_path = db_url.replace("sqlite:///", "")
        else:
            print(f"⚠️  Base de datos no es SQLite, omitiendo backup: {db_url}")
            return False

    if not os.path.exists(resolved_path):
        print(f"❌ ERROR: No se encuentra la base de datos: {resolved_path}")
        return False

    backup_dir = DatabaseConfig.get_backup_dir()
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)
        print(f"✅ Carpeta de backups creada: {backup_dir}/")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = os.path.basename(resolved_path)
    backup_name = f"{db_name}.backup_{timestamp}"
    backup_path = os.path.join(backup_dir, backup_name)

    try:
        shutil.copy2(resolved_path, backup_path)

        original_size = os.path.getsize(resolved_path)
        backup_size = os.path.getsize(backup_path)

        if original_size == backup_size:
            print(f"\n{'=' * 70}")
            print("✅ BACKUP CREADO EXITOSAMENTE")
            print(f"{'=' * 70}")
            print(f"📁 Archivo original: {resolved_path}")
            print(f"💾 Backup guardado: {backup_path}")
            print(f"📊 Tamaño: {original_size:,} bytes")
            print(f"🕐 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'=' * 70}\n")
            return True
        print("❌ ERROR: El backup no coincide con el original")
        print(f"   Original: {original_size} bytes")
        print(f"   Backup: {backup_size} bytes")
        return False

    except OSError as e:
        print(f"❌ ERROR al crear backup: {e}")
        return False


def backup_all_databases() -> None:
    """Crea backup de la base de datos principal configurada."""
    print("\n" + "=" * 70)
    print("BACKUP DE BASES DE DATOS - SISTEMA DE TRAZABILIDAD")
    print("=" * 70 + "\n")

    print("🔄 Creando backup de base de datos principal...")
    success = create_backup()

    print("\n" + "=" * 70)
    if success:
        print("✅ BACKUP COMPLETADO EXITOSAMENTE")
    else:
        print("⚠️  BACKUP FALLÓ - REVISAR ERRORES ARRIBA")
    print("=" * 70 + "\n")

    print("📝 SIGUIENTE PASO:")
    print("   Ahora puedes proceder a modificar models.py con seguridad.")
    print(f"   Si algo sale mal, restaura desde {DatabaseConfig.get_backup_dir()}/")
    print()


if __name__ == "__main__":
    backup_all_databases()
    input("\nPresiona Enter para salir...")
