# -*- coding: utf-8 -*-
"""
Tests for ConnectionDialog following the AAA pattern and strict testing guidelines.
"""
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog
from ui.dialogs.connection_dialog import ConnectionDialog

@pytest.fixture
def connection_dialog(qtbot):
    """Fixture providing an instance of ConnectionDialog."""
    dialog = ConnectionDialog()
    qtbot.addWidget(dialog)
    return dialog

@pytest.mark.unit
class TestConnectionDialog:
    """Tests for the ConnectionDialog logic and interactions."""

    def test_connection_dialog_initial_state(self, connection_dialog):
        # Arrange / Act - Dialog is initialized by the fixture
        
        # Assert
        assert connection_dialog.rb_local.isChecked() is True
        assert connection_dialog.rb_server.isChecked() is False
        assert connection_dialog.chk_remember.isChecked() is False
        assert connection_dialog.windowTitle() == "Modo de Conexión - Tiempos de Fabricación"

    def test_get_selection_default_returns_sqlite_false(self, connection_dialog):
        # Arrange - Initial state

        # Act
        mode, remember = connection_dialog.get_selection()

        # Assert
        assert mode == "sqlite"
        assert remember is False

    def test_get_selection_server_remember_returns_postgresql_true(self, connection_dialog):
        # Arrange
        connection_dialog.rb_server.setChecked(True)
        connection_dialog.chk_remember.setChecked(True)

        # Act
        mode, remember = connection_dialog.get_selection()

        # Assert
        assert mode == "postgresql"
        assert remember is True

    def test_get_selection_local_remember_returns_sqlite_true(self, connection_dialog):
        # Arrange
        connection_dialog.rb_local.setChecked(True)
        connection_dialog.chk_remember.setChecked(True)

        # Act
        mode, remember = connection_dialog.get_selection()

        # Assert
        assert mode == "sqlite"
        assert remember is True

    def test_connect_button_calls_accept(self, connection_dialog, qtbot):
        # Arrange
        
        # Act & Assert
        with qtbot.waitSignal(connection_dialog.accepted, timeout=1000):
            qtbot.mouseClick(connection_dialog.btn_connect, Qt.MouseButton.LeftButton)
            
        assert connection_dialog.result() == QDialog.DialogCode.Accepted
