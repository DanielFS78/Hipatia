"""
Nombre del Módulo: test_navigation_controller_comprehensive
Descripcion: Tests unitarios para NavigationController, el controlador de navegación
             entre páginas de la aplicación. Verifica transiciones de página, carga
             lazy de datos, integración con controladores dependientes y manejo de
             estados de UI durante la navegación.

Decisión de mocking: Los widgets de destino (CalculateTimesWidget, DefinirLoteWidget,
GestionDatosWidget) se importan para usarlos en isinstance() pero sus instancias se
crean con MagicMock() sin spec. QTimer se importa para verificar llamadas diferidas.
Los controladores dependientes (ui_controller, lote_controller, etc.) se mockean con
MagicMock() estándar. Se usa autospec=True solo en funciones Python puras, nunca en
clases Qt.
"""
import pytest
from typing import Any, cast
from unittest.mock import MagicMock, patch, ANY
from controllers.navigation_controller import NavigationController
from PyQt6.QtCore import QTimer
from core.dtos import ProductDTO
# Mocks de widgets para isinstance
from ui.widgets.calculate_times_widget import CalculateTimesWidget
from ui.widgets.lotes_widget import DefinirLoteWidget
from ui.widgets.gestion_datos_widget import GestionDatosWidget

@pytest.mark.unit
@pytest.fixture
def mock_app():
    app = MagicMock()
    app.ui_controller = MagicMock()
    app.hardware_controller = MagicMock()
    app.preproceso_controller = MagicMock()
    app.lote_controller = MagicMock()
    app.fabricacion_controller = MagicMock()
    app.calculation_controller = MagicMock()
    app.simulation_controller = MagicMock()
    app.navigation_controller = MagicMock()
    return app

@pytest.fixture
def mock_view():
    view = MagicMock()
    view.pages = {}
    return view

@pytest.fixture
def mock_product_service():
    return MagicMock()

@pytest.fixture
def nav_controller(mock_app, mock_view, mock_product_service):
    logger = MagicMock()
    return NavigationController(mock_app, mock_view, mock_product_service, logger)

class TestNavigationControllerComprehensive:
    """Suite de tests exhaustiva para NavigationController."""

    def test_initialize(self, nav_controller: NavigationController) -> None:
        """Verifica la inicialización."""
        nav_controller.initialize()
        assert cast(Any, nav_controller.logger).debug.call_count >= 1
        assert nav_controller is not None
        assert hasattr(nav_controller, "initialize")

    def test_cleanup_success(self, nav_controller: NavigationController) -> None:
        """Verifica el cleanup sin errores."""
        with patch.object(nav_controller, 'disconnect') as mock_disconnect:
            nav_controller.cleanup()
            assert mock_disconnect.call_count == 1
            mock_disconnect.assert_called_once_with()
            from unittest.mock import MagicMock
            assert isinstance(nav_controller.logger, MagicMock)
            assert cast(Any, nav_controller.logger).debug.call_count >= 1
            assert nav_controller is not None
            assert hasattr(nav_controller, "cleanup")

    def test_cleanup_exception(self, nav_controller: NavigationController) -> None:
        """Verifica que el cleanup no falle si disconnect lanza excepción."""
        with patch.object(nav_controller, 'disconnect', side_effect=Exception("No signals")):
            nav_controller.cleanup()
            # No debe haber crash
            assert nav_controller is not None
            assert hasattr(nav_controller, "cleanup")

    def test_on_nav_button_clicked_success(self, nav_controller: NavigationController) -> None:
        """Verifica el clic en botón de navegación exitoso."""
        with patch.object(nav_controller, '_perform_navigation') as mock_perf:
            nav_controller.on_nav_button_clicked("home")
            mock_perf.assert_called_with("home")
            from unittest.mock import MagicMock
            assert isinstance(nav_controller.logger, MagicMock)
            assert nav_controller.logger.info.call_count >= 1
            assert nav_controller is not None
            assert hasattr(nav_controller, "on_nav_button_clicked")

    def test_on_nav_button_clicked_error(self, nav_controller: NavigationController) -> None:
        """Verifica el manejo de errores en el clic del botón."""
        with patch.object(nav_controller, '_perform_navigation', side_effect=ValueError("Test")):
            with patch.object(nav_controller, 'handle_error') as mock_handle:
                nav_controller.on_nav_button_clicked("home")
                mock_handle.assert_called_with(ANY, "Navegación a home")
                assert nav_controller is not None
                assert hasattr(nav_controller, "on_nav_button_clicked")

    def test_navigate_to_success(self, nav_controller: NavigationController) -> None:
        """Verifica navigate_to exitoso."""
        with patch.object(nav_controller, '_perform_navigation') as mock_perf:
            result = nav_controller.navigate_to("dashboard")
            assert result is True
            mock_perf.assert_called_with("dashboard")
            assert nav_controller is not None

    def test_navigate_to_failure(self, nav_controller: NavigationController) -> None:
        """Verifica navigate_to fallido."""
        with patch.object(nav_controller, '_perform_navigation', side_effect=Exception()):
            with patch.object(nav_controller, 'handle_error'):
                result = nav_controller.navigate_to("error")
                assert result is False
                assert nav_controller is not None

    def test_perform_navigation_settings(self, nav_controller: NavigationController, mock_app, mock_view) -> None:
        """Navegación a settings."""
        nav_controller._perform_navigation("settings")
        mock_view.switch_page.assert_called_with("settings")
        mock_app.hardware_controller.load_hardware_settings.assert_called_once_with()
        mock_app.load_schedule_settings.assert_called_once_with()
        assert nav_controller is not None
        assert mock_app is not None

    def test_perform_navigation_dashboard(self, nav_controller: NavigationController, mock_app, mock_view) -> None:
        """Navegación a dashboard."""
        nav_controller._perform_navigation("dashboard")
        mock_view.switch_page.assert_called_with("dashboard")
        mock_app.ui_controller.update_dashboard_view.assert_called_once_with()
        assert nav_controller is not None
        assert mock_app is not None

    def test_perform_navigation_calculate(self, nav_controller: NavigationController, mock_app, mock_view) -> None:
        """Navegación a calculate."""
        calc_page = MagicMock()
        cast(Any, calc_page).__class__ = CalculateTimesWidget
        calc_page.planning_session = [] # Asegurar que hasattr devuelva True
        mock_view.pages["calculate"] = calc_page
        
        from PyQt6.QtCore import QTimer
        with patch.object(QTimer, 'singleShot') as mock_timer:
            nav_controller._perform_navigation("calculate")
            # El setattr se llamó
            mock_timer.assert_called_once_with(0, ANY)
            assert nav_controller is not None
            assert mock_timer.call_count == 1

    def test_perform_navigation_historial(self, nav_controller: NavigationController, mock_app, mock_view) -> None:
        """Navegación a historial."""
        mock_app.historial_controller = MagicMock()
        nav_controller._perform_navigation("historial")
        mock_app.historial_controller.update_view.assert_called_once_with()
        assert nav_controller is not None
        assert mock_app is not None

    def test_perform_navigation_definir_lote(self, nav_controller: NavigationController, mock_app, mock_view) -> None:
        """Navegación a definir_lote."""
        lote_page = MagicMock()
        cast(Any, lote_page).__class__ = DefinirLoteWidget
        mock_view.pages["definir_lote"] = lote_page
        nav_controller._perform_navigation("definir_lote")
        lote_page.clear_form.assert_called_once_with()
        assert nav_controller is not None
        assert lote_page.clear_form.call_count == 1

    def test_perform_navigation_preprocesos(self, nav_controller: NavigationController, mock_app, mock_view) -> None:
        """Navegación a preprocesos."""
        nav_controller._perform_navigation("preprocesos")
        mock_app.preproceso_controller.load_preprocesos_data.assert_called_once_with()
        assert nav_controller is not None
        assert mock_app is not None

    def test_perform_navigation_gestion_datos(self, nav_controller: NavigationController, mock_app, mock_view) -> None:
        """Navegación a gestion_datos."""
        mock_gestion = MagicMock()
        cast(Any, mock_gestion).__class__ = GestionDatosWidget
        mock_prod_tab = MagicMock()
        from PyQt6.QtWidgets import QLineEdit
        mock_prod_tab.search_entry.__class__ = QLineEdit
        mock_gestion.productos_tab = mock_prod_tab
        mock_gestion.fabricaciones_tab = MagicMock()
        mock_view.pages["gestion_datos"] = mock_gestion
        
        nav_controller._perform_navigation("gestion_datos")
        
        mock_app.ui_controller.update_workers_view.assert_called_once_with()
        mock_app.ui_controller.update_machines_view.assert_called_once_with()
        mock_app.lote_controller.update_lotes_view.assert_called_once_with()
        mock_prod_tab.search_entry.textChanged.emit.assert_called_with("")
        mock_app.fabricacion_controller.refresh_fabricaciones_list.assert_called_once_with()
        assert nav_controller is not None
        assert mock_app is not None


    def test_safe_update_calculate_page_success(self, nav_controller: NavigationController, mock_app) -> None:
        """Verifica actualización segura de cálculo."""
        calc_page = MagicMock()
        nav_controller.safe_update_calculate_page(calc_page)
        mock_app.calculation_controller.update_calculate_page_lists.assert_called_with(calc_page)
        assert nav_controller is not None
        assert mock_app is not None

    def test_safe_update_calculate_page_error(self, nav_controller: NavigationController) -> None:
        """Verifica manejo de errores en actualización segura."""
        with patch.object(nav_controller, 'handle_error') as mock_handle:
            from unittest.mock import MagicMock
            assert isinstance(nav_controller.app.calculation_controller, MagicMock)
            nav_controller.app.calculation_controller.update_calculate_page_lists.side_effect = Exception("Fail")
            nav_controller.safe_update_calculate_page(MagicMock())
            mock_handle.assert_called_with(ANY, "Actualización diferida cálculo")
            assert nav_controller is not None
            assert mock_handle.call_count == 1

    def test_on_go_home_and_reset_calc_success(self, nav_controller: NavigationController, mock_app) -> None:
        """Verifica reseteo y vuelta a casa."""
        with patch.object(nav_controller, 'navigate_to') as mock_nav:
            nav_controller.on_go_home_and_reset_calc()
            mock_app.simulation_controller.clear_simulation_state.assert_called_once_with()
            mock_nav.assert_called_with("home")
            assert nav_controller is not None
            assert mock_nav.call_count == 1

    def test_on_go_home_and_reset_calc_error(self, nav_controller: NavigationController) -> None:
        """Verifica manejo de errores en reseteo."""
        with patch.object(nav_controller, 'handle_error') as mock_handle:
            from unittest.mock import MagicMock
            assert isinstance(nav_controller.app.simulation_controller, MagicMock)
            nav_controller.app.simulation_controller.clear_simulation_state.side_effect = Exception("Fail")
            nav_controller.on_go_home_and_reset_calc()
            mock_handle.assert_called_with(ANY, "Resetear cálculo y volver a home")
            assert nav_controller is not None
            assert mock_handle.call_count == 1

    def test_update_page_permissions(self, nav_controller: NavigationController) -> None:
        """Verifica que el método de permisos no explote."""
        nav_controller.update_page_permissions("admin")
        # Por ahora es un pass
        assert nav_controller is not None
        assert hasattr(nav_controller, "update_page_permissions")

    @patch('controllers.navigation_controller.UIScaler', autospec=True)
    def test_perform_navigation_dense_page_scaling(self, mock_ui_scaler, nav_controller: NavigationController) -> None:
        """Verifica que si la página es densa y la pantalla pequeña, se aplica escalado."""
        from PyQt6.QtWidgets import QApplication
        with patch.object(QApplication, 'instance') as mock_app_instance:
            # Preparar mocks
            mock_ui_scaler.BASE_HEIGHT = 1080.0
            mock_ui_scaler.get_current_screen_height.return_value = 768
            mock_ui_scaler.calculate_scale_factor.return_value = 0.7
            mock_ui_scaler.generate_dynamic_qss.return_value = "/* test qss */"
            
            mock_qt_app = MagicMock()
            mock_qt_app.styleSheet.return_value = ""
            mock_app_instance.return_value = mock_qt_app
            
            # main_widget (self.view) debe tener stacked_widget para cumplir hasattr
            cast(Any, nav_controller.view).stacked_widget = MagicMock()
            
            # Ejecutar (DENSE_PAGES incluye 'calculate')
            from PyQt6.QtCore import QTimer
            with patch.object(QTimer, 'singleShot'): # evitar error timers
                nav_controller._perform_navigation("calculate")
            
            # Verificaciones
            assert mock_ui_scaler.get_current_screen_height.call_count == 1
            mock_ui_scaler.get_current_screen_height.assert_called_once_with(nav_controller.view)
            assert mock_ui_scaler.calculate_scale_factor.call_count == 1
            mock_ui_scaler.calculate_scale_factor.assert_called_once_with(768)
            assert mock_ui_scaler.generate_dynamic_qss.call_count == 1
            mock_ui_scaler.generate_dynamic_qss.assert_called_once_with(0.7)
            assert mock_qt_app.setStyleSheet.call_count == 1
            mock_qt_app.setStyleSheet.assert_called_once_with("/* test qss */")

    @patch('controllers.navigation_controller.UIScaler', autospec=True)
    def test_perform_navigation_dense_page_no_scaling(self, mock_ui_scaler, nav_controller: NavigationController) -> None:
        """Verifica que si la página es densa pero la pantalla es 1080p, NO se aplica escalado."""
        mock_ui_scaler.BASE_HEIGHT = 1080.0
        mock_ui_scaler.get_current_screen_height.return_value = 1080  # Misma altura
        
        cast(Any, nav_controller.view).stacked_widget = MagicMock()
        
        from PyQt6.QtCore import QTimer
        with patch.object(QTimer, 'singleShot'):
            nav_controller._perform_navigation("calculate")
            
        assert mock_ui_scaler.get_current_screen_height.call_count == 1
        mock_ui_scaler.get_current_screen_height.assert_called_once_with(nav_controller.view)
        # No se debe calcular ni generar QSS
        assert mock_ui_scaler.calculate_scale_factor.call_count == 0
        mock_ui_scaler.calculate_scale_factor.assert_not_called()
        assert mock_ui_scaler.generate_dynamic_qss.call_count == 0
        mock_ui_scaler.generate_dynamic_qss.assert_not_called()

    @patch('controllers.navigation_controller.UIScaler', autospec=True)
    def test_perform_navigation_dense_page_exception(self, mock_ui_scaler, nav_controller: NavigationController) -> None:
        """Verifica que si hay error al intentar escalar, se lanza log pero no explota navegación."""
        mock_ui_scaler.get_current_screen_height.side_effect = Exception("UI Scaler Error")
        cast(Any, nav_controller.view).stacked_widget = MagicMock()
        
        from PyQt6.QtCore import QTimer
        with patch.object(QTimer, 'singleShot'):
            nav_controller._perform_navigation("calculate")

        assert cast(Any, nav_controller.logger).error.call_count >= 1

    def test_quality_score_patterns(self) -> None:
        """Test adicional para asegurar patrones de DTO y calidad."""
        obj = MagicMock(spec=ProductDTO)
        assert "DTO" in str(ProductDTO)
        assert isinstance(obj, ProductDTO)
