"""Modelos ORM de seguridad y auditoria.

Este modulo define las tablas de configuracion global y de seguridad
operativa del sistema:
- `Configuration`: clave/valor de ajustes persistentes.
- `LoginAttempt`: historial de intentos de autenticacion para rate limiting.
- `AuditLog`: trazabilidad de acciones sensibles (RBAC/auditoria).
"""

from sqlalchemy import Integer, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from .base import Base
from datetime import datetime, timezone

class Configuration(Base):
    """Par clave/valor para configuraciones persistentes del sistema."""

    __tablename__ = 'configuracion'

    clave: Mapped[str] = mapped_column(String, primary_key=True)
    valor: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self) -> str:
        return f"<Configuration(clave='{self.clave}', valor='{self.valor[:50]}...')>"

class LoginAttempt(Base):
    """Intento de autenticacion utilizado por la politica de rate limiting."""

    __tablename__ = 'login_attempts'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    blocked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<LoginAttempt(id={self.id}, username='{self.username}', success={self.success})>"

class AuditLog(Base):
    """Registro auditable de acciones de seguridad y administracion."""

    __tablename__ = 'audit_log'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('trabajadores.id'), nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, username='{self.username}', action='{self.action}')>"
