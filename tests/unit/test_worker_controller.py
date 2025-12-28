"""
Tests unitarios para AppController - Gestión de Workers.

Cobertura objetivo: Métodos relacionados con trabajadores y asignación de tareas.
"""
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt

from controllers.worker_controller import WorkerController
from ui.widgets import GestionDatosWidget, WorkersWidget


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def controller():
    """Crea WorkerController con dependencias mockeadas."""
    mock_app = MagicMock()
    mock_app.model = MagicMock()
    mock_app.model.get_all_workers.return_value = []
    mock_app.model.worker_repo = MagicMock()
    mock_app.model.add_worker.return_value = True
    mock_app.model.update_worker.return_value = True
    mock_app.model.delete_worker.return_value = True
    mock_app.model.get_worker_details.return_value = {"id": 1, "nombre_completo": "Test"}
    mock_app.db = MagicMock()
    mock_app.db.tracking_repo = MagicMock()
    mock_app.db.tracking_repo.get_all_ordenes_fabricacion.return_value = []
    
    view = MagicMock()
    view.pages = {}
    view.show_message = MagicMock()
    view.show_confirmation_dialog = MagicMock(return_value=True)
    mock_app.view = view
    mock_app.current_user = {"id": 1, "username": "admin", "role": "Responsable"} # Default user

    ctrl = WorkerController(mock_app)
    return ctrl


@pytest.fixture
def mock_workers_page():
    """Mock de WorkersWidget."""
    page = MagicMock(spec=WorkersWidget)
    page.current_worker_id = None
    page.get_form_data.return_value = {
        "nombre_completo": "Test Worker",
        "notas": "Notes",
        "tipo_trabajador": 1,
        "username": "testuser",
        "password": "testpass",
        "role": "Trabajador",
        "activo": True
    }
    page.workers_list = MagicMock()
    page.show_worker_details = MagicMock()
    page.setup_of_completer = MagicMock()
    page.clear_details_area = MagicMock()
    return page


@pytest.fixture
def mock_gestion_datos_page(mock_workers_page):
    """Mock de GestionDatosWidget con trabajadores_tab."""
    page = MagicMock(spec=GestionDatosWidget)
    page.trabajadores_tab = mock_workers_page
    return page


# =============================================================================
# TESTS: update_workers_view
# =============================================================================

class TestUpdateWorkersView:
    """Tests para update_workers_view."""

    def test_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller.update_workers_view)


# =============================================================================
# TESTS: _connect_workers_signals
# =============================================================================

class TestConnectWorkersSignals:
    """Tests para _connect_workers_signals."""

    def test_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller._connect_workers_signals)

    def test_no_crash_with_page(self, controller, mock_gestion_datos_page, mock_workers_page):
        """Verifica que no crashea con página mockeada completa."""
        mock_workers_page.add_button = MagicMock()
        controller.view.pages = {"gestion_datos": mock_gestion_datos_page}
        # No debería crashear con la página configurada
        controller._connect_workers_signals()


# =============================================================================
# TESTS: _on_save_worker_clicked
# =============================================================================

class TestOnSaveWorkerClicked:
    """Tests para _on_save_worker_clicked."""

    def test_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller._on_save_worker_clicked)

    def test_returns_early_without_page(self, controller):
        """Verifica retorno si no hay página gestion_datos."""
        controller.view.pages = {}
        controller._on_save_worker_clicked()
        controller.view.show_message.assert_not_called()

    def test_shows_warning_for_invalid_data(self, controller, mock_gestion_datos_page, mock_workers_page):
        """Verifica warning con datos inválidos."""
        controller.view.pages = {"gestion_datos": mock_gestion_datos_page}
        mock_workers_page.get_form_data.return_value = None
        
        with patch('controllers.app_controller.isinstance', return_value=True):
            controller._on_save_worker_clicked()
        
        controller.view.show_message.assert_called()

    def test_shows_warning_for_empty_name(self, controller, mock_gestion_datos_page, mock_workers_page):
        """Verifica warning cuando nombre está vacío."""
        controller.view.pages = {"gestion_datos": mock_gestion_datos_page}
        mock_workers_page.get_form_data.return_value = {"nombre_completo": ""}
        
        with patch('controllers.worker_controller.isinstance', return_value=True):
            controller._on_save_worker_clicked()
        
        controller.view.show_message.assert_called()

    def test_adds_new_worker_successfully(self, controller, mock_gestion_datos_page, mock_workers_page):
        """Verifica añadir nuevo trabajador con éxito."""
        controller.view.pages = {"gestion_datos": mock_gestion_datos_page}
        mock_workers_page.current_worker_id = None  # Nuevo
        
        with patch('controllers.worker_controller.isinstance', return_value=True), \
             patch.object(controller, 'update_workers_view'):
            controller._on_save_worker_clicked()
        
        controller.model.add_worker.assert_called()
        controller.view.show_message.assert_called()

    def test_updates_existing_worker(self, controller, mock_gestion_datos_page, mock_workers_page):
        """Verifica actualización de trabajador existente."""
        controller.view.pages = {"gestion_datos": mock_gestion_datos_page}
        mock_workers_page.current_worker_id = 1  # Existente
        
        with patch('controllers.worker_controller.isinstance', return_value=True), \
             patch.object(controller, 'update_workers_view'):
            controller._on_save_worker_clicked()
        
        controller.model.update_worker.assert_called()

    def test_handles_unique_constraint_error(self, controller, mock_gestion_datos_page, mock_workers_page):
        """Verifica manejo de error de constraint único."""
        controller.view.pages = {"gestion_datos": mock_gestion_datos_page}
        mock_workers_page.current_worker_id = None
        controller.model.add_worker.return_value = "UNIQUE_CONSTRAINT"
        
        with patch('controllers.worker_controller.isinstance', return_value=True):
            controller._on_save_worker_clicked()
        
        controller.view.show_message.assert_called()


# =============================================================================
# TESTS: _on_delete_worker_clicked
# =============================================================================

class TestOnDeleteWorkerClicked:
    """Tests para _on_delete_worker_clicked."""

    def test_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller._on_delete_worker_clicked)

    def test_deletes_on_confirmation(self, controller):
        """Verifica eliminación con confirmación."""
        controller.view.show_confirmation_dialog.return_value = True
        controller.model.delete_worker.return_value = True
        
        controller._on_delete_worker_clicked(1)
        
        controller.model.delete_worker.assert_called_with(1)
        controller.view.show_message.assert_called()

    def test_cancels_on_no_confirmation(self, controller):
        """Verifica que no elimina sin confirmación."""
        controller.view.show_confirmation_dialog.return_value = False
        
        controller._on_delete_worker_clicked(1)
        
        controller.model.delete_worker.assert_not_called()

    def test_shows_error_on_delete_failure(self, controller):
        """Verifica mensaje de error al fallar eliminación."""
        controller.view.show_confirmation_dialog.return_value = True
        controller.model.delete_worker.return_value = False
        
        controller._on_delete_worker_clicked(1)
        
        controller.view.show_message.assert_called_with("Error", "No se pudo eliminar.", "critical")


# =============================================================================
# TESTS: _on_worker_selected_in_list
# =============================================================================

class TestOnWorkerSelectedInList:
    """Tests para _on_worker_selected_in_list."""

    def test_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller._on_worker_selected_in_list)

    def test_loads_worker_details(self, controller, mock_gestion_datos_page, mock_workers_page):
        """Verifica carga de detalles de trabajador."""
        controller.view.pages = {"gestion_datos": mock_gestion_datos_page}
        mock_item = MagicMock()
        mock_item.data.return_value = 1
        
        with patch('controllers.worker_controller.isinstance', return_value=True):
            controller._on_worker_selected_in_list(mock_item)
        
        controller.model.get_worker_details.assert_called_with(1)
        mock_workers_page.show_worker_details.assert_called()

    def test_clears_area_when_no_data(self, controller, mock_gestion_datos_page, mock_workers_page):
        """Verifica que limpia el área cuando no hay datos."""
        controller.view.pages = {"gestion_datos": mock_gestion_datos_page}
        controller.model.get_worker_details.return_value = None
        mock_item = MagicMock()
        mock_item.data.return_value = 999
        
        with patch('controllers.worker_controller.isinstance', return_value=True):
            controller._on_worker_selected_in_list(mock_item)
        
        mock_workers_page.clear_details_area.assert_called()


# =============================================================================
# TESTS: _on_worker_product_search_changed
# =============================================================================

class TestOnWorkerProductSearchChanged:
    """Tests para _on_worker_product_search_changed."""

    def test_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller._on_worker_product_search_changed)


# =============================================================================
# TESTS: _on_assign_task_to_worker_clicked
# =============================================================================

class TestOnAssignTaskToWorkerClicked:
    """Tests para _on_assign_task_to_worker_clicked."""

    def test_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller._on_assign_task_to_worker_clicked)


# =============================================================================
# TESTS: _on_cancel_task_clicked
# =============================================================================

class TestOnCancelTaskClicked:
    """Tests para _on_cancel_task_clicked."""

    def test_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller._on_cancel_task_clicked)


# =============================================================================
# TESTS: _on_change_worker_password_clicked
# =============================================================================

class TestOnChangeWorkerPasswordClicked:
    """Tests para _on_change_worker_password_clicked."""

    def test_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller._on_change_worker_password_clicked)


# =============================================================================
# TESTS: _on_change_own_password_clicked
# =============================================================================

class TestOnChangeOwnPasswordClicked:
    """Tests para _on_change_own_password_clicked."""

    def test_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller._on_change_own_password_clicked)

