# -*- coding: utf-8 -*-
"""
Nombre del Módulo: fabricacion_controller
Descripción: Controlador central para la gestión del ciclo de vida de las fabricaciones.
             Maneja la creación, búsqueda y la integración con preprocesos.
"""
from __future__ import annotations

import logging
from typing import Any, cast
from PyQt6.QtCore import QObject, pyqtSignal
from database.database_manager import DatabaseManager
from core.dtos import CalculationProductDTO
from core.interfaces.view_interface import IView
from controllers.product.protocols import IFabricacionControllerDelegate


class FabricacionController(QObject):
    """
    Controlador dedicado a la gestión de fabricaciones.
    
    Actúa como mediador para las operaciones CRUD de fabricaciones, delegando gran 
    parte de la lógica pesada a `ProductControllerV2` para mantener la consistencia.
    """
    
    # Signals
    fabricacion_created = pyqtSignal(int)  # ID de fabricación creada
    fabricaciones_updated = pyqtSignal()
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        view: IView,
        product_controller: IFabricacionControllerDelegate,
        logger: logging.Logger,
    ) -> None:
        """
        Inicializa el controlador de fabricaciones.

        Args:
            db_manager: Gestor de conexión a la base de datos.
            view: Referencia a la vista principal.
            product_controller: Controlador de productos para delegación.
            logger: Instancia de logging.
        """
        super().__init__()
        self.db: DatabaseManager = db_manager
        self.view: IView = view
        self.product_controller: IFabricacionControllerDelegate = product_controller
        self.logger: logging.Logger = logger
        
    def connect_signals(self) -> None:
        """Conecta las señales del widget de gestión de Fabricaciones."""
        # Las señales específicas se conectan en AppController._connect_fabrications_signals
        pass
        
    def show_create_fabricacion_dialog(self) -> None:
        """Muestra el diálogo para crear una nueva fabricación."""
        # Esta funcionalidad está delegada a ProductControllerV2
        self.product_controller.show_create_fabricacion_dialog()
        
    def search_fabricaciones(self, text: str) -> list[Any]:
        """
        Busca fabricaciones por texto.
        
        Args:
            text: Texto de búsqueda
        """
        # Delegado a ProductControllerV2
        return self.product_controller.search_fabricaciones(text)
        
    def show_fabricacion_preprocesos(self, fabricacion_id: int) -> None:
        """
        Muestra los preprocesos de una fabricación.
        
        Args:
            fabricacion_id: ID de la fabricación
        """
        # Delegado a ProductControllerV2
        self.product_controller.show_fabricacion_preprocesos(fabricacion_id)
        
    def refresh_fabricaciones_list(self) -> None:
        """Actualiza la lista de fabricaciones en la UI."""
        self.product_controller._refresh_fabricaciones_list()
        self.fabricaciones_updated.emit()
        
    def get_fabricacion_products_for_calculation(
        self, 
        fabricacion_id: int
    ) -> list[CalculationProductDTO]:
        """
        Obtiene todos los productos de una fabricación preparados para cálculo.
        
        Args:
            fabricacion_id: ID de la fabricación
            
        Returns:
            Lista de CalculationProductDTO con datos para cálculo
        """
        try:
            # Delegar al product_controller para mantener consistencia
            if hasattr(self.product_controller, 'get_fabricacion_products_for_calculation'):
                return cast(list[CalculationProductDTO], self.product_controller.get_fabricacion_products_for_calculation(fabricacion_id))
            
            # Fallback (si por alguna razón no está disponible)
            productos = self.db.get_products_by_fabricacion(fabricacion_id)
            
            result = []
            for p in productos:
                result.append(CalculationProductDTO(
                    codigo=p.codigo,
                    descripcion=p.descripcion or '',
                    departamento="Produccion",
                    tipo_trabajador=1,
                    donde="",
                    tiene_subfabricaciones=False,
                    tiempo_optimo=0.0,
                    sub_partes=[],
                    cantidad_en_kit=1,
                    fabricacion_id=fabricacion_id
                ))
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo productos de fabricación {fabricacion_id}: {e}")
            return []
