# -*- coding: utf-8 -*-
# =================================================================================
# GESTOR DE LA BASE DE DATOS (database_manager.py)
# =================================================================================
# Este módulo se encarga de la interacción con la base de datos usando SQLAlchemy.
# Se ha eliminado el soporte histórico para SQLite directo y migraciones manuales
# en favor de Alembic y SQLAlchemy puro.
# =================================================================================

"""
Nombre del Módulo: database.database_manager

Descripción: Define protocolos o tipos principales: ``DatabaseManager``. Gestiona todas las operaciones de la base de datos para la aplicación. Integración típica con: ``__future__``, ``types``, ``sqlalchemy``, ``models``, ``config``, ``repositories``.
"""
from __future__ import annotations

import logging
from types import TracebackType
from typing import Any, Callable, Dict, Optional

# --- IMPORTS DE SQLALCHEMY ---
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, close_all_sessions, sessionmaker
from .models import Base
from .config import DatabaseConfig

# --- REPOSITORIOS ---
from .repositories import (ProductRepository, WorkerRepository, MachineRepository,
                           PilaRepository, LoteRepository, ConfigurationRepository,
                           MaterialRepository, PreprocesoRepository,
                           IterationRepository, TrackingRepository, ReportsRepository)
from core.dtos import IterationImageDTO, DatabaseComparisonDTO

class DatabaseManager:
    """
    Gestiona todas las operaciones de la base de datos para la aplicación
    utilizando SQLAlchemy.
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        engine: Optional[Engine | Connection] = None,
    ) -> None:
        """
        Inicializa el gestor y configura el motor de SQLAlchemy.
        
        Args:
            db_url (str, optional): URL de conexión.
            engine (Engine, optional): Motor SQLAlchemy pre-configurado (útil para tests).
        """
        self.logger = logging.getLogger("EvolucionTiemposApp")
        
        # Obtener URL de configuración si no se pasa explícitamente
        self.db_url = db_url or DatabaseConfig.get_db_url()
        self.echo_sql = DatabaseConfig.get_echo_sql()
        
        self.engine = engine
        self.SessionLocal: Callable[[], Session] | None = None
        
        try:
            # --- CONFIGURACIÓN DE SQLALCHEMY ---
            if not self.engine:
                connect_args: Dict[str, Any] = {}
                self.engine = create_engine(
                    self.db_url, 
                    echo=self.echo_sql,
                    connect_args=connect_args
                )

            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self.logger.info(f"Motor SQLAlchemy configurado para: {self.db_url.split('@')[-1] if '@' in self.db_url else 'SQLite Local'}")

            # --- ADVERTENCIA SOBRE SQLite THREADING ---
            if self.db_url.startswith("sqlite"):
                self.logger.warning(
                    "ADVERTENCIA: SQLite en modo multi-thread (check_same_thread=False). "
                    "Esto es necesario para PyQt6, pero SQLite NO es thread-safe para escrituras concurrentes. "
                    "Evitar operaciones de escritura simultáneas desde múltiples threads. "
                    "Para producción con múltiples usuarios, usar PostgreSQL."
                )

            # --- INICIALIZACIÓN DE TABLAS (DEPRECADO) ---
            # NOTA: En producción, usar EXCLUSIVAMENTE Alembic para gestión de esquema.
            # create_all() solo debe usarse en desarrollo inicial o via script dedicado.
            # Descomentar la siguiente línea SOLO para desarrollo local sin migraciones:
            self._create_tables_if_not_exist()
            # Para inicialización correcta, usar: python scripts/init_database.py

            # --- INICIALIZACIÓN DE REPOSITORIOS ---
            self._init_repositories()

        except Exception as e:
            self.logger.critical(f"CRITICAL: Error general en la inicialización de DatabaseManager: {e}")
            self.engine = None
            self.SessionLocal = None

    def _create_tables_if_not_exist(self) -> None:
        """Crea las tablas definidas en los modelos si no existen."""
        try:
            if self.engine:
                Base.metadata.create_all(bind=self.engine)
                self.logger.info("Verificación de tablas completada.")
            else:
                self.logger.error("Engine no inicializado, no se pueden crear tablas.")
        except Exception as e:
            self.logger.error(f"Error creando tablas: {e}")

    def _init_repositories(self) -> None:
        """Inicializa los repositorios con la fábrica de sesiones."""
        if not self.SessionLocal:
            return

        self.product_repo = ProductRepository(self.SessionLocal)
        self.worker_repo = WorkerRepository(self.SessionLocal)
        self.machine_repo = MachineRepository(self.SessionLocal)
        self.pila_repo = PilaRepository(self.SessionLocal)
        self.lote_repo = LoteRepository(self.SessionLocal)
        self.preproceso_repo = PreprocesoRepository(self.SessionLocal)
        self.config_repo = ConfigurationRepository(self.SessionLocal)
        self.material_repo = MaterialRepository(self.SessionLocal)
        self.iteration_repo = IterationRepository(self.SessionLocal)
        self.tracking_repo = TrackingRepository(self.SessionLocal)
        self.reports_repo = ReportsRepository(self.SessionLocal)

    def close(self) -> None:
        """Cierra todas las conexiones a la base de datos."""
        if self.SessionLocal:
            close_all_sessions()

        eng = self.engine
        if eng:
            if isinstance(eng, Engine):
                eng.dispose()
            else:
                eng.close()
            self.engine = None

        self.logger.info("Conexiones a base de datos cerradas.")

    def get_session(self) -> Session:
        """Devuelve una nueva sesión de SQLAlchemy."""
        if not self.SessionLocal:
            self.logger.error("SessionLocal no está inicializado. No se puede crear sesión.")
            raise Exception("Base de datos no inicializada")
        return self.SessionLocal()

    def __enter__(self) -> DatabaseManager:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def get_iteration_images(self, iteration_id: int) -> list[IterationImageDTO]:
        return self.iteration_repo.get_images(iteration_id)

    def update_iteration_file_path(self, iteration_id: int, key: str, final_path: str) -> bool:
        return self.iteration_repo.update_iteration_file_path(iteration_id, key, final_path)

    def get_products_by_fabricacion(self, fabricacion_id: int) -> list[Any]:
        return self.product_repo.get_products_by_fabricacion(fabricacion_id)

    def get_products_for_fabricacion(self, fabricacion_id: int) -> list[Any]:
        return self.preproceso_repo.get_products_for_fabricacion(fabricacion_id)

    def add_worker(self, *args: Any, **kwargs: Any) -> Any:
        return self.worker_repo.add_worker(*args, **kwargs)

    def get_all_preprocesos_with_components(self) -> list[Any]:
        return self.preproceso_repo.get_all_preprocesos_with_components()

    def get_all_workers(self, *args: Any, **kwargs: Any) -> Any:
        return self.worker_repo.get_all_workers(*args, **kwargs)

    def add_machine(self, *args: Any, **kwargs: Any) -> Any:
        return self.machine_repo.add_machine(*args, **kwargs)

    def get_distinct_machine_processes(self) -> list[str]:
        return self.machine_repo.get_distinct_machine_processes()

    def get_machines_by_process_type(self, process_type: str) -> list[Any]:
        return self.machine_repo.get_machines_by_process_type(process_type)

    def add_machine_maintenance(self, *args: Any, **kwargs: Any) -> Any:
        return self.machine_repo.add_machine_maintenance(*args, **kwargs)

    def get_machine_history(self, machine_id: int) -> dict[str, Any]:
        return self.machine_repo.get_machine_history(machine_id)

    @property
    def db_path(self) -> str:
        """
        Devuelve la ruta al archivo de base de datos (solo para SQLite).
        Extrado de db_url.
        """
        if self.db_url.startswith("sqlite:///"):
            return self.db_url.replace("sqlite:///", "")
        return ""

    # --- MÉTODOS DE UTILIDAD MIGRADOS A REPOSITORIOS O ELIMINADOS ---
    # Los métodos de migración (_migrate_to_vN) han sido eliminados.
    # La responsabilidad de las migraciones recae ahora en Alembic.

    # --- SYNC METHODS (USB/Sneakernet workflow) ---
    def compare_with_db(self, foreign_db_path: str) -> DatabaseComparisonDTO:
        """
        Compare local database with a foreign SQLite database file.
        
        Args:
            foreign_db_path: Path to the foreign .db file (from USB)
            
        Returns:
            DatabaseComparisonDTO containing differences per table
        """
        from core.sync_service import SyncService
        if not self.SessionLocal:
            raise ValueError("SessionLocal no inicializado")
        sync_service = SyncService(self.SessionLocal)
        return sync_service.compare_databases(foreign_db_path)

    def apply_sync_changes(self, comparison: DatabaseComparisonDTO) -> int:
        """
        Apply selected changes from a sync operation.
        
        Args:
            comparison: DatabaseComparisonDTO with changes to apply
            
        Returns:
            Number of records successfully applied
        """
        from core.sync_service import SyncService
        if not self.SessionLocal:
            raise ValueError("SessionLocal no inicializado")
        sync_service = SyncService(self.SessionLocal)
        return sync_service.apply_changes(comparison)
