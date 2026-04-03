# -*- coding: utf-8 -*-
"""
Nombre del Módulo: inspector_task_payload_io
Descripcion: Lectura de filas task/config del inspector de flujo, fuera de ui/ (Fase 12C).
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping


def inspector_row_id(row: Mapping[str, Any]) -> Any:
    return row.get("id")


def inspector_row_inner_task(row: Mapping[str, Any]) -> Mapping[str, Any]:
    t = row.get("task", {})
    return t if isinstance(t, dict) else {}


def inspector_row_config(row: Mapping[str, Any]) -> Mapping[str, Any]:
    c = row.get("config", {})
    return c if isinstance(c, dict) else {}


def inspector_inner_task_name(inner: Mapping[str, Any]) -> str:
    return str(inner.get("name", "Tarea sin nombre"))


def inspector_inner_task_duration_raw(inner: Mapping[str, Any]) -> Any:
    return inner.get("duration", 0)


def inspector_config_start_condition(config: Mapping[str, Any]) -> Mapping[str, Any]:
    sc = config.get("start_condition", {})
    return sc if isinstance(sc, dict) else {}


def inspector_start_condition_type(sc: Mapping[str, Any]) -> str:
    return str(sc.get("type", "date"))


def inspector_start_condition_value(sc: Mapping[str, Any]) -> Any:
    return sc.get("value")


def inspector_config_min_predecessor_units(config: Mapping[str, Any]) -> int:
    return int(config.get("min_predecessor_units", 1))


def inspector_config_is_cycle_start(config: Mapping[str, Any]) -> bool:
    return bool(config.get("is_cycle_start", False))


def inspector_row_trigger_units(row: Mapping[str, Any]) -> int:
    return int(row.get("trigger_units", 1))


def inspector_config_units_per_cycle(config: Mapping[str, Any]) -> int:
    return int(config.get("units_per_cycle", 1))


def inspector_config_next_cyclic_index(config: Mapping[str, Any]) -> Any:
    return config.get("next_cyclic_task_index")


def inspector_config_machine_id(config: Mapping[str, Any]) -> Any:
    return config.get("machine_id")


def inspector_row_dependency_display_name(row: Mapping[str, Any], index: int) -> Any:
    inner = inspector_row_inner_task(row)
    return inner.get("name", f"Tarea {index}")


def inspector_config_workers_list(config: Mapping[str, Any]) -> list[Any]:
    w = config.get("workers", [])
    return list(w) if isinstance(w, list) else []


def inspector_worker_entry_name(entry: Any) -> str:
    if isinstance(entry, dict):
        return str(entry.get("name", ""))
    return str(entry)


def inspector_mut_task_config(task_data: MutableMapping[str, Any]) -> dict[str, Any]:
    raw = task_data.get("config")
    if isinstance(raw, dict):
        return raw
    out: dict[str, Any] = {}
    task_data["config"] = out
    return out


def inspector_config_set_workers(config: MutableMapping[str, Any], workers: list[Any]) -> None:
    config["workers"] = workers


def inspector_new_worker_entry(name: str) -> dict[str, Any]:
    return {"name": name, "rule": None}
