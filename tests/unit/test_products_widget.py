# -*- coding: utf-8 -*-
"""Tests unitarios para products_widget.py (AddProductWidget y ProductsWidget)."""
import pytest
from unittest.mock import MagicMock, patch

from PyQt6.QtCore import Qt

from core.dtos import ProductDTO
from ui.widgets.products_widget import ProductsWidget


def _make_product_dto(codigo="P1", descripcion="Producto 1"):
    """Crea un ProductDTO de prueba."""
    dto = MagicMock(spec=ProductDTO)
    dto.codigo = codigo
    dto.descripcion = descripcion
    return dto


def _make_product_data():
    """Crea un objeto de datos de producto simulado con atributos directos."""
    data = MagicMock(
        spec=[
            "codigo",
            "descripcion",
            "departamento",
            "donde",
            "tiene_subfabricaciones",
        ]
    )
    data.codigo = "P1"
    data.descripcion = "Producto Test"
    data.departamento = "Mecánica"
    data.donde = "Almacén A"
    data.tiene_subfabricaciones = True
    return data


def _make_sub_data():
    """Crea datos de subfabricaciones simulados."""
    sub = MagicMock(
        spec=[
            "id",
            "descripcion",
            "tiempo",
            "tipo_trabajador",
            "maquina_id",
        ]
    )
    sub.id = 1
    sub.descripcion = "Sub 1"
    sub.tiempo = 10
    sub.tipo_trabajador = 1
    sub.maquina_id = None
    return [sub]


@pytest.fixture
def controller():
    """Controller mock."""
    from core.di_container import DIContainer
    from controllers.product_controller_v2 import ProductController
    ctrl = MagicMock(spec=["product_service"])
    ctrl.product_service = MagicMock(spec=["get_product_iterations"])
    ctrl.product_service.get_product_iterations.return_value = []
    DIContainer.get_instance().register(ProductController, instance=ctrl)
    return ctrl


@pytest.mark.unit
class TestProductsWidget:
    """Tests unitarios para ProductsWidget."""

    @pytest.fixture
    def widget(self, qtbot, controller):
        """Instancia de ProductsWidget con controller mock."""
        w = ProductsWidget(controller)
        qtbot.addWidget(w)
        return w

    def test_init(self, widget):
        """Verifica inicialización correcta."""
        assert "Buscar o Añadir" in widget.search_entry.placeholderText()
        assert widget.results_list is not None
        assert widget.form_widgets == {}
        assert widget.current_subfabricaciones == []

    def test_search_or_add_signal_on_enter(self, qtbot, widget):
        """Verifica que la señal search_or_add_signal se emite al presionar Enter."""
        widget.search_entry.setText("NEWPROD")
        with qtbot.waitSignal(widget.search_or_add_signal, timeout=1000) as blocker:
            qtbot.keyClick(widget.search_entry, Qt.Key.Key_Return)
        assert blocker.args[0] == "NEWPROD"

    def test_update_search_results(self, widget):
        """Verifica que los resultados de búsqueda se muestran con DTOs."""
        products = [_make_product_dto("P1", "Producto 1")]
        widget.update_search_results(products)
        assert widget.results_list.count() == 1
        assert "P1" in widget.results_list.item(0).text()
        assert isinstance(products[0], ProductDTO)

    def test_update_search_results_with_iterations(self, widget, controller):
        """Verifica el ícono de iteraciones en resultados."""
        controller.product_service.get_product_iterations.return_value = ['iter1']
        products = [_make_product_dto("P1", "Producto 1")]
        widget.update_search_results(products)
        assert "📜" in widget.results_list.item(0).text()

    def test_clear_edit_area(self, widget):
        """Verifica limpieza del área de edición."""
        widget.clear_edit_area()
        assert widget.form_widgets == {}
        assert widget.current_subfabricaciones == []

    def _find_widget_by_text(self, layout, text):
        """Helper to find a widget by its text in a layout."""
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() and hasattr(item.widget(), "text") and text in item.widget().text():
                return item.widget()
            if item.layout():
                res = self._find_widget_by_text(item.layout(), text)
                if res: return res
        return None

    def test_display_product_form_existing(self, widget):
        """Verifica que el formulario de edición para producto existente se muestra correctamente."""
        data = _make_product_data()
        subs = _make_sub_data()

        widget.display_product_form(data, subs, is_new=False)
        assert widget.form_widgets['codigo'].text() == 'P1'
        assert widget.form_widgets['descripcion'].text() == 'Producto Test'
        assert widget.form_widgets['departamento'].currentText() == 'Mecánica'
        assert widget.form_widgets['sub_switch'].isChecked()
        assert len(widget.current_subfabricaciones) == 1
        
        save_btn = self._find_widget_by_text(widget.edit_area_container_layout, "Guardar Cambios")
        assert save_btn is not None

    def test_display_product_form_new(self, widget):
        """Verifica que el formulario para un producto nuevo se muestra correctamente."""
        widget.display_product_form("NEWP", [], is_new=True)
        assert widget.form_widgets['codigo'].text() == 'NEWP'
        assert widget.form_widgets['descripcion'].text() == ''
        assert not widget.form_widgets['sub_switch'].isChecked()
        assert widget.form_widgets['details_container'].isVisibleTo(widget)
        
        create_btn = self._find_widget_by_text(widget.edit_area_container_layout, "Crear Producto")
        assert create_btn is not None

    def test_get_product_form_data(self, widget):
        """Verifica la extracción de datos del formulario de edición."""
        data = _make_product_data()
        subs = _make_sub_data()
        widget.display_product_form(data, subs)

        form_data = widget.get_product_form_data()
        assert form_data['codigo'] == 'P1'
        assert form_data['tiene_subfabricaciones'] == 1
        assert len(form_data['sub_partes']) == 1

    def test_get_product_form_data_new(self, widget):
        """Verifica la extracción de datos para un producto nuevo sin subfabricaciones."""
        widget.display_product_form("NEWP", [], is_new=True)
        widget.form_widgets['descripcion'].setText("Desc")
        widget.form_widgets['sub_switch'].setChecked(False)
        widget.form_widgets['tiempo_optimo'].setText("10.5")
        widget.form_widgets['trabajador_menu'].setCurrentIndex(1) # Tipo 2

        form_data = widget.get_product_form_data()
        assert form_data['codigo'] == 'NEWP'
        assert form_data['descripcion'] == 'Desc'
        assert form_data['tiene_subfabricaciones'] == 0
        assert form_data['tiempo_optimo'] == '10.5'
        assert form_data['tipo_trabajador'] == '2'

    def test_clear_all(self, widget):
        """Verifica la limpieza total del widget."""
        widget.search_entry.setText("search")
        widget.clear_all()
        assert widget.search_entry.text() == ''
        assert widget.results_list.count() == 0

    def test_toggle_subs_visibility(self, widget):
        """Verifica que el botón de subfabricaciones y el contenedor de detalles se alternan."""
        data = _make_product_data()
        subs = _make_sub_data()
        widget.display_product_form(data, subs)

        # Initially checked (has subs), so button should be visible, details hidden
        assert widget.form_widgets['manage_subs_button'].isVisibleTo(widget)
        assert not widget.form_widgets['details_container'].isVisibleTo(widget)

        # Uncheck
        widget.form_widgets['sub_switch'].setChecked(False)
        assert not widget.form_widgets['manage_subs_button'].isVisibleTo(widget)
        assert widget.form_widgets['details_container'].isVisibleTo(widget)
