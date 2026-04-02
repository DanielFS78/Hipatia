# -*- coding: utf-8 -*-
"""
Nombre del Módulo: flow_dialog_bridges
Descripcion: Extraccion de campos desde dicts de dialogos y tareas del canvas,
             para mantener ui/dialogs/production_flow sin accesos .get/[] innecesarios.
"""

from __future__ import annotations

from typing import Any, Mapping


def canvas_task_body(task: Mapping[str, Any]) -> Any:
    """Cuerpo `data` de una entrada `presenter.canvas_tasks[i]`."""
    return task.get("data")


def canvas_task_display_name(task: Mapping[str, Any], fallback: str) -> str:
    """Nombre de tarea para listas de dialogo (`data` dict o DTO con `.name`)."""
    body = canvas_task_body(task)
    if isinstance(body, Mapping):
        n = body.get("name", fallback)
        return str(n) if n is not None else fallback
    name_attr = getattr(body, "name", None)
    if name_attr is not None:
        return str(name_attr)
    return fallback


def flow_task_config_is_cycle_end_flag(cfg: Mapping[str, Any]) -> bool:
    """True si config marca fin de ciclo."""
    return bool(cfg.get("is_cycle_end", False))


def flow_task_config_is_cycle_start_flag(cfg: Mapping[str, Any]) -> bool:
    """True si config marca inicio de ciclo."""
    return bool(cfg.get("is_cycle_start", False))

