import sys
import pytest
from unittest.mock import MagicMock, patch, ANY
import json
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import Qt

from controllers.app_controller import AppController
from ui.widgets import SettingsWidget, CalculateTimesWidget, AddProductWidget, GestionDatosWidget

# --- FIXTURES ---

@pytest.fixture
def mock_view():
    """Mock de MainView con todas las páginas y componentes necesarios."""
    view = MagicMock()
    view.pages = {}
    view.buttons = {}
    view.show_message = MagicMock()
    view.show_confirmation_dialog = MagicMock(return_value=True)
    return view

@pytest.fixture
def mock_model():
    """Mock de AppModel con repositorios simulados."""
    model = MagicMock()
    model.db = MagicMock()
    model.worker_repo = MagicMock()
    model.config_repo = MagicMock()
    model.lote_repo = MagicMock()
    model.product_deleted_signal = MagicMock()
    model.pilas_changed_signal = MagicMock()
    
    # Mockear repositorios específicos
    model.db.config_repo = model.config_repo
    model.db.tracking_repo = MagicMock()
    
    return model

@pytest.fixture
def mock_schedule_config():
    """Mock de ScheduleConfig."""
    return MagicMock()

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
        
        # Mock botones
        mock_buttons = {
            'dashboard': MagicMock(), 'reportes': MagicMock(),
            'historial': MagicMock(), 'gestion_datos': MagicMock(),
            'add_product': MagicMock(), 'settings': MagicMock()
        }
        controller.view.buttons = mock_buttons
        
        controller._update_ui_for_role()
        
        for btn in mock_buttons.values():
            btn.setEnabled.assert_called_with(True)

    def test_update_ui_for_role_worker(self, controller):
        """Verifica que el rol Trabajador deshabilita botones y redirige a home."""
        controller.current_user = {'role': 'Trabajador'}
        
        mock_buttons = {
            'dashboard': MagicMock(), 'reportes': MagicMock(),
            'historial': MagicMock(), 'gestion_datos': MagicMock(),
            'add_product': MagicMock(), 'settings': MagicMock()
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
        
        mock_camera_info = MagicMock()
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
        # Setup mock widget
        mock_widget = MagicMock()
        controller.view.pages = {"preprocesos": mock_widget}
        
        # Setup data
        data = [{"id": 1, "nombre": "Corte"}]
        controller.model.get_all_preprocesos_with_components.return_value = data
        
        controller._load_preprocesos_data()
        
        mock_widget.load_preprocesos_data.assert_called_with(data)

    def test_load_preprocesos_data_error(self, controller):
        """Test error handling during preprocesos loading."""
        mock_widget = MagicMock()
        controller.view.pages = {"preprocesos": mock_widget}
        
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
            
            # Setup view pages for safety
            mock_gestion = MagicMock()
            mock_gestion.trabajadores_tab = MagicMock()
            controller.view.pages = {"gestion_datos": mock_gestion}
            
            controller.connect_signals()
            
            mock_nav.assert_called_once()
            mock_prod.assert_called_once()
            mock_prep.assert_called_once()

    def test_connect_preprocesos_signals_success(self, controller):
        """Test specific connection of preprocesos signals."""
        from ui.widgets import PreprocesosWidget
        
        mock_widget = MagicMock(spec=PreprocesosWidget)
        mock_widget.add_button = MagicMock()
        mock_widget.edit_button = MagicMock()
        mock_widget.delete_button = MagicMock()
        
        controller.view.pages = {"preprocesos": mock_widget}
        
        controller._connect_preprocesos_signals()
        
        mock_widget.set_controller.assert_called_with(controller)
        mock_widget.add_button.clicked.connect.assert_called()
