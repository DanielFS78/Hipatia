
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: reports.reports_search_manager
Descripción: Consultas SQL para informes: órdenes, productos, incidencias, búsqueda y estadísticas.
"""

from typing import List
from datetime import datetime
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from ..base import BaseRepository
from ...models import Producto, TrabajoLog
from core.reports_dtos import ResultadoBusquedaDTO

class ReportsSearchManager(BaseRepository):
    """Gestor DAO para búsquedas transversales orientadas a reportes."""

    def buscar_por_codigo(self, query: str, limit: int = 20) -> List[ResultadoBusquedaDTO]:
        def _operation(session: Session) -> List[ResultadoBusquedaDTO]:
            clean_query = query.strip().lower()
            if not clean_query:
                return []
            safe_limit = max(1, min(limit, 100))
            products_limit = max(1, int(safe_limit * 0.6))
            orders_limit = max(1, safe_limit - products_limit)
            results = []
            pattern = f"%{clean_query}%"
            prod_data = (
                session.query(
                    Producto.codigo,
                    Producto.descripcion,
                    func.max(TrabajoLog.tiempo_inicio).label("last"),
                    func.count(TrabajoLog.id).label("total"),
                )
                .outerjoin(TrabajoLog, Producto.codigo == TrabajoLog.producto_codigo)
                .filter(
                    or_(
                        func.lower(Producto.codigo).like(pattern),
                        func.lower(Producto.descripcion).like(pattern),
                    )
                )
                .group_by(Producto.codigo, Producto.descripcion)
                .order_by(func.max(TrabajoLog.tiempo_inicio).desc(), Producto.codigo.asc())
                .limit(products_limit)
                .all()
            )
            for p in prod_data:
                results.append(
                    ResultadoBusquedaDTO(
                        tipo="producto",
                        codigo=p.codigo,
                        descripcion=p.descripcion or "",
                        fecha_ultimo_uso=p.last,
                        total_unidades=p.total or 0,
                    )
                )
            ordenes = (
                session.query(
                    TrabajoLog.orden_fabricacion,
                    func.max(TrabajoLog.tiempo_inicio).label("last"),
                    func.count(TrabajoLog.id).label("total"),
                )
                .filter(
                    TrabajoLog.orden_fabricacion.isnot(None),
                    func.lower(TrabajoLog.orden_fabricacion).like(pattern),
                )
                .group_by(TrabajoLog.orden_fabricacion)
                .order_by(func.max(TrabajoLog.tiempo_inicio).desc(), TrabajoLog.orden_fabricacion.asc())
                .limit(orders_limit)
                .all()
            )
            for o in ordenes:
                if o.orden_fabricacion:
                    results.append(
                        ResultadoBusquedaDTO(
                            tipo="orden",
                            codigo=o.orden_fabricacion,
                            descripcion="Orden de Fabricación",
                            fecha_ultimo_uso=o.last,
                            total_unidades=o.total,
                        )
                    )
            results.sort(key=lambda x: x.fecha_ultimo_uso or datetime.min, reverse=True)
            return results[:safe_limit]
        return self.safe_execute(_operation) or []
