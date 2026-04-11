# -*- coding: utf-8 -*-
"""
Nombre del Módulo: machine.stats_manager
Descripción: Acceso a datos de máquinas (CRUD, mantenimiento, preparación y estadísticas).
"""

from typing import List, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..base import BaseRepository
from ...models import Maquina, Subfabricacion

class MachineStatsManager(BaseRepository):
    """Gestor DAO para estadísticas relacionadas con máquinas."""

    def get_machine_usage_stats(self) -> List[Tuple[str, float]]:
        def _operation(session: Session) -> List[Tuple[str, float]]:
            result = (
                session.query(Maquina.nombre, func.sum(Subfabricacion.tiempo).label("total_minutos"))
                .join(Subfabricacion, Maquina.id == Subfabricacion.maquina_id)
                .group_by(Maquina.nombre)
                .order_by(func.sum(Subfabricacion.tiempo).desc())
                .all()
            )
            return [(row.nombre, float(row.total_minutos or 0)) for row in result]
        return self.safe_execute(_operation) or []
