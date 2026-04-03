"""Fachada de dominio de fabricación y preprocesos."""

from __future__ import annotations

from typing import Any


class ProductionFacade:
    """Agrupa FabricacionService y operaciones de repositorio pendientes de migrar."""

    def __init__(self, fabricacion_service: Any, db: Any) -> None:
        self._fabricacion_service = fabricacion_service
        self._db = db

    def __getattr__(self, name: str) -> Any:
        return getattr(self._fabricacion_service, name)

    def get_fabricacion_by_id(self, fabricacion_id: int) -> Any:
        return self._db.preproceso_repo.get_fabricacion_by_id(fabricacion_id)

    def get_fabricacion_by_codigo(self, codigo: str) -> Any:
        return self._db.preproceso_repo.get_fabricacion_by_codigo(codigo)

    def get_products_for_fabricacion(self, fabricacion_id: int) -> list[Any]:
        return self._db.get_products_for_fabricacion(fabricacion_id)

    def create_fabricacion_with_preprocesos(self, data: Any) -> bool:
        return self._db.preproceso_repo.create_fabricacion_with_preprocesos(data)

    def set_products_for_fabricacion(self, fabricacion_id: int, productos: Any) -> bool:
        return self._db.preproceso_repo.set_products_for_fabricacion(fabricacion_id, productos)

    def update_fabricacion_and_preprocesos(self, dto: Any, preprocesos: Any) -> bool:
        return self._db.preproceso_repo.update_fabricacion_and_preprocesos(dto, preprocesos)

    def delete_fabricacion(self, fabricacion_id: int) -> bool:
        return self._db.preproceso_repo.delete_fabricacion(fabricacion_id)
