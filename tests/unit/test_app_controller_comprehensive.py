import pytest
from unittest.mock import MagicMock, patch, ANY, call
import sys
import os
import shutil
from datetime import datetime

# Eagerly import to ensure we patch the loaded module
import controllers.app_controller
from controllers.app_controller import AppController

# --- DUMMY MODEL ---
class DummyAppModel:
    def __init__(self, *args, **kwargs):
        pass

# --- FIXTURES SHARED ---
@pytest.fixture
def mock_view():
    view = MagicMock()
    view.pages = {}
    view.show_message = MagicMock()
    view.show_confirmation_dialog = MagicMock(return_value=True)
    return view

@pytest.fixture
def mock_model():
    model = DummyAppModel()
    model.db = MagicMock()
    model.db.tracking_repo = MagicMock()
    model.db.config_repo = MagicMock()
    model.worker_repo = MagicMock()
    
    # Configure DB paths as strings to avoid path issues
    model.db.db_path = "/path/to/montaje.db"
    model.pilas_db = MagicMock()
    model.pilas_db.db_path = "/path/to/pilas.db"
    
    model.product_deleted_signal = MagicMock()
    model.search_products = MagicMock(return_value=[])
    model.get_all_preprocesos_with_components = MagicMock(return_value=[])
    model.save_pila = MagicMock()
    model.pila_repo = MagicMock()
    model.delete_pila = MagicMock()
    
    # Necessary to return list of workers for simulation setup
    model.get_all_workers = MagicMock(return_value=[])
    model.get_all_machines = MagicMock(return_value=[])
    
    return model

@pytest.fixture
def controller(mock_model, mock_view):
    with patch('controllers.app_controller.CameraManager', MagicMock()), \
         patch('controllers.app_controller.QrGenerator', MagicMock()), \
         patch('controllers.app_controller.LabelManager', MagicMock()), \
         patch('controllers.app_controller.LabelCounterRepository', MagicMock()), \
         patch('database.database_manager.DatabaseManager', MagicMock()), \
         patch('controllers.app_controller.DatabaseManager', MagicMock()):
        
        ctrl = AppController(mock_model, mock_view, MagicMock())
        # Mock schedule_manager manually as it's often accessed
        ctrl.schedule_manager = MagicMock()
        return ctrl

# --- TEST CLASSES ---

class TestWorkerInterface:
    def test_launch_worker_interface_success(self, controller):
        controller.current_user = {"id": 1, "nombre": "Pepe", "role": "Trabajador"}

        with patch.dict('sys.modules', {
            'ui.worker.worker_main_window': MagicMock(),
            'features.worker_controller': MagicMock()
        }):
            mock_window = MagicMock()
            sys.modules['ui.worker.worker_main_window'].WorkerMainWindow = MagicMock(return_value=mock_window)
            sys.modules['features.worker_controller'].WorkerController = MagicMock()
            
            with patch('controllers.app_controller.QMessageBox'):
                controller._initialize_qr_scanner = MagicMock()
                controller.qr_scanner = MagicMock()
                controller._launch_worker_interface()
                mock_window.show.assert_called_once()

    def test_launch_worker_interface_import_error(self, controller):
        controller.current_user = {"id": 1, "nombre": "Pepe", "role": "Trabajador"}
        with patch.dict('sys.modules', {}), \
             patch('builtins.__import__', side_effect=ImportError("Module missing")), \
             patch('controllers.app_controller.QMessageBox') as MockMB, \
             patch('sys.exit') as mock_exit:
            
            controller._launch_worker_interface()
            MockMB.information.assert_called_once()
            mock_exit.assert_called_with(0)

class TestBackupRestore:
    def test_create_automatic_backup_success(self, controller):
        controller.model.db.db_path = "/path/to/montaje.db"
        with patch('os.path.exists', return_value=True), \
             patch('os.makedirs'), \
             patch('shutil.copy2') as mock_copy:
            controller.create_automatic_backup()
            assert mock_copy.call_count >= 1

    def test_on_import_databases_success(self, controller):
        controller.view.pages["gestion_datos"] = MagicMock()
        patcher = patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', return_value=("/path/to/backup.zip", "zip"))
        patcher.start()
        
        with patch('controllers.app_controller.DatabaseManager') as MockDB, \
             patch('zipfile.ZipFile') as MockZip, \
             patch('shutil.move') as mock_move, \
             patch('os.path.exists', return_value=True), \
             patch('os.remove'):
            
            mock_zip = MockZip.return_value
            mock_zip.__enter__.return_value = mock_zip
            mock_zip.namelist.return_value = ["montaje.db"]
            
            controller._on_import_databases()
            
            mock_zip.extractall.assert_called()
            controller.view.show_message.assert_called()

        patcher.stop()

    def test_on_export_databases_success(self, controller):
        patcher = patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', return_value=("/path/to/export.zip", "zip"))
        patcher.start()
        
        controller.model.db.db_path = "/valid/path/db.sqlite"
        controller.model.pilas_db.db_path = "/valid/path/pilas.db"
        
        with patch('controllers.app_controller.resource_path', side_effect=lambda x: x), \
             patch('zipfile.ZipFile') as MockZip, \
             patch('os.path.exists', return_value=True):
             
             mock_zip_instance = MockZip.return_value
             mock_zip_instance.__enter__.return_value = mock_zip_instance
             
             controller._on_export_databases()
             
             mock_zip_instance.write.assert_called()
             controller.view.show_message.assert_called()
        patcher.stop()

class TestHardware:
    def test_initialize_qr_scanner_no_cameras(self, controller):
        controller.model.db.config_repo.get_setting.return_value = None
        mock_info = MagicMock()
        mock_info.is_working = False
        controller.camera_manager.get_camera_info.return_value = mock_info
        controller._initialize_qr_scanner()
        assert controller.qr_scanner is None

    def test_on_detect_cameras(self, controller):
        mock_settings = MagicMock()
        mock_settings.camera_combo.currentData.return_value = 0
        
        controller.view.pages["settings"] = mock_settings
        cameras = [MagicMock(index=0), MagicMock(index=1)]
        controller.camera_manager.detect_cameras.return_value = cameras
        
        with patch('controllers.app_controller.SettingsWidget', MagicMock), \
             patch('controllers.app_controller.QMessageBox'), \
             patch('ui.widgets.SettingsWidget', MagicMock):
            
            controller._on_detect_cameras()
        
        assert mock_settings.camera_combo.addItem.call_count >= len(cameras)

    def test_on_save_hardware_settings_valid(self, controller):
        mock_settings = MagicMock()
        mock_settings.camera_combo.currentData.return_value = 0
        controller.view.pages = {"settings": mock_settings}
        controller.camera_manager.validate_camera.return_value = (True, "OK")
        
        with patch('controllers.app_controller.SettingsWidget', MagicMock), \
             patch('controllers.app_controller.QMessageBox'), \
             patch('ui.widgets.SettingsWidget', MagicMock):
            
            controller._on_save_hardware_settings() 
            controller.model.db.config_repo.set_setting.assert_called()

class TestSimulationFlow:
    def test_on_run_manual_plan_clicked(self, controller):
        mock_calc_page = MagicMock()
        mock_calc_page.planning_session = [{"task_id": 1}]
        
        # Necessary Check: Code relies on self.last_production_flow being set
        controller.last_production_flow = [{"step": 1}]
        
        controller.view.pages = {"calculate": mock_calc_page}
        
        with patch('controllers.app_controller.CalculateTimesWidget', MagicMock), \
             patch('ui.widgets.CalculateTimesWidget', MagicMock), \
             patch('controllers.app_controller.CalculadorDeTiempos'), \
             patch('controllers.app_controller.AdaptadorScheduler') as MockScheduler, \
             patch('PyQt6.QtWidgets.QApplication.processEvents'):
            
            controller._start_simulation_thread = MagicMock()
            
            controller._on_run_manual_plan_clicked()
            
            controller._start_simulation_thread.assert_called()

    def test_on_optimize_by_deadline_clicked(self, controller):
        mock_calc_page = MagicMock()
        mock_calc_page.planning_session = [{"id": 1, "unidades": 1}]
        controller.view.pages = {"calculate": mock_calc_page}
        
        with patch('controllers.app_controller.GetOptimizationParametersDialog') as MockDialog, \
             patch('controllers.app_controller.QDialog') as MockQDialog, \
             patch('controllers.app_controller.Optimizer'), \
             patch('controllers.app_controller.SimulationWorker') as MockWorker, \
             patch('PyQt6.QtWidgets.QApplication.processEvents'): 
            
            ACCEPTED = 1
            MockQDialog.DialogCode.Accepted = ACCEPTED
            
            dialog = MockDialog.return_value
            dialog.exec.return_value = ACCEPTED
            dialog.get_data.return_value = {"units": 10, "deadline": "2025-12-31"}
            dialog.get_parameters.return_value = {
                "units": 10, 
                "start_date": datetime.today(), 
                "end_date": datetime.today()
            }
            
            mock_worker_instance = MockWorker.return_value
            controller._on_optimize_by_deadline_clicked()
            
            if mock_worker_instance.start.called:
                mock_worker_instance.start.assert_called_once()
            
            controller.view.statusBar().showMessage.assert_called()

class TestVisualEditor:
    def test_handle_save_pila_from_visual_editor(self, controller):
        mock_flow_dialog = MagicMock()
        mock_flow_dialog.get_flow_data.return_value = []
        
        with patch('controllers.app_controller.SavePilaDialog') as MockDialog, \
             patch('controllers.app_controller.QDialog') as MockQDialog:
             
            ACCEPTED = 1
            MockQDialog.DialogCode.Accepted = ACCEPTED
            
            dialog = MockDialog.return_value
            dialog.exec.return_value = ACCEPTED
            dialog.get_data.return_value = ("Mi Pila", "Descripción")
            
            controller._handle_save_pila_from_visual_editor(mock_flow_dialog)
            
            controller.model.save_pila.assert_called()

    def test_handle_load_pila_into_visual_editor(self, controller):
        mock_flow_dialog = MagicMock()
        with patch('controllers.app_controller.LoadPilaDialog') as MockDialog, \
             patch('controllers.app_controller.QDialog') as MockQDialog:
             
            ACCEPTED = 1
            MockQDialog.DialogCode.Accepted = ACCEPTED
            
            dialog = MockDialog.return_value
            dialog.exec.return_value = ACCEPTED
            
            dialog.get_selected_id.return_value = 1
            dialog.delete_requested = False
            
            controller.model.pila_repo.load_pila.return_value = ({"id": 1}, None, [{"data": 1}], None)
            
            controller._handle_load_pila_into_visual_editor(mock_flow_dialog)
            
            mock_flow_dialog._load_flow_onto_canvas.assert_called()

class TestInteractiveFlows:
    def test_handle_attach_file_success(self, controller):
        source = "/tmp/image.jpg"
        with patch('os.makedirs'), patch('shutil.copy'), patch('os.path.exists', return_value=True):
            success, path = controller.handle_attach_file("iteration", 1, source, "imagen")
            assert success is True

    def test_handle_view_file_success(self, controller):
        with patch('os.path.exists', return_value=True), \
             patch('PyQt6.QtGui.QDesktopServices.openUrl') as mock_open:
            controller.handle_view_file("path/to/file.pdf")
            mock_open.assert_called()
