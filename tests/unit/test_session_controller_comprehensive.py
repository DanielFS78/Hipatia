# -*- coding: utf-8 -*-
"""
Tests comprensivos unitarios para SessionController.
Verifica autenticación, rate-limiting, actualización de UI por rol y lanzamiento de interfaz operario.
"""

from __future__ import annotations
import sys
import pytest
from typing import Dict, Any, cast
from dataclasses import asdict
from unittest.mock import MagicMock, patch, ANY, Mock, call, create_autospec

from PyQt6.QtWidgets import QDialog

from controllers.session_controller import SessionController
from core.services.worker_service import WorkerService
from core.security.security_service import Permission, SecurityService
from core.dtos import WorkerDTO, AuthResponseDTO


pytestmark = pytest.mark.unit


@pytest.mark.unit
class TestSessionControllerInit:
    """Tests para inicialización de SessionController."""

    def test_init_sets_attributes(self) -> None:
        """Verifica que __init__ asigna correctamente todos los atributos del controlador."""
        mock_app = MagicMock(spec=['model', 'view', 'security_service', 'ui_controller', 'tracking_repo', 'label_manager', 'qr_generator', 'label_counter_repo', 'hardware_controller'])
        mock_app.model = MagicMock(spec=['db', 'worker_service'])
        mock_app.model.db = Mock(spec=['SessionLocal'])
        mock_app.model.worker_service = create_autospec(WorkerService, instance=True)
        mock_app.view = MagicMock(spec=['show_message', 'switch_page', 'buttons'])
        mock_app.security_service = create_autospec(SecurityService, instance=True)
        
        with patch('controllers.session_controller.RateLimiter', autospec=True) as MockRL, \
             patch('controllers.session_controller.AuditLogger', autospec=True) as MockAL:
            ctrl = SessionController(mock_app)
        
        assert ctrl.app is mock_app
        assert ctrl.db is mock_app.model.db
        assert ctrl.worker_service is mock_app.model.worker_service
        assert ctrl.view is mock_app.view
        assert ctrl.security_service is mock_app.security_service
        assert ctrl.current_user is None
        assert ctrl.worker_window is None
        assert ctrl.worker_feature_controller is None
        assert ctrl.logger is not None
        assert MockRL.call_count == 1
        assert MockAL.call_count == 1


@pytest.mark.unit
class TestHandleLogin:
    """Tests para el método handle_login."""

    @pytest.fixture
    def controller(self) -> SessionController:
        """Construye un SessionController con todos los servicios de seguridad mockeados."""
        mock_app = MagicMock(spec=['view', 'model', 'security_service', 'ui_controller'])
        mock_app.view = MagicMock(spec=['show_message', 'switch_page', 'buttons'])
        mock_app.model = MagicMock(spec=['worker_service', 'db'])
        mock_app.model.db = MagicMock(spec=['SessionLocal'])
        mock_app.model.worker_service = create_autospec(WorkerService, instance=True)
        mock_app.security_service = create_autospec(SecurityService, instance=True)
        mock_app.ui_controller = MagicMock(spec=['load_quote_for_home'])

        with patch('controllers.session_controller.RateLimiter', autospec=True), \
             patch('controllers.session_controller.AuditLogger', autospec=True):
            ctrl = SessionController(mock_app)

        ctrl.rate_limiter = MagicMock(spec=['is_blocked', 'check_and_record_attempt'])
        ctrl.rate_limiter.is_blocked.return_value = False
        ctrl.audit_logger = MagicMock(spec=['log_login'])
        return ctrl

    @patch('ui.dialogs.LoginDialog', autospec=True)
    def test_login_success(self, MockLD: MagicMock, controller: SessionController) -> None:
        """Verifica flujo de login exitoso: datos de usuario retornados y UI actualizada."""
        inst = MockLD.return_value
        inst.exec.return_value = QDialog.DialogCode.Accepted
        inst.get_credentials.return_value = ('alice', 'secret')

        user = AuthResponseDTO(id=1, nombre_completo='Alice Smith', username='alice', role='Admin', activo=True)
        controller.worker_service.authenticate_user.return_value = user
        
        result = controller.handle_login()
        
        assert result == (user, True)
        assert controller.current_user == user
        assert controller.security_service is not None
        ss = cast(Any, controller.security_service)
        assert ss.login_user.call_count == 1
        ss.login_user.assert_called_once_with(user)
        assert controller.app.ui_controller is not None
        assert controller.app.ui_controller.load_quote_for_home.call_count == 1  # type: ignore[attr-defined]
        controller.app.ui_controller.load_quote_for_home.assert_called_once_with()  # type: ignore[attr-defined]
        assert controller.audit_logger.log_login.call_count >= 1  # type: ignore[attr-defined]
        controller.audit_logger.log_login.assert_called_with( # type: ignore[attr-defined]
            username='alice', success=True, user_id=1
        )

    @patch('ui.dialogs.LoginDialog', autospec=True)
    def test_login_cancelled(self, MockLD: MagicMock, controller: SessionController) -> None:
        """Test login when user closes dialog — returns None."""
        inst = MockLD.return_value
        inst.exec.return_value = QDialog.DialogCode.Rejected

        result = controller.handle_login()
        assert result is None
        assert controller.current_user is None

    @patch('ui.dialogs.LoginDialog', autospec=True)
    def test_login_wrong_credentials(self, MockLD: MagicMock, controller: SessionController) -> None:
        """Test login fails with wrong credentials — returns (None, False)."""
        inst = MockLD.return_value
        inst.exec.return_value = QDialog.DialogCode.Accepted
        inst.get_credentials.return_value = ('alice', 'wrong')
        controller.worker_service.authenticate_user.return_value = None

        result = controller.handle_login()
        
        assert result == (None, False)
        assert controller.current_user is None
        assert controller.audit_logger.log_login.call_count >= 1  # type: ignore[attr-defined]
        controller.audit_logger.log_login.assert_called_with( # type: ignore[attr-defined]
            username='alice', success=False, error_message='Credenciales incorrectas'
        )
        assert controller.rate_limiter.check_and_record_attempt.call_count >= 1  # type: ignore[attr-defined]
        controller.rate_limiter.check_and_record_attempt.assert_called_with('alice', success=False) # type: ignore[attr-defined]

    @patch('ui.dialogs.LoginDialog', autospec=True)
    def test_login_blocked_by_rate_limiter(self, MockLD: MagicMock, controller: SessionController) -> None:
        """Test login is blocked by rate limiter — covers lines 52-59."""
        inst = MockLD.return_value
        inst.exec.return_value = QDialog.DialogCode.Accepted
        inst.get_credentials.return_value = ('alice', 'secret')

        # Rate limiter blocks this user
        controller.rate_limiter.is_blocked.return_value = True # type: ignore[attr-defined]

        result = controller.handle_login()

        assert result == (None, False)
        assert controller.view.show_message.call_count == 1
        controller.view.show_message.assert_called_with(
            "Cuenta Bloqueada Temporalmente",
            "Demasiados intentos de login fallidos. Por favor, espere 5 minutos.",
            "warning"
        )
        assert controller.audit_logger.log_login.call_count == 1  # type: ignore[attr-defined]
        controller.audit_logger.log_login.assert_called_with( # type: ignore[attr-defined]
            'alice', success=False, error_message="Bloqueado por rate limiting"
        )
        # Must NOT attempt authentication
        assert controller.worker_service.authenticate_user.call_count == 0
        controller.worker_service.authenticate_user.assert_not_called()


@pytest.mark.unit
class TestLogout:
    """Tests for logout method."""

    @pytest.fixture
    def controller(self) -> SessionController:
        """Controller with a logged-in user."""
        mock_app = MagicMock(spec=['view', 'model', 'security_service', 'ui_controller', 'current_user'])
        mock_app.view = MagicMock(spec=['show_message', 'switch_page', 'buttons'])
        mock_app.model = MagicMock(spec=['db', 'worker_service'])
        mock_app.security_service = create_autospec(SecurityService, instance=True)

        with patch('controllers.session_controller.RateLimiter', autospec=True), \
             patch('controllers.session_controller.AuditLogger', autospec=True):
            ctrl = SessionController(mock_app)

        ctrl.rate_limiter = MagicMock(spec=['is_blocked', 'check_and_record_attempt'])
        ctrl.audit_logger = MagicMock(spec=['log_login'])
        ctrl.current_user = AuthResponseDTO(id=1, nombre_completo='Alice', username='alice', role='Admin', activo=True)
        return ctrl

    def test_logout_clears_user_and_calls_security(self, controller: SessionController) -> None:
        """Test logout clears user, calls security.logout, and disables buttons."""
        mock_buttons: Dict[str, MagicMock] = {
            'dashboard': MagicMock(spec=['setEnabled', 'isEnabled']),
            'reportes': MagicMock(spec=['setEnabled', 'isEnabled']),
            'historial': MagicMock(spec=['setEnabled', 'isEnabled']),
            'gestion_datos': MagicMock(spec=['setEnabled', 'isEnabled']),
            'add_product': MagicMock(spec=['setEnabled', 'isEnabled']),
            'settings': MagicMock(spec=['setEnabled', 'isEnabled'])
        }
        controller.view.buttons = mock_buttons

        controller.logout()

        assert controller.current_user is None
        assert controller.security_service is not None
        assert controller.security_service.logout.call_count == 1  # type: ignore[attr-defined]
        controller.security_service.logout.assert_called_once_with()  # type: ignore[attr-defined]
        assert controller.view.switch_page.call_count == 1
        controller.view.switch_page.assert_called_with("home")
        for btn in mock_buttons.values():
            assert btn.setEnabled.call_count == 1
            btn.setEnabled.assert_called_once_with(False)


@pytest.mark.unit
class TestUpdateUiForRole:
    """Tests for _update_ui_for_role method."""

    @pytest.fixture
    def controller(self) -> SessionController:
        """Controller fixture for role checking tests."""
        mock_app = MagicMock(spec=['view', 'model', 'security_service', 'ui_controller'])
        mock_app.view = MagicMock(spec=['show_message', 'switch_page', 'buttons'])
        mock_app.model = MagicMock(spec=['db', 'worker_service'])
        mock_app.security_service = create_autospec(SecurityService, instance=True)

        with patch('controllers.session_controller.RateLimiter', autospec=True), \
             patch('controllers.session_controller.AuditLogger', autospec=True):
            ctrl = SessionController(mock_app)

        ctrl.rate_limiter = MagicMock(spec=['is_blocked', 'check_and_record_attempt'])
        ctrl.audit_logger = MagicMock(spec=['log_login'])
        return ctrl

    def test_update_ui_no_user_returns_early(self, controller: SessionController) -> None:
        """Test _update_ui_for_role returns early if current_user is None (line 125)."""
        controller.current_user = None
        controller._update_ui_for_role()
        # Security service must NOT be called
        assert controller.security_service is not None
        assert controller.security_service.has_permission.call_count == 0  # type: ignore[attr-defined]
        controller.security_service.has_permission.assert_not_called() # type: ignore[attr-defined]

    def test_update_ui_admin_enables_all_buttons(self, controller: SessionController) -> None:
        """Test all buttons are enabled for admin role."""
        controller.current_user = AuthResponseDTO(id=1, nombre_completo='Admin', username='admin', role='Admin', activo=True)
        assert controller.security_service is not None
        controller.security_service.has_permission.return_value = True # type: ignore[attr-defined]

        controller._update_ui_for_role()

        buttons = controller.view.buttons
        for btn_name in ['dashboard', 'reportes', 'historial', 'gestion_datos', 'add_product', 'settings']:
            buttons[btn_name].setEnabled.assert_called_with(True)

    def test_update_ui_limited_role_redirects(self, controller: SessionController) -> None:
        """Test limited role is redirected to home with a message."""
        controller.current_user = AuthResponseDTO(id=2, nombre_completo='Operario', username='ope', role='Operario', activo=True)
        assert controller.security_service is not None
        controller.security_service.has_permission.return_value = False # type: ignore[attr-defined]

        controller._update_ui_for_role()

        controller.view.switch_page.assert_called_with("home")
        assert controller.view.show_message.call_count >= 1
        controller.view.show_message.assert_called_with(
            "Acceso Limitado",
            "Tu rol tiene acceso limitado a las funciones de gestión.",
            "info"
        )


@pytest.mark.unit
class TestLaunchWorkerInterface:
    """Tests for launch_worker_interface method."""

    @pytest.fixture
    def controller(self) -> SessionController:
        """Controller with a logged-in user ready for worker launch."""
        mock_app = MagicMock(spec=['view', 'model', 'security_service', 'ui_controller', 'tracking_repo', 'label_manager', 'qr_generator', 'label_counter_repo', 'hardware_controller'])
        mock_app.model = MagicMock(spec=['db', 'worker_service'])
        mock_app.model.db = MagicMock(spec=['SessionLocal'])
        mock_app.security_service = create_autospec(SecurityService, instance=True)
        mock_app.tracking_repo = MagicMock(spec=['add', 'get'])
        mock_app.label_manager = MagicMock(spec=['generate'])
        mock_app.qr_generator = MagicMock(spec=['generate'])
        mock_app.label_counter_repo = MagicMock(spec=['increment'])
        mock_app.hardware_controller = MagicMock(spec=['qr_scanner', 'initialize_qr_scanner'])

        with patch('controllers.session_controller.RateLimiter', autospec=True), \
             patch('controllers.session_controller.AuditLogger', autospec=True):
            ctrl = SessionController(mock_app)

        ctrl.rate_limiter = MagicMock(spec=['is_blocked', 'check_and_record_attempt'])
        ctrl.audit_logger = MagicMock(spec=['log_login'])
        ctrl.current_user = AuthResponseDTO(id=1, nombre_completo='Worker Joe', username='joe', role='Trabajador', activo=True)
        return ctrl

    @patch('ui.dialogs.LoginDialog', autospec=True)
    def test_launch_worker_interface_success(self, MockLD: MagicMock, controller: SessionController) -> None:
        """Test successful launch of worker interface (lines 188-248)."""
        mock_scanner = MagicMock(spec=['scan'])
        assert controller.app.hardware_controller is not None
        controller.app.hardware_controller.qr_scanner = mock_scanner

        MockWorkerController = MagicMock(spec=['initialize'])
        MockWorkerMainWindow = MagicMock(spec=['show'])

        with patch.dict('sys.modules', {
            'features.worker_controller': MagicMock(WorkerController=MockWorkerController),
            'ui.worker.main_window.window': MagicMock(WorkerMainWindow=MockWorkerMainWindow)
        }):
            controller.launch_worker_interface()

        if controller.current_user:
            MockWorkerMainWindow.assert_called_once_with(current_user=controller.current_user)
        assert MockWorkerController.call_count == 1
        MockWorkerController.assert_called_once_with(
            current_user=controller.current_user,
            db_manager=controller.app.model.db,
            main_window=MockWorkerMainWindow.return_value,
            qr_scanner=mock_scanner,
            tracking_repo=controller.app.tracking_repo,
            label_manager=controller.app.label_manager,
            qr_generator=controller.app.qr_generator,
            label_counter_repo=controller.app.label_counter_repo,
        )
        assert MockWorkerController.return_value.initialize.call_count == 1
        MockWorkerController.return_value.initialize.assert_called_once_with()
        assert MockWorkerMainWindow.return_value.show.call_count == 1
        MockWorkerMainWindow.return_value.show.assert_called_once_with()

    def test_launch_feature_import_error_fallback(self, controller: SessionController) -> None:
        """Test fallback path when features.worker_controller cannot be imported (lines 161-162, 210-211)."""
        mock_scanner = MagicMock(spec=['scan'])
        assert controller.app.hardware_controller is not None
        controller.app.hardware_controller.qr_scanner = mock_scanner

        MockWorkerMainWindow = MagicMock(spec=['show'])

        # Simulate ImportError for features.worker_controller
        import builtins
        real_import = builtins.__import__

        def import_side_effect(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == 'features.worker_controller':
                raise ImportError("module not found")
            return real_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=import_side_effect), \
             patch.dict('sys.modules', {'ui.worker.main_window.window': MagicMock(spec=['WorkerMainWindow'], WorkerMainWindow=MockWorkerMainWindow)}), \
             patch('controllers.session_controller.QMessageBox') as MockQMB:
            controller.launch_worker_interface()
            assert MockQMB.information.call_count == 1
            MockQMB.information.assert_called_once_with(ANY, ANY, ANY)

    def test_launch_no_scanner_logs_error(self, controller: SessionController) -> None:
        """Test that missing scanner triggers error log (line 179)."""
        assert controller.app.hardware_controller is not None
        controller.app.hardware_controller.qr_scanner = None
        controller.logger = MagicMock(spec=['error', 'info', 'warning'])  # Replace real logger with mock

        MockWorkerController = MagicMock(spec=['initialize'])
        MockWorkerMainWindow = MagicMock(spec=['show'])

        with patch.dict('sys.modules', {
            'features.worker_controller': MagicMock(spec=['WorkerController'], WorkerController=MockWorkerController),
            'ui.worker.main_window.window': MagicMock(spec=['WorkerMainWindow'], WorkerMainWindow=MockWorkerMainWindow)
        }):
            controller.launch_worker_interface()

        controller.logger.error.assert_called()

    def test_launch_no_user_raises_value_error(self, controller: SessionController) -> None:
        """Test launch with no user triggers ValueError (line 222: ValueError not causing sys.exit)."""
        controller.current_user = None

        with patch.dict('sys.modules', {
            'features.worker_controller': MagicMock(spec=[]),
            'ui.worker.main_window.window': MagicMock(spec=['WorkerMainWindow'])
        }), \
        patch('controllers.session_controller.QMessageBox') as MockQMB, \
        patch('sys.exit', autospec=True) as mock_exit:
            controller.launch_worker_interface()
            # ValueError should NOT call sys.exit
            assert mock_exit.call_count == 0
            mock_exit.assert_not_called()
            assert MockQMB.critical.call_count == 1
            MockQMB.critical.assert_called_once_with(ANY, ANY, ANY)

    def test_launch_generic_exception_calls_sys_exit(self, controller: SessionController) -> None:
        """Test that a non-ValueError exception causes sys.exit(1) — covers line 222."""
        controller.logger = MagicMock(spec=['critical', 'info', 'error'])

        # Make WorkerMainWindow raise a generic RuntimeError
        MockWorkerMainWindow = MagicMock(spec=['show'])
        MockWorkerMainWindow.side_effect = RuntimeError("unexpected crash")

        with patch.dict('sys.modules', {
            'features.worker_controller': MagicMock(spec=[]),
            'ui.worker.main_window.window': MagicMock(spec=['WorkerMainWindow'], WorkerMainWindow=MockWorkerMainWindow)
        }), \
        patch('controllers.session_controller.QMessageBox') as MockQMB, \
        patch('sys.exit', autospec=True) as mock_exit:
            controller.launch_worker_interface()
            assert mock_exit.call_count == 1
            mock_exit.assert_called_once_with(1)
            assert MockQMB.critical.call_count == 1
            MockQMB.critical.assert_called_once_with(ANY, ANY, ANY)

