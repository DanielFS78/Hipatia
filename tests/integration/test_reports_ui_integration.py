# -*- coding: utf-8 -*-
"""Tests de integración UI de reportes: búsqueda producto, actualización de widgets."""
import pytest
from unittest.mock import MagicMock, create_autospec
from ui.widgets.reportes_widget import ReportesWidget
from core.reports_dtos import OrdenFabricacionDetalleDTO
from core.services.report_service import ReportService
from datetime import datetime

pytestmark = pytest.mark.integration


class TestReportsUIIntegration:
    """Tests de integración para la UI de reportes."""

    @pytest.fixture
    def mock_controller(self):
        controller = MagicMock(spec=["model", "container"])
        controller.container = MagicMock(spec=["is_registered", "resolve"])
        controller.container.is_registered.return_value = False
        rs = create_autospec(ReportService, instance=True)
        rs.get_order_units.return_value = []
        controller.model = MagicMock(spec=["report_service"])
        controller.model.report_service = rs
        return controller

    @pytest.fixture
    def widget(self, qtbot, mock_controller):
        widget = ReportesWidget(mock_controller)
        widget.show()
        qtbot.addWidget(widget)
        return widget

    def test_product_search_updates_widgets(self, widget, mock_controller, qtbot):
        """Verifica que seleccionar un producto actualiza órdenes y gráficas."""
        prod_code = "PROD-123"
        rs = mock_controller.model.report_service
        rs.get_orders_for_product.return_value = []
        rs.get_product_time_stats.return_value = None
        rs.get_evolution_stats.return_value = []

        widget.search_widget.result_selected.emit('producto', prod_code)
        assert rs.get_orders_for_product.call_count >= 1
        rs.get_orders_for_product.assert_called_with(prod_code)
        assert prod_code in widget.orders_widget.title_label.text()
        assert rs.get_product_time_stats.call_count >= 1
        rs.get_product_time_stats.assert_called_with(prod_code)

    def test_order_search_updates_widgets_via_product(self, widget, mock_controller):
        """Verifica que seleccionar una orden busca su producto y actualiza todo."""
        order_code = "OF-999"
        prod_code = "PROD-FROM-ORDER"
        rs = mock_controller.model.report_service

        detalle_mock = OrdenFabricacionDetalleDTO(
            orden_fabricacion=order_code,
            producto_codigo=prod_code,
            producto_descripcion="Desc",
            fecha_inicio=datetime.now(),
        )
        rs.get_order_details.return_value = detalle_mock
        rs.get_orders_for_product.return_value = []

        widget.search_widget.result_selected.emit('orden', order_code)
        assert rs.get_order_details.call_count >= 1
        rs.get_order_details.assert_called_with(order_code)
        assert rs.get_orders_for_product.call_count >= 1
        rs.get_orders_for_product.assert_called_with(prod_code)
        assert prod_code in widget.orders_widget.title_label.text()

    def test_clear_search_clears_widgets(self, widget):
        """Verifica que limpiar la búsqueda limpia los sub-widgets."""
        widget.orders_widget.title_label.setText("DIRTY")
        widget.charts_widget.title_label.setText("DIRTY")
        widget.search_widget.search_cleared.emit()
        assert "Órdenes de Fabricación" in widget.orders_widget.title_label.text()
        assert "Análisis de Producción" in widget.charts_widget.title_label.text()
