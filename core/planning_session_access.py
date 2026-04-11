# -*- coding: utf-8 -*-
"""
Nombre del Módulo: core.planning_session_access

Descripción: Funciones puras de apoyo (sin estado de proceso): ``planning_unidades``, ``planning_identificador``, ``planning_deadline``, ``planning_lote_codigo``, ``deadline_to_date``. Integración típica con: ``__future__``, ``datetime``, ``core``.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from core.dtos import CalculationProductDTO, CalculationStepDTO


def planning_unidades(item: Any, default: int = 1) -> int:
    """Unidades de fabricación asociadas al ítem de sesión."""
    if isinstance(item, dict):
        try:
            return int(item.get("unidades", default))
        except (TypeError, ValueError):
            return default
    if isinstance(item, CalculationStepDTO):
        return int(item.unidades)
    if isinstance(item, CalculationProductDTO):
        u = getattr(item, "units_for_this_instance", default)
        try:
            return int(u) if u is not None else default
        except (TypeError, ValueError):
            return default
    return default


def planning_identificador(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("identificador") or "")
    if isinstance(item, CalculationStepDTO):
        return str(item.identificador or "")
    if isinstance(item, CalculationProductDTO):
        return str(item.codigo or "")
    return ""


def planning_deadline(item: Any) -> datetime | date | None:
    if isinstance(item, dict):
        return item.get("deadline")
    if isinstance(item, CalculationStepDTO):
        return item.deadline
    if isinstance(item, CalculationProductDTO):
        return item.deadline
    return None


def planning_lote_codigo(item: Any, default: str = "N/A") -> str:
    if isinstance(item, dict):
        return str(item.get("lote_codigo", default))
    if isinstance(item, CalculationStepDTO):
        return str(item.lote_codigo or default)
    if isinstance(item, CalculationProductDTO):
        return str(item.codigo or default)
    return default


def deadline_to_date(d: datetime | date | None) -> date | None:
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.date()
    return d
