# -*- coding: utf-8 -*-
"""Tests unitarios para StartupController.

Cubre inicialización (initialize_app), registro en DIContainer e _init_state.
Decisión de mocking: app con spec AppController/AppModel/ScheduleConfig; QTimer parcheado.
"""
import pytest
from unittest.mock import MagicMock, patch, ANY
from controllers.startup_controller import StartupController
from controllers.app_controller import AppController
from core.app_model import AppModel
from core.schedule_config import ScheduleConfig
from core.di_container import DIContainer, ServiceLifecycle

pytestmark = pytest.mark.unit

@pytest.fixture
def mock_app_controller():
    model = MagicMock(spec=AppModel)
    model.db = MagicMock(spec=["SessionLocal", "tracking_repo"])
    # Mock SessionLocal to be a callable that returns a mock session
    def _session_local():
        return object()
    model.db.SessionLocal = _session_local
    model.db.tracking_repo = MagicMock(spec=[])
    
    view = MagicMock(spec=[])
    schedule_manager = MagicMock(spec=ScheduleConfig)
    
    app = MagicMock(spec=AppController)
    app.model = model
    app.view = view
    app.schedule_manager = schedule_manager
    app.logger = MagicMock(spec=["debug", "info", "warning", "error", "critical"])
    app.ui_signals_controller = MagicMock(spec=[])
    app.maintenance_service = MagicMock(spec=["run_background_maintenance"])
    
    return app

@patch("controllers.startup_controller.DIContainer", autospec=True)
def test_startup_controller_initialization(mock_di_container_cls, mock_app_controller):
    # Setup
    mock_container = MagicMock(spec=["register", "resolve"])
    mock_di_container_cls.get_instance.return_value = mock_container
    
    # Patch QTimer to avoid "TypeError: QTimer(parent: Optional[QObject] = None)..."
    # because mock_app_controller is not a QObject
    with patch('PyQt6.QtCore.QTimer') as MockQTimer:
        # Execute
        startup = StartupController(mock_app_controller)
        startup.initialize_app()
    
    # Verify Services Init
    assert mock_app_controller.qr_generator is not None
    assert mock_app_controller.label_manager is not None
    assert mock_app_controller.security_service is not None
    assert mock_app_controller.quote_service is not None
    assert mock_app_controller.thread_pool is not None
    
    assert mock_container.register.call_count >= 1
    mock_container.register.assert_any_call('AppModel', mock_app_controller.model, lifecycle=ServiceLifecycle.SINGLETON)
    
    # Verify Controllers Init
    assert mock_app_controller.backup_controller is not None
    assert mock_app_controller.product_controller is not None
    


from core.application_state import ApplicationState
def test_init_state(mock_app_controller):
    # Setup
    startup = StartupController(mock_app_controller)
    
    # Execute
    startup._init_state()
    
    # Verify
    assert isinstance(mock_app_controller.state, ApplicationState)
    assert mock_app_controller.state.active_dialogs == {}
