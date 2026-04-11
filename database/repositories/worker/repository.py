# -*- coding: utf-8 -*-
"""
Nombre del Módulo: worker.repository
Descripción: Datos de trabajadores, anotaciones y repositorio compuesto del subpaquete worker.
"""

from typing import List, Optional, Union, Callable
from sqlalchemy.orm import Session
from ..base import BaseRepository
from .worker_manager import WorkerCoreManager
from .auth_manager import WorkerAuthManager
from .annotation_manager import WorkerAnnotationManager
from core.dtos import WorkerDTO, WorkerDetailDTO, AuthResponseDTO, WorkerAnnotationDTO


class WorkerRepository(BaseRepository):
    """
    Repositorio para la gestión de trabajadores.
    Implementa el patrón Fachada delegando en DAO Managers especializados.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        super().__init__(session_factory)
        
        # Composición de gestores
        self.core = WorkerCoreManager(session_factory)
        self.auth = WorkerAuthManager(session_factory)
        self.annotation = WorkerAnnotationManager(session_factory)

    # Delegación: WorkerCoreManager
    def get_all_workers(self, include_inactive: bool = False) -> List[WorkerDTO]:
        return self.core.get_all_workers(include_inactive=include_inactive)

    def get_latest_workers(self, limit: int = 10) -> List[WorkerDTO]:
        return self.core.get_latest_workers(limit=limit)

    def get_worker_details(self, worker_id: int) -> Optional[WorkerDetailDTO]:
        return self.core.get_worker_details(worker_id)

    def add_worker(
        self,
        nombre_completo: str,
        notas: str = "",
        tipo_trabajador: int = 1,
        activo: bool = True,
        worker_id: Optional[int] = None,
        username: Optional[str] = None,
        password_hash: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Union[bool, str]:
        return self.core.add_worker(
            nombre_completo,
            notas=notas,
            tipo_trabajador=tipo_trabajador,
            activo=activo,
            worker_id=worker_id,
            username=username,
            password_hash=password_hash,
            role=role,
        )

    def update_worker(
        self,
        worker_id: int,
        nombre_completo: str,
        activo: bool,
        notas: str,
        tipo_trabajador: int,
    ) -> bool:
        return self.core.update_worker(
            worker_id, nombre_completo, activo, notas, tipo_trabajador
        )

    def delete_worker(self, worker_id: int) -> bool:
        return self.core.delete_worker(worker_id)

    # Delegación: WorkerAuthManager
    def authenticate_user(self, username: str, password: str) -> Optional[AuthResponseDTO]:
        return self.auth.authenticate_user(username, password)

    def update_user_credentials(
        self, worker_id: int, username: str, password: str, role: str
    ) -> bool:
        return self.auth.update_user_credentials(worker_id, username, password, role)

    def update_user_password(self, worker_id: int, password: str) -> bool:
        return self.auth.update_user_password(worker_id, password)

    # Delegación: WorkerAnnotationManager
    def get_worker_annotations(self, worker_id: int) -> List[WorkerAnnotationDTO]:
        return self.annotation.get_worker_annotations(worker_id)

    def add_worker_annotation(
        self, worker_id: int, pila_id: int, annotation: str
    ) -> bool:
        return self.annotation.add_worker_annotation(worker_id, pila_id, annotation)
