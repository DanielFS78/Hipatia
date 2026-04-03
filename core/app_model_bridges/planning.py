# -*- coding: utf-8 -*-
"""Puente de compatibilidad para operaciones de planificación / pilas."""

from __future__ import annotations

from datetime import date
from typing import Any

from core.dtos import CalculationProductDTO, PilaDTO
from core.facades.planning_facade import PlanningFacade


class AppModelPlanningBridge:
    """Delega en :class:`PlanningFacade` (API estable hacia planificación)."""

    def __init__(self, planning_facade: PlanningFacade) -> None:
        self.planning_facade = planning_facade

    def get_all_pilas(self) -> list[PilaDTO]:
        return self.planning_facade.get_all_pilas()

    def get_all_pilas_with_dates(self) -> list[PilaDTO]:
        return self.planning_facade.get_all_pilas_with_dates()

    def load_pila(
        self, pila_id: int
    ) -> tuple[PilaDTO | None, dict[Any, Any] | None, list[Any] | None, list[Any] | None]:
        return self.planning_facade.load_pila(pila_id)

    def save_pila(
        self,
        nombre: str,
        descripcion: str,
        pila_de_calculo: dict[str, Any],
        production_flow: list[Any],
        simulation_results: list[Any],
        producto_origen_codigo: str | None = None,
        unidades: int = 1,
    ) -> str | bool | int:
        return self.planning_facade.save_pila(
            nombre,
            descripcion,
            pila_de_calculo,
            production_flow,
            simulation_results,
            producto_origen_codigo,
            unidades,
        )

    def delete_pila(self, pila_id: int) -> bool:
        return self.planning_facade.delete_pila(pila_id)

    def get_diario_bitacora(self, pila_id: int) -> tuple[int | None, list[Any]]:
        return self.planning_facade.get_diario_bitacora(pila_id)

    def add_diario_evento(
        self,
        pila_id: int,
        fecha: date,
        dia_numero: int,
        plan_previsto: str,
        trabajo_realizado: str,
        notas: str,
    ) -> bool:
        return self.planning_facade.add_diario_evento(
            pila_id, fecha, dia_numero, plan_previsto, trabajo_realizado, notas
        )

    def create_diario_bitacora(self, pila_id: int) -> bool:
        return self.planning_facade.create_diario_bitacora(pila_id)

    def get_data_for_calculation(self, producto_codigo: str) -> list[CalculationProductDTO]:
        return self.planning_facade.get_data_for_calculation(producto_codigo)

    def get_data_for_calculation_from_session(
        self, planning_session: list[CalculationProductDTO | dict[str, Any]]
    ) -> list[CalculationProductDTO]:
        return self.planning_facade.get_data_for_calculation_from_session(planning_session)
