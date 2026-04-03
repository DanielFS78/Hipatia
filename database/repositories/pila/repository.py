"""
Capa de datos (`repository`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from ..base import BaseRepository
from typing import List, Optional, Tuple, Dict, Any, Union
from .pila_base_manager import PilaBaseManager
from .pila_crud_manager import PilaCRUDManager
from .pila_workflow_manager import PilaWorkflowManager
from .pila_bitacora_manager import PilaBitacoraManager
from core.dtos import PilaDTO

class PilaRepository(BaseRepository):
    """
    Repositorio para la gestión de pilas de producción.
    Implementa el patrón Fachada delegando en DAO Managers especializados.
    """

    def __init__(self, session_factory) -> None:
        super().__init__(session_factory)
        
        # Composición de gestores
        self.base = PilaBaseManager(session_factory)
        self.crud = PilaCRUDManager(session_factory)
        self.workflow = PilaWorkflowManager(session_factory, self.base)
        self.bitacora = PilaBitacoraManager(session_factory)
        self._sync_managers()

    def _sync_managers(self):
        for m in [self.base, self.crud, self.workflow, self.bitacora]:
            m.session_factory = self.session_factory

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name in ('session_factory', 'safe_execute'):
            if hasattr(self, 'crud'):
                for m in [self.base, self.crud, self.workflow, self.bitacora]:
                    setattr(m, name, value)

    # Delegación: PilaCRUDManager
    def get_all_pilas(self) -> List[PilaDTO]:
        return self.crud.get_all_pilas()

    def get_all_pilas_with_dates(self) -> List[PilaDTO]:
        return self.crud.get_all_pilas_with_dates()

    def search_pilas(self, query: str) -> List[PilaDTO]:
        return self.crud.search_pilas(query)

    def find_pilas_by_producto_codigo(self, code: str) -> List[PilaDTO]:
        return self.crud.find_pilas_by_producto_codigo(code)

    def find_pila_by_name(self, name: str) -> Optional[int]:
        return self.crud.find_pila_by_name(name)

    def delete_pila(self, pid: int) -> bool:
        return self.crud.delete_pila(pid)

    # Delegación: PilaWorkflowManager
    def save_pila(self, *args, **kwargs) -> Union[int, str, bool]:
        return self.workflow.save_pila(*args, **kwargs)

    def update_pila(self, *args, **kwargs) -> Union[bool, str]:
        return self.workflow.update_pila(*args, **kwargs)

    def load_pila(self, *args, **kwargs) -> Tuple[Optional[PilaDTO], Optional[Dict], Optional[List], Optional[List]]:
        return self.workflow.load_pila(*args, **kwargs)

    # Delegación: PilaBitacoraManager
    def create_diario_bitacora(self, *args, **kwargs) -> Optional[int]:
        return self.bitacora.create_diario_bitacora(*args, **kwargs)

    def get_diario_bitacora(self, *args, **kwargs) -> Tuple[Optional[int], List[Tuple]]:
        return self.bitacora.get_diario_bitacora(*args, **kwargs)

    def add_diario_evento(self, *args, **kwargs) -> bool:
        return self.bitacora.add_diario_evento(*args, **kwargs)

    def update_diario_evento(self, *args, **kwargs) -> bool:
        return self.bitacora.update_diario_evento(*args, **kwargs)

    # Métodos de utilidad (compatibilidad con tests y lógica interna)
    def _convert_indices_to_ids(self, *args, **kwargs) -> None:
        return self.base.convert_indices_to_ids(*args, **kwargs)

    def _convert_ids_to_indices(self, *args, **kwargs) -> None:
        return self.base.convert_ids_to_indices(*args, **kwargs)
