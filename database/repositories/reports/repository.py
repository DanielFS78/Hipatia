"""
Capa de datos (`repository`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from ..base import BaseRepository
from .reports_search_manager import ReportsSearchManager
from .reports_incidences_manager import ReportsIncidencesManager
from .reports_orders_manager import ReportsOrdersManager
from .reports_products_manager import ReportsProductsManager
from .reports_stats_manager import ReportsStatsManager
from core.reports_dtos import (ResultadoBusquedaDTO, IncidenciaResumenDTO, 
                               OrdenFabricacionResumenDTO, OrdenFabricacionDetalleDTO, 
                               UnidadTrabajoDTO, ResumenProductoDTO, 
                               PromedioTiempoDTO, TiempoTrabajadorDTO, PuntoEvolucionDTO)

class ReportsRepository(BaseRepository):
    """
    Repositorio especializado en consultas de agregación y análisis para reportes.
    Implementa el patrón Fachada delegando en DAO Managers especializados.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        super().__init__(session_factory)
        self.logger = logging.getLogger("EvolucionTiemposApp.ReportsRepository")
        
        # Composición de gestores
        self.search = ReportsSearchManager(session_factory)
        self.incidences = ReportsIncidencesManager(session_factory)
        self.orders = ReportsOrdersManager(session_factory)
        self.products = ReportsProductsManager(session_factory)
        self.stats = ReportsStatsManager(session_factory)
        self._sync_managers()

    def _sync_managers(self) -> None:
        for m in [self.search, self.incidences, self.orders, self.products, self.stats]:
            m.session_factory = self.session_factory

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name in ('session_factory', 'safe_execute'):
            if hasattr(self, 'search'):
                for m in [self.search, self.incidences, self.orders, self.products, self.stats]:
                    setattr(m, name, value)

    # Delegación: ReportsSearchManager
    def buscar_por_codigo(self, query: str, limit: int = 20) -> List[ResultadoBusquedaDTO]:
        return self.search.buscar_por_codigo(query, limit)

    # Delegación: ReportsIncidencesManager
    def obtener_incidencias_por_producto(self, code: str) -> List[IncidenciaResumenDTO]:
        return self.incidences.obtener_incidencias_por_producto(code)

    # Delegación: ReportsOrdersManager
    def obtener_ordenes_por_producto(self, code: str, limit: int = 50) -> List[OrdenFabricacionResumenDTO]:
        return self.orders.obtener_ordenes_por_producto(code, limit)

    def obtener_detalle_orden(self, of: str) -> Optional[OrdenFabricacionDetalleDTO]:
        return self.orders.obtener_detalle_orden(of)

    def obtener_unidades_de_orden(self, of: str) -> List[UnidadTrabajoDTO]:
        return self.orders.obtener_unidades_de_orden(of)

    # Delegación: ReportsProductsManager
    def obtener_resumen_producto(self, code: str) -> Optional[ResumenProductoDTO]:
        return self.products.obtener_resumen_producto(code)

    # Delegación: ReportsStatsManager
    def calcular_promedio_tiempo_unidad(
        self, code: str, start: Optional[datetime] = None, end: Optional[datetime] = None
    ) -> Optional[PromedioTiempoDTO]:
        return self.stats.calcular_promedio_tiempo_unidad(code, start, end)

    def obtener_tiempos_por_trabajador(self, code: str) -> List[TiempoTrabajadorDTO]:
        return self.stats.obtener_tiempos_por_trabajador(code)

    def obtener_evolucion_temporal(self, code: str, days: int = 30) -> List[PuntoEvolucionDTO]:
        return self.stats.obtener_evolucion_temporal(code, days)

    def obtener_dashboard_producto(self, product_code: str, evolution_days: int = 30) -> dict[str, Any]:
        """
        Obtiene en una sola llamada lógica todos los datos del dashboard de un producto.
        Centraliza el contrato consumido por UI para reducir round-trips en capas superiores.
        """
        return {
            "summary": self.obtener_resumen_producto(product_code),
            "orders": self.obtener_ordenes_por_producto(product_code),
            "time_stats": self.calcular_promedio_tiempo_unidad(product_code),
            "worker_stats": self.obtener_tiempos_por_trabajador(product_code),
            "incidents": self.obtener_incidencias_por_producto(product_code),
            "evolution": self.obtener_evolucion_temporal(product_code, evolution_days),
        }
