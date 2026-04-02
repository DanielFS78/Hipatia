# -*- coding: utf-8 -*-
"""Tests unitarios para ReportesWidget.

Cubre ReportesWidget: init, selección producto/orden, búsqueda limpiada,
set_controller y refresh. Controller y model mockeados con spec.
"""
import pytest
from unittest.mock import MagicMock, patch

from ui.widgets.reportes_widget import ReportesWidget

pytestmark = pytest.mark.unit


class TestReportesWidget:
    """Tests unitarios para ReportesWidget."""

    @pytest.fixture
    def widget(self, qtbot):
        """Fixture para ReportesWidget con controller mock."""
        from core.di_container import DIContainer
        from controllers.report_controller import ReportController
        ctrl = MagicMock(spec=['model'])
        ctrl.model = MagicMock(spec=['get_order_details', 'get_order_units'])
        ctrl.model.get_order_units.return_value = []
        DIContainer.get_instance().register(ReportController, instance=ctrl)
        w = ReportesWidget(controller=ctrl)
        qtbot.addWidget(w)
        return w

    def test_init(self, widget):
        """Widget se inicializa con sub-widgets."""
        assert widget.search_widget is not None
        assert widget.orders_widget is not None
        assert widget.charts_widget is not None

    def test_on_search_result_selected_producto(self, widget):
        """Selección de producto carga órdenes y gráficas."""
        with patch.object(widget.orders_widget, 'load_orders_for_product') as mock_orders, \
             patch.object(widget.charts_widget, 'update_charts') as mock_charts:
            widget._on_search_result_selected("producto", "PROD1")
            assert mock_orders.call_count == 1
            mock_orders.assert_called_once_with("PROD1")
            assert mock_charts.call_count == 1
            mock_charts.assert_called_once_with("PROD1")

    def test_on_search_result_selected_orden(self, widget):
        """Selección de orden busca producto asociado."""
        detalle = MagicMock(spec=['producto_codigo'])
        detalle.producto_codigo = "PROD1"
        widget.report_controller.model.get_order_details.return_value = detalle

        with patch.object(widget.orders_widget, 'load_orders_for_product') as mock_orders, \
             patch.object(widget.charts_widget, 'update_charts') as mock_charts:
            widget._on_search_result_selected("orden", "OF-001")
            assert mock_orders.call_count == 1
            mock_orders.assert_called_once_with("PROD1")
            assert mock_charts.call_count == 1
            mock_charts.assert_called_once_with("PROD1")

    def test_on_search_result_selected_orden_error(self, widget):
        """Error al buscar detalles de orden no crashea."""
        widget.report_controller.model.get_order_details.side_effect = Exception("DB Error")
        try:
            widget._on_search_result_selected("orden", "OF-001")
        except Exception:
            pytest.fail("_on_search_result_selected no debería propagar excepciones de BD")
        assert widget.report_controller is not None

    def test_on_search_cleared(self, widget):
        """Limpiar búsqueda limpia órdenes y gráficas."""
        with patch.object(widget.orders_widget, 'clear') as mock_orders, \
             patch.object(widget.charts_widget, 'clear') as mock_charts:
            widget._on_search_cleared()
            assert mock_orders.call_count == 1
            mock_orders.assert_called_once_with()
            assert mock_charts.call_count == 1
            mock_charts.assert_called_once_with()

    def test_on_order_selected(self, widget):
        """Selección de orden logea información."""
        try:
            widget._on_order_selected("OF-001")
        except Exception:
            pytest.fail("_on_order_selected no debería propagar excepciones")
        assert widget.report_controller is not None

    def test_set_controller(self, widget):
        """set_controller propaga a sub-widgets."""
        new_ctrl = MagicMock(spec=[])
        with patch.object(widget.search_widget, 'set_controller') as mock_search, \
             patch.object(widget.orders_widget, 'set_controller') as mock_orders, \
             patch.object(widget.charts_widget, 'set_controller') as mock_charts:
            widget.set_controller(new_ctrl)
            assert mock_search.call_count == 1
            mock_search.assert_called_once_with(new_ctrl)
            assert mock_orders.call_count == 1
            mock_orders.assert_called_once_with(new_ctrl)
            assert mock_charts.call_count == 1
            mock_charts.assert_called_once_with(new_ctrl)

    def test_refresh(self, widget):
        """refresh limpia todos los sub-widgets."""
        with patch.object(widget.search_widget, 'clear_search') as mock_search, \
             patch.object(widget.orders_widget, 'clear') as mock_orders, \
             patch.object(widget.charts_widget, 'clear') as mock_charts:
            widget.refresh()
            assert mock_search.call_count == 1
            mock_search.assert_called_once_with()
            assert mock_orders.call_count == 1
            mock_orders.assert_called_once_with()
            assert mock_charts.call_count == 1
            mock_charts.assert_called_once_with()
