# -*- coding: utf-8 -*-
"""Tests E2E de flujos de MainWindow.

Cubre navegación (home, dashboard, definir_lote) y enlace view/controller.
Widgets principales parcheados para evitar dependencias pesadas; se prueba
orquestación y cambio de página.
"""
import pytest
from PyQt6.QtCore import Qt
from unittest.mock import patch, MagicMock
from typing import Any, cast
from ui.main_window import MainView
from controllers.app_controller import AppController
from core.app_model import AppModel
from core.schedule_config import ScheduleConfig

pytestmark = pytest.mark.e2e


# @pytest.mark.skip(reason="MainView.__init__ hace super().__init__() -> Qt crea ventana nativa -> SIGABRT. Verificar manualmente en entorno con display o en CI con Xvfb.")
class TestMainWindowFlows:
    
    @pytest.fixture
    def app_stack(self, qapp, qtbot, in_memory_db_manager
):

        """
        Sets up the full application stack with in-memory DB and Mocked Widgets.
        This allows testing the interaction between View, Controller, and Model.
        """
        model = AppModel(in_memory_db_manager)
        schedule_manager = ScheduleConfig(in_memory_db_manager)
# Patch all widgets to ensure we don't depend on their internal complex logic/imports
        # We only want to test the MainView orchestration and navigation flow.
        # MainView is now in ui/main_window.py and imports widgets from ui.widgets
        with patch('ui.main_window.HomeWidget') as MockHome, \
             patch('ui.main_window.DashboardWidget') as MockDashboard, \
             patch('ui.main_window.DefinirLoteWidget') as MockDefinirLote, \
             patch('ui.main_window.CalculateTimesWidget') as MockCalculate, \
             patch('ui.main_window.PreprocesosWidget') as MockPreprocesos, \
             patch('ui.main_window.GestionDatosWidget') as MockGestionDatos, \
             patch('ui.main_window.ReportesWidget') as MockReportes, \
             patch('ui.main_window.HistorialWidget') as MockHistorial, \
             patch('ui.main_window.SettingsWidget') as MockSettings, \
             patch('ui.main_window.HelpWidget') as MockHelp:
             
            # Configure mocks to return valid QWidgets if needed, or just standard mocks
            # MainView adds them to QStackedWidget so they should be widget-like or QWidgets.
            # Using MagicMock usually works if QStackedWidget doesn't do strict type check in Python
            # But safer to return QWidget
            from PyQt6.QtWidgets import QWidget
            mock_widget_factory = lambda *args, **kwargs: QWidget()
            # Patch QApplication to avoid conflicts
            # REMOVED: patcher = patch('ui.main_window.QApplication'
            # The real QApplication (managed by pytest-qt
            # is already running and should be used.



            
            # Specific Mock for GestionDatosWidget to satisfy Controller dependencies
            class MockGestionDatosWidget(QWidget):
                def __init__(self):
                    super().__init__()
                    self.productos_tab = MagicMock(spec=[])
                    self.fabricaciones_tab = MagicMock(spec=[])
                    self.maquinas_tab = MagicMock(spec=[])
                    self.trabajadores_tab = MagicMock(spec=[])
                    self.preprocesos_tab = MagicMock(spec=[])
                    self.lotes_tab = MagicMock(spec=[])
            MockHome.side_effect = mock_widget_factory
            MockDashboard.side_effect = mock_widget_factory
            MockDefinirLote.side_effect = mock_widget_factory
            MockCalculate.side_effect = mock_widget_factory
            MockGestionDatos.side_effect = lambda *args, **kwargs: MockGestionDatosWidget()
            MockPreprocesos.side_effect = mock_widget_factory
            MockReportes.side_effect = mock_widget_factory
            MockHistorial.side_effect = mock_widget_factory
            MockSettings.side_effect = mock_widget_factory
            MockHelp.side_effect = mock_widget_factory
            
            # Instantiate View
            view = MainView()
            cast(Any, view).show_confirmation_dialog = MagicMock(return_value=True)
            # Prevent blocking

            # Instantiate Controller (Real one!)
            # AppController expects (model, view, schedule_manager)
            controller = AppController(model, view, schedule_manager)
            
            # Explicitly initialize infra (since we removed it from __init__)
            controller.initialize_infra()
            
            # Connect them
            view.controller = controller
            view.init_ui()
            view.set_controller(controller)
            controller.connect_all_signals()
            qtbot.addWidget(view)
            yield view, controller


    def test_navigation_updates_view_and_controller(self, app_stack, qtbot):

        """
        Verify that clicking navigation buttons updates both the View state 
        and triggers Controller actions (though controller might just set view
.
        """
        view, controller = app_stack
        
        # Initial state
        assert view.current_page_name == 'home'
        
        # 1. Navigate to Dashboard
        btn = view.buttons['dashboard']
        qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
        assert view.current_page_name == 'dashboard'
        assert view.stacked_widget.currentWidget() == view.pages['dashboard']
        
        # 2. Navigate to Planificacion (via menu logic check
# Note: Planificacion is a menu, we can't click it directly to change page without menu interaction.
        # But we can simulate clicking the sub-actions if we had access to them or use switch_page directly 
        # to verify button state updates.
        
        # Let's use the public method to switch to 'definir_lote' simulating the menu action
        view.switch_page('definir_lote')
        assert view.current_page_name == 'definir_lote'
        assert view.stacked_widget.currentWidget() == view.pages['definir_lote']
    def test_controller_delegation_sanity(self, app_stack):
        """
        Verify that the real controller is correctly linked and delegates signals/actions.
        """
        view, controller = app_stack
        
        # Verify controller methods are accessible via view (common pattern in this app)
        assert view.controller == controller
        
        # If we had a method in controller that updates the view, we could test it.
        # For example, update_machines_view which was mentioned in Phase 3.4 revision.
        # But that updates a specific widget (MachinesWidget).
        # Since we mocked GestionDatosWidget (which contains MachinesWidget), 
        # we can check if the controller TRIES to access it.
        
        # But update_machines_view is likely called when navigating to gestion_datos
        assert controller is not None and view.controller is controller
