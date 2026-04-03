# -*- coding: utf-8 -*-
"""
Nombre del Módulo: application_state.py
Descripción: Almacén de estado compartido (State Management) que centraliza las 
             variables globales y temporales de la aplicación.
"""
import logging
from typing import Any, Callable, Dict, List, Optional

class ApplicationState:
    """
    Estado compartido de la aplicación.

    Almacena variables de sesión, resultados de la última simulación, estados de 
    búsqueda y referencias a hilos en segundo plano, permitiendo la comunicación 
    entre componentes desacoplados.
    """
    def __init__(self) -> None:
        """
        Inicializa una nueva instancia de ApplicationState.

        Configura el logger y todas las variables de estado iniciales.
        """
        self.logger = logging.getLogger("ApplicationState")
        
        # State variables extracted from AppController
        self.active_dialogs: Dict[str, Any] = {}
        self.edit_search_type: str = "Productos"
        self.selected_product: Optional[str] = None
        self.last_production_flow: Optional[Any] = None
        self.last_simulation_results: Optional[Any] = None
        self.last_audit_log: Optional[Any] = None
        self.last_units_calculated: int = 1
        self.last_flexible_workers_needed: int = 0
        self.current_lote_content: List[Any] = []
        self.selected_report_item: Optional[Any] = None
        self.selected_product_for_calc: Optional[Any] = None
        self.selected_product_for_calc_desc: str = ""
        self.bg_thread: Optional[Any] = None
        self.worker: Optional[Any] = None
        self.last_pila_id_calculated: Optional[int] = None
        
        # Simple observer pattern for state changes
        self._listeners: Dict[str, List[Callable[[Any], None]]] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def set(self, key: str, value: Any) -> None:
        if hasattr(self, key):
            setattr(self, key, value)
            self._notify_listeners(key, value)
        else:
            self.logger.warning(f"Attempted to set unknown state variable: {key}")
            # Allow dynamic setting if strictly needed, but warn for now
            setattr(self, key, value)
            self._notify_listeners(key, value)

    def add_listener(self, key: str, callback: Callable[[Any], None]) -> None:
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)

    def remove_listener(self, key: str, callback: Callable[[Any], None]) -> None:
         if key in self._listeners and callback in self._listeners[key]:
             self._listeners[key].remove(callback)

    def _notify_listeners(self, key: str, value: Any) -> None:
        if key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(value)
                except Exception as e:
                    self.logger.error(f"Error in ApplicationState listener for '{key}': {e}")
