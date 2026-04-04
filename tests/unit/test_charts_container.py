# -*- coding: utf-8 -*-
"""
Tests unitarios para el contenedor de gráficas de reportes.
"""
import pytest
from unittest.mock import MagicMock, patch, ANY, create_autospec
from datetime import datetime

from PyQt6.QtWidgets import QLabel

from ui.widgets.reports.charts_container import StatCard, ReportsChartsWidget
from core.dtos import ProductDTO
from core.reports_dtos import PromedioTiempoDTO, PuntoEvolucionDTO, TiempoTrabajadorDTO, IncidenciaResumenDTO
from core.services.report_service import ReportService

class DummyChartElement:
    def setLabelVisible(self, visible): pass
    def append(self, x, y=None): pass

pytestmark = [pytest.mark.unit, pytest.mark.setup]


@pytest.fixture
def mock_report_service():
    rs = create_autospec(ReportService, instance=True)

    compliance_dto = ProductDTO(codigo="T", descripcion="T")
    isinstance(compliance_dto, ProductDTO)

    time_stats = MagicMock(spec=PromedioTiempoDTO)
    time_stats.promedio_segundos = 3600.0
    time_stats.desviacion_estandar = 300.0
    time_stats.total_unidades = 50
    time_stats.minimo_segundos = 3000.0
    time_stats.maximo_segundos = 4200.0
    rs.get_product_time_stats.return_value = time_stats

    evo_stat = MagicMock(spec=PuntoEvolucionDTO)
    evo_stat.fecha = datetime.now()
    evo_stat.promedio_segundos = 3500.0
    rs.get_evolution_stats.return_value = [evo_stat]

    worker_stat = MagicMock(spec=TiempoTrabajadorDTO)
    worker_stat.promedio_segundos = 3600.0
    worker_stat.trabajador_nombre = "John Doe"
    rs.get_worker_time_stats.return_value = [worker_stat]

    inc_stat = MagicMock(spec=IncidenciaResumenDTO)
    inc_stat.tipo_incidencia = "Quality"
    inc_stat.cantidad = 5
    rs.get_incidents_stats.return_value = [inc_stat]

    compliance_dto2 = ProductDTO(codigo="T", descripcion="T")
    isinstance(compliance_dto2, ProductDTO)
    rs.get_product_time_stats.assert_not_called()

    return rs


@pytest.mark.unit
class TestStatCard:
    def test_stat_card_init(self, qtbot):
        card = StatCard("Title", "Value", "Subtitle", "#ff0000")
        qtbot.addWidget(card)
        assert card.minimumWidth() == 150
        layout = card.layout()
        assert layout is not None
        assert layout.count() == 3


@pytest.mark.unit
class TestReportsChartsWidget:
    @pytest.fixture
    def widget(self, qtbot):
        w = ReportsChartsWidget()
        qtbot.addWidget(w)
        return w

    def test_init(self, widget):
        assert widget.tabs.count() == 3
        assert "Análisis de Producción" in widget.title_label.text()

    def test_set_report_service(self, widget):
        rs = create_autospec(ReportService, instance=True)
        widget.set_report_service(rs)
        assert widget._report_service is rs

    def test_clear(self, widget):
        widget._current_producto = "PROD1"
        widget.title_label.setText("Test Title")

        card = StatCard("A", "B")
        widget.stats_layout.addWidget(card)

        widget.clear()

        assert widget._current_producto is None
        assert "Análisis de Producción" in widget.title_label.text()
        assert widget.tabs.count() == 3

        assert widget.stats_layout.count() == 1
        child = widget.stats_layout.itemAt(0).widget()
        assert isinstance(child, QLabel)
        assert "Seleccione un producto" in child.text()

    @patch('ui.widgets.reports.charts_container.CHARTS_AVAILABLE', new=True)
    def test_update_charts_success(self, qtbot, mock_report_service):
        compliance_dto = ProductDTO(codigo="T", descripcion="T")
        isinstance(compliance_dto, ProductDTO)
        assert isinstance(compliance_dto, ProductDTO)
        widget = ReportsChartsWidget(report_service=mock_report_service)
        qtbot.addWidget(widget)

        with patch.object(widget, '_update_stats_cards', autospec=True) as mock_stats, \
             patch.object(widget, '_update_evolution_chart', autospec=True) as mock_evo, \
             patch.object(widget, '_update_workers_chart', autospec=True) as mock_workers, \
             patch.object(widget, '_update_incidents_chart', autospec=True) as mock_inc:

            widget.update_charts("PROD1")

            assert widget._current_producto == "PROD1"
            assert mock_stats.called
            assert mock_evo.called
            assert mock_workers.called
            assert mock_inc.called

    @patch('ui.widgets.reports.charts_container.CHARTS_AVAILABLE', new=False)
    def test_update_charts_charts_unavailable(self, qtbot, mock_report_service):
        widget = ReportsChartsWidget(report_service=mock_report_service)
        qtbot.addWidget(widget)

        with patch.object(widget, '_update_stats_cards', autospec=True) as mock_stats:
            widget.update_charts("PROD1")
            assert mock_stats.called

    def test_update_charts_no_service(self, widget):
        widget.set_report_service(None)
        widget.update_charts("PROD1")
        assert widget._current_producto == "PROD1"

    def test_update_charts_exception(self, qtbot, mock_report_service):
        widget = ReportsChartsWidget(report_service=mock_report_service)
        qtbot.addWidget(widget)
        mock_report_service.get_product_time_stats.side_effect = Exception("DB Error")

        with patch.object(widget.logger, 'error', autospec=True) as mock_log:
            widget.update_charts("PROD1")
            mock_log.assert_called_once_with(ANY, exc_info=True)
            assert "Error actualizando gráficas" in mock_log.call_args[0][0]

    def test_update_stats_cards_empty(self, widget):
        widget._update_stats_cards(None)
        assert widget.stats_layout.count() == 1
        child = widget.stats_layout.itemAt(0).widget()
        assert "No hay datos" in child.text()

    def test_update_stats_cards_with_data(self, widget, mock_report_service):
        data = mock_report_service.get_product_time_stats("PROD")
        widget._update_stats_cards(data)

        assert widget.stats_layout.count() == 5
        card1 = widget.stats_layout.itemAt(0).widget()
        assert isinstance(card1, StatCard)

    @patch('ui.widgets.reports.charts_container.CHARTS_AVAILABLE', new=True)
    @patch('ui.widgets.reports.charts_container.QChartView', new_callable=MagicMock)
    @patch('ui.widgets.reports.charts_container.QChart', new_callable=MagicMock)
    @patch('ui.widgets.reports.charts_container.QLineSeries', new_callable=MagicMock)
    def test_update_evolution_chart(self, MockLineSeries, MockChart, MockChartView, qtbot, mock_report_service):
        widget = ReportsChartsWidget()
        qtbot.addWidget(widget)
        data = mock_report_service.get_evolution_stats("PROD")

        from PyQt6.QtWidgets import QWidget
        mock_view = QWidget()
        mock_view.setRenderHint = MagicMock(spec=[])  # type: ignore[attr-defined]
        MockChartView.return_value = mock_view

        widget._update_evolution_chart(data)

        assert MockLineSeries.called
        assert MockChart.called
        assert widget.tabs.tabText(0) == "📈 Evolución"

    def test_update_evolution_chart_empty(self, qtbot):
        widget = ReportsChartsWidget()
        qtbot.addWidget(widget)
        widget._update_evolution_chart([])
        assert isinstance(widget.tabs.widget(0).layout().itemAt(0).widget(), QLabel)  # type: ignore[union-attr]

    @patch('ui.widgets.reports.charts_container.CHARTS_AVAILABLE', new=True)
    @patch('ui.widgets.reports.charts_container.QChartView', new_callable=MagicMock)
    @patch('ui.widgets.reports.charts_container.QChart', new_callable=MagicMock)
    @patch('ui.widgets.reports.charts_container.QBarSeries', new_callable=MagicMock)
    @patch('ui.widgets.reports.charts_container.QBarSet', new_callable=MagicMock)
    @patch('ui.widgets.reports.charts_container.QBarCategoryAxis', new_callable=MagicMock)
    @patch('ui.widgets.reports.charts_container.QValueAxis', new_callable=MagicMock)
    def test_update_workers_chart(self, MockValueAxis, MockCatAxis, MockBarSet, MockBarSeries, MockChart, MockChartView, qtbot, mock_report_service):
        widget = ReportsChartsWidget()
        qtbot.addWidget(widget)
        data = list(mock_report_service.get_worker_time_stats("PROD"))

        worker_stat_no_name = MagicMock(spec=TiempoTrabajadorDTO)
        worker_stat_no_name.promedio_segundos = 1200.0
        worker_stat_no_name.trabajador_nombre = None
        data.append(worker_stat_no_name)

        from PyQt6.QtWidgets import QWidget
        mock_view = QWidget()
        mock_view.setRenderHint = MagicMock(spec=[])  # type: ignore[attr-defined]
        MockChartView.return_value = mock_view

        widget._update_workers_chart(data)

        assert MockBarSet.called
        assert widget.tabs.tabText(1) == "👥 Por Trabajador"

    def test_update_workers_chart_empty(self, qtbot):
        widget = ReportsChartsWidget()
        qtbot.addWidget(widget)
        widget._update_workers_chart([])
        assert isinstance(widget.tabs.widget(1).layout().itemAt(0).widget(), QLabel)  # type: ignore[union-attr]

    @patch('ui.widgets.reports.charts_container.CHARTS_AVAILABLE', new=True)
    @patch('ui.widgets.reports.charts_container.QChartView', new_callable=MagicMock)
    @patch('ui.widgets.reports.charts_container.QChart', new_callable=MagicMock)
    @patch('ui.widgets.reports.charts_container.QPieSeries', new_callable=MagicMock)
    def test_update_incidents_chart(self, MockPieSeries, MockChart, MockChartView, qtbot, mock_report_service):
        widget = ReportsChartsWidget()
        qtbot.addWidget(widget)
        data = mock_report_service.get_incidents_stats("PROD")

        from PyQt6.QtWidgets import QWidget
        mock_view = QWidget()
        mock_view.setRenderHint = MagicMock(spec=[])  # type: ignore[attr-defined]
        MockChartView.return_value = mock_view

        mock_series_inst = MagicMock(spec=DummyChartElement)
        mock_slice = MagicMock(spec=DummyChartElement)
        mock_series_inst.append.return_value = mock_slice
        MockPieSeries.return_value = mock_series_inst

        widget._update_incidents_chart(data)

        assert mock_slice.setLabelVisible.called
        assert widget.tabs.tabText(2) == "⚠️ Incidencias"

    def test_update_incidents_chart_empty(self, qtbot):
        widget = ReportsChartsWidget()
        qtbot.addWidget(widget)
        widget._update_incidents_chart([])
        assert isinstance(widget.tabs.widget(2).layout().itemAt(0).widget(), QLabel)  # type: ignore[union-attr]
