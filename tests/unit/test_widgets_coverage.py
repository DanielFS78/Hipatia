"""
Tests de Cobertura para ui/widgets/ - Fase 3.9
===============================================
Suite de tests diseñada para maximizar la cobertura ejecutando el código real.
Utilizamos Mocks como contenedores y llamamos a los métodos de clase para evitar
problemas con la inicialización de Qt y super().__init__().
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date

# Importamos las clases de widgets
from ui.widgets import (
    HomeWidget, 
    TimelineVisualizationWidget, 
    TaskAnalysisPanel,
    HistorialWidget,
    DashboardWidget,
    SettingsWidget,
    WorkersWidget,
    MachinesWidget,
    ProductsWidget,
    FabricationsWidget
)

@pytest.mark.unit
class TestWidgetsRealExecution:
    """Tests que ejecutan los métodos reales sin instanciar los widgets de Qt."""

    def test_home_widget_set_quote_execution(self):
        """set_quote debe ejecutar su código interno."""
        widget = MagicMock(spec=HomeWidget)
        widget.quote_text = MagicMock()
        widget.author_text = MagicMock()
        
        # Ejecutar método REAL sobre un MOCK
        HomeWidget.set_quote(widget, "Test Quote", "Test Author")
        
        widget.quote_text.setText.assert_called_once()
        widget.author_text.setText.assert_called_once()

    def test_timeline_setData_execution(self):
        """setData debe ejecutar su lógica de ordenación y fechas."""
        widget = MagicMock(spec=TimelineVisualizationWidget)
        widget.update = MagicMock()
        
        start1 = datetime(2025, 1, 1, 10, 0)
        end1 = datetime(2025, 1, 1, 12, 0)
        start2 = datetime(2025, 1, 2, 8, 0)
        end2 = datetime(2025, 1, 2, 10, 0)
        
        results = [
            {'Inicio': start2, 'Fin': end2, 'Tarea': 'T2'},
            {'Inicio': start1, 'Fin': end1, 'Tarea': 'T1'}
        ]
        
        # Ejecutar método REAL
        TimelineVisualizationWidget.setData(widget, results, [])
        
        # Verificar efectos (los atributos se guardan en el mock)
        assert len(widget.results) == 2
        assert widget.results[0]['Tarea'] == 'T1'
        assert widget.start_time.hour == 0
        assert widget.total_days == 2

    def test_timeline_clear_execution(self):
        """clear debe resetear la lista de tareas."""
        widget = MagicMock(spec=TimelineVisualizationWidget)
        widget.update = MagicMock()
        widget.tasks = ['dummy']
        
        TimelineVisualizationWidget.clear(widget)
        assert widget.tasks == []
        widget.update.assert_called_once()

    def test_historial_clear_view_execution(self):
        """clear_view debe resetear componentes."""
        widget = MagicMock(spec=HistorialWidget)
        widget.results_list = MagicMock()
        widget.clear_calendar_format = MagicMock()
        widget.details_stack = MagicMock()
        
        HistorialWidget.clear_view(widget)
        widget.results_list.clear.assert_called_once()
        widget.clear_calendar_format.assert_called_once()
        widget.details_stack.setCurrentIndex.assert_called_once_with(0)

    def test_historial_highlight_calendar_dates_execution(self):
        """highlight_calendar_dates debe aplicar formato."""
        widget = MagicMock(spec=HistorialWidget)
        widget.calendar = MagicMock()
        
        dates = [date(2025, 1, 1)]
        # Necesitamos que el mock de QColor funcione o esté parcheado
        with patch('ui.widgets.historial_widget.QColor'), \
             patch('ui.widgets.historial_widget.QTextCharFormat'):
            HistorialWidget.highlight_calendar_dates(widget, dates, "#FF0000")
            widget.calendar.setDateTextFormat.assert_called_once()

    def test_task_analysis_panel_displayTask_execution(self):
        """displayTask debe poblar el log."""
        widget = MagicMock(spec=TaskAnalysisPanel)
        widget.log_vbox = MagicMock()
        widget.header_label = MagicMock()
        
        # Mock de limpieza de layout
        widget.log_vbox.count.side_effect = [1, 0, 0, 0, 0]
        widget.log_vbox.takeAt.return_value = MagicMock()
        
        # Mock de auditoría
        decision = MagicMock()
        decision.status = MagicMock()
        decision.status.value = 'POSITIVE'
        decision.icon = '✅'
        decision.user_friendly_reason = 'Test'
        decision.timestamp = datetime.now()
        
        # Parcheamos QLabel porque se instancia dentro del método
        with patch('ui.widgets.timeline_widget.QLabel'):
            TaskAnalysisPanel.displayTask(widget, {'Tarea': 'T1'}, [decision])
            widget.log_vbox.takeAt.assert_called()
            widget.log_vbox.addWidget.assert_called()

    def test_dashboard_update_machine_usage_execution(self):
        """update_machine_usage debe ejecutar su lógica."""
        widget = MagicMock(spec=DashboardWidget)
        widget.machine_chart_view = MagicMock()
        
        data = [('M1', 10.5), ('M2', 5.0)]
        # Parcheamos clases de QChart
        with patch('ui.widgets.dashboard_widget.QBarSeries'), \
             patch('ui.widgets.dashboard_widget.QBarSet'), \
             patch('ui.widgets.dashboard_widget.QColor'):
            DashboardWidget.update_machine_usage(widget, data)
            widget.machine_chart_view.chart.assert_called()

    def test_settings_update_break_buttons_state_execution(self):
        """_update_break_buttons_state debe habilitar/deshabilitar botones."""
        widget = MagicMock(spec=SettingsWidget)
        widget.breaks_list = MagicMock()
        widget.edit_break_button = MagicMock()
        widget.remove_break_button = MagicMock()
        
        widget.breaks_list.selectedItems.return_value = [MagicMock()]
        SettingsWidget._update_break_buttons_state(widget)
        widget.edit_break_button.setEnabled.assert_called_with(True)
        
        widget.breaks_list.selectedItems.return_value = []
        SettingsWidget._update_break_buttons_state(widget)
        widget.edit_break_button.setEnabled.assert_called_with(False)

    def test_workers_widget_populate_list_execution(self):
        """populate_list debe ejecutar su lógica de inserción."""
        widget = MagicMock(spec=WorkersWidget)
        widget.workers_list = MagicMock()
        widget.details_container_layout = MagicMock()
        widget.details_container_layout.count.return_value = 0
        
        w1 = MagicMock(id=1, nombre_completo="Juan G", activo=True)
        # Parcheamos QListWidgetItem y QColor
        with patch('ui.widgets.workers_widget.QListWidgetItem'), \
             patch('ui.widgets.workers_widget.QColor'):
            WorkersWidget.populate_list(widget, [w1])
            widget.workers_list.clear.assert_called_once()
            widget.workers_list.addItem.assert_called()

    def test_machines_widget_populate_list_execution(self):
        """populate_list de máquinas debe ejecutar su lógica."""
        widget = MagicMock(spec=MachinesWidget)
        widget.machines_list = MagicMock()
        widget.details_container_layout = MagicMock()
        widget.details_container_layout.count.return_value = 0
        widget.search_bar = MagicMock()
        
        m1 = MagicMock(id=1, nombre="Torno", activa=True)
        with patch('ui.widgets.machines_widget.QListWidgetItem'), \
             patch('ui.widgets.machines_widget.QColor'):
            MachinesWidget.populate_list(widget, [m1])
            widget.machines_list.clear.assert_called_once()
            widget.machines_list.addItem.assert_called()

    def test_products_widget_update_search_results_execution(self):
        """update_search_results de productos debe ejecutar su lógica."""
        widget = MagicMock(spec=ProductsWidget)
        widget.results_list = MagicMock()
        widget.controller = MagicMock()
        widget.controller.model.get_product_iterations.return_value = []
        
        p1 = MagicMock(codigo="P-001", descripcion="Prod 1")
        with patch('ui.widgets.products_widget.QListWidgetItem'):
            ProductsWidget.update_search_results(widget, [p1])
            widget.results_list.clear.assert_called_once()
            widget.results_list.addItem.assert_called()

    def test_fabrications_widget_update_search_results_execution(self):
        """update_search_results de fabricaciones debe ejecutar su lógica."""
        widget = MagicMock(spec=FabricationsWidget)
        widget.results_list = MagicMock()
        
        f1 = MagicMock(id=1, nombre="Fab 1", codigo="F-001")
        with patch('ui.widgets.fabrications_widget.QListWidgetItem'):
            FabricationsWidget.update_search_results(widget, [f1])
            widget.results_list.clear.assert_called_once()
            widget.results_list.addItem.assert_called()
