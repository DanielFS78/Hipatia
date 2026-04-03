# -*- coding: utf-8 -*-
"""
Nombre del Módulo: define_flow_form_io
Descripcion: Convierte el dict devuelto por DefineControlPanel.get_form_data en
             FlowTaskConfigDTO, fuera de la capa ui (Fase 12C).
"""

from __future__ import annotations

from typing import Any, Mapping

from core.dtos import FlowTaskConfigDTO


def define_form_data_to_flow_task_config(
    form_data: Mapping[str, Any],
    total_units: int,
) -> FlowTaskConfigDTO:
    """Arma el DTO de configuracion desde el mapa del panel de definicion."""
    workers_raw = form_data.get("workers", [])
    workers = list(workers_raw) if workers_raw is not None else []

    mpu = form_data.get("min_predecessor_units", 1)
    if not isinstance(mpu, int):
        try:
            mpu = int(mpu)
        except (TypeError, ValueError):
            mpu = 1

    return FlowTaskConfigDTO(
        workers=workers,
        machine_id=form_data.get("machine_id"),
        start_condition_type=str(form_data.get("start_condition_type", "date")),
        start_condition_date=form_data.get("start_condition_date"),
        previous_task_index=form_data.get("previous_task_index"),
        depends_on_worker=form_data.get("depends_on_worker"),
        total_units=total_units,
        min_predecessor_units=mpu,
    )
