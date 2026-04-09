"""
Interfaz PyQt6 (`enhanced_flow_state_manager`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple, cast

from core.enhanced_flow_canvas_state_io import (
    canvas_state_apply_cycle_end,
    canvas_state_find_worker_by_name,
    canvas_state_inspector_view,
    canvas_state_logical_connections_for_index,
    canvas_state_mut_config,
    canvas_state_reindex_after_remove,
    canvas_state_set_config_key,
    canvas_state_simulation_progress_text,
)


class EnhancedFlowStateManager:
    """Colaborador de composición para estado del canvas y preview de simulación."""

    def __init__(self, presenter: Any) -> None:
        self.presenter = presenter

    def add_task(self, task_data: Dict[str, Any], position: Dict[str, int]) -> Tuple[Dict[str, Any], int]:
        presenter = self.presenter
        default_config: Dict[str, Any] = {
            "workers": [],
            "machine_id": None,
            "start_condition": {"type": "date", "value": date.today()},
            "total_units": presenter.default_units,
            "min_predecessor_units": 1,
            "units_per_cycle": 1,
            "is_cycle_start": False,
            "is_cycle_end": False,
            "cycle_return_to_index": None,
            "next_cyclic_task_index": None,
        }

        task_entry = {"data": task_data, "config": default_config, "position": position}
        presenter.canvas_tasks.append(task_entry)
        index = len(presenter.canvas_tasks) - 1
        return task_entry, index

    def remove_task(self, index: int) -> bool:
        presenter = self.presenter
        if not (0 <= index < len(presenter.canvas_tasks)):
            return False

        presenter.canvas_tasks.pop(index)
        canvas_state_reindex_after_remove(presenter.canvas_tasks, index, date.today())
        return True

    def clear_tasks(self) -> None:
        self.presenter.canvas_tasks.clear()

    def get_task(self, index: int) -> Optional[Dict[str, Any]]:
        presenter = self.presenter
        if 0 <= index < len(presenter.canvas_tasks):
            return cast(Optional[Dict[str, Any]], presenter.canvas_tasks[index])
        return None

    def update_task_config(self, index: int, key: str, value: Any) -> bool:
        presenter = self.presenter
        if not (0 <= index < len(presenter.canvas_tasks)):
            return False
        canvas_state_set_config_key(presenter.canvas_tasks[index], key, value)
        return True

    def apply_cycle_end_config(self, index: int, is_cycle_end: bool, return_to_index: Optional[int]) -> bool:
        presenter = self.presenter
        if not (0 <= index < len(presenter.canvas_tasks)):
            return False

        current_task_config = canvas_state_mut_config(presenter.canvas_tasks[index])
        canvas_state_apply_cycle_end(current_task_config, is_cycle_end, return_to_index)
        return True

    def get_worker_config(self, task_index: int, worker_name: str) -> Optional[Dict[str, Any]]:
        task = self.get_task(task_index)
        if not task:
            return None
        return canvas_state_find_worker_by_name(task, worker_name)

    def get_inspector_data(self, task_index: int) -> Dict[str, Any]:
        return canvas_state_inspector_view(self.presenter.canvas_tasks, task_index)

    def identify_last_tasks_in_cycles(self, simulation_service: Any) -> List[int]:
        return cast(List[int], simulation_service.identify_last_tasks_in_cycles(self.presenter.canvas_tasks))

    def start_simulation_preview(self, simulation_service: Any) -> bool:
        presenter = self.presenter
        if not presenter.canvas_tasks:
            return False

        presenter.simulation_service = simulation_service
        presenter.simulation_session = presenter.simulation_service.start_simulation(presenter.canvas_tasks)
        return presenter.simulation_session is not None and bool(getattr(presenter.simulation_session, "order", []))

    def get_next_simulation_step(self) -> Optional[int]:
        presenter = self.presenter
        if not presenter.simulation_session:
            return None
        return cast(Optional[int], presenter.simulation_session.next_step())

    def stop_simulation_preview(self) -> None:
        self.presenter.simulation_session = None

    def get_simulation_progress_text(self, current_idx: int) -> str:
        return canvas_state_simulation_progress_text(self.presenter.canvas_tasks, current_idx)

    def get_logical_connections(self, selected_index: int) -> List[Dict[str, Any]]:
        return canvas_state_logical_connections_for_index(self.presenter.canvas_tasks, selected_index)
