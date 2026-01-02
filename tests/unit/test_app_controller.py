import sys
import pytest
from unittest.mock import MagicMock, patch, ANY
import json
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import Qt

from controllers.app_controller import AppController
from core.app_model import AppModel
from ui.main_window import MainView
from ui.widgets.dashboard_widget import DashboardWidget
from ui.widgets.reportes_widget import ReportesWidget
from ui.widgets.historial_widget import HistorialWidget
from ui.widgets.gestion_datos_widget import GestionDatosWidget
from ui.widgets.products_widget import AddProductWidget
from ui.widgets.settings_widget import SettingsWidget
from ui.widgets.preprocesos_widget import PreprocesosWidget
from ui.widgets.home_widget import HomeWidget
from ui.widgets.workers_widget import WorkersWidget
from database.database_manager import DatabaseManager
from database.repositories.worker_repository import WorkerRepository
from database.repositories.configuration_repository import ConfigurationRepository
from database.repositories.lote_repository import LoteRepository
from database.repositories.tracking_repository import TrackingRepository
from schedule_config import ScheduleConfig
from PyQt6.QtWidgets import QPushButton
from core.camera_manager import CameraInfo

# --- FIXTURES ---

@pytest.fixture
def mock_view():
    """Mock de MainView con todas las páginas y componentes necesarios."""
    view = MagicMock(spec=MainView)
    
    # Mock specific pages with specs
    mock_dashboard = MagicMock(spec=DashboardWidget)
    mock_reportes = MagicMock(spec=ReportesWidget)
    mock_historial = MagicMock(spec=HistorialWidget)
    
    mock_gestion = MagicMock(spec=GestionDatosWidget)
    # Ensure nested attributes used in other tests (though AppController test might not go deep into GestionDatos internals)
    # mock_gestion.trabajadores_tab is used in test_connect_signals_calls_submethods
    # mock_gestion.trabajadores_tab is used in test_connect_signals_calls_submethods
    mock_gestion.trabajadores_tab = MagicMock(spec=WorkersWidget)
    
    mock_add = MagicMock(spec=AddProductWidget)
    mock_settings = MagicMock(spec=SettingsWidget)
    mock_preprocesos = MagicMock(spec=PreprocesosWidget)
    mock_home = MagicMock(spec=HomeWidget)
    
    # Populate pages dict
    view.pages = {
        "dashboard": mock_dashboard,
        "reportes": mock_reportes,
        "historial": mock_historial,
        "gestion_datos": mock_gestion,
        "add_product": mock_add,
        "settings": mock_settings,
        "preprocesos": mock_preprocesos,
        "home": mock_home
    }
    
    view.buttons = {} # Tests will populate this
    # Methods are part of Key Interface, auto-created by spec=MainView access.
    # We configure return value for confirmation dialog
    view.show_confirmation_dialog.return_value = True
    return view

@pytest.fixture
def mock_model():
    """Mock de AppModel con repositorios simulados."""
    model = MagicMock(spec=AppModel)
    model.db = MagicMock(spec=DatabaseManager)
    model.db.SessionLocal = MagicMock() # Key attribute not in class spec (created in __init__)
    # Mocking attributes accessed in tests
    model.worker_repo = MagicMock(spec=WorkerRepository)
    model.config_repo = MagicMock(spec=ConfigurationRepository)
    model.lote_repo = MagicMock(spec=LoteRepository)
    # Signals are attributes of AppModel, auto-created by spec interaction if we don't overwrite.
    # We don't strictly need to overwrite them if we just emit them or connect them.
    
    # Mockear repositorios específicos
    model.db.config_repo = model.config_repo
    model.db.config_repo = model.config_repo
    model.db.tracking_repo = MagicMock(spec=TrackingRepository)
    
    # Methods needed
    # get_all_preprocesos_with_components returns list, so validation is on return value type mostly
    # It exists in AppModel, so we don't need to overwrite it, just use it.
    
    return model

@pytest.fixture
def mock_schedule_config():
    """Mock de ScheduleConfig."""
    return MagicMock(spec=ScheduleConfig)

@pytest.fixture
def controller(mock_model, mock_view, mock_schedule_config):
    """Instancia de AppController con dependencias mockeadas."""
    # Patching dependencies that are instantiated in __init__
    with patch('controllers.app_controller.CameraManager'), \
         patch('controllers.app_controller.QrGenerator'), \
         patch('controllers.app_controller.LabelManager'), \
         patch('controllers.app_controller.LabelCounterRepository'):
        
        ctrl = AppController(mock_model, mock_view, mock_schedule_config)
        return ctrl

# --- TESTS ---

class TestAppControllerInitialization:
    def test_init_creates_dependencies(self, controller):
        """Verifica que el controlador inicializa sus componentes internos."""
        assert controller.camera_manager is not None
        assert controller.qr_generator is not None
        assert controller.label_manager is not None
        assert controller.label_counter_repo is not None
        assert controller.qr_scanner is None  # Debe ser None al inicio

class TestAppControllerLogin:
    def test_handle_login_success(self, controller):
        """Verifica el flujo de login exitoso."""
        # Mock de LoginDialog
        with patch('ui.dialogs.LoginDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = QDialog.DialogCode.Accepted
            dialog_instance.get_credentials.return_value = ("admin", "password")
            
            # Mock de autenticación
            user_data = {"id": 1, "username": "admin", "role": "Responsable"}
            controller.model.worker_repo.authenticate_user.return_value = user_data
            
            result, success = controller.handle_login()
            
            assert success is True
            assert result == user_data
            assert controller.current_user == user_data

    def test_handle_login_failure(self, controller):
        """Verifica el flujo de login fallido."""
        with patch('ui.dialogs.LoginDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = QDialog.DialogCode.Accepted
            dialog_instance.get_credentials.return_value = ("user", "wrong")
            
            controller.model.worker_repo.authenticate_user.return_value = None
            
            result, success = controller.handle_login()
            
            assert success is False
            assert result is None
            assert controller.current_user is None

class TestAppControllerNavigation:
    def test_update_ui_for_role_responsable(self, controller):
        """Verifica que el rol Responsable habilita todos los botones."""
        controller.current_user = {'role': 'Responsable'}
        
        # Mock botones - using simple MagicMocks as buttons are usually just widgets
        # If strictness is required for buttons, use spec=QPushButton
        mock_buttons = {
            'dashboard': MagicMock(spec=QPushButton), 'reportes': MagicMock(spec=QPushButton),
            'historial': MagicMock(spec=QPushButton), 'gestion_datos': MagicMock(spec=QPushButton),
            'add_product': MagicMock(spec=QPushButton), 'settings': MagicMock(spec=QPushButton)
        }
        controller.view.buttons = mock_buttons
        
        controller._update_ui_for_role()
        
        for btn in mock_buttons.values():
            btn.setEnabled.assert_called_with(True)

    def test_update_ui_for_role_worker(self, controller):
        """Verifica que el rol Trabajador deshabilita botones y redirige a home."""
        controller.current_user = {'role': 'Trabajador'}
        
        mock_buttons = {
            'dashboard': MagicMock(spec=QPushButton), 'reportes': MagicMock(spec=QPushButton),
            'historial': MagicMock(spec=QPushButton), 'gestion_datos': MagicMock(spec=QPushButton),
            'add_product': MagicMock(spec=QPushButton), 'settings': MagicMock(spec=QPushButton)
        }
        controller.view.buttons = mock_buttons
        
        controller._update_ui_for_role()
        
        for btn in mock_buttons.values():
            btn.setEnabled.assert_called_with(False)
        
        controller.view.switch_page.assert_called_with("home")

class TestHardwareSettings:
    def test_initialize_qr_scanner_success(self, controller):
        """Verifica la inicialización exitosa del escáner QR."""
        # Configurar mocks para éxito
        controller.model.db.config_repo.get_setting.return_value = '0'
        
        mock_camera_info = MagicMock(spec=CameraInfo)
        mock_camera_info.is_working = True
        mock_camera_info.index = 0
        controller.camera_manager.get_camera_info.return_value = mock_camera_info
        
        # Mock cv2.VideoCapture para evitar acceso real a hardware
        with patch('cv2.VideoCapture') as MockCapture, \
             patch('controllers.app_controller.QrScanner') as MockScanner:
            
            mock_cap = MockCapture.return_value
            mock_cap.isOpened.return_value = True
            
            mock_scanner_instance = MockScanner.return_value
            mock_scanner_instance.is_camera_ready = True
            
            controller._initialize_qr_scanner()
            
            assert controller.qr_scanner is not None
            # Verificar que se intentó configurar la cámara
            mock_cap.set.assert_called()

class TestTaskMapping:
    def test_map_task_keys_normalizes_data(self, controller):
        """Verifica que _map_task_keys normaliza correctamente los datos de tareas."""
        input_task = {
            'id': '123',
            'descripcion': 'Tarea Test',
            'tiempo': '10.5',
            'departamento': 'Montaje',
            'tipo_trabajador': 2
        }
        units = 5
        
        result = controller._map_task_keys(input_task, units)
        
        assert result['id'] == '123'
        assert result['name'] == 'Tarea Test'
        assert result['duration'] == 10.5
        assert result['trigger_units'] == 5
        assert result['required_skill_level'] == 2
        assert result['department'] == 'Montaje'

    def test_map_task_keys_handles_missing_data(self, controller):
        """Verifica que _map_task_keys maneja datos faltantes de forma robusta."""
        input_task = {} # Tarea vacía
        units = 1
        
        result = controller._map_task_keys(input_task, units)
        
        assert result['name'] == 'Tarea sin nombre'
        assert result['duration'] == 0.0
        assert result['required_skill_level'] == 1 # Default
        assert 'task_' in str(result['id']) # ID generado automáticamente

class TestUiDataLoading:
    def test_load_preprocesos_data_success(self, controller):
        """Test loading preprocesos data into widget."""
        # Use existing view fixture config, verify PreprocesosWidget spec
        mock_widget = controller.view.pages["preprocesos"] 
        # It's already a MagicMock(spec=PreprocesosWidget)
        
        # Setup data
        data = [{"id": 1, "nombre": "Corte"}]
        controller.model.get_all_preprocesos_with_components.return_value = data
        
        controller._load_preprocesos_data()
        
        mock_widget.load_preprocesos_data.assert_called_with(data)

    def test_load_preprocesos_data_error(self, controller):
        """Test error handling during preprocesos loading."""
        mock_widget = controller.view.pages["preprocesos"]
        
        controller.model.get_all_preprocesos_with_components.side_effect = Exception("DB Error")
        
        controller._load_preprocesos_data()
        
        # Should load empty list on error
        mock_widget.load_preprocesos_data.assert_called_with([])

class TestSignalConnections:
    def test_connect_signals_calls_submethods(self, controller):
        """Test that connect_signals calls all sub-connection methods."""
        # Use wraps to spy on internal methods
        with patch.object(controller, '_connect_navigation_signals') as mock_nav, \
             patch.object(controller, '_connect_add_product_signals') as mock_prod, \
             patch.object(controller, '_connect_preprocesos_signals') as mock_prep:
            
            # Setup specific nested mock needed
            controller.view.pages["gestion_datos"].trabajadores_tab = MagicMock(spec=WorkersWidget)
            controller.view.pages["gestion_datos"].trabajadores_tab.workers_list = MagicMock()
            controller.view.pages["gestion_datos"].trabajadores_tab.add_button = MagicMock()
            
            controller.connect_signals()
            
            mock_nav.assert_called_once()
            mock_prod.assert_called_once()
            mock_prep.assert_called_once()

    def test_connect_preprocesos_signals_success(self, controller):
        """Test specific connection of preprocesos signals."""
        # Check current view pages config
        mock_widget = controller.view.pages["preprocesos"]
        # Ensure adds, edits, deletes exist (they do thanks to class attr fix)
        
        controller._connect_preprocesos_signals()
        
        mock_widget.set_controller.assert_called_with(controller)
        mock_widget.add_button.clicked.connect.assert_called()

