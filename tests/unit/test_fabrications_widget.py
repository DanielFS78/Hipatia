# -*- coding: utf-8 -*-
"""Tests unitarios para FabricationsWidget.

Cubre FabricationsWidget: inicialización, búsqueda, formulario de fabricación,
datos del formulario, señales create/save. Controller mockeado (no Qt).
"""
import pytest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt

from ui.widgets.fabrications_widget import FabricationsWidget

pytestmark = pytest.mark.unit


class TestFabricationsWidget:
    """Tests unitarios para FabricationsWidget."""

    @pytest.fixture
    def widget(self, qtbot):
        """Fixture para FabricationsWidget."""
        w = FabricationsWidget()
        qtbot.addWidget(w)
        return w

    def test_init(self, widget):
        """Widget se inicializa correctamente."""
        assert widget.current_fabricacion_id is None
        assert widget.form_widgets == {}

    def test_update_search_results(self, widget):
        """Actualiza resultados de búsqueda."""
        fab1 = MagicMock(spec=['codigo', 'descripcion', 'id'])
        fab1.codigo = "FAB-1"; fab1.descripcion = "Desc 1"; fab1.id = 1
        fab2 = MagicMock(spec=['codigo', 'descripcion', 'id'])
        fab2.codigo = "FAB-2"; fab2.descripcion = "Desc 2"; fab2.id = 2
        widget.update_search_results([fab1, fab2])
        assert widget.results_list.count() == 2

    def test_clear_edit_area(self, widget):
        """Limpia el área de edición."""
        widget.clear_edit_area()
        assert widget.form_widgets == {}

    def test_display_fabricacion_form(self, widget):
        """Muestra formulario de fabricación."""
        data = MagicMock(spec=['id', 'codigo', 'descripcion', 'productos', 'fabricaciones'])
        data.id = 1; data.codigo = "FAB-1"; data.descripcion = "Desc"
        data.productos = []; data.fabricaciones = []
        prep = MagicMock(spec=['nombre', 'descripcion'])
        prep.nombre = "Corte"; prep.descripcion = "Desc prep"
        widget.display_fabricacion_form(data, [prep])
        assert widget.current_fabricacion_id == 1
        assert widget.form_widgets['codigo'].text() == "FAB-1"

    def test_display_fabricacion_form_with_products(self, widget):
        """Muestra fabricación con productos asignados."""
        data = MagicMock(spec=['id', 'codigo', 'descripcion', 'productos', 'fabricaciones'])
        data.id = 2; data.codigo = "FAB-2"; data.descripcion = "Desc"
        prod = MagicMock(spec=['producto_codigo', 'cantidad', 'descripcion'])
        prod.producto_codigo = "P1"; prod.cantidad = 5; prod.descripcion = "Prod"
        data.productos = [prod]
        widget.display_fabricacion_form(data, [])
        assert widget.form_widgets['productos_list'].count() == 1

    def test_get_fabricacion_form_data_empty(self, widget):
        """get_fabricacion_form_data sin formulario retorna None."""
        assert widget.get_fabricacion_form_data() is None

    def test_get_fabricacion_form_data(self, widget):
        """get_fabricacion_form_data retorna datos del formulario."""
        data = MagicMock(spec=['id', 'codigo', 'descripcion', 'productos', 'fabricaciones'])
        data.id = 1; data.codigo = "FAB-1"; data.descripcion = "Desc"
        data.productos = []
        widget.display_fabricacion_form(data, [])
        form_data = widget.get_fabricacion_form_data()
        assert form_data.codigo == "FAB-1"
        assert form_data.id == 1

    def test_clear_all(self, widget):
        """clear_all limpia búsqueda, resultados y edición."""
        widget.search_entry.setText("test")
        widget.results_list.addItem(QListWidgetItem("item"))
        widget.clear_all()
        assert widget.search_entry.text() == ""
        assert widget.results_list.count() == 0

    def test_create_signal(self, widget, qtbot):
        """Botón crear emite create_fabricacion_signal."""
        with qtbot.waitSignal(widget.create_fabricacion_signal, timeout=1000) as blocker:
            widget.create_button.click()
        assert blocker.signal_triggered

    def test_save_signal(self, widget, qtbot):
        """save_fabricacion_signal se emite."""
        with qtbot.waitSignal(widget.save_fabricacion_signal, timeout=1000) as blocker:
            widget.save_fabricacion_signal.emit(1)
        assert blocker.args == [1]
