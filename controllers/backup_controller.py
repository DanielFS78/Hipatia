# -*- coding: utf-8 -*-
"""
Nombre del Módulo: backup_controller
Descripción: Gestiona las operaciones de copia de seguridad (backup), restauración, 
             exportación e importación de la base de datos y logs del sistema.
"""
from __future__ import annotations

import os
import shutil
import sys
import zipfile
import logging
from typing import Any, Callable, Protocol
from datetime import datetime
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QFileDialog, QApplication, QDialog

from core.utils.helpers import resource_path
from core.security.access_control import require_permission
from core.security.security_service import Permission
from core.services.backup_service import BackupService
from core.services.audit_logger import AuditLogger
from database.database_manager import DatabaseManager
from controllers.backup_controller_io_manager import BackupIOManager
from controllers.ui_class_loader import ui_class


class IBackupControllerDatabase(Protocol):
    """Contrato mínimo de BD para backup/sync (incluye dobles de test ligeros)."""

    db_url: Any

    @property
    def db_path(self) -> str: ...

    def close(self) -> None: ...

    def compare_with_db(self, foreign_db_path: str) -> Any: ...

    def apply_sync_changes(self, selected_changes: Any) -> int: ...


class BackupController(QObject):
    """
    Controlador encargado de la gestión de copias de seguridad.

    Centraliza la lógica para crear backups estructurados por fecha, importar datos
    desde paquetes ZIP, exportar la BD actual y sincronizar cambios entre diferentes
    archivos de base de datos SQLite.
    """

    def __init__(
        self,
        db: DatabaseManager | IBackupControllerDatabase,
        view: Any,
        logger: logging.Logger,
        backup_service: BackupService | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        """
        Inicializa el controlador de backups.

        Args:
            db: Instancia del gestor de base de datos.
            view: Referencia a la vista principal para diálogos y mensajes.
            logger: Instancia para el registro de eventos técnicos.
            backup_service: Servicio especializado en lógica de backup (opcional).
            audit_logger: Servicio de auditoría para registrar acciones de usuario (opcional).
        """
        super().__init__()
        self.db: DatabaseManager | IBackupControllerDatabase = db
        self.view: Any = view
        self.logger: logging.Logger = logger
        self.backup_service: BackupService | None = backup_service
        self.audit_logger: AuditLogger | None = audit_logger
        self._db_io = BackupIOManager(self)

    @require_permission(Permission.MANAGE_SETTINGS)
    def on_import_databases(self, on_success_callback: Callable[[], None] | None = None) -> None:
        self._db_io.on_import_databases(on_success_callback)

    @require_permission(Permission.MANAGE_SETTINGS)
    def on_export_databases(self) -> None:
        self._db_io.on_export_databases()

    @require_permission(Permission.MANAGE_SETTINGS)
    def on_sync_databases(self, on_success_callback: Callable[[], None] | None = None) -> None:
        self._db_io.on_sync_databases(on_success_callback)

    @require_permission(Permission.MANAGE_SETTINGS)
    def show_backup_restore_dialog(self) -> None:
        """Muestra el diálogo de gestión de backups."""
        if not self.backup_service:
            self.logger.error("BackupService no inicializado.")
            return

        BackupRestoreDialog = ui_class("ui.dialogs.backup_restore_dialog", "BackupRestoreDialog")
        dialog = BackupRestoreDialog(self.backup_service, self.view, self.audit_logger)
        dialog.exec()

    def _get_db_path(self) -> str:
        """Extract SQLite file path from db_url. Returns empty string for non-SQLite DBs."""
        db_url = self.db.db_url
        if db_url and str(db_url).startswith("sqlite:///"):
            return str(db_url).replace("sqlite:///", "")
        return ""

    def _create_backup_directory_structure(self) -> tuple[str | None, str | None]:
        """Crea la estructura de carpetas para backups organizados por fecha y hora."""
        try:
            # Obtener directorio base donde está el ejecutable
            base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            backup_main_dir = os.path.join(base_dir, "Backup")

            # Crear carpeta principal Backup si no existe
            os.makedirs(backup_main_dir, exist_ok=True)

            # Crear subcarpetas principales
            db_backup_dir = os.path.join(backup_main_dir, "Base de datos")
            log_backup_dir = os.path.join(backup_main_dir, "Registro de errores")
            os.makedirs(db_backup_dir, exist_ok=True)
            os.makedirs(log_backup_dir, exist_ok=True)

            # Obtener fecha y hora actual
            now = datetime.now()
            date_folder = now.strftime("%Y-%m-%d")
            time_folder = now.strftime("%H-%M")

            # Crear carpetas de fecha y hora para base de datos
            db_date_dir = os.path.join(db_backup_dir, date_folder)
            db_final_dir = os.path.join(db_date_dir, time_folder)
            os.makedirs(db_final_dir, exist_ok=True)

            # Crear carpetas de fecha y hora para logs
            log_date_dir = os.path.join(log_backup_dir, date_folder)
            log_final_dir = os.path.join(log_date_dir, time_folder)
            os.makedirs(log_final_dir, exist_ok=True)

            self.logger.info(f"Estructura de backup creada: DB={db_final_dir}, LOG={log_final_dir}")
            return db_final_dir, log_final_dir

        except Exception as e:
            self.logger.error(f"Error al crear estructura de directorios de backup: {e}")
            return None, None

    def _backup_and_clean_log(self, log_backup_dir: str) -> bool:
        """Realiza backup del log de errores y lo limpia."""
        try:
            log_file_path = os.path.join("logs", "EvolucionTiempos.log")

            if os.path.exists(log_file_path):
                # Copiar el log al directorio de backup
                log_backup_path = os.path.join(log_backup_dir, "EvolucionTiempos.log")
                shutil.copy2(log_file_path, log_backup_path)
                self.logger.info(f"Log copiado a: {log_backup_path}")

                # Limpiar el archivo de log original
                with open(log_file_path, 'w', encoding='utf-8') as f:
                    f.write("")  # Vaciar el archivo

                self.logger.info("Archivo de log limpiado después del backup.")
                return True
            else:
                self.logger.warning(f"Archivo de log no encontrado: {log_file_path}")
                return False

        except Exception as e:
            self.logger.error(f"Error en backup/limpieza del log: {e}")
            return False

    def create_automatic_backup(self) -> bool:
        """
        Realiza una copia de seguridad automática completa.
        Crea una estructura organizada por fecha y hora, copia la base de datos 
        y realiza la rotación/limpieza de los logs de errores.

        Returns:
            True si el proceso se completó con éxito, False en caso contrario.
        """
        self.logger.info("Iniciando proceso de copia de seguridad automática mejorada...")

        try:
            db_backup_dir, log_backup_dir = self._create_backup_directory_structure()
            if not db_backup_dir or not log_backup_dir:
                self.logger.error("No se pudo crear la estructura de directorios de backup")
                return False

            # 1. Backup de la base de datos principal
            db_backup_success = False
            main_db_path = self._get_db_path()
            if main_db_path and os.path.exists(main_db_path):
                destination_path = os.path.join(db_backup_dir, os.path.basename(main_db_path))
                shutil.copy2(main_db_path, destination_path)
                self.logger.info(f"BD principal copiada a: {destination_path}")
                db_backup_success = True
            elif not main_db_path:
                self.logger.warning("Base de datos no es SQLite, omitiendo backup de archivo.")
                db_backup_success = True  # Not a failure for non-SQLite
            else:
                self.logger.warning(f"Archivo de BD principal no encontrado: {main_db_path}")

            # 2. Backup del log de errores
            log_backup_success = self._backup_and_clean_log(log_backup_dir)

            if db_backup_success and log_backup_success:
                self.logger.info("Copia de seguridad automática completada con éxito.")
                # Audit log for automatic backup (optional, usually too verbose if every time)
                # But requested by user? "Audit system... and others". 
                # Let's log it if we have audit logger.
                if self.audit_logger:
                    self.audit_logger.log(
                        username="SYSTEM",
                        action="BACKUP_AUTO",
                        description="Copia de seguridad automática completada",
                        success=True
                    )
                return True
            else:
                self.logger.warning("Copia de seguridad completada con algunos errores.")
                if self.audit_logger:
                    self.audit_logger.log(
                        username="SYSTEM",
                        action="BACKUP_AUTO",
                        description="Copia de seguridad completada con advertencias",
                        success=False
                    )
                return False

        except Exception as e:
            self.logger.critical(f"FALLO CRÍTICO en la copia de seguridad automática: {e}", exc_info=True)
            if self.audit_logger:
                    self.audit_logger.log(
                        username="SYSTEM",
                        action="BACKUP_AUTO",
                        description=f"Fallo crítico: {str(e)}",
                        success=False,
                        error_message=str(e)
                    )
            return False

