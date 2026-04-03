"""
========================================================================
MOTOR DE EVENTOS — PUNTO DE ENTRADA DEL PAQUETE
========================================================================
Fachada de compatibilidad (Fase 2.2): reexporta MotorDeEventos desde
core.simulation.engine para orquestar el bucle de eventos de simulación
sin acoplar importadores al subpaquete interno.
========================================================================
"""

from .engine.motor import MotorDeEventos

__all__ = ["MotorDeEventos"]