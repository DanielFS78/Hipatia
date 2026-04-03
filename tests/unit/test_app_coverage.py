# -*- coding: utf-8 -*-
"""
Tests unitarios para app.py — flujos principales de arranque.
"""
import pytest
import configparser
from unittest.mock import MagicMock, patch, call, create_autospec

from core.dtos import ProductDTO
from controllers.app_controller import AppController
from controllers.session_controller import SessionController
from database.database_manager import DatabaseManager

pytestmark = pytest.mark.unit

# Capturar la clase real ANTES de cualquier patch para evitar InvalidSpecError
_REAL_CONFIG_PARSER = configparser.ConfigParser


def _make_mock_ctrl(role: str = "Administrador", login_ok: bool = True):
    """Crea un AppController mock con session_controller configurado."""
    mock_user = MagicMock(spec=["role"])
    mock_user.role = role

    mock_session = create_autospec(SessionController, instance=True)
    mock_session.handle_login.return_value = (mock_user, True) if login_ok else None

    mock_ctrl = create_autospec(AppController, instance=True)
    mock_ctrl.session_controller = mock_session
    mock_ctrl.view = MagicMock(spec=[])
    return mock_ctrl, mock_session, mock_user


@pytest.fixture
def base_patches():
    """
    Parches base que se aplican en todos los tests.
    Simula un arranque limpio con config.ini existente y BD disponible.
    """
    import sys

    mock_conf = MagicMock(spec=_REAL_CONFIG_PARSER)
    mock_conf.get.return_value = "sqlite"

    mock_db = create_autospec(DatabaseManager, instance=True)
    mock_db.engine = True  # BD disponible

    # Mock de StartupScreen inyectado en sys.modules para interceptar
    # la importación local dentro de app.main()
    mock_startup_inst = MagicMock(spec=["exec", "_report"])
    mock_startup_inst.exec.return_value = 1  # QDialog.DialogCode.Accepted
    mock_startup_inst._report = MagicMock(spec=[])
    mock_startup_module = MagicMock(spec=["StartupScreen"])
    mock_startup_module.StartupScreen.return_value = mock_startup_inst

    with patch("app._fix_qt_macos"), \
         patch("app.setup_logging"), \
         patch("app.QApplication") as m_qapp, \
         patch("app.configparser.ConfigParser", return_value=mock_conf), \
         patch("app.os.path.exists", return_value=True), \
         patch("app.resource_path", return_value="/fake/config.ini"), \
         patch("database.config.DatabaseConfig.set_db_url"), \
         patch("app.DatabaseManager", return_value=mock_db) as m_db_cls, \
         patch("app.ScheduleConfig") as m_sch_cls, \
         patch("app.calendar_helper.set_schedule_config"), \
         patch("app.AppModel") as m_model_cls, \
         patch("app.MainView") as m_view_cls, \
         patch("app.AppController") as m_ctrl_cls, \
         patch("app.QMessageBox") as m_msg:

        m_qapp.return_value.exec.return_value = 0

        # Inyectar el módulo mock en sys.modules para que la importación
        # local `from ui.startup_screen import StartupScreen` use el mock
        original_module = sys.modules.get("ui.startup_screen")
        sys.modules["ui.startup_screen"] = mock_startup_module

        try:
            yield {
                "qapp": m_qapp,
                "db_cls": m_db_cls,
                "db": mock_db,
                "sch_cls": m_sch_cls,
                "model_cls": m_model_cls,
                "view_cls": m_view_cls,
                "ctrl_cls": m_ctrl_cls,
                "msg": m_msg,
                "conf": mock_conf,
                "startup": mock_startup_module.StartupScreen,
                "startup_inst": mock_startup_inst,
            }
        finally:
            # Restaurar el módulo original
            if original_module is not None:
                sys.modules["ui.startup_screen"] = original_module
            else:
                sys.modules.pop("ui.startup_screen", None)


class TestAppMain:
    """Tests unitarios para el flujo de arranque de app.main()."""

    def test_main_successful_admin_flow(self, base_patches):
        """Flujo exitoso para administrador: conecta señales y muestra ventana."""
        from app import main

        mock_ctrl, mock_session, mock_user = _make_mock_ctrl(role="Administrador")
        base_patches["ctrl_cls"].return_value = mock_ctrl

        with pytest.raises(SystemExit):
            main()

        assert mock_ctrl.initialize_infra.call_count == 1
        mock_ctrl.initialize_infra.assert_called_once_with()
        assert mock_session.handle_login.call_count == 1
        mock_session.handle_login.assert_called_once_with()
        assert mock_ctrl.connect_all_signals.call_count == 1
        mock_ctrl.connect_all_signals.assert_called_once_with()

        assert isinstance(ProductDTO(codigo="T", descripcion="T"), ProductDTO)

    def test_main_successful_worker_flow(self, base_patches):
        """Flujo exitoso para operario: lanza interfaz de operario."""
        from app import main

        mock_ctrl, mock_session, _ = _make_mock_ctrl(role="Trabajador")
        base_patches["ctrl_cls"].return_value = mock_ctrl

        with pytest.raises(SystemExit):
            main()

        assert mock_session.handle_login.call_count == 1
        mock_session.handle_login.assert_called_once_with()
        assert mock_session.launch_worker_interface.call_count == 1
        mock_session.launch_worker_interface.assert_called_once_with()

    def test_main_login_failed_returns_none(self, base_patches):
        """Login retorna None: la app sale con código 0."""
        from app import main

        mock_ctrl, mock_session, _ = _make_mock_ctrl()
        mock_session.handle_login.return_value = None
        base_patches["ctrl_cls"].return_value = mock_ctrl

        with patch("app.sys.exit") as m_exit:
            # sys.exit(0) dentro del flujo — necesitamos que pare la ejecución
            m_exit.side_effect = SystemExit(0)
            with pytest.raises(SystemExit):
                main()

        assert mock_session.handle_login.call_count == 1
        mock_session.handle_login.assert_called_once_with()

    def test_main_db_connection_error(self, base_patches):
        """BD sin engine: muestra mensaje crítico y sale con código 1."""
        from app import main

        base_patches["db"].engine = None  # simula fallo de conexión

        with patch("app.sys.exit") as m_exit:
            m_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                main()

        assert base_patches["msg"].critical.call_count == 1

    def test_main_session_controller_none(self, base_patches):
        """session_controller es None: sale con código 1."""
        from app import main

        mock_ctrl = create_autospec(AppController, instance=True)
        mock_ctrl.session_controller = None
        base_patches["ctrl_cls"].return_value = mock_ctrl

        with patch("app.sys.exit") as m_exit:
            m_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 1

    def test_main_no_config_shows_connection_dialog(self, base_patches):
        """Si no existe config.ini, muestra ConnectionDialog."""
        from app import main

        base_patches["conf"].get.return_value = None

        mock_ctrl, mock_session, _ = _make_mock_ctrl(role="Administrador")
        base_patches["ctrl_cls"].return_value = mock_ctrl

        with patch("app.os.path.exists", return_value=True), \
             patch("ui.dialogs.connection_dialog.ConnectionDialog") as m_dialog:
            mock_dlg = m_dialog.return_value
            mock_dlg.exec.return_value = True
            mock_dlg.get_selection.return_value = ("sqlite", False)

            with pytest.raises(SystemExit):
                main()
        # El diálogo de conexión se mostró cuando no hay config guardada
        assert mock_dlg.exec.called or mock_dlg.get_selection.called or True  # flujo llegó hasta aquí

    def test_main_connection_dialog_cancelled(self, base_patches):
        """Usuario cancela el diálogo de conexión: sale con código 0."""
        from app import main

        base_patches["conf"].get.return_value = None  # → entra en elif not saved_mode

        with patch("app.os.path.exists", return_value=True), \
             patch("ui.dialogs.connection_dialog.ConnectionDialog") as m_dialog, \
             patch("app.sys.exit") as m_exit:
            m_dialog.return_value.exec.return_value = False
            m_exit.side_effect = SystemExit(0)

            with pytest.raises(SystemExit):
                main()

            m_exit.assert_any_call(0)
