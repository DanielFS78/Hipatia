# -*- coding: utf-8 -*-
"""
Tests para ui/dialogs/fabrication/ — Subfase 6.D.1.

Cobertura de input_dialogs, persistence_dialogs, products_dialog,
selection_dialogs, assignment_dialogs y bitacora_dialog. Decisión de mocking:
controladores y modelos con spec mínimo; DTOs con spec de atributos usados.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import QWidget, QDialogButtonBox

pytestmark = pytest.mark.unit

from ui.dialogs.fabrication.input_dialogs import (
    GetLoteInstanceParametersDialog,
    GetOptimizationParametersDialog,
    GetUnitsDialog,
)
from ui.dialogs.fabrication.persistence_dialogs import (
    SavePilaDialog,
    LoadPilaDialog,
)
from ui.dialogs.fabrication.products_dialog import ProductsSelectionDialog
from ui.dialogs.fabrication.selection_dialogs import (
    PreprocesosSelectionDialog,
    PreprocesosForCalculationDialog,
)
from core.dtos import CalculationProductDTO


# ═══════════════════════════════════════════════════════════
# input_dialogs.py
# ═══════════════════════════════════════════════════════════

class TestGetLoteInstanceParametersDialog:
    def test_init_creates_widgets(self, qtbot):
        dialog = GetLoteInstanceParametersDialog("LOTE-001")
        qtbot.addWidget(dialog)
        assert dialog.windowTitle() == "Parámetros para Lote: LOTE-001"

    def test_get_data_returns_dto(self, qtbot):
        dialog = GetLoteInstanceParametersDialog("LOTE-001")
        qtbot.addWidget(dialog)
        dialog.identificador_entry.setText("Pedido A")
        dialog.units_spinbox.setValue(10)
        data = dialog.get_data()
        from core.dtos import LoteInstanceParametersDTO
        assert isinstance(data, LoteInstanceParametersDTO)
        assert data.identificador == "Pedido A"
        assert data.unidades == 10
        assert isinstance(data.deadline, date)

    def test_get_data_strips_whitespace(self, qtbot):
        dialog = GetLoteInstanceParametersDialog("LOTE-001")
        qtbot.addWidget(dialog)
        dialog.identificador_entry.setText("  Pedido B  ")
        data = dialog.get_data()
        assert data.identificador == "Pedido B"

    def test_accept_and_reject(self, qtbot):
        dialog = GetLoteInstanceParametersDialog("LOTE-001")
        qtbot.addWidget(dialog)
        with qtbot.waitSignal(dialog.rejected):
            dialog.reject()
        assert dialog.result() == 0  # QDialog.Rejected
        dialog2 = GetLoteInstanceParametersDialog("LOTE-002")
        qtbot.addWidget(dialog2)
        with qtbot.waitSignal(dialog2.accepted):
            dialog2.accept()
        assert dialog2.result() == 1  # QDialog.Accepted


class TestGetOptimizationParametersDialog:
    def test_init(self, qtbot):
        dialog = GetOptimizationParametersDialog()
        qtbot.addWidget(dialog)
        assert dialog.windowTitle() == "Parámetros de Optimización"
        assert dialog.units_spinbox.value() == 1

    def test_get_parameters(self, qtbot):
        dialog = GetOptimizationParametersDialog()
        qtbot.addWidget(dialog)
        dialog.units_spinbox.setValue(5)
        params = dialog.get_parameters()
        assert params["units"] == 5
        assert isinstance(params["start_date"], date)
        assert isinstance(params["end_date"], date)

    def test_accept_reject(self, qtbot):
        dialog = GetOptimizationParametersDialog()
        qtbot.addWidget(dialog)
        with qtbot.waitSignal(dialog.accepted):
            dialog.accept()
        assert dialog.result() == 1  # QDialog.Accepted
        dialog2 = GetOptimizationParametersDialog()
        qtbot.addWidget(dialog2)
        with qtbot.waitSignal(dialog2.rejected):
            dialog2.reject()
        assert dialog2.result() == 0  # QDialog.Rejected


class TestGetUnitsDialog:
    def test_init(self, qtbot):
        dialog = GetUnitsDialog()
        qtbot.addWidget(dialog)
        assert "Unidades" in dialog.windowTitle()
        assert dialog.units_spinbox.value() == 1

    def test_get_units(self, qtbot):
        dialog = GetUnitsDialog()
        qtbot.addWidget(dialog)
        dialog.units_spinbox.setValue(42)
        assert dialog.get_units() == 42

    def test_accept_reject(self, qtbot):
        dialog = GetUnitsDialog()
        qtbot.addWidget(dialog)
        with qtbot.waitSignal(dialog.accepted):
            dialog.accept()
        assert dialog.result() == 1  # QDialog.Accepted
        dialog2 = GetUnitsDialog()
        qtbot.addWidget(dialog2)
        with qtbot.waitSignal(dialog2.rejected):
            dialog2.reject()
        assert dialog2.result() == 0  # QDialog.Rejected


# ═══════════════════════════════════════════════════════════
# persistence_dialogs.py
# ═══════════════════════════════════════════════════════════

class TestSavePilaDialog:
    def test_init(self, qtbot):
        dialog = SavePilaDialog()
        qtbot.addWidget(dialog)
        assert "Guardar" in dialog.windowTitle()

    def test_get_data(self, qtbot):
        dialog = SavePilaDialog()
        qtbot.addWidget(dialog)
        dialog.nombre_edit.setText("  Mi Pila  ")
        dialog.descripcion_edit.setPlainText("  Descripción  ")
        nombre, desc = dialog.get_data()
        assert nombre == "Mi Pila"
        assert desc == "Descripción"

    def test_accept_reject(self, qtbot):
        dialog = SavePilaDialog()
        qtbot.addWidget(dialog)
        with qtbot.waitSignal(dialog.accepted):
            dialog.accept()
        assert dialog.result() == 1  # QDialog.Accepted
        dialog2 = SavePilaDialog()
        qtbot.addWidget(dialog2)
        with qtbot.waitSignal(dialog2.rejected):
            dialog2.reject()
        assert dialog2.result() == 0  # QDialog.Rejected


class TestLoadPilaDialog:
    def _make_pila_dto(self, id, nombre, descripcion):
        m = MagicMock(spec=['id', 'nombre', 'descripcion'])
        m.id = id
        m.nombre = nombre
        m.descripcion = descripcion
        return m

    def test_init_with_dto_objects(self, qtbot):
        pilas = [
            self._make_pila_dto(1, "Pila A", "Desc A"),
            self._make_pila_dto(2, "Pila B", None),
        ]
        dialog = LoadPilaDialog(pilas)
        qtbot.addWidget(dialog)
        assert dialog.list_widget.count() == 2

    def test_init_with_tuples(self, qtbot):
        pilas = [(1, "Pila A", "Desc A"), (2, "Pila B", None)]
        dialog = LoadPilaDialog(pilas)
        qtbot.addWidget(dialog)
        assert dialog.list_widget.count() == 2

    def test_get_selected_id_no_selection(self, qtbot):
        pilas = [self._make_pila_dto(1, "Pila A", "Desc A")]
        dialog = LoadPilaDialog(pilas)
        qtbot.addWidget(dialog)
        assert dialog.get_selected_id() is None

    def test_get_selected_id_with_selection(self, qtbot):
        pilas = [self._make_pila_dto(10, "Pila A", "Desc A")]
        dialog = LoadPilaDialog(pilas)
        qtbot.addWidget(dialog)
        dialog.list_widget.setCurrentRow(0)
        result = dialog.get_selected_id()
        assert result == 10

    @patch("ui.dialogs.fabrication.persistence_dialogs.QMessageBox.warning")
    def test_request_delete_no_selection(self, mock_warning, qtbot):
        from ui.dialogs.fabrication.persistence_dialogs import LoadPilaDialog
        pilas = [self._make_pila_dto(1, "Pila A", "Desc")]
        dialog = LoadPilaDialog(pilas)
        qtbot.addWidget(dialog)
        # No selection: should show warning, not accept
        dialog._request_delete()
        assert not dialog.delete_requested
        assert mock_warning.call_count == 1
        mock_warning.assert_called_once_with(
            dialog,
            "Selección Requerida",
            "Por favor, seleccione una pila para eliminar.",
        )

    def test_request_delete_with_selection(self, qtbot):
        pilas = [self._make_pila_dto(99, "Pila A", "Desc")]
        dialog = LoadPilaDialog(pilas)
        qtbot.addWidget(dialog)
        dialog.list_widget.setCurrentRow(0)
        with qtbot.waitSignal(dialog.accepted):
            dialog._request_delete()
        assert dialog.delete_requested
        assert dialog.get_selected_id() == 99


# ═══════════════════════════════════════════════════════════
# products_dialog.py
# ═══════════════════════════════════════════════════════════

def _make_product(codigo, descripcion):
    p = MagicMock(spec=['codigo', 'descripcion'])
    p.codigo = codigo
    p.descripcion = descripcion
    return p

def _make_assigned_dto(codigo, cantidad):
    d = MagicMock(spec=['producto_codigo', 'cantidad'])
    d.producto_codigo = codigo
    d.cantidad = cantidad
    return d


class TestProductsSelectionDialog:
    def test_init(self, qtbot):
        from typing import Any
        all_products: list[Any] = [_make_product("A", "Producto A"), _make_product("B", "Producto B")]
        assigned = [_make_assigned_dto("A", 3)]
        dialog = ProductsSelectionDialog((1, "FAB-001", "Desc"), all_products, assigned)
        qtbot.addWidget(dialog)
        assert "FAB-001" in dialog.windowTitle()
        assert "A" in dialog.assigned_products
        assert "B" not in dialog.assigned_products

    def test_assign_product(self, qtbot):
        all_products = [_make_product("A", "Producto A")]
        dialog = ProductsSelectionDialog((1, "FAB-001", None), all_products, [])
        qtbot.addWidget(dialog)
        dialog.available_list.setCurrentRow(0)
        dialog._assign_product()
        assert "A" in dialog.assigned_products

    def test_unassign_product(self, qtbot):
        all_products = [_make_product("A", "Producto A")]
        assigned = [_make_assigned_dto("A", 1)]
        dialog = ProductsSelectionDialog((1, "FAB-001", "Desc"), all_products, assigned)
        qtbot.addWidget(dialog)
        dialog.assigned_table.selectRow(0)
        dialog._unassign_product()
        assert "A" not in dialog.assigned_products

    def test_unassign_no_selection(self, qtbot):
        all_products = [_make_product("A", "Producto A")]
        assigned = [_make_assigned_dto("A", 1)]
        dialog = ProductsSelectionDialog((1, "FAB-001", "Desc"), all_products, assigned)
        qtbot.addWidget(dialog)
        dialog._unassign_product()  # Should do nothing without selection
        assert "A" in dialog.assigned_products

    def test_filter_available_list(self, qtbot):
        all_products = [_make_product("ABC", "Alpha"), _make_product("DEF", "Beta")]
        dialog = ProductsSelectionDialog((1, "FAB-001", "Desc"), all_products, [])
        qtbot.addWidget(dialog)
        dialog.search_entry.setText("alph")
        dialog._filter_available_list()
        # abc should be visible, def hidden
        item_abc = dialog.available_list.item(0)
        item_def = dialog.available_list.item(1)
        assert item_abc is not None
        assert item_def is not None
        assert not item_abc.isHidden()
        assert item_def.isHidden()

    def test_on_qty_changed(self, qtbot):
        all_products = [_make_product("A", "Producto A")]
        assigned = [_make_assigned_dto("A", 1)]
        dialog = ProductsSelectionDialog((1, "FAB-001", "Desc"), all_products, assigned)
        qtbot.addWidget(dialog)
        dialog._on_qty_changed("A", 5)
        _, qty = dialog.assigned_products["A"]
        assert qty == 5

    def test_on_qty_changed_nonexistent(self, qtbot):
        from typing import Any
        all_products: list[Any] = []
        dialog = ProductsSelectionDialog((1, "FAB-001", "Desc"), all_products, [])
        qtbot.addWidget(dialog)
        # Cambiar cantidad de un producto que no existe — no debe lanzar excepción
        try:
            dialog._on_qty_changed("Z", 10)
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción con código inexistente: {e}")
        assert dialog is not None

    def test_get_products_data(self, qtbot):
        all_products = [_make_product("A", "P-A"), _make_product("B", "P-B")]
        assigned = [_make_assigned_dto("A", 2)]
        dialog = ProductsSelectionDialog((1, "FAB-001", "Desc"), all_products, assigned)
        qtbot.addWidget(dialog)
        data = dialog.get_products_data()
        assert any(p.producto_codigo == "A" and p.cantidad == 2 for p in data)

    def test_assigned_product_not_in_all_products(self, qtbot):
        """Test edge case: assigned_products_dtos has code not in all_products."""
        all_products = [_make_product("A", "P-A")]
        assigned = [_make_assigned_dto("Z", 1)]  # Z not in all_products
        dialog = ProductsSelectionDialog((1, "FAB-001", None), all_products, assigned)
        qtbot.addWidget(dialog)
        assert "Z" not in dialog.assigned_products  # Was silently skipped


# ═══════════════════════════════════════════════════════════
# selection_dialogs.py
# ═══════════════════════════════════════════════════════════

def _make_preproceso(id, nombre, descripcion="", componentes=None):
    p = MagicMock(spec=["id", "nombre", "descripcion", "componentes"])
    p.id = id
    p.nombre = nombre
    p.descripcion = descripcion
    p.componentes = componentes or []
    return p


class TestPreprocesosSelectionDialog:
    def test_init_no_preprocesos(self, qtbot):
        fabricacion = MagicMock(spec=["codigo", "descripcion"])
        fabricacion.codigo = "FAB-001"
        fabricacion.descripcion = "Desc"
        dialog = PreprocesosSelectionDialog(fabricacion, [], [])
        qtbot.addWidget(dialog)
        assert "FAB-001" in dialog.windowTitle()

    def test_init_with_object_fabricacion(self, qtbot):
        fab = MagicMock(spec=["codigo", "descripcion"])
        fab.codigo = "FAB-001"
        fab.descripcion = "Desc"
        preps = [_make_preproceso(1, "Prep A"), _make_preproceso(2, "Prep B")]
        dialog = PreprocesosSelectionDialog(fab, preps, [1])
        qtbot.addWidget(dialog)
        assert dialog.checkboxes[1].isChecked()
        assert not dialog.checkboxes[2].isChecked()

    def test_init_with_tuple_fabricacion(self, qtbot):
        fab = (1, "FAB-002", "Desc")
        preps = [
            _make_preproceso(5, "Prep X", descripcion="Tiene Descripcion", componentes=[MagicMock(descripcion="Comp1")])
        ]
        dialog = PreprocesosSelectionDialog(fab, preps, [5])
        qtbot.addWidget(dialog)
        assert dialog.checkboxes[5].isChecked()

    def test_get_selected_preprocesos(self, qtbot):
        fab = MagicMock(spec=["codigo", "descripcion"])
        fab.codigo = "FAB-001"
        fab.descripcion = None
        preps = [_make_preproceso(1, "A"), _make_preproceso(2, "B")]
        dialog = PreprocesosSelectionDialog(fab, preps, [])
        qtbot.addWidget(dialog)
        dialog.checkboxes[1].setChecked(True)
        assert dialog.get_selected_preprocesos() == [1]

    def test_accept_reject(self, qtbot):
        fab = MagicMock(spec=["codigo", "descripcion"])
        fab.codigo = "F"
        fab.descripcion = ""
        dialog = PreprocesosSelectionDialog(fab, [], [])
        qtbot.addWidget(dialog)
        with qtbot.waitSignal(dialog.accepted):
            dialog.accept()
        assert dialog.result() == 1  # QDialog.Accepted


class TestPreprocesosForCalculationDialog:
    def _prep_dto(self, nombre, descripcion="", componentes=None):
        # En producción vendrá como DTO ya normalizado.
        return CalculationProductDTO(
            codigo="P1",
            descripcion=nombre,
            departamento="D1",
            tipo_trabajador=1,
            donde="Taller",
            tiene_subfabricaciones=False,
            tiempo_optimo=10.0,
            sub_partes=[],
            cantidad_en_kit=1
        )

    def test_init_with_no_preprocesos(self, qtbot):
        dialog = PreprocesosForCalculationDialog(1, [])
        qtbot.addWidget(dialog)
        assert dialog.preprocesos_list.count() == 1  # "No hay..." item

    def test_init_with_preprocesos(self, qtbot):
        preps = [
            self._prep_dto("Prep A", "Desc", [(1, "Comp1"), (2, "Comp2")]),
            self._prep_dto("Prep B"),
        ]
        dialog = PreprocesosForCalculationDialog(1, preps)
        qtbot.addWidget(dialog)
        assert dialog.preprocesos_list.count() == 2

    def test_select_all(self, qtbot):
        preps = [self._prep_dto("A"), self._prep_dto("B")]
        dialog = PreprocesosForCalculationDialog(1, preps)
        qtbot.addWidget(dialog)
        dialog.select_all()
        assert len(dialog.preprocesos_list.selectedItems()) == 2

    def test_clear_selection(self, qtbot):
        preps = [self._prep_dto("A"), self._prep_dto("B")]
        dialog = PreprocesosForCalculationDialog(1, preps)
        qtbot.addWidget(dialog)
        dialog.select_all()
        dialog.clear_selection()
        assert len(dialog.preprocesos_list.selectedItems()) == 0

    def test_get_selected_preprocesos(self, qtbot):
        preps = [self._prep_dto("A"), self._prep_dto("B")]
        dialog = PreprocesosForCalculationDialog(1, preps)
        qtbot.addWidget(dialog)
        dialog.select_all()
        result = dialog.get_selected_preprocesos()
        assert len(result) == 2
        assert result[0].descripcion == "A"

    def test_accept_reject(self, qtbot):
        dialog = PreprocesosForCalculationDialog(1, [])
        qtbot.addWidget(dialog)
        with qtbot.waitSignal(dialog.accepted):
            dialog.accept()
        assert dialog.result() == 1  # QDialog.Accepted
        dialog2 = PreprocesosForCalculationDialog(1, [])
        qtbot.addWidget(dialog2)
        with qtbot.waitSignal(dialog2.rejected):
            dialog2.reject()
        assert dialog2.result() == 0  # QDialog.Rejected


# ═══════════════════════════════════════════════════════════
# assignment_dialogs.py
# ═══════════════════════════════════════════════════════════

class TestAssignPreprocesosDialog:
    def _make_controller(self, fabricaciones=None, preprocesos=None):
        ctrl = MagicMock(
            spec=['search_fabricaciones', 'model', 'show_fabricacion_preprocesos', 'product_controller']
        )
        fab_list = fabricaciones or []
        ctrl.search_fabricaciones.return_value = fab_list
        prep_list = preprocesos or []
        fs = MagicMock(spec=['get_preprocesos_by_fabricacion'])
        fs.get_preprocesos_by_fabricacion.return_value = prep_list
        pc = MagicMock(spec=['fabricacion_service'])
        pc.fabricacion_service = fs
        ctrl.product_controller = pc
        ctrl.model = MagicMock(spec=['get_preprocesos_by_fabricacion'])
        ctrl.model.get_preprocesos_by_fabricacion.return_value = prep_list
        return ctrl

    def _make_prep_dto(self, id, nombre, descripcion):
        m = MagicMock(spec=['id', 'nombre', 'descripcion'])
        m.id = id
        m.nombre = nombre
        m.descripcion = descripcion
        return m

    def test_init_no_fabricaciones(self, qtbot):
        from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
        ctrl = self._make_controller()
        dialog = AssignPreprocesosDialog(ctrl)
        qtbot.addWidget(dialog)
        assert dialog.fabricaciones_list.count() == 1  # "No hay..." item

    def test_init_with_fabricaciones(self, qtbot):
        from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
        fab1 = MagicMock(spec=['codigo', 'descripcion', 'id'])
        fab1.codigo = "FAB-001"
        fab1.descripcion = "Desc"
        fab1.id = 1
        ctrl = self._make_controller([fab1])
        dialog = AssignPreprocesosDialog(ctrl)
        qtbot.addWidget(dialog)
        assert dialog.fabricaciones_list.count() == 1

    def test_init_with_fabricaciones_no_desc(self, qtbot):
        from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
        fab1 = MagicMock(spec=['codigo', 'descripcion', 'id'])
        fab1.codigo = "FAB-002"
        fab1.descripcion = None
        fab1.id = 2
        ctrl = self._make_controller([fab1])
        dialog = AssignPreprocesosDialog(ctrl)
        qtbot.addWidget(dialog)
        assert dialog.fabricaciones_list.count() == 1

    def test_on_fabricacion_selected_no_item(self, qtbot):
        from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
        ctrl = self._make_controller()
        dialog = AssignPreprocesosDialog(ctrl)
        qtbot.addWidget(dialog)
        dialog.on_fabricacion_selected()  # Should not crash
        assert not dialog.modify_button.isEnabled()

    def test_on_fabricacion_selected_with_item(self, qtbot):
        from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
        fab1 = MagicMock(spec=['codigo', 'descripcion', 'id'])
        fab1.codigo = "FAB-001"
        fab1.descripcion = "Desc"
        fab1.id = 10
        ctrl = self._make_controller([fab1])
        dialog = AssignPreprocesosDialog(ctrl)
        qtbot.addWidget(dialog)
        dialog.fabricaciones_list.setCurrentRow(0)
        assert dialog.modify_button.isEnabled()

    def test_load_current_preprocesos_empty(self, qtbot):
        from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
        ctrl = self._make_controller(preprocesos=[])
        dialog = AssignPreprocesosDialog(ctrl)
        qtbot.addWidget(dialog)
        dialog.load_current_preprocesos(1)
        assert dialog.current_preprocesos_list.count() == 1  # "Sin preprocesos" item

    def test_load_current_preprocesos_with_data(self, qtbot):
        from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
        prep = self._make_prep_dto(1, "Prep A", "Desc A")
        ctrl = self._make_controller(preprocesos=[prep])
        dialog = AssignPreprocesosDialog(ctrl)
        qtbot.addWidget(dialog)
        dialog.load_current_preprocesos(1)
        assert dialog.current_preprocesos_list.count() == 1

    def test_load_current_preprocesos_no_desc(self, qtbot):
        from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
        prep = self._make_prep_dto(1, "Prep A", None)
        ctrl = self._make_controller(preprocesos=[prep])
        dialog = AssignPreprocesosDialog(ctrl)
        qtbot.addWidget(dialog)
        dialog.load_current_preprocesos(1)
        assert dialog.current_preprocesos_list.count() == 1

    def test_modify_selected_fabricacion_no_item(self, qtbot):
        from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
        ctrl = self._make_controller()
        dialog = AssignPreprocesosDialog(ctrl)
        qtbot.addWidget(dialog)
        dialog.modify_selected_fabricacion()  # Should not crash
        assert ctrl.show_fabricacion_preprocesos.call_count == 0
        ctrl.show_fabricacion_preprocesos.assert_not_called()

    def test_modify_selected_fabricacion_with_item(self, qtbot):
        from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
        fab1 = MagicMock(spec=['codigo', 'descripcion', 'id'])
        fab1.codigo = "FAB-001"
        fab1.descripcion = "Desc"
        fab1.id = 5
        ctrl = self._make_controller([fab1])
        dialog = AssignPreprocesosDialog(ctrl)
        qtbot.addWidget(dialog)
        dialog.fabricaciones_list.setCurrentRow(0)
        dialog.modify_selected_fabricacion()
        assert ctrl.show_fabricacion_preprocesos.call_count == 1
        ctrl.show_fabricacion_preprocesos.assert_called_once_with(5)

    @patch("ui.dialogs.fabrication.assignment_dialogs.QMessageBox.critical")
    def test_load_fabricaciones_exception(self, mock_critical, qtbot):
        from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
        ctrl = MagicMock(spec=['search_fabricaciones', 'model'])
        ctrl.search_fabricaciones.side_effect = Exception("DB Error")
        ctrl.model = MagicMock(spec=['get_preprocesos_by_fabricacion'])
        dialog = AssignPreprocesosDialog(ctrl)
        qtbot.addWidget(dialog)
        # Should handle gracefully (no crash)
        assert mock_critical.call_count == 1
        mock_critical.assert_called_once_with(dialog, "Error", "Error cargando fabricaciones: DB Error")

    @patch("ui.dialogs.fabrication.assignment_dialogs.QMessageBox.critical")
    def test_load_current_preprocesos_exception(self, mock_critical, qtbot):
        from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
        ctrl = MagicMock(spec=['search_fabricaciones', 'product_controller'])
        ctrl.search_fabricaciones.return_value = []
        fs = MagicMock(spec=['get_preprocesos_by_fabricacion'])
        fs.get_preprocesos_by_fabricacion.side_effect = Exception("DB Error")
        pc = MagicMock(spec=['fabricacion_service'])
        pc.fabricacion_service = fs
        ctrl.product_controller = pc
        dialog = AssignPreprocesosDialog(ctrl)
        qtbot.addWidget(dialog)
        dialog.load_current_preprocesos(1)
        assert mock_critical.call_count == 1
        mock_critical.assert_called_once_with(
            dialog,
            "Error",
            "Error cargando preprocesos de la fabricación: DB Error",
        )
