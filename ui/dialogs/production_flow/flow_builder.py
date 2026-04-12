# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.production_flow.flow_builder

Descripción: Construcción y serialización de flujos de producción (composición con ``EnhancedFlowPresenter``).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from core.enhanced_flow_presenter_io import (
    canvas_task_to_export_step,
    enhanced_parse_duration,
    enhanced_prepare_product_library,
    flow_step_position_with_index_fallback,
    load_flow_widget_stub,
    normalize_worker_entries,
    resolve_start_date_from_condition,
)
from core.flow_graph_manager_io import (
    apply_loaded_flow_step_to_presenter_config,
    flow_step_task_payload,
    presenter_task_config_mut,
)
from core.flow_canvas_io import flow_task_config_is_cycle_start_flag
from core.dtos import ProductFlowLibraryProductDTO


class FlowBuilder:
    """Carga/reconstrucción de estado y construcción/preparación de flujos (delegado por el presenter)."""

    def __init__(self, presenter: Any) -> None:
        self._p = presenter

    def load_flow(self, flow_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Inicializa el estado del Presenter desde datos externos.
        Retorna lista de tareas procesadas con posiciones para que la vista cree los widgets.
        """
        p = self._p
        p.clear_tasks()
        processed_tasks: List[Dict[str, Any]] = []

        for i, step in enumerate(flow_data):
            task_data = flow_step_task_payload(step)
            if not task_data:
                continue

            pos = flow_step_position_with_index_fallback(step, i)
            entry, _new_index = p.add_task(task_data, pos)
            config = presenter_task_config_mut(entry)
            apply_loaded_flow_step_to_presenter_config(config, step, p.default_units)

            processed_tasks.append(
                load_flow_widget_stub(
                    task_data,
                    pos,
                    flow_task_config_is_cycle_start_flag(config),
                )
            )

        return processed_tasks

    def prepare_task_data(self, tasks_data: List[Dict[str, Any]]) -> Dict[str, ProductFlowLibraryProductDTO]:
        """Organiza la lista plana de tareas primarias en DTOs agrupados por producto."""
        return enhanced_prepare_product_library(tasks_data, self._p.logger)

    def _parse_duration(self, val_raw: Any, context: str) -> float:
        return enhanced_parse_duration(val_raw, context, self._p.logger)

    def resolve_start_date(self, start_cond: Dict[str, Any]) -> Optional[datetime]:
        return resolve_start_date_from_condition(start_cond, self._p.schedule_config)

    def normalize_workers(self, config_workers: List[Any]) -> List[Dict[str, Any]]:
        return normalize_worker_entries(config_workers)

    def build_production_flow(self, tasks_to_build: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Construye el flujo final extraído del estado lógico o de la lista proporcionada."""
        p = self._p
        final_flow: List[Dict[str, Any]] = []
        source_tasks = tasks_to_build if tasks_to_build is not None else p.canvas_tasks

        for i, canvas_task in enumerate(source_tasks):
            step = canvas_task_to_export_step(
                canvas_task, p.default_units, p.schedule_config
            )
            if step is None:
                p.logger.warning(f"Saltando tarea inválida en índice {i}.")
                continue
            final_flow.append(step)

        p.logger.info(f"Flujo construido: {len(final_flow)} tareas.")
        return final_flow
