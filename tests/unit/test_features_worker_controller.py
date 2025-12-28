"""
Tests unitarios para features/worker_controller.py (Interfaz de Planta).
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, ANY
from PyQt6.QtCore import Qt

from features.worker_controller import WorkerController

@pytest.fixture
def mock_db_manager():
    db = MagicMock()
    db.tracking_repo = MagicMock()
    return db

@pytest.fixture
def mock_main_window():
    win = MagicMock()
    win.logout_requested = MagicMock()
    win.camera_config_requested = MagicMock()
    win.task_selected = MagicMock()
    win.generate_labels_requested = MagicMock()
    win.consult_qr_requested = MagicMock()
    win.start_task_requested = MagicMock()
    win.end_task_requested = MagicMock()
    win.register_incidence_requested = MagicMock()
    win.export_data_requested = MagicMock()
    win.show_message = MagicMock()
    return win

@pytest.fixture
def current_user():
    return {"id": 101, "nombre": "Operario Test", "role": "Trabajador"}

@pytest.fixture
def controller(current_user, mock_db_manager, mock_main_window):
    ctrl = WorkerController(
        current_user=current_user,
        db_manager=mock_db_manager,
        main_window=mock_main_window
    )
    return ctrl

class TestWorkerControllerBasics:
    """Tests básicos de inicialización y carga."""

    def test_init(self, controller, current_user, mock_db_manager, mock_main_window):
        assert controller.current_user == current_user
        assert controller.db_manager == mock_db_manager
        assert controller.main_window == mock_main_window
        assert controller.tracking_repo == mock_db_manager.tracking_repo

    def test_initialize_success(self, controller):
        with patch.object(controller, '_load_assigned_fabricaciones') as mock_load_fab, \
             patch.object(controller, '_load_active_trabajos') as mock_load_active, \
             patch.object(controller, '_connect_signals') as mock_connect:
            
            controller.initialize()
            
            mock_load_fab.assert_called_once()
            mock_load_active.assert_called_once()
            mock_connect.assert_called_once()

    def test_initialize_exception(self, controller, mock_main_window):
        with patch.object(controller, '_load_assigned_fabricaciones', side_effect=Exception("DB Error")):
            controller.initialize()
            mock_main_window.show_message.assert_called_with(
                "Error de Inicialización",
                ANY,
                "error"
            )

    def test_connect_signals(self, controller, mock_main_window):
        controller._connect_signals()
        
        # Verificar algunas conexiones críticas
        mock_main_window.logout_requested.connect.assert_called()
        mock_main_window.start_task_requested.connect.assert_called_with(controller._handle_start_task)
        mock_main_window.end_task_requested.connect.assert_called_with(controller._handle_end_task)

class TestWorkerControllerDataLoading:
    """Tests de carga de datos desde el repositorio."""

    def test_load_assigned_fabricaciones_success(self, controller, mock_db_manager, mock_main_window):
        # Mock de fabricaciones devueltas por el repo
        mock_fab = MagicMock()
        mock_fab.id = 1
        mock_fab.codigo = "FAB-001"
        mock_fab.descripcion = "Test Fab"
        mock_fab.productos = [{"codigo": "PROD-1", "descripcion": "P1", "cantidad": 10}]
        mock_fab.fecha_asignacion = "2023-01-01"
        mock_fab.estado = "pendiente"
        
        mock_db_manager.tracking_repo.get_fabricaciones_por_trabajador.return_value = [mock_fab]
        
        controller._load_assigned_fabricaciones()
        
        assert len(controller._fabricaciones_asignadas) == 1
        assert controller._fabricaciones_asignadas[0]['codigo'] == "FAB-001"
        mock_main_window.update_tasks_list.assert_called_once()

    def test_load_assigned_fabricaciones_no_user_id(self, controller, mock_main_window):
        controller.current_user = {}
        controller._load_assigned_fabricaciones()
        assert controller._fabricaciones_asignadas == []
        mock_main_window.update_tasks_list.assert_called_with([])

    def test_load_active_trabajos(self, controller, mock_db_manager):
        mock_db_manager.tracking_repo.obtener_trabajos_activos.return_value = [{"id": 50}]
        controller._load_active_trabajos()
        assert len(controller._trabajos_activos) == 1
        assert controller._trabajos_activos[0]['id'] == 50

class TestWorkerControllerLifecycle:
    """Tests del ciclo de vida de trabajo (Iniciar, Finalizar, Incidencias)."""

    def test_iniciar_trabajo_success(self, controller, mock_db_manager, mock_main_window):
        mock_trabajo = MagicMock()
        mock_trabajo.id = 1000
        mock_db_manager.tracking_repo.iniciar_trabajo.return_value = mock_trabajo
        
        with patch.object(controller, '_load_active_trabajos') as mock_reload:
            res = controller.iniciar_trabajo("QR-123", 1, "PROD-A")
            
            assert res == mock_trabajo
            mock_db_manager.tracking_repo.iniciar_trabajo.assert_called_with(
                qr_code="QR-123",
                trabajador_id=101,
                fabricacion_id=1,
                producto_codigo="PROD-A"
            )
            mock_reload.assert_called_once()
            mock_main_window.show_message.assert_called_with("Trabajo Iniciado", ANY, "info")

    def test_iniciar_trabajo_failure(self, controller, mock_db_manager):
        mock_db_manager.tracking_repo.iniciar_trabajo.return_value = None
        res = controller.iniciar_trabajo("QR-123", 1, "PROD-A")
        assert res is None

    def test_finalizar_trabajo_success(self, controller, mock_db_manager, mock_main_window):
        mock_db_manager.tracking_repo.finalizar_trabajo_log.return_value = MagicMock()
        
        with patch.object(controller, '_load_active_trabajos') as mock_reload:
            res = controller.finalizar_trabajo(1000)
            
            assert res is True
            mock_db_manager.tracking_repo.finalizar_trabajo_log.assert_called_with(1000)
            mock_reload.assert_called_once()
            mock_main_window.show_message.assert_called_with("Trabajo Finalizado", ANY, "info")

    def test_registrar_incidencia_success(self, controller, mock_db_manager, mock_main_window):
        mock_incidencia = MagicMock()
        mock_incidencia.id = 1
        mock_db_manager.tracking_repo.registrar_incidencia.return_value = mock_incidencia
        
        res = controller.registrar_incidencia(1000, "Parada", "Máquina rota", ["foto1.jpg"])
        
        assert res == mock_incidencia
        mock_db_manager.tracking_repo.registrar_incidencia.assert_called_with(
            trabajo_log_id=1000,
            trabajador_id=101,
            tipo_incidencia="Parada",
            descripcion="Máquina rota",
            rutas_fotos=["foto1.jpg"]
        )
        mock_main_window.show_message.assert_called_with("Incidencia Registrada", ANY, "info")

class TestWorkerControllerSignals:
    """Tests de manejadores de señales (Handlers)."""

    def test_handle_task_selected_libre(self, controller, mock_db_manager, mock_main_window):
        # Trabajador sin pasos activos
        mock_db_manager.tracking_repo.get_paso_activo_por_trabajador.return_value = None
        
        controller._handle_task_selected({"id": 1, "codigo": "FAB1"})
        
        mock_main_window.update_task_state.assert_called_with("pendiente", None)
        mock_main_window.generate_labels_btn.setEnabled.assert_called_with(True)

    def test_handle_task_selected_ocupado_otra(self, controller, mock_db_manager, mock_main_window):
        # Trabajador con paso activo en OTRA fabricación
        mock_paso = MagicMock()
        mock_paso.trabajo_log_id = 99
        mock_db_manager.tracking_repo.get_paso_activo_por_trabajador.return_value = mock_paso
        
        mock_trabajo = MagicMock()
        mock_trabajo.fabricacion_id = 555 # Diferente a la seleccionada (1)
        mock_db_manager.tracking_repo.obtener_trabajo_por_id.return_value = mock_trabajo
        
        controller._handle_task_selected({"id": 1, "codigo": "FAB1"})
        
        mock_main_window.update_task_state.assert_called_with("pendiente", None)
        mock_main_window.show_message.assert_called() # Aviso de que está en otra

class TestWorkerControllerQRHandlers:
    """Tests para los manejadores de QR y entrada de datos."""

    def test_handle_consult_qr_ready(self, controller, mock_db_manager, mock_main_window):
        # Escaneo exitoso de un QR disponible
        controller.qr_scanner = MagicMock()
        controller.qr_scanner.scan_once.return_value = "QR-DATA"
        controller.qr_scanner.parse_qr_data.return_value = {"producto_codigo": "P1", "unit_number": 5}
        mock_db_manager.tracking_repo.obtener_trabajo_por_qr.return_value = None
        
        controller._handle_consult_qr()
        
        mock_main_window.show_message.assert_any_call("QR DISPONIBLE", ANY, "info")

    def test_handle_consult_qr_in_use(self, controller, mock_db_manager, mock_main_window):
        # Escaneo de un QR que ya tiene historial
        controller.qr_scanner = MagicMock()
        controller.qr_scanner.scan_once.return_value = "QR-DATA"
        controller.qr_scanner.parse_qr_data.return_value = {"producto_codigo": "P1"}
        
        mock_trabajo = MagicMock()
        mock_trabajo.tiempo_inicio = datetime.now()
        mock_trabajo.producto_codigo = "P1"
        mock_trabajo.estado = "EN_PROCESO" # Override MagicMock default
        mock_db_manager.tracking_repo.obtener_trabajo_por_qr.return_value = mock_trabajo
        
        controller._handle_consult_qr()
        
        mock_main_window.show_message.assert_any_call(ANY, ANY, "warning")

    @patch('features.worker_controller.QInputDialog.getText')
    def test_handle_start_task_new_qr(self, mock_get_text, controller, mock_db_manager, mock_main_window):
        # Caso: QR nuevo -> Pide OF -> Crea TrabajoLog -> Inicia Paso
        controller.qr_scanner = MagicMock()
        controller.qr_scanner.scan_once.return_value = "QR-NEW"
        controller.qr_scanner.parse_qr_data.return_value = {"producto_codigo": "PROD-1"}
        
        mock_db_manager.tracking_repo.get_paso_activo_por_trabajador.return_value = None
        mock_db_manager.tracking_repo.obtener_trabajo_por_qr.return_value = None
        
        mock_get_text.return_value = ("OF-2023", True)
        
        mock_log = MagicMock()
        mock_log.id = 500
        mock_log.orden_fabricacion = "OF-2023"
        mock_db_manager.tracking_repo.obtener_o_crear_trabajo_log_por_qr.return_value = mock_log
        mock_db_manager.tracking_repo.get_ultimo_paso_para_qr.return_value = None
        
        mock_paso = MagicMock()
        mock_paso.id = 999
        mock_db_manager.tracking_repo.iniciar_nuevo_paso.return_value = mock_paso
        
        controller._handle_start_task({"id": 1, "producto_codigo": "PROD-1"})
        
        mock_get_text.assert_called()
        mock_db_manager.tracking_repo.iniciar_nuevo_paso.assert_called()
        mock_main_window.update_task_state.assert_called_with("en_proceso", ANY)

    def test_handle_end_task_confirm_qr(self, controller, mock_db_manager, mock_main_window):
        # Caso: Finalizar paso -> Pide confirmación escaneando el MISMO QR
        mock_paso = MagicMock()
        mock_paso.id = 99
        mock_paso.trabajo_log_id = 500
        mock_db_manager.tracking_repo.get_paso_activo_por_trabajador.return_value = mock_paso
        
        mock_log = MagicMock()
        mock_log.qr_code = "QR-MATCH"
        mock_db_manager.tracking_repo.obtener_trabajo_por_id.return_value = mock_log
        
        controller.qr_scanner = MagicMock()
        controller.qr_scanner.scan_once.return_value = "QR-MATCH"
        
        mock_paso_fin = MagicMock()
        mock_paso_fin.paso_nombre = "Paso Genérico 1"
        mock_paso_fin.trabajo_log_id = 500
        mock_db_manager.tracking_repo.finalizar_paso.return_value = mock_paso_fin
        
        # Simular que es el último paso
        mock_db_manager.tracking_repo.finalizar_trabajo_log.return_value = MagicMock()
        
        controller._handle_end_task({})
        
        mock_db_manager.tracking_repo.finalizar_paso.assert_called_with(99)
        mock_main_window.update_task_state.assert_called_with("pendiente", None)

class TestWorkerControllerLabelGeneration:
    """Tests para la generación de etiquetas QR (Paso 18)."""

    @patch('features.worker_controller.QInputDialog.getInt')
    def test_handle_generate_labels_success(self, mock_get_int, controller, mock_main_window):
        # Configurar mocks de managers
        controller.label_manager = MagicMock()
        controller.qr_generator = MagicMock()
        controller.label_counter_repo = MagicMock()
        
        # Plantilla tiene 4 QRs
        controller.label_manager.count_qr_placeholders.return_value = 4
        # Usuario pide 2 hojas (8 QRs total)
        mock_get_int.return_value = (2, True)
        
        # Mock para range object con atributos start/end
        from collections import namedtuple
        RangeMock = namedtuple('RangeMock', ['start', 'end'])
        controller.label_counter_repo.get_next_unit_range.return_value = RangeMock(1, 8)
        
        # Generación de ID único
        controller.qr_generator.generate_unique_id.return_value = "UNIQUE-ID"
        # Ruta del documento generado
        controller.label_manager.generate_labels.return_value = "/tmp/labels.docx"
        controller.label_manager.print_document.return_value = True
        
        controller._handle_generate_labels({"id": 1, "producto_codigo": "P1"})
        
        controller.label_manager.generate_labels.assert_called()
        controller.label_manager.print_document.assert_called_with("/tmp/labels.docx")
        mock_main_window.show_message.assert_any_call("Impresión", ANY, "info")

    def test_handle_generate_labels_no_placeholders(self, controller, mock_main_window):
        controller.label_manager = MagicMock()
        controller.qr_generator = MagicMock()
        controller.label_manager.count_qr_placeholders.return_value = 0
        
        controller._handle_generate_labels({"id": 1, "producto_codigo": "P1"})
        
        mock_main_window.show_message.assert_called_with("Error de Plantilla", ANY, "error")

class TestWorkerControllerUtilities:
    """Tests para utilidades: Logout, Refresh y Exportación."""

    def test_handle_logout(self, controller):
        with patch('sys.exit') as mock_exit:
            controller._handle_logout()
            mock_exit.assert_called_with(0)
            assert controller._fabricaciones_asignadas == []
            assert controller._trabajos_activos == []

    def test_refresh_data(self, controller):
        with patch.object(controller, '_load_assigned_fabricaciones') as m1, \
             patch.object(controller, '_load_active_trabajos') as m2:
            controller.refresh_data()
            m1.assert_called_once()
            m2.assert_called_once()

    @patch('features.worker_controller.QFileDialog.getSaveFileName')
    @patch('builtins.open', new_callable=MagicMock)
    def test_handle_export_data_success(self, mock_open, mock_save_dialog, controller, mock_db_manager, mock_main_window):
        mock_save_dialog.return_value = ("/tmp/export.json", "JSON")
        mock_db_manager.config_repo = MagicMock()
        mock_db_manager.config_repo.get_setting.return_value = "2023-01-01T00:00:00"
        
        mock_db_manager.tracking_repo.get_data_for_export.return_value = [{"id": 1}]
        
        controller._handle_export_data()
        
        mock_open.assert_called()
        mock_db_manager.config_repo.set_setting.assert_called_with('last_export_date', ANY)
        mock_main_window.show_message.assert_any_call("Éxito", ANY, "info")
