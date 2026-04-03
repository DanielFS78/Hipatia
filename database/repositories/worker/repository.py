"""
Capa de datos (`repository`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from typing import List, Optional, Union, Callable, Any
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
    def get_all_workers(self, *args, **kwargs) -> List[WorkerDTO]:
        return self.core.get_all_workers(*args, **kwargs)

    def get_latest_workers(self, *args, **kwargs) -> List[WorkerDTO]:
        return self.core.get_latest_workers(*args, **kwargs)

    def get_worker_details(self, *args, **kwargs) -> Optional[WorkerDetailDTO]:
        return self.core.get_worker_details(*args, **kwargs)

    def add_worker(self, *args, **kwargs) -> Union[bool, str]:
        return self.core.add_worker(*args, **kwargs)

    def update_worker(self, *args, **kwargs) -> bool:
        return self.core.update_worker(*args, **kwargs)

    def delete_worker(self, *args, **kwargs) -> bool:
        return self.core.delete_worker(*args, **kwargs)

    # Delegación: WorkerAuthManager
    def authenticate_user(self, *args, **kwargs) -> Optional[AuthResponseDTO]:
        return self.auth.authenticate_user(*args, **kwargs)

    def update_user_credentials(self, *args, **kwargs) -> bool:
        return self.auth.update_user_credentials(*args, **kwargs)

    def update_user_password(self, *args, **kwargs) -> bool:
        return self.auth.update_user_password(*args, **kwargs)

    # Delegación: WorkerAnnotationManager
    def get_worker_annotations(self, *args, **kwargs) -> List[WorkerAnnotationDTO]:
        return self.annotation.get_worker_annotations(*args, **kwargs)

    def add_worker_annotation(self, *args, **kwargs) -> bool:
        return self.annotation.add_worker_annotation(*args, **kwargs)
