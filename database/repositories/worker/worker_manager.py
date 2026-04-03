# database/repositories/worker/worker_manager.py
"""
Capa de datos (`worker_manager`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from typing import List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ...models import Trabajador
from core.dtos import WorkerDTO, WorkerDetailDTO
from ..base import BaseRepository


class WorkerCoreManager(BaseRepository):
    """
    Gestor DAO para la gestión de datos básicos de trabajadores.
    """

    def get_all_workers(self, include_inactive: bool = False) -> List[WorkerDTO]:
        """Obtiene una lista de todos los trabajadores."""
        def _operation(session: Session) -> List[WorkerDTO]:
            query = session.query(Trabajador)
            if not include_inactive:
                query = query.filter(Trabajador.activo == True)

            trabajadores = query.order_by(Trabajador.nombre_completo).all()
            return [
                WorkerDTO(
                    id=int(t.id or 0),
                    nombre_completo=t.nombre_completo or "",
                    activo=bool(t.activo),
                    notas=t.notas or "",
                    tipo_trabajador=t.tipo_trabajador or 1
                ) for t in trabajadores
            ]

        return self.safe_execute(_operation) or []

    def get_latest_workers(self, limit: int = 10) -> List[WorkerDTO]:
        """Obtiene los últimos trabajadores añadidos."""
        def _operation(session: Session) -> List[WorkerDTO]:
            trabajadores = session.query(Trabajador).order_by(Trabajador.id.desc()).limit(limit).all()
            return [
                WorkerDTO(
                    id=int(t.id or 0),
                    nombre_completo=t.nombre_completo or "",
                    activo=bool(t.activo),
                    notas=t.notas or "",
                    tipo_trabajador=t.tipo_trabajador or 1
                ) for t in trabajadores
            ]

        return self.safe_execute(_operation) or []

    def get_worker_details(self, worker_id: int) -> Optional[WorkerDetailDTO]:
        """Obtiene los detalles de un trabajador específico por su ID."""
        def _operation(session: Session) -> Optional[WorkerDetailDTO]:
            trabajador = session.query(Trabajador).filter_by(id=worker_id).first()
            if not trabajador:
                return None

            return WorkerDetailDTO(
                id=int(trabajador.id or 0),
                nombre_completo=trabajador.nombre_completo or "",
                activo=bool(trabajador.activo),
                notas=trabajador.notas or "",
                tipo_trabajador=trabajador.tipo_trabajador or 1,
                username=trabajador.username,
                role=trabajador.role
            )

        return self.safe_execute(_operation)

    def add_worker(self, nombre_completo: str, notas: str = "", tipo_trabajador: int = 1, activo: bool = True,
                    worker_id: Optional[int] = None, username: Optional[str] = None,
                    password_hash: Optional[str] = None, role: Optional[str] = None) -> Union[bool, str]:
        """Añade un nuevo trabajador o actualiza uno existente."""
        def _operation(session: Session) -> Union[bool, str]:
            target_worker = None
            if worker_id is not None:
                target_worker = session.query(Trabajador).filter_by(id=worker_id).first()

            if target_worker is None:
                target_worker = session.query(Trabajador).filter_by(nombre_completo=nombre_completo).first()

            if target_worker:
                if worker_id is None or target_worker.id == worker_id:
                    target_worker.nombre_completo = nombre_completo
                    target_worker.notas = notas
                    target_worker.tipo_trabajador = tipo_trabajador
                    target_worker.activo = activo
                    if username is not None: target_worker.username = username
                    if password_hash is not None: target_worker.password_hash = password_hash
                    if role is not None: target_worker.role = role
                    return True
                else:
                    return False
            else:
                try:
                    nuevo_trabajador = Trabajador(
                        nombre_completo=nombre_completo,
                        notas=notas,
                        tipo_trabajador=tipo_trabajador,
                        activo=activo,
                        username=username,
                        password_hash=password_hash,
                        role=role
                    )
                    session.add(nuevo_trabajador)
                    session.flush()
                    return True
                except IntegrityError:
                    session.rollback()
                    return "UNIQUE_CONSTRAINT"

        result = self.safe_execute(_operation)
        return result if isinstance(result, str) else (result or False)

    def update_worker(self, worker_id: int, nombre_completo: str, activo: bool, notas: str,
                       tipo_trabajador: int) -> bool:
        """Actualiza los datos de un trabajador existente."""
        def _operation(session: Session) -> bool:
            trabajador = session.query(Trabajador).filter_by(id=worker_id).first()
            if not trabajador:
                return False

            trabajador.nombre_completo = nombre_completo
            trabajador.activo = activo
            trabajador.notas = notas
            trabajador.tipo_trabajador = tipo_trabajador
            return True

        return self.safe_execute(_operation) or False

    def delete_worker(self, worker_id: int) -> bool:
        """Elimina un trabajador de la base de datos."""
        def _operation(session: Session) -> bool:
            trabajador = session.query(Trabajador).filter_by(id=worker_id).first()
            if not trabajador:
                return False

            session.delete(trabajador)
            return True

        return self.safe_execute(_operation) or False
