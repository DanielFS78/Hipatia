# -*- coding: utf-8 -*-
"""
Nombre del Módulo: flow_card_labels
Descripcion: Textos para tarjetas del canvas de flujo; lectura de mapas de tarea
             fuera de ui/ (Fase 12C).
"""

from __future__ import annotations

from typing import Any, Mapping


def flow_card_primary_html(task: Mapping[str, Any]) -> str:
    """HTML principal nombre + duracion."""
    name = str(task.get("name", "Tarea"))
    try:
        duration = float(task.get("duration", 0.0) or 0.0)
    except (TypeError, ValueError):
        duration = 0.0
    return f"<b>{name}</b>\n<small>{duration:.2f} min</small>"


def flow_card_task_id_str(task: Mapping[str, Any]) -> str:
    """Identificador logico de la tarea para señales."""
    return str(task.get("id", ""))


def flow_card_with_workers_html(task: Mapping[str, Any], worker_names: list[str]) -> tuple[str, str]:
    """
    Returns:
        (texto QLabel, tooltip)
    """
    base = flow_card_primary_html(task)
    if worker_names:
        workers_str = ", ".join(worker_names)
        return (
            f"{base}\n<small style='color:blue'>👥 {len(worker_names)}</small>",
            f"Trabajadores: {workers_str}",
        )
    return base, "Sin trabajadores asignados"
