# -*- coding: utf-8 -*-
"""Tests unitarios para ReportsChartsWidget: estado inicial, update_charts, clear."""
import pytest
from unittest.mock import create_autospec
from ui.widgets.reports.charts_container import ReportsChartsWidget
from core.reports_dtos import PromedioTiempoDTO
from core.services.report_service import ReportService
from datetime import datetime

pytestmark = pytest.mark.unit


class TestReportsChartsWidget:
    """Tests para el widget de gráficas."""

    @pytest.fixture
    def mock_report_service(self):
        rs = create_autospec(ReportService, instance=True)
        return rs

    @pytest.fixture
    def widget(self, qtbot, mock_report_service):
        widget = ReportsChartsWidget(report_service=mock_report_service)
        qtbot.addWidget(widget)
        return widget

    def test_initial_state(self, widget):
        """Verifica estado inicial."""
        assert "Análisis de Producción" in widget.title_label.text()
        assert widget._current_producto is None
        assert widget.tabs.count() == 3

    def test_update_charts_calls_report_service(self, widget, mock_report_service):
        """Verifica que update_charts llame a ReportService."""
        code = "TEST-PROD"
        mock_report_service.get_product_time_stats.return_value = PromedioTiempoDTO(
            producto_codigo=code,
            producto_descripcion="Desc",
            promedio_segundos=120.0,
            desviacion_estandar=10.0,
            minimo_segundos=100,
            maximo_segundos=130,
            total_unidades=1
        )
        mock_report_service.get_evolution_stats.return_value = []
        mock_report_service.get_worker_time_stats.return_value = []
        mock_report_service.get_incidents_stats.return_value = []

        widget.update_charts(code)
        assert mock_report_service.get_product_time_stats.call_count >= 1
        mock_report_service.get_product_time_stats.assert_called_with(code)
        assert mock_report_service.get_evolution_stats.call_count >= 1
        mock_report_service.get_evolution_stats.assert_called_with(code, days=30)
        assert mock_report_service.get_worker_time_stats.call_count >= 1
        mock_report_service.get_worker_time_stats.assert_called_with(code)
        assert mock_report_service.get_incidents_stats.call_count >= 1
        mock_report_service.get_incidents_stats.assert_called_with(code)
        assert code in widget.title_label.text()

    def test_update_stats_display(self, widget, mock_report_service):
        """Verifica que las tarjetas de estadísticas se actualicen."""
        code = "TEST-PROD"
        stats = PromedioTiempoDTO(
            producto_codigo=code,
            producto_descripcion="Desc",
            promedio_segundos=300.0,
            desviacion_estandar=0.0,
            minimo_segundos=300,
            maximo_segundos=300,
            total_unidades=50
        )
        mock_report_service.get_product_time_stats.return_value = stats
        mock_report_service.get_evolution_stats.return_value = []
        mock_report_service.get_worker_time_stats.return_value = []
        mock_report_service.get_incidents_stats.return_value = []

        widget.update_charts(code)
        assert widget.stats_layout.count() >= 4

    def test_clear_reset(self, widget):
        """Verifica limpiar el widget."""
        widget._current_producto = "SOME-PROD"
        widget.title_label.setText("Changed")
        widget.clear()
        assert widget._current_producto is None
        assert "Análisis de Producción" in widget.title_label.text()
