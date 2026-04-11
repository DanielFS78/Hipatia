# -*- coding: utf-8 -*-
"""
Nombre del Módulo: auth_manager
Descripción: Comprueba usuario y contraseña de operarios frente a la tabla ``trabajadores``.

El nombre de usuario se normaliza (minúsculas, sin espacios al inicio o al final) y
se compara con ``func.lower(Trabajador.username)`` para que el inicio de sesión no
dependa de mayúsculas.
"""

from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from ...models import Trabajador
from core.dtos import AuthResponseDTO
from ..base import BaseRepository


def _normalize_username(username: str | None) -> str:
    """Usuario de login: sin espacios laterales y en minúsculas para comparar con BD."""
    if not username:
        return ""
    return username.strip().lower()


class WorkerAuthManager(BaseRepository):
    """
    Gestor DAO para la gestión de autenticación y credenciales de trabajadores.
    """

    def authenticate_user(self, username: str, password: str) -> Optional[AuthResponseDTO]:
        """
        Verifica usuario y contraseña; devuelve ``AuthResponseDTO`` si el trabajador está activo.

        El nombre de usuario se normaliza (minúsculas, sin espacios laterales)
        antes de consultar la base de datos.
        """
        def _operation(session: Session) -> Optional[AuthResponseDTO]:
            un = _normalize_username(username)
            if not un:
                return None

            trabajador = (
                session.query(Trabajador)
                .filter(
                    Trabajador.activo == True,  # noqa: E712
                    Trabajador.username.isnot(None),
                    func.lower(Trabajador.username) == un,
                )
                .first()
            )

            if not trabajador:
                return None

            from core.security.password_service import PasswordService
            if PasswordService.verify_password(password, trabajador.password_hash or ""):
                return AuthResponseDTO(
                    id=int(trabajador.id or 0),
                    nombre_completo=trabajador.nombre_completo or "",
                    username=trabajador.username or "",
                    role=trabajador.role or "",
                    activo=bool(trabajador.activo)
                )
            
            return None

        return self.safe_execute(_operation)

    def update_user_credentials(self, worker_id: int, username: str, password: str, role: str) -> bool:
        """Actualiza los datos de login de un trabajador."""
        def _operation(session: Session) -> bool:
            trabajador = session.query(Trabajador).filter_by(id=worker_id).first()
            if not trabajador:
                return False

            trabajador.username = _normalize_username(username) or None
            trabajador.role = role

            if password:
                from core.security.password_service import PasswordService
                trabajador.password_hash = PasswordService.hash_password(password)

            return True

        return self.safe_execute(_operation) or False

    def update_user_password(self, worker_id: int, password: str) -> bool:
        """Actualiza únicamente la contraseña de un trabajador."""
        def _operation(session: Session) -> bool:
            trabajador = session.query(Trabajador).filter_by(id=worker_id).first()
            if not trabajador:
                return False

            from core.security.password_service import PasswordService
            trabajador.password_hash = PasswordService.hash_password(password)
            return True

        return self.safe_execute(_operation) or False
