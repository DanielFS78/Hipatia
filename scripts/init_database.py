# -*- coding: utf-8 -*-
"""
Script ejecutable (`init_database`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""
from __future__ import annotations

import sys
import os
import logging

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager
from database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database() -> bool:
    """Inicializa la base de datos creando todas las tablas."""
    logger.info("=" * 70)
    logger.info("Inicializando base de datos...")
    logger.info("=" * 70)
    
    try:
        db = DatabaseManager()
        if not db.engine:
            logger.error("No se pudo conectar a la base de datos")
            return False
        
        # Crear todas las tablas
        logger.info("Creando tablas desde modelos SQLAlchemy...")
        Base.metadata.create_all(bind=db.engine)
        logger.info("✓ Tablas creadas exitosamente")
        
        # Ejecutar migraciones de Alembic
        logger.info("\nAplicando migraciones de Alembic...")
        logger.info("Ejecutando: alembic upgrade head")
        result = os.system("alembic upgrade head")
        
        if result == 0:
            logger.info("✓ Migraciones aplicadas exitosamente")
        else:
            logger.warning("⚠ Hubo un problema al ejecutar las migraciones de Alembic")
            logger.info("  Puedes ejecutar manualmente: alembic upgrade head")
        
        logger.info("\n" + "=" * 70)
        logger.info("Inicialización completa")
        logger.info("=" * 70)
        return True
        
    except Exception as e:
        logger.error(f"Error durante la inicialización: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
