# -*- coding: utf-8 -*-
"""Tests unitarios para PreprocesosWidget.

Cubre PreprocesosWidget: init, set_controller, carga/filtro lista, selección,
botones añadir/editar/eliminar y comportamiento sin controlador. Mocks con spec.
"""
import pytest
from unittest.mock import MagicMock, patch, create_autospec

from controllers.product_controller_v2 import ProductController
from core.di_container import DIContainer
from core.services.fabricacion_service import FabricacionService
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt

from ui.widgets.preprocesos_widget import PreprocesosWidget

pytestmark = pytest.mark.unit


class TestPreprocesosWidget:
    """Tests unitarios para PreprocesosWidget."""

    @pytest.fixture
    def widget(self, qtbot):
        """Fixture para PreprocesosWidget."""
        ctrl = create_autospec(ProductController, instance=True)
        DIContainer.get_instance().register(ProductController, instance=ctrl)
        w = PreprocesosWidget()
        qtbot.addWidget(w)
        return w

    def test_init(self, widget):
        """Widget se inicializa correctamente."""
        assert widget.preprocesos_data_cache == []
        assert widget.current_preproceso_id is None

    def test_set_controller(self, widget):
        """set_controller es compat MainView; no altera el ProductController del DI."""
        ctrl = object()
        pc = widget.preproceso_controller
        widget.set_controller(ctrl)
        assert widget.preproceso_controller is pc

    def test_load_preprocesos_data(self, widget):
        """Carga datos de preprocesos en la lista."""
        p1 = MagicMock(spec=['id', 'nombre', 'tiempo', 'descripcion'])
        p1.id = 1; p1.nombre = "Corte"; p1.tiempo = 10; p1.descripcion = "Desc"
        p2 = MagicMock(spec=['id', 'nombre', 'tiempo', 'descripcion'])
        p2.id = 2; p2.nombre = "Soldadura"; p2.tiempo = 20; p2.descripcion = "Desc2"
        widget.load_preprocesos_data([p1, p2])
        assert widget.preprocesos_list.count() == 2

    def test_filter_list(self, widget):
        """Filtra preprocesos por texto."""
        p1 = MagicMock(spec=['id', 'nombre', 'tiempo', 'descripcion'])
        p1.id = 1; p1.nombre = "Corte"; p1.tiempo = 10; p1.descripcion = ""
        widget.load_preprocesos_data([p1])
        widget.search_entry.setText("soldadura")
        assert widget.preprocesos_list.item(0).isHidden()

    def test_on_item_selected(self, widget):
        """Seleccionar item muestra detalles."""
        p1 = MagicMock(spec=['id', 'nombre', 'tiempo', 'descripcion'])
        p1.id = 1; p1.nombre = "Corte"; p1.tiempo = 10; p1.descripcion = "Desc"
        widget.load_preprocesos_data([p1])
        widget._on_item_selected(widget.preprocesos_list.item(0))
        assert widget.current_preproceso_id == 1
        assert widget.edit_button.isEnabled()
        assert widget.delete_button.isEnabled()

    def test_on_item_selected_not_found(self, widget):
        """Seleccionar item no encontrado muestra placeholder."""
        item = QListWidgetItem("Test")
        item.setData(Qt.ItemDataRole.UserRole, 999)
        widget.preprocesos_list.addItem(item)
        widget._on_item_selected(item)
        assert widget.current_preproceso_id is None

    def test_show_placeholder_details(self, widget):
        """Placeholder desactiva botones."""
        widget._show_placeholder_details()
        assert not widget.edit_button.isEnabled()
        assert not widget.delete_button.isEnabled()

    def test_on_add_clicked(self, widget):
        """Botón añadir llama al controlador."""
        ctrl = MagicMock(spec=['show_add_preproceso_dialog'])
        widget.preproceso_controller = ctrl
        widget._on_add_clicked()
        ctrl.show_add_preproceso_dialog.assert_called_once_with()

    def test_on_edit_clicked(self, widget):
        """Botón editar llama al controlador."""
        p1 = MagicMock(spec=['id', 'nombre', 'tiempo', 'descripcion'])
        p1.id = 1; p1.nombre = "Corte"; p1.tiempo = 10; p1.descripcion = ""
        widget.load_preprocesos_data([p1])
        widget._on_item_selected(widget.preprocesos_list.item(0))
        ctrl = MagicMock(spec=['show_edit_preproceso_dialog'])
        widget.preproceso_controller = ctrl
        widget._on_edit_clicked()
        ctrl.show_edit_preproceso_dialog.assert_called_once_with(p1)

    def test_on_delete_clicked(self, widget):
        """Botón eliminar llama al controlador."""
        p1 = MagicMock(spec=['id', 'nombre', 'tiempo', 'descripcion'])
        p1.id = 1; p1.nombre = "Corte"; p1.tiempo = 10; p1.descripcion = ""
        widget.load_preprocesos_data([p1])
        widget._on_item_selected(widget.preprocesos_list.item(0))
        ctrl = MagicMock(spec=['delete_preproceso'])
        widget.preproceso_controller = ctrl
        widget._on_delete_clicked()
        ctrl.delete_preproceso.assert_called_once_with(1, "Corte")

    def test_on_add_no_controller(self, widget):
        """Botón añadir sin controlador no crashea."""
        widget.preproceso_controller = None
        try:
            widget._on_add_clicked()
        except Exception:
            pytest.fail("_on_add_clicked no debería propagar excepciones sin controlador")
        assert widget.preproceso_controller is None

    def test_on_edit_no_controller(self, widget):
        """Botón editar sin controlador no crashea."""
        widget.preproceso_controller = None
        try:
            widget._on_edit_clicked()
        except Exception:
            pytest.fail("_on_edit_clicked no debería propagar excepciones sin controlador")
        assert widget.preproceso_controller is None

    def test_assign_to_fabricaciones_no_fabricacion_service(self, widget):
        """Sin FabricacionService resoluble el manejador no abre diálogo."""
        with patch(
            "ui.dialogs.fabrication.dialog_dependencies.resolve_fabricacion_service",
            return_value=None,
        ), patch(
            "ui.dialogs.fabrication.assignment_dialogs.AssignPreprocesosDialog",
        ) as MockDlg:
            widget._on_assign_to_fabricaciones_clicked()
        MockDlg.assert_not_called()

    def test_assign_to_fabricaciones_opens_dialog(self, widget):
        """Se resuelve FabricacionService por DI y se abre el diálogo con ProductController."""
        sentinel = create_autospec(FabricacionService, instance=True)
        with patch(
            "ui.dialogs.fabrication.assignment_dialogs.AssignPreprocesosDialog",
        ) as MockDlg, patch(
            "ui.dialogs.fabrication.dialog_dependencies.resolve_fabricacion_service",
            return_value=sentinel,
        ) as mock_res:
            inst = MockDlg.return_value
            widget._on_assign_to_fabricaciones_clicked()
            mock_res.assert_called_once_with(None, DIContainer.get_instance())
            MockDlg.assert_called_once_with(
                None,
                widget,
                fabricacion_service=sentinel,
                opens_fabricacion_preprocesos=widget.preproceso_controller,
            )
            inst.exec.assert_called_once_with()
