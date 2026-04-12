# core/simulation/events/__init__.py

"""
Nombre del Módulo: core.simulation.simulation_events

Descripción: Concentra datos de configuración o catálogos estáticos: ``__all__``, consumidos por la UI y controladores. Integración típica con: ``base``, ``production``, ``worker``.
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
