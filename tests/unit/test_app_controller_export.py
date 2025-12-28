"""
Tests unitarios para AppController - Exportación de datos.

Cobertura objetivo: Métodos de exportación a Excel, PDF y archivos de log.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from controllers.app_controller import AppController
from ui.widgets import CalculateTimesWidget


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_app():
    """Crea AppController con dependencias mockeadas."""
    model = MagicMock()
    
    view = MagicMock()
    view.pages = {}
    view.show_message = MagicMock()
    view.statusBar().showMessage = MagicMock()
    view.statusBar().clearMessage = MagicMock()
    
    config = MagicMock()
    
    with patch('controllers.app_controller.CameraManager'), \
         patch('controllers.app_controller.QrGenerator'), \
         patch('controllers.app_controller.LabelManager'), \
         patch('controllers.app_controller.LabelCounterRepository'):
        ctrl = AppController(model, view, config)
        return ctrl


@pytest.fixture
def mock_calc_page():
    """Mock de CalculateTimesWidget."""
    page = MagicMock(spec=CalculateTimesWidget)
    page.pila_content_table = MagicMock()
    page.pila_content_table.rowCount.return_value = 1
    page.pila_content_table.item.return_value = MagicMock(text=MagicMock(return_value="PILA001"))
    page.last_audit = True
    page.audit_log_display = MagicMock()
    page.audit_log_display.toHtml.return_value = "<html>Audit Log</html>"
    return page


# =============================================================================
# TESTS: _on_export_to_excel_clicked
# =============================================================================

class TestOnExportToExcelClicked:
    """Tests para _on_export_to_excel_clicked."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._on_export_to_excel_clicked)

    def test_shows_warning_without_results(self, mock_app, mock_calc_page):
        """Verifica warning cuando no hay resultados."""
        mock_app.view.pages = {"calculate": mock_calc_page}
        mock_app.last_simulation_results = None
        
        mock_app._on_export_to_excel_clicked()
        
        mock_app.view.show_message.assert_called_with(
            "Sin Datos", "No hay resultados de simulación para exportar.", "warning"
        )

    def test_returns_early_on_file_dialog_cancel(self, mock_app, mock_calc_page):
        """Verifica que retorna si el usuario cancela el diálogo."""
        mock_app.view.pages = {"calculate": mock_calc_page}
        mock_app.last_simulation_results = [{"task": "test"}]
        
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
            mock_dialog.return_value = ("", "")  # Usuario canceló
            
            mock_app._on_export_to_excel_clicked()
            
            # No debería mostrar mensaje de éxito
            assert mock_app.view.show_message.call_count == 0

    def test_export_success(self, mock_app, mock_calc_page):
        """Verifica exportación exitosa a Excel."""
        mock_app.view.pages = {"calculate": mock_calc_page}
        mock_app.last_simulation_results = [
            {"Inicio": datetime.now(), "Tarea": "Test"}
        ]
        mock_app.last_audit_log = []
        mock_app.last_production_flow = []
        mock_app.last_units_calculated = 1
        
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog, \
             patch('controllers.app_controller.ReportePilaFabricacionExcelMejorado'), \
             patch('controllers.app_controller.GeneradorDeInformes') as MockGen, \
             patch('PyQt6.QtWidgets.QApplication.processEvents'):
            
            mock_dialog.return_value = ("/tmp/test.xlsx", "")
            mock_gen_instance = MockGen.return_value
            mock_gen_instance.generar_y_guardar.return_value = True
            
            mock_app._on_export_to_excel_clicked()
            
            mock_app.view.show_message.assert_called()
            assert "Éxito" in str(mock_app.view.show_message.call_args)

    def test_handles_export_error(self, mock_app, mock_calc_page):
        """Verifica manejo de errores durante exportación."""
        mock_app.view.pages = {"calculate": mock_calc_page}
        mock_app.last_simulation_results = [{"task": "test"}]
        mock_app.last_audit_log = []
        mock_app.last_production_flow = []
        mock_app.last_units_calculated = 1
        
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog, \
             patch('controllers.app_controller.ReportePilaFabricacionExcelMejorado') as MockRepo, \
             patch('PyQt6.QtWidgets.QApplication.processEvents'):
            
            mock_dialog.return_value = ("/tmp/test.xlsx", "")
            MockRepo.side_effect = Exception("Test error")
            
            mock_app._on_export_to_excel_clicked()
            
            # Debería mostrar error crítico
            mock_app.view.show_message.assert_called()


# =============================================================================
# TESTS: _on_export_gantt_to_pdf_clicked
# =============================================================================

class TestOnExportGanttToPdfClicked:
    """Tests para _on_export_gantt_to_pdf_clicked."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._on_export_gantt_to_pdf_clicked)

    def test_shows_warning_without_results(self, mock_app):
        """Verifica warning cuando no hay resultados."""
        mock_app.last_simulation_results = None
        mock_app.last_audit_log = None
        
        mock_app._on_export_gantt_to_pdf_clicked()
        
        mock_app.view.show_message.assert_called_with(
            "Sin Datos", "Debe ejecutar una simulación completa primero.", "warning"
        )

    def test_returns_early_on_dialog_cancel(self, mock_app, mock_calc_page):
        """Verifica que retorna si el usuario cancela."""
        mock_app.view.pages = {"calculate": mock_calc_page}
        mock_app.last_simulation_results = [{}]
        mock_app.last_audit_log = [{}]
        
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
            mock_dialog.return_value = ("", "")
            
            mock_app._on_export_gantt_to_pdf_clicked()
            
            assert mock_app.view.show_message.call_count == 0

    def test_export_pdf_success(self, mock_app, mock_calc_page):
        """Verifica exportación exitosa a PDF."""
        mock_app.view.pages = {"calculate": mock_calc_page}
        mock_app.last_simulation_results = [{"task": "test"}]
        mock_app.last_audit_log = [{}]
        mock_app.last_production_flow = []
        
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog, \
             patch('controllers.app_controller.ReporteHistorialFabricacion'), \
             patch('controllers.app_controller.GeneradorDeInformes') as MockGen:
            
            mock_dialog.return_value = ("/tmp/gantt.pdf", "")
            mock_gen_instance = MockGen.return_value
            mock_gen_instance.generar_y_guardar.return_value = True
            
            mock_app._on_export_gantt_to_pdf_clicked()
            
            mock_app.view.show_message.assert_called()

    def test_export_pdf_failure(self, mock_app, mock_calc_page):
        """Verifica manejo de fallo en exportación PDF."""
        mock_app.view.pages = {"calculate": mock_calc_page}
        mock_app.last_simulation_results = [{}]
        mock_app.last_audit_log = [{}]
        
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog, \
             patch('controllers.app_controller.ReporteHistorialFabricacion'), \
             patch('controllers.app_controller.GeneradorDeInformes') as MockGen:
            
            mock_dialog.return_value = ("/tmp/gantt.pdf", "")
            mock_gen_instance = MockGen.return_value
            mock_gen_instance.generar_y_guardar.return_value = False
            
            mock_app._on_export_gantt_to_pdf_clicked()
            
            mock_app.view.show_message.assert_called_with("Error", "No se pudo generar el informe PDF.", "critical")


# =============================================================================
# TESTS: _on_export_audit_log
# =============================================================================

class TestOnExportAuditLog:
    """Tests para _on_export_audit_log."""

    def test_method_exists(self, mock_app):
        """Verifica que el método existe."""
        assert callable(mock_app._on_export_audit_log)

    def test_shows_warning_without_data(self, mock_app, mock_calc_page):
        """Verifica warning cuando no hay log."""
        mock_calc_page.last_audit = None
        mock_app.view.pages = {"calculate": mock_calc_page}
        
        # Parchear isinstance para que retorne True
        with patch('controllers.app_controller.isinstance', return_value=True):
            mock_app._on_export_audit_log()
        
            mock_app.view.show_message.assert_called_with(
                "Sin Datos", "No hay un log de auditoría para exportar.", "warning"
            )

    def test_returns_early_on_cancel(self, mock_app, mock_calc_page):
        """Verifica que retorna al cancelar diálogo."""
        mock_calc_page.last_audit = True
        mock_app.view.pages = {"calculate": mock_calc_page}
        
        with patch('controllers.app_controller.isinstance', return_value=True), \
             patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
            
            mock_dialog.return_value = ("", "")
            
            mock_app._on_export_audit_log()
            
            # No debería intentar escribir archivo
            assert mock_app.view.show_message.call_count == 0

    def test_export_success(self, mock_app, mock_calc_page):
        """Verifica exportación exitosa del log."""
        mock_calc_page.last_audit = True
        mock_calc_page.audit_log_display.toHtml.return_value = "<html>Test</html>"
        mock_app.view.pages = {"calculate": mock_calc_page}
        
        with patch('controllers.app_controller.isinstance', return_value=True), \
             patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_dialog.return_value = ("/tmp/audit.html", "")
            
            mock_app._on_export_audit_log()
            
            mock_open.assert_called()
            mock_app.view.show_message.assert_called()

    def test_handles_write_error(self, mock_app, mock_calc_page):
        """Verifica manejo de error de escritura."""
        mock_calc_page.last_audit = True
        mock_app.view.pages = {"calculate": mock_calc_page}
        
        with patch('controllers.app_controller.isinstance', return_value=True), \
             patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog, \
             patch('builtins.open', side_effect=IOError("Test error")):
            
            mock_dialog.return_value = ("/tmp/audit.html", "")
            
            mock_app._on_export_audit_log()
            
            mock_app.view.show_message.assert_called()
