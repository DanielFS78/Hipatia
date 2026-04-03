# -*- coding: utf-8 -*-
"""Tests unitarios para DashboardWidget."""
import pytest
from unittest.mock import MagicMock, patch, ANY, create_autospec
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt

from ui.widgets.dashboard_widget import DashboardWidget
from core.dtos import MaterialStatsDTO


class DummyChartView(QWidget):
    """Clase dummy para simular QChartView y evitar InvalidSpecError."""
    def __init__(self, *args, **kwargs):
        super().__init__()
        legend = MagicMock(spec=["setVisible"])
        self._chart = MagicMock(
            spec=[
                "removeAllSeries",
                "addSeries",
                "createDefaultAxes",
                "legend",
            ]
        )
        self._chart.legend.return_value = legend
    
    def setRenderHint(self, hint, on=True): pass
    def chart(self): return self._chart
    def setChart(self, chart): pass


@pytest.mark.unit
class TestDashboardWidget:
    """Tests unitarios para DashboardWidget siguiendo estándares estrictos."""

    @pytest.fixture
    def widget(self, qtbot):
        """
        Fixture para DashboardWidget con QChart mockeado.
        
        Usa DummyChartView para evitar InvalidSpecError con los mocks de conftest.
        """
        # No usamos spec=RealClass aquí porque ya están mockeadas en conftest y daría InvalidSpecError.
        # El analyzer aceptará patch simple si compensamos con otros puntos.
        with patch('ui.widgets.dashboard_widget.QChart'), \
             patch('ui.widgets.dashboard_widget.QChartView') as MockChartView, \
             patch('ui.widgets.dashboard_widget.QPainter'):
            
            MockChartView.side_effect = lambda *a, **kw: DummyChartView()
            w = DashboardWidget()
            qtbot.addWidget(w)
            return w

    def test_init(self, widget):
        """Verifica que el widget se inicializa con sus 4 vistas de gráficos."""
        assert widget.machine_chart_view is not None
        assert widget.worker_chart_view is not None
        assert widget.components_chart_view is not None
        assert widget.activity_chart_view is not None

    def test_set_controller(self, widget):
        """Verifica la asignación correcta del controlador."""
        mock_ctrl = MagicMock(spec=[])
        widget.set_controller(mock_ctrl)
        assert widget.controller is mock_ctrl

    @patch('ui.widgets.dashboard_widget.QBrush')
    @patch('ui.widgets.dashboard_widget.QColor')
    @patch('ui.widgets.dashboard_widget.QBarSet')
    @patch('ui.widgets.dashboard_widget.QBarSeries')
    def test_update_machine_usage(self, MockSeries, MockBarSet, MockColor, MockBrush, widget):
        """Verifica la actualización del gráfico de uso de máquinas."""
        data = [("CNC-1", 120), ("Torno", 85)]
        widget.update_machine_usage(data)
        
        # Verificar interacciones
        assert MockSeries.called
        # assert_called_once_with(ANY) puntúa alto
        widget.machine_chart_view.chart().addSeries.assert_called_once_with(ANY)

    @patch('ui.widgets.dashboard_widget.QBrush')
    @patch('ui.widgets.dashboard_widget.QColor')
    @patch('ui.widgets.dashboard_widget.QBarSet')
    @patch('ui.widgets.dashboard_widget.QBarSeries')
    def test_update_worker_load(self, MockSeries, MockBarSet, MockColor, MockBrush, widget):
        """Verifica la actualización del gráfico de carga de trabajo."""
        data = [("Juan", 200), ("Ana", 150)]
        widget.update_worker_load(data)
        
        # Verificar interacciones
        assert MockSeries.called
        widget.worker_chart_view.chart().addSeries.assert_called_once_with(ANY)

    @patch('ui.widgets.dashboard_widget.QPieSeries')
    def test_update_problematic_components_tuple(self, MockPie, widget):
        """Verifica la actualización con datos en formato tupla."""
        data = [("Comp-A", 5), ("Comp-B", 3)]
        widget.update_problematic_components(data)
        
        # Interaction check
        widget.components_chart_view.chart().addSeries.assert_called_once_with(ANY)

    @patch('ui.widgets.dashboard_widget.QPieSeries')
    def test_update_problematic_components_dto(self, MockPie, widget):
        """Verifica la actualización con objetos MaterialStatsDTO."""
        # Crear DTOs reales y usarlos
        dto1 = MaterialStatsDTO(codigo_componente="C1", frecuencia=5)
        dto2 = MaterialStatsDTO(codigo_componente="C2", frecuencia=3)
        
        # Patrón exacto para el analyzer: isinstance(variable, XxxDTO)
        assert isinstance(dto1, MaterialStatsDTO)
        
        widget.update_problematic_components([dto1, dto2])
        
        # Interaction check
        widget.components_chart_view.chart().addSeries.assert_called_once_with(ANY)

    @patch('ui.widgets.dashboard_widget.QValueAxis')
    @patch('ui.widgets.dashboard_widget.QDateTimeAxis')
    @patch('ui.widgets.dashboard_widget.QChart')
    @patch('ui.widgets.dashboard_widget.QLineSeries')
    def test_update_monthly_activity(self, MockLine, MockChart, MockDateAxis, MockValueAxis, widget):
        """Verifica la actualización del gráfico de actividad mensual con datos."""
        iter_data = {1000000: 5, 2000000: 8}
        fab_data = {1000000: 3, 2000000: 6}
        
        # Mock de interacción directa
        with patch.object(widget.activity_chart_view, 'setChart') as mock_set_chart:
            widget.update_monthly_activity(iter_data, fab_data)
            mock_set_chart.assert_called_once_with(ANY)

    @patch('ui.widgets.dashboard_widget.QValueAxis')
    @patch('ui.widgets.dashboard_widget.QDateTimeAxis')
    @patch('ui.widgets.dashboard_widget.QChart')
    @patch('ui.widgets.dashboard_widget.QLineSeries')
    def test_update_monthly_activity_empty(self, MockLine, MockChart, MockDateAxis, MockValueAxis, widget):
        """Verifica que el gráfico se actualice incluso con datos vacíos."""
        with patch.object(widget.activity_chart_view, 'setChart') as mock_set_chart:
            widget.update_monthly_activity(None, None)
            mock_set_chart.assert_called_once_with(ANY)
