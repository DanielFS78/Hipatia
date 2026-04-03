import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, ANY
from PyQt6.QtWidgets import QDialog
from features.worker_controller import WorkerController

pytestmark = pytest.mark.unit

@pytest.fixture
def mock_db_manager():
    db = MagicMock(spec=["tracking_repo", "config_repo"])
    db.tracking_repo = MagicMock(spec=[])
    db.config_repo = MagicMock(spec=["get_setting", "set_setting"])
    return db

@pytest.fixture
def mock_main_window():
    win = MagicMock(
        spec=[
            "update_tasks_list",
            "update_task_state",
            "show_message",
            "enable_action_buttons",
            "generate_labels_btn",
        ]
    )
    win.update_tasks_list = MagicMock(spec=[])
    win.update_task_state = MagicMock(spec=[])
    win.show_message = MagicMock(spec=[])
    win.enable_action_buttons = MagicMock(spec=[])
    win.generate_labels_btn = MagicMock(spec=[])
    return win

@pytest.fixture
def current_user():
    return MagicMock(spec=["id", "nombre_completo", "role"], id=101, nombre_completo="Operario Test", role="Trabajador")

@pytest.fixture
def controller(current_user, mock_db_manager, mock_main_window):
    ctrl = WorkerController(
        current_user=current_user,
        db_manager=mock_db_manager,
        main_window=mock_main_window
    )
    # Mock services
    ctrl.db_sync = MagicMock(
        spec=[
            "get_paso_activo",
            "get_trabajo_por_qr",
            "get_active_trabajos",
            "iniciar_o_recuperar_trabajo",
            "iniciar_paso",
            "finalizar_paso",
            "get_trabajo_por_id",
            "registrar_incidencia",
            "get_data_for_export",
        ]
    )
    ctrl.db_sync.get_active_trabajos.return_value = []
    ctrl.validation_service = MagicMock(spec=["validate_qr_data", "validate_product_match"])
    ctrl.qr_scanner = MagicMock(spec=["scan_once"])
    ctrl.label_manager = MagicMock(spec=["count_qr_placeholders", "generate_labels"])
    ctrl.qr_generator = MagicMock(spec=["generate_unique_id"])
    ctrl.qr_generator.generate_unique_id.return_value = "QR-UNIQ"
    ctrl.label_counter_repo = MagicMock(spec=["get_next_unit_range"])
    return ctrl

class TestWorkerControllerHandlers:
    """Tests para los manejadores de señales del controlador."""

    def test_handle_task_selected(self, controller, mock_main_window):
        controller.db_sync.get_paso_activo.return_value = None
        controller._handle_task_selected({"id": 1})
        mock_main_window.update_task_state.assert_called_with("pendiente", None)

    def test_handle_generate_labels(self, controller, mock_main_window):
        controller.label_manager.count_qr_placeholders.return_value = 4
        with patch('PyQt6.QtWidgets.QInputDialog.getInt', return_value=(1, True)):
            controller.label_counter_repo.get_next_unit_range.return_value = MagicMock(start=1, end=4)
            controller.label_manager.generate_labels.return_value = "doc.docx"
            with patch.object(controller, '_process_label_document') as mock_proc:
                controller._handle_generate_labels({"id": 1, "producto_codigo": "P1"})
                mock_proc.assert_called_with("doc.docx")

    def test_handle_consult_qr(self, controller, mock_main_window):
        controller.qr_scanner.scan_once.return_value = "QR-123"
        controller.validation_service.validate_qr_data.return_value = (True, {"p": "c"}, "")
        controller.db_sync.get_trabajo_por_qr.return_value = None
        
        controller._handle_consult_qr()
        mock_main_window.show_message.assert_any_call("Libre", ANY, "info")

    def test_handle_start_task(self, controller, mock_main_window):
        controller.db_sync.get_paso_activo.return_value = None
        controller.qr_scanner.scan_once.return_value = "QR-123"
        controller.validation_service.validate_qr_data.return_value = (True, {"producto_codigo": "P1"}, "")
        controller.validation_service.validate_product_match.return_value = (True, "")
        
        mock_log = MagicMock(id=500)
        controller.db_sync.iniciar_o_recuperar_trabajo.return_value = mock_log
        controller.db_sync.iniciar_paso.return_value = True
        
        controller._handle_start_task({"id": 1, "producto_codigo": "P1"})
        
        assert controller.db_sync.iniciar_paso.call_count >= 1
        controller.db_sync.iniciar_paso.assert_called()
        mock_main_window.update_task_state.assert_called_with("en_proceso", ANY)

    def test_handle_end_task(self, controller, mock_main_window):
        mock_paso = MagicMock(id=99, trabajo_log_id=500)
        controller.db_sync.get_paso_activo.return_value = mock_paso
        
        mock_trabajo = MagicMock(qr_code="QR-123")
        controller.db_sync.get_trabajo_por_id.return_value = mock_trabajo
        
        controller.qr_scanner.scan_once.return_value = "QR-123"
        controller.db_sync.finalizar_paso.return_value = True
        
        controller._handle_end_task({})
        
        controller.db_sync.finalizar_paso.assert_called_with(99)
        mock_main_window.update_task_state.assert_called_with("pendiente", None)

    def test_handle_register_incidence(self, controller, mock_main_window):
        mock_paso = MagicMock(trabajo_log_id=500)
        controller.db_sync.get_paso_activo.return_value = mock_paso
        mock_trabajo = MagicMock(id=500, qr_code="QR-123")
        controller.db_sync.get_trabajo_por_id.return_value = mock_trabajo
        
        controller.qr_scanner.scan_once.return_value = "QR-123"
        
        with patch('features.worker_controller.IncidenceDialog') as mock_dialog:
            mock_dialog_inst = mock_dialog.return_value
            mock_dialog_inst.exec.return_value = QDialog.DialogCode.Accepted
            mock_dialog_inst.get_data.return_value = {"tipo_incidencia": "T", "descripcion": "D", "fotos_paths": []}
            
            controller._handle_register_incidence({})
            assert controller.db_sync.registrar_incidencia.call_count >= 1
            controller.db_sync.registrar_incidencia.assert_called()

    def test_handle_export_data(self, controller, mock_main_window, mock_db_manager):
        mock_db_manager.config_repo.get_setting.return_value = "2023-01-01T00:00:00Z"
        controller.db_sync.get_data_for_export.return_value = [{"id": 1}]
        
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', return_value=("file.json", "JSON")):
            with patch('builtins.open', create=True) as mock_open:
                controller._handle_export_data()
                assert mock_open.call_count >= 1
                args, kwargs = mock_open.call_args
                assert args[0] == "file.json"
                mock_main_window.show_message.assert_any_call("Éxito", ANY, "info")
