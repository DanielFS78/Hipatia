# core/simulation/engine/base.py
"""
Definición de estructuras de datos base para el motor de simulación.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any

from ..timeline_task import LineaTemporalTarea

@dataclass
class SimulationState:
    """
    Mantiene el estado volátil y reactivo de una simulación en curso.
    
    Almacena la cola de eventos, las líneas temporales de las tareas y
    el estado actual de los recursos asignados.
    """
    tiempo_actual: datetime
    production_flow: List[Dict[str, Any]]
    eventos_futuros: list[tuple[datetime, int, Any]] = field(default_factory=list)
    event_counter: int = 0
    audit_log_interno: List[Any] = field(default_factory=list)
    lineas_temporales: Dict[int, LineaTemporalTarea] = field(default_factory=dict)
    indice_a_tarea_id: Dict[int, int] = field(default_factory=dict)
    tarea_id_a_indice: Dict[int, int] = field(default_factory=dict)
