"""
Capa de datos (`protocols`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar
from sqlalchemy.orm import Session
import logging

T = TypeVar("T")

class RepositoryProtocol(Protocol):
    """Contrato común de repositorios basados en BaseRepository (sesión y ejecución segura)."""
    session_factory: Callable[[], Session]
    logger: logging.Logger
    
    def get_session(self) -> Optional[Session]: ...
    def safe_execute(self, operation: Callable[..., T], *args: Any, **kwargs: Any) -> Optional[T]: ...

class PilaRepositoryProtocol(RepositoryProtocol):
    """Protocolo específico para el repositorio de Pila."""
    def _convert_indices_to_ids(self, production_flow: List[Dict[str, Any]]) -> None: ...
    def _convert_ids_to_indices(self, production_flow: List[Dict[str, Any]]) -> None: ...

class TrackingRepositoryProtocol(RepositoryProtocol):
    """Protocolo específico para el repositorio de Tracking."""
    def _map_to_trabajo_log_dto(self, trabajo: Any) -> Any: ...
    def _map_to_incidencia_log_dto(self, incidencia: Any) -> Any: ...
    def _map_to_incidencia_adjunto_dto(self, adjunto: Any) -> Any: ...
    def _map_to_paso_trazabilidad_dto(self, paso: Any) -> Any: ...
    def obtener_o_crear_trabajo_log_por_qr(self, qr_code: str, trabajador_id: int, fabricacion_id: int, producto_codigo: str, orden_fabricacion: Optional[str] = None, notas: Optional[str] = None) -> Any: ...
