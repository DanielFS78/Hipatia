# -*- coding: utf-8 -*-
"""
Nombre del Módulo: tracking_stats_repository
Descripción: Agregados y estadísticas de seguimiento (tiempos por trabajador, incidencias, etc.).

Consultas de solo lectura sobre ``TrabajoLog``, ``IncidenciaLog`` y tablas relacionadas.
"""
import logging
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database.models import (
    TrabajoLog, IncidenciaLog, Fabricacion, Trabajador
)
from database.repositories.base import BaseRepository

class TrackingStatsRepository(BaseRepository):
    """
    Repositorio para consultas estadísticas de seguimiento.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        super().__init__(session_factory)
        self.logger = logging.getLogger("EvolucionTiemposApp.TrackingStatsRepository")

    def obtener_estadisticas_trabajador(
        self,
        trabajador_id: int,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de un trabajador.
        """
        session = self.session_factory()
        try:
            query = session.query(TrabajoLog).filter(
                TrabajoLog.trabajador_id == trabajador_id,
                TrabajoLog.estado == 'completado'
            )

            if fecha_inicio:
                query = query.filter(TrabajoLog.tiempo_inicio >= fecha_inicio)
            if fecha_fin:
                query = query.filter(TrabajoLog.tiempo_fin <= fecha_fin)

            trabajos = query.all()

            if not trabajos:
                return {
                    'unidades_completadas': 0,
                    'tiempo_total_segundos': 0,
                    'tiempo_promedio_segundos': 0,
                    'tiempo_minimo_segundos': 0,
                    'tiempo_maximo_segundos': 0
                }

            duraciones = [t.duracion_segundos for t in trabajos if t.duracion_segundos]

            return {
                'unidades_completadas': len(trabajos),
                'tiempo_total_segundos': sum(duraciones),
                'tiempo_promedio_segundos': sum(duraciones) // len(duraciones) if duraciones else 0,
                'tiempo_minimo_segundos': min(duraciones) if duraciones else 0,
                'tiempo_maximo_segundos': max(duraciones) if duraciones else 0
            }

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener estadísticas: {e}")
            return {}
        finally:
            session.close()

    def obtener_estadisticas_fabricacion(
        self,
        fabricacion_id: int
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de una fabricación.
        """
        session = self.session_factory()
        try:
            # Trabajos completados
            completados = session.query(func.count(TrabajoLog.id)).filter(
                TrabajoLog.fabricacion_id == fabricacion_id,
                TrabajoLog.estado == 'completado'
            ).scalar()

            # Trabajos en proceso
            en_proceso = session.query(func.count(TrabajoLog.id)).filter(
                TrabajoLog.fabricacion_id == fabricacion_id,
                TrabajoLog.estado == 'en_proceso'
            ).scalar()

            # Incidencias abiertas
            incidencias_abiertas = session.query(func.count(IncidenciaLog.id)).join(
                TrabajoLog
            ).filter(
                TrabajoLog.fabricacion_id == fabricacion_id,
                IncidenciaLog.estado == 'abierta'
            ).scalar()

            return {
                'unidades_completadas': completados or 0,
                'unidades_en_proceso': en_proceso or 0,
                'incidencias_abiertas': incidencias_abiertas or 0,
                'trabajadores_asignados': len(self.obtener_trabajadores_de_fabricacion(fabricacion_id))
            }

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener estadísticas de fabricación: {e}")
            return {}
        finally:
            session.close()

    def obtener_trabajadores_de_fabricacion(
        self,
        fabricacion_id: int
    ) -> List[Trabajador]:
        """
        Obtiene todos los trabajadores asignados a una fabricación.
        """
        session = self.session_factory()
        try:
            fabricacion = session.query(Fabricacion).options(
                joinedload(Fabricacion.trabajadores_asignados)
            ).filter(Fabricacion.id == fabricacion_id).first()

            if not fabricacion:
                return []

            return fabricacion.trabajadores_asignados

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener trabajadores de fabricación: {e}")
            return []
        finally:
            session.close()
