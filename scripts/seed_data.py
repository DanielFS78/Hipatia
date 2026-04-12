# -*- coding: utf-8 -*-
"""
Nombre del Módulo: scripts.seed_data

Descripción: Script ejecutable (`seed_data`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""
from __future__ import annotations

import sys
import os
import logging
from datetime import datetime
import random
from typing import List, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database_manager import DatabaseManager
from database.config import DatabaseConfig
from database.models import (
    Producto, Trabajador, Fabricacion, TrabajoLog, 
    IncidenciaLog, Preproceso, Subfabricacion,
    fabricacion_productos, trabajador_fabricacion_link
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Seeder")

def seed_data() -> None:
    """Inserta datos de prueba en la base de datos."""
    db_url = DatabaseConfig.get_db_url()
    logger.info(f"Connecting to {db_url}")
    db_manager = DatabaseManager(db_url)
    session = db_manager.get_session()
    
    try:
        # Check if data exists
        if session.query(Producto).count() > 0:
            logger.info("Database already contains data. Skipping seed.")
            return

        logger.info("Seeding data...")

        # 1. Create Workers
        workers: List[Trabajador] = []
        for i in range(5):
            w = Trabajador(
                nombre_completo=f"Trabajador {i+1}",
                activo=True,
                tipo_trabajador=1
            )
            session.add(w)
            workers.append(w)
        session.flush()

        # 2. Create Products
        products: List[Producto] = []
        for i in range(10):
            p = Producto(
                codigo=f"PROD-{i+1:03d}",
                descripcion=f"Producto de Prueba {i+1}",
                departamento="Montaje",
                tipo_trabajador=1,
                tiene_subfabricaciones=False,
                tiempo_optimo=120.0
            )
            session.add(p)
            products.append(p)
        session.flush()

        # 3. Create Fabrications and logs
        for i in range(20):
            prod = random.choice(products)
            fab = Fabricacion(
                codigo=f"FAB-{i+1:03d}",
                descripcion=f"Fabricación de {prod.codigo}"
            )
            session.add(fab)
            session.flush()
            
            # Link fab to product
            stmt = fabricacion_productos.insert().values(
                fabricacion_id=fab.id,
                producto_codigo=prod.codigo,
                cantidad=random.randint(1, 10)
            )
            session.execute(stmt)

            # Assign workers
            worker = random.choice(workers)
            stmt2 = trabajador_fabricacion_link.insert().values(
                trabajador_id=worker.id,
                fabricacion_id=fab.id,
                fecha_asignacion=datetime.now(),
                estado='activo'
            )
            session.execute(stmt2)

            # Create Logs
            for j in range(3):
                log = TrabajoLog(
                    qr_code=f"QR-{fab.codigo}-{j+1}",
                    trabajador_id=worker.id,
                    fabricacion_id=fab.id,
                    producto_codigo=prod.codigo,
                    orden_fabricacion=f"OF-{random.randint(100, 105)}",
                    tiempo_inicio=datetime.now(),
                    tiempo_fin=datetime.now(),
                    duracion_segundos=random.randint(60, 3600),
                    estado='completado'
                )
                session.add(log)
                
                # Create Incidencia occasionally
                if random.random() < 0.3:
                    inc = IncidenciaLog(
                        trabajador_id=worker.id,
                        trabajo_log=log,
                        tipo_incidencia="Material Defectuoso",
                        descripcion="Prueba de incidencia",
                        fecha_reporte=datetime.now()
                    )
                    session.add(inc)

        session.commit()
        logger.info("Seeding completed successfully!")

    except Exception as e:
        session.rollback()
        logger.error(f"Seeding failed: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_data()
