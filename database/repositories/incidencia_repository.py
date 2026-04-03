# -*- coding: utf-8 -*-
"""
INCIDENCIA REPOSITORY
========================================================================
Repositorio para la gestión de incidencias y adjuntos.
========================================================================
"""
import os
import logging
from datetime import datetime, timezone
from typing import Callable, Optional, List, cast
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models import (
    IncidenciaLog, IncidenciaAdjunto, TrabajoLog, Trabajador
)
from database.repositories.base import BaseRepository
from core.tracking_dtos import IncidenciaLogDTO, IncidenciaAdjuntoDTO

class IncidenciaRepository(BaseRepository):
    """
    Repositorio para gestión de incidencias.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        super().__init__(session_factory)
        self.logger = logging.getLogger("EvolucionTiemposApp.IncidenciaRepository")

    def registrar_incidencia(
            self,
            trabajo_log_id: int,
            trabajador_id: int,
            tipo_incidencia: str,
            descripcion: str,
            rutas_fotos: Optional[List[str]] = None
    ) -> Optional[IncidenciaLogDTO]:
        """
        Registra una nueva incidencia.
        """
        session = self.session_factory()
        try:
            # Crear incidencia
            incidencia = IncidenciaLog(
                trabajo_log_id=trabajo_log_id,
                trabajador_id=trabajador_id,
                tipo_incidencia=tipo_incidencia,
                descripcion=descripcion,
                fecha_reporte=datetime.now(timezone.utc),
                estado='abierta'
            )

            session.add(incidencia)
            session.flush()  # Para obtener el ID

            # Guardamos el ID para la recarga
            nueva_incidencia_id = incidencia.id

            # Añadir fotos si las hay
            if rutas_fotos:
                for ruta in rutas_fotos:
                    if nueva_incidencia_id:
                        self._crear_adjunto(session, nueva_incidencia_id, ruta)

            session.commit()  # Guardamos todo en la BD

            # Recargar con DTO
            incidencia_cargada = session.query(IncidenciaLog).options(
                joinedload(IncidenciaLog.trabajador),
                joinedload(IncidenciaLog.trabajo_log),
                joinedload(IncidenciaLog.adjuntos)
            ).filter(
                IncidenciaLog.id == nueva_incidencia_id
            ).first()

            return self._map_to_incidencia_log_dto(incidencia_cargada)

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al registrar incidencia: {e}")
            return None
        finally:
            session.close()

    def _crear_adjunto(
        self,
        session: Session,
        incidencia_id: int,
        ruta_archivo: str
    ) -> Optional[IncidenciaAdjunto]:
        """
        Crea un adjunto fotográfico (uso interno).
        """
        nombre_archivo = os.path.basename(ruta_archivo)

        # Detectar tipo MIME básico
        extension = os.path.splitext(nombre_archivo)[1].lower()
        tipo_mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp'
        }
        tipo_mime = tipo_mime_map.get(extension, 'application/octet-stream')

        # Obtener tamaño del archivo
        tamano = os.path.getsize(ruta_archivo) if os.path.exists(ruta_archivo) else 0

        adjunto = IncidenciaAdjunto(
            incidencia_id=incidencia_id,
            ruta_archivo=ruta_archivo,
            nombre_archivo=nombre_archivo,
            tipo_mime=tipo_mime,
            tamano_bytes=tamano,
            fecha_subida=datetime.now(timezone.utc)
        )

        session.add(adjunto)
        return adjunto

    def añadir_foto_a_incidencia(
        self,
        incidencia_id: int,
        ruta_foto: str,
        descripcion: Optional[str] = None
    ) -> Optional[IncidenciaAdjuntoDTO]:
        """
        Añade una foto a una incidencia existente.
        """
        session = self.session_factory()
        try:
            adjunto = self._crear_adjunto(session, incidencia_id, ruta_foto)
            if adjunto and descripcion:
                adjunto.descripcion = descripcion

            session.commit()
            
            # Recargar para asegurar IDs y consistencia
            session.refresh(adjunto)
            
            self.logger.info(f"Foto añadida a incidencia {incidencia_id}")
            return self._map_to_incidencia_adjunto_dto(adjunto)

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al añadir foto: {e}")
            return None
        finally:
            session.close()

    def resolver_incidencia(
        self,
        incidencia_id: int,
        resolucion: str
    ) -> Optional[IncidenciaLogDTO]:
        """
        Marca una incidencia como resuelta.
        """
        session = self.session_factory()
        try:
            incidencia = session.query(IncidenciaLog).options(
                joinedload(IncidenciaLog.trabajador),
                joinedload(IncidenciaLog.trabajo_log),
                joinedload(IncidenciaLog.adjuntos)
            ).filter(
                IncidenciaLog.id == incidencia_id
            ).first()

            if not incidencia:
                return None

            incidencia.estado = 'resuelta'
            incidencia.resolucion = resolucion
            incidencia.fecha_resolucion = datetime.now(timezone.utc)

            session.commit()
            self.logger.info(f"Incidencia {incidencia_id} resuelta")
            
            return self._map_to_incidencia_log_dto(incidencia)

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al resolver incidencia: {e}")
            return None
        finally:
            session.close()

    def obtener_incidencias_abiertas(
        self,
        fabricacion_id: Optional[int] = None
    ) -> List[IncidenciaLogDTO]:
        """
        Obtiene todas las incidencias abiertas.
        """
        session = self.session_factory()
        try:
            query = session.query(IncidenciaLog).filter(
                IncidenciaLog.estado == 'abierta'
            )

            if fabricacion_id:
                query = query.join(TrabajoLog).filter(
                    TrabajoLog.fabricacion_id == fabricacion_id
                )

            incidencias = query.options(
                joinedload(IncidenciaLog.trabajo_log),
                joinedload(IncidenciaLog.trabajador),
                joinedload(IncidenciaLog.adjuntos)
            ).all()

            return [dto for i in incidencias if (dto := self._map_to_incidencia_log_dto(i))]

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener incidencias abiertas: {e}")
            return []
        finally:
            session.close()

    # Helpers for mapping
    def _map_to_incidencia_log_dto(self, incidencia: Optional[IncidenciaLog]) -> Optional[IncidenciaLogDTO]:
        """Map an IncidenciaLog ORM object to IncidenciaLogDTO."""
        if not incidencia:
            return None
            
        dto = IncidenciaLogDTO(
            id=incidencia.id or 0,
            tipo_incidencia=incidencia.tipo_incidencia or "",
            descripcion=incidencia.descripcion or "",
            fecha_reporte=incidencia.fecha_reporte or datetime.min,
            estado=incidencia.estado or "",
            resolucion=incidencia.resolucion or "",
            fecha_resolucion=incidencia.fecha_resolucion,
            trabajador_nombre=incidencia.trabajador.nombre_completo if incidencia.trabajador else ""
        )
        
        try:
            adjuntos = getattr(incidencia, 'adjuntos', [])
            dto.adjuntos = [a_dto for a in adjuntos if (a_dto := self._map_to_incidencia_adjunto_dto(a))]
        except Exception:
            dto.adjuntos = []
            
        return dto

    def _map_to_incidencia_adjunto_dto(self, adjunto: Optional[IncidenciaAdjunto]) -> Optional[IncidenciaAdjuntoDTO]:
        """Map IncidenciaAdjunto ORM to DTO."""
        if not adjunto:
            return None
        return IncidenciaAdjuntoDTO(
            id=adjunto.id or 0,
            ruta_archivo=adjunto.ruta_archivo or "",
            tipo_archivo=adjunto.tipo_mime or "" 
        )
