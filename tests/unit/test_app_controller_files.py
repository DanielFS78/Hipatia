import os
import shutil
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QDialog, QMessageBox

from controllers.app_controller import AppController

# --- FIXTURES ---

@pytest.fixture
def mock_view():
    """Mock de MainView."""
    view = MagicMock()
    view.pages = {}
    view.show_message = MagicMock()
    view.show_confirmation_dialog = MagicMock(return_value=True)
    return view

@pytest.fixture
def mock_model():
    """Mock de AppModel."""
    model = MagicMock()
    model.db = MagicMock()
    model.db.tracking_repo = MagicMock()
    return model

@pytest.fixture
def mock_schedule_config():
    """Mock de ScheduleConfig."""
    return MagicMock()

@pytest.fixture
def controller(mock_model, mock_view, mock_schedule_config):
    """Instancia de AppController con dependencias mockeadas."""
    with patch('controllers.app_controller.CameraManager'), \
         patch('controllers.app_controller.QrGenerator'), \
         patch('controllers.app_controller.LabelManager'), \
         patch('controllers.app_controller.LabelCounterRepository'):
        
        ctrl = AppController(mock_model, mock_view, mock_schedule_config)
        return ctrl

# --- TESTS ---

class TestAppControllerFiles:

    def test_handle_attach_file_success(self, controller):
        """Test handle_attach_file copies file and returns relative path."""
        owner_type = "iteration"
        owner_id = 123
        source_file = "/path/to/source.pdf"
        file_type = "plano"
        
        with patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=True), \
             patch('shutil.copy') as mock_copy:
            
            success, rel_path = controller.handle_attach_file(owner_type, owner_id, source_file, file_type)
            
            assert success is True
            assert rel_path == "data/planos/iteration_123.pdf"
            mock_makedirs.assert_called()
            mock_copy.assert_called_once()

    def test_handle_attach_file_failure(self, controller):
        """Test handle_attach_file handles exceptions."""
        with patch('shutil.copy', side_effect=Exception("Copy error")):
            success, msg = controller.handle_attach_file("iter", 1, "src", "type")
            assert success is False
            assert "Copy error" in msg

    def test_handle_view_file_success(self, controller):
        """Test handle_view_file opens file with QDesktopServices."""
        path = "data/file.pdf"
        with patch('os.path.exists', return_value=True), \
             patch('PyQt6.QtGui.QDesktopServices.openUrl') as mock_open:
            
            controller.handle_view_file(path)
            mock_open.assert_called_once()

    def test_handle_view_file_not_found(self, controller):
        """Test handle_view_file shows warning if file doesn't exist."""
        path = "data/missing.pdf"
        with patch('os.path.exists', return_value=False):
            controller.handle_view_file(path)
            controller.view.show_message.assert_called_with(
                "Error", "El archivo no se encuentra o la ruta es inválida.", "warning"
            )

    def test_handle_save_flow_only(self, controller):
        """Test handle_save_flow_only calls model.save_pila correctly."""
        flow = [
            {'task': {'original_product_code': 'PROD-001', 'original_product_info': {'desc': 'Desc'}}, 'start_date': '2025-01-01'},
            {'task': {'original_product_code': 'PREP_5', 'name': '[PREPROCESO] Prep 1'}, 'start_date': '2025-01-02'}
        ]
        
        controller.handle_save_flow_only("Pila Test", "Desc Test", flow)
        
        controller.model.save_pila.assert_called_once()
        args = controller.model.save_pila.call_args[0]
        assert args[0] == "Pila Test"
        assert args[1] == "Desc Test"
        pila_calc = args[2]
        assert 'PROD-001' in pila_calc['productos']
        assert 5 in pila_calc['preprocesos']

    def test_on_import_task_data_success(self, controller):
        """Test importing tasks from JSON."""
        mock_data = [{"id": 1, "desc": "Task 1"}]
        
        with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', return_value=("tasks.json", "JSON")), \
             patch('builtins.open', create=True) as mock_open, \
             patch('json.load', return_value=mock_data):
            
            controller._on_import_task_data()
            
            # Verify upsert called for each item
            controller.model.db.tracking_repo.upsert_trabajo_log_from_dict.assert_called()

    def test_on_import_task_data_cancelled(self, controller):
        """Test import canceled by user."""
        with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', return_value=("", "")):
            controller._on_import_task_data()
            controller.model.db.tracking_repo.upsert_trabajo_log_from_dict.assert_not_called()

    def test_add_new_iteration_clicked_success(self, controller):
        """Test flow for adding a new iteration with file attachment."""
        controller.product_code = "PROD-123"
        # Mock load_iterations since it might be missing or dynamic
        controller.load_iterations = MagicMock()
        
        dialog_data = {
            "responsable": "Juan",
            "descripcion": "Cambio diseño",
            "tipo_fallo": "General",
            "ruta_plano_origen": "/tmp/plano.pdf"
        }
        
        # Patch where it is imported!
        with patch('controllers.app_controller.AddIterationDialog') as MockDialog, \
             patch.object(controller, 'handle_attach_file', return_value=(True, "data/planos/new.pdf")) as mock_attach:
                        
            dialog = MockDialog.return_value
            dialog.exec.return_value = True
            dialog.get_data.return_value = dialog_data
            
            controller.model.add_product_iteration.return_value = 55
            
            controller._on_add_new_iteration_clicked()
            
            controller.model.add_product_iteration.assert_called_once()
            mock_attach.assert_called_once()
            controller.model.db.update_iteration_file_path.assert_called_with(55, 'ruta_plano', 'data/planos/new.pdf')
            # Verify load_iterations called
            controller.load_iterations.assert_called_once()

    def test_add_new_iteration_clicked_validation_fail(self, controller):
        """Test validation failure in add iteration."""
        controller.product_code = "PROD-123"
        dialog_data = {"responsable": "", "descripcion": ""} # Empty
        
        with patch('controllers.app_controller.AddIterationDialog') as MockDialog:
            dialog = MockDialog.return_value
            dialog.exec.return_value = True
            dialog.get_data.return_value = dialog_data
            
            controller._on_add_new_iteration_clicked()
            
            controller.view.show_message.assert_called_with("Campos Vacíos", "El responsable y la descripción son obligatorios.", "warning")
            controller.model.add_product_iteration.assert_not_called()
