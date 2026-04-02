# -*- coding: utf-8 -*-
"""Tests de integración UI de reportes: búsqueda producto, actualización de widgets."""
import pytest
from unittest.mock import MagicMock
from PyQt6.QtCore import Qt
from ui.widgets.reportes_widget import ReportesWidget
from core.reports_dtos import OrdenFabricacionDetalleDTO
from datetime import datetime

pytestmark = pytest.mark.integration


class TestReportsUIIntegration:
    """Tests de integración para la UI de reportes."""

#     @pytest.mark.skip(reason="ReportesWidget.__init__ hace super().__init__() -> Qt crea ventana nativa -> SIGABRT. Verificar manualmente en entorno con display.")
    @pytest.fixture
    def mock_controller(self):
        controller = MagicMock(spec=["model"])
        controller.model = MagicMock(
            spec=[
                "get_orders_for_product",
                "get_product_time_stats",
                "get_evolution_stats",
                "get_order_details",
            ]
        )
        return controller

    @pytest.fixture
    def widget(self, qtbot, mock_controller):
        widget = ReportesWidget(controller=mock_controller)
        widget.show()
        qtbot.addWidget(widget)
        return widget

    def test_product_search_updates_widgets(self, widget, mock_controller, qtbot):

        """Verifica que seleccionar un producto actualiza órdenes y gráficas."""
        # Arrange
        prod_code = "PROD-123"
        # Mocks para que no fallen las llamadas internas
        mock_controller.model.get_orders_for_product.return_value = []
        mock_controller.model.get_product_time_stats.return_value = None
        mock_controller.model.get_evolution_stats.return_value = []
        
        # Act - Simular señal desde SmartSearch
        widget.search_widget.result_selected.emit('producto', prod_code)
        assert mock_controller.model.get_orders_for_product.call_count >= 1
        mock_controller.model.get_orders_for_product.assert_called_with(prod_code)
        # Verificar que se actualizó el título de órdenes
        assert prod_code in widget.orders_widget.title_label.text()
        # Verificar que se llamó a actualizar gráficas (al menos una llamada)
        assert mock_controller.model.get_product_time_stats.call_count >= 1
        mock_controller.model.get_product_time_stats.assert_called_with(prod_code)

    def test_order_search_updates_widgets_via_product(self, widget, mock_controller):
        """Verifica que seleccionar una orden busca su producto y actualiza todo."""
        # Arrange
        order_code = "OF-999"
        prod_code = "PROD-FROM-ORDER"
        
        detalle_mock = OrdenFabricacionDetalleDTO(
            orden_fabricacion=order_code,
            producto_codigo=prod_code,
            producto_descripcion="Desc",
            fecha_inicio=datetime.now(),
        )
        mock_controller.model.get_order_details.return_value = detalle_mock
        mock_controller.model.get_orders_for_product.return_value = []
        
        # Act
        widget.search_widget.result_selected.emit('orden', order_code)
        # Assert
        assert mock_controller.model.get_order_details.call_count >= 1
        mock_controller.model.get_order_details.assert_called_with(order_code)
        assert mock_controller.model.get_orders_for_product.call_count >= 1
        mock_controller.model.get_orders_for_product.assert_called_with(prod_code)
        assert prod_code in widget.orders_widget.title_label.text()
        
    def test_clear_search_clears_widgets(self, widget):
        """Verifica que limpiar la búsqueda limpia los sub-widgets."""
        # Arrange - Poner algo de estado
        widget.orders_widget.title_label.setText("DIRTY")
        widget.charts_widget.title_label.setText("DIRTY")
        # Act
        widget.search_widget.search_cleared.emit()
        # Assert
        assert "Órdenes de Fabricación" in widget.orders_widget.title_label.text()
        assert "Análisis de Producción" in widget.charts_widget.title_label.text()
