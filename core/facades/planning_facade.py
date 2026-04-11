# -*- coding: utf-8 -*-
"""
Nombre del Módulo: core.facades.planning_facade

Descripción: Expone ``PlanningFacade`` como API estable de aplicación sobre servicios ya inyectados; no contiene reglas de persistencia directa. Integración típica con: ``__future__``, ``datetime``, ``core``.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from core.dtos import CalculationProductDTO, CalculationStepDTO, PilaDTO
from core.services.pila_service import PilaService


class PlanningFacade:
    """Punto estable para planificación; delega en ``PilaService``."""

    def __init__(self, pila_service: PilaService) -> None:
        self._service = pila_service

    @property
    def service(self) -> PilaService:
        return self._service

    def get_all_pilas(self) -> list[PilaDTO]:
        return self._service.get_all_pilas()

    def get_all_pilas_with_dates(self) -> list[PilaDTO]:
        return self._service.get_all_pilas_with_dates()

    def load_pila(
        self, pila_id: int
    ) -> tuple[PilaDTO | None, dict[Any, Any] | None, list[Any] | None, list[Any] | None]:
        return self._service.load_pila(pila_id)

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
        return self._service.save_pila(
            nombre,
            descripcion,
            pila_de_calculo,
            production_flow,
            simulation_results,
            producto_origen_codigo,
            unidades,
        )

    def delete_pila(self, pila_id: int) -> bool:
        return self._service.delete_pila(pila_id)

    def get_diario_bitacora(self, pila_id: int) -> tuple[int | None, list[Any]]:
        return self._service.get_diario_bitacora(pila_id)

    def add_diario_evento(
        self,
        pila_id: int,
        fecha: date,
        dia_numero: int,
        plan_previsto: str,
        trabajo_realizado: str,
        notas: str,
    ) -> bool:
        return self._service.add_diario_evento(
            pila_id, fecha, dia_numero, plan_previsto, trabajo_realizado, notas
        )

    def create_diario_bitacora(self, pila_id: int) -> bool:
        return self._service.create_diario_bitacora(pila_id)

    def get_data_for_calculation(self, producto_codigo: str) -> list[CalculationProductDTO]:
        return self._service.get_data_for_calculation(producto_codigo)

    def get_data_for_calculation_from_session(
        self,
        planning_session: list[CalculationProductDTO | CalculationStepDTO | dict[str, Any]],
    ) -> list[CalculationProductDTO]:
        return self._service.get_data_for_calculation_from_session(planning_session)
