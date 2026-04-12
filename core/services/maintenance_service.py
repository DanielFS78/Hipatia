# -*- coding: utf-8 -*-
"""
Nombre del Módulo: maintenance_service
Descripción: Mantenimiento programado en segundo plano: limpieza de intentos de login,
             retención de auditoría, copias de seguridad y rotación de ficheros antiguos.

``MaintenanceService`` encola un ``MaintenanceWorker`` en el ``QThreadPool`` global.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from PyQt6.QtCore import QObject, QRunnable, QThreadPool

if TYPE_CHECKING:
    from core.services.rate_limiter import RateLimiter
    from core.services.audit_logger import AuditLogger
    from core.services.backup_service import BackupService

class MaintenanceWorker(QRunnable):
    """Worker para ejecutar tareas de mantenimiento en segundo plano."""

    def __init__(self, service: MaintenanceService) -> None:
        super().__init__()
        self.service = service

    def run(self) -> None:
        self.service.perform_maintenance()


class MaintenanceService(QObject):
    """
    Servicio que orquesta tareas de mantenimiento:
    - Limpieza de intentos de login antiguos.
    - Limpieza de logs de auditoría antiguos.
    - Creación de backups automatizados.
    - Rotación de backups antiguos.
    """
    
    def __init__(self, rate_limiter: RateLimiter, audit_logger: AuditLogger, 
                 backup_service: BackupService | None = None):
        super().__init__()
        self.rate_limiter = rate_limiter
        self.audit_logger = audit_logger
        self.backup_service = backup_service
        self.logger = logging.getLogger("MaintenanceService")
        self.thread_pool = QThreadPool.globalInstance()

    def run_background_maintenance(self) -> None:
        """Inicia el mantenimiento en un hilo separado."""
        self.logger.info("Iniciando tarea de mantenimiento en segundo plano...")
        worker = MaintenanceWorker(self)
        if self.thread_pool is not None:
            self.thread_pool.start(worker)

    def perform_maintenance(self) -> None:
        """Ejecuta las tareas de mantenimiento secuencialmente."""
        try:
            self.logger.info(">>> EJECUTANDO MANTENIMIENTO PROGRAMADO <<<")
            
            # 1. Limpiar intentos de login (> 24 horas)
            self.rate_limiter.cleanup_old_attempts()
            
            # 2. Limpiar logs de auditoría (> 365 días por defecto)
            self.audit_logger.cleanup_old_logs(retention_days=365)
            
            # 3. Crear backup diario (si está configurado)
            if self.backup_service:
                success, message = self.backup_service.create_backup()
                if success:
                    self.logger.info(f"Backup creado: {message}")
                else:
                    self.logger.warning(f"Error en backup: {message}")
                
                # 4. Limpiar backups antiguos
                deleted = self.backup_service.cleanup_old_backups()
                if deleted > 0:
                    self.logger.info(f"Backups antiguos eliminados: {deleted}")
            
            self.logger.info(">>> MANTENIMIENTO COMPLETADO EXITOSAMENTE <<<")
            
        except Exception as e:
            self.logger.error(f"Error durante el mantenimiento: {e}", exc_info=True)
