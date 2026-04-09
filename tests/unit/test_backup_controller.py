# -*- coding: utf-8 -*-
"""Tests unitarios para BackupController — flujos básicos de backup/export/import."""
import os
import pytest
from unittest.mock import MagicMock, patch, create_autospec

from controllers.backup_controller import BackupController
from core.security.access_control import set_security_service
from core.security.security_service import SecurityService
from database.database_manager import DatabaseManager
from core.services.backup_service import BackupService
from ui.main_window import MainView


@pytest.fixture
def mock_db():
    """Mock estricto del gestor de base de datos."""
    db = create_autospec(DatabaseManager, instance=True)
    db.db_path = "/path/to/montaje.db"
    db.db_url = "sqlite:///path/to/montaje.db"
    return db


@pytest.fixture
def mock_view():
    """Mock estricto de la vista principal."""
    return create_autospec(MainView, instance=True)


@pytest.fixture
def mock_backup_service():
    """Mock estricto del servicio de backup."""
    return create_autospec(BackupService, instance=True)


@pytest.fixture
def mock_audit_logger():
    """Mock del audit logger."""
    return MagicMock(spec=["log", "log_export", "log_delete", "log_import", "log_backup", "log_restore"])


@pytest.fixture
def mock_logger():
    """Mock del logger de aplicación."""
    return MagicMock(spec=["debug", "info", "warning", "error", "exception"])


@pytest.fixture
def backup_controller(mock_db, mock_view, mock_logger, mock_backup_service, mock_audit_logger):
    """Instancia de BackupController con todas las dependencias mockeadas."""
    return BackupController(mock_db, mock_view, mock_logger, mock_backup_service, mock_audit_logger)


@pytest.mark.unit
class TestBackupController:
    """Tests unitarios para BackupController."""

    def test_create_backup_directory_structure_success(self, backup_controller):
        """Verifica que se crean los directorios de backup correctamente."""
        with patch('os.makedirs', autospec=True) as mock_makedirs, \
             patch('os.path.abspath', autospec=True, return_value="/app/dir/main.py"):

            db_dir, log_dir = backup_controller._create_backup_directory_structure()

            assert db_dir is not None
            assert log_dir is not None
            assert mock_makedirs.call_count >= 4

    def test_create_automatic_backup_success(self, backup_controller):
        """Verifica que el backup automático copia el archivo y registra en el log."""
        with patch.object(backup_controller, '_create_backup_directory_structure',
                          return_value=("/db/backup", "/log/backup")), \
             patch('os.path.exists', autospec=True, return_value=True), \
             patch('shutil.copy2', autospec=True) as mock_copy, \
             patch('builtins.open', create=True) as mock_open:

            mock_open.return_value.__enter__ = MagicMock(spec=[], return_value=MagicMock(spec=[]))
            mock_open.return_value.__exit__ = MagicMock(spec=[], return_value=False)

            backup_controller.create_automatic_backup()

            mock_copy.assert_called()
            backup_controller.logger.info.assert_called()

    def test_on_export_databases_cancel(self, backup_controller):
        """Verifica que cancelar el diálogo no exporta nada."""
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', return_value=("", "")):
            backup_controller.on_export_databases()
            backup_controller.view.show_message.assert_not_called()

    def test_on_import_databases_cancel(self, backup_controller):
        """Verifica que cancelar el diálogo no importa nada."""
        with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', return_value=("", "")):
            callback = MagicMock(spec=[])
            backup_controller.on_import_databases(on_success_callback=callback)
            callback.assert_not_called()

    def test_show_backup_restore_dialog(self, backup_controller):
        """Verifica que se muestra el diálogo de restauración con los args correctos."""
        with patch('ui.dialogs.backup_restore_dialog.BackupRestoreDialog') as MockDialog:
            mock_dialog_instance = MockDialog.return_value

            backup_controller.show_backup_restore_dialog()

            MockDialog.assert_called_once_with(
                backup_controller.backup_service,
                backup_controller.view,
                backup_controller.audit_logger,
            )
            assert mock_dialog_instance.exec.call_count == 1
            mock_dialog_instance.exec.assert_called_once_with()

    def test_on_export_databases_permission_denied_no_file_dialog(self, backup_controller):
        """Sin MANAGE_SETTINGS no se abre el diálogo de exportación (defensa en profundidad)."""
        mock_ss = MagicMock(spec=SecurityService)
        mock_ss.has_permission.return_value = False
        set_security_service(mock_ss)
        try:
            with patch(
                "controllers.backup_controller_io_manager.zipfile.ZipFile"
            ) as mock_zip, patch(
                "controllers.backup_controller.QFileDialog.getSaveFileName",
                return_value=("/tmp/x.zip", ""),
            ) as mock_save:
                backup_controller.on_export_databases()
                mock_save.assert_not_called()
                mock_zip.assert_not_called()
        finally:
            set_security_service(None)

    def test_show_backup_restore_dialog_permission_denied(self, backup_controller):
        """Sin permiso no se instancia el diálogo de backup/restore."""
        mock_ss = MagicMock(spec=SecurityService)
        mock_ss.has_permission.return_value = False
        set_security_service(mock_ss)
        try:
            with patch("ui.dialogs.backup_restore_dialog.BackupRestoreDialog") as MockDialog:
                backup_controller.show_backup_restore_dialog()
                MockDialog.assert_not_called()
        finally:
            set_security_service(None)
