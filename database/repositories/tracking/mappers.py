# database/repositories/tracking/mappers.py
"""
Capa de datos (`mappers`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from typing import Optional, Any, cast
from datetime import datetime
from database.models import (
    TrabajoLog, IncidenciaLog, IncidenciaAdjunto, Trabajador, Fabricacion, Producto, Maquina, PasoTrazabilidad
)
from core.tracking_dtos import (
    TrabajoLogDTO, PasoTrazabilidadDTO, IncidenciaLogDTO, IncidenciaAdjuntoDTO
)

class TrackingMapper:
    """Utilidad para mapear modelos de Trazabilidad a DTOs."""

    @staticmethod
    def map_to_trabajo_log_dto(trabajo: Any, logger: Any = None) -> Optional[TrabajoLogDTO]:
        if not trabajo: return None
        dto = TrabajoLogDTO(
            id=trabajo.id or 0, qr_code=trabajo.qr_code or "", estado=trabajo.estado or "",
            tiempo_inicio=trabajo.tiempo_inicio or datetime.min, tiempo_fin=trabajo.tiempo_fin,
            duracion_segundos=trabajo.duracion_segundos, notas=trabajo.notas,
            trabajador_id=trabajador_id if (trabajador_id := getattr(trabajo, 'trabajador_id', 0)) else 0,
            trabajador_nombre=cast(Trabajador, trabajo.trabajador).nombre_completo if getattr(trabajo, 'trabajador', None) else "",
            fabricacion_id=fab_id if (fab_id := getattr(trabajo, 'fabricacion_id', 0)) else 0,
            fabricacion_codigo=cast(Fabricacion, trabajo.fabricacion).codigo if getattr(trabajo, 'fabricacion', None) else "",
            fabricacion_descripcion=cast(Fabricacion, trabajo.fabricacion).descripcion if getattr(trabajo, 'fabricacion', None) else "",
            producto_codigo=trabajo.producto_codigo or "",
            producto_descripcion=cast(Producto, trabajo.producto).descripcion if getattr(trabajo, 'producto', None) else "",
            orden_fabricacion=trabajo.orden_fabricacion
        )
        try:
            dto.incidencias = [i_dto for i in getattr(trabajo, 'incidencias', []) if (i_dto := TrackingMapper.map_to_incidencia_log_dto(i, logger))]
            dto.pasos_trazabilidad = [p_dto for p in getattr(trabajo, 'pasos_trazabilidad', []) if (p_dto := TrackingMapper.map_to_paso_trazabilidad_dto(p, logger))]
        except Exception as e:
            if logger: logger.warning("Error mapeando relaciones de trabajo %s: %s", trabajo.id, e)
        return dto

    @staticmethod
    def map_to_incidencia_log_dto(incidencia: Any, logger: Any = None) -> Optional[IncidenciaLogDTO]:
        if not incidencia: return None
        dto = IncidenciaLogDTO(
            id=incidencia.id or 0, tipo_incidencia=incidencia.tipo_incidencia or "",
            descripcion=incidencia.descripcion or "", fecha_reporte=incidencia.fecha_reporte or datetime.min,
            estado=incidencia.estado or "", resolucion=incidencia.resolucion or "", fecha_resolucion=incidencia.fecha_resolucion,
            trabajador_nombre=cast(Trabajador, incidencia.trabajador).nombre_completo if getattr(incidencia, 'trabajador', None) else ""
        )
        try:
            dto.adjuntos = [a_dto for a in getattr(incidencia, 'adjuntos', []) if (a_dto := TrackingMapper.map_to_incidencia_adjunto_dto(a))]
        except Exception as e:
            if logger: logger.warning("Error mapeando adjuntos de incidencia %s: %s", incidencia.id, e)
        return dto

    @staticmethod
    def map_to_incidencia_adjunto_dto(adjunto: Any) -> Optional[IncidenciaAdjuntoDTO]:
        if not adjunto: return None
        return IncidenciaAdjuntoDTO(id=adjunto.id or 0, ruta_archivo=adjunto.ruta_archivo or "", tipo_archivo=getattr(adjunto, 'tipo_mime', ""))

    @staticmethod
    def map_to_paso_trazabilidad_dto(paso: Any, logger: Any = None) -> Optional[PasoTrazabilidadDTO]:
        if not paso: return None
        return PasoTrazabilidadDTO(
            id=paso.id or 0, trabajo_log_id=paso.trabajo_log_id or 0, paso_nombre=paso.paso_nombre or "",
            tipo_paso=paso.tipo_paso or "", estado_paso=paso.estado_paso or "",
            tiempo_inicio_paso=paso.tiempo_inicio_paso or datetime.min, tiempo_fin_paso=paso.tiempo_fin_paso,
            duracion_paso_segundos=paso.duracion_paso_segundos, maquina_id=paso.maquina_id,
            maquina_nombre=cast(Maquina, paso.maquina).nombre if getattr(paso, 'maquina', None) else "",
            trabajador_nombre=cast(Trabajador, paso.trabajador).nombre_completo if getattr(paso, 'trabajador', None) else ""
        )
