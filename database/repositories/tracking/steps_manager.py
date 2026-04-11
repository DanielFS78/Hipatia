# -*- coding: utf-8 -*-
"""
Nombre del Módulo: tracking.steps_manager

Descripción: Define protocolos o tipos principales: ``TrackingStepsManager``. Gestor DAO para la gestión de pasos de trazabilidad. Integración típica con: ``datetime``, ``sqlalchemy``, ``database``, ``core``, ``base``, ``mappers``.
"""

import logging
from typing import Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from database.models import PasoTrazabilidad, TrabajoLog
from core.tracking_dtos import PasoTrazabilidadDTO
from ..base import BaseRepository
from .mappers import TrackingMapper


class TrackingStepsManager(BaseRepository):
    """Gestor DAO para la gestión de pasos de trazabilidad."""

    def get_paso_activo_por_trabajador(self, trabajador_id: int) -> Optional[PasoTrazabilidadDTO]:
        session = self.session_factory()
        try:
            paso = session.query(PasoTrazabilidad).options(
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.fabricacion),
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.producto),
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.trabajador),
                joinedload(PasoTrazabilidad.trabajador),
                joinedload(PasoTrazabilidad.maquina)
            ).filter_by(trabajador_id=trabajador_id, estado_paso='en_proceso').order_by(PasoTrazabilidad.tiempo_inicio_paso.desc()).first()
            return TrackingMapper.map_to_paso_trazabilidad_dto(paso, self.logger)
        except SQLAlchemyError as e:
            self.logger.error(f"Error paso activo T{trabajador_id}: {e}")
            return None
        finally:
            session.close()

    def get_ultimo_paso_para_qr(self, trabajo_log_id: int) -> Optional[PasoTrazabilidadDTO]:
        session = self.session_factory()
        try:
            paso = session.query(PasoTrazabilidad).options(
                joinedload(PasoTrazabilidad.trabajo_log),
                joinedload(PasoTrazabilidad.maquina),
                joinedload(PasoTrazabilidad.trabajador)
            ).filter_by(trabajo_log_id=trabajo_log_id).order_by(PasoTrazabilidad.tiempo_inicio_paso.desc()).first()
            return TrackingMapper.map_to_paso_trazabilidad_dto(paso, self.logger)
        except SQLAlchemyError as e:
            self.logger.error(f"Error último paso QR {trabajo_log_id}: {e}")
            return None
        finally:
            session.close()

    def iniciar_nuevo_paso(self, trabajo_log_id: int, trabajador_id: int, paso_nombre: str, tipo_paso: str, maquina_id: Optional[int] = None) -> Optional[PasoTrazabilidadDTO]:
        session = self.session_factory()
        try:
            nuevo = PasoTrazabilidad(
                trabajo_log_id=trabajo_log_id, trabajador_id=trabajador_id,
                maquina_id=maquina_id, paso_nombre=paso_nombre, tipo_paso=tipo_paso,
                tiempo_inicio_paso=datetime.now(timezone.utc), estado_paso='en_proceso'
            )
            session.add(nuevo)
            session.flush()
            pid = nuevo.id
            session.commit()
            paso = session.query(PasoTrazabilidad).options(
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.fabricacion),
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.producto),
                joinedload(PasoTrazabilidad.trabajador), joinedload(PasoTrazabilidad.maquina)
            ).filter_by(id=pid).first()
            return TrackingMapper.map_to_paso_trazabilidad_dto(paso, self.logger)
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error iniciando paso: {e}")
            return None
        finally:
            session.close()

    def finalizar_paso(self, paso_id: int) -> Optional[PasoTrazabilidadDTO]:
        session = self.session_factory()
        try:
            paso = session.query(PasoTrazabilidad).filter_by(id=paso_id, estado_paso='en_proceso').first()
            if not paso: return None
            t_fin = datetime.now(timezone.utc)
            t_ini = paso.tiempo_inicio_paso.replace(tzinfo=timezone.utc) if paso.tiempo_inicio_paso.tzinfo is None else paso.tiempo_inicio_paso
            duracion = (t_fin - t_ini).total_seconds()
            paso.tiempo_fin_paso = t_fin
            paso.duracion_paso_segundos = int(duracion)
            paso.estado_paso = 'completado'
            session.commit()
            paso_c = session.query(PasoTrazabilidad).options(
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.fabricacion),
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.producto),
                joinedload(PasoTrazabilidad.trabajador), joinedload(PasoTrazabilidad.maquina)
            ).filter_by(id=paso_id).first()
            return TrackingMapper.map_to_paso_trazabilidad_dto(paso_c, self.logger)
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error finalizando paso: {e}")
            return None
        finally:
            session.close()
