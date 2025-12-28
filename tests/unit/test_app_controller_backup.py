"""
Tests unitarios para AppController - Backup y bases de datos.

Cobertura objetivo: Métodos de backup automático y gestión de bases de datos.
"""
import pytest
from unittest.mock import MagicMock, patch
import os

from controllers.app_controller import AppController


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_app():
    """Crea AppController con dependencias mockeadas."""
    model = MagicMock()
    model.db = MagicMock()
    model.db.db_path = "/tmp/test_db.sqlite"
    
    view = MagicMock()
    view.pages = {}
    view.show_message = MagicMock()
    
    config = MagicMock()
    
    with patch('controllers.app_controller.CameraManager'), \
         patch('controllers.app_controller.QrGenerator'), \
         patch('controllers.app_controller.LabelManager'), \
         patch('controllers.app_controller.LabelCounterRepository'):
        ctrl = AppController(model, view, config)
        return ctrl


# =============================================================================
# TESTS: create_automatic_backup
# =============================================================================

class TestCreateAutomaticBackup:
    """Tests para create_automatic_backup."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app.create_automatic_backup)

    def test_returns_false_on_dir_creation_failure(self, mock_app):
        """Verifica que retorna False si falla la creación de directorios."""
        with patch.object(mock_app, '_create_backup_directory_structure', return_value=(None, None)):
            result = mock_app.create_automatic_backup()
            assert result is False

    def test_returns_false_when_db_not_found(self, mock_app):
        """Verifica manejo cuando la BD no existe."""
        with patch.object(mock_app, '_create_backup_directory_structure', return_value=("/tmp/db", "/tmp/log")), \
             patch('os.path.exists', return_value=False), \
             patch.object(mock_app, '_backup_and_clean_log', return_value=True):
            
            result = mock_app.create_automatic_backup()
            assert result is False  # db_backup_success es False

    def test_successful_full_backup(self, mock_app):
        """Verifica backup completo exitoso."""
        with patch.object(mock_app, '_create_backup_directory_structure', return_value=("/tmp/db", "/tmp/log")), \
             patch('os.path.exists', return_value=True), \
             patch('shutil.copy2') as mock_copy, \
             patch.object(mock_app, '_backup_and_clean_log', return_value=True):
            
            result = mock_app.create_automatic_backup()
            
            mock_copy.assert_called_once()
            assert result is True

    def test_handles_critical_exception(self, mock_app):
        """Verifica manejo de excepciones críticas."""
        with patch.object(mock_app, '_create_backup_directory_structure', side_effect=Exception("Critical")):
            result = mock_app.create_automatic_backup()
            assert result is False


# =============================================================================
# TESTS: _create_backup_directory_structure
# =============================================================================

class TestCreateBackupDirectoryStructure:
    """Tests para _create_backup_directory_structure."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._create_backup_directory_structure)

    def test_creates_directories_successfully(self, mock_app):
        """Verifica creación exitosa de estructura."""
        with patch('os.makedirs') as mock_makedirs, \
             patch('os.path.dirname', return_value="/app"), \
             patch('os.path.abspath', return_value="/app/script.py"):
            
            db_dir, log_dir = mock_app._create_backup_directory_structure()
            
            assert db_dir is not None
            assert log_dir is not None
            assert mock_makedirs.call_count >= 4  # Al menos 4 carpetas

    def test_returns_none_on_error(self, mock_app):
        """Verifica que retorna None en caso de error."""
        with patch('os.makedirs', side_effect=PermissionError("No permission")):
            db_dir, log_dir = mock_app._create_backup_directory_structure()
            
            assert db_dir is None
            assert log_dir is None


# =============================================================================
# TESTS: _backup_and_clean_log
# =============================================================================

class TestBackupAndCleanLog:
    """Tests para _backup_and_clean_log."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._backup_and_clean_log)

    def test_returns_false_when_log_not_found(self, mock_app):
        """Verifica retorno False cuando no existe el log."""
        with patch('os.path.exists', return_value=False):
            result = mock_app._backup_and_clean_log("/tmp/backup")
            assert result is False

    def test_copies_and_cleans_log_successfully(self, mock_app):
        """Verifica copia y limpieza exitosa del log."""
        with patch('os.path.exists', return_value=True), \
             patch('shutil.copy2') as mock_copy, \
             patch('builtins.open', create=True) as mock_open:
            
            result = mock_app._backup_and_clean_log("/tmp/backup")
            
            mock_copy.assert_called_once()
            mock_open.assert_called()
            assert result is True

    def test_handles_exception(self, mock_app):
        """Verifica manejo de excepciones."""
        with patch('os.path.exists', return_value=True), \
             patch('shutil.copy2', side_effect=IOError("Copy failed")):
            
            result = mock_app._backup_and_clean_log("/tmp/backup")
            assert result is False


# =============================================================================
# TESTS: _on_import_databases
# =============================================================================

class TestOnImportDatabases:
    """Tests para _on_import_databases."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._on_import_databases)

    def test_cancels_on_dialog_cancel(self, mock_app):
        """Verifica cancelación en diálogo."""
        with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = ("", "")
            
            mock_app._on_import_databases()
            
            # No debería mostrar mensaje de éxito
            mock_app.view.show_message.assert_not_called()


# =============================================================================
# TESTS: _on_export_databases
# =============================================================================

class TestOnExportDatabases:
    """Tests para _on_export_databases."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._on_export_databases)

    def test_cancels_on_dialog_cancel(self, mock_app):
        """Verifica cancelación en diálogo."""
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
            mock_dialog.return_value = ("", "")
            
            mock_app._on_export_databases()
            
            mock_app.view.show_message.assert_not_called()


# =============================================================================
# TESTS: _on_sync_databases_clicked
# =============================================================================

class TestOnSyncDatabasesClicked:
    """Tests para _on_sync_databases_clicked."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._on_sync_databases_clicked)
