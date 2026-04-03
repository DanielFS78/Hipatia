# -*- coding: utf-8 -*-
import pytest
from PyQt6.QtWidgets import QApplication, QWidget, QStackedWidget, QMessageBox, QFrame, QPushButton, QMenu
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from unittest.mock import MagicMock, patch, create_autospec, call
import logging
import os

from ui.main_window import MainView, resource_path
from ui.widgets.calculate_times_widget import CalculateTimesWidget
from controllers.app_controller import AppController
from controllers.backup_controller import BackupController

pytestmark = pytest.mark.unit

class MockWidget(QWidget):
    def __init__(self, controller=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = controller
        class Tab:
            def __init__(self): self.controller = None
            def set_controller(self, c): self.controller = c
        self.productos_tab = Tab()
        self.fabricaciones_tab = Tab()
        self.maquinas_tab = Tab()
        self.trabajadores_tab = Tab()

    def set_controller(self, c):
        self.controller = c

@pytest.fixture(autouse=True)
def mock_widgets(monkeypatch):
    widgets_to_mock = [
        "HomeWidget", "DashboardWidget", "DefinirLoteWidget", "CalculateTimesWidget",
        "PreprocesosWidget", "GestionDatosWidget", "ReportesWidget",
        "HistorialWidget", "SettingsWidget", "HelpWidget"
    ]
    for w in widgets_to_mock:
        monkeypatch.setattr(f"ui.main_window.{w}", MockWidget)

@pytest.fixture
def mock_controller():
    controller = create_autospec(AppController, instance=True)
    controller.backup_controller = create_autospec(BackupController, instance=True)
    return controller

@pytest.fixture
def main_view(qtbot):
    view = MainView()
    qtbot.addWidget(view)
    return view

def test_resource_path():
    path = resource_path("test.txt")
    assert "test.txt" in path

def test_init_ui(main_view):
    main_view.init_ui()
    assert "home" in main_view.pages
    assert main_view.current_page_name == "home"
    assert hasattr(main_view, 'header')
    assert hasattr(main_view, 'nav_panel')

def test_init_ui_with_exception_fallback(main_view, monkeypatch):
    def raise_err(*args, **kwargs): raise ValueError("Fail")
    monkeypatch.setattr("ui.main_window.DashboardWidget", raise_err)
    main_view.init_ui()
    assert "dashboard" in main_view.pages

def test_set_controller(main_view, mock_controller):
    main_view.init_ui()
    main_view.set_controller(mock_controller)
    assert main_view.controller == mock_controller
    assert main_view.get_page("calculate").controller == mock_controller

def test_switch_page(main_view):
    main_view.init_ui()
    main_view.switch_page("dashboard")
    assert main_view.current_page_name == "dashboard"

def test_nav_requested(main_view, mock_controller):
    main_view.init_ui()
    main_view.controller = mock_controller
    main_view._on_nav_requested("add_product")
    mock_controller.on_nav_button_clicked.assert_called_once_with("add_product")

def test_nav_requested_no_controller(main_view):
    main_view.init_ui()
    main_view.controller = None
    main_view._on_nav_requested("settings")
    assert main_view.current_page_name == "settings"

def test_getters(main_view):
    main_view.init_ui()
    assert main_view.get_page("home") is not None
    assert main_view.get_products_tab() is not None
    assert main_view.get_fabrications_tab() is not None

def test_getters_empty(main_view):
    main_view._pages = {}
    assert main_view.get_products_tab() is None

def test_show_message(main_view):
    with patch('ui.main_window.QMessageBox') as mock_class:
        mock_class.StandardButton = QMessageBox.StandardButton
        main_view.show_message("T", "M", "info")
        mock_class.information.assert_called_once_with(main_view, "T", "M")
        
        main_view.show_message("T", "M", "warning")
        mock_class.warning.assert_called_once_with(main_view, "T", "M")
        
        main_view.show_message("T", "M", "critical")
        mock_class.critical.assert_called_once_with(main_view, "T", "M")
        
        main_view.show_message("T", "M", "unknown")
        mock_class.information.assert_called_with(main_view, "T", "M")

def test_show_confirmation_dialog(main_view):
    with patch('ui.main_window.QMessageBox') as mock_class:
        mock_class.StandardButton = QMessageBox.StandardButton
        mock_class.question.return_value = QMessageBox.StandardButton.Yes
        assert main_view.show_confirmation_dialog("T", "M") is True
        mock_class.question.assert_called_once_with(
            main_view, "T", "M",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

def test_display_simulation_results(main_view):
    main_view.init_ui()
    mock_calc = create_autospec(CalculateTimesWidget, instance=True)
    main_view._pages["calculate"] = mock_calc
    main_view.display_simulation_results("R", "A")
    mock_calc.display_simulation_results.assert_called_once_with("R", "A")

def test_run_simulation_and_display(main_view):
    main_view.init_ui()
    with patch.object(main_view, 'display_simulation_results', autospec=True) as mock_display:
        main_view.run_simulation_and_display("R", "A", 1, None)
        mock_display.assert_called_once_with("R", "A")

def test_close_event(main_view, mock_controller, monkeypatch):
    main_view.init_ui()
    main_view.controller = mock_controller
    mock_conf = MagicMock(spec=[]) # Still simple but specced
    mock_conf.return_value = True
    monkeypatch.setattr(main_view, "show_confirmation_dialog", mock_conf)
    event = create_autospec(QCloseEvent, instance=True)
    
    main_view.closeEvent(event)
    
    mock_conf.assert_called_once_with("Cerrar Aplicación", "¿Desea cerrar y realizar backup?")
    mock_controller.backup_controller.create_automatic_backup.assert_called_once_with()
    event.accept.assert_called_once_with()

def test_close_event_rejected(main_view, monkeypatch):
    main_view.init_ui()
    mock_conf = MagicMock(spec=[])
    mock_conf.return_value = False
    monkeypatch.setattr(main_view, "show_confirmation_dialog", mock_conf)
    event = create_autospec(QCloseEvent, instance=True)
    
    main_view.closeEvent(event)
    
    mock_conf.assert_called_once_with("Cerrar Aplicación", "¿Desea cerrar y realizar backup?")
    event.ignore.assert_called_once_with()

def test_close_event_backup_error(main_view, mock_controller, monkeypatch):
    main_view.init_ui()
    main_view.controller = mock_controller
    mock_controller.backup_controller.create_automatic_backup.side_effect = Exception("err")
    mock_conf = MagicMock(spec=[])
    mock_conf.return_value = True
    monkeypatch.setattr(main_view, "show_confirmation_dialog", mock_conf)
    event = create_autospec(QCloseEvent, instance=True)
    
    main_view.closeEvent(event)
    
    mock_conf.assert_called_once_with("Cerrar Aplicación", "¿Desea cerrar y realizar backup?")
    mock_controller.backup_controller.create_automatic_backup.assert_called_once_with()
    event.accept.assert_called_once_with()

@patch('core.utils.ui_scaler.UIScaler', autospec=True)
@patch('PyQt6.QtWidgets.QApplication.instance', autospec=True)
def test_forzar_auto_ajuste(mock_app, mock_scaler, main_view):
    main_view.init_ui()
    mock_scaler.get_current_screen_height.return_value = 800
    mock_scaler.calculate_scale_factor.return_value = 1.0
    mock_scaler.generate_dynamic_qss.return_value = "BODY { color: red; }"
    mock_instance = create_autospec(QApplication, instance=True)
    mock_app.return_value = mock_instance
    
    # Simular la señal de ajuste automático
    main_view.header.auto_adjust_requested.emit()
    
    mock_scaler.get_current_screen_height.assert_called_with(main_view)
    mock_scaler.calculate_scale_factor.assert_called_with(800)
    mock_scaler.generate_dynamic_qss.assert_called_with(1.0)
    mock_instance.setStyleSheet.assert_called_with("BODY { color: red; }")

def test_assign_controller_to_gestion_tabs_error(main_view, mock_controller):
    main_view.init_ui()
    class Broken:
        def __getattr__(self, n): raise ValueError("err")
    main_view._pages["gestion_datos"] = Broken()
    # Verificamos que no explota (manejo interno de excepción)
    with patch('ui.main_window.logging.warning') as mock_log:
        main_view.set_controller(mock_controller)
        assert mock_log.called
