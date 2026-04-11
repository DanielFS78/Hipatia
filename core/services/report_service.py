# -*- coding: utf-8 -*-
"""
Nombre del Módulo: report_service
Descripción: Informes y estadísticas de producción (órdenes, tiempos, incidencias, evolución).

Interfaz delgada entre controladores de informes y ``ReportsRepository``; los DTOs de
salida viven en ``core.reports_dtos``.
"""

from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QObject

from core.reports_dtos import (ResultadoBusquedaDTO, OrdenFabricacionResumenDTO, OrdenFabricacionDetalleDTO,
                       PromedioTiempoDTO, TiempoTrabajadorDTO, IncidenciaResumenDTO,
                       PuntoEvolucionDTO, UnidadTrabajoDTO, ResumenProductoDTO)
from database.database_manager import DatabaseManager

if TYPE_CHECKING:
    from database.repositories.reports import ReportsRepository

class ReportService(QObject):
    """
    Servicio de dominio para gestionar Reportes y Estadísticas.
    Actúa como interfaz entre la UI/Controladores y el repositorio de reportes.
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db = db_manager

    @property
    def reports_repo(self) -> "ReportsRepository":
        return self.db.reports_repo

    def search_reports_data(self, query: str) -> list[ResultadoBusquedaDTO]:
        return self.reports_repo.buscar_por_codigo(query)

    def get_orders_for_product(self, product_code: str) -> list[OrdenFabricacionResumenDTO]:
        return self.reports_repo.obtener_ordenes_por_producto(product_code)

    def get_order_details(self, order_id: str) -> OrdenFabricacionDetalleDTO | None:
        return self.reports_repo.obtener_detalle_orden(order_id)

    def get_product_time_stats(self, product_code: str) -> PromedioTiempoDTO | None:
        return self.reports_repo.calcular_promedio_tiempo_unidad(product_code)

    def get_worker_time_stats(self, product_code: str) -> list[TiempoTrabajadorDTO]:
        return self.reports_repo.obtener_tiempos_por_trabajador(product_code)

    def get_incidents_stats(self, product_code: str) -> list[IncidenciaResumenDTO]:
        return self.reports_repo.obtener_incidencias_por_producto(product_code)

    def get_evolution_stats(self, product_code: str, days: int = 30) -> list[PuntoEvolucionDTO]:
        return self.reports_repo.obtener_evolucion_temporal(product_code, days)

    def get_product_summary(self, product_code: str) -> ResumenProductoDTO | None:
        return self.reports_repo.obtener_resumen_producto(product_code)

    def get_order_units(self, order_id: str) -> list[UnidadTrabajoDTO]:
        return self.reports_repo.obtener_unidades_de_orden(order_id)

    def get_product_dashboard(self, product_code: str, evolution_days: int = 30) -> dict[str, Any]:
        """Obtiene el bundle de dashboard para un producto en un contrato único."""
        return self.reports_repo.obtener_dashboard_producto(product_code, evolution_days)
    
    def get_problematic_components_stats(self) -> dict[str, Any]:
        # Placeholder for complex stats logic previously in AppModel
        return {}
