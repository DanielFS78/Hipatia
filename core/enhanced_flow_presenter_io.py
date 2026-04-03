# -*- coding: utf-8 -*-
"""
Nombre del Módulo: enhanced_flow_presenter_io
Descripcion: Carga de flujo, biblioteca de productos y exportacion a dicts para
             FlowBuilder (ui/dialogs/production_flow/flow_builder.py), fuera de ui/dialogs (Fase 12C).
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Dict, List, Mapping, Optional, Sequence

from core.define_flow_presenter_io import find_first_positive_duration
from core.dtos import FlowTaskDataDTO, ProductFlowLibraryProductDTO
from core.flow_canvas_io import canvas_task_body, legacy_canvas_task_config


_EXPORT_TASK_DATA_EXCLUDE = frozenset({"canvas_unique_id", "glow_effect_widget"})


def flow_step_position_with_index_fallback(
    step: Mapping[str, Any],
    index: int,
    base: int = 50,
    stride: int = 30,
) -> Dict[str, int]:
    p = step.get("position")
    if not isinstance(p, dict):
        p = {}
    fx = base + index * stride
    fy = base + index * stride
    return {"x": int(p.get("x", fx)), "y": int(p.get("y", fy))}


def load_flow_widget_stub(task_data: Any, pos: Dict[str, int], is_cycle_start: bool) -> Dict[str, Any]:
    return {"data": task_data, "position": pos, "is_cycle_start": is_cycle_start}


def enhanced_parse_duration(val_raw: Any, context: str, logger: Any) -> float:
    try:
        return float(str(val_raw).replace(",", "."))
    except (ValueError, TypeError):
        logger.warning(f"Tiempo inválido en {context}")
        return 0.0


def enhanced_prepare_product_library(
    tasks_data: Sequence[Mapping[str, Any]],
    logger: Any,
) -> Dict[str, ProductFlowLibraryProductDTO]:
    structured_data: Dict[str, ProductFlowLibraryProductDTO] = {}
    for main_task in tasks_data:
        product_code = str(main_task.get("codigo", "N/A"))
        fab_id = main_task.get("fabricacion_id", "N/A")
        desc_main = str(main_task.get("descripcion", "Sin descripción"))
        orig_info: dict[str, str] = {"desc": desc_main}

        structured_data[product_code] = ProductFlowLibraryProductDTO(
            descripcion=str(main_task.get("descripcion", "")),
        )
        bucket = structured_data[product_code].tasks

        if not main_task.get("tiene_subfabricaciones"):
            task_name = str(main_task.get("descripcion", "Tarea de producto simple"))
            duration = enhanced_parse_duration(main_task.get("tiempo_optimo", 0.0), product_code, logger)
            task_id = f"{product_code}_main_task"
            try:
                ttipo = int(main_task.get("tipo_trabajador", 1))
            except (TypeError, ValueError):
                ttipo = 1
            bucket.append(
                FlowTaskDataDTO(
                    id=task_id,
                    name=task_name,
                    duration=duration,
                    duration_per_unit=duration,
                    department=str(main_task.get("departamento", "General")),
                    requiere_maquina_tipo=None,
                    tipo_trabajador=ttipo,
                    fabricacion_id=fab_id,
                    original_product_code=product_code,
                    original_product_info=orig_info,
                    deadline=main_task.get("deadline"),
                )
            )

        elif main_task.get("sub_partes"):
            sub_partes = main_task.get("sub_partes", [])
            if isinstance(sub_partes, list):
                for i, sub_task in enumerate(sub_partes):
                    if not isinstance(sub_task, dict):
                        continue
                    task_name = str(sub_task.get("descripcion", "Tarea sin nombre"))
                    duration = find_first_positive_duration(sub_task, ("tiempo", "duration"))
                    task_id = f"{product_code}_{i}_{task_name.replace(' ', '_')}"
                    try:
                        sttipo = int(sub_task.get("tipo_trabajador", 1))
                    except (TypeError, ValueError):
                        sttipo = 1
                    bucket.append(
                        FlowTaskDataDTO(
                            id=task_id,
                            name=task_name,
                            duration=duration,
                            duration_per_unit=duration,
                            department=str(main_task.get("departamento", "General")),
                            requiere_maquina_tipo=sub_task.get("requiere_maquina_tipo"),
                            tipo_trabajador=sttipo,
                            fabricacion_id=fab_id,
                            original_product_code=product_code,
                            original_product_info=orig_info,
                            deadline=main_task.get("deadline"),
                        )
                    )

    return structured_data


def resolve_start_date_from_condition(
    start_cond: Mapping[str, Any],
    schedule_config: Any,
) -> Optional[datetime]:
    if start_cond.get("type") != "date" or not start_cond.get("value"):
        return None

    value = start_cond["value"]
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        start_time_config = (
            getattr(schedule_config, "WORK_START_TIME", time(8, 0)) if schedule_config else time(8, 0)
        )
        return datetime.combine(value, start_time_config)
    return None


def normalize_worker_entries(config_workers: List[Any]) -> List[Dict[str, Any]]:
    if not config_workers:
        return []
    if isinstance(config_workers[0], dict):
        return [w.copy() for w in config_workers]
    return [{"name": str(w), "reassignment_rule": None} for w in config_workers]


def _canvas_entry_position(entry: Mapping[str, Any]) -> Dict[str, int]:
    p = entry.get("position", {"x": 0, "y": 0})
    if not isinstance(p, dict):
        return {"x": 0, "y": 0}
    return {"x": int(p.get("x", 0)), "y": int(p.get("y", 0))}


def _task_body_for_export(body: Mapping[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in body.items() if k not in _EXPORT_TASK_DATA_EXCLUDE}


def canvas_task_to_export_step(
    canvas_task: Mapping[str, Any],
    default_units: int,
    schedule_config: Any,
) -> Optional[Dict[str, Any]]:
    task_data_original = canvas_task_body(canvas_task)
    if not isinstance(task_data_original, Mapping) or not task_data_original:
        return None

    task_config = legacy_canvas_task_config(canvas_task)
    widget_pos = _canvas_entry_position(canvas_task)

    start_cond_raw = task_config.get("start_condition", {})
    start_cond = start_cond_raw if isinstance(start_cond_raw, dict) else {}

    start_date_value = resolve_start_date_from_condition(start_cond, schedule_config)

    previous_task_index = None
    if start_cond.get("type") == "dependency":
        previous_task_index = start_cond.get("value")

    wr = task_config.get("workers", [])
    workers_list: List[Any] = [] if wr is None else list(wr) if isinstance(wr, list) else []

    return {
        "task": _task_body_for_export(task_data_original),
        "workers": normalize_worker_entries(workers_list),
        "machine_id": task_config.get("machine_id"),
        "trigger_units": task_config.get("total_units", default_units),
        "min_predecessor_units": task_config.get("min_predecessor_units", 1),
        "units_per_cycle": task_config.get("units_per_cycle", 1),
        "next_cyclic_task_index": task_config.get("next_cyclic_task_index"),
        "is_cycle_start": task_config.get("is_cycle_start", False),
        "is_cycle_end": task_config.get("is_cycle_end", False),
        "cycle_return_to_index": task_config.get("cycle_return_to_index"),
        "start_date": start_date_value,
        "previous_task_index": previous_task_index,
        "position": widget_pos,
    }
