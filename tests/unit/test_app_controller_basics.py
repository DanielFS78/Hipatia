
import pytest
from unittest.mock import MagicMock, patch
import sys
import os
from controllers.app_controller import AppController, resource_path
from core.app_model import AppModel
from schedule_config import ScheduleConfig

class TestAppControllerBasics:

    @pytest.fixture
    def mock_dependencies(self):
        model = MagicMock(spec=AppModel)
        view = MagicMock()
        schedule_config = MagicMock(spec=ScheduleConfig)
        
        # Mock DB and Repos
        model.db = MagicMock()
        model.db.SessionLocal = MagicMock()
        model.db.tracking_repo = MagicMock()
        model.worker_repo = MagicMock()
        model.preproceso_repo = MagicMock()
        model.product_deleted_signal = MagicMock()
        
        return model, view, schedule_config

    def test_resource_path_local(self):
        """Test resource_path when running locally (not frozen)."""
        # Ensure _MEIPASS is not set
        if hasattr(sys, '_MEIPASS'):
            del sys._MEIPASS
            
        test_path = "test_file.txt"
        abs_path = os.path.abspath(".")
        expected = os.path.join(abs_path, test_path)
        
        assert resource_path(test_path) == expected

    def test_resource_path_frozen(self):
        """Test resource_path when running as frozen app (PyInstaller)."""
        test_dir = "/tmp/test_meipass"
        with patch.object(sys, '_MEIPASS', test_dir, create=True):
            test_path = "icon.png"
            expected = os.path.join(test_dir, test_path)
            assert resource_path(test_path) == expected

    def test_initialization(self, mock_dependencies):
        """Test proper initialization of AppController."""
        model, view, config = mock_dependencies
        
        # Patching internal managers to avoid complex side effects
        with patch('controllers.app_controller.CameraManager') as MockCameraManager, \
             patch('controllers.app_controller.QrGenerator') as MockQrGenerator, \
             patch('controllers.app_controller.LabelManager') as MockLabelManager, \
             patch('controllers.app_controller.LabelCounterRepository') as MockLabelCounterRepo:
             
            controller = AppController(model, view, config)
            
            assert controller.model == model
            assert controller.view == view
            assert controller.schedule_manager == config
            
            # Verify internal components initialization
            MockCameraManager.assert_called_once()
            MockQrGenerator.assert_called_once()
            MockLabelManager.assert_called_once()
            MockLabelCounterRepo.assert_called_once()
            
            # Check initial state
            assert controller.camera_manager is not None
            assert controller.qr_generator is not None
            assert controller.label_manager is not None
            assert controller.qr_scanner is None  # Should be None initially
            assert controller.active_dialogs == {}

    def test_get_all_preprocesos_with_components(self, mock_dependencies):
        """Test retrieval of preprocesos."""
        model, view, config = mock_dependencies
        controller = AppController(model, view, config)
        
        # Setup mock return
        expected_data = [{"id": 1, "nombre": "Corte"}, {"id": 2, "nombre": "Soldadura"}]
        model.preproceso_repo.get_all_preprocesos.return_value = expected_data
        
        result = controller.get_all_preprocesos_with_components()
        
        assert result == expected_data
        model.preproceso_repo.get_all_preprocesos.assert_called_once()

    def test_get_all_preprocesos_exception(self, mock_dependencies):
        """Test exception handling in get_all_preprocesos."""
        model, view, config = mock_dependencies
        controller = AppController(model, view, config)
        
        # Setup mock to raise exception
        model.preproceso_repo.get_all_preprocesos.side_effect = Exception("DB Error")
        
        # Should return empty list and log error
        with patch.object(controller.logger, 'error') as mock_log:
            result = controller.get_all_preprocesos_with_components()
            
            assert result == []
            mock_log.assert_called_once()
