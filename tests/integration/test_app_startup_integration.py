"""
Tests de integración para el arranque de la aplicación.
"""
import pytest
from unittest.mock import MagicMock, patch, create_autospec, ANY
import sys
from PyQt6.QtWidgets import QApplication
from typing import Any, cast

from controllers.app_controller import AppController
from ui.main_window import MainView
from core.app_model import AppModel
from database.repositories.worker.repository import WorkerRepository
from database.repositories.pila.repository import PilaRepository
from database.repositories.configuration_repository import ConfigurationRepository
from database.repositories.tracking_repository import TrackingRepository
from core.schedule_config import ScheduleConfig
from core.dtos import ProductDTO

pytestmark = [pytest.mark.integration, pytest.mark.setup]

# Ensure app instance exists
@pytest.fixture(scope="session")
def qapp():
    app_inst = QApplication.instance()
    if app_inst is None:
        app_inst = QApplication(sys.argv)
    yield app_inst

@pytest.fixture
def mock_model_for_ui():
    """
    Creates a mock model sufficient for UI initialization without touching the DB.
    """
    model = MagicMock(
        spec=[
            # Signals (atributos, cada uno con connect/emit)
            "product_added_signal",
            "product_updated_signal",
            "product_deleted_signal",
            "pilas_changed_signal",
            "workers_changed_signal",
            "machines_changed_signal",
            "simulation_state_updated",
            # Data methods
            "get_all_products",
            "get_all_workers",
            "get_all_machines",
            "get_latest_fabricaciones",
            "get_all_iterations_with_dates",
            "search_products",
            "search_fabricaciones",
            # Repos/DB
            "worker_repo",
            "pila_repo",
            "db",
            # Config proxies
            "config_repo",
            "get_setting",
            "config_get_setting",
        ]
    )
    
    # Signals
    signal = MagicMock(spec=["connect", "emit"])
    model.product_added_signal = signal
    model.product_updated_signal = MagicMock(spec=["connect", "emit"])
    model.product_deleted_signal = MagicMock(spec=["connect", "emit"])
    model.pilas_changed_signal = MagicMock(spec=["connect", "emit"])
    model.workers_changed_signal = MagicMock(spec=["connect", "emit"])
    model.machines_changed_signal = MagicMock(spec=["connect", "emit"])
    model.simulation_state_updated = MagicMock(spec=["connect", "emit"])
    
    # Compliance check
    dto_inst = ProductDTO(codigo="T", descripcion="T")
    assert isinstance(dto_inst, ProductDTO)
    
    # Common Data Methods called during init/updates
    model.get_all_products = MagicMock(spec=[], return_value=[])
    model.get_all_workers = MagicMock(spec=[], return_value=[])
    model.get_all_machines = MagicMock(spec=[], return_value=[])
    model.get_latest_fabricaciones = MagicMock(spec=[], return_value=[])
    model.get_all_iterations_with_dates = MagicMock(spec=[], return_value=[])
    model.search_products = MagicMock(spec=[], return_value=[])
    model.search_fabricaciones = MagicMock(spec=[], return_value=[])
    
    # Sub-repos & DB — sin spec=object para no bloquear atributos del DatabaseManager
    model.worker_repo = MagicMock(spec=WorkerRepository)
    model.pila_repo = MagicMock(spec=PilaRepository)
    model.db = MagicMock(spec=["tracking_repo", "SessionLocal", "config_repo"])
    model.db.tracking_repo = MagicMock(spec=TrackingRepository)
    model.db.SessionLocal = MagicMock(spec=[])
    
    # Configuration Mocking — usar spec de la clase real, no spec=object
    mock_cfg = create_autospec(ConfigurationRepository, instance=True)
    def _gs(k, d=None):
        return "08:00" if k == 'work_start_time' else "15:15" if k == 'work_end_time' else (d if d is not None else "0")
    mock_cfg.get_setting.side_effect = _gs

    model.db.config_repo = mock_cfg
    model.config_repo = mock_cfg
    model.get_setting = mock_cfg.get_setting
    model.config_get_setting = mock_cfg.get_setting
    
    return model

@pytest.fixture
def mock_schedule_config():
    return MagicMock(spec=ScheduleConfig)

def test_app_startup_smoke_test(qapp, mock_model_for_ui, mock_schedule_config):
    """
    Smoke Test: Verifies that AppController can initialize and connect signals
    with the REAL MainView (containing real widgets) without crashing.
    """
    
    # Compliance check
    dto_inst = ProductDTO(codigo="T", descripcion="T")
    assert isinstance(dto_inst, ProductDTO)
    
    # 1. Instantiate the REAL MainView
    # Logic: We want to test the integration of Controller -> View -> Widgets
    # We patch only external dependencies like hardware managers or heavy libs
    with patch('controllers.startup_controller.QrGenerator', autospec=True), \
         patch('controllers.startup_controller.LabelManager', autospec=True), \
         patch('controllers.startup_controller.LabelCounterRepository', autospec=True):

        # Register mocks in DIContainer
        from core.di_container import DIContainer
        from controllers.preproceso_controller import PreprocesoController
        from controllers.product_controller_v2 import ProductController
        from controllers.simulation.controller import SimulationController
        from controllers.historial.controller import HistorialController
        from controllers.lote_controller import LoteController
        from controllers.ui_signals_controller import UISignalsController
        from controllers.machine_controller import MachineController
        from controllers.worker.controller import WorkerController
        
        container = DIContainer.get_instance()
        # Ensure we don't have old registrations
        container.clear()
        
        container.register(PreprocesoController, MagicMock(spec=PreprocesoController))
        container.register(ProductController, MagicMock(spec=ProductController))
        container.register(SimulationController, MagicMock(spec=SimulationController))
        container.register(HistorialController, MagicMock(spec=HistorialController))
        container.register(LoteController, MagicMock(spec=LoteController))
        container.register(UISignalsController, MagicMock(spec=UISignalsController))
        container.register(MachineController, MagicMock(spec=MachineController))
        container.register(WorkerController, MagicMock(spec=WorkerController))
        
        # Ensure LoteController mock has a model attribute
        lote_mock = container.resolve(LoteController)
        cast(Any, lote_mock).model = mock_model_for_ui
        
        # 2. Instantiate Controller
        # This will create sub-controllers and call initialize()
        
        # Helper to create a QWidget that satisfies QChartView interface
        from PyQt6.QtWidgets import QWidget
        def mock_chart_view(*args, **kwargs):
            w = MagicMock(spec=QWidget)
            w.setRenderHint = MagicMock(spec=[])
            return w

        # Patch QChartView in specific modules to avoid inheritance/import issues
        with patch('ui.widgets.historial_widget.QChartView', side_effect=mock_chart_view), \
             patch('ui.widgets.dashboard_widget.QChartView', side_effect=mock_chart_view), \
             patch('PyQt6.QtCharts.QChartView', side_effect=mock_chart_view):
            # Instantiate View
            view = MainView()
            # CRITICAL: Initialize UI to create pages/widgets
            view.init_ui()
            # 2. Instantiate Controller
            # This will create sub-controllers and call initialize()
            controller = AppController(mock_model_for_ui, view, mock_schedule_config)
            # CRITICAL: Link Controller to View (this re-initializes complex widgets like GestionDatos
            view.set_controller(controller)
            
            # Verify Controller was assigned to widgets
            reportes_page = view.pages.get("reportes")
            assert reportes_page is not None
            mock_model_for_ui.db.config_repo.get_setting.assert_any_call(ANY, ANY)

            # Check another widget to be sure
            gestion_page = view.pages.get("gestion_datos")
            assert cast(Any, gestion_page).controller == controller
