import pytest
from unittest.mock import MagicMock, patch
import sys
from PyQt6.QtWidgets import QApplication

from controllers.app_controller import AppController
from ui.main_window import MainView

# Ensure app instance exists
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

@pytest.fixture
def mock_model_for_ui():
    """
    Creates a mock model sufficient for UI initialization without touching the DB.
    """
    model = MagicMock()
    # Signals
    model.product_deleted_signal = MagicMock()
    model.pilas_changed_signal = MagicMock()
    model.machines_changed_signal = MagicMock()
    
    # Common Data Methods called during init/updates
    model.get_all_products.return_value = []
    model.get_all_workers.return_value = []
    model.get_all_machines.return_value = []
    model.get_recent_fabricaciones.return_value = []
    model.get_all_iterations_with_dates.return_value = []
    model.config_repo.get_setting.return_value = "0" # Camera index
    
    # Sub-repos & DB
    model.worker_repo = MagicMock()
    model.config_repo = MagicMock()
    model.pila_repo = MagicMock()
    model.db = MagicMock()
    model.db.tracking_repo = MagicMock()
    model.db.SessionLocal = MagicMock()
    
    return model

@pytest.fixture
def mock_schedule_config():
    return MagicMock()

def test_app_startup_smoke_test(qapp, mock_model_for_ui, mock_schedule_config):
    """
    Smoke Test: Verifies that AppController can initialize and connect signals
    with the REAL MainView (containing real widgets) without crashing.
    """
    
    # 1. Instantiate the REAL MainView
    # Logic: We want to test the integration of Controller -> View -> Widgets
    # We patch only external dependencies like hardware managers or heavy libs
    with patch('controllers.app_controller.CameraManager'), \
         patch('controllers.app_controller.QrGenerator'), \
         patch('controllers.app_controller.LabelManager'), \
         patch('controllers.app_controller.LabelCounterRepository'):
        
        # Instantiate View
        view = MainView() 
        # CRITICAL: Initialize UI to create pages/widgets
        view.init_ui()
        
        # 2. Instantiate Controller
        # This will create sub-controllers
        controller = AppController(mock_model_for_ui, view, mock_schedule_config)
        
        # CRITICAL: Link Controller to View (this re-initializes complex widgets like GestionDatos)
        view.set_controller(controller)
        
        # 3. CRITICAL STEP: Connect Signals
        # This is where regressions like 'AttributeError' happen
        try:
            controller.connect_signals()
        except AttributeError as e:
            pytest.fail(f"Startup Crash Detected during signal connection: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected Startup Crash: {e}")
            
        # 4. Verify Controller was assigned to widgets
        # Check ReportesWidget specifically since it was the point of failure
        reportes_page = view.pages.get("reportes")
        assert reportes_page is not None
        assert reportes_page.controller == controller

        
        # Check another widget to be sure
        gestion_page = view.pages.get("gestion_datos")
        assert gestion_page.controller == controller
