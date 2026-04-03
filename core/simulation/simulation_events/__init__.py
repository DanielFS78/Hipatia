# core/simulation/events/__init__.py

"""
Lógica o utilidades del núcleo (`__init__`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

from .base import EventoDeSimulacion
from .production import EventoInicioUnidad, EventoFinUnidad
from .worker import EventoReasignacionTrabajador, EventoTiempoInactivo

# Maintain backward compatibility
__all__ = [
    'EventoDeSimulacion',
    'EventoInicioUnidad',
    'EventoFinUnidad',
    'EventoReasignacionTrabajador',
    'EventoTiempoInactivo'
]
