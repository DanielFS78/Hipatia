# -*- coding: utf-8 -*-
"""
Nombre del Módulo: preproceso_controller
Descripción: Gestiona la lógica de preprocesos, incluyendo su carga desde el modelo, 
             vínculo con componentes y conversión a pasos operativos en la pila.
"""
from __future__ import annotations

import logging
from typing import Any, cast
from PyQt6.QtCore import QObject, pyqtSignal
from database.database_manager import DatabaseManager
from database.repositories import PreprocesoRepository

class PreprocesoController(QObject):
    """
    Controlador para la gestión de preprocesos de fabricación.
    """
    db: DatabaseManager
    view: Any
    fabricacion_service: Any
    logger: logging.Logger
    _preproceso_repo: PreprocesoRepository | None
    
    # Signals
    preprocesos_loaded: pyqtSignal = pyqtSignal()
    preprocesos_updated: pyqtSignal = pyqtSignal()
    
    def __init__(self, db_manager: DatabaseManager, view: Any, fabricacion_service: Any, logger: logging.Logger) -> None:
        """
        Inicializa el controlador de preprocesos.

        Args:
            db_manager: Gestor de conexión a la base de datos.
            view: Referencia a la vista principal.
            fabricacion_service: Servicio lógico de fabricaciones.
            logger: Instancia de logging.
        """
        super().__init__()
        self.db: DatabaseManager = db_manager
        self.view: Any = view
        self.fabricacion_service: Any = fabricacion_service
        self.logger: logging.Logger = logger
        # Lazy init del repo
        self._preproceso_repo: PreprocesoRepository | None = None
        
    @property
    def preproceso_repo(self) -> PreprocesoRepository:
        """Lazy initialization del repositorio de preprocesos."""
        if self._preproceso_repo is None:
            sf = self.db.SessionLocal
            if sf is None:
                raise RuntimeError("SessionLocal no inicializado en DatabaseManager")
            self._preproceso_repo = PreprocesoRepository(sf)
        return self._preproceso_repo
        
    def connect_signals(self) -> None:
        """Conecta las señales del widget de preprocesos."""
        # Implementación delegada por ahora
        # Las señales específicas se conectan en AppController._connect_preprocesos_signals
        pass
        
    def load_preprocesos_data(self) -> None:
        """
        Solicita al servicio la carga de todos los preprocesos disponibles y los 
        refleja en la tabla de la interfaz de usuario.
        """
        self.logger.info("Cargando datos de preprocesos...")
        try:
            preprocesos_widget = self.view.pages.get("preprocesos")

            if not preprocesos_widget:
                self.logger.warning("Widget de preprocesos no encontrado en las páginas.")
                return

            # Obtener los datos de preprocesos del modelo
            preprocesos_data = self.get_all_preprocesos_with_components()

            # Cargar en el widget
            preprocesos_widget.load_preprocesos_data(preprocesos_data)
            self.preprocesos_loaded.emit()

        except Exception as e:
            self.logger.error(f"Error cargando datos de preprocesos: {e}")
            # Cargar lista vacía en caso de error
            preprocesos_widget = self.view.pages.get("preprocesos")
            if preprocesos_widget:
                preprocesos_widget.load_preprocesos_data([])
        
    def get_all_preprocesos_with_components(self) -> list[dict[str, Any]]:
        """
        Obtiene todos los preprocesos ya formateados desde el repositorio.
        
        Returns:
            Lista de preprocesos con sus componentes
        """
        try:
            return cast(list[dict[str, Any]], self.fabricacion_service.get_all_preprocesos_with_components())
        except Exception as e:
            self.logger.error(f"Error obteniendo preprocesos: {e}", exc_info=True)
            return []
        
    def get_preprocesos_by_fabricacion(self, fabricacion_id: int) -> list[dict[str, Any]]:
        """
        Obtiene los preprocesos asignados a una fabricación.
        
        Args:
            fabricacion_id: ID de la fabricación
            
        Returns:
            Lista de diccionarios con información de preprocesos
        """
        try:
            preprocesos = self.preproceso_repo.get_preprocesos_by_fabricacion(fabricacion_id)

            # Convertir a formato esperado
            result = []
            for preproceso in preprocesos:
                comps_data = []
                for comp in preproceso.componentes:
                    desc = getattr(comp, 'descripcion_componente', getattr(comp, 'descripcion', ''))
                    comps_data.append((comp.id, desc))
                
                result.append({
                    'id': preproceso.id,
                    'nombre': preproceso.nombre,
                    'descripcion': preproceso.descripcion or '',
                    'componentes': comps_data
                })

            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo preprocesos de fabricación: {e}")
            return []
        
    def add_preprocesos_to_current_pila(self, preprocesos: list[Any]) -> None:
        """
        Añade preprocesos a la pila de cálculo actual.
        
        Args:
            preprocesos: Lista de preprocesos a añadir
        """
        # Esta funcionalidad está delegada a CalculationController/PilaController
        # Este método se mantiene como proxy para compatibilidad
        pass
        
    def convert_preproceso_to_pila_step(self, preproceso: dict[str, Any]) -> dict[str, Any]:
        """
        Convierte un preproceso al formato de paso de pila.
        
        Args:
            preproceso: Diccionario con datos del preproceso
            
        Returns:
            Diccionario en formato de paso de pila
        """
        # Convertir formato de preproceso a formato de paso de pila
        return {
            'tipo': 'preproceso',
            'id': preproceso.get('id'),
            'codigo': preproceso.get('nombre', ''),
            'descripcion': preproceso.get('descripcion', ''),
            'componentes': preproceso.get('componentes', [])
        }
        
    def on_manage_procesos_for_new_product(self, current_procesos: list[dict[str, Any]]) -> None:
        """
        Gestiona los procesos para un nuevo producto.
        
        Args:
            current_procesos: Procesos actuales del producto
        """
        # Esta funcionalidad está delegada a ProductControllerV2
        # Mantenido como placeholder
        pass

