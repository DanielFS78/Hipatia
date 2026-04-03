# -*- coding: utf-8 -*-
"""
Nombre del Módulo: protocols.py (Simulation)
Descripción: Define los protocolos para asegurar la interoperabilidad entre el 
             SimulationController y sus gestores delegados (Execution y Editor).
"""
from typing import Protocol, Any, Optional
import logging
from PyQt6.QtCore import QThread

class SimulationControllerProtocol(Protocol):
    app: Any
    model: Any
    view: Any
    logger: logging.Logger
    state: Any
    db: Any
    worker_service: Any
    machine_service: Any
    pila_service: Any
    schedule_manager: Any
    flow_builder: Any
    execution_thread: Optional[QThread]
    worker: Any

    def _on_simulation_finished(self, results: Any, audit: Any) -> None: ...
    def _on_optimization_finished(self, results: Any, audit: Any, workers_needed: int) -> None: ...
    def _start_simulation_thread(self, scheduler: Any) -> None: ...
