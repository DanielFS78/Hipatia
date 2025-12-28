"""
Tests unitarios para AppController - Navegación y UI.

Cobertura objetivo: Métodos de navegación, señales y gestión de UI.
"""
import pytest
from unittest.mock import MagicMock, patch
from controllers.app_controller import AppController
from ui.widgets import SettingsWidget, CalculateTimesWidget


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_view():
    """Mock de MainView con páginas y botones de navegación."""
    view = MagicMock()
    view.pages = {
        "settings": MagicMock(),
        "calculate": MagicMock(),
        "gestion_datos": MagicMock(),
    }
    view.buttons = {
        "home": MagicMock(),
        "dashboard": MagicMock(),
        "settings": MagicMock(),
        "calculate": MagicMock(),
        "historial": MagicMock(),
        "gestion_datos": MagicMock(),
        "context_help": MagicMock(),
        "reportes": MagicMock(),
        "add_product": MagicMock(),
    }
    view.show_message = MagicMock()
    view.switch_page = MagicMock()
    return view


@pytest.fixture
def mock_model():
    """Mock de AppModel."""
    model = MagicMock()
    model.db = MagicMock()
    model.db.config_repo = MagicMock()
    model.db.tracking_repo = MagicMock()
    model.worker_repo = MagicMock()
    model.product_deleted_signal = MagicMock()
    model.pilas_changed_signal = MagicMock()
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


# =============================================================================
# TESTS: _on_nav_button_clicked
# =============================================================================

class TestOnNavButtonClicked:
    """Tests para _on_nav_button_clicked."""

    def test_nav_button_switches_to_home(self, controller):
        """Verifica navegación a la página de inicio."""
        controller._on_nav_button_clicked("home")
        controller.view.switch_page.assert_called_once_with("home")

    def test_nav_button_switches_to_dashboard(self, controller):
        """Verifica navegación a dashboard y actualización de vista."""
        controller.update_dashboard_view = MagicMock()
        controller._on_nav_button_clicked("dashboard")
        
        controller.view.switch_page.assert_called_once_with("dashboard")
        controller.update_dashboard_view.assert_called_once()

    def test_nav_button_switches_to_settings(self, controller):
        """Verifica navegación a configuración y carga de ajustes."""
        controller._load_schedule_settings = MagicMock()
        controller._on_nav_button_clicked("settings")
        
        controller.view.switch_page.assert_called_once_with("settings")
        controller._load_schedule_settings.assert_called_once()

    def test_nav_button_switches_to_historial(self, controller):
        """Verifica navegación a historial y actualización."""
        controller.update_historial_view = MagicMock()
        controller._on_nav_button_clicked("historial")
        
        controller.view.switch_page.assert_called_once_with("historial")
        controller.update_historial_view.assert_called_once()

    def test_nav_button_switches_to_calculate(self, controller):
        """Verifica navegación a página de cálculo."""
        mock_calc = MagicMock(spec=CalculateTimesWidget)
        mock_calc.planning_session = []
        controller.view.pages = {"calculate": mock_calc}
        
        with patch('PyQt6.QtCore.QTimer'):
            controller._on_nav_button_clicked("calculate")
        
        controller.view.switch_page.assert_called_once_with("calculate")
        assert mock_calc.planning_session == []

    def test_nav_button_switches_to_gestion_datos(self, controller):
        """Verifica navegación a gestión de datos."""
        controller.update_workers_view = MagicMock()
        controller.update_machines_view = MagicMock()
        controller.update_lotes_view = MagicMock()
        
        mock_gestion = MagicMock()
        mock_gestion.productos_tab = MagicMock()
        mock_gestion.productos_tab.search_entry = MagicMock()
        mock_gestion.fabricaciones_tab = MagicMock()
        mock_gestion.fabricaciones_tab.search_entry = MagicMock()
        controller.view.pages = {"gestion_datos": mock_gestion}
        
        controller._on_nav_button_clicked("gestion_datos")
        
        controller.view.switch_page.assert_called_once_with("gestion_datos")
        controller.update_workers_view.assert_called_once()
        controller.update_machines_view.assert_called_once()
        controller.update_lotes_view.assert_called_once()

    def test_nav_button_switches_to_preprocesos(self, controller):
        """Verifica navegación a preprocesos y carga de datos."""
        controller._load_preprocesos_data = MagicMock()
        controller._on_nav_button_clicked("preprocesos")
        
        controller.view.switch_page.assert_called_once_with("preprocesos")
        controller._load_preprocesos_data.assert_called_once()

    def test_nav_button_switches_to_definir_lote(self, controller):
        """Verifica navegación a definir lote y limpieza de formulario."""
        mock_lote = MagicMock()
        mock_lote.clear_form = MagicMock()
        controller.view.pages = {"definir_lote": mock_lote}
        
        controller._on_nav_button_clicked("definir_lote")
        
        controller.view.switch_page.assert_called_once_with("definir_lote")
        mock_lote.clear_form.assert_called_once()


# =============================================================================
# TESTS: _connect_navigation_signals
# =============================================================================

class TestConnectNavigationSignals:
    """Tests para _connect_navigation_signals."""

    def test_connects_navigation_buttons(self, controller):
        """Verifica que se conectan los botones de navegación."""
        controller._connect_navigation_signals()
        
        for name, button in controller.view.buttons.items():
            button.clicked.connect.assert_called()

    def test_connects_settings_signals_when_present(self, controller):
        """Verifica conexión de señales de configuración."""
        mock_settings = MagicMock(spec=SettingsWidget)
        mock_settings.add_holiday_button = MagicMock()
        mock_settings.remove_holiday_button = MagicMock()
        mock_settings.import_signal = MagicMock()
        mock_settings.export_signal = MagicMock()
        mock_settings.save_schedule_signal = MagicMock()
        mock_settings.add_break_signal = MagicMock()
        mock_settings.sync_signal = MagicMock()
        mock_settings.change_own_password_signal = MagicMock()
        mock_settings.edit_break_signal = MagicMock()
        mock_settings.remove_break_signal = MagicMock()
        mock_settings.detect_cameras_signal = MagicMock()
        mock_settings.save_hardware_signal = MagicMock()
        mock_settings.import_tasks_signal = MagicMock()
        
        controller.view.pages = {"settings": mock_settings}
        
        controller._connect_navigation_signals()
        
        mock_settings.add_holiday_button.clicked.connect.assert_called()
        mock_settings.remove_holiday_button.clicked.connect.assert_called()
        mock_settings.import_signal.connect.assert_called()
        mock_settings.export_signal.connect.assert_called()


# =============================================================================
# TESTS: _update_ui_for_role
# =============================================================================

class TestUpdateUiForRole:
    """Tests para _update_ui_for_role."""

    def test_update_ui_for_responsable_role(self, controller):
        """Verifica UI para rol de Responsable."""
        controller.current_user = {'role': 'Responsable'}
        
        controller._update_ui_for_role()
        
        controller.view.buttons['dashboard'].setEnabled.assert_called_with(True)
        controller.view.buttons['settings'].setEnabled.assert_called_with(True)

    def test_update_ui_for_worker_role(self, controller):
        """Verifica UI para rol de Trabajador."""
        controller.current_user = {'role': 'Trabajador'}
        
        controller._update_ui_for_role()
        
        controller.view.buttons['dashboard'].setEnabled.assert_called_with(False)
        controller.view.buttons['settings'].setEnabled.assert_called_with(False)
        controller.view.switch_page.assert_called_with("home")
        controller.view.show_message.assert_called()

    def test_update_ui_no_current_user(self, controller):
        """Verifica que no hace nada si no hay usuario."""
        controller.current_user = None
        
        controller._update_ui_for_role()
        
        # No debería llamar a setEnabled
        for btn in controller.view.buttons.values():
            btn.setEnabled.assert_not_called()


# =============================================================================
# TESTS: _on_context_help_clicked
# =============================================================================

class TestOnContextHelpClicked:
    """Tests para _on_context_help_clicked."""

    def test_context_help_shows_message(self, controller):
        """Verifica que se muestra ayuda contextual."""
        # Simular página actual
        controller.view.current_page_name = MagicMock(return_value="home")
        controller.view.pages = {"home": MagicMock()}
        
        with patch.object(controller.view, 'current_page_name', "home"):
            controller._on_context_help_clicked()


# =============================================================================
# TESTS: Edit Search Type
# =============================================================================

class TestEditSearchType:
    """Tests para _edit_search_type attribute."""

    def test_edit_search_type_default_value(self, controller):
        """Verifica que _edit_search_type tiene valor inicial correcto."""
        assert controller._edit_search_type == "Productos"

    def test_edit_search_type_can_be_changed(self, controller):
        """Verifica que _edit_search_type puede ser modificado."""
        controller._edit_search_type = "Fabricaciones"
        assert controller._edit_search_type == "Fabricaciones"




# =============================================================================
# TESTS: connect_signals
# =============================================================================

class TestConnectSignals:
    """Tests para connect_signals."""

    def test_connect_signals_calls_all_connectors(self, controller):
        """Verifica que connect_signals llama a todos los métodos de conexión."""
        controller._connect_navigation_signals = MagicMock()
        controller._connect_add_product_signals = MagicMock()
        controller._connect_reportes_signals = MagicMock()
        controller._connect_calculate_signals = MagicMock()
        controller._connect_historial_signals = MagicMock()
        controller._connect_workers_signals = MagicMock()
        controller._connect_machines_signals = MagicMock()
        controller._connect_products_signals = MagicMock()
        controller._connect_fabrications_signals = MagicMock()
        controller._connect_preprocesos_signals = MagicMock()
        controller._connect_definir_lote_signals = MagicMock()
        controller._connect_lotes_management_signals = MagicMock()
        
        controller.connect_signals()
        
        controller._connect_navigation_signals.assert_called_once()
        controller._connect_add_product_signals.assert_called_once()
        controller._connect_reportes_signals.assert_called_once()
        controller._connect_calculate_signals.assert_called_once()

    def test_connect_signals_handles_preprocesos_exception(self, controller):
        """Verifica manejo de excepción al conectar señales de preprocesos."""
        controller._connect_navigation_signals = MagicMock()
        controller._connect_add_product_signals = MagicMock()
        controller._connect_reportes_signals = MagicMock()
        controller._connect_calculate_signals = MagicMock()
        controller._connect_historial_signals = MagicMock()
        controller._connect_workers_signals = MagicMock()
        controller._connect_machines_signals = MagicMock()
        controller._connect_products_signals = MagicMock()
        controller._connect_fabrications_signals = MagicMock()
        controller._connect_preprocesos_signals = MagicMock(side_effect=Exception("Error"))
        controller._connect_definir_lote_signals = MagicMock()
        controller._connect_lotes_management_signals = MagicMock()
        
        # No debería propagar la excepción
        controller.connect_signals()


# =============================================================================
# TESTS: Help Texts
# =============================================================================

class TestHelpTexts:
    """Tests para textos de ayuda contextual."""

    def test_help_texts_exist_for_all_pages(self, controller):
        """Verifica que existen textos de ayuda para las páginas principales."""
        expected_pages = ["home", "dashboard", "settings", "historial", "gestion_datos"]
        
        for page in expected_pages:
            assert page in controller.help_texts
            assert len(controller.help_texts[page]) > 0

    def test_help_texts_are_strings(self, controller):
        """Verifica que todos los textos de ayuda son strings."""
        for page, text in controller.help_texts.items():
            assert isinstance(text, str)
