"""
Controlador para la interfaz de trabajador.

Maneja la lógica de negocio para trabajadores:
- Carga de fabricaciones asignadas
- Registro de tiempos mediante QR
- Gestión de incidencias
- Comunicación con la base de datos
"""

import logging
from typing import Any, Callable, Dict, Optional
try:
    import cv2
except (ImportError, AttributeError):
    from unittest.mock import MagicMock
    cv2 = MagicMock()
from core.camera_manager import CameraBackend
from core.interfaces.worker_view_interface import IWorkerView
from PyQt6.QtWidgets import (
    QDialog, QMessageBox
)

# New Imports for Phase 4
from core.production_context import ProductionContext
from features.worker_validation_service import WorkerValidationService
from features.worker_db_sync import WorkerDbSync
from features.worker_incidence_dialog import IncidenceDialog
from features.worker_controller_io_manager import WorkerIOManager

# ============================================================================
# CLASE DEL CONTROLADOR
# ============================================================================

class WorkerController:
    """Controlador para gestionar las operaciones de trabajadores."""

    def __init__(
            self,
            current_user: Any,
            db_manager: Any,
            main_window: IWorkerView,
            qr_scanner: Any = None,
            tracking_repo: Any = None,
            label_manager: Any = None,
            qr_generator: Any = None,
            label_counter_repo: Any = None,
            camera_config_runner: Optional[Callable[[], None]] = None,
    ) -> None:
        self.current_user = current_user
        self.db_manager = db_manager
        self.main_window = main_window
        self.qr_scanner = qr_scanner
        
        # Servicios
        self.tracking_repo = tracking_repo or db_manager.tracking_repo
        self.db_sync = WorkerDbSync(self.tracking_repo)
        self.validation_service = WorkerValidationService(self.qr_scanner)

        self.label_manager = label_manager
        self.qr_generator = qr_generator
        self.label_counter_repo = label_counter_repo
        
        from core.camera_manager import CameraManager
        self.camera_manager = CameraManager()

        self.logger = logging.getLogger("EvolucionTiemposApp.WorkerController")
        self.context = ProductionContext()
        self.io_manager = WorkerIOManager(self, camera_config_runner=camera_config_runner)

    def _handle_generate_labels(self, task_data: Dict[str, Any]) -> None:
        self.io_manager._handle_generate_labels(task_data)

    def _process_label_document(self, doc_path: str) -> None:
        self.io_manager._process_label_document(doc_path)

    def _handle_export_data(self) -> None:
        self.io_manager._handle_export_data()

    def _handle_camera_config(self) -> None:
        self.io_manager._handle_camera_config()

    def initialize(self) -> None:
        """Inicializa los datos y conecta señales."""
        try:
            self.refresh_data()
            self._connect_signals()
        except Exception as e:
            self.logger.error(f"Error inicializando: {e}", exc_info=True)

    def _connect_signals(self) -> None:
        """Conecta las señales de la ventana."""
        self.main_window.logout_requested.connect(self._handle_logout)
        self.main_window.camera_config_requested.connect(self._handle_camera_config)
        self.main_window.task_selected.connect(self._handle_task_selected)
        self.main_window.generate_labels_requested.connect(self._handle_generate_labels)
        self.main_window.consult_qr_requested.connect(self._handle_consult_qr)
        self.main_window.start_task_requested.connect(self._handle_start_task)
        self.main_window.end_task_requested.connect(self._handle_end_task)
        self.main_window.register_incidence_requested.connect(self._handle_register_incidence)
        self.main_window.export_data_requested.connect(self._handle_export_data)

    def _load_assigned_fabricaciones(self) -> None:
        trabajador_id = self.current_user.id
        items = self.db_sync.get_assigned_fabricaciones(trabajador_id) if trabajador_id else []
        self.main_window.update_tasks_list(items)

    def _load_active_trabajos(self) -> None:
        trabajador_id = self.current_user.id
        if trabajador_id:
            self.db_sync.get_active_trabajos(trabajador_id)

    def refresh_data(self) -> None:
        """Recarga todos los datos."""
        self._load_assigned_fabricaciones()
        self._load_active_trabajos()

    def _handle_logout(self) -> None:
        import sys
        self.logger.info("Logout solicitado")
        sys.exit(0)

    def _handle_task_selected(self, task_data: Dict[str, Any]) -> None:
        """Actualiza el estado de la UI al seleccionar una tarea."""
        if not task_data:
            self.main_window.update_task_state("pendiente", None)
            return

        trabajador_id = self.current_user.id
        fabricacion_id = task_data.get('id')
        # self.main_window.generate_labels_btn.setEnabled(True) <- Esto ahora lo asume la vista al seleccionar


        if not trabajador_id: return
        try:
            paso_activo = self.db_sync.get_paso_activo(trabajador_id)
            if not paso_activo:
                self.main_window.update_task_state("pendiente", None)
                return

            trabajo_log = self.db_sync.get_trabajo_por_id(paso_activo.trabajo_log_id)
            if trabajo_log and trabajo_log.fabricacion_id == fabricacion_id:
                self.main_window.update_task_state("en_proceso", paso_activo.paso_nombre)
            else:
                self.main_window.update_task_state("pendiente", None)
                self.main_window.show_message("Aviso", "Tienes otra tarea en proceso.", "warning")

        except Exception as e:
            self.logger.error(f"Error en selección: {e}", exc_info=True)

    def _handle_consult_qr(self) -> None:
        """Maneja la consulta de un código QR."""
        if not self.qr_scanner: return
        self.main_window.show_message("Escáner", "Escanee para consultar...", "info")
        try:
            qr_data = self.qr_scanner.scan_once(timeout=30)
            if not qr_data: return

            is_valid, parsed_data, error_msg = self.validation_service.validate_qr_data(qr_data)
            if not is_valid:
                self.main_window.show_message("Inválido", error_msg, "warning")
                return

            trabajo = self.db_sync.get_trabajo_por_qr(qr_data)
            if not trabajo:
                self.main_window.show_message("Libre", "QR disponible.", "info")
                return

            msg = f"UNIDAD: {trabajo.qr_code[:10]}...\nEstado: {trabajo.estado}\n"
            if trabajo.pasos_trazabilidad:
                msg += "\nPasos:\n" + "\n".join([f"- {p.paso_nombre}" for p in trabajo.pasos_trazabilidad])
            self.main_window.show_message("Info", msg, "info")

        except Exception as e:
            self.logger.error(f"Error consulta: {e}", exc_info=True)

    def _handle_start_task(self, task_data: Dict[str, Any]) -> None:
        """Maneja el inicio de un paso."""
        if not self.qr_scanner: return
        trabajador_id = self.current_user.id
        rol = getattr(self.current_user, 'role', 'Operario')
        if not trabajador_id: return
        
        try:
            if self.db_sync.get_paso_activo(trabajador_id):
                self.main_window.show_message("Aviso", "Ya tienes un paso activo.", "warning")
                return

            self.main_window.show_message("Escáner", "Escanee la unidad...", "info")
            qr_data = self.qr_scanner.scan_once(timeout=30)
            if not qr_data: return

            is_valid, parsed_data, _ = self.validation_service.validate_qr_data(qr_data)
            
            fab_cod = task_data.get('producto_codigo')
            if not isinstance(fab_cod, str):
                self.main_window.show_message("Error", "Código de producto en la tarea no es válido.", "error")
                return

            if not is_valid or parsed_data is None:
                self.main_window.show_message("Error", "QR no válido.", "error")
                return
                
            parsed_cod = parsed_data.get('producto_codigo')
            if not isinstance(parsed_cod, str) or not self.validation_service.validate_product_match(parsed_cod, fab_cod)[0]:
                self.main_window.show_message("Error", "QR no coincide con el producto.", "error")
                return

            trabajo_log = self.db_sync.iniciar_o_recuperar_trabajo(qr_data, trabajador_id, int(task_data.get('id', 0)), fab_cod)
            if trabajo_log and self.db_sync.iniciar_paso(trabajo_log.id, trabajador_id, str(rol)):
                self._load_active_trabajos()
                self.main_window.update_task_state("en_proceso", rol)
                self.main_window.enable_action_buttons(True)
                self.main_window.show_message("Éxito", "Paso iniciado.", "info")

        except Exception as e:
            self.logger.error(f"Error inicio: {e}", exc_info=True)

    def _handle_end_task(self, task_data: Dict[str, Any]) -> None:
        """Maneja la finalización de un paso."""
        trabajador_id = self.current_user.id
        if not trabajador_id: return
        try:
            paso = self.db_sync.get_paso_activo(trabajador_id)
            if not paso: return

            trabajo = self.db_sync.get_trabajo_por_id(paso.trabajo_log_id)
            if not trabajo: return
            self.main_window.show_message("Escáner", f"Acerque QR ({trabajo.qr_code[:10]}...)", "info")
            qr = self.qr_scanner.scan_once(timeout=30)
            if qr == trabajo.qr_code and self.db_sync.finalizar_paso(paso.id):
                self._load_active_trabajos()
                self.main_window.update_task_state("pendiente", None)
                self.main_window.enable_action_buttons(False)
                self.main_window.show_message("Éxito", "Finalizado.", "info")
            else:
                self.main_window.show_message("Error", "QR no coincide.", "error")

        except Exception as e:
            self.logger.error(f"Error fin: {e}", exc_info=True)

    def _handle_register_incidence(self, task_data: Dict[str, Any]) -> None:
        """Maneja incidencias."""
        trabajador_id = self.current_user.id
        if not trabajador_id: return
        try:
            paso = self.db_sync.get_paso_activo(trabajador_id)
            if not paso: return
            trabajo = self.db_sync.get_trabajo_por_id(paso.trabajo_log_id)
            if not trabajo: return

            self.main_window.show_message("Escáner", "Confirme QR...", "info")
            if self.qr_scanner.scan_once() == trabajo.qr_code:
                dialog = IncidenceDialog(None)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    data = dialog.get_data()
                    if data and self.db_sync.registrar_incidencia(trabajo.id, trabajador_id, data['tipo_incidencia'], data['descripcion'], data['fotos_paths']):
                        self.main_window.show_message("OK", "Registrada.", "info")
        except Exception as e:
            self.logger.error(f"Error incidencia: {e}", exc_info=True)

