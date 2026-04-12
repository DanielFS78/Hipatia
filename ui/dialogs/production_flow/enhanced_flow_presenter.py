# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.production_flow.enhanced_flow_presenter
Descripción: Definición o simulación del flujo de producción (estado, presentadores, reglas y diálogos auxiliares).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .flow_builder import FlowBuilder
from .enhanced_flow_state_manager import EnhancedFlowStateManager

if TYPE_CHECKING:
    from core.schedule_config import ScheduleConfig
    from core.dtos import ProductFlowLibraryProductDTO


class EnhancedFlowPresenter:
    """Presenter/Lógica para aislar el ensamblado de datos y configuraciones de la vista."""

    def __init__(self, schedule_config: Optional[ScheduleConfig] = None, default_units: int = 1) -> None:
        self.logger = logging.getLogger("EvolucionTiemposApp.EnhancedFlowPresenter")
        self.schedule_config = schedule_config
        self.default_units = default_units

        self.canvas_tasks: List[Dict[str, Any]] = []

        self.simulation_service: Any = None  # Inyectado después o lazy
        self.simulation_session: Any = None

        self._flow_builder = FlowBuilder(self)
        self._state_manager = EnhancedFlowStateManager(self)

    def load_flow(self, flow_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self._flow_builder.load_flow(flow_data)

    def prepare_task_data(self, tasks_data: List[Dict[str, Any]]) -> Dict[str, ProductFlowLibraryProductDTO]:
        return self._flow_builder.prepare_task_data(tasks_data)

    def _parse_duration(self, val_raw: Any, context: str) -> float:
        return self._flow_builder._parse_duration(val_raw, context)

    def resolve_start_date(self, start_cond: Dict[str, Any]) -> Optional[datetime]:
        return self._flow_builder.resolve_start_date(start_cond)

    def normalize_workers(self, config_workers: List[Any]) -> List[Dict[str, Any]]:
        return self._flow_builder.normalize_workers(config_workers)

    def build_production_flow(self, tasks_to_build: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        return self._flow_builder.build_production_flow(tasks_to_build)

    def add_task(self, task_data: Dict[str, Any], position: Dict[str, int]) -> tuple[Dict[str, Any], int]:
        return self._state_manager.add_task(task_data, position)

    def remove_task(self, index: int) -> bool:
        return self._state_manager.remove_task(index)

    def clear_tasks(self) -> None:
        self._state_manager.clear_tasks()

    def get_task(self, index: int) -> Optional[Dict[str, Any]]:
        return self._state_manager.get_task(index)

    def update_task_config(self, index: int, key: str, value: Any) -> bool:
        return self._state_manager.update_task_config(index, key, value)

    def apply_cycle_end_config(self, index: int, is_cycle_end: bool, return_to_index: Optional[int]) -> bool:
        return self._state_manager.apply_cycle_end_config(index, is_cycle_end, return_to_index)

    def get_worker_config(self, task_index: int, worker_name: str) -> Optional[Dict[str, Any]]:
        return self._state_manager.get_worker_config(task_index, worker_name)

    def get_inspector_data(self, task_index: int) -> Dict[str, Any]:
        return self._state_manager.get_inspector_data(task_index)

    def identify_last_tasks_in_cycles(self, simulation_service: Any) -> List[int]:
        return self._state_manager.identify_last_tasks_in_cycles(simulation_service)

    def start_simulation_preview(self, simulation_service: Any) -> bool:
        return self._state_manager.start_simulation_preview(simulation_service)

    def get_next_simulation_step(self) -> Optional[int]:
        return self._state_manager.get_next_simulation_step()

    def stop_simulation_preview(self) -> None:
        self._state_manager.stop_simulation_preview()

    def get_simulation_progress_text(self, current_idx: int) -> str:
        return self._state_manager.get_simulation_progress_text(current_idx)

    def get_logical_connections(self, selected_index: int) -> List[Dict[str, Any]]:
        return self._state_manager.get_logical_connections(selected_index)
