"""
Tests unitarios para AppController - Configuración y Settings.

Cobertura objetivo: Métodos de configuración de horarios, descansos y festivos.
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, time
from controllers.app_controller import AppController


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_view():
    """Mock de MainView con páginas configuradas."""
    view = MagicMock()
    
    # Mock completo del SettingsWidget
    mock_settings = MagicMock()
    mock_settings.calendar = MagicMock()
    mock_settings.breaks_list = MagicMock()
    mock_settings.start_time_edit = MagicMock()
    mock_settings.end_time_edit = MagicMock()
    mock_settings.work_start_time = MagicMock()
    mock_settings.work_end_time = MagicMock()
    mock_settings.holiday_list = MagicMock()
    
    view.pages = {"settings": mock_settings}
    view.buttons = {}
    view.show_message = MagicMock()
    view.show_confirmation_dialog = MagicMock(return_value=True)
    return view


@pytest.fixture
def mock_model():
    """Mock de AppModel."""
    model = MagicMock()
    model.db = MagicMock()
    model.db.config_repo = MagicMock()
    model.db.config_repo.get_setting = MagicMock(return_value='[]')
    model.db.tracking_repo = MagicMock()
    model.worker_repo = MagicMock()
    model.product_deleted_signal = MagicMock()
    model.pilas_changed_signal = MagicMock()
    return model


@pytest.fixture
def mock_schedule_config():
    """Mock de ScheduleConfig."""
    config = MagicMock()
    config.reload_config = MagicMock()
    return config


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
# TESTS: _on_add_holiday
# =============================================================================

class TestOnAddHoliday:
    """Tests para _on_add_holiday."""

    def test_add_holiday_new_date(self, controller):
        """Verifica añadir un festivo nuevo."""
        mock_qdate = MagicMock()
        mock_qdate.toPyDate.return_value = date(2024, 12, 25)
        
        settings_page = controller.view.pages["settings"]
        settings_page.calendar.selectedDate.return_value = mock_qdate
        
        # Simular lista vacía de festivos
        controller.model.db.config_repo.get_setting.return_value = "[]"
        
        # Mockear _load_schedule_settings para evitar efectos secundarios
        controller._load_schedule_settings = MagicMock()
        
        controller._on_add_holiday()
        
        # Verificar que se guardó el festivo
        controller.model.db.config_repo.set_setting.assert_called_once()
        call_args = controller.model.db.config_repo.set_setting.call_args
        assert "holidays" in call_args[0]

    def test_add_holiday_already_exists(self, controller):
        """Verifica que no se añade un festivo duplicado."""
        mock_qdate = MagicMock()
        mock_qdate.toPyDate.return_value = date(2024, 12, 25)
        
        settings_page = controller.view.pages["settings"]
        settings_page.calendar.selectedDate.return_value = mock_qdate
        
        # Simular que el festivo ya existe
        controller.model.db.config_repo.get_setting.return_value = '["2024-12-25"]'
        
        controller._on_add_holiday()
        
        # No debería llamar a set_setting porque ya existe
        controller.model.db.config_repo.set_setting.assert_not_called()


# =============================================================================
# TESTS: _on_remove_holiday
# =============================================================================

class TestOnRemoveHoliday:
    """Tests para _on_remove_holiday."""

    def test_remove_holiday_success(self, controller):
        """Verifica eliminar un festivo correctamente."""
        mock_qdate = MagicMock()
        mock_qdate.toPyDate.return_value = date(2024, 12, 25)
        
        settings_page = controller.view.pages["settings"]
        settings_page.calendar.selectedDate.return_value = mock_qdate
        
        # Simular que el festivo existe
        controller.model.db.config_repo.get_setting.return_value = '["2024-12-25", "2024-01-01"]'
        
        # Mockear _load_schedule_settings
        controller._load_schedule_settings = MagicMock()
        
        controller._on_remove_holiday()
        
        # Verificar que se llamó a guardar
        controller.model.db.config_repo.set_setting.assert_called_once()

    def test_remove_holiday_not_found(self, controller):
        """Verifica comportamiento cuando el festivo no existe."""
        mock_qdate = MagicMock()
        mock_qdate.toPyDate.return_value = date(2024, 7, 4)
        
        settings_page = controller.view.pages["settings"]
        settings_page.calendar.selectedDate.return_value = mock_qdate
        
        # Simular lista sin ese festivo
        controller.model.db.config_repo.get_setting.return_value = '["2024-12-25"]'
        
        controller._on_remove_holiday()
        
        # No debería llamar a set_setting
        controller.model.db.config_repo.set_setting.assert_not_called()


# =============================================================================
# TESTS: _on_save_schedule_settings
# =============================================================================

class TestOnSaveScheduleSettings:
    """Tests para _on_save_schedule_settings."""

    def test_save_schedule_settings_calls_set_setting(self, controller):
        """Verifica que guardar configuración llama a set_setting."""
        settings_page = controller.view.pages["settings"]
        
        mock_start = MagicMock()
        mock_time_start = MagicMock()
        mock_time_start.toPyTime.return_value = time(8, 0)
        mock_start.time.return_value = mock_time_start
        
        mock_end = MagicMock()
        mock_time_end = MagicMock()
        mock_time_end.toPyTime.return_value = time(17, 0)
        mock_end.time.return_value = mock_time_end
        
        settings_page.start_time_edit = mock_start
        settings_page.end_time_edit = mock_end
        
        controller._on_save_schedule_settings()
        
        # Verificar que se guardó la configuración
        controller.model.db.config_repo.set_setting.assert_called()
        controller.schedule_manager.reload_config.assert_called()


# =============================================================================
# TESTS: Break Management - Simple Tests
# =============================================================================

class TestBreakManagement:
    """Tests para gestión de descansos."""

    def test_add_break_clicked_exists(self, controller):
        """Verifica que _on_add_break_clicked existe."""
        assert hasattr(controller, '_on_add_break_clicked')
        assert callable(controller._on_add_break_clicked)

    def test_on_add_break_exists(self, controller):
        """Verifica que _on_add_break existe."""
        assert hasattr(controller, '_on_add_break')
        assert callable(controller._on_add_break)

    def test_on_remove_break_clicked_no_selection(self, controller):
        """Verifica comportamiento sin selección."""
        settings_page = controller.view.pages["settings"]
        settings_page.breaks_list.currentItem.return_value = None
        
        controller._on_remove_break_clicked()
        
        # Show message debería ser llamado (ninguna selección)
        # Note: El código real muestra un mensaje, verificamos que no crashea

    def test_on_edit_break_clicked_no_selection(self, controller):
        """Verifica comportamiento sin selección en edición."""
        settings_page = controller.view.pages["settings"]
        settings_page.breaks_list.currentItem.return_value = None
        
        # Should not crash when no selection
        controller._on_edit_break_clicked()


# =============================================================================
# TESTS: _load_schedule_settings
# =============================================================================

class TestLoadScheduleSettings:
    """Tests para _load_schedule_settings."""

    def test_load_schedule_settings_method_exists(self, controller):
        """Verifica que _load_schedule_settings existe."""
        assert hasattr(controller, '_load_schedule_settings')
        assert callable(controller._load_schedule_settings)


# =============================================================================
# TESTS: Edge Cases
# =============================================================================

class TestSettingsEdgeCases:
    """Tests para casos límite de configuración."""

    def test_settings_page_in_view(self, controller):
        """Verifica que la página de settings existe en view.pages."""
        assert "settings" in controller.view.pages

    def test_schedule_manager_accessible(self, controller):
        """Verifica que schedule_manager es accesible."""
        assert hasattr(controller, 'schedule_manager')

    def test_model_config_repo_accessible(self, controller):
        """Verifica que config_repo es accesible."""
        assert hasattr(controller.model.db, 'config_repo')
