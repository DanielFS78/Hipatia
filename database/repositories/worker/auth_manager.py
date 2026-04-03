# database/repositories/worker/auth_manager.py
"""
Capa de datos (`auth_manager`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from typing import Optional
from sqlalchemy.orm import Session
from ...models import Trabajador
from core.dtos import AuthResponseDTO
from ..base import BaseRepository


class WorkerAuthManager(BaseRepository):
    """
    Gestor DAO para la gestión de autenticación y credenciales de trabajadores.
    """

    def authenticate_user(self, username: str, password: str) -> Optional[AuthResponseDTO]:
        """Verifica las credenciales de un usuario y devuelve sus datos si son correctas."""
        def _operation(session: Session) -> Optional[AuthResponseDTO]:
            trabajador = session.query(Trabajador).filter(
                Trabajador.username == username,
                Trabajador.activo == True
            ).first()

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

            trabajador.username = username
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
