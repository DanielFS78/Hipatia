"""
Carga de datos en `ProductionTaskInspector` (set_task).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from PyQt6.QtCore import QDate, QDateTime, QTime

from core.inspector_task_payload_io import (
    inspector_config_is_cycle_start,
    inspector_config_machine_id,
    inspector_config_min_predecessor_units,
    inspector_config_next_cyclic_index,
    inspector_config_start_condition,
    inspector_config_units_per_cycle,
    inspector_inner_task_duration_raw,
    inspector_inner_task_name,
    inspector_row_config,
    inspector_row_inner_task,
    inspector_row_trigger_units,
    inspector_start_condition_type,
    inspector_start_condition_value,
)
from ui.widgets.production_flow.inspector_ui import InspectorWidgets


def apply_task_to_widgets(
    *,
    task_data: dict[str, Any],
    widgets: InspectorWidgets,
    presenter: Any,
    all_tasks: list[Any] | None,
    machines: list[Any] | None,
    available_workers: list[str] | None,
) -> tuple[str | None, dict[str, Any] | None]:
    """
    Aplica `task_data` a los widgets del inspector y sincroniza presenter.
    Retorna (current_task_id, current_task_data).
    """
    presenter.set_task(task_data, available_workers)
    current_task_id = presenter.current_task_id
    current_task_data = presenter.current_task_data

    task_inner = inspector_row_inner_task(task_data)
    widgets.title.setText(inspector_inner_task_name(task_inner))
    duration = inspector_inner_task_duration_raw(task_inner)
    widgets.duration_label.setText(f"Duración: {duration} min")

    config = inspector_row_config(task_data)
    start_cond = inspector_config_start_condition(config)
    sc_type = inspector_start_condition_type(start_cond)

    if sc_type == "date":
        widgets.start_date_radio.setChecked(True)
        dt_val = inspector_start_condition_value(start_cond)
        if isinstance(dt_val, QDateTime):
            widgets.start_date_edit.setDateTime(dt_val)
        elif isinstance(dt_val, datetime):
            widgets.start_date_edit.setDateTime(dt_val)
        elif isinstance(dt_val, QDate):
            widgets.start_date_edit.setDateTime(QDateTime(dt_val, QTime(0, 0, 0)))
        else:
            widgets.start_date_edit.setDateTime(QDateTime.currentDateTime())
    else:
        widgets.dependency_radio.setChecked(True)

    widgets.dependency_combo.clear()
    widgets.next_cyclic_combo.clear()
    widgets.next_cyclic_combo.addItem(" - Ninguna - ", None)

    if all_tasks:
        dep_list = presenter.build_dependency_list(all_tasks)
        for item_text, idx in dep_list:
            widgets.dependency_combo.addItem(item_text, idx)
            widgets.next_cyclic_combo.addItem(item_text, idx)

    if sc_type == "dependency":
        dep_idx = inspector_start_condition_value(start_cond)
        if dep_idx is not None:
            idx = widgets.dependency_combo.findData(dep_idx)
            if idx >= 0:
                widgets.dependency_combo.setCurrentIndex(idx)

    widgets.min_units_spin.setValue(inspector_config_min_predecessor_units(config))
    widgets.cycle_start_cb.setChecked(inspector_config_is_cycle_start(config))

    widgets.units_spin.setValue(inspector_row_trigger_units(task_data))
    widgets.units_per_cycle_spin.setValue(inspector_config_units_per_cycle(config))

    next_cyclic = inspector_config_next_cyclic_index(config)
    if next_cyclic is not None:
        idx = widgets.next_cyclic_combo.findData(next_cyclic)
        if idx >= 0:
            widgets.next_cyclic_combo.setCurrentIndex(idx)

    widgets.machine_combo.clear()
    widgets.machine_combo.addItem(" - Ninguna - ", None)
    if machines:
        for m in machines:
            m_id = getattr(m, "id", None)
            m_name = getattr(m, "nombre", None)
            if m_id is None or m_name is None:
                continue
            widgets.machine_combo.addItem(str(m_name), int(m_id))

    current_machine = inspector_config_machine_id(config)
    if current_machine:
        idx = widgets.machine_combo.findData(current_machine)
        if idx >= 0:
            widgets.machine_combo.setCurrentIndex(idx)

    return current_task_id, current_task_data
