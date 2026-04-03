# -*- coding: utf-8 -*-
"""Puente de compatibilidad para la API legacy de reportes, lotes y sistema."""

from __future__ import annotations

from typing import Any

from core.reports_dtos import (
    IncidenciaResumenDTO,
    OrdenFabricacionDetalleDTO,
    OrdenFabricacionResumenDTO,
    PromedioTiempoDTO,
    PuntoEvolucionDTO,
    ResultadoBusquedaDTO,
    ResumenProductoDTO,
    TiempoTrabajadorDTO,
)
from core.dtos import LoteDTO
from core.services.report_service import ReportService
from core.services.system_integration_service import SystemIntegrationService


class AppModelCompatBridge:
    """Reporting vía ``ReportService``; lotes/config/órdenes vía ``SystemIntegrationService``."""

    def __init__(
        self,
        reporting_facade: ReportService,
        system_facade: SystemIntegrationService,
    ) -> None:
        self.reporting_facade = reporting_facade
        self.system_facade = system_facade

    def search_reports_data(self, query: str) -> list[ResultadoBusquedaDTO]:
        return self.reporting_facade.search_reports_data(query)

    def get_orders_for_product(self, product_code: str) -> list[OrdenFabricacionResumenDTO]:
        return self.reporting_facade.get_orders_for_product(product_code)

    def get_order_details(self, order_id: str) -> OrdenFabricacionDetalleDTO | None:
        return self.reporting_facade.get_order_details(order_id)

    def get_product_time_stats(self, product_code: str) -> PromedioTiempoDTO | None:
        return self.reporting_facade.get_product_time_stats(product_code)

    def get_worker_time_stats(self, product_code: str) -> list[TiempoTrabajadorDTO]:
        return self.reporting_facade.get_worker_time_stats(product_code)

    def get_incidents_stats(self, product_code: str) -> list[IncidenciaResumenDTO]:
        return self.reporting_facade.get_incidents_stats(product_code)

    def get_evolution_stats(self, product_code: str, days: int = 30) -> list[PuntoEvolucionDTO]:
        return self.reporting_facade.get_evolution_stats(product_code, days)

    def get_product_summary(self, product_code: str) -> ResumenProductoDTO | None:
        return self.reporting_facade.get_product_summary(product_code)

    def search_lotes(self, query: str) -> list[Any]:
        return self.system_facade.search_lotes(query)

    def create_lote(self, data: dict[str, Any]) -> int | None:
        return self.system_facade.create_lote(data)

    def get_lote_details(self, lote_id: int) -> LoteDTO | None:
        return self.system_facade.get_lote_details(lote_id)

    def update_lote(self, lote_id: int, data: dict[str, Any]) -> bool:
        return self.system_facade.update_lote(lote_id, data)

    def delete_lote(self, lote_id: int) -> bool:
        return self.system_facade.delete_lote(lote_id)

    def config_get_setting(self, key: str, default: str) -> str:
        return self.system_facade.config_get_setting(key, default)

    def config_set_setting(self, key: str, value: str) -> bool:
        return self.system_facade.config_set_setting(key, value)

    def get_all_ordenes_fabricacion(self) -> list[str]:
        return self.system_facade.get_all_ordenes_fabricacion()
