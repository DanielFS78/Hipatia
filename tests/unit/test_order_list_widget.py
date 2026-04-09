# -*- coding: utf-8 -*-
"""Tests unitarios para OrderListWidget: estado inicial, load_orders, señales."""
import pytest
from PyQt6.QtCore import Qt
from unittest.mock import create_autospec
from ui.widgets.reports.order_list import OrderListWidget
from core.reports_dtos import OrdenFabricacionResumenDTO
from core.services.report_service import ReportService
from datetime import datetime

pytestmark = pytest.mark.unit


class TestOrderListWidget:
    """Tests para el widget de lista de órdenes."""

    @pytest.fixture
    def mock_report_service(self):
        return create_autospec(ReportService, instance=True)

    @pytest.fixture
    def widget(self, qtbot, mock_report_service):
        widget = OrderListWidget(report_service=mock_report_service)
        qtbot.addWidget(widget)
        return widget

    def test_initial_state(self, widget):
        """Verifica el estado inicial."""
        assert 'Órdenes de Fabricación' in widget.title_label.text()
        assert not widget.status_label.isHidden()
        assert widget._current_producto is None

    def test_load_orders(self, widget, mock_report_service, qtbot):
        """Verifica la carga de órdenes."""
        code = 'PROD-ABC'
        orders = [
            OrdenFabricacionResumenDTO('OF-1', code, 'Desc 1', datetime.now(), estado='completado'),
            OrdenFabricacionResumenDTO('OF-2', code, 'Desc 2', datetime.now(), estado='en_proceso')
        ]
        mock_report_service.get_orders_for_product.return_value = orders
        widget.load_orders_for_product(code)
        assert mock_report_service.get_orders_for_product.call_count >= 1
        mock_report_service.get_orders_for_product.assert_called_with(code)
        assert widget.status_label.isHidden()
        assert len(widget._order_cards) == 2
        assert code in widget.title_label.text()

    def test_load_empty_orders(self, widget, mock_report_service):
        """Verifica carga sin resultados."""
        mock_report_service.get_orders_for_product.return_value = []
        widget.load_orders_for_product('EMPTY')
        assert not widget.status_label.isHidden()
        assert 'No hay órdenes' in widget.status_label.text()
        assert len(widget._order_cards) == 0

    def test_selection_signal(self, widget, mock_report_service, qtbot):
        """Verifica la emisión de la señal al seleccionar."""
        orders = [OrdenFabricacionResumenDTO('OF-TEST', 'P1', 'D1', datetime.now())]
        mock_report_service.get_orders_for_product.return_value = orders
        widget.load_orders_for_product('P1')
        with qtbot.waitSignal(widget.order_selected) as blocker:
            card = widget._order_cards[0]
            qtbot.mouseClick(card, Qt.MouseButton.LeftButton)
        assert blocker.args == ['OF-TEST']

    def test_clear_reset(self, widget, mock_report_service):
        """Verifica el limpiado del widget."""
        mock_report_service.get_orders_for_product.return_value = [OrdenFabricacionResumenDTO('OF-1', 'P', 'D', datetime.now())]
        widget.load_orders_for_product('P')
        assert len(widget._order_cards) == 1
        widget.clear()
        assert len(widget._order_cards) == 0
        assert widget._current_producto is None
        assert 'Órdenes de Fabricación' in widget.title_label.text()
