"""
Tests unitarios para AppController - Gestión de Historial.

Cobertura objetivo: Métodos relacionados con historial y bitácora.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, date, timedelta
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import QListWidgetItem

from controllers.app_controller import AppController
from ui.widgets import HistorialWidget


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_app():
    """Crea AppController con dependencias mockeadas."""
    model = MagicMock()
    model.get_historial_entries.return_value = []
    model.get_product_iterations.return_value = []
    model.get_diario_bitacora.return_value = (None, [])
    model.load_pila.return_value = ({}, [], [], [])
    
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


@pytest.fixture
def mock_historial_page():
    """Mock de HistorialWidget con todos los componentes necesarios."""
    page = MagicMock(spec=HistorialWidget)
    page.current_mode = "iteraciones"
    page.search_entry = MagicMock()
    page.search_entry.text.return_value = ""
    page.filter_combo = MagicMock()
    page.filter_combo.currentText.return_value = "Todos los Responsables"
    page.results_list = MagicMock()
    page.results_list.clear = MagicMock()
    page.results_list.count.return_value = 0
    page.results_list.selectedItems.return_value = []
    page.details_stack = MagicMock()
    page.details_title_label = MagicMock()
    page.details_text = MagicMock()
    page.activity_chart_view = MagicMock()
    page.clear_calendar_format = MagicMock()
    page.highlight_calendar_dates = MagicMock()
    return page


# =============================================================================
# TESTS: update_historial_view
# =============================================================================

class TestUpdateHistorialView:
    """Tests para update_historial_view."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app.update_historial_view)


# =============================================================================
# TESTS: _connect_historial_signals
# =============================================================================

class TestConnectHistorialSignals:
    """Tests para _connect_historial_signals."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._connect_historial_signals)

    def test_no_crash_without_page(self, mock_app):
        """Verifica que no crashea sin página."""
        mock_app.view.pages = {}
        mock_app._connect_historial_signals()

    def test_connects_signals_when_page_exists(self, mock_app, mock_historial_page):
        """Verifica que conecta señales cuando la página existe."""
        mock_app.view.pages = {"historial": mock_historial_page}
        # Parchear isinstance para que retorne True para nuestro mock
        with patch('controllers.app_controller.isinstance', return_value=True):
            mock_app._connect_historial_signals()
            # Debería haber intentado conectar señales
            mock_historial_page.mode_changed_signal.connect.assert_called()


# =============================================================================
# TESTS: _populate_historial_list
# =============================================================================

class TestPopulateHistorialList:
    """Tests para _populate_historial_list."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._populate_historial_list)

    def test_returns_early_without_page(self, mock_app):
        """Verifica que retorna sin hacer nada si no hay página."""
        mock_app.view.pages = {}
        mock_app._populate_historial_list()  # No debería crashear

    def test_returns_early_without_historial_data(self, mock_app, mock_historial_page):
        """Verifica que retorna si no hay historial_data."""
        mock_app.view.pages = {"historial": mock_historial_page}
        # Eliminar el atributo historial_data si existe
        if hasattr(mock_app, 'historial_data'):
            delattr(mock_app, 'historial_data')
        mock_app._populate_historial_list()
        # Sin historial_data, no debería añadir items
        mock_historial_page.results_list.addItem.assert_not_called()

    def test_clears_list_and_populates_iteraciones(self, mock_app, mock_historial_page):
        """Verifica que limpia la lista y popula con iteraciones."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        # Mock iteration data
        mock_iteration = MagicMock()
        mock_iteration.producto_codigo = "PROD001"
        mock_iteration.producto_descripcion = "Producto Test"
        mock_iteration.nombre_responsable = "Juan"
        mock_iteration.fecha_creacion = datetime.now()
        
        mock_app.historial_data = [mock_iteration]
        
        mock_app._populate_historial_list()
        
        mock_historial_page.results_list.clear.assert_called_once()
        mock_historial_page.results_list.addItem.assert_called()

    def test_populates_fabricaciones_mode(self, mock_app, mock_historial_page):
        """Verifica que popula en modo fabricaciones."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "fabricaciones"
        
        mock_fab = MagicMock()
        mock_fab.nombre = "Fab001"
        mock_fab.descripcion = "Fabricación Test"
        mock_fab.start_date = date.today()
        mock_fab.end_date = date.today() + timedelta(days=5)
        
        mock_app.historial_data = [mock_fab]
        
        mock_app._populate_historial_list()
        
        mock_historial_page.results_list.addItem.assert_called()

    def test_filters_by_responsable(self, mock_app, mock_historial_page):
        """Verifica que filtra por responsable."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        mock_historial_page.filter_combo.currentText.return_value = "Pedro"
        
        mock_iteration = MagicMock()
        mock_iteration.producto_codigo = "PROD001"
        mock_iteration.producto_descripcion = "Producto"
        mock_iteration.nombre_responsable = "Juan"  # Diferente al filtro
        mock_iteration.fecha_creacion = datetime.now()
        
        mock_app.historial_data = [mock_iteration]
        
        mock_app._populate_historial_list()
        
        # No debería añadir item porque el responsable no coincide
        mock_historial_page.results_list.addItem.assert_not_called()

    def test_filters_by_search_text(self, mock_app, mock_historial_page):
        """Verifica que filtra por texto de búsqueda."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        mock_historial_page.search_entry.text.return_value = "noexiste"
        
        mock_iteration = MagicMock()
        mock_iteration.producto_codigo = "PROD001"
        mock_iteration.producto_descripcion = "Producto Test"
        mock_iteration.nombre_responsable = "Juan"
        mock_iteration.fecha_creacion = datetime.now()
        
        mock_app.historial_data = [mock_iteration]
        
        mock_app._populate_historial_list()
        
        mock_historial_page.results_list.addItem.assert_not_called()


# =============================================================================
# TESTS: _on_historial_item_selected
# =============================================================================

class TestOnHistorialItemSelected:
    """Tests para _on_historial_item_selected."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._on_historial_item_selected)

    def test_returns_early_without_page(self, mock_app):
        """Verifica que retorna si no hay página historial."""
        mock_app.view.pages = {}
        mock_item = MagicMock()
        mock_app._on_historial_item_selected(mock_item)

    def test_handles_iteraciones_mode(self, mock_app, mock_historial_page):
        """Verifica el manejo de selección en modo iteraciones."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        mock_iteration = MagicMock()
        mock_iteration.producto_codigo = "PROD001"
        mock_iteration.fecha_creacion = datetime.now()
        
        mock_item = MagicMock()
        mock_item.data.return_value = mock_iteration
        
        mock_app.model.get_product_iterations.return_value = []
        
        mock_app._on_historial_item_selected(mock_item)
        
        mock_historial_page.details_stack.setCurrentIndex.assert_called_with(1)
        mock_app.model.get_product_iterations.assert_called_with("PROD001")

    def test_handles_fabricaciones_mode(self, mock_app, mock_historial_page):
        """Verifica el manejo de selección en modo fabricaciones."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "fabricaciones"
        
        mock_fab = MagicMock()
        mock_fab.nombre = "Fab001"
        mock_fab.id = 1
        mock_fab.start_date = date.today()
        mock_fab.end_date = date.today()
        
        mock_item = MagicMock()
        mock_item.data.return_value = mock_fab
        
        mock_app.model.get_diario_bitacora.return_value = (1, [])
        
        mock_app._on_historial_item_selected(mock_item)
        
        mock_historial_page.details_stack.setCurrentIndex.assert_called_with(1)


# =============================================================================
# TESTS: _on_historial_calendar_clicked
# =============================================================================

class TestOnHistorialCalendarClicked:
    """Tests para _on_historial_calendar_clicked."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._on_historial_calendar_clicked)

    def test_returns_early_without_page(self, mock_app):
        """Verifica que retorna sin página."""
        mock_app.view.pages = {}
        q_date = QDate.currentDate()
        mock_app._on_historial_calendar_clicked(q_date)

    def test_filters_items_by_date_iteraciones(self, mock_app, mock_historial_page):
        """Verifica que filtra items por fecha en modo iteraciones."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        # Mock list item
        mock_list_item = MagicMock()
        mock_item_data = {"fecha_creacion": "2025-12-27 10:00:00"}
        mock_list_item.data.return_value = mock_item_data
        
        mock_historial_page.results_list.count.return_value = 1
        mock_historial_page.results_list.item.return_value = mock_list_item
        
        q_date = QDate(2025, 12, 27)
        mock_app._on_historial_calendar_clicked(q_date)
        
        # Debería setear visible
        mock_list_item.setHidden.assert_called()

    def test_filters_items_by_date_fabricaciones(self, mock_app, mock_historial_page):
        """Verifica que filtra items por fecha en modo fabricaciones."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "fabricaciones"
        
        today = date.today()
        mock_item_data = {
            "start_date": today - timedelta(days=2),
            "end_date": today + timedelta(days=2)
        }
        
        mock_list_item = MagicMock()
        mock_list_item.data.return_value = mock_item_data
        
        mock_historial_page.results_list.count.return_value = 1
        mock_historial_page.results_list.item.return_value = mock_list_item
        
        q_date = QDate(today.year, today.month, today.day)
        mock_app._on_historial_calendar_clicked(q_date)
        
        mock_list_item.setHidden.assert_called_with(False)


# =============================================================================
# TESTS: _update_historial_calendar_highlights
# =============================================================================

class TestUpdateHistorialCalendarHighlights:
    """Tests para _update_historial_calendar_highlights."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._update_historial_calendar_highlights)

    def test_returns_early_without_page(self, mock_app):
        """Verifica que retorna sin página."""
        mock_app.view.pages = {}
        mock_app._update_historial_calendar_highlights()

    def test_clears_calendar_format(self, mock_app, mock_historial_page):
        """Verifica que limpia el formato del calendario."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.results_list.count.return_value = 0
        
        mock_app._update_historial_calendar_highlights()
        
        mock_historial_page.clear_calendar_format.assert_called_once()

    def test_highlights_dates_for_iteraciones(self, mock_app, mock_historial_page):
        """Verifica que resalta fechas para iteraciones."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        mock_iteration = MagicMock()
        mock_iteration.fecha_creacion = datetime.now()
        
        mock_list_item = MagicMock()
        mock_list_item.data.return_value = mock_iteration
        
        mock_historial_page.results_list.count.return_value = 1
        mock_historial_page.results_list.item.return_value = mock_list_item
        
        mock_app._update_historial_calendar_highlights()
        
        mock_historial_page.highlight_calendar_dates.assert_called()
        # Color azul para iteraciones
        call_args = mock_historial_page.highlight_calendar_dates.call_args
        assert call_args[0][1] == "#3498db"


# =============================================================================
# TESTS: _on_print_historial_report_clicked
# =============================================================================

class TestOnPrintHistorialReportClicked:
    """Tests para _on_print_historial_report_clicked."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._on_print_historial_report_clicked)

    def test_returns_early_without_page(self, mock_app):
        """Verifica que retorna sin página."""
        mock_app.view.pages = {}
        mock_app._on_print_historial_report_clicked()

    def test_shows_warning_when_no_selection(self, mock_app, mock_historial_page):
        """Verifica mensaje de warning cuando no hay selección."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.results_list.selectedItems.return_value = []
        
        mock_app._on_print_historial_report_clicked()
        
        mock_app.view.show_message.assert_called_with(
            "Selección Requerida",
            "Debe seleccionar un elemento de la lista para imprimir.",
            "warning"
        )

    def test_generates_iteration_report(self, mock_app, mock_historial_page):
        """Verifica generación de informe de iteración."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        mock_item_data = {"producto_codigo": "PROD001", "descripcion": "Test"}
        mock_selected = MagicMock()
        mock_selected.data.return_value = mock_item_data
        mock_historial_page.results_list.selectedItems.return_value = [mock_selected]
        
        mock_app.model.get_product_iterations.return_value = []
        
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog, \
             patch('controllers.app_controller.GeneradorDeInformes') as MockGen:
            mock_dialog.return_value = ("/tmp/test.pdf", "")
            mock_gen_instance = MockGen.return_value
            mock_gen_instance.generar_y_guardar.return_value = True
            
            mock_app._on_print_historial_report_clicked()
            
            mock_app.view.show_message.assert_called()

    def test_handles_file_dialog_cancel(self, mock_app, mock_historial_page):
        """Verifica que maneja cancelación del diálogo de archivo."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        mock_item_data = {"producto_codigo": "PROD001", "descripcion": "Test"}
        mock_selected = MagicMock()
        mock_selected.data.return_value = mock_item_data
        mock_historial_page.results_list.selectedItems.return_value = [mock_selected]
        
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
            mock_dialog.return_value = ("", "")  # Usuario canceló
            
            mock_app._on_print_historial_report_clicked()
            
            # No debería mostrar mensaje de éxito ni error
            assert mock_app.view.show_message.call_count == 0 or \
                   "warning" not in str(mock_app.view.show_message.call_args)


# =============================================================================
# TESTS: _update_historial_activity_chart
# =============================================================================

class TestUpdateHistorialActivityChart:
    """Tests para _update_historial_activity_chart."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._update_historial_activity_chart)

    def test_returns_early_without_page(self, mock_app):
        """Verifica que retorna sin página."""
        mock_app.view.pages = {}
        mock_app._update_historial_activity_chart()

    def test_returns_early_without_historial_data(self, mock_app, mock_historial_page):
        """Verifica que retorna sin historial_data."""
        mock_app.view.pages = {"historial": mock_historial_page}
        # Asegurarse de que NO existe el atributo historial_data
        if hasattr(mock_app, 'historial_data'):
            delattr(mock_app, 'historial_data')
        
        mock_app._update_historial_activity_chart()
        # No debería llamar a setChart si retornó temprano
        mock_historial_page.activity_chart_view.setChart.assert_not_called()

    def test_creates_chart_for_iteraciones(self, mock_app, mock_historial_page):
        """Verifica creación de gráfico para iteraciones."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        mock_item = {"fecha_creacion": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        mock_app.historial_data = [mock_item]
        
        with patch('controllers.app_controller.QLineSeries'), \
             patch('controllers.app_controller.QChart') as MockChart, \
             patch('controllers.app_controller.QDateTimeAxis'), \
             patch('controllers.app_controller.QValueAxis'):
            
            mock_app._update_historial_activity_chart()
            
            MockChart.assert_called()
            mock_historial_page.activity_chart_view.setChart.assert_called()

    def test_handles_empty_data(self, mock_app, mock_historial_page):
        """Verifica manejo de datos vacíos."""
        mock_app.view.pages = {"historial": mock_historial_page}
        mock_app.historial_data = []
        
        with patch('controllers.app_controller.QLineSeries'), \
             patch('controllers.app_controller.QChart') as MockChart, \
             patch('controllers.app_controller.QDateTimeAxis'), \
             patch('controllers.app_controller.QValueAxis'):
            
            mock_app._update_historial_activity_chart()
            
            MockChart.assert_called()
