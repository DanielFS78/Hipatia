# -*- coding: utf-8 -*-
"""
Nombre del Módulo: define_flow_presenter_io
Descripcion: Lectura de mapas de producto/tarea/paso y conversion legacy a DTOs
             para DefineFlowPresenter, fuera de ui/dialogs (Fase 12C).
"""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping, MutableMapping, Sequence

from core.dtos import FlowTaskConfigDTO, FlowTaskDataDTO, ProductionFlowStepDTO


def main_task_product_code(main_task: Mapping[str, Any]) -> str:
    return str(main_task.get("codigo", "N/A"))


def main_task_desc_for_library(main_task: Mapping[str, Any]) -> str:
    return str(main_task.get("descripcion", "Producto sin descripcion"))


def main_task_descripcion_producto(main_task: Mapping[str, Any]) -> str:
    return str(main_task.get("descripcion", ""))


def main_task_iterate_sub_partes(main_task: Mapping[str, Any]) -> bool:
    return bool(main_task.get("tiene_subfabricaciones") and main_task.get("sub_partes"))


def main_task_sub_partes_sequence(main_task: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw = main_task.get("sub_partes", [])
    if not isinstance(raw, list):
        return []
    out: list[Mapping[str, Any]] = []
    for item in raw:
        if isinstance(item, Mapping):
            out.append(item)
    return out


def main_task_departamento(main_task: Mapping[str, Any]) -> str:
    return str(main_task.get("departamento", "General"))


def main_task_fabricacion_id(main_task: Mapping[str, Any]) -> Any:
    return main_task.get("fabricacion_id", "N/A")


def main_task_deadline(main_task: Mapping[str, Any]) -> Any:
    return main_task.get("deadline")


def sub_task_display_name(sub_task: Mapping[str, Any]) -> str:
    return str(sub_task.get("descripcion", sub_task.get("name", "Tarea sin nombre")))


def sub_task_requiere_maquina_tipo(sub_task: Mapping[str, Any]) -> Any:
    return sub_task.get("requiere_maquina_tipo")


def sub_task_tipo_trabajador(sub_task: Mapping[str, Any]) -> int:
    return int(sub_task.get("tipo_trabajador", 1))


def find_first_positive_duration(sub_task: Mapping[str, Any], keys: Sequence[str]) -> float:
    """Primera clave con valor float > 0 (misma logica que el presenter legacy)."""
    for key in keys:
        if key not in sub_task:
            continue
        try:
            val_str = str(sub_task[key]).strip()
            if val_str:
                val = float(val_str.replace(",", "."))
                if val > 0:
                    return val
        except (ValueError, TypeError):
            continue
    return 0.0


def legacy_step_task_mapping(step_dict: Mapping[str, Any]) -> MutableMapping[str, Any]:
    t = step_dict.get("task", {})
    if isinstance(t, MutableMapping):
        return t
    if isinstance(t, Mapping):
        return dict(t)
    return {}


def flow_task_data_from_legacy_step_task(task_dict: Mapping[str, Any]) -> FlowTaskDataDTO:
    """DTO de tarea desde el dict anidado en un paso de flujo persistido."""
    return FlowTaskDataDTO(
        id=str(task_dict.get("id", "")),
        name=str(task_dict.get("name", "")),
        duration=float(task_dict.get("duration", 0.0)),
        duration_per_unit=float(task_dict.get("duration", 0.0)),
        department=str(task_dict.get("department", "General")),
        requiere_maquina_tipo=task_dict.get("requiere_maquina_tipo"),
        tipo_trabajador=int(task_dict.get("tipo_trabajador", 1)),
        original_product_code=str(task_dict.get("original_product_code", "")),
        fabricacion_id=task_dict.get("fabricacion_id", "N/A"),
    )


def flow_task_config_from_legacy_step(step_dict: Mapping[str, Any]) -> FlowTaskConfigDTO:
    """DTO de config desde un paso de flujo persistido (dict plano)."""
    prev = step_dict.get("previous_task_index")
    wr = step_dict.get("workers", [])
    workers: list[Any] = [] if wr is None else list(wr)
    return FlowTaskConfigDTO(
        workers=workers,
        machine_id=step_dict.get("machine_id"),
        start_condition_type="dependency" if prev is not None else "date",
        start_condition_date=step_dict.get("start_date", date.today()),
        previous_task_index=prev,
        depends_on_worker=step_dict.get("depends_on_worker"),
        total_units=int(step_dict.get("total_units", 1)),
        units_per_cycle=int(step_dict.get("units_per_cycle", 1)),
    )


def legacy_step_dict_to_production_step(step_dict: Mapping[str, Any]) -> ProductionFlowStepDTO:
    td = legacy_step_task_mapping(step_dict)
    return ProductionFlowStepDTO(
        task=flow_task_data_from_legacy_step_task(td),
        config=flow_task_config_from_legacy_step(step_dict),
    )


def legacy_flow_list_to_production_steps(
    flow: Sequence[Mapping[str, Any]],
) -> list[ProductionFlowStepDTO]:
    return [legacy_step_dict_to_production_step(s) for s in flow]
