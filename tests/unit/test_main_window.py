import pytest
from PyQt6.QtWidgets import QWidget, QPushButton
from PyQt6.QtCore import Qt, QTimer
from unittest.mock import MagicMock, patch
from ui.main_window import MainView

class TestMainView:
    
    @pytest.fixture
    def mock_controller(self):
        controller = MagicMock()
        controller.model = MagicMock()
        return controller

    @pytest.fixture
    def main_view(self, qtbot, mock_controller):
        """
        Fixture for MainView with mocked child widgets to isolate View testing.
        """
        print("\nSETUP FIXTURE")
        # Patching all widget classes imported in ui.main_window
        with patch('ui.main_window.HomeWidget') as MockHome, \
             patch('ui.main_window.DashboardWidget') as MockDashboard, \
             patch('ui.main_window.DefinirLoteWidget') as MockDefinirLote, \
             patch('ui.main_window.CalculateTimesWidget') as MockCalculate, \
             patch('ui.main_window.PreprocesosWidget') as MockPreprocesos, \
             patch('ui.main_window.AddProductWidget') as MockAddProduct, \
             patch('ui.main_window.GestionDatosWidget') as MockGestionDatos, \
             patch('ui.main_window.ReportesWidget') as MockReportes, \
             patch('ui.main_window.HistorialWidget') as MockHistorial, \
             patch('ui.main_window.SettingsWidget') as MockSettings, \
             patch('ui.main_window.HelpWidget') as MockHelp:
            
            # Use a side_effect that returns a plain QWidget
            mock_widget_factory = lambda *args, **kwargs: QWidget()
            
            MockHome.side_effect = mock_widget_factory
            MockDashboard.side_effect = mock_widget_factory
            MockDefinirLote.side_effect = mock_widget_factory
            MockCalculate.side_effect = mock_widget_factory
            MockPreprocesos.side_effect = mock_widget_factory
            MockAddProduct.side_effect = mock_widget_factory
            MockGestionDatos.side_effect = mock_widget_factory
            MockReportes.side_effect = mock_widget_factory
            MockHistorial.side_effect = mock_widget_factory
            MockSettings.side_effect = mock_widget_factory
            MockHelp.side_effect = mock_widget_factory

            view = MainView()
            view.controller = mock_controller
            # MOCK BLOCKING DIALOGS
            view.show_confirmation_dialog = MagicMock(return_value=True)
            
            view.init_ui()
            view.set_controller(mock_controller)
            
            qtbot.addWidget(view)
            yield view
            print("\nTEARDOWN FIXTURE")

    def test_initialization(self, main_view):
        print("Running test_initialization")
        assert "Calculadora de Tiempos" in main_view.windowTitle()
        assert main_view.stacked_widget.count() > 0
        assert len(main_view.pages) > 0

    def test_navigation_structure(self, main_view):
        print("Running test_navigation_structure")
        expected_pages = [
            "home", "dashboard", "definir_lote", "calculate", "preprocesos",
            "add_product", "gestion_datos", "reportes", "historial", "settings", "help"
        ]
        for page in expected_pages:
            assert page in main_view.pages

    def test_switch_page(self, main_view):
        print("Running test_switch_page")
        main_view.switch_page("dashboard")
        assert main_view.stacked_widget.currentWidget() == main_view.pages["dashboard"]
        assert main_view.buttons["dashboard"].isChecked()
        
        main_view.switch_page("settings")
        assert main_view.stacked_widget.currentWidget() == main_view.pages["settings"]
        assert main_view.buttons["settings"].isChecked()

    def test_nav_button_click(self, main_view, mock_controller, qtbot):
        print("Running test_nav_button_click")
        # Simulate click on 'dashboard' button
        btn = main_view.buttons["dashboard"]
        
        # Use QTimer to ensure event loop is running if needed, or just mouseClick
        # qtbot.mouseClick sends events immediately.
        qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
        
        # Verify controller method was called
        mock_controller._on_nav_button_clicked.assert_called_with("dashboard")

    def test_planification_menu_selection(self, main_view):
        print("Running test_planification_menu_selection")
        main_view.switch_page("definir_lote")
        assert main_view.buttons["planificacion_main"].isChecked()
        
        main_view.switch_page("calculate")
        assert main_view.buttons["planificacion_main"].isChecked()
        
        main_view.switch_page("home")
        assert not main_view.buttons["planificacion_main"].isChecked()
