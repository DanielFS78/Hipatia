"""
========================================================================
SCRIPT DE BACKUP - BASE DE DATOS
========================================================================
Este script crea una copia de seguridad de tu base de datos ANTES de
realizar cualquier modificación al esquema.

IMPORTANTE: Ejecuta este script ANTES de añadir los nuevos modelos.
========================================================================
"""

import os
import shutil
from datetime import datetime

def create_backup(db_path="montaje.db"):
    """
    Crea una copia de seguridad de la base de datos.
    
    Args:
        db_path: Ruta a la base de datos (por defecto montaje.db)
    """
    if not os.path.exists(db_path):
        print(f"❌ ERROR: No se encuentra la base de datos: {db_path}")
        return False
    
    # Crear carpeta de backups si no existe
    backup_dir = "database_backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"✅ Carpeta de backups creada: {backup_dir}/")
    
    # Generar nombre de backup con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = os.path.basename(db_path)
    backup_name = f"{db_name}.backup_{timestamp}"
    backup_path = os.path.join(backup_dir, backup_name)
    
    try:
        # Copiar base de datos
        shutil.copy2(db_path, backup_path)
        
        # Verificar que se copió correctamente
        original_size = os.path.getsize(db_path)
        backup_size = os.path.getsize(backup_path)
        
        if original_size == backup_size:
            print(f"\n{'='*70}")
            print(f"✅ BACKUP CREADO EXITOSAMENTE")
            print(f"{'='*70}")
            print(f"📁 Archivo original: {db_path}")
            print(f"💾 Backup guardado: {backup_path}")
            print(f"📊 Tamaño: {original_size:,} bytes")
            print(f"🕐 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}\n")
            return True
        else:
            print(f"❌ ERROR: El backup no coincide con el original")
            print(f"   Original: {original_size} bytes")
            print(f"   Backup: {backup_size} bytes")
            return False
            
    except Exception as e:
        print(f"❌ ERROR al crear backup: {e}")
        return False

def backup_all_databases():
    """Crea backup de todas las bases de datos del proyecto."""
    databases = ["montaje.db", "pilas.db"]
    
    print("\n" + "="*70)
    print("BACKUP DE BASES DE DATOS - SISTEMA DE TRAZABILIDAD")
    print("="*70 + "\n")
    
    success_count = 0
    for db in databases:
        if os.path.exists(db):
            print(f"🔄 Creando backup de {db}...")
            if create_backup(db):
                success_count += 1
        else:
            print(f"⚠️  {db} no encontrada, omitiendo...")
    
    print("\n" + "="*70)
    if success_count == len([db for db in databases if os.path.exists(db)]):
        print("✅ TODOS LOS BACKUPS COMPLETADOS EXITOSAMENTE")
    else:
        print("⚠️  ALGUNOS BACKUPS FALLARON - REVISAR ERRORES ARRIBA")
    print("="*70 + "\n")
    
    print("📝 SIGUIENTE PASO:")
    print("   Ahora puedes proceder a modificar models.py con seguridad.")
    print("   Si algo sale mal, restaura desde database_backups/")
    print()

if __name__ == "__main__":
    backup_all_databases()
    input("\nPresiona Enter para salir...")
