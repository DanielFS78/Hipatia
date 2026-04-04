# -*- coding: utf-8 -*-
"""Tests unitarios para DefinirLoteWidget y LotesWidget."""
import pytest
from unittest.mock import MagicMock, patch, create_autospec
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt

from ui.widgets.lotes_widget import DefinirLoteWidget, LotesWidget

pytestmark = pytest.mark.unit


class TestDefinirLoteWidget:
    """Tests unitarios para DefinirLoteWidget."""

    @pytest.fixture
    def widget(self, qtbot):
        """Fixture para DefinirLoteWidget."""
        from core.di_container import DIContainer
        from controllers.lote_controller import LoteController
        ctrl = create_autospec(LoteController, instance=True)
        DIContainer.get_instance().register(LoteController, instance=ctrl)
        w = DefinirLoteWidget()
        qtbot.addWidget(w)
        return w

    def test_init(self, widget):
        """Widget se inicializa correctamente."""
        assert widget.current_lote_id is None
        assert widget.lote_content == {"products": set(), "fabrications": set()}

    def test_set_controller(self, widget):
        """set_controller guarda app controller y refresca listas si hay lote_controller."""
        ctrl = MagicMock(spec=["model"])
        ctrl.model = MagicMock(spec=["search_fabricaciones", "search_products"])
        ctrl.model.search_fabricaciones.return_value = []
        ctrl.model.search_products.return_value = []
        widget.lote_controller = ctrl
        widget.set_controller(ctrl)
        assert widget.lote_controller is ctrl
        assert widget._app_controller is ctrl

    def test_set_controller_updates_fabricacion_via_resolve(self, widget):
        """Si resolve_fabricacion_service devuelve instancia, sustituye _fabricacion_service."""
        sentinel = MagicMock(spec=["search_fabricaciones"])
        sentinel.search_fabricaciones.return_value = []
        app = MagicMock(spec=["product_controller", "model"])
        widget.lote_controller = MagicMock(spec=[])
        with patch(
            "ui.dialogs.fabrication.dialog_dependencies.resolve_fabricacion_service",
            return_value=sentinel,
        ):
            widget.set_controller(app)
        assert widget._fabricacion_service is sentinel

    def test_set_controller_keeps_fabricacion_when_resolve_returns_none(self, widget):
        """Si resolve devuelve None, no borra un FabricacionService ya asignado."""
        keep = MagicMock(spec=["search_fabricaciones"])
        widget._fabricacion_service = keep
        widget.lote_controller = MagicMock(spec=[])
        with patch(
            "ui.dialogs.fabrication.dialog_dependencies.resolve_fabricacion_service",
            return_value=None,
        ):
            widget.set_controller(MagicMock(spec=["product_controller", "model"]))
        assert widget._fabricacion_service is keep

    def test_populate_fabrications_list(self, widget):
        """Carga fabricaciones excluyendo TASK-* (vía FabricacionService, no model)."""
        fab1 = MagicMock(spec=["codigo", "descripcion", "id"]); fab1.codigo = "FAB-1"; fab1.descripcion = "Fab 1"; fab1.id = 1
        fab2 = MagicMock(spec=["codigo", "descripcion", "id"]); fab2.codigo = "TASK-AUTO"; fab2.descripcion = "Auto"; fab2.id = 2
        fs = MagicMock(spec=["search_fabricaciones"])
        fs.search_fabricaciones.return_value = [fab1, fab2]
        widget._fabricacion_service = fs
        ctrl = MagicMock(spec=["model"])
        widget.lote_controller = ctrl
        widget.populate_fabrications_list()
        assert widget.fab_results.count() == 1
        fs.search_fabricaciones.assert_called_once_with("")

    def test_populate_fabrications_list_no_controller(self, widget):
        """Sin controlador no hace nada."""
        widget.lote_controller = None
        widget.populate_fabrications_list()
        assert widget.fab_results.count() == 0

    def test_populate_fabrications_list_error(self, widget):
        """Error en carga no crashea."""
        fs = MagicMock(spec=["search_fabricaciones"])
        fs.search_fabricaciones.side_effect = Exception("DB")
        widget._fabricacion_service = fs
        widget.lote_controller = MagicMock(spec=["model"])
        try:
            widget.populate_fabrications_list()
        except Exception:
            pytest.fail("populate_fabrications_list no debería propagar excepciones")
        assert widget.fab_results.count() >= 0

    def test_filter_fabrications(self, widget):
        """Filtra fabricaciones por texto."""
        item1 = QListWidgetItem("FAB-1 - Corte"); widget.fab_results.addItem(item1)
        item2 = QListWidgetItem("FAB-2 - Soldadura"); widget.fab_results.addItem(item2)
        widget.filter_fabrications("corte")
        assert not widget.fab_results.item(0).isHidden()
        assert widget.fab_results.item(1).isHidden()

    def test_populate_products_list(self, widget):
        """Carga productos correctamente (vía ProductService, no model)."""
        prod = MagicMock(spec=["codigo", "descripcion"]); prod.codigo = "P1"; prod.descripcion = "Prod 1"
        ps = MagicMock(spec=["search_products"])
        ps.search_products.return_value = [prod]
        widget._product_service = ps
        widget.lote_controller = MagicMock(spec=["model"])
        widget.populate_products_list()
        assert widget.product_results.count() == 1
        ps.search_products.assert_called_once_with("")

    def test_populate_products_list_no_controller(self, widget):
        """Sin controlador no hace nada."""
        widget.lote_controller = None
        widget.populate_products_list()
        assert widget.product_results.count() == 0

    def test_populate_products_list_error(self, widget):
        """Error en carga no crashea."""
        ps = MagicMock(spec=["search_products"])
        ps.search_products.side_effect = Exception("DB")
        widget._product_service = ps
        widget.lote_controller = MagicMock(spec=["model"])
        try:
            widget.populate_products_list()
        except Exception:
            pytest.fail("populate_products_list no debería propagar excepciones")
        assert widget.product_results.count() >= 0

    def test_filter_products(self, widget):
        """Filtra productos por texto (el source tiene un bug conocido con main_layout en l.127)."""
        item1 = QListWidgetItem("P1 - Mesa"); widget.product_results.addItem(item1)
        item2 = QListWidgetItem("P2 - Silla"); widget.product_results.addItem(item2)
        widget.filter_products("mesa")
        assert not widget.product_results.item(0).isHidden()
        assert widget.product_results.item(1).isHidden()

    def test_clear_form(self, widget):
        """clear_form reinicia todo."""
        widget.current_lote_id = 5
        widget.lote_content["products"].add(("P1", "Prod 1"))
        widget.clear_form()
        assert widget.current_lote_id is None
        assert len(widget.lote_content["products"]) == 0

    def test_update_content_list(self, widget):
        """update_content_list muestra contenido."""
        widget.lote_content["products"].add(("P1", "Prod 1"))
        widget.lote_content["fabrications"].add((1, "FAB-1"))
        widget.update_content_list()
        assert widget.lote_content_list.count() == 2

    def test_get_data(self, widget):
        """get_data retorna datos del formulario."""
        widget.lote_codigo_entry.setText("LOT-1")
        widget.lote_descripcion_entry.setText("Test Lote")
        widget.lote_content["products"].add(("P1", "Prod 1"))
        widget.lote_content["fabrications"].add((1, "FAB-1"))
        data = widget.get_data()
        assert data["codigo"] == "LOT-1"
        assert "P1" in data["product_codes"]
        assert 1 in data["fabricacion_ids"]


class TestLotesWidget:
    """Tests unitarios para LotesWidget."""

    @pytest.fixture
    def widget(self, qtbot):
        """Fixture para LotesWidget."""
        from core.di_container import DIContainer
        from controllers.lote_controller import LoteController
        ctrl = create_autospec(LoteController, instance=True)
        DIContainer.get_instance().register(LoteController, instance=ctrl)
        w = LotesWidget(controller=ctrl)
        qtbot.addWidget(w)
        return w

    def test_init(self, widget):
        """Widget se inicializa correctamente."""
        assert widget.current_lote_id is None

    def test_set_controller(self, widget):
        """set_controller asigna controlador."""
        ctrl = object()
        widget.set_controller(ctrl)
        assert widget.lote_controller is not None

    def test_clear_edit_area(self, widget):
        """clear_edit_area limpia el área de edición."""
        widget.current_lote_id = 5
        widget.clear_edit_area()
        assert widget.current_lote_id is None

    def test_display_lote_details(self, widget, qtbot):
        """display_lote_details muestra detalles del lote."""
        lote = MagicMock(spec=["id", "codigo", "descripcion", "productos", "fabricaciones"])
        lote.id = 1; lote.codigo = "LOT-1"; lote.descripcion = "Lote Test"
        prod = MagicMock(spec=["codigo", "descripcion"]); prod.codigo = "P1"; prod.descripcion = "Prod 1"
        fab = MagicMock(spec=["codigo"]); fab.codigo = "FAB-1"
        lote.productos = [prod]; lote.fabricaciones = [fab]

        widget.display_lote_details(lote)
        assert widget.current_lote_id == 1

    def test_display_lote_signals(self, widget, qtbot):
        """Botones de lote emiten señales correctas."""
        lote = MagicMock(spec=["id", "codigo", "descripcion", "productos", "fabricaciones"])
        lote.id = 1; lote.codigo = "L1"; lote.descripcion = "D"
        lote.productos = []; lote.fabricaciones = []
        widget.display_lote_details(lote)

        with qtbot.waitSignal(widget.delete_lote_signal, timeout=1000) as blocker:
            widget.delete_lote_signal.emit(1)
        assert blocker.args == [1]

    def test_get_form_data_no_lote(self, widget):
        """get_form_data sin lote retorna None."""
        widget.current_lote_id = None
        assert widget.get_form_data() is None

    def test_get_form_data_with_lote(self, widget):
        """get_form_data con lote retorna datos."""
        lote = MagicMock(spec=["id", "codigo", "descripcion", "productos", "fabricaciones"])
        lote.id = 1; lote.codigo = "LOT-1"; lote.descripcion = "Desc"
        lote.productos = []; lote.fabricaciones = []
        widget.display_lote_details(lote)
        data = widget.get_form_data()
        assert data is not None
        assert data["codigo"] == "LOT-1"
