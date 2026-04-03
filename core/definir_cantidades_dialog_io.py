# -*- coding: utf-8 -*-
"""
Nombre del Módulo: definir_cantidades_dialog_io
Descripcion: Etiquetas de filas del plan de produccion para DefinirCantidadesDialog,
             fuera de ui/dialogs (Fase 12C).
"""

from __future__ import annotations

from typing import Any, Mapping


def _step_nested_tasks(step: Mapping[str, Any]) -> list[Any]:
    raw = step.get("tasks", [])
    return list(raw) if isinstance(raw, list) else []


def _container_inner_task(container: Mapping[str, Any]) -> Mapping[str, Any]:
    t = container.get("task", {})
    return t if isinstance(t, dict) else {}


def definir_cantidades_step_row_label(step: Mapping[str, Any]) -> str:
    if step.get("type") == "sequential_group":
        names: list[str] = []
        for item in _step_nested_tasks(step)[:2]:
            if isinstance(item, dict):
                inner = _container_inner_task(item)
                names.append(str(inner.get("name", "")))
        return f"Grupo: {', '.join(names)}..."
    inner = step.get("task", {})
    inner_d = inner if isinstance(inner, dict) else {}
    return str(inner_d.get("name", "Tarea Desconocida"))
