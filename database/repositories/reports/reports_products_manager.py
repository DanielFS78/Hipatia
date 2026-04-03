# database/repositories/reports/reports_products_manager.py

"""
Capa de datos (`reports_products_manager`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from typing import Optional
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session
from ..base import BaseRepository
# from ...models import Producto, TrabajoLog, IncidenciaLog # Late imports to avoid circular ones
from core.reports_dtos import ResumenProductoDTO

class ReportsProductsManager(BaseRepository):
    """Gestor DAO para resúmenes de productos en reportes."""

    def obtener_resumen_producto(self, code: str) -> Optional[ResumenProductoDTO]:
        def _op(session: Session) -> Optional[ResumenProductoDTO]:
            from ...models import Producto, TrabajoLog, IncidenciaLog
            p = session.query(Producto).filter(Producto.codigo == code).first()
            if not p: return None
            stats = session.query(func.count(distinct(TrabajoLog.orden_fabricacion)).label('of_qty'), func.count(TrabajoLog.id).label('u_qty'),
                                 func.avg(TrabajoLog.duracion_segundos).label('avg_s'), func.min(TrabajoLog.tiempo_inicio).label('first'),
                                 func.max(TrabajoLog.tiempo_inicio).label('last')).filter(TrabajoLog.producto_codigo == code).first()
            incs = session.query(func.count(IncidenciaLog.id)).join(TrabajoLog).filter(TrabajoLog.producto_codigo == code).scalar() or 0
            return ResumenProductoDTO(producto_codigo=code, producto_descripcion=p.descripcion or "", total_ordenes=stats.of_qty or 0,
                                     total_unidades=stats.u_qty or 0, tiempo_promedio_segundos=float(stats.avg_s or 0), total_incidencias=incs,
                                     fecha_primera_produccion=stats.first, fecha_ultima_produccion=stats.last)
        return self.safe_execute(_op)
