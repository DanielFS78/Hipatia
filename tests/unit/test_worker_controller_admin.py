import pytest
import hashlib
import logging
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt
from controllers.worker_controller import WorkerController

# Dummy class for isinstance checks
class MockGestionDatosWidget:
    def __init__(self):
        self.trabajadores_tab = MagicMock()

@pytest.mark.unit
class TestWorkerControllerAdmin:
    """Tests for WorkerController (Admin side) in controllers/worker_controller.py"""

    @pytest.fixture
    def mock_app_controller(self):
        """Creates a mock AppController with necessary attributes."""
        mock_app = MagicMock()
        mock_app.db = MagicMock()
        mock_app.model = MagicMock()
        # Connect model.db to app.db so they share the same mock
        mock_app.model.db = mock_app.db
        
        mock_app.view = MagicMock()
        # Ensure user has correct role for password change
        mock_app.current_user = {"id": 1, "nombre": "AdminUser", "role": "Responsable", "username": "admin"}
        mock_app.tracking_repo = MagicMock()
        mock_app.label_manager = MagicMock()
        mock_app.qr_scanner = MagicMock()
        mock_app.qr_generator = MagicMock()
        mock_app.label_counter_repo = MagicMock()
        return mock_app

    @pytest.fixture
    def worker_controller(self, mock_app_controller):
        """Instantiates WorkerController with mocked AppController."""
        # Patch logging at the class level or instance level to avoid real logging
        with patch("controllers.worker_controller.logging") as mock_logging:
            mock_logger = MagicMock()
            mock_logging.getLogger.return_value = mock_logger
            
            controller = WorkerController(mock_app_controller)
            # Ensure the logger instance on the controller is also our mock
            controller.logger = mock_logger
            return controller

    @patch("controllers.worker_controller.WorkerMainWindow")
    @patch("controllers.worker_controller.FeatureWorkerController")
    def test_launch_worker_interface_success(self, mock_feature_ctrl, mock_window_cls, worker_controller):
        """Test successful launch of worker interface."""
        # Setup mocks
        mock_window_instance = MagicMock()
        mock_window_cls.return_value = mock_window_instance
        
        mock_feature_instance = MagicMock()
        mock_feature_ctrl.return_value = mock_feature_instance
        
        worker_controller.app.qr_scanner = MagicMock() # Ensure scanner exists

        # Execute
        worker_controller._launch_worker_interface()

        # Verify
        mock_window_cls.assert_called_once()
        worker_controller.app._initialize_qr_scanner.assert_called_once()
        mock_feature_ctrl.assert_called_once()
        mock_feature_instance.initialize.assert_called_once()
        mock_window_instance.show.assert_called_once()

    def test_on_worker_selected_in_list(self, worker_controller):
        """Test logic when a worker is selected in the list."""
        # Setup data
        worker_id = 123
        mock_item = MagicMock()
        mock_item.data.return_value = worker_id
        
        worker_data = {"id": worker_id, "nombre": "Test Worker"}
        worker_controller.model.get_worker_details.return_value = worker_data
        
        of_list = ["OF-001", "OF-002"]
        worker_controller.db.tracking_repo.get_all_ordenes_fabricacion.return_value = of_list
        
        # Use patch to replace the class used in isinstance check
        with patch("controllers.worker_controller.GestionDatosWidget", MockGestionDatosWidget):
            # Create a mock instance complying with the dummy type
            mock_page_instance = MockGestionDatosWidget()
            worker_controller.view.pages.get.return_value = mock_page_instance
            mock_workers_page = mock_page_instance.trabajadores_tab
            
            # Execute
            worker_controller._on_worker_selected_in_list(mock_item)
            
            # Verify
            worker_controller.model.get_worker_details.assert_called_with(worker_id)
            mock_workers_page.show_worker_details.assert_called_with(worker_data)
            mock_workers_page.setup_of_completer.assert_called_with(of_list)

    def test_save_worker_new_success(self, worker_controller):
        """Test saving a new worker successfully."""
        # Setup
        with patch("controllers.worker_controller.GestionDatosWidget", MockGestionDatosWidget):
            mock_page_instance = MockGestionDatosWidget()
            mock_workers_page = mock_page_instance.trabajadores_tab
            worker_controller.view.pages.get.return_value = mock_page_instance
             
            mock_workers_page.current_worker_id = None
            mock_workers_page.get_form_data.return_value = {
                "nombre_completo": "New Worker",
                "username": "newuser",
                "password": "password123",
                "role": "Trabajador",
                "tipo_trabajador": 1,
                "notas": "Note"
            }
            
            worker_controller.model.add_worker.return_value = True

            # Execute
            worker_controller._on_save_worker_clicked()

            # Verify
            worker_controller.model.add_worker.assert_called()
            # Verify hashing happened
            args, _ = worker_controller.model.add_worker.call_args
            assert args[0] == "New Worker"
            hashed_pw = args[4]
            assert hashed_pw == hashlib.sha256(b"password123").hexdigest()
            
            worker_controller.view.show_message.assert_called_with("Éxito", "Trabajador añadido.", "info")

    def test_save_worker_update_success(self, worker_controller):
        """Test updating an existing worker."""
        # Setup
        with patch("controllers.worker_controller.GestionDatosWidget", MockGestionDatosWidget):
            mock_page_instance = MockGestionDatosWidget()
            mock_workers_page = mock_page_instance.trabajadores_tab
            worker_controller.view.pages.get.return_value = mock_page_instance
            
            mock_workers_page.current_worker_id = 99
            mock_workers_page.get_form_data.return_value = {
                "nombre_completo": "Updated Worker",
                "activo": True,
                "notas": "Updated Note"
                # No username/password change
            }
            
            worker_controller.model.update_worker.return_value = True

            # Execute
            worker_controller._on_save_worker_clicked()

            # Verify
            worker_controller.model.update_worker.assert_called_with(
                99, "Updated Worker", True, "Updated Note", 1, None, None, None
            )
            worker_controller.view.show_message.assert_called_with("Éxito", "Trabajador actualizado.", "info")

    def test_save_worker_validation_error(self, worker_controller):
        """Test validation error when name is missing."""
         # Setup
        with patch("controllers.worker_controller.GestionDatosWidget", MockGestionDatosWidget):
            mock_page_instance = MockGestionDatosWidget()
            mock_workers_page = mock_page_instance.trabajadores_tab
            worker_controller.view.pages.get.return_value = mock_page_instance
            
            mock_workers_page.get_form_data.return_value = {
                "nombre_completo": "" # Empty name
            }

            # Execute
            worker_controller._on_save_worker_clicked()

            # Verify no DB call
            worker_controller.model.add_worker.assert_not_called()
            worker_controller.model.update_worker.assert_not_called()
            worker_controller.view.show_message.assert_called_with("Error", "El nombre del trabajador es obligatorio.", "warning")

    def test_delete_worker_confirmed(self, worker_controller):
        """Test deleting a worker when confirmed."""
        worker_id = 55
        worker_controller.view.show_confirmation_dialog.return_value = True
        worker_controller.model.delete_worker.return_value = True

        worker_controller._on_delete_worker_clicked(worker_id)

        worker_controller.model.delete_worker.assert_called_with(worker_id)
        worker_controller.view.show_message.assert_called_with("Éxito", "Trabajador eliminado.", "info")

    def test_delete_worker_cancelled(self, worker_controller):
        """Test deleting a worker when cancelled by user."""
        worker_id = 55
        worker_controller.view.show_confirmation_dialog.return_value = False

        worker_controller._on_delete_worker_clicked(worker_id)

        worker_controller.model.delete_worker.assert_not_called()

    @patch("controllers.worker_controller.ChangePasswordDialog")
    def test_change_worker_password_success(self, MockDialog, worker_controller):
        """Test changing a worker password via dialog."""
        worker_id = 10
        mock_dialog_instance = MockDialog.return_value
        mock_dialog_instance.exec.return_value = 1  # Verify correct dialog code
        
        mock_dialog_instance.get_passwords.return_value = {
            "new": "newpass",
            "confirm": "newpass"
        }
        
        # Mock Worker Data return
        worker_controller.model.get_worker_details.return_value = {"nombre_completo": "Test"}
        
        # Ensure update returns True
        worker_controller.model.worker_repo.update_user_password.return_value = True
        
        # Ensure user is valid and has role (set in fixture but good to double check)
        assert worker_controller.app.current_user.get("role") == "Responsable"

        worker_controller._on_change_worker_password_clicked(worker_id)

        worker_controller.model.worker_repo.update_user_password.assert_called_with(worker_id, "newpass")
        # Verify success message (partially as exact message contains formatting)
        worker_controller.view.show_message.assert_called()
        assert "Éxito" in worker_controller.view.show_message.call_args[0]
