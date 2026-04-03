# database/repositories/reports/reports_orders_manager.py

"""
Capa de datos (`reports_orders_manager`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from typing import List, Optional
from sqlalchemy import func, desc, distinct, case
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from ..base import BaseRepository
from ...models import TrabajoLog, Producto, IncidenciaLog, Trabajador
from core.reports_dtos import OrdenFabricacionResumenDTO, OrdenFabricacionDetalleDTO, UnidadTrabajoDTO

class ReportsOrdersManager(BaseRepository):
    """Gestor DAO para consultas sobre órdenes de fabricación en reportes."""

    def obtener_ordenes_por_producto(self, code: str, limit: int = 50) -> List[OrdenFabricacionResumenDTO]:
        def _op(session: Session) -> List[OrdenFabricacionResumenDTO]:
            p = session.query(Producto).filter(Producto.codigo == code).first()
            p_desc = p.descripcion if p else ""
            query = session.query(TrabajoLog.orden_fabricacion, func.min(TrabajoLog.tiempo_inicio).label('start'), func.max(TrabajoLog.tiempo_fin).label('end'),
                                 func.count(TrabajoLog.id).label('qty'), func.sum(TrabajoLog.duracion_segundos).label('total_s'),
                                 func.count(distinct(IncidenciaLog.id)).label('inc_qty'),
                                 func.sum(case((TrabajoLog.estado.in_(['en_proceso', 'pausado']), 1), else_=0)).label('active')).outerjoin(
                IncidenciaLog, TrabajoLog.id == IncidenciaLog.trabajo_log_id).filter(TrabajoLog.producto_codigo == code, TrabajoLog.orden_fabricacion.isnot(None)).group_by(
                TrabajoLog.orden_fabricacion).order_by(desc('start')).limit(limit)
            return [OrdenFabricacionResumenDTO(orden_fabricacion=r.orden_fabricacion or "Sin OF", producto_codigo=code, producto_descripcion=p_desc,
                                              fecha_inicio=r.start, fecha_fin=r.end, cantidad_unidades=r.qty or 0, tiempo_total_segundos=r.total_s or 0,
                                              incidencias_count=r.inc_qty or 0, estado="en_proceso" if (r.active or 0) > 0 else "completado") for r in query.all()]
        return self.safe_execute(_op) or []

    def obtener_detalle_orden(self, of: str) -> Optional[OrdenFabricacionDetalleDTO]:
        def _op(session: Session) -> Optional[OrdenFabricacionDetalleDTO]:
            d = session.query(TrabajoLog.producto_codigo, func.min(TrabajoLog.tiempo_inicio).label('start'), func.max(TrabajoLog.tiempo_fin).label('end'),
                             func.count(TrabajoLog.id).label('qty'), func.sum(TrabajoLog.duracion_segundos).label('total_s'),
                             func.avg(TrabajoLog.duracion_segundos).label('avg_s')).filter(TrabajoLog.orden_fabricacion == of).group_by(TrabajoLog.producto_codigo).first()
            if not d: return None
            p = session.query(Producto).filter(Producto.codigo == d.producto_codigo).first()
            inc = session.query(func.count(IncidenciaLog.id)).join(TrabajoLog).filter(TrabajoLog.orden_fabricacion == of).scalar() or 0
            trabs = session.query(distinct(Trabajador.nombre_completo)).join(TrabajoLog, TrabajoLog.trabajador_id == Trabajador.id).filter(TrabajoLog.orden_fabricacion == of).all()
            in_pro = session.query(TrabajoLog).filter(TrabajoLog.orden_fabricacion == of, TrabajoLog.estado.in_(['en_proceso', 'pausado'])).first() is not None
            return OrdenFabricacionDetalleDTO(orden_fabricacion=of, producto_codigo=d.producto_codigo, producto_descripcion=p.descripcion if p else "",
                                             fecha_inicio=d.start, fecha_fin=d.end, cantidad_unidades=d.qty or 0, tiempo_total_segundos=int(d.total_s or 0),
                                             tiempo_promedio_segundos=float(d.avg_s or 0), incidencias_count=inc, trabajadores_involucrados=[t[0] for t in trabs if t[0]],
                                             estado="en_proceso" if in_pro else "completado")
        return self.safe_execute(_op)

    def obtener_unidades_de_orden(self, of: str) -> List[UnidadTrabajoDTO]:
        def _op(s: Session) -> List[UnidadTrabajoDTO]:
            logs = s.query(TrabajoLog).options(joinedload(TrabajoLog.trabajador), joinedload(TrabajoLog.incidencias)).filter(TrabajoLog.orden_fabricacion == of).order_by(TrabajoLog.tiempo_inicio).all()
            res = []
            for t in logs:
                name = t.trabajador.nombre_completo if t.trabajador else ""
                res.append(UnidadTrabajoDTO(qr_code=t.qr_code or "", tiempo_inicio=t.tiempo_inicio or datetime.min, tiempo_fin=t.tiempo_fin, duracion_segundos=t.duracion_segundos or 0, 
                                           trabajador_nombre=name, tiene_incidencias=len(t.incidencias or []) > 0))
            return res
        return self.safe_execute(_op) or []
