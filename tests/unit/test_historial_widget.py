# -*- coding: utf-8 -*-
"""Tests unitarios para HistorialWidget (modos iteraciones/fabricaciones, clear_view, highlight)."""
import pytest
from unittest.mock import MagicMock, patch, create_autospec
from PyQt6.QtWidgets import QWidget, QListWidgetItem
from PyQt6.QtCore import Qt

from ui.widgets.historial_widget import HistorialWidget

pytestmark = pytest.mark.unit


def _make_chart_view():
    """Creates a QWidget with setRenderHint for mocking QChartView."""
    w = QWidget()
    # Qt: no usar autospec; solo asegurar que existen los atributos esperados.
    w.setRenderHint = MagicMock(spec=[])  # type: ignore[attr-defined]
    w.chart = MagicMock(spec=[])  # type: ignore[attr-defined]
    w.setChart = MagicMock(spec=[])  # type: ignore[attr-defined]
    return w


class TestHistorialWidget:
    """Tests unitarios para HistorialWidget."""

    @pytest.fixture
    def widget(self, qtbot):
        """Fixture para HistorialWidget con QChart mockeado."""
        with patch('ui.widgets.historial_widget.QChart') as MockChart, \
             patch('ui.widgets.historial_widget.QChartView') as MockChartView, \
             patch('ui.widgets.historial_widget.QPainter'):
            MockChartView.side_effect = lambda *a, **kw: _make_chart_view()
            from core.di_container import DIContainer
            from controllers.historial.controller import HistorialController
            ctrl = create_autospec(HistorialController, instance=True)
            DIContainer.get_instance().register(HistorialController, instance=ctrl)
            w = HistorialWidget(controller=ctrl)
            qtbot.addWidget(w)
            return w

    def test_init(self, widget):
        """Widget se inicializa en modo iteraciones."""
        assert widget.current_mode == "iteraciones"
        assert widget.iteraciones_radio.isChecked()

    def test_mode_changed_to_fabricaciones(self, widget, qtbot):
        """Cambiar a modo fabricaciones emite señal correcta."""
        with qtbot.waitSignal(widget.mode_changed_signal, timeout=1000) as blocker:
            widget.fabricaciones_radio.setChecked(True)
        assert blocker.args == ["fabricaciones"]
        assert widget.current_mode == "fabricaciones"

    def test_mode_changed_to_iteraciones(self, widget, qtbot):
        """Cambiar de vuelta a iteraciones emite señal correcta."""
        widget.fabricaciones_radio.setChecked(True)
        with qtbot.waitSignal(widget.mode_changed_signal, timeout=1000) as blocker:
            widget.iteraciones_radio.setChecked(True)
        assert blocker.args == ["iteraciones"]

    def test_clear_view(self, widget):
        """clear_view limpia resultados y formato del calendario."""
        widget.results_list.addItem(QListWidgetItem("Item"))
        with patch.object(widget, 'clear_calendar_format') as mock_clear:
            widget.clear_view()
            assert widget.results_list.count() == 0
            assert mock_clear.call_count == 1
            mock_clear.assert_called_once_with()

    @patch('ui.widgets.historial_widget.QTextCharFormat')
    @patch('ui.widgets.historial_widget.QColor')
    def test_highlight_calendar_dates(self, MockColor, MockFormat, widget):
        """highlight_calendar_dates aplica formato al calendario."""
        from PyQt6.QtCore import QDate
        dates = [QDate(2026, 1, 15), QDate(2026, 1, 16)]
        with patch.object(widget.calendar, 'setDateTextFormat') as mock_set:
            widget.highlight_calendar_dates(dates, "#ff0000")
            assert mock_set.call_count == len(dates)

    @patch('ui.widgets.historial_widget.QTextCharFormat')
    def test_clear_calendar_format(self, MockFormat, widget):
        """clear_calendar_format resetea el formato."""
        with patch.object(widget.calendar, 'setDateTextFormat') as mock_set:
            widget.clear_calendar_format()
            mock_set.assert_called()

    def test_search_signal(self, widget, qtbot):
        """Texto en búsqueda emite señal."""
        with qtbot.waitSignal(widget.search_text_changed_signal, timeout=1000) as blocker:
            widget.search_entry.setText("test")
        assert blocker.signal_triggered

    def test_print_report_signal(self, widget, qtbot):
        """Botón imprimir emite señal."""
        with qtbot.waitSignal(widget.print_report_signal, timeout=1000) as blocker:
            widget.print_report_button.click()
        assert blocker.signal_triggered
