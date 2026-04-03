# database/repositories/reports/reports_incidences_manager.py

"""
Capa de datos (`reports_incidences_manager`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from typing import List
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..base import BaseRepository
from ...models import TrabajoLog, IncidenciaLog
from core.reports_dtos import IncidenciaResumenDTO

class ReportsIncidencesManager(BaseRepository):
    """Gestor DAO para análisis de incidencias en reportes."""

    def obtener_incidencias_por_producto(self, code: str) -> List[IncidenciaResumenDTO]:
        def _op(session: Session) -> List[IncidenciaResumenDTO]:
            data = session.query(IncidenciaLog.tipo_incidencia, func.count(IncidenciaLog.id).label('qty')).join(TrabajoLog).filter(
                TrabajoLog.producto_codigo == code).group_by(IncidenciaLog.tipo_incidencia).all()
            total = sum(d.qty for d in data) if data else 0
            res = [IncidenciaResumenDTO(tipo_incidencia=d.tipo_incidencia or "Sin clasificar", cantidad=d.qty, porcentaje=round((d.qty/total*100), 1) if total > 0 else 0) for d in data]
            res.sort(key=lambda x: x.cantidad, reverse=True)
            return res
        return self.safe_execute(_op) or []
