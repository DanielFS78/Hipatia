"""
Nombre del Módulo: tracking.queries_manager
Descripcion: Gestor central de consultas complejas para el sistema de tracking.
             Incluye exportación de datos y recuperación de fabricaciones asignadas.
"""
import logging
from typing import List, Dict, Any, Optional, cast
from datetime import datetime, timezone
from sqlalchemy.orm import load_only
from sqlalchemy.exc import SQLAlchemyError
from database.models import (
    TrabajoLog, PasoTrazabilidad, IncidenciaLog, IncidenciaAdjunto,
    Fabricacion, trabajador_fabricacion_link, fabricacion_productos, Producto
)
from core.tracking_dtos import FabricacionAsignadaDTO
from core.dtos import FabricacionProductoDTO
from ..base import BaseRepository


class TrackingQueriesManager(BaseRepository):
    """
    Gestor DAO para consultas complejas y exportación de datos de tracking.

    Centraliza la lógica de consultas de solo lectura pesadas y transformaciones
    a DTOs para la interfaz de trabajador y exportaciones.
    """

    def get_data_for_export(self, trabajador_id: int, since_date: datetime) -> List[Dict[str, Any]]:
        def _to_dict(obj):
            data = {}
            for key in dir(obj):
                if not key.startswith('_') and key not in ['metadata', 'registry']:
                    try:
                        value = getattr(obj, key)
                        if not callable(value) and not hasattr(value, '_sa_instance_state'):
                            if isinstance(value, datetime): data[key] = value.isoformat()
                            elif isinstance(value, (str, int, float, bool)) or value is None:
                                data[key] = cast(Any, value)
                    except Exception as e:
                        self.logger.debug("Atributo '%s' omitido en exportación de %s: %s", key, obj, e)
            return data

        session = self.session_factory()
        try:
            if since_date.tzinfo is None: since_date = since_date.replace(tzinfo=timezone.utc)
            trabajos = session.query(TrabajoLog).filter_by(trabajador_id=trabajador_id).filter(TrabajoLog.created_at >= since_date).order_by(TrabajoLog.created_at).all()
            
            export_data = []
            for t in trabajos:
                session.expunge(t)
                tdict = _to_dict(t)
                
                pasos = session.query(PasoTrazabilidad).options(load_only(
                    PasoTrazabilidad.id, PasoTrazabilidad.trabajo_log_id, PasoTrazabilidad.trabajador_id,
                    PasoTrazabilidad.maquina_id, PasoTrazabilidad.paso_nombre, PasoTrazabilidad.tipo_paso,
                    PasoTrazabilidad.tiempo_inicio_paso, PasoTrazabilidad.estado_paso, PasoTrazabilidad.duracion_paso_segundos
                )).filter_by(trabajo_log_id=t.id).order_by(PasoTrazabilidad.tiempo_inicio_paso).all()

                pasos_list = []
                for p in pasos:
                    session.expunge(p)
                    pdict = _to_dict(p)
                    if p.estado_paso == 'completado':
                        pc = session.query(PasoTrazabilidad).filter_by(id=p.id).first()
                        if pc and pc.tiempo_fin_paso: pdict['tiempo_fin_paso'] = pc.tiempo_fin_paso.isoformat()
                        session.expunge(pc)
                    pasos_list.append(pdict)
                tdict['pasos_trazabilidad'] = pasos_list

                incidencias = session.query(IncidenciaLog).filter_by(trabajo_log_id=t.id).order_by(IncidenciaLog.fecha_reporte).all()
                inc_list = []
                for inc in incidencias:
                    session.expunge(inc)
                    idict = _to_dict(inc)
                    adjuntos = session.query(IncidenciaAdjunto).filter_by(incidencia_id=inc.id).all()
                    idict['adjuntos'] = [_to_dict(a) for a in adjuntos]
                    inc_list.append(idict)
                tdict['incidencias'] = inc_list
                export_data.append(tdict)
            return export_data
        except Exception as e:
            self.logger.error(f"Error exportando datos: {e}")
            return []
        finally:
            session.close()

    def get_all_ordenes_fabricacion(self) -> list[str]:
        session = self.session_factory()
        try:
            ordenes = session.query(TrabajoLog.orden_fabricacion).distinct().filter(
                TrabajoLog.orden_fabricacion.isnot(None), TrabajoLog.orden_fabricacion != ""
            ).order_by(TrabajoLog.orden_fabricacion).all()
            return [of[0] for of in ordenes if of[0]]
        except SQLAlchemyError as e:
            self.logger.error(f"Error OFs: {e}")
            return []
        finally:
            session.close()

    def get_fabricaciones_por_trabajador(self, trabajador_id: int) -> List[FabricacionAsignadaDTO]:
        """
        Obtiene las fabricaciones asignadas a un trabajador incluyendo sus productos.

        Realiza un JOIN entre la tabla de enlace de asignaciones y las fabricaciones,
        trayendo además los productos vinculados a cada una mediante un outer join.
        Agrupa los resultados para construir objetos FabricacionAsignadaDTO.

        Args:
            trabajador_id: ID del trabajador cuyas asignaciones se desean recuperar.

        Returns:
            Lista de DTOs con la información de las fabricaciones y sus productos.
        """
        session = self.session_factory()
        try:
            query_results = session.query(
                Fabricacion.id, Fabricacion.codigo, Fabricacion.descripcion,
                trabajador_fabricacion_link.c.fecha_asignacion,
                trabajador_fabricacion_link.c.estado,
                fabricacion_productos.c.producto_codigo,
                fabricacion_productos.c.cantidad,
                Producto.descripcion.label('producto_descripcion')
            ).join(
                trabajador_fabricacion_link,
                Fabricacion.id == trabajador_fabricacion_link.c.fabricacion_id
            ).outerjoin(
                fabricacion_productos,
                Fabricacion.id == fabricacion_productos.c.fabricacion_id
            ).outerjoin(
                Producto,
                fabricacion_productos.c.producto_codigo == Producto.codigo
            ).filter(
                trabajador_fabricacion_link.c.trabajador_id == trabajador_id
            ).order_by(
                trabajador_fabricacion_link.c.fecha_asignacion.desc()
            ).all()

            fabricaciones_dict = {}
            for row in query_results:
                if row.id not in fabricaciones_dict:
                    fabricaciones_dict[row.id] = FabricacionAsignadaDTO(
                        id=row.id, codigo=row.codigo or "", descripcion=row.descripcion or "",
                        fecha_asignacion=row.fecha_asignacion, estado=row.estado or "",
                        productos=[]
                    )
                if row.producto_codigo:
                    fabricaciones_dict[row.id].productos.append(FabricacionProductoDTO(
                        producto_codigo=row.producto_codigo,
                        descripcion=row.producto_descripcion or "",
                        cantidad=row.cantidad
                    ))
            return list(fabricaciones_dict.values())
        except SQLAlchemyError as e:
            self.logger.error(f"Error obteniendo fabricaciones por trabajador: {e}")
            return []
        finally:
            session.close()
