# core/simulation/events/base.py

"""
Nombre del Módulo: core.simulation.simulation_events.base

Descripción: Define protocolos o tipos principales: ``EventoDeSimulacion``. Clase base para todos los eventos de la simulación. Integración típica con: ``datetime``.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine.motor import MotorDeEventos

@dataclass
class EventoDeSimulacion:
    """
    Clase base para todos los eventos de la simulación.
    
    Define la estructura mínima de un evento, incluyendo su marca de tiempo,
    prioridad y la lógica para ser procesado por el motor de eventos.
    """
    timestamp: datetime
    datos: Dict[str, Any] = field(default_factory=dict)
    cancelado: bool = field(default=False)
    tipo_evento: str = field(init=False)
    prioridad: int = field(init=False)

    def procesar(self, motor_eventos: "MotorDeEventos") -> List["EventoDeSimulacion"]:
        """
        Ejecuta la lógica asociada al evento y devuelve nuevos eventos generados.

        Args:
            motor_eventos: Instancia del motor que está procesando la cola.

        Returns:
            Lista de nuevos eventos a programar en la cola.
        """
        raise NotImplementedError
