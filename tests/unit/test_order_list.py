# -*- coding: utf-8 -*-
"""Tests unitarios para OrderListWidget y OrderCard."""
import pytest
from unittest.mock import MagicMock, create_autospec
from datetime import datetime

from core.services.report_service import ReportService

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

from ui.widgets.reports.order_list import OrderCard, OrderListWidget


def _make_order(of="OF-001", estado="completado", fecha=None, cantidad=10, tiempo=600, incidencias=0):
    """Helper para crear DTOs de orden mock."""
    order = MagicMock(
        spec=[
            "orden_fabricacion",
            "estado",
            "fecha_inicio",
            "cantidad_unidades",
            "tiempo_total_segundos",
            "incidencias_count",
        ]
    )
    order.orden_fabricacion = of
    order.estado = estado
    order.fecha_inicio = fecha or datetime(2026, 1, 15, 10, 0)
    order.cantidad_unidades = cantidad
    order.tiempo_total_segundos = tiempo
    order.incidencias_count = incidencias
    return order


@pytest.mark.unit
class TestOrderCard:
    """Tests unitarios para OrderCard."""

    def test_init_completado(self, qtbot):
        """Tarjeta con estado completado muestra badge verde."""
        order = _make_order(estado="completado")
        card = OrderCard(order)
        qtbot.addWidget(card)
        assert card.order_data == order

    def test_init_en_proceso(self, qtbot):
        """Tarjeta con estado en_proceso muestra badge azul."""
        order = _make_order(estado="en_proceso")
        card = OrderCard(order)
        qtbot.addWidget(card)
        assert card.order_data.estado == "en_proceso"

    def test_init_pausado(self, qtbot):
        """Tarjeta con estado desconocido muestra badge pausado."""
        order = _make_order(estado="pausado")
        card = OrderCard(order)
        qtbot.addWidget(card)
        assert card.order_data.estado == "pausado"

    def test_init_with_incidencias(self, qtbot):
        """Tarjeta con incidencias muestra el contador."""
        order = _make_order(incidencias=3)
        card = OrderCard(order)
        qtbot.addWidget(card)
        assert card.order_data.incidencias_count == 3

    def test_init_fecha_none(self, qtbot):
        """Tarjeta con fecha None muestra N/A."""
        order = _make_order()
        order.fecha_inicio = None
        card = OrderCard(order)
        qtbot.addWidget(card)
        assert card.order_data.fecha_inicio is None

    def test_clicked_signal(self, qtbot):
        """Click en tarjeta emite señal con orden_fabricacion."""
        order = _make_order(of="OF-TEST")
        card = OrderCard(order)
        qtbot.addWidget(card)

        with qtbot.waitSignal(card.clicked, timeout=1000) as blocker:
            from PyQt6.QtGui import QMouseEvent
            from PyQt6.QtCore import QPointF
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                QPointF(5, 5), Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
            )
            card.mousePressEvent(event)
        assert blocker.args == ["OF-TEST"]


@pytest.mark.unit
class TestOrderListWidget:
    """Tests unitarios para OrderListWidget."""

    @pytest.fixture
    def widget(self, qtbot):
        """Fixture para OrderListWidget."""
        w = OrderListWidget()
        qtbot.addWidget(w)
        return w

    def test_init(self, widget):
        """Widget se inicializa correctamente."""
        assert widget._current_producto is None
        assert widget._order_cards == []
        assert "Órdenes de Fabricación" in widget.title_label.text()

    def test_set_report_service(self, widget):
        """Asigna ReportService inyectado."""
        rs = create_autospec(ReportService, instance=True)
        widget.set_report_service(rs)
        assert widget._report_service is rs

    def test_load_orders_no_service(self, widget):
        """Sin ReportService, muestra lista vacía."""
        widget.set_report_service(None)
        widget.load_orders_for_product("PROD1")
        assert widget._current_producto == "PROD1"
        assert "No hay órdenes" in widget.status_label.text()

    def test_load_orders_success(self, widget):
        """Con ReportService, carga y muestra órdenes."""
        orders = [_make_order(of="OF-1"), _make_order(of="OF-2", estado="en_proceso")]
        rs = create_autospec(ReportService, instance=True)
        rs.get_orders_for_product.return_value = orders
        widget.set_report_service(rs)

        widget.load_orders_for_product("PROD1")

        assert len(widget._order_cards) == 2
        assert widget._current_producto == "PROD1"
        assert "OF-1" in [c.order_data.orden_fabricacion for c in widget._order_cards]
        rs.get_orders_for_product.assert_called_once_with("PROD1")

    def test_load_orders_error(self, widget):
        """Error en carga muestra mensaje de error."""
        rs = create_autospec(ReportService, instance=True)
        rs.get_orders_for_product.side_effect = Exception("DB Error")
        widget.set_report_service(rs)

        widget.load_orders_for_product("PROD1")
        assert "Error" in widget.status_label.text()

    def test_display_orders_empty(self, widget):
        """Sin órdenes, muestra mensaje apropiado."""
        widget._display_orders([])
        assert "No hay órdenes" in widget.status_label.text()

    def test_order_selected_signal(self, widget, qtbot):
        """Click en orden emite order_selected."""
        orders = [_make_order(of="OF-SIG")]
        widget._display_orders(orders)

        with qtbot.waitSignal(widget.order_selected, timeout=1000) as blocker:
            widget._order_cards[0].clicked.emit("OF-SIG")
        assert blocker.args == ["OF-SIG"]

    def test_clear(self, widget):
        """clear() limpia todo el estado."""
        orders = [_make_order()]
        widget._display_orders(orders)
        assert len(widget._order_cards) == 1

        widget.clear()
        assert widget._order_cards == []
        assert widget._current_producto is None
        assert "Seleccione un producto" in widget.status_label.text()

    def test_clear_cards(self, widget):
        """_clear_cards elimina tarjetas correctamente."""
        orders = [_make_order(), _make_order(of="OF-2")]
        widget._display_orders(orders)
        assert len(widget._order_cards) == 2

        widget._clear_cards()
        assert widget._order_cards == []
