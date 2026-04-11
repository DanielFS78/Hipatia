# -*- coding: utf-8 -*-
"""
Nombre del Módulo: rate_limiter
Descripción: Limita intentos de inicio de sesión fallidos (bloqueo temporal y limpieza de históricos).

Registra cada intento en base de datos y bloquea el usuario unos minutos tras superar el umbral.
"""

from datetime import datetime, timedelta
from typing import Callable, Optional
from sqlalchemy.orm import Session
from database.models import LoginAttempt
import logging


class RateLimiter:
    """Gestiona el rate limiting para intentos de login."""
    
    MAX_ATTEMPTS = 3
    LOCKOUT_DURATION = timedelta(minutes=5)
    CLEANUP_WINDOW = timedelta(hours=24)
    
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory
        self.logger = logging.getLogger("RateLimiter")
    
    def check_and_record_attempt(self, username: str, success: bool, 
                                   ip_address: Optional[str] = None) -> bool:
        """
        Verifica si el usuario puede intentar login y registra el intento.
        
        Args:
            username: Nombre de usuario
            success: Si el intento fue exitoso
            ip_address: Dirección IP del intento (opcional)
            
        Returns:
            True si el intento está permitido, False si está bloqueado
        """
        session = self.session_factory()
        try:
            # Verificar si el usuario está bloqueado
            now = datetime.now()
            active_block = session.query(LoginAttempt).filter(
                LoginAttempt.username == username,
                LoginAttempt.blocked_until.isnot(None),
                LoginAttempt.blocked_until > now
            ).first()
            
            if active_block:
                self.logger.warning(f"Usuario '{username}' bloqueado hasta {active_block.blocked_until}")
                return False
            
            # Contar intentos fallidos recientes
            recent_failures = session.query(LoginAttempt).filter(
                LoginAttempt.username == username,
                LoginAttempt.success == False,
                LoginAttempt.timestamp > now - timedelta(minutes=15)
            ).count()
            
            # Registrar el intento actual
            attempt = LoginAttempt(
                username=username,
                ip_address=ip_address,
                success=success,
                timestamp=now
            )
            
            # Si alcanzó el máximo de intentos, aplicar bloqueo
            if recent_failures >= self.MAX_ATTEMPTS - 1 and not success:
                attempt.blocked_until = now + self.LOCKOUT_DURATION
                self.logger.warning(
                    f"Usuario '{username}' bloqueado por {self.LOCKOUT_DURATION.total_seconds()/60} minutos "
                    f"tras {recent_failures + 1} intentos fallidos"
                )
            
            session.add(attempt)
            session.commit()
            
            # Si el login fue exitoso, limpiar bloqueos previos
            if success:
                session.query(LoginAttempt).filter(
                    LoginAttempt.username == username,
                    LoginAttempt.blocked_until.isnot(None)
                ).update({"blocked_until": None})
                session.commit()
            
            return recent_failures < self.MAX_ATTEMPTS
            
        except Exception as e:
            self.logger.error(f"Error en rate limiter: {e}")
            session.rollback()
            # En caso de error, permitir el intento (fail-open solo para rate limiting)
            return True
        finally:
            session.close()
    
    def is_blocked(self, username: str) -> bool:
        """
        Verifica si un usuario está bloqueado sin registrar un intento.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            True si el usuario está bloqueado
        """
        session = self.session_factory()
        try:
            now = datetime.now()
            active_block = session.query(LoginAttempt).filter(
                LoginAttempt.username == username,
                LoginAttempt.blocked_until.isnot(None),
                LoginAttempt.blocked_until > now
            ).first()
            
            return active_block is not None
        finally:
            session.close()
    
    def cleanup_old_attempts(self) -> None:
        """Elimina registros antiguos para mantener la tabla limpia."""
        session = self.session_factory()
        try:
            cutoff = datetime.now() - self.CLEANUP_WINDOW
            deleted = session.query(LoginAttempt).filter(
                LoginAttempt.timestamp < cutoff
            ).delete()
            session.commit()
            
            if deleted > 0:
                self.logger.info(f"Limpieza: {deleted} intentos de login antiguos eliminados")
        except Exception as e:
            self.logger.error(f"Error en limpieza de intentos: {e}")
            session.rollback()
        finally:
            session.close()
