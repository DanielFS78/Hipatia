"""
Tests for AppController._launch_worker_interface.
"""
import pytest
from unittest.mock import MagicMock, patch
from controllers.app_controller import AppController

class TestLaunchWorkerInterface:
    @pytest.fixture
    def mock_app(self):
        model = MagicMock()
        view = MagicMock()
        config = MagicMock()
        
        with patch('controllers.app_controller.CameraManager'), \
             patch('controllers.app_controller.QrGenerator'), \
             patch('controllers.app_controller.LabelManager'), \
             patch('controllers.app_controller.LabelCounterRepository'):
            ctrl = AppController(model, view, config)
            ctrl.current_user = {'nombre': 'Test Worker', 'role': 'Trabajador'}
            return ctrl

    def test_launch_success(self, mock_app):
        """Test successful launch of worker interface."""
        # Patch where the class is defined, not where it is imported (since it's a local import)
        with patch('ui.worker.worker_main_window.WorkerMainWindow') as MockWindow, \
             patch('features.worker_controller.WorkerController') as MockController, \
             patch.object(mock_app, '_initialize_qr_scanner') as mock_init_cam, \
             patch('sys.exit'): # Prevent exit just in case
            
            mock_window_instance = MockWindow.return_value
            mock_controller_instance = MockController.return_value
            
            # Setup qr_scanner to prevent error log
            mock_app.qr_scanner = MagicMock()
            
            mock_app._launch_worker_interface()
            
            # Verify window creation
            MockWindow.assert_called_once_with(mock_app.current_user)
            mock_window_instance.show.assert_called_once()
            
            # Verify controller initialization
            MockController.assert_called_once()
            mock_controller_instance.initialize.assert_called_once()
            
            # Verify camera init was called
            mock_init_cam.assert_called_once()

    def test_import_error_fallback(self, mock_app):
        """Test handling of ImportError (modules not found)."""
        # Simulate ImportError when importing WorkerMainWindow
        with patch.dict('sys.modules', {'ui.worker.worker_main_window': None}):
             with patch('sys.exit') as mock_exit, \
                  patch('PyQt6.QtWidgets.QMessageBox.information') as mock_msg:
                 
                 mock_app._launch_worker_interface()
                 
                 mock_msg.assert_called_once()
                 mock_exit.assert_called_with(0)

    def test_critical_exception(self, mock_app):
        """Test critical exception during launch."""
        with patch('ui.worker.worker_main_window.WorkerMainWindow', side_effect=Exception("Boom")), \
             patch('sys.exit') as mock_exit, \
             patch('PyQt6.QtWidgets.QMessageBox.critical') as mock_msg:
            
            mock_app._launch_worker_interface()
            
            mock_msg.assert_called_once()
            mock_exit.assert_called_with(1)
