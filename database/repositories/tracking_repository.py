# -*- coding: utf-8 -*-
"""
========================================================================
TRACKING REPOSITORY - GESTIÓN DE TRAZABILIDAD Y SEGUIMIENTO (FACADE)
========================================================================
Repositorio principal que ahora actúa como Facade delegando a:
- TrackingLogRepository
- IncidenciaRepository
- TrackingStatsRepository

Autor: Sistema de Trazabilidad
Fecha: 2025
========================================================================
"""

import logging
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime

from .base import BaseRepository
from database.models import Trabajador
from core.tracking_dtos import (
    TrabajoLogDTO, PasoTrazabilidadDTO, IncidenciaLogDTO, 
    IncidenciaAdjuntoDTO, FabricacionAsignadaDTO
)

# Import New Repositories
from database.repositories.tracking_log_repository import TrackingLogRepository
from database.repositories.incidencia_repository import IncidenciaRepository
from database.repositories.tracking_stats_repository import TrackingStatsRepository

class TrackingRepository(BaseRepository):
    """
    Repositorio FACADE para operaciones de tracking y trazabilidad.
    Delega la lógica a repositorios especializados.
    """

    def __init__(self, session_factory: Any) -> None:
        """
        Inicializa el repositorio y sus sub-repositorios.
        """
        super().__init__(session_factory)
        self.logger = logging.getLogger("EvolucionTiemposApp.TrackingRepository")
        
        # Initialize sub-repositories
        self.log_repo = TrackingLogRepository(session_factory)
        self.incidencia_repo = IncidenciaRepository(session_factory)
        self.stats_repo = TrackingStatsRepository(session_factory)

    # ========================================================================
    # DELEGACIÓN: TRABAJO LOGS
    # ========================================================================


    def obtener_o_crear_trabajo_log_por_qr(self, qr_code: str, trabajador_id: int, fabricacion_id: int, producto_codigo: str, orden_fabricacion: Optional[str] = None, notas: Optional[str] = None) -> Optional[TrabajoLogDTO]:
        return self.log_repo.obtener_o_crear_trabajo_log_por_qr(qr_code, trabajador_id, fabricacion_id, producto_codigo, orden_fabricacion, notas)

    def iniciar_trabajo(self, qr_code: str, trabajador_id: int, fabricacion_id: int, producto_codigo: str) -> Optional[TrabajoLogDTO]:
        return self.log_repo.iniciar_trabajo(qr_code, trabajador_id, fabricacion_id, producto_codigo)

    def finalizar_trabajo_log(self, trabajo_log_id: int, notas_finalizacion: Optional[str] = None) -> Optional[TrabajoLogDTO]:
        return self.log_repo.finalizar_trabajo_log(trabajo_log_id, notas_finalizacion)

    def pausar_trabajo(self, qr_code: str, motivo: str) -> bool:
        return self.log_repo.pausar_trabajo(qr_code, motivo)

    def reanudar_trabajo(self, qr_code: str) -> bool:
        return self.log_repo.reanudar_trabajo(qr_code)

    def obtener_trabajo_por_qr(self, qr_code: str) -> Optional[TrabajoLogDTO]:
        return self.log_repo.obtener_trabajo_por_qr(qr_code)

    def obtener_trabajo_por_id(self, trabajo_log_id: int) -> Optional[TrabajoLogDTO]:
        return self.log_repo.obtener_trabajo_por_id(trabajo_log_id)
    
    def get_paso_activo_por_trabajador(self, trabajador_id: int) -> Optional[PasoTrazabilidadDTO]:
        return self.log_repo.get_paso_activo_por_trabajador(trabajador_id)

    def get_ultimo_paso_para_qr(self, trabajo_log_id: int) -> Optional[PasoTrazabilidadDTO]:
        return self.log_repo.get_ultimo_paso_para_qr(trabajo_log_id)

    def iniciar_nuevo_paso(self, trabajo_log_id: int, trabajador_id: int, paso_nombre: str, tipo_paso: str, maquina_id: Optional[int] = None) -> Optional[PasoTrazabilidadDTO]:
        return self.log_repo.iniciar_nuevo_paso(trabajo_log_id, trabajador_id, paso_nombre, tipo_paso, maquina_id)

    def finalizar_paso(self, paso_id: int) -> Optional[PasoTrazabilidadDTO]:
        return self.log_repo.finalizar_paso(paso_id)

    def obtener_trabajos_activos(self, trabajador_id: Optional[int] = None, fabricacion_id: Optional[int] = None) -> List[TrabajoLogDTO]:
        return self.log_repo.obtener_trabajos_activos(trabajador_id, fabricacion_id)


    def get_trabajo_logs_por_trabajador(self, trabajador_id: int) -> List[TrabajoLogDTO]:
        return self.log_repo.get_trabajo_logs_por_trabajador(trabajador_id)

    def upsert_trabajo_log_from_dict(self, data: Dict[str, Any]) -> Tuple[str, Optional[int]]:
        return self.log_repo.upsert_trabajo_log_from_dict(data)

    def get_data_for_export(self, trabajador_id: int, since_date: datetime) -> List[Dict[str, Any]]:
        return self.log_repo.get_data_for_export(trabajador_id, since_date)

    def get_all_ordenes_fabricacion(self) -> List[str]:
        return self.log_repo.get_all_ordenes_fabricacion()

    def get_fabricaciones_por_trabajador(self, trabajador_id: int) -> List[FabricacionAsignadaDTO]:
        """
        Obtiene las fabricaciones asignadas a un trabajador (vía log_repo).

        Args:
            trabajador_id: ID del trabajador.

        Returns:
            Lista de fabricaciones con sus productos asociados en formato DTO.
        """
        return self.log_repo.get_fabricaciones_por_trabajador(trabajador_id)

    # ========================================================================
    # DELEGACIÓN: INCIDENCIAS
    # ========================================================================

    def registrar_incidencia(self, trabajo_log_id: int, trabajador_id: int, tipo_incidencia: str, descripcion: str, rutas_fotos: Optional[List[str]] = None) -> Optional[IncidenciaLogDTO]:
        return self.incidencia_repo.registrar_incidencia(trabajo_log_id, trabajador_id, tipo_incidencia, descripcion, rutas_fotos)
    
    # Note: _crear_adjunto is internal/private, generally not exposed in facade unless necessary.
    # But if existing external code calls it (unlikely for private), we should expose it or fix caller.
    # Assuming standard usage, only public methods are called.

    def añadir_foto_a_incidencia(self, incidencia_id: int, ruta_foto: str, descripcion: Optional[str] = None) -> Optional[IncidenciaAdjuntoDTO]:
        return self.incidencia_repo.añadir_foto_a_incidencia(incidencia_id, ruta_foto, descripcion)

    def resolver_incidencia(self, incidencia_id: int, resolucion: str) -> Optional[IncidenciaLogDTO]:
        return self.incidencia_repo.resolver_incidencia(incidencia_id, resolucion)

    def obtener_incidencias_abiertas(self, fabricacion_id: Optional[int] = None) -> List[IncidenciaLogDTO]:
        return self.incidencia_repo.obtener_incidencias_abiertas(fabricacion_id)

    # ========================================================================
    # DELEGACIÓN: ESTADÍSTICAS
    # ========================================================================

    def obtener_estadisticas_trabajador(self, trabajador_id: int, fecha_inicio: Optional[datetime] = None, fecha_fin: Optional[datetime] = None) -> Dict:
        return self.stats_repo.obtener_estadisticas_trabajador(trabajador_id, fecha_inicio, fecha_fin)

    def obtener_estadisticas_fabricacion(self, fabricacion_id: int) -> Dict:
        return self.stats_repo.obtener_estadisticas_fabricacion(fabricacion_id)

    def obtener_trabajadores_de_fabricacion(self, fabricacion_id: int) -> List[Trabajador]:
        return self.stats_repo.obtener_trabajadores_de_fabricacion(fabricacion_id)

    def import_tasks_from_csv(self, file_path: str) -> bool:
        """
        Importa tareas desde un archivo CSV. (Stub para compatibilidad UI)
        """
        self.logger.info(f"Solicitud de importación de tareas desde: {file_path}")
        # La lógica de importación real debería ir aquí o en un servicio dedicado
        return False

    # ========================================================================
    # Helper Accessors (if needed for testing/mocking)
    # ========================================================================
    # Some older tests might mock `_map_to_trabajo_log_dto` directly on TrackingRepository.
    # If so, they will fail because the method is gone.
    # We can add proxies if strictly necessary, but better to update tests.
    # For now, we assume public API compatibility is the goal.
