# database/repositories/tracking/core_manager.py
"""
Capa de datos (`core_manager`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

import logging
from typing import Optional, List, Dict, Tuple, Any, cast
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database.models import (
    TrabajoLog, IncidenciaLog, IncidenciaAdjunto, Trabajador, Fabricacion, Producto, Maquina, PasoTrazabilidad
)
from core.tracking_dtos import (
    TrabajoLogDTO, PasoTrazabilidadDTO, IncidenciaLogDTO, IncidenciaAdjuntoDTO
)
from ..base import BaseRepository
from .mappers import TrackingMapper


class TrackingCoreManager(BaseRepository):
    """Gestor DAO para la gestión central de trabajos (obtención, creación, finalización)."""

    def obtener_o_crear_trabajo_log_por_qr(self, qr_code: str, trabajador_id: int, fabricacion_id: int, producto_codigo: str, orden_fabricacion: Optional[str] = None, notas: Optional[str] = None) -> Optional[TrabajoLogDTO]:
        session = self.session_factory()
        try:
            trabajo = session.query(TrabajoLog).options(
                joinedload(TrabajoLog.trabajador), joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto), joinedload(TrabajoLog.pasos_trazabilidad),
                joinedload(TrabajoLog.incidencias).joinedload(IncidenciaLog.adjuntos)
            ).filter_by(qr_code=qr_code).first()

            if trabajo: return TrackingMapper.map_to_trabajo_log_dto(trabajo, self.logger)

            nuevo_trabajo = TrabajoLog(
                qr_code=qr_code, trabajador_id=trabajador_id, fabricacion_id=fabricacion_id,
                producto_codigo=producto_codigo, orden_fabricacion=orden_fabricacion,
                tiempo_inicio=datetime.now(timezone.utc), estado='en_proceso', notas=notas
            )
            session.add(nuevo_trabajo)
            session.commit()
            
            trabajo_recargado = session.query(TrabajoLog).options(
                joinedload(TrabajoLog.trabajador), joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto), joinedload(TrabajoLog.pasos_trazabilidad),
                joinedload(TrabajoLog.incidencias).joinedload(IncidenciaLog.adjuntos)
            ).filter_by(id=nuevo_trabajo.id).first()
            return TrackingMapper.map_to_trabajo_log_dto(trabajo_recargado, self.logger)
        except (IntegrityError, SQLAlchemyError) as e:
            session.rollback()
            self.logger.error(f"Error crear trabajo: {e}")
            return None
        finally:
            session.close()

    def iniciar_trabajo(self, qr_code: str, trabajador_id: int, fabricacion_id: int, producto_codigo: str) -> Optional[TrabajoLogDTO]:
        return self.obtener_o_crear_trabajo_log_por_qr(qr_code, trabajador_id, fabricacion_id, producto_codigo)

    def finalizar_trabajo_log(self, trabajo_log_id: int, notas_finalizacion: Optional[str] = None) -> Optional[TrabajoLogDTO]:
        session = self.session_factory()
        try:
            trabajo = session.query(TrabajoLog).filter_by(id=trabajo_log_id, estado='en_proceso').first()
            if not trabajo: return None
            t_fin = datetime.now(timezone.utc)
            t_ini = trabajo.tiempo_inicio.replace(tzinfo=timezone.utc) if trabajo.tiempo_inicio and trabajo.tiempo_inicio.tzinfo is None else trabajo.tiempo_inicio
            duracion = (t_fin - t_ini).total_seconds() if t_ini else 0.0
            trabajo.tiempo_fin = t_fin
            trabajo.duracion_segundos = int(duracion)
            trabajo.estado = 'completado'
            if notas_finalizacion: trabajo.notas = (trabajo.notas or "") + f"\\n[Finalización] {notas_finalizacion}"
            trabajo.updated_at = t_fin
            session.commit()
            trabajo_c = session.query(TrabajoLog).options(
                joinedload(TrabajoLog.trabajador), joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto), joinedload(TrabajoLog.incidencias).joinedload(IncidenciaLog.adjuntos)
            ).filter_by(id=trabajo_log_id).first()
            return TrackingMapper.map_to_trabajo_log_dto(trabajo_c, self.logger)
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error finalizando trabajo: {e}")
            return None
        finally:
            session.close()

    def pausar_trabajo(self, qr_code: str, motivo: str) -> bool:
        session = self.session_factory()
        try:
            trabajo = session.query(TrabajoLog).filter_by(qr_code=qr_code, estado='en_proceso').first()
            if not trabajo: return False
            trabajo.estado = 'pausado'
            trabajo.notas = (trabajo.notas or "") + f"\\n[Pausa] {motivo}"
            trabajo.updated_at = datetime.now(timezone.utc)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            return False
        finally:
            session.close()

    def reanudar_trabajo(self, qr_code: str) -> bool:
        session = self.session_factory()
        try:
            trabajo = session.query(TrabajoLog).filter_by(qr_code=qr_code, estado='pausado').first()
            if not trabajo: return False
            trabajo.estado = 'en_proceso'
            trabajo.notas = (trabajo.notas or "") + f"\\n[Reanudación] {datetime.now(timezone.utc).isoformat()}"
            trabajo.updated_at = datetime.now(timezone.utc)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            return False
        finally:
            session.close()

    def obtener_trabajo_por_qr(self, qr_code: str) -> Optional[TrabajoLogDTO]:
        session = self.session_factory()
        try:
            trabajo = session.query(TrabajoLog).options(
                joinedload(TrabajoLog.trabajador), joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto), joinedload(TrabajoLog.pasos_trazabilidad),
                joinedload(TrabajoLog.incidencias).joinedload(IncidenciaLog.adjuntos)
            ).filter_by(qr_code=qr_code).first()
            return TrackingMapper.map_to_trabajo_log_dto(trabajo, self.logger)
        except SQLAlchemyError as e:
            return None
        finally:
            session.close()

    def obtener_trabajo_por_id(self, trabajo_log_id: int) -> Optional[TrabajoLogDTO]:
        session = self.session_factory()
        try:
            trabajo = session.query(TrabajoLog).options(
                joinedload(TrabajoLog.trabajador), joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto), joinedload(TrabajoLog.pasos_trazabilidad),
                joinedload(TrabajoLog.incidencias).joinedload(IncidenciaLog.adjuntos)
            ).filter_by(id=trabajo_log_id).first()
            return TrackingMapper.map_to_trabajo_log_dto(trabajo, self.logger)
        except SQLAlchemyError as e:
            return None
        finally:
            session.close()

    def obtener_trabajos_activos(self, trabajador_id: Optional[int] = None, fabricacion_id: Optional[int] = None) -> List[TrabajoLogDTO]:
        session = self.session_factory()
        try:
            query = session.query(TrabajoLog).filter(TrabajoLog.estado.in_(['en_proceso', 'pausado']))
            if trabajador_id: query = query.filter_by(trabajador_id=trabajador_id)
            if fabricacion_id: query = query.filter_by(fabricacion_id=fabricacion_id)
            trabajos = query.options(
                joinedload(TrabajoLog.trabajador), joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto), joinedload(TrabajoLog.incidencias)
            ).all()
            dtos: list[TrabajoLogDTO] = []
            for t in trabajos:
                if not t:
                    continue
                dto = TrackingMapper.map_to_trabajo_log_dto(t, self.logger)
                if dto is not None:
                    dtos.append(dto)
            return dtos
        except SQLAlchemyError:
            return []
        finally:
            session.close()

    def get_trabajo_logs_por_trabajador(self, trabajador_id: int) -> List[TrabajoLogDTO]:
        session = self.session_factory()
        try:
            trabajos = session.query(TrabajoLog).options(
                joinedload(TrabajoLog.incidencias), joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto), joinedload(TrabajoLog.trabajador)
            ).filter_by(trabajador_id=trabajador_id).order_by(TrabajoLog.tiempo_inicio.desc()).all()
            dtos: list[TrabajoLogDTO] = []
            for log in trabajos:
                if not log:
                    continue
                dto = TrackingMapper.map_to_trabajo_log_dto(log, self.logger)
                if dto is not None:
                    dtos.append(dto)
            return dtos
        except SQLAlchemyError:
            return []
        finally:
            session.close()

    def upsert_trabajo_log_from_dict(self, data: Dict[str, Any]) -> Tuple[str, Optional[int]]:
        session = self.session_factory()
        try:
            qr_code = data.get('qr_code')
            if not qr_code: return 'error', None
            for k in ['tiempo_inicio', 'tiempo_fin', 'created_at', 'updated_at']:
                if data.get(k) and isinstance(data[k], str):
                    data[k] = datetime.fromisoformat(data[k].replace('Z', '+00:00'))
            
            trabajo = session.query(TrabajoLog).filter_by(qr_code=qr_code).first()
            incidencias_data = data.pop('incidencias', [])
            tl_keys = TrabajoLog.__table__.columns.keys()
            t_data_clean = {k: v for k, v in data.items() if k in tl_keys}

            if trabajo:
                l_u = trabajo.updated_at or trabajo.created_at
                r_u = t_data_clean.get('updated_at') or t_data_clean.get('created_at')
                if l_u and r_u:
                    l_u = l_u.replace(tzinfo=timezone.utc) if l_u.tzinfo is None else l_u
                    r_u = r_u.replace(tzinfo=timezone.utc) if r_u.tzinfo is None else r_u
                    if l_u >= r_u: return 'skipped', trabajo.id
                for k, v in t_data_clean.items(): setattr(trabajo, k, v)
                status, tid = 'updated', trabajo.id
            else:
                trabajo = TrabajoLog(**t_data_clean)
                session.add(trabajo)
                session.flush()
                status, tid = 'created', trabajo.id

            for inc_d in incidencias_data:
                for k in ['fecha_reporte', 'fecha_resolucion']:
                    if inc_d.get(k) and isinstance(inc_d[k], str):
                        inc_d[k] = datetime.fromisoformat(inc_d[k].replace('Z', '+00:00'))
                adj_d = inc_d.pop('adjuntos', [])
                inc_d['trabajo_log_id'] = tid
                inc_d.pop('id', None)
                il_keys = IncidenciaLog.__table__.columns.keys()
                inc_d_clean = {k: v for k, v in inc_d.items() if k in il_keys}
                incidencia = IncidenciaLog(**inc_d_clean)
                session.add(incidencia)
                session.flush()
                for a_d in adj_d:
                    a_d['incidencia_id'] = incidencia.id
                    a_d.pop('id', None)
                    al_keys = IncidenciaAdjunto.__table__.columns.keys()
                    a_d_clean = {k: v for k, v in a_d.items() if k in al_keys}
                    session.add(IncidenciaAdjunto(**a_d_clean))
            session.commit()
            return status, tid
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error upsert: {e}")
            return 'error', None
        finally:
            session.close()
