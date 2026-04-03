# core/services/fabricacion_service.py
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: FabricacionService
Descripción: Servicio de lógica de negocio para la gestión de fabricaciones, órdenes de seguimiento y preprocesos.
"""
import logging
from datetime import datetime
from typing import Any
from dataclasses import asdict

from PyQt6.QtCore import QObject, pyqtSignal

from core.dtos import PreprocesoDTO, FabricacionDTO, FabricacionProductoDTO
from database.database_manager import DatabaseManager

class FabricacionService(QObject):
    """
    Servicio de dominio para la gestión centralizada de Fabricaciones y Preprocesos.
    
    Actúa como una capa de orquestación (Fase 11C/12C) que:
    1. Valida las reglas de negocio antes de persistir los datos.
    2. Coordina la creación de fabricaciones complejas que incluyen preprocesos y productos.
    3. Garantiza que toda la comunicación sea mediante `FabricacionDTO` y `PreprocesoDTO`,
       sirviendo como frontera limpia para los controladores de la UI.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Inicializa el servicio de fabricación con su gestor de base de datos.

        Args:
            db_manager: Instancia central de gestión de persistencia.
        """
        super().__init__()
        self.db = db_manager
        self.logger = logging.getLogger("FabricacionService")

    @property
    def preproceso_repo(self):
        """Acceso directo al repositorio de preprocesos."""
        return self.db.preproceso_repo
    
    @property
    def tracking_repo(self):
        """Acceso directo al repositorio de seguimiento."""
        return self.db.tracking_repo

    # --- Fabricaciones ---

    def get_latest_fabricaciones(self, limit: int = 5) -> list[Any]:
        """
        Obtiene las fabricaciones más recientes.

        Args:
            limit: Número máximo de fabricaciones a retornar.

        Returns:
            Lista de objetos de fabricación.
        """
        return self.preproceso_repo.get_latest_fabricaciones(limit)

    def search_fabricaciones(self, query: str) -> list[Any]:
        """
        Busca fabricaciones por código o descripción.

        Args:
            query: Texto de búsqueda.

        Returns:
            Lista de fabricaciones coincidentes.
        """
        return self.preproceso_repo.search_fabricaciones(query)

    def create_fabricacion(self, codigo: str, descripcion: str) -> bool:
        return self.preproceso_repo.create_fabricacion(codigo, descripcion)

    def get_fabricacion_by_id(self, fabricacion_id: int) -> Any:
        return self.preproceso_repo.get_fabricacion_by_id(fabricacion_id)

    def get_fabricacion_by_codigo(self, codigo: str) -> Any:
        return self.preproceso_repo.get_fabricacion_by_codigo(codigo)

    def delete_fabricacion(self, fabricacion_id: int) -> bool:
        return self.preproceso_repo.delete_fabricacion(fabricacion_id)

    def create_fabricacion_with_preprocesos(self, data: FabricacionDTO) -> bool:
        """
        Orquesta la creación de una fabricación con sus preprocesos asociados.
        
        Recibe un `FabricacionDTO` completo y delega la persistencia al repositorio.
        Este método es el punto de entrada principal para flujos que requieren
        integridad referencial entre la cabecera de fabricación y su checklist técnica.
        """
        return self.preproceso_repo.create_fabricacion_with_preprocesos(data)

    def update_fabricacion_and_preprocesos(
        self, fabricacion_id: int, data: FabricacionDTO, preproceso_ids: list[int] | None = None
    ) -> bool:
        return self.preproceso_repo.update_fabricacion_and_preprocesos(fabricacion_id, data, preproceso_ids)

    def update_fabricacion_preprocesos(self, fabricacion_id: int, preproceso_ids: list[int]) -> bool:
        return self.preproceso_repo.update_fabricacion_preprocesos(fabricacion_id, preproceso_ids)

    def get_products_for_fabricacion(self, fabricacion_id: int) -> list[FabricacionProductoDTO]:
        return self.preproceso_repo.get_products_for_fabricacion(fabricacion_id)

    def set_products_for_fabricacion(self, fabricacion_id: int, productos: list[FabricacionProductoDTO]) -> bool:
        return self.preproceso_repo.set_products_for_fabricacion(fabricacion_id, productos)

    # --- Preprocesos ---
    
    def get_all_preprocesos_with_components(self) -> list[PreprocesoDTO]:
        return self.preproceso_repo.get_all_preprocesos()

    def create_preproceso(self, data: PreprocesoDTO) -> bool:
        return self.preproceso_repo.create_preproceso(data) is not None

    def update_preproceso(self, preproceso_id: int, data: PreprocesoDTO) -> bool:
        return self.preproceso_repo.update_preproceso(preproceso_id, data)

    def delete_preproceso(self, preproceso_id: int) -> bool:
        return self.preproceso_repo.delete_preproceso(preproceso_id)

    def get_preprocesos_by_fabricacion(self, fabricacion_id: int) -> list[Any]:
        """
        Obtiene la lista de preprocesos asociados a una fabricación.

        Args:
            fabricacion_id: ID único de la fabricación.

        Returns:
            Lista de preprocesos.
        """
        return self.preproceso_repo.get_preprocesos_by_fabricacion(fabricacion_id)

    def get_all_ordenes_fabricacion(self) -> list[Any]:
        """Obtiene la lista de todas las órdenes de fabricación."""
        return self.tracking_repo.get_all_ordenes_fabricacion()

