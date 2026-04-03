"""
Tests unitarios exhaustivos para ReportController.
Objetivo: 100% de cobertura y verificación de todas las ramas lógicas, incluyendo calidad 100/100.
"""
import pytest
from unittest.mock import MagicMock, patch, ANY, create_autospec
from datetime import datetime
from typing import Any, cast

from controllers.report_controller import ReportController
from core.services.worker_service import WorkerService
from core.services.product_service import ProductService
from core.services.pila_service import PilaService
from core.dtos import ProductIterationDTO, PilaDTO, FabricacionDTO, ComponenteDTO

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_model():
    """Mock del modelo con servicios usando create_autospec."""
    model = MagicMock(spec=['db', 'worker_service', 'product_service', 'pila_service'])
    item = MagicMock(spec=ProductIterationDTO)
    item.fecha_creacion = datetime(2025, 1, 1)
    item.tiempo_estimado_total = 120
    model.db = MagicMock(spec=['product_repo', 'iteration_repo'])
    model.db.product_repo = MagicMock(spec=['get_product_iterations'])
    model.db.iteration_repo = MagicMock(spec=['get_product_iterations'])
    model.worker_service = create_autospec(WorkerService, instance=True)
    model.product_service = create_autospec(ProductService, instance=True)
    model.pila_service = create_autospec(PilaService, instance=True)
    model.db.product_repo.get_product_iterations.return_value = [item]
    
    pila_obj = MagicMock(spec=PilaDTO)
    pila_obj.id = 1
    pila_obj.nombre = "Test Pila"
    model.pila_service.load_pila.return_value = (pila_obj, [], [], [])
    
    model.pila_service.get_diario_bitacora.return_value = (None, [])
    return model

@pytest.fixture
def mock_view():
    """Mock de la vista."""
    view = MagicMock(spec=['pages', 'statusBar', 'show_message'])
    view.pages = {}
    view.statusBar.return_value = MagicMock(spec=['showMessage', 'clearMessage'])
    return view

@pytest.fixture
def mock_schedule():
    """Mock de horarios."""
    return MagicMock(spec=['get_working_days'])

@pytest.fixture
def report_controller(mock_model, mock_view, mock_schedule):
    """Instancia del controlador."""
    logger = MagicMock(spec=['debug', 'info', 'error', 'warning', 'critical'])
    return ReportController(
        db=mock_model.db, 
        view=mock_view, 
        worker_service=mock_model.worker_service,
        product_service=mock_model.product_service,
        pila_service=mock_model.pila_service,
        schedule_manager=mock_schedule, 
        logger=logger
    )

@pytest.mark.unit
class TestReportControllerComprehensive:
    """Suite exhaustiva para ReportController."""

    def test_initialize(self, report_controller: ReportController) -> None:
        """Verifica inicialización."""
        report_controller.initialize()
        assert cast(Any, report_controller.logger).debug.call_count >= 1

    def test_cleanup(self, report_controller: ReportController) -> None:
        """Verifica limpieza."""
        report_controller.update_simulation_data([{}], [], [], 1)
        assert report_controller.last_simulation_results is not None
        report_controller.cleanup()
        assert report_controller.last_simulation_results is None
        assert cast(Any, report_controller.logger).debug.call_count >= 1

    def test_update_simulation_data(self, report_controller: ReportController) -> None:
        """Verifica actualización de datos."""
        res: list[dict[str, Any]] = [{}]
        audit: list[Any] = [{"a": 1}]
        flow: list[dict[str, Any]] = [{"s": 1}]
        units: int = 10
        report_controller.update_simulation_data(res, audit, flow, units, flexible_workers=3)
        assert report_controller.last_simulation_results == res
        assert report_controller.last_audit_log == audit
        assert report_controller.last_production_flow == flow
        assert report_controller.last_units_calculated == units
        assert report_controller.last_flexible_workers_needed == 3

    def test_on_generar_informe_no_selection(self, report_controller: ReportController) -> None:
        """Error si no hay selección."""
        report_controller.selected_report_item = None
        report_controller.on_generar_informe_clicked("any")
        assert report_controller.view.show_message.call_count >= 1
        report_controller.view.show_message.assert_called_with("Error", ANY, "warning")

    def test_on_generar_informe_historial_pila_pdf_no_sim_data(self, report_controller: ReportController) -> None:
        """Error si no hay datos de simulación para PDF."""
        mock_item = MagicMock(spec=['code'])
        mock_item.code = "T"
        report_controller.selected_report_item = mock_item
        report_controller.last_simulation_results = None
        report_controller.on_generar_informe_clicked("historial_pila_pdf")
        assert report_controller.view.show_message.call_count >= 1
        report_controller.view.show_message.assert_called_with("Error", ANY, "warning")

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    @patch('controllers.report_controller.GeneradorDeInformes', autospec=True)
    @patch('controllers.report_controller.ReporteHistorialFabricacion', autospec=True)
    def test_on_generar_informe_historial_pila_pdf_success(self, mock_strat, mock_gen, mock_file, report_controller: ReportController) -> None:
        """Generación exitosa de PDF de pila."""
        mock_item = MagicMock(spec=['code'])
        mock_item.code = "T"
        report_controller.selected_report_item = mock_item
        report_controller.last_simulation_results = [{}]
        mock_file.return_value = ("/tmp/t.pdf", "pdf")
        mock_gen_inst = mock_gen.return_value
        mock_gen_inst.generar_y_guardar.return_value = True
        
        report_controller.on_generar_informe_clicked("historial_pila_pdf")
        
        assert mock_gen_inst.generar_y_guardar.call_count == 1
        mock_gen_inst.generar_y_guardar.assert_called_once_with(ANY, "/tmp/t.pdf")
        assert report_controller.view.show_message.call_count >= 1
        report_controller.view.show_message.assert_called_with("Éxito", ANY, "info")

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    @patch('controllers.report_controller.GeneradorDeInformes', autospec=True)
    @patch('controllers.report_controller.ReporteHistorialIteracion', autospec=True)
    def test_on_generar_informe_historial_iteraciones_success(self, mock_strat, mock_gen, mock_file, report_controller: ReportController) -> None:
        """Generación exitosa de PDF de iteraciones."""
        mock_item = MagicMock(spec=['code', 'description', 'get'])
        mock_item.code = "P001"
        mock_item.description = "D"
        mock_item.get.side_effect = lambda k, d=None: getattr(mock_item, k, d)
        report_controller.selected_report_item = mock_item
        mock_file.return_value = ("/tmp/t.pdf", "pdf")
        mock_gen_inst = mock_gen.return_value
        mock_gen_inst.generar_y_guardar.return_value = True
        
        report_controller.on_generar_informe_clicked("historial_iteraciones")
        
        assert mock_gen_inst.generar_y_guardar.call_count == 1
        mock_gen_inst.generar_y_guardar.assert_called_once_with(ANY, "/tmp/t.pdf")
        iters_call = cast(Any, report_controller.db.iteration_repo.get_product_iterations)
        assert iters_call.call_count >= 1
        iters_call.assert_called_with("P001")

    def test_export_to_excel_no_data(self, report_controller: ReportController) -> None:
        """Error excel sin datos."""
        report_controller.last_simulation_results = None
        assert report_controller.on_export_to_excel_clicked() is False
        assert report_controller.view.show_message.call_count >= 1
        report_controller.view.show_message.assert_called_with("Sin Datos", ANY, "warning")

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    @patch('controllers.report_controller.GeneradorDeInformes', autospec=True)
    @patch('controllers.report_controller.ReportePilaFabricacionExcelMejorado', autospec=True)
    @patch('controllers.report_controller.QApplication.processEvents', autospec=True)
    def test_export_to_excel_success(self, mock_pe, mock_strat, mock_gen, mock_file, report_controller: ReportController) -> None:
        """Excel exitoso con ordenación y datos de pila."""
        report_controller.last_simulation_results = [
            {"Inicio": datetime(2025, 2, 1), "Tarea": "B"},
            {"Inicio": datetime(2025, 1, 1), "Tarea": "A"}
        ]
        mock_file.return_value = ("/tmp/t.xlsx", "xlsx")
        mock_gen_inst = mock_gen.return_value
        mock_gen_inst.generar_y_guardar.return_value = True
        
        calc_page = MagicMock(spec=['pila_content_table'])
        mock_item = MagicMock(spec=['text'])
        mock_item.text.return_value = "Lote 1"
        calc_page.pila_content_table = MagicMock(spec=['rowCount', 'item'])
        calc_page.pila_content_table.rowCount.return_value = 1
        calc_page.pila_content_table.item.return_value = mock_item
        
        assert report_controller.on_export_to_excel_clicked(calc_page) is True
        assert mock_gen_inst.generar_y_guardar.call_count == 1
        mock_gen_inst.generar_y_guardar.assert_called_once_with(ANY, "/tmp/t.xlsx")
        # Verificar ordenación: A (enero) antes que B (febrero)
        call_args = mock_gen_inst.generar_y_guardar.call_args[0][0]
        assert call_args["data"][0]["Tarea"] == "A"

    def test_export_gantt_to_pdf_no_data(self, report_controller: ReportController) -> None:
        """Error Gantt sin datos."""
        report_controller.last_simulation_results = None
        assert report_controller.on_export_gantt_to_pdf_clicked() is False

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    @patch('controllers.report_controller.GeneradorDeInformes', autospec=True)
    @patch('controllers.report_controller.ReporteHistorialFabricacion', autospec=True)
    def test_export_gantt_to_pdf_success(self, mock_strat, mock_gen, mock_file, report_controller: ReportController) -> None:
        """Gantt PDF exitoso."""
        report_controller.last_simulation_results = [{}]
        report_controller.last_audit_log = [{"event": 1}] # No vacío
        mock_file.return_value = ("/tmp/g.pdf", "pdf")
        mock_gen_inst = mock_gen.return_value
        mock_gen_inst.generar_y_guardar.return_value = True
        
        assert report_controller.on_export_gantt_to_pdf_clicked() is True
        assert mock_gen_inst.generar_y_guardar.call_count == 1
        mock_gen_inst.generar_y_guardar.assert_called_once_with(ANY, "/tmp/g.pdf")

    def test_print_historial_report_no_selection(self, report_controller: ReportController) -> None:
        """Error historial sin selección."""
        widget = MagicMock(spec=['results_list'])
        widget.results_list = MagicMock(spec=['selectedItems'])
        widget.results_list.selectedItems.return_value = []
        assert report_controller.on_print_historial_report_clicked(widget) is False

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    @patch('controllers.report_controller.GeneradorDeInformes', autospec=True)
    @patch('controllers.report_controller.ReporteHistorialFabricacion', autospec=True)
    def test_print_historial_report_fabricaciones_success(self, mock_strat, mock_gen, mock_file, report_controller: ReportController) -> None:
        """Historial fabricaciones exitoso."""
        mock_data = MagicMock(spec=['id'])
        mock_data.id = 1
        mock_item = MagicMock(spec=['data'])
        mock_item.data.return_value = mock_data
        widget = MagicMock(spec=['results_list', 'current_mode'])
        widget.results_list = MagicMock(spec=['selectedItems'])
        widget.results_list.selectedItems.return_value = [mock_item]
        widget.current_mode = "fabricaciones"
        
        mock_file.return_value = ("/tmp/f.pdf", "pdf")
        mock_gen_inst = mock_gen.return_value
        mock_gen_inst.generar_y_guardar.return_value = True
        
        assert report_controller.on_print_historial_report_clicked(widget) is True
        load_pila = cast(Any, report_controller.pila_service.load_pila)
        assert load_pila.call_count == 1
        load_pila.assert_called_with(1)

    def test_export_to_excel_exception(self, report_controller: ReportController) -> None:
        """Manejo de excepción en excel."""
        report_controller.last_simulation_results = [{}]
        with patch('controllers.report_controller.QFileDialog.getSaveFileName', side_effect=Exception("Crash")):
            with patch.object(report_controller, 'handle_error') as mock_handle:
                assert report_controller.on_export_to_excel_clicked() is False
                mock_handle.assert_called()

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    @patch('controllers.report_controller.GeneradorDeInformes', autospec=True)
    @patch('controllers.report_controller.ReporteHistorialFabricacion', autospec=True)
    def test_on_generar_informe_historial_pila_pdf_failure(self, mock_strat, mock_gen, mock_file, report_controller: ReportController) -> None:
        """Fallo en generación de PDF de pila."""
        mock_item = MagicMock(spec=['code'])
        mock_item.code = "T"
        report_controller.selected_report_item = mock_item
        report_controller.last_simulation_results = [{}]
        mock_file.return_value = ("/tmp/t.pdf", "pdf")
        mock_gen.return_value.generar_y_guardar.return_value = False
        report_controller.on_generar_informe_clicked("historial_pila_pdf")
        assert report_controller.view.show_message.call_count >= 1
        report_controller.view.show_message.assert_called_with("Error", ANY, "critical")

    def test_on_generar_informe_excel_noop(self, report_controller: ReportController) -> None:
        """Caso excel en generar_informe es no-op."""
        mock_item = MagicMock(spec=['code'])
        mock_item.code = "T"
        report_controller.selected_report_item = mock_item
        try:
            report_controller.on_generar_informe_clicked("pila_fabricacion_excel")
        except Exception:
            pytest.fail("on_generar_informe_clicked no debería propagar excepciones en modo excel no-op")
        assert report_controller.selected_report_item is mock_item

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    @patch('controllers.report_controller.GeneradorDeInformes', autospec=True)
    @patch('controllers.report_controller.ReporteHistorialIteracion', autospec=True)
    def test_on_generar_informe_historial_iteraciones_failure(self, mock_strat, mock_gen, mock_file, report_controller: ReportController) -> None:
        """Fallo en generación de PDF de iteraciones."""
        mock_item = MagicMock(spec=['code', 'description', 'get'])
        mock_item.code = "P001"
        mock_item.get.side_effect = lambda k, d=None: getattr(mock_item, k, d)
        report_controller.selected_report_item = mock_item
        mock_file.return_value = ("/tmp/t.pdf", "pdf")
        mock_gen.return_value.generar_y_guardar.return_value = False
        report_controller.on_generar_informe_clicked("historial_iteraciones")
        assert report_controller.view.show_message.call_count >= 1
        report_controller.view.show_message.assert_called_with("Error", ANY, "critical")

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    def test_export_to_excel_cancelled(self, mock_file, report_controller: ReportController) -> None:
        """Cancelación de diálogo excel."""
        report_controller.last_simulation_results = [{}]
        mock_file.return_value = ("", "")
        assert report_controller.on_export_to_excel_clicked() is False

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    @patch('controllers.report_controller.GeneradorDeInformes', autospec=True)
    @patch('controllers.report_controller.ReportePilaFabricacionExcelMejorado', autospec=True)
    def test_export_to_excel_gen_failure(self, mock_strat, mock_gen, mock_file, report_controller: ReportController) -> None:
        """Fallo del generador en excel."""
        report_controller.last_simulation_results = [{}]
        mock_file.return_value = ("/tmp/t.xlsx", "xlsx")
        mock_gen.return_value.generar_y_guardar.return_value = False
        assert report_controller.on_export_to_excel_clicked() is False
        assert report_controller.view.show_message.call_count >= 1
        report_controller.view.show_message.assert_called_with("Error", ANY, "critical")

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    def test_export_gantt_to_pdf_cancelled(self, mock_file, report_controller: ReportController) -> None:
        """Cancelación de diálogo PDF Gantt."""
        report_controller.last_simulation_results = [{}]
        report_controller.last_audit_log = [{}]
        mock_file.return_value = ("", "")
        assert report_controller.on_export_gantt_to_pdf_clicked() is False

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    @patch('controllers.report_controller.GeneradorDeInformes', autospec=True)
    @patch('controllers.report_controller.ReporteHistorialFabricacion', autospec=True)
    def test_export_gantt_to_pdf_gen_failure(self, mock_strat, mock_gen, mock_file, report_controller: ReportController) -> None:
        """Fallo del generador en PDF Gantt."""
        report_controller.last_simulation_results = [{}]
        report_controller.last_audit_log = [{}]
        mock_file.return_value = ("/tmp/g.pdf", "pdf")
        mock_gen.return_value.generar_y_guardar.return_value = False
        assert report_controller.on_export_gantt_to_pdf_clicked() is False
        assert report_controller.view.show_message.call_count >= 1
        report_controller.view.show_message.assert_called_with("Error", ANY, "critical")

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    @patch('controllers.report_controller.GeneradorDeInformes', autospec=True)
    @patch('controllers.report_controller.ReporteHistorialFabricacion', autospec=True)
    def test_export_gantt_to_pdf_with_metadata(self, mock_strat, mock_gen, mock_file, report_controller: ReportController) -> None:
        """Gantt PDF con extracción de metadatos de calc_page."""
        report_controller.last_simulation_results = [{}]
        report_controller.last_audit_log = [{"event": 1}]
        mock_file.return_value = ("/tmp/g.pdf", "pdf")
        mock_gen.return_value.generar_y_guardar.return_value = True
        
        calc_page = MagicMock(spec=['pila_content_table'])
        mock_item = MagicMock(spec=['text'])
        mock_item.text.return_value = "PILA-XYZ"
        calc_page.pila_content_table = MagicMock(spec=['rowCount', 'item'])
        calc_page.pila_content_table.rowCount.return_value = 1
        calc_page.pila_content_table.item.return_value = mock_item
        
        assert report_controller.on_export_gantt_to_pdf_clicked(calc_page) is True
        # Verificar que se extrajo el código
        call_args = mock_gen.return_value.generar_y_guardar.call_args[0][0]
        assert call_args["meta_data"]["code"] == "PILA-XYZ"

    def test_export_gantt_to_pdf_exception(self, report_controller: ReportController) -> None:
        """Manejo de excepción en Gantt PDF."""
        report_controller.last_simulation_results = [{}]
        report_controller.last_audit_log = [{"event": 1}]
        with patch('controllers.report_controller.QFileDialog.getSaveFileName', side_effect=Exception("Crash")):
            with patch.object(report_controller, 'handle_error') as mock_handle:
                assert report_controller.on_export_gantt_to_pdf_clicked() is False
                assert mock_handle.call_count >= 1
                mock_handle.assert_called()

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    def test_print_historial_report_iteraciones_cancelled(self, mock_file, report_controller: ReportController) -> None:
        """Cancelación de diálogo historial iteraciones."""
        mock_data = MagicMock(spec=['producto_codigo'])
        mock_data.producto_codigo = "T"
        mock_item = MagicMock(spec=['data'])
        mock_item.data.return_value = mock_data
        widget = MagicMock(spec=['results_list', 'current_mode'])
        widget.results_list = MagicMock(spec=['selectedItems'])
        widget.results_list.selectedItems.return_value = [mock_item]
        widget.current_mode = "iteraciones"
        mock_file.return_value = ("", "")
        assert report_controller.on_print_historial_report_clicked(widget) is False

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    def test_print_historial_report_fabricaciones_cancelled(self, mock_file, report_controller: ReportController) -> None:
        """Cancelación de diálogo historial fabricaciones."""
        mock_data = MagicMock(spec=['id'])
        mock_data.id = 1
        mock_item = MagicMock(spec=['data'])
        mock_item.data.return_value = mock_data
        widget = MagicMock(spec=['results_list', 'current_mode'])
        widget.results_list = MagicMock(spec=['selectedItems'])
        widget.results_list.selectedItems.return_value = [mock_item]
        widget.current_mode = "fabricaciones"
        mock_file.return_value = ("", "")
        assert report_controller.on_print_historial_report_clicked(widget) is False

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    @patch('controllers.report_controller.GeneradorDeInformes', autospec=True)
    @patch('controllers.report_controller.ReporteHistorialFabricacion', autospec=True)
    def test_print_historial_report_fabricaciones_gen_failure(self, mock_strat, mock_gen, mock_file, report_controller: ReportController) -> None:
        """Fallo del generador en historial fabricaciones."""
        mock_data = MagicMock(spec=['id'])
        mock_data.id = 1
        mock_item = MagicMock(spec=['data'])
        mock_item.data.return_value = mock_data
        widget = MagicMock(spec=['results_list', 'current_mode'])
        widget.results_list = MagicMock(spec=['selectedItems'])
        widget.results_list.selectedItems.return_value = [mock_item]
        widget.current_mode = "fabricaciones"
        mock_file.return_value = ("/tmp/f.pdf", "pdf")
        mock_gen.return_value.generar_y_guardar.return_value = False
        assert report_controller.on_print_historial_report_clicked(widget) is False
        assert report_controller.view.show_message.call_count >= 1
        report_controller.view.show_message.assert_called_with("Error", ANY, "critical")

    @patch('controllers.report_controller.QFileDialog.getSaveFileName')
    @patch('controllers.report_controller.GeneradorDeInformes')
    @patch('controllers.report_controller.ReporteHistorialIteracion')
    def test_print_historial_report_iteraciones_success(self, mock_strat, mock_gen, mock_file, report_controller: ReportController) -> None:
        """Historial iteraciones exitoso."""
        mock_data = MagicMock(spec=['producto_codigo', 'descripcion'])
        mock_data.producto_codigo = "P001"
        mock_data.descripcion = "Desc"
        mock_item = MagicMock(spec=['data'])
        mock_item.data.return_value = mock_data
        widget = MagicMock(spec=['results_list', 'current_mode'])
        widget.results_list = MagicMock(spec=['selectedItems'])
        widget.results_list.selectedItems.return_value = [mock_item]
        widget.current_mode = "iteraciones"
        
        mock_file.return_value = ("/tmp/i.pdf", "pdf")
        mock_gen.return_value.generar_y_guardar.return_value = True
        
        assert report_controller.on_print_historial_report_clicked(widget) is True
        iters_call = cast(Any, report_controller.db.iteration_repo.get_product_iterations)
        assert iters_call.call_count >= 1
        iters_call.assert_called_with("P001")

    def test_print_historial_report_exception(self, report_controller: ReportController) -> None:
        """Manejo de excepción en historial."""
        widget = MagicMock(spec=['results_list'])
        widget.results_list = MagicMock(spec=['selectedItems'])
        widget.results_list.selectedItems.side_effect = Exception("Crash")
        with patch.object(report_controller, 'handle_error') as mock_handle:
            assert report_controller.on_print_historial_report_clicked(widget) is False
            assert mock_handle.call_count >= 1
            mock_handle.assert_called()
