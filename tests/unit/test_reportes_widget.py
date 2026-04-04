# -*- coding: utf-8 -*-
"""Tests unitarios para ReportesWidget.

Cubre ReportesWidget: init, selección producto/orden, búsqueda limpiada,
set_controller y refresh. Controller y model mockeados con spec.
"""
import pytest
from unittest.mock import MagicMock, patch, create_autospec

from core.services.report_service import ReportService
from ui.widgets.reportes_widget import ReportesWidget

pytestmark = pytest.mark.unit


class _ControllerSinModeloNiContainer:
    """Objeto mínimo: `model` es None y no hay `container` (getattr → None)."""

    model = None


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
            mock_orders.assert_called_once_with("PROD1")
            mock_charts.assert_called_once_with("PROD1")

    def test_on_search_result_selected_orden(self, widget):
        """Selección de orden busca producto asociado."""
        detalle = MagicMock(spec=['producto_codigo'])
        detalle.producto_codigo = "PROD1"
        widget.report_controller.model.get_order_details.return_value = detalle

        with patch.object(widget.orders_widget, 'load_orders_for_product') as mock_orders, \
             patch.object(widget.charts_widget, 'update_charts') as mock_charts:
            widget._on_search_result_selected("orden", "OF-001")
            mock_orders.assert_called_once_with("PROD1")
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
            mock_orders.assert_called_once_with()
            mock_charts.assert_called_once_with()

    def test_on_order_selected(self, widget):
        """Selección de orden logea información."""
        try:
            widget._on_order_selected("OF-001")
        except Exception:
            pytest.fail("_on_order_selected no debería propagar excepciones")
        assert widget.report_controller is not None

    def test_on_order_selected_uses_report_service_from_di(self, qtbot):
        """Con ReportService en el DI, no se llama a model.get_order_details."""
        rs = create_autospec(ReportService, instance=True)
        rs.get_order_details.return_value = None
        rs.get_order_units.return_value = []
        ctrl = MagicMock(spec=["model", "container"])
        ctrl.model = MagicMock(spec=["get_order_details", "get_order_units"])
        ctrl.container = MagicMock(spec=["is_registered", "resolve"])
        ctrl.container.is_registered.side_effect = lambda t: t is ReportService
        ctrl.container.resolve.return_value = rs
        w = ReportesWidget(controller=ctrl)
        qtbot.addWidget(w)
        w._on_order_selected("OF-001")
        rs.get_order_details.assert_called_once_with("OF-001")
        ctrl.model.get_order_details.assert_not_called()

    def test_set_controller(self, widget):
        """set_controller propaga a sub-widgets."""
        new_ctrl = _ControllerSinModeloNiContainer()
        with patch.object(widget.search_widget, 'set_controller') as mock_search, \
             patch.object(widget.search_widget, 'set_report_service') as mock_rs, \
             patch.object(widget.orders_widget, 'set_controller') as mock_orders, \
             patch.object(widget.charts_widget, 'set_controller') as mock_charts:
            widget.set_controller(new_ctrl)
            mock_search.assert_called_once_with(new_ctrl)
            mock_rs.assert_called_once_with(None)
            mock_orders.assert_called_once_with(new_ctrl)
            mock_charts.assert_called_once_with(new_ctrl)

    def test_refresh(self, widget):
        """refresh limpia todos los sub-widgets."""
        with patch.object(widget.search_widget, 'clear_search') as mock_search, \
             patch.object(widget.orders_widget, 'clear') as mock_orders, \
             patch.object(widget.charts_widget, 'clear') as mock_charts:
            widget.refresh()
            mock_search.assert_called_once_with()
            mock_orders.assert_called_once_with()
            mock_charts.assert_called_once_with()
