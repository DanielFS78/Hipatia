# -*- coding: utf-8 -*-
"""
Nombre del Módulo: flow_graph_manager_io
Descripcion: Lectura y mutacion del estado canvas/presenter usada por FlowGraphManager,
             fuera de subscripts y .get en la capa ui (Fase 12C).
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Sequence, cast

from core.flow_canvas_io import canvas_task_body, legacy_canvas_task_config


def logical_connection_indices(conn: Mapping[str, Any]) -> tuple[int, int]:
    """Indices from/to desde `get_logical_connections`."""
    return int(conn["from"]), int(conn["to"])


def logical_connection_edge_type(conn: Mapping[str, Any]) -> str:
    return str(conn["type"])


def logical_connection_highlights(conn: Mapping[str, Any]) -> tuple[bool, bool, bool, bool]:
    """highlight_parent, highlight_child, highlight_destination, highlight_origin."""
    return (
        bool(conn.get("highlight_parent")),
        bool(conn.get("highlight_child")),
        bool(conn.get("highlight_destination")),
        bool(conn.get("highlight_origin")),
    )


def flow_step_task_payload(step: Mapping[str, Any]) -> Any:
    return step.get("task")


def flow_step_position_xy(step: Mapping[str, Any], default_x: int = 50, default_y: int = 50) -> tuple[int, int]:
    p = step.get("position")
    if not isinstance(p, dict):
        return default_x, default_y
    return int(p.get("x", default_x)), int(p.get("y", default_y))


def apply_loaded_flow_step_to_presenter_config(
    config: MutableMapping[str, Any],
    step: Mapping[str, Any],
    default_units: int,
) -> None:
    """Copia campos persistidos del paso al subdict config del presenter."""
    config["workers"] = step.get("workers", [])
    config["machine_id"] = step.get("machine_id")
    config["total_units"] = step.get("trigger_units", default_units)
    config["min_predecessor_units"] = step.get("min_predecessor_units", 1)
    config["units_per_cycle"] = step.get("units_per_cycle", 1)
    config["is_cycle_start"] = step.get("is_cycle_start", False)
    config["is_cycle_end"] = step.get("is_cycle_end", False)
    config["next_cyclic_task_index"] = step.get("next_cyclic_task_index")
    config["cycle_return_to_index"] = step.get("cycle_return_to_index")

    if step.get("start_date"):
        config["start_condition"] = {"type": "date", "value": step["start_date"]}
    elif step.get("previous_task_index") is not None:
        config["start_condition"] = {
            "type": "dependency",
            "value": step["previous_task_index"],
        }


def presenter_task_data_mut(task: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    return cast(MutableMapping[str, Any], task["data"])


def presenter_task_config_mut(task: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    return cast(MutableMapping[str, Any], task["config"])


def task_data_glow_effect_get(data: Mapping[str, Any]) -> Any:
    return data.get("glow_effect_widget") if isinstance(data, Mapping) else None


def task_data_glow_effect_set(data: MutableMapping[str, Any], widget: Any) -> None:
    data["glow_effect_widget"] = widget


def task_data_glow_effect_clear(data: MutableMapping[str, Any]) -> None:
    data["glow_effect_widget"] = None


def presenter_canvas_task_effect_get(task: Mapping[str, Any], key: str) -> Any:
    return task.get(key)


def presenter_canvas_task_effect_set(task: MutableMapping[str, Any], key: str, value: Any) -> None:
    task[key] = value


def canvas_task_entry_set_position(entry: MutableMapping[str, Any], x: int, y: int) -> None:
    entry["position"] = {"x": x, "y": y}


def canvas_task_data_canvas_unique_id(entry: Mapping[str, Any]) -> Any:
    body = canvas_task_body(entry)
    if isinstance(body, Mapping):
        return body.get("canvas_unique_id")
    return getattr(body, "canvas_unique_id", None)


def flow_task_payload_is_cycle_start(payload: Mapping[str, Any]) -> bool:
    return bool(payload.get("is_cycle_start"))


def flow_task_payload_set_canvas_unique_id(payload: MutableMapping[str, Any], canvas_unique_id: int) -> None:
    payload["canvas_unique_id"] = canvas_unique_id


def worker_entry_display_name(w: Any) -> str:
    if isinstance(w, dict):
        n = w.get("name")
        return str(n) if n is not None else str(w)
    return str(w)


def inspector_context_all_tasks_rows(
    canvas_tasks: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for t in canvas_tasks:
        rows.append(
            {
                "id": canvas_task_data_canvas_unique_id(t),
                "task": canvas_task_body(t),
                "config": legacy_canvas_task_config(t),
            }
        )
    return rows
