# -*- coding: utf-8 -*-
"""
Nombre del Módulo: reassignment_rule_dialog_io
Descripcion: Lectura de tareas canvas y reglas de reasignacion para el dialogo,
             fuera de ui/dialogs (Fase 12C).
"""

from __future__ import annotations

from typing import Any, Mapping


def reassignment_dialog_current_task_name(task: Mapping[str, Any]) -> str:
    return str(task.get("name", ""))


def reassignment_dialog_current_task_id(task: Mapping[str, Any]) -> Any:
    return task.get("id")


def reassignment_dialog_canvas_row_data(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    d = entry.get("data")
    return d if isinstance(d, dict) else {}


def reassignment_dialog_canvas_row_task_id(entry: Mapping[str, Any]) -> Any:
    return reassignment_dialog_canvas_row_data(entry).get("id")


def reassignment_dialog_canvas_row_task_name(entry: Mapping[str, Any]) -> str:
    n = reassignment_dialog_canvas_row_data(entry).get("name")
    return str(n) if n is not None else ""


def reassignment_rule_target_task_id(rule: Mapping[str, Any]) -> Any:
    return rule.get("target_task_id")


def reassignment_rule_mode_is_parallel_join(rule: Mapping[str, Any]) -> bool:
    return rule.get("mode") == "PARALLEL_JOIN"


def reassignment_rule_is_after_units(rule: Mapping[str, Any]) -> bool:
    return rule.get("condition_type") == "AFTER_UNITS"


def reassignment_rule_condition_value_as_int(rule: Mapping[str, Any]) -> int:
    v = rule.get("condition_value")
    return int(v) if v is not None else 1
