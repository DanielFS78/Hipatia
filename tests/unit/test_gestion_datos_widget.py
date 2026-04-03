# -*- coding: utf-8 -*-
"""Tests unitarios para GestionDatosWidget."""
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QWidget

from ui.widgets.gestion_datos_widget import GestionDatosWidget


@pytest.mark.unit
class TestGestionDatosWidget:
    """Tests unitarios para GestionDatosWidget."""

    @pytest.fixture
    def widget(self, qtbot):
        """Fixture para GestionDatosWidget sin controlador (tabs placeholder)."""
        w = GestionDatosWidget()
        qtbot.addWidget(w)
        return w

    def test_init_no_controller(self, widget):
        """Widget se inicializa con tabs placeholder sin controlador."""
        assert widget.tab_widget.count() == 5
        assert isinstance(widget.productos_tab, QWidget)

    def test_init_with_controller(self, qtbot):
        """Widget con controlador crea tabs reales."""
        ctrl = MagicMock(spec=["model"])
        ctrl.model = MagicMock(spec=["get_distinct_machine_processes"])
        ctrl.model.get_distinct_machine_processes.return_value = []
        with patch('ui.widgets.gestion_datos_widget.ProductsWidget') as MockProd, \
             patch('ui.widgets.gestion_datos_widget.FabricationsWidget') as MockFab, \
             patch('ui.widgets.gestion_datos_widget.MachinesWidget') as MockMach, \
             patch('ui.widgets.gestion_datos_widget.WorkersWidget') as MockWork, \
             patch('ui.widgets.gestion_datos_widget.LotesWidget') as MockLot:
            MockProd.return_value = QWidget()
            MockFab.return_value = QWidget()
            MockMach.return_value = QWidget()
            MockWork.return_value = QWidget()
            MockLot.return_value = QWidget()
            w = GestionDatosWidget(controller=ctrl)
            qtbot.addWidget(w)
            assert w.tab_widget is not None
            assert w.tab_widget.count() == 5

    def test_set_controller_propagates(self, widget):
        """set_controller propaga a sub-widgets."""
        ctrl = MagicMock(spec=[])
        widget.set_controller(ctrl)
        assert widget.controller is ctrl
