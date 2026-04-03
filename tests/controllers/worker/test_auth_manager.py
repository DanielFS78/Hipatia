"""
Pruebas Unitarias para WorkerAuthManager.

Este módulo verifica la lógica de autenticación y cambio de contraseñas
para los trabajadores, incluyendo validaciones de permisos y roles.
"""
import pytest
from unittest.mock import MagicMock, create_autospec, patch, ANY
from controllers.worker.auth_manager import WorkerAuthManager
from controllers.worker.protocols import IWorkerView, IWorkerService
from core.dtos_models import WorkerDTO
from core.security.access_control import set_security_service
from core.security.security_service import SecurityService

@pytest.mark.unit
class TestWorkerAuthManager:
    """Suite de pruebas para el gestor de autenticación de trabajadores."""

    @pytest.fixture(autouse=True)
    def setup_security(self):
        """Configura un mock estricto del servicio de seguridad."""
        mock_security = MagicMock(spec=SecurityService)
        mock_security.has_permission.return_value = True
        set_security_service(mock_security)
        yield
        set_security_service(None)
    @pytest.fixture
    def mock_view(self):
        """Crea un mock de la interfaz de vista del trabajador."""
        return MagicMock(spec=IWorkerView)

    @pytest.fixture
    def mock_service(self):
        """Crea un mock de la interfaz de servicio del trabajador."""
        return MagicMock(spec=IWorkerService)

    @pytest.fixture
    def mock_app(self):
        """Crea un mock de la aplicación principal con un usuario actual."""
        app = MagicMock(spec=["current_user"])
        user = MagicMock(spec=["id", "username", "role"])
        user.id = 1
        user.username = 'admin'
        user.role = 'Responsable'
        app.current_user = user
        return app

    @pytest.fixture
    def manager(self, mock_app, mock_view, mock_service):
        """Instancia WorkerAuthManager con sus dependencias."""
        return WorkerAuthManager(app=mock_app, view=mock_view, worker_service=mock_service)

    def test_change_worker_password_success(self, manager, mock_view, mock_service):
        """Prueba el cambio exitoso de contraseña de un trabajador."""
        # Configurar mocks
        worker_data = MagicMock(spec=WorkerDTO)
        worker_data.nombre_completo = 'Juan Perez'
        mock_service.get_worker_details.return_value = worker_data
        mock_service.update_user_password.return_value = True
        
        # Mock del diálogo usando patch como context manager
        with patch('controllers.worker.auth_manager.ChangePasswordDialog') as mock_dialog_class:
            mock_dialog = mock_dialog_class.return_value
            mock_dialog.exec.return_value = 1 # Accepted
            mock_dialog.get_passwords.return_value = {'new': 'ValidPass123!', 'confirm': 'ValidPass123!'}
            
            # Ejecutar
            manager._on_change_worker_password_clicked(10)
            
            # Verificar
            mock_service.update_user_password.assert_called_once_with(10, 'ValidPass123!')
            mock_view.show_message.assert_called_with("Éxito", "Contraseña actualizada para Juan Perez.", "info")

    def test_change_worker_password_denied_no_permission(self, manager, mock_view, mock_app):
        """Prueba que se deniega el cambio de contraseña si el usuario no tiene permisos."""
        # Cambiar rol del usuario
        mock_app.current_user = MagicMock(spec=["role"])
        mock_app.current_user.role = 'Trabajador'
        
        # Ejecutar (debería fallar el chequeo interno de rol antes de entrar al diálogo)
        manager._on_change_worker_password_clicked(10)
        
        # Verificar
        mock_view.show_message.assert_called_with("Acceso Denegado", ANY, "warning")
        
    def test_change_worker_password_mismatch(self, manager, mock_view, mock_service):
        """Prueba que el cambio falla si las contraseñas introducidas no coinciden."""
        # Configurar mocks
        worker_data = MagicMock(spec=WorkerDTO)
        worker_data.nombre_completo = 'Juan Perez'
        mock_service.get_worker_details.return_value = worker_data
        
        # Mock del diálogo con contraseñas que no coinciden
        with patch('controllers.worker.auth_manager.ChangePasswordDialog') as mock_dialog_class:
            mock_dialog = mock_dialog_class.return_value
            mock_dialog.exec.return_value = 1 # Accepted
            mock_dialog.get_passwords.return_value = {'new': 'Pass1', 'confirm': 'Pass2'}
            
            # Ejecutar
            manager._on_change_worker_password_clicked(10)
            
            # Verificar
            mock_view.show_message.assert_called_with("Error", "Las contraseñas no coinciden.", "warning")
