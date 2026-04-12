# -*- coding: utf-8 -*-
"""
Nombre del Módulo: inspector_presenter

Descripción: Lógica pura del inspector de tareas: estado de la tarea actual, trabajadores posibles
             y mutaciones sobre el payload de configuración.
"""

from __future__ import annotations

from typing import Any, List, Tuple

from core.inspector_task_payload_io import (
    inspector_config_set_workers,
    inspector_config_workers_list,
    inspector_mut_task_config,
    inspector_new_worker_entry,
    inspector_row_config,
    inspector_row_dependency_display_name,
    inspector_row_id,
    inspector_worker_entry_name,
)


class InspectorPresenter:
    def __init__(self) -> None:
        self.current_task_id: Any = None
        self.current_task_data: dict[str, Any] = {}
        self.all_possible_workers: List[str] = []

    def set_task(self, task_data: dict[str, Any] | None, available_workers: List[str] | None = None) -> None:
        """
        Almacena la tarea actual y los trabajadores posibles.
        """
        if not task_data:
            self.current_task_id = None
            self.current_task_data = {}
            self.all_possible_workers = []
            return

        self.current_task_id = inspector_row_id(task_data)
        self.current_task_data = task_data
        self.all_possible_workers = available_workers or []

    def get_workers_lists(self) -> Tuple[List[str], List[str]]:
        """
        Devuelve (nombres asignados, nombres disponibles).
        """
        if not self.current_task_data:
            return [], []

        config = inspector_row_config(self.current_task_data)
        assigned_workers_raw = inspector_config_workers_list(config)

        assigned_names = [inspector_worker_entry_name(w) for w in assigned_workers_raw]
        available_names = [w for w in self.all_possible_workers if w not in assigned_names]

        return sorted(assigned_names), sorted(available_names)

    def assign_workers(self, worker_names: List[str]) -> List[Any]:
        """
        Añade trabajadores por nombre; devuelve la lista completa de asignados.
        """
        config = inspector_mut_task_config(self.current_task_data)
        current_assigned = list(inspector_config_workers_list(config))

        assigned_names = {inspector_worker_entry_name(w) for w in current_assigned}

        for name in worker_names:
            if name not in assigned_names:
                current_assigned.append(inspector_new_worker_entry(name))
                assigned_names.add(name)

        inspector_config_set_workers(config, current_assigned)
        return current_assigned

    def unassign_workers(self, worker_names: List[str]) -> List[Any]:
        """
        Quita trabajadores por nombre; devuelve la lista de asignados resultante.
        """
        config = inspector_mut_task_config(self.current_task_data)
        current_assigned = inspector_config_workers_list(config)

        updated = []
        for w in current_assigned:
            name = inspector_worker_entry_name(w)
            if name not in worker_names:
                updated.append(w)

        inspector_config_set_workers(config, updated)
        return updated

    def build_dependency_list(self, all_tasks: List[dict[str, Any]]) -> List[Tuple[str, int]]:
        """
        Lista (texto para combo, índice) para dependencias; omite la tarea actual.
        """
        if not all_tasks or not self.current_task_id:
            return []

        result = []
        for idx, t in enumerate(all_tasks):
            t_id = inspector_row_id(t)
            if t_id == self.current_task_id:
                continue
            name = inspector_row_dependency_display_name(t, idx)
            item_text = f"{idx}: {name}"
            result.append((item_text, idx))

        return result
