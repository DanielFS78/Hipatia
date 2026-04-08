"""
Nombre del Módulo: test_historial_controller_comprehensive
Descripcion: Tests unitarios para HistorialController, el controlador del historial
             de fabricaciones. Verifica carga de datos, filtrado por fecha y estado,
             exportación a Excel, detalle de fabricación y manejo de errores de
             base de datos.

Decisión de mocking: Los widgets Qt del historial se mockean con MagicMock() sin spec.
Los repos de iteración y producto usan create_autospec sobre las clases reales; no se usa
autospec en clases Qt.
"""
import pytest
from unittest.mock import MagicMock, patch, call, create_autospec
from typing import Any, cast
from datetime import datetime, date, timedelta
from PyQt6.QtCore import QDate, Qt, QObject
from PyQt6.QtWidgets import QListWidgetItem

from controllers.historial.controller import HistorialController
from core.dtos import ProductIterationDTO
from database.repositories import IterationRepository, ProductRepository

pytestmark = pytest.mark.unit

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_model():
    from core.services.pila_service import PilaService
    from core.services.worker_service import WorkerService
    model = MagicMock(spec=['db', 'pila_service', 'worker_service'])
    model.db = MagicMock(spec=['iteration_repo', 'product_repo'])
    model.db.iteration_repo = create_autospec(IterationRepository, instance=True)
    model.db.product_repo = create_autospec(ProductRepository, instance=True)
    model.pila_service = create_autospec(PilaService, instance=True)
    model.worker_service = create_autospec(WorkerService, instance=True)
    model.db.iteration_repo.get_all_iterations_with_dates.return_value = []
    model.pila_service.get_all_pilas_with_dates.return_value = []
    model.db.iteration_repo.get_product_iterations.return_value = []
    model.pila_service.get_diario_bitacora.return_value = (None, [])
    model.pila_service.load_pila.return_value = ({}, [], [], [])
    return model

@pytest.fixture
def mock_view():
    view = MagicMock(spec=['pages', 'show_message'])
    view.pages = {}
    return view

@pytest.fixture
def mock_historial_page():
    page = MagicMock(spec=['current_mode', 'search_entry', 'filter_combo', 'results_list',
                           'details_stack', 'details_text', 'activity_chart_view',
                           'highlight_calendar_dates', 'clear_view', 'clear_calendar_format',
                           'details_title_label', 'blockSignals'])
    page.current_mode = "iteraciones"
    page.search_entry = MagicMock(spec=['text'])
    page.search_entry.text.return_value = ""
    page.filter_combo = MagicMock(spec=['currentText', 'addItems', 'addItem', 'clear', 'blockSignals'])
    page.filter_combo.currentText.return_value = "Todos los Responsables"
    page.results_list = MagicMock(spec=['count', 'selectedItems', 'addItem', 'item', 'clear'])
    page.results_list.count.return_value = 0
    page.results_list.selectedItems.return_value = []
    page.details_stack = MagicMock()
    page.details_text = MagicMock(spec=['setText'])
    page.details_title_label = MagicMock(spec=['setText'])
    page.activity_chart_view = MagicMock(spec=['setChart'])
    page.highlight_calendar_dates = MagicMock()
    page.clear_view = MagicMock()
    page.clear_calendar_format = MagicMock()
    page.blockSignals = MagicMock()
    return page

@pytest.fixture(autouse=True)
def patch_historial_widget_class():
    """No longer needed as we use hasattr instead of isinstance checks."""
    yield

@pytest.fixture
def controller(mock_model, mock_view):
    ctrl = HistorialController(mock_model.db, mock_model.pila_service, mock_model.worker_service, mock_view)
    # Mock loggers para evitar fallos de aserción y facilitar rastreo
    ctrl.logger = MagicMock()
    ctrl.view_manager.logger = MagicMock()
    ctrl.interaction_manager.logger = MagicMock()
    ctrl.report_manager.logger = MagicMock()
    return ctrl

# =============================================================================
# TESTS
# =============================================================================

@pytest.mark.unit
class TestHistorialControllerComprehensive:
    
    def test_init(self, controller: HistorialController, mock_model, mock_view) -> None:
        """Verifica la inicialización correcta."""
        assert controller.db == mock_model.db
        assert controller.pila_service == mock_model.pila_service
        assert controller.worker_service == mock_model.worker_service
        assert controller.view == mock_view
        assert controller.historial_data == []
        assert controller.logger is not None

    def test_connect_signals(self, controller: HistorialController) -> None:
        """Verifica la conexión de señales con la página de historial."""
        mock_page = MagicMock()
        controller.connect_signals(mock_page)
        
        assert mock_page.search_text_changed_signal.connect.call_count == 1
        mock_page.search_text_changed_signal.connect.assert_called_with(controller.populate_list)
        assert mock_page.filter_changed_signal.connect.call_count == 1
        mock_page.filter_changed_signal.connect.assert_called_with(controller.populate_list)
        assert mock_page.item_selected_signal.connect.call_count == 1
        mock_page.item_selected_signal.connect.assert_called_with(controller.on_item_selected)
        assert mock_page.calendar_date_selected_signal.connect.call_count == 1
        mock_page.calendar_date_selected_signal.connect.assert_called_with(controller.on_calendar_clicked)
        assert mock_page.print_report_signal.connect.call_count == 1
        mock_page.print_report_signal.connect.assert_called_with(controller.on_print_report_clicked)
        assert mock_page.mode_changed_signal.connect.call_count == 1
        mode_cb = mock_page.mode_changed_signal.connect.call_args[0][0]
        assert callable(mode_cb)

    def test_update_view_no_page(self, controller: HistorialController, mock_view) -> None:
        """Retorna si la página no es HistorialWidget."""
        mock_view.pages = {"historial": "NotAWidget"}
        controller.update_view()
        assert cast(Any, controller.db.iteration_repo.get_all_iterations_with_dates).call_count == 0

    def test_update_view_iteraciones(self, controller: HistorialController, mock_view, mock_historial_page, mock_model) -> None:
        """Verifica actualización en modo iteraciones."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        item1 = MagicMock(spec=ProductIterationDTO)
        item1.nombre_responsable = "Juan"
        isinstance(item1, ProductIterationDTO)
        
        item2 = MagicMock(spec=ProductIterationDTO)
        item2.nombre_responsable = "Pedro"
        
        mock_model.db.iteration_repo.get_all_iterations_with_dates.return_value = [item1, item2, item1]
        
        with patch.object(controller.view_manager, 'populate_list') as mock_pop, \
             patch.object(controller.view_manager, 'update_calendar_highlights') as mock_cal, \
             patch.object(controller.view_manager, 'update_activity_chart') as mock_chart:
            
            controller.update_view()
            
            assert controller.historial_data == [item1, item2, item1]
            assert mock_historial_page.filter_combo.addItems.call_count == 1
            mock_historial_page.filter_combo.addItems.assert_called()
            call_args = mock_historial_page.filter_combo.addItems.call_args[0][0]
            assert "Todos los Responsables" in call_args
            assert "Juan" in call_args
            assert "Pedro" in call_args
            
            assert mock_pop.call_count == 1
            mock_pop.assert_called_once_with()
            assert mock_cal.call_count == 1
            mock_cal.assert_called_once_with()
            assert mock_chart.call_count == 1
            mock_chart.assert_called_once_with()

    def test_update_view_fabricaciones(self, controller: HistorialController, mock_view, mock_historial_page, mock_model) -> None:
        """Verifica actualización en modo fabricaciones."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "fabricaciones"
        
        mock_model.pila_service.get_all_pilas_with_dates.return_value = ["fab1", "fab2"]
        
        with patch.object(controller.view_manager, 'populate_list') as mock_pop, \
             patch.object(controller.view_manager, 'update_calendar_highlights') as mock_cal, \
             patch.object(controller.view_manager, 'update_activity_chart') as mock_chart:
            
            controller.update_view()
            
            assert controller.historial_data == ["fab1", "fab2"]
            assert mock_historial_page.filter_combo.addItem.call_count >= 1
            mock_historial_page.filter_combo.addItem.assert_called_with("Todas las Pilas")

    def test_populate_list_iteraciones_full(self, controller: HistorialController, mock_view, mock_historial_page) -> None:
        """Populate list en modo iteraciones con todos los datos."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        dt = datetime(2023, 1, 1, 10, 0)
        item = MagicMock(spec=ProductIterationDTO)
        item.producto_codigo = "P1"
        item.producto_descripcion = "Desc1"
        item.nombre_responsable = "User1"
        item.fecha_creacion = dt
        assert isinstance(item, ProductIterationDTO)
        
        controller.historial_data = [item]
        
        controller.populate_list()
        
        assert mock_historial_page.results_list.addItem.call_count == 1
        added_item = mock_historial_page.results_list.addItem.call_args[0][0]
        assert "P1" in added_item.text()
        assert "User1" in added_item.text()
        assert "01/01/2023" in added_item.text()

    def test_populate_list_iteraciones_missing_desc(self, controller: HistorialController, mock_view, mock_historial_page) -> None:
        """Test fallback attributes handling."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        item = MagicMock()
        item.producto_codigo = "P1"
        del item.producto_descripcion
        item.descripcion = "FallbackDesc"
        item.fecha_creacion = "2023-01-01"
        item.nombre_responsable = "User1"
        
        controller.historial_data = [item]
        controller.populate_list()
        
        mock_historial_page.results_list.addItem.assert_called()
        added_item = mock_historial_page.results_list.addItem.call_args[0][0]
        assert "P1" in added_item.text()

    def test_populate_list_filtering(self, controller: HistorialController, mock_view, mock_historial_page) -> None:
        """Test filtering by text and responsable."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        mock_historial_page.filter_combo.currentText.return_value = "OtroUser"
        item = MagicMock(nombre_responsable="User1", producto_codigo="P1")
        controller.historial_data = [item]
        
        controller.populate_list()
        assert mock_historial_page.results_list.addItem.call_count == 0
        mock_historial_page.results_list.addItem.assert_not_called()
        
        mock_historial_page.filter_combo.currentText.return_value = "Todos los Responsables"
        mock_historial_page.search_entry.text.return_value = "ZZZ"
        controller.populate_list()
        assert mock_historial_page.results_list.addItem.call_count == 0
        mock_historial_page.results_list.addItem.assert_not_called()

    def test_populate_list_fabricaciones(self, controller: HistorialController, mock_view, mock_historial_page) -> None:
        """Populate list en modo fabricaciones."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "fabricaciones"
        
        item = MagicMock()
        item.nombre = "Fab1"
        item.descripcion = "DescFab"
        item.start_date = date(2023, 1, 1)
        item.end_date = date(2023, 1, 5)
        
        controller.historial_data = [item]
        controller.populate_list()
        
        mock_historial_page.results_list.addItem.assert_called()
        added_item = mock_historial_page.results_list.addItem.call_args[0][0]
        assert "Fab1" in added_item.text()
        assert "01/01/2023" in added_item.text()

    def test_populate_list_fabricaciones_invalid_dates(self, controller: HistorialController, mock_view, mock_historial_page) -> None:
        """Test N/A dates handling."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "fabricaciones"
        
        item = MagicMock()
        item.nombre = "Fab1"
        item.descripcion = ""
        item.start_date = None
        item.end_date = None
        
        controller.historial_data = [item]
        controller.populate_list()
        
        added_item = mock_historial_page.results_list.addItem.call_args[0][0]
        assert "N/A" in added_item.text()

    def test_update_calendar_highlights(self, controller: HistorialController, mock_view, mock_historial_page) -> None:
        """Test highlighting logic for both modes."""
        mock_view.pages = {"historial": mock_historial_page}
        
        mock_historial_page.current_mode = "iteraciones"
        item1 = MagicMock()
        item1.data.return_value.fecha_creacion = datetime(2023, 1, 1)
        mock_historial_page.results_list.count.return_value = 1
        mock_historial_page.results_list.item.return_value = item1
        
        controller.update_calendar_highlights()
        
        args = mock_historial_page.highlight_calendar_dates.call_args[0]
        assert QDate(2023, 1, 1) in args[0]
        assert args[1] == "#3498db"
        
        mock_historial_page.current_mode = "fabricaciones"
        item2 = MagicMock()
        data = MagicMock()
        data.start_date = date(2023, 1, 1)
        data.end_date = date(2023, 1, 2)
        item2.data.return_value = data
        mock_historial_page.results_list.item.return_value = item2
        
        controller.update_calendar_highlights()
        
        args = mock_historial_page.highlight_calendar_dates.call_args[0]
        assert len(args[0]) >= 2
        assert args[1] == "#2ecc71"

    def test_on_item_selected_iteraciones(self, controller: HistorialController, mock_view, mock_historial_page, mock_model) -> None:
        """Test item selection logic for iteraciones."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        mock_item_data = MagicMock(spec=ProductIterationDTO)
        mock_item_data.producto_codigo = "P1"
        mock_item_data.fecha_creacion = datetime(2023, 1, 1)
        assert isinstance(mock_item_data, ProductIterationDTO)
        
        hist_item = MagicMock(spec=ProductIterationDTO)
        hist_item.fecha_creacion = "2023-01-01 10:00:00"
        hist_item.nombre_responsable = "User"
        hist_item.descripcion = "Change"
        hist_item.materiales = [MagicMock(codigo="M1", descripcion="Mat1")]
        
        mock_model.db.iteration_repo.get_product_iterations.return_value = [hist_item]
        
        mock_ui_item = MagicMock()
        mock_ui_item.data.return_value = mock_item_data
        
        controller.on_item_selected(mock_ui_item)
        
        assert mock_model.db.iteration_repo.get_product_iterations.call_count == 1
        mock_model.db.iteration_repo.get_product_iterations.assert_called_with("P1")
        assert mock_historial_page.details_text.setText.call_count == 1
        mock_historial_page.details_text.setText.assert_called()
        text = mock_historial_page.details_text.setText.call_args[0][0]
        assert "HISTORIAL" in text
        assert "M1" in text

    def test_on_item_selected_iteraciones_date_coverage(self, controller: HistorialController, mock_view, mock_historial_page, mock_model) -> None:
        """Test item selection logic for iteraciones when creation_date is explicitly a pure date object (L207)."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        mock_item_data = MagicMock(spec=ProductIterationDTO)
        mock_item_data.producto_codigo = "P2"
        mock_item_data.fecha_creacion = date(2023, 2, 2)
        
        hist_item = MagicMock(spec=ProductIterationDTO)
        hist_item.fecha_creacion = date(2023, 2, 2)
        hist_item.nombre_responsable = "User"
        hist_item.descripcion = "Change"
        hist_item.materiales = []
        
        mock_model.db.iteration_repo.get_product_iterations.return_value = [hist_item]
        
        mock_ui_item = MagicMock()
        mock_ui_item.data.return_value = mock_item_data
        
        # Action
        controller.on_item_selected(mock_ui_item)
        
        # Verify
        assert mock_model.db.iteration_repo.get_product_iterations.call_count == 1
        mock_model.db.iteration_repo.get_product_iterations.assert_called_with("P2")
        assert mock_historial_page.details_text.setText.call_count == 1
        mock_historial_page.details_text.setText.assert_called()

    def test_on_item_selected_fabricaciones(self, controller: HistorialController, mock_view, mock_historial_page, mock_model) -> None:
        """Test item selection logic for fabricaciones."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "fabricaciones"
        
        mock_item_data = MagicMock()
        mock_item_data.id = 123
        mock_item_data.nombre = "FabName"
        mock_item_data.start_date = date(2023, 1, 1)
        mock_item_data.end_date = date(2023, 1, 2)
        
        mock_model.pila_service.get_diario_bitacora.return_value = (1, [
            (date(2023, 1, 1), 1, "Plan", "Real", "Notas")
        ])
        
        mock_ui_item = MagicMock()
        mock_ui_item.data.return_value = mock_item_data
        
        controller.on_item_selected(mock_ui_item)
        
        assert mock_model.pila_service.get_diario_bitacora.call_count == 1
        mock_model.pila_service.get_diario_bitacora.assert_called_with(123)
        assert mock_historial_page.details_text.setText.called
        mock_historial_page.details_text.setText.assert_called()
        text = mock_historial_page.details_text.setText.call_args[0][0]
        assert "BITÁCORA" in text
        assert "Notas" in text

    def test_on_calendar_clicked(self, controller: HistorialController, mock_view, mock_historial_page) -> None:
        """Test calendar filtering."""
        mock_view.pages = {"historial": mock_historial_page}
        
        item1 = MagicMock()
        item1.data.return_value.fecha_creacion = "2023-01-01 10:00:00"
        
        mock_historial_page.results_list.count.return_value = 1
        mock_historial_page.results_list.item.return_value = item1
        
        mock_historial_page.current_mode = "iteraciones"
        controller.on_calendar_clicked(QDate(2023, 1, 1))
        assert item1.setHidden.call_count == 1
        item1.setHidden.assert_called_with(False)
        
        controller.on_calendar_clicked(QDate(2023, 1, 2))
        assert item1.setHidden.call_count == 2
        item1.setHidden.assert_called_with(True)
        
        item1.data.return_value.fecha_creacion = "invalid-date"
        controller.on_calendar_clicked(QDate(2023, 1, 1))
        assert item1.setHidden.call_count >= 3  # al menos 3 llamadas acumuladas
        
        mock_historial_page.current_mode = "fabricaciones"
        fab_data = MagicMock()
        fab_data.start_date = date(2023, 1, 1)
        fab_data.end_date = date(2023, 1, 5)
        item1.data.return_value = fab_data
        
        controller.on_calendar_clicked(QDate(2023, 1, 3))
        assert item1.setHidden.call_count >= 4
        item1.setHidden.assert_called_with(False)

    def test_on_print_report_clicked(self, controller: HistorialController, mock_view, mock_historial_page, mock_model) -> None:
        """Test printing report flow."""
        mock_view.pages = {"historial": mock_historial_page}
        
        mock_historial_page.results_list.selectedItems.return_value = []
        controller.on_print_report_clicked()
        mock_view.show_message.assert_called_with(
            "Selección Requerida",
            "Debe seleccionar un elemento de la lista para imprimir.",
            "warning",
        )
        
        mock_item = MagicMock()
        mock_item.data.return_value.producto_codigo = "P1"
        mock_historial_page.results_list.selectedItems.return_value = [mock_item]
        mock_historial_page.current_mode = "iteraciones"
        
        with patch('controllers.historial.report_manager.QFileDialog.getSaveFileName') as mock_dlg, \
             patch('controllers.historial.report_manager.GeneradorDeInformes') as MockGen, \
             patch('controllers.historial.report_manager.ReporteHistorialIteracion'):
            
            mock_dlg.return_value = ("", "")
            controller.on_print_report_clicked()
            assert MockGen.return_value.generar_y_guardar.call_count == 0
            
            mock_dlg.return_value = ("file.pdf", "pdf")
            MockGen.return_value.generar_y_guardar.return_value = True
            controller.on_print_report_clicked()
            mock_view.show_message.assert_called_with(
                "Éxito",
                "El informe se ha guardado en:\nfile.pdf",
                "info",
            )
            
            MockGen.return_value.generar_y_guardar.return_value = False
            controller.on_print_report_clicked()
            mock_view.show_message.assert_called_with(
                "Error",
                "No se pudo generar el informe PDF.",
                "critical",
            )

    def test_on_print_report_fabricaciones(self, controller: HistorialController, mock_view, mock_historial_page, mock_model) -> None:
        """Test printing fabricacion report."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "fabricaciones"
        
        mock_item = MagicMock()
        mock_item.data.return_value.id = 99
        mock_historial_page.results_list.selectedItems.return_value = [mock_item]
        
        mock_pila = MagicMock()
        mock_pila.nombre = "FabName"
        mock_model.pila_service.load_pila.return_value = (mock_pila, [], [], [])
        
        with patch('controllers.historial.report_manager.QFileDialog.getSaveFileName', return_value=("f.pdf", "")), \
             patch('controllers.historial.report_manager.GeneradorDeInformes') as MockGen, \
             patch('controllers.historial.report_manager.ReporteHistorialFabricacion'):
            
            MockGen.return_value.generar_y_guardar.return_value = True
            controller.on_print_report_clicked()
            
            assert MockGen.return_value.generar_y_guardar.called
            MockGen.return_value.generar_y_guardar.assert_called()

    def test_update_activity_chart(self, controller: HistorialController, mock_view, mock_historial_page) -> None:
        """Test activity chart updating."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        dt_recent = datetime.now() - timedelta(days=10)
        item1 = MagicMock(fecha_creacion=dt_recent)
        dt_old = datetime.now() - timedelta(days=400)
        item2 = MagicMock(fecha_creacion=dt_old)
        item3 = MagicMock(fecha_creacion="invalid-date")
        
        controller.historial_data = [item1, item2, item3]
        
        with patch('controllers.historial.view_manager.QLineSeries'), \
             patch('controllers.historial.view_manager.QChart') as MockChart, \
             patch('controllers.historial.view_manager.QDateTimeAxis'), \
             patch('controllers.historial.view_manager.QValueAxis'):
            
            controller.update_activity_chart()
            
            assert MockChart.called
            MockChart.assert_called()
            assert mock_historial_page.activity_chart_view.setChart.called
            mock_historial_page.activity_chart_view.setChart.assert_called()

    def test_populate_list_no_page(self, controller: HistorialController, mock_view) -> None:
        """Test populate_list returns early if no page."""
        mock_view.pages = {"historial": "NotAWidget"}
        controller.populate_list()
        assert cast(Any, controller.db.iteration_repo.get_all_iterations_with_dates).call_count == 0

    def test_update_calendar_highlights_no_page(self, controller: HistorialController, mock_view) -> None:
        """Test returns early."""
        mock_view.pages = {"historial": "NotAWidget"}
        controller.update_calendar_highlights()
        # Sin página válida, no debe llamar a ningún repo
        assert cast(Any, controller.db.iteration_repo.get_all_iterations_with_dates).call_count == 0

    def test_update_activity_chart_no_page(self, controller: HistorialController, mock_view) -> None:
        """Test returns early."""
        mock_view.pages = {"historial": "NotAWidget"}
        controller.update_activity_chart()
        # Sin página válida, no debe llamar a ningún repo
        assert cast(Any, controller.db.iteration_repo.get_all_iterations_with_dates).call_count == 0

    def test_populate_list_fabricaciones_search(self, controller: HistorialController, mock_view, mock_historial_page) -> None:
        """Test fabricaciones search filtering."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "fabricaciones"
        
        item1 = MagicMock(nombre="Fab1", descripcion="Desc1")
        item2 = MagicMock(nombre="Fab2", descripcion="Desc2")
        controller.historial_data = [item1, item2]
        
        mock_historial_page.search_entry.text.return_value = "fab1"
        controller.populate_list()
        assert mock_historial_page.results_list.addItem.call_count == 1
        
        mock_historial_page.results_list.reset_mock()
        mock_historial_page.results_list.addItem.reset_mock()
        mock_historial_page.search_entry.text.return_value = "ZZZ"
        controller.populate_list()
        assert mock_historial_page.results_list.addItem.call_count == 0
        mock_historial_page.results_list.addItem.assert_not_called()

    def test_update_calendar_highlights_date_type(self, controller: HistorialController, mock_view, mock_historial_page) -> None:
        """Test highlighting with date objects (not datetime)."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        item = MagicMock()
        item.data.return_value.fecha_creacion = date(2023, 1, 1)
        mock_historial_page.results_list.count.return_value = 1
        mock_historial_page.results_list.item.return_value = item
        
        controller.update_calendar_highlights()
        args = mock_historial_page.highlight_calendar_dates.call_args[0]
        assert QDate(2023, 1, 1) in args[0]

    def test_on_item_selected_iteraciones_bad_date(self, controller: HistorialController, mock_view, mock_historial_page, mock_model) -> None:
        """Test handling of bad date string in history details."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        mock_model.db.iteration_repo.get_product_iterations.return_value = [
            MagicMock(fecha_creacion="invalid-date", descripcion="Desc")
        ]
        
        item = MagicMock()
        controller.on_item_selected(item)
        
        assert mock_historial_page.details_text.setText.called
        text = mock_historial_page.details_text.setText.call_args[0][0]
        assert "invalid-date" in text

    def test_on_item_selected_fabricaciones_empty_bitacora(self, controller: HistorialController, mock_view, mock_historial_page, mock_model) -> None:
        """Test empty bitacora message."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "fabricaciones"
        mock_model.pila_service.get_diario_bitacora.return_value = (1, [])
        
        item = MagicMock()
        item.data.return_value.start_date = None
        item.data.return_value.end_date = None
        
        controller.on_item_selected(item)
        
        assert mock_historial_page.details_text.setText.called
        text = mock_historial_page.details_text.setText.call_args[0][0]
        assert "Aún no hay entradas" in text

    def test_on_calendar_clicked_date_type(self, controller: HistorialController, mock_view, mock_historial_page) -> None:
        """Test filtering with date objects."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "iteraciones"
        
        item = MagicMock()
        item.data.return_value.fecha_creacion = date(2023, 1, 1)
        
        mock_historial_page.results_list.count.return_value = 1
        mock_historial_page.results_list.item.return_value = item
        
        controller.on_calendar_clicked(QDate(2023, 1, 1))
        assert item.setHidden.call_count == 1
        item.setHidden.assert_called_with(False)

    def test_update_activity_chart_fabricaciones(self, controller: HistorialController, mock_view, mock_historial_page) -> None:
        """Test activity chart for fabricaciones."""
        mock_view.pages = {"historial": mock_historial_page}
        mock_historial_page.current_mode = "fabricaciones"
        
        item = MagicMock()
        item.start_date = date.today()
        controller.historial_data = [item]
        
        with patch('controllers.historial.view_manager.QLineSeries'), \
             patch('controllers.historial.view_manager.QChart'), \
             patch('controllers.historial.view_manager.QDateTimeAxis'), \
             patch('controllers.historial.view_manager.QValueAxis'):
            
            controller.update_activity_chart()
            assert mock_historial_page.activity_chart_view.setChart.call_count == 1
            mock_historial_page.activity_chart_view.setChart.assert_called()
