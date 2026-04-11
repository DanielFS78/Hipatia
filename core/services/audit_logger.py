# -*- coding: utf-8 -*-
"""
Nombre del Módulo: audit_logger
Descripción: Persistencia de acciones sensibles (login, importación, sincronización, etc.)
             en la tabla de auditoría de base de datos para trazabilidad y cumplimiento.
"""

from typing import Callable, Optional
from sqlalchemy.orm import Session
from database.models import AuditLog
import logging


class AuditLogger:
    """Registra acciones sensibles en la base de datos."""
    
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory
        self.logger = logging.getLogger("AuditLogger")
    
    def log(self, username: str, action: str, 
            entity_type: Optional[str] = None,
            entity_id: Optional[int] = None,
            description: Optional[str] = None,
            user_id: Optional[int] = None,
            success: bool = True,
            error_message: Optional[str] = None,
            ip_address: Optional[str] = None) -> None:
        """
        Registra una acción en el log de auditoría.
        
        Args:
            username: Nombre del usuario que realiza la acción
            action: Tipo de acción (LOGIN, DELETE, EXPORT, etc.)
            entity_type: Tipo de entidad afectada (opcional)
            entity_id: ID de la entidad afectada (opcional)
            description: Descripción adicional (opcional)
            user_id: ID del usuario en la BD (opcional)
            success: Si la acción fue exitosa
            error_message: Mensaje de error si falló
            ip_address: Dirección IP (opcional)
        """
        session = None
        try:
            session = self.session_factory()
            entry = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                success=success,
                error_message=error_message,
                ip_address=ip_address
            )
            session.add(entry)
            session.commit()
            
            status = 'SUCCESS' if success else 'FAILED'
            self.logger.info(
                f"AUDIT: {username} - {action} - "
                f"{entity_type or 'N/A'}:{entity_id or 'N/A'} - {status}"
            )
        except Exception as e:
            self.logger.error(f"Error al registrar en audit log: {e}")
            if session:
                session.rollback()
        finally:
            if session:
                session.close()

    
    def log_login(self, username: str, success: bool, user_id: Optional[int] = None,
                  ip_address: Optional[str] = None, error_message: Optional[str] = None) -> None:
        """Registra un intento de login."""
        self.log(
            username=username,
            action='LOGIN',
            user_id=user_id,
            success=success,
            error_message=error_message,
            ip_address=ip_address
        )
    
    def log_logout(self, username: str, user_id: Optional[int] = None) -> None:
        """Registra un logout."""
        self.log(
            username=username,
            action='LOGOUT',
            user_id=user_id
        )
    
    def log_delete(self, username: str, entity_type: str, entity_id: int,
                   description: Optional[str] = None, user_id: Optional[int] = None) -> None:
        """Registra eliminación de entidad."""
        self.log(
            username=username,
            action='DELETE',
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            user_id=user_id
        )
    
    def log_export(self, username: str, description: str, user_id: Optional[int] = None) -> None:
        """Registra exportación de datos."""
        self.log(
            username=username,
            action='EXPORT',
            description=description,
            user_id=user_id
        )
    
    def log_import(self, username: str, description: str, user_id: Optional[int] = None) -> None:
        """Registra importación de datos."""
        self.log(
            username=username,
            action='IMPORT',
            description=description,
            user_id=user_id
        )
    
    def log_settings_change(self, username: str, description: str, user_id: Optional[int] = None) -> None:
        """Registra cambio de configuración."""
        self.log(
            username=username,
            action='SETTINGS_CHANGE',
            description=description,
            user_id=user_id
        )

    def cleanup_old_logs(self, retention_days: int = 365) -> int:
        """
        Elimina registros de auditoría más antiguos que el periodo de retención.
        
        Args:
            retention_days: Número de días a retener los logs.
            
        Returns:
            Número de registros eliminados.
        """
        from datetime import datetime, timedelta
        session = None
        try:
            session = self.session_factory()
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            deleted_count = session.query(AuditLog).filter(
                AuditLog.timestamp < cutoff_date
            ).delete()
            
            session.commit()
            if deleted_count > 0:
                self.logger.info(f"Limpieza de auditoría: {deleted_count} registros eliminados (anteriores a {cutoff_date})")
            return deleted_count
        except Exception as e:
            self.logger.error(f"Error limpiando logs de auditoría: {e}")
            if session:
                session.rollback()
            return 0
        finally:
            if session:
                session.close()
