# -*- coding: utf-8 -*-
"""
Tests unitarios para FileController (controllers.file_controller).

Verifica handle_attach_file, handle_view_file, on_import_task_data y on_data_after_import.
Patrón AAA; mocks con spec para DatabaseManager, vista y logger.
"""
import os
import json
import logging
import pytest
from unittest.mock import MagicMock, patch, mock_open, create_autospec, ANY
from PyQt6.QtCore import QUrl
from controllers.file_controller import FileController
from database.database_manager import DatabaseManager

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_db_manager():
    """Mock del DatabaseManager con repositorios configurados."""
    db = MagicMock(spec=['tracking_repo'])
    db.tracking_repo = MagicMock(spec=['upsert_trabajo_log_from_dict'])
    return db

@pytest.fixture
def mock_view():
    """Mock de la vista."""
    view = MagicMock(spec=['show_message', 'show_confirmation_dialog'])
    return view

@pytest.fixture
def mock_logger():
    """Mock del logger."""
    return create_autospec(logging.Logger, instance=True)

@pytest.fixture
def file_controller(mock_db_manager, mock_view, mock_logger):
    """Fixture providing a FileController instance."""
    controller = FileController(mock_db_manager, mock_view, mock_logger)
    return controller


@pytest.mark.unit
class TestFileControllerAttachFile:
    """Tests para el método handle_attach_file."""

    @patch("controllers.file_controller.os.makedirs", autospec=True)
    @patch("controllers.file_controller.shutil.copy", autospec=True)
    def test_handle_attach_file_success(self, mock_copy, mock_makedirs, file_controller):
        """Verifica adjuntar archivo exitosamente."""
        # Arrange
        owner_type = "producto"
        owner_id = 123
        source_file = "/tmp/some_image.jpg"
        file_type = "imagen"
        
        # We connect a mock slot to the signal to check if it's emitted
        mock_slot = MagicMock(spec=[])
        file_controller.file_attached.connect(mock_slot)
        
        # Act
        result = file_controller.handle_attach_file(owner_type, owner_id, source_file, file_type)
        
        # Assert
        assert result.success is True
        assert "producto_123.jpg" in result.path_or_error
        assert "imagens" in result.path_or_error
        
        # Verify makedirs was called twice (once for base dir, once for target dir)
        assert mock_makedirs.call_count == 2
        
        # Verify copy was called
        assert mock_copy.call_count == 1
        mock_copy.assert_called_once_with(source_file, result.path_or_error)
        
        # Verify signal emitted
        assert mock_slot.call_count == 1
        mock_slot.assert_called_once_with(result.path_or_error)

    @patch("controllers.file_controller.os.makedirs", autospec=True)
    def test_handle_attach_file_exception(self, mock_makedirs, file_controller):
        """Verifica manejo de excepciones al adjuntar archivo."""
        # Arrange
        mock_makedirs.side_effect = PermissionError("Access denied")
        
        # Act
        result = file_controller.handle_attach_file("test", 1, "path.jpg", "img")
        
        # Assert
        assert result.success is False
        assert "Access denied" in result.path_or_error
        assert file_controller.logger.error.call_count == 1
        assert "Access denied" in (file_controller.logger.error.call_args[0][0] or "")


@pytest.mark.unit
class TestFileControllerViewFile:
    """Tests para el método handle_view_file."""

    def test_handle_view_file_empty_path(self, file_controller):
        """Verifica manejo de ruta vacía."""
        # Arrange
        empty_path = ""
        
        # Act
        file_controller.handle_view_file(empty_path)
        
        # Assert
        assert file_controller.logger.warning.call_count == 1
        assert "visualizar" in (file_controller.logger.warning.call_args[0][0] or "")

    @patch("controllers.file_controller.os.path.exists", autospec=True)
    @patch("controllers.file_controller.os.path.abspath", autospec=True)
    def test_handle_view_file_not_found(self, mock_abspath, mock_exists, file_controller, mock_view):
        """Verifica manejo de archivo no encontrado."""
        # Arrange
        mock_abspath.return_value = "/absolute/missing.pdf"
        mock_exists.return_value = False
        
        # Act
        file_controller.handle_view_file("missing.pdf")
        
        # Assert
        assert file_controller.logger.error.call_count == 1
        assert "/absolute/missing.pdf" in (file_controller.logger.error.call_args[0][0] or "")
        assert mock_view.show_message.call_count == 1
        assert "archivo" in (mock_view.show_message.call_args[0][1] or "").lower()
        assert "Archivo No Encontrado" in mock_view.show_message.call_args[0][0]

    @patch("controllers.file_controller.os.path.exists", autospec=True)
    @patch("controllers.file_controller.os.path.abspath", autospec=True)
    @patch("controllers.file_controller.QDesktopServices.openUrl")
    @patch("controllers.file_controller.QUrl.fromLocalFile")
    def test_handle_view_file_success(self, mock_from_local, mock_open_url, mock_abspath, mock_exists, file_controller):
        """Verifica visualización exitosa de archivo."""
        # Arrange
        mock_abspath.return_value = "/absolute/existing.pdf"
        mock_exists.return_value = True
        mock_url = MagicMock(spec=QUrl)
        mock_from_local.return_value = mock_url
        
        # Act
        file_controller.handle_view_file("existing.pdf")
        
        # Assert
        assert mock_from_local.call_count == 1
        mock_from_local.assert_called_once_with("/absolute/existing.pdf")
        assert mock_open_url.call_count == 1
        mock_open_url.assert_called_once_with(mock_url)
        assert file_controller.logger.info.call_count == 1
        assert "/absolute/existing.pdf" in (file_controller.logger.info.call_args[0][0] or "")

    @patch("controllers.file_controller.os.path.exists", autospec=True)
    @patch("controllers.file_controller.os.path.abspath", autospec=True)
    @patch("controllers.file_controller.QDesktopServices.openUrl")
    def test_handle_view_file_exception(self, mock_open_url, mock_abspath, mock_exists, file_controller, mock_view):
        """Verifica manejo de excepciones al visualizar archivo."""
        # Arrange
        mock_abspath.return_value = "/absolute/existing.pdf"
        mock_exists.return_value = True
        mock_open_url.side_effect = Exception("System error")
        
        # Act
        file_controller.handle_view_file("existing.pdf")
        
        # Assert
        assert file_controller.logger.error.call_count == 1
        assert "System error" in (file_controller.logger.error.call_args[0][0] or "")
        assert mock_view.show_message.call_count == 1
        assert "Error" in (mock_view.show_message.call_args[0][0] or "")
        assert "Error" in mock_view.show_message.call_args[0][0]


@pytest.mark.unit
class TestFileControllerImportTaskData:
    """Tests para el método on_import_task_data."""

    @patch("controllers.file_controller.QFileDialog.getOpenFileName")
    def test_import_cancelled_by_user(self, mock_file_dialog, file_controller):
        """Verifica cancelación de importación por usuario."""
        # Arrange
        mock_file_dialog.return_value = ("", "")
        
        # Act
        file_controller.on_import_task_data()
        
        # Assert
        assert file_controller.logger.info.call_count >= 1
        calls = [args[0][0] for args in file_controller.logger.info.call_args_list]
        assert any("cancelada" in call for call in calls)

    @patch("controllers.file_controller.QFileDialog.getOpenFileName")
    @patch("builtins.open", new_callable=mock_open, read_data='{"not": "a list"}')
    def test_import_invalid_json_structure(self, mock_file, mock_file_dialog, file_controller, mock_view):
        """Verifica manejo de estructura JSON inválida."""
        # Arrange
        mock_file_dialog.return_value = ("/fake/path.json", "Archivos JSON (*.json)")
        
        # Act
        file_controller.on_import_task_data()
        
        # Assert
        assert file_controller.logger.error.call_count == 1
        assert "crítico" in (file_controller.logger.error.call_args[0][0] or "").lower()
        assert mock_view.show_message.call_count == 1
        assert mock_view.show_message.call_count == 1
        assert "Error Crítico" in mock_view.show_message.call_args[0][0]
        assert "no contiene una lista" in mock_view.show_message.call_args[0][1]

    @patch("controllers.file_controller.QFileDialog.getOpenFileName")
    @patch("builtins.open", new_callable=mock_open, read_data='[{"id": 1}]')
    def test_import_confirmation_cancelled(self, mock_file, mock_file_dialog, file_controller, mock_view):
        """Verifica cancelación de confirmación de importación."""
        # Arrange
        mock_file_dialog.return_value = ("/fake/path.json", "Archivos JSON (*.json)")
        mock_view.show_confirmation_dialog.return_value = False
        
        # Act
        file_controller.on_import_task_data()
        
        # Assert
        assert mock_view.show_confirmation_dialog.call_count == 1
        assert mock_view.show_confirmation_dialog.call_count == 1
        assert file_controller.db.tracking_repo.upsert_trabajo_log_from_dict.call_count == 0
        file_controller.db.tracking_repo.upsert_trabajo_log_from_dict.assert_not_called()

    @patch("controllers.file_controller.QFileDialog.getOpenFileName")
    @patch("builtins.open", new_callable=mock_open, read_data='[{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}]')
    def test_import_success_with_stats(self, mock_file, mock_file_dialog, file_controller, mock_view, mock_db_manager):
        """Verifica importación exitosa con estadísticas."""
        # Arrange
        mock_file_dialog.return_value = ("/fake/path.json", "Archivos JSON (*.json)")
        mock_view.show_confirmation_dialog.return_value = True
        
        # Mock responses from upsert to simulate different stats updates
        mock_db_manager.tracking_repo.upsert_trabajo_log_from_dict.side_effect = [
            ("created", None),
            ("updated", None),
            ("skipped", None),
            ("error", None),
            ("unknown", None) # testing fallback branch where status not in stats
        ]
        
        mock_slot = MagicMock(spec=[])
        file_controller.import_completed.connect(mock_slot)
        
        # Act
        file_controller.on_import_task_data()
        
        # Assert
        assert mock_db_manager.tracking_repo.upsert_trabajo_log_from_dict.call_count == 5
        assert mock_view.show_message.call_count == 1
        args = mock_view.show_message.call_args[0]
        assert args[0] == "Importación Completa"
        assert args[-1] == "info"
        
        message_text = args[1]
        assert "Nuevos: 1" in message_text
        assert "Actualizados: 1" in message_text
        assert "Omitidos: 1" in message_text
        assert "Errores: 1" in message_text
        
        assert mock_slot.call_count == 1
        assert mock_slot.call_count == 1

    @patch("controllers.file_controller.QFileDialog.getOpenFileName")
    @patch("builtins.open", new_callable=mock_open, read_data='{invalid_json')
    def test_import_json_decode_error(self, mock_file, mock_file_dialog, file_controller, mock_view):
        """Verifica manejo de error de decodificación JSON."""
        # Arrange
        mock_file_dialog.return_value = ("/fake/path.json", "Archivos JSON (*.json)")
        
        # Act
        file_controller.on_import_task_data()
        
        # Assert
        assert file_controller.logger.error.call_count == 1
        assert "json" in (file_controller.logger.error.call_args[0][0] or "").lower()
        assert mock_view.show_message.call_count == 1
        assert mock_view.show_message.call_count == 1
        assert "Error de Archivo" in mock_view.show_message.call_args[0][0]


@pytest.mark.unit
class TestFileControllerDataAfterImport:
    """Tests para el método on_data_after_import."""

    def test_on_data_after_import_emits_signal(self, file_controller):
        """Verifica emisión de señal después de importación."""
        # Arrange
        mock_slot = MagicMock(spec=[])
        file_controller.import_completed.connect(mock_slot)
        
        # Act
        file_controller.on_data_after_import()
        
        # Assert
        assert file_controller.logger.info.call_count == 1
        assert "importación" in (file_controller.logger.info.call_args[0][0] or "").lower()
        assert mock_slot.call_count == 1
        assert mock_slot.call_count == 1
