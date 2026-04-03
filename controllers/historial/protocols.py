"""
Nombre del Módulo: protocols.py (Historial)
Descripción: Define los protocolos (interfaces estructurales) para garantizar el 
             tipado correcto y la compatibilidad entre el controlador de historial y sus gestores.
"""
from typing import Protocol, Any, List, Dict

class HistorialControllerProtocol(Protocol):
    view: Any
    model: Any
    logger: Any
    db: Any
    pila_service: Any
    worker_service: Any
    historial_data: List[Any]

    def update_calendar_highlights(self) -> None: ...
    def populate_list(self) -> None: ...
    def update_activity_chart(self) -> None: ...
