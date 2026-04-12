# -*- coding: utf-8 -*-
"""
Nombre del Módulo: tracking_log_repository
Descripción: Logs de trabajo, pasos de trazabilidad y consultas pesadas vía subgestores.

Compone ``TrackingCoreManager``, ``TrackingStepsManager``, ``TrackingQueriesManager`` y
``TrackingMapper`` para no concentrar todo el SQL en una sola clase.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from database.repositories.base import BaseRepository
from core.tracking_dtos import (
    FabricacionAsignadaDTO,
    IncidenciaAdjuntoDTO,
    IncidenciaLogDTO,
    PasoTrazabilidadDTO,
    TrabajoLogDTO,
)
from .tracking.core_manager import TrackingCoreManager
from .tracking.steps_manager import TrackingStepsManager
from .tracking.queries_manager import TrackingQueriesManager
from .tracking.mappers import TrackingMapper


class TrackingLogRepository(BaseRepository):
    """
    Repositorio para gestión de logs de trabajo y pasos de trazabilidad.
    Implementa el patrón Fachada delegando en managers especializados.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        super().__init__(session_factory)
        self.logger = logging.getLogger("EvolucionTiemposApp.TrackingLogRepository")

        self.core = TrackingCoreManager(session_factory)
        self.steps = TrackingStepsManager(session_factory)
        self.queries = TrackingQueriesManager(session_factory)

    def _map_to_trabajo_log_dto(self, trabajo: Any, _logger: Any = None, **kwargs: Any) -> Optional[TrabajoLogDTO]:
        """
        Wrapper de compatibilidad.

        Algunos tests pasan `logger` como argumento posicional o keyword; se ignora y
        se usa siempre `self.logger` para evitar duplicidad en la llamada al mapper.
        """
        kwargs_no_logger = {k: v for k, v in kwargs.items() if k != "logger"}
        return TrackingMapper.map_to_trabajo_log_dto(trabajo, logger=self.logger, **kwargs_no_logger)

    def _map_to_incidencia_log_dto(
        self, incidencia: Any, _logger: Any = None, **kwargs: Any
    ) -> Optional[IncidenciaLogDTO]:
        """Wrapper de compatibilidad; ver `_map_to_trabajo_log_dto`."""
        kwargs_no_logger = {k: v for k, v in kwargs.items() if k != "logger"}
        return TrackingMapper.map_to_incidencia_log_dto(incidencia, logger=self.logger, **kwargs_no_logger)

    def _map_to_incidencia_adjunto_dto(self, adjunto: Any) -> Optional[IncidenciaAdjuntoDTO]:
        return TrackingMapper.map_to_incidencia_adjunto_dto(adjunto)

    def _map_to_paso_trazabilidad_dto(
        self, paso: Any, _logger: Any = None, **kwargs: Any
    ) -> Optional[PasoTrazabilidadDTO]:
        """Wrapper de compatibilidad; ver `_map_to_trabajo_log_dto`."""
        kwargs_no_logger = {k: v for k, v in kwargs.items() if k != "logger"}
        return TrackingMapper.map_to_paso_trazabilidad_dto(paso, logger=self.logger, **kwargs_no_logger)

    def obtener_o_crear_trabajo_log_por_qr(
        self,
        qr_code: str,
        trabajador_id: int,
        fabricacion_id: int,
        producto_codigo: str,
        orden_fabricacion: Optional[str] = None,
        notas: Optional[str] = None,
    ) -> Optional[TrabajoLogDTO]:
        return self.core.obtener_o_crear_trabajo_log_por_qr(
            qr_code, trabajador_id, fabricacion_id, producto_codigo, orden_fabricacion, notas
        )

    def iniciar_trabajo(
        self, qr_code: str, trabajador_id: int, fabricacion_id: int, producto_codigo: str
    ) -> Optional[TrabajoLogDTO]:
        return self.core.iniciar_trabajo(qr_code, trabajador_id, fabricacion_id, producto_codigo)

    def finalizar_trabajo_log(
        self, trabajo_log_id: int, notas_finalizacion: Optional[str] = None
    ) -> Optional[TrabajoLogDTO]:
        return self.core.finalizar_trabajo_log(trabajo_log_id, notas_finalizacion)

    def pausar_trabajo(self, qr_code: str, motivo: str) -> bool:
        return self.core.pausar_trabajo(qr_code, motivo)

    def reanudar_trabajo(self, qr_code: str) -> bool:
        return self.core.reanudar_trabajo(qr_code)

    def obtener_trabajo_por_qr(self, qr_code: str) -> Optional[TrabajoLogDTO]:
        return self.core.obtener_trabajo_por_qr(qr_code)

    def obtener_trabajo_por_id(self, trabajo_log_id: int) -> Optional[TrabajoLogDTO]:
        return self.core.obtener_trabajo_por_id(trabajo_log_id)

    def obtener_trabajos_activos(
        self, trabajador_id: Optional[int] = None, fabricacion_id: Optional[int] = None
    ) -> List[TrabajoLogDTO]:
        return self.core.obtener_trabajos_activos(trabajador_id, fabricacion_id)

    def get_trabajo_logs_por_trabajador(self, trabajador_id: int) -> List[TrabajoLogDTO]:
        return self.core.get_trabajo_logs_por_trabajador(trabajador_id)

    def upsert_trabajo_log_from_dict(self, data: Dict[str, Any]) -> Tuple[str, Optional[int]]:
        return self.core.upsert_trabajo_log_from_dict(data)

    def get_paso_activo_por_trabajador(self, trabajador_id: int) -> Optional[PasoTrazabilidadDTO]:
        return self.steps.get_paso_activo_por_trabajador(trabajador_id)

    def get_ultimo_paso_para_qr(self, trabajo_log_id: int) -> Optional[PasoTrazabilidadDTO]:
        return self.steps.get_ultimo_paso_para_qr(trabajo_log_id)

    def iniciar_nuevo_paso(
        self,
        trabajo_log_id: int,
        trabajador_id: int,
        paso_nombre: str,
        tipo_paso: str,
        maquina_id: Optional[int] = None,
    ) -> Optional[PasoTrazabilidadDTO]:
        return self.steps.iniciar_nuevo_paso(
            trabajo_log_id, trabajador_id, paso_nombre, tipo_paso, maquina_id
        )

    def finalizar_paso(self, paso_id: int) -> Optional[PasoTrazabilidadDTO]:
        return self.steps.finalizar_paso(paso_id)

    def get_data_for_export(self, trabajador_id: int, since_date: datetime) -> List[Dict[str, Any]]:
        return self.queries.get_data_for_export(trabajador_id, since_date)

    def get_all_ordenes_fabricacion(self) -> List[str]:
        return self.queries.get_all_ordenes_fabricacion()

    def get_fabricaciones_por_trabajador(self, trabajador_id: int) -> List[FabricacionAsignadaDTO]:
        """
        Delega la obtención de fabricaciones asignadas al gestor de consultas.

        Args:
            trabajador_id: ID del trabajador.

        Returns:
            Lista de DTOs de fabricaciones asignadas.
        """
        return self.queries.get_fabricaciones_por_trabajador(trabajador_id)
