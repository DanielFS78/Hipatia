# -*- coding: utf-8 -*-
"""
Nombre del Módulo: enhanced_flow_canvas_state_io
Descripcion: Mutaciones y consultas sobre entradas `canvas_tasks` del flujo
             enhanced (data/config/position), fuera de ui/dialogs (Fase 12C).
"""

from __future__ import annotations

from datetime import date
from typing import Any, List, Mapping, MutableMapping, Optional

from core.flow_canvas_io import (
    canvas_task_body,
    canvas_task_display_name,
    legacy_canvas_task_config,
)
from core.inspector_task_payload_io import (
    inspector_config_next_cyclic_index,
    inspector_config_start_condition,
    inspector_start_condition_type,
    inspector_start_condition_value,
)


def canvas_state_mut_config(task_entry: MutableMapping[str, Any]) -> dict[str, Any]:
    raw = task_entry.get("config")
    if isinstance(raw, dict):
        return raw
    out: dict[str, Any] = {}
    task_entry["config"] = out
    return out


def canvas_state_set_config_key(task_entry: MutableMapping[str, Any], key: str, value: Any) -> None:
    canvas_state_mut_config(task_entry)[key] = value


def canvas_state_reindex_after_remove(
    canvas_tasks: List[dict[str, Any]],
    removed_index: int,
    today: date,
) -> None:
    for task in canvas_tasks:
        config = canvas_state_mut_config(task)
        cond_raw = config.get("start_condition", {})
        if isinstance(cond_raw, dict) and cond_raw.get("type") == "dependency":
            dep_idx = cond_raw["value"]
            if dep_idx == removed_index:
                config["start_condition"] = {"type": "date", "value": today}
            elif dep_idx > removed_index:
                cond_raw["value"] = dep_idx - 1

        next_cyclic = config.get("next_cyclic_task_index")
        if next_cyclic is not None:
            if next_cyclic == removed_index:
                config["next_cyclic_task_index"] = None
            elif next_cyclic > removed_index:
                config["next_cyclic_task_index"] = next_cyclic - 1

        return_idx = config.get("cycle_return_to_index")
        if return_idx is not None:
            if return_idx == removed_index:
                config["cycle_return_to_index"] = None
            elif return_idx > removed_index:
                config["cycle_return_to_index"] = return_idx - 1


def canvas_state_apply_cycle_end(
    task_config: MutableMapping[str, Any],
    is_cycle_end: bool,
    return_to_index: Optional[int],
) -> None:
    previous_return_index = task_config.get("cycle_return_to_index")
    task_config["is_cycle_end"] = is_cycle_end
    task_config["cycle_return_to_index"] = return_to_index

    if is_cycle_end and return_to_index is not None:
        task_config["next_cyclic_task_index"] = return_to_index
    elif (not is_cycle_end) or return_to_index is None:
        if task_config.get("next_cyclic_task_index") == previous_return_index:
            task_config["next_cyclic_task_index"] = None


def canvas_state_find_worker_by_name(
    task_entry: Mapping[str, Any],
    worker_name: str,
) -> Optional[dict[str, Any]]:
    clean_name = worker_name.replace(" 🔧", "").strip()
    config = legacy_canvas_task_config(task_entry)
    workers = config.get("workers", [])
    if not isinstance(workers, list):
        return None
    for w in workers:
        if isinstance(w, dict) and w.get("name") == clean_name:
            return w
    return None


def canvas_state_inspector_view(
    canvas_tasks: List[dict[str, Any]],
    task_index: int,
) -> dict[str, Any]:
    if not (0 <= task_index < len(canvas_tasks)):
        return {}
    selected_task = canvas_tasks[task_index]
    possible_predecessors: list[tuple[int, Any]] = []
    for i, t in enumerate(canvas_tasks):
        if i == task_index:
            continue
        body = canvas_task_body(t)
        if isinstance(body, Mapping):
            possible_predecessors.append((i, body.get("name")))
        else:
            possible_predecessors.append((i, getattr(body, "name", None)))
    return {"selected_task": selected_task, "possible_predecessors": possible_predecessors}


def canvas_state_simulation_progress_text(
    canvas_tasks: List[dict[str, Any]],
    current_idx: int,
) -> str:
    if not (0 <= current_idx < len(canvas_tasks)):
        return "Simulación..."
    entry = canvas_tasks[current_idx]
    task_name = canvas_task_display_name(entry, "Tarea")
    total_tasks = len(canvas_tasks)
    return f"Procesando: {task_name} ({current_idx + 1}/{total_tasks})"


def canvas_state_logical_connections_for_index(
    canvas_tasks: List[dict[str, Any]],
    selected_index: int,
) -> List[dict[str, Any]]:
    if not (0 <= selected_index < len(canvas_tasks)):
        return []

    connections: List[dict[str, Any]] = []
    n = len(canvas_tasks)
    task_config = legacy_canvas_task_config(canvas_tasks[selected_index])
    start_cond = inspector_config_start_condition(task_config)

    if inspector_start_condition_type(start_cond) == "dependency":
        parent_idx = inspector_start_condition_value(start_cond)
        if parent_idx is not None and 0 <= parent_idx < n:
            connections.append(
                {"from": parent_idx, "to": selected_index, "type": "standard", "highlight_parent": True}
            )

    for i, t in enumerate(canvas_tasks):
        t_cfg = legacy_canvas_task_config(t)
        t_cond = inspector_config_start_condition(t_cfg)
        if inspector_start_condition_type(t_cond) == "dependency":
            v = inspector_start_condition_value(t_cond)
            if v == selected_index:
                connections.append(
                    {"from": selected_index, "to": i, "type": "standard", "highlight_child": True}
                )

    next_cyclic = inspector_config_next_cyclic_index(task_config)
    if next_cyclic is not None and 0 <= next_cyclic < n:
        connections.append(
            {
                "from": selected_index,
                "to": next_cyclic,
                "type": "cyclic",
                "highlight_destination": True,
            }
        )

    for i, t in enumerate(canvas_tasks):
        t_cfg = legacy_canvas_task_config(t)
        nc = inspector_config_next_cyclic_index(t_cfg)
        if nc == selected_index:
            connections.append({"from": i, "to": selected_index, "type": "cyclic", "highlight_origin": True})

    return connections
