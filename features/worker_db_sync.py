"""
Servicio para la sincronización y persistencia de datos del trabajador.
Actúa como fachada para el repositorio de trazabilidad y otras operaciones de BD.

Las fabricaciones asignadas a la lista del trabajador se exponen como
``WorkerTaskListRowDTO`` (ver ``get_assigned_fabricaciones``), no como dicts opacos.
"""

import logging
from typing import Any, Dict, List, Optional, cast
from datetime import datetime

from core.worker_ui_dtos import WorkerTaskListRowDTO

class WorkerDbSync:
    """
    Maneja las operaciones de lectura/escritura en base de datos para el trabajador.
    """

    def __init__(
        self, tracking_repo: Any, logger: Optional[logging.Logger] = None
    ) -> None:
        self.tracking_repo = tracking_repo
        self.logger = logger or logging.getLogger("EvolucionTiemposApp.WorkerDbSync")

    def get_assigned_fabricaciones(self, trabajador_id: int) -> List[WorkerTaskListRowDTO]:
        """
        Obtiene y formatea las fabricaciones asignadas a un trabajador para la UI.

        Solicita al repositorio las asignaciones (como DTOs) y devuelve filas tipadas
        (`WorkerTaskListRowDTO`) para la lista del trabajador.

        Args:
            trabajador_id: ID del trabajador logueado.

        Returns:
            Lista de DTOs con id, codigo, producto_codigo, etc.
        """
        try:
            fabricaciones = self.tracking_repo.get_fabricaciones_por_trabajador(trabajador_id)
            result = []
            for fab in fabricaciones:
                # fab puede ser FabricacionAsignadaDTO o dict según la versión del repositorio
                is_dto = not isinstance(fab, dict)
                
                productos = fab.productos if is_dto else fab.get('productos', [])
                producto_info = productos[0] if productos else None
                
                # Extraer info del producto (producto_info puede ser FabricacionProductoDTO o dict)
                prod_cod = ""
                prod_desc = ""
                prod_cant = 0
                
                if producto_info:
                    if not isinstance(producto_info, dict): # DTO
                        prod_cod = getattr(producto_info, 'producto_codigo', '')
                        prod_desc = getattr(producto_info, 'descripcion', '')
                        prod_cant = getattr(producto_info, 'cantidad', 0)
                    else: # dict
                        prod_cod = str(producto_info.get('producto_codigo', producto_info.get('codigo', '')) or '')
                        prod_desc = str(producto_info.get('descripcion', '') or '')
                        prod_cant = int(producto_info.get('cantidad', 0) or 0)

                result.append(
                    WorkerTaskListRowDTO(
                        id=fab.id if is_dto else fab.get("id"),
                        codigo=str((fab.codigo if is_dto else fab.get("codigo")) or ""),
                        descripcion=str((fab.descripcion if is_dto else fab.get("descripcion")) or ""),
                        producto_codigo=prod_cod,
                        producto_descripcion=prod_desc,
                        cantidad=prod_cant,
                        fecha_asignacion=fab.fecha_asignacion if is_dto else fab.get("fecha_asignacion"),
                        estado=fab.estado if is_dto else fab.get("estado"),
                        productos=productos,
                    )
                )
            return result
        except Exception as e:
            self.logger.error(f"Error al obtener fabricaciones asignadas: {e}", exc_info=True)
            return []

    def get_active_trabajos(self, trabajador_id: int) -> List[Any]:
        """Obtiene los trabajos actualmente en proceso para el trabajador."""
        try:
            return cast(List[Any], self.tracking_repo.obtener_trabajos_activos(trabajador_id))
        except Exception as e:
            self.logger.error(f"Error al obtener trabajos activos: {e}", exc_info=True)
            return []

    def get_paso_activo(self, trabajador_id: int) -> Optional[Any]:
        """Obtiene el paso actual en proceso del trabajador."""
        try:
            return self.tracking_repo.get_paso_activo_por_trabajador(trabajador_id)
        except Exception as e:
            self.logger.error(f"Error al obtener paso activo: {e}", exc_info=True)
            return None

    def get_trabajo_por_qr(self, qr_code: str) -> Optional[Any]:
        """Busca el historial (TrabajoLog) de una unidad por su QR."""
        return self.tracking_repo.obtener_trabajo_por_qr(qr_code)

    def get_trabajo_por_id(self, trabajo_log_id: int) -> Optional[Any]:
        """Obtiene un TrabajoLog por su ID."""
        return self.tracking_repo.obtener_trabajo_por_id(trabajo_log_id)

    def iniciar_o_recuperar_trabajo(self, qr_code: str, trabajador_id: int, 
                                   fabricacion_id: int, producto_codigo: str, 
                                   orden_fabricacion: Optional[str] = None) -> Optional[Any]:
        """
        Inicia un nuevo registro de unidad o recupera uno existente.
        """
        try:
            return self.tracking_repo.obtener_o_crear_trabajo_log_por_qr(
                qr_code=qr_code,
                trabajador_id=trabajador_id,
                fabricacion_id=fabricacion_id,
                producto_codigo=producto_codigo,
                orden_fabricacion=orden_fabricacion
            )
        except Exception as e:
            self.logger.error(f"Error al iniciar/recuperar trabajo log: {e}", exc_info=True)
            return None

    def iniciar_paso(self, trabajo_log_id: int, trabajador_id: int, 
                     paso_nombre: str, tipo_paso: str = "standard_process") -> Optional[Any]:
        """Registra el inicio de un nuevo paso de trabajo."""
        try:
            return self.tracking_repo.iniciar_nuevo_paso(
                trabajo_log_id=trabajo_log_id,
                trabajador_id=trabajador_id,
                paso_nombre=paso_nombre,
                tipo_paso=tipo_paso,
                maquina_id=None
            )
        except Exception as e:
            self.logger.error(f"Error al iniciar paso: {e}", exc_info=True)
            return None

    def finalizar_paso(self, paso_id: int) -> Optional[Any]:
        """Registra la finalización de un paso de trabajo."""
        try:
            return self.tracking_repo.finalizar_paso(paso_id)
        except Exception as e:
            self.logger.error(f"Error al finalizar paso: {e}", exc_info=True)
            return None

    def registrar_incidencia(self, trabajo_log_id: int, trabajador_id: int, 
                             tipo: str, descripcion: str, fotos: List[str]) -> Optional[Any]:
        """Registra una incidencia asociada a un trabajo."""
        try:
            return self.tracking_repo.registrar_incidencia(
                trabajo_log_id=trabajo_log_id,
                trabajador_id=trabajador_id,
                tipo_incidencia=tipo,
                descripcion=descripcion,
                rutas_fotos=fotos
            )
        except Exception as e:
            self.logger.error(f"Error al registrar incidencia: {e}", exc_info=True)
            return None

    def get_estadisticas(self, trabajador_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene estadísticas de rendimiento del trabajador."""
        try:
            return cast(Dict[str, Any] | None, self.tracking_repo.obtener_estadisticas_trabajador(trabajador_id))
        except Exception as e:
            self.logger.error(f"Error al obtener estadísticas: {e}", exc_info=True)
            return None

    def get_data_for_export(self, trabajador_id: int, last_export_date: datetime) -> List[Dict[str, Any]]:
        """Obtiene datos nuevos para exportación."""
        return cast(List[Dict[str, Any]], self.tracking_repo.get_data_for_export(trabajador_id, last_export_date))
