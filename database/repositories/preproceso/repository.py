"""
Capa de datos (`repository`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from typing import List, Optional, Dict, Any, Callable
from sqlalchemy.orm import Session
from core.dtos import PreprocesoDTO, ComponenteDTO, FabricacionDTO, FabricacionProductoDTO
from ..base import BaseRepository
from .preproceso_manager import PreprocesoManager
from .fabricacion_manager import FabricacionManager


class PreprocesoRepository(BaseRepository):
    """
    Gestiona las operaciones CRUD para los modelos Preproceso y Fabricacion
    utilizando exclusivamente SQLAlchemy.
    Implementa el patrón Fachada delegando en managers especializados.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        super().__init__(session_factory)
        self.preproceso = PreprocesoManager(session_factory)
        self.fabricacion = FabricacionManager(session_factory)

    # Delegación de PreprocesoManager
    def get_all_preprocesos(self) -> List[PreprocesoDTO]:
        return self.preproceso.get_all_preprocesos()

    def get_preproceso_components(self, preproceso_id: int) -> List[ComponenteDTO]:
        return self.preproceso.get_preproceso_components(preproceso_id)

    def get_all_preprocesos_with_components(self) -> list[dict[str, Any]]:
        """
        Devuelve preprocesos junto con sus componentes.

        Se usa como método de compatibilidad para `DatabaseManager.get_all_preprocesos_with_components()`.
        """
        result: list[dict[str, Any]] = []
        for p in self.get_all_preprocesos():
            componentes = self.get_preproceso_components(p.id)
            result.append({"preproceso": p, "componentes": componentes})
        return result

    def create_preproceso(self, data: PreprocesoDTO) -> bool:
        return self.preproceso.create_preproceso(data)

    def update_preproceso(self, preproceso_id: int, data: PreprocesoDTO) -> bool:
        return self.preproceso.update_preproceso(preproceso_id, data)

    def delete_preproceso(self, preproceso_id: int) -> bool:
        return self.preproceso.delete_preproceso(preproceso_id)

    # Delegación de FabricacionManager
    def get_all_fabricaciones(self) -> List[FabricacionDTO]:
        return self.fabricacion.get_all_fabricaciones()

    def get_products_for_fabricacion(self, fabricacion_id: int) -> List[FabricacionProductoDTO]:
        return self.fabricacion.get_products_for_fabricacion(fabricacion_id)

    def add_product_to_fabricacion(self, fabricacion_id: int, producto_codigo: str, cantidad: int = 1) -> bool:
        return self.fabricacion.add_product_to_fabricacion(fabricacion_id, producto_codigo, cantidad)

    def set_products_for_fabricacion(self, fabricacion_id: int, products: List[FabricacionProductoDTO]) -> bool:
        return self.fabricacion.set_products_for_fabricacion(fabricacion_id, products)

    def get_fabricacion_by_codigo(self, codigo: str) -> Optional[FabricacionDTO]:
        return self.fabricacion.get_fabricacion_by_codigo(codigo)

    def search_fabricaciones(self, query: str) -> List[FabricacionDTO]:
        return self.fabricacion.search_fabricaciones(query)

    def get_fabricacion_by_id(self, fabricacion_id: int) -> Optional[FabricacionDTO]:
        return self.fabricacion.get_fabricacion_by_id(fabricacion_id)

    def create_fabricacion_with_preprocesos(self, data: FabricacionDTO) -> bool:
        return self.fabricacion.create_fabricacion_with_preprocesos(data)

    def update_fabricacion_and_preprocesos(self, fabricacion_id: int, data: FabricacionDTO, preproceso_ids: Optional[List[int]]) -> bool:
        return self.fabricacion.update_fabricacion_and_preprocesos(fabricacion_id, data, preproceso_ids)

    def delete_fabricacion(self, fabricacion_id: int) -> bool:
        return self.fabricacion.delete_fabricacion(fabricacion_id)

    def get_latest_fabricaciones(self, limit: int = 5) -> List[FabricacionDTO]:
        return self.fabricacion.get_latest_fabricaciones(limit)

    def get_preprocesos_by_fabricacion(self, fabricacion_id: int) -> List[PreprocesoDTO]:
        return self.fabricacion.get_preprocesos_by_fabricacion(fabricacion_id)

    def update_fabricacion_preprocesos(self, fabricacion_id: int, preproceso_ids: List[int]) -> bool:
        return self.fabricacion.update_fabricacion_preprocesos(fabricacion_id, preproceso_ids)

    def create_fabricacion(self, codigo: str, descripcion: str) -> bool:
        """Crea una nueva fabricación simple (wrapper para compatibilidad)."""
        return self.create_fabricacion_with_preprocesos(FabricacionDTO(
            id=0,
            codigo=codigo,
            descripcion=descripcion
        ))
