# database/repositories/reports/reports_stats_manager.py

"""
Capa de datos (`reports_stats_manager`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import Float, func
from sqlalchemy.orm import Session
from ..base import BaseRepository
from ...models import TrabajoLog, Producto, Trabajador
from core.reports_dtos import PromedioTiempoDTO, TiempoTrabajadorDTO, PuntoEvolucionDTO

class ReportsStatsManager(BaseRepository):
    """Gestor DAO para cálculos estadísticos complejos en reportes."""

    def calcular_promedio_tiempo_unidad(self, code: str, start: Optional[datetime] = None, end: Optional[datetime] = None) -> Optional[PromedioTiempoDTO]:
        def _op(session: Session) -> Optional[PromedioTiempoDTO]:
            duration_expr = func.cast(TrabajoLog.duracion_segundos, Float)
            q = session.query(
                func.avg(duration_expr).label("avg"),
                func.min(TrabajoLog.duracion_segundos).label("min"),
                func.max(TrabajoLog.duracion_segundos).label("max"),
                func.count(TrabajoLog.id).label("total"),
                func.avg(duration_expr * duration_expr).label("avg_sq"),
            ).filter(
                TrabajoLog.producto_codigo == code,
                TrabajoLog.duracion_segundos.isnot(None),
                TrabajoLog.duracion_segundos > 0,
            )
            if start:
                q = q.filter(TrabajoLog.tiempo_inicio >= start)
            if end:
                q = q.filter(TrabajoLog.tiempo_inicio <= end)
            res = q.first()
            if not res or res.total == 0:
                return None
            p = session.query(Producto).filter(Producto.codigo == code).first()
            avg = float(res.avg or 0.0)
            avg_sq = float(res.avg_sq or 0.0)
            variance = max(0.0, avg_sq - (avg * avg))
            std = variance ** 0.5 if (res.total or 0) > 1 else 0.0
            return PromedioTiempoDTO(
                producto_codigo=code,
                producto_descripcion=(p.descripcion or "") if p else "",
                promedio_segundos=avg,
                desviacion_estandar=std,
                minimo_segundos=int(res.min or 0),
                maximo_segundos=int(res.max or 0),
                total_unidades=res.total,
                periodo_inicio=start,
                periodo_fin=end,
            )
        return self.safe_execute(_op)

    def obtener_tiempos_por_trabajador(self, code: str) -> List[TiempoTrabajadorDTO]:
        def _op(s: Session) -> List[TiempoTrabajadorDTO]:
            data = s.query(Trabajador.id, Trabajador.nombre_completo, func.avg(TrabajoLog.duracion_segundos).label('avg'),
                          func.min(TrabajoLog.duracion_segundos).label('min'), func.max(TrabajoLog.duracion_segundos).label('max'),
                          func.count(TrabajoLog.id).label('total')).join(TrabajoLog, TrabajoLog.trabajador_id == Trabajador.id).filter(
                TrabajoLog.producto_codigo == code, TrabajoLog.duracion_segundos > 0).group_by(Trabajador.id, Trabajador.nombre_completo).order_by('avg').all()
            return [TiempoTrabajadorDTO(trabajador_id=d.id, trabajador_nombre=d.nombre_completo or "Desconocido", promedio_segundos=float(d.avg or 0),
                                       minimo_segundos=int(d.min or 0), maximo_segundos=int(d.max or 0), unidades_realizadas=d.total) for d in data]
        return self.safe_execute(_op) or []

    def obtener_evolucion_temporal(self, code: str, days: int = 30) -> List[PuntoEvolucionDTO]:
        def _op(s: Session) -> List[PuntoEvolucionDTO]:
            limit = datetime.now() - timedelta(days=days)
            data = s.query(func.date(TrabajoLog.tiempo_inicio).label('date'), func.avg(TrabajoLog.duracion_segundos).label('avg'), func.count(TrabajoLog.id).label('qty')).filter(
                TrabajoLog.producto_codigo == code, TrabajoLog.tiempo_inicio >= limit, TrabajoLog.duracion_segundos > 0).group_by(
                func.date(TrabajoLog.tiempo_inicio)).order_by('date').all()
            res = []
            for d in data:
                if d.date:
                    dt = datetime.strptime(d.date, "%Y-%m-%d") if isinstance(d.date, str) else datetime.combine(d.date, datetime.min.time())
                    res.append(PuntoEvolucionDTO(fecha=dt, promedio_segundos=float(d.avg or 0), cantidad_unidades=d.qty))
            return res
        return self.safe_execute(_op) or []
