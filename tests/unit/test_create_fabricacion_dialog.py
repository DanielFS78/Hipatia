# -*- coding: utf-8 -*-
"""
Tests unitarios para CreateFabricacionDialog y CreateFabricacionPresenter.

Verifica inicialización, validación, asignación de preprocesos/productos,
filtros y compatibilidad de propiedades. Decisión de mocking: view y datos
con spec mínimo para aislar el diálogo en headless.
"""
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QDialog, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

from ui.dialogs.fabrication.create_dialog import CreateFabricacionDialog
from ui.dialogs.fabrication.create_presenter import CreateFabricacionPresenter

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_view():
    """Vista mockeada con spec mínimo."""
    view = MagicMock(spec=['show_message'])
    view.show_message = MagicMock()
    return view

@pytest.fixture
def dialog_data():
    """Datos de preprocesos y productos para el diálogo."""
    preprocesos = [
        MagicMock(spec=['id', 'nombre', 'descripcion', 'componentes'], id=1, nombre="Prep 1", descripcion="Desc 1", componentes=[]),
        MagicMock(spec=['id', 'nombre', 'descripcion', 'componentes'], id=2, nombre="Prep 2", descripcion="Desc 2", componentes=[MagicMock(spec=['descripcion'], descripcion="C1")])
    ]
    productos = [
        MagicMock(spec=['codigo', 'descripcion'], codigo="P1", descripcion="Prod 1"),
        MagicMock(spec=['codigo', 'descripcion'], codigo="P2", descripcion="Prod 2")
    ]
    return preprocesos, productos

class TestCreateFabricacionDialog:
    def test_init(self, qtbot, dialog_data, mock_view):
        preps, prods = dialog_data
        # We pass None as parent to avoid MagicMock vs QWidget error
        dialog = CreateFabricacionDialog(preps, prods, None)
        # We can still mock the view methods afterwards if needed
        dialog.view = mock_view  # type: ignore[attr-defined]
        qtbot.addWidget(dialog)
        assert dialog.windowTitle() == "Crear Nueva Fabricación"
        assert dialog.prep_available_list.count() == 2
        assert dialog.prod_available_list.count() == 2

    def test_get_fabricacion_data_invalid(self, qtbot, dialog_data, mock_view):
        preps, prods = dialog_data
        dialog = CreateFabricacionDialog(preps, prods, None)
        dialog.view = mock_view  # type: ignore[attr-defined]
        qtbot.addWidget(dialog)
        dialog.codigo_entry.setText("") # Invalid empty code
        
        # Mock QMessageBox.warning
        with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog.validate_and_accept()
            assert mock_warn.call_count >= 1
            mock_warn.assert_called()

    def test_get_fabricacion_data_no_selection(self, qtbot, dialog_data, mock_view):
        preps, prods = dialog_data
        dialog = CreateFabricacionDialog(preps, prods, None)
        dialog.view = mock_view  # type: ignore[attr-defined]
        qtbot.addWidget(dialog)
        dialog.codigo_entry.setText("FAB-001")
        
        with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog.validate_and_accept()
            assert mock_warn.call_count >= 1
            mock_warn.assert_called()

    def test_get_fabricacion_data_success(self, qtbot, dialog_data, mock_view):
        preps, prods = dialog_data
        dialog = CreateFabricacionDialog(preps, prods, None)
        dialog.view = mock_view  # type: ignore[attr-defined]
        qtbot.addWidget(dialog)
        dialog.codigo_entry.setText("FAB-001")
        dialog.descripcion_entry.setText("Desc")
        
        # Assign preproceso (Row 0 is ID 2 because of reverse sort in presenter)
        dialog.prep_available_list.setCurrentRow(0)
        dialog._assign_preproceso() 
        
        # Assign product
        dialog.prod_available_list.setCurrentRow(0)
        dialog._assign_product()
        
        data = dialog.get_fabricacion_data()
        assert data.codigo == "FAB-001"
        assert data.descripcion == "Desc"
        assert data.preprocesos_ids is not None
        assert 2 in data.preprocesos_ids
        assert data.productos is not None
        assert len(data.productos) == 1

    def test_unassign_product(self, qtbot, dialog_data, mock_view):
        preps, prods = dialog_data
        dialog = CreateFabricacionDialog(preps, prods, None)
        dialog.view = mock_view  # type: ignore[attr-defined]
        qtbot.addWidget(dialog)
        
        dialog.prod_available_list.setCurrentRow(0)
        dialog._assign_product()
        assert dialog.prod_assigned_table.rowCount() == 1
        
        dialog.prod_assigned_table.selectRow(0)
        dialog._unassign_product()
        assert dialog.prod_assigned_table.rowCount() == 0

    def test_filter_preprocesos(self, qtbot, dialog_data, mock_view):
        preps, prods = dialog_data
        dialog = CreateFabricacionDialog(preps, prods, None)
        dialog.view = mock_view  # type: ignore[attr-defined]
        qtbot.addWidget(dialog)
        
        # Initial: Prep 1, Prep 2
        assert dialog.prep_available_list.count() == 2
        
        dialog.prep_search_entry.setText("Prep 2")
        # Should only have Prep 2 now (filtering clears and rebuilds)
        assert dialog.prep_available_list.count() == 1
        item0 = dialog.prep_available_list.item(0)
        assert item0 is not None
        assert "Prep 2" in item0.text()

    def test_filter_productos(self, qtbot, dialog_data, mock_view):
        preps, prods = dialog_data
        dialog = CreateFabricacionDialog(preps, prods, None)
        dialog.view = mock_view  # type: ignore[attr-defined]
        qtbot.addWidget(dialog)
        
        # Initial: P1, P2
        assert dialog.prod_available_list.count() == 2
        
        dialog.prod_search_entry.setText("Prod 1")
        # Should only have P1 now
        assert dialog.prod_available_list.count() == 1
        item0 = dialog.prod_available_list.item(0)
        assert item0 is not None
        assert "P1" in item0.text()

    def test_unassign_preproceso(self, qtbot, dialog_data, mock_view):
        preps, prods = dialog_data
        dialog = CreateFabricacionDialog(preps, prods, None)
        qtbot.addWidget(dialog)
        dialog.prep_available_list.setCurrentRow(0)
        dialog._assign_preproceso()
        assert dialog.prep_assigned_list.count() == 1
        
        dialog.prep_assigned_list.setCurrentRow(0)
        dialog._unassign_preproceso()
        assert dialog.prep_assigned_list.count() == 0

    def test_on_qty_changed(self, qtbot, dialog_data, mock_view):
        preps, prods = dialog_data
        dialog = CreateFabricacionDialog(preps, prods, None)
        qtbot.addWidget(dialog)
        dialog.prod_available_list.setCurrentRow(0)
        dialog._assign_product()
        
        # Trigger qty change for code "P1"
        dialog._on_qty_changed("P1", 10)
        # In the presenter, assigned_products stores (data, qty)
        assert dialog.presenter.assigned_products["P1"][1] == 10

    def test_accept_saves_data(self, qtbot, dialog_data, mock_view):
        preps, prods = dialog_data
        dialog = CreateFabricacionDialog(preps, prods, None)
        dialog.view = mock_view  # type: ignore[attr-defined]
        qtbot.addWidget(dialog)
        
        dialog.codigo_entry.setText("NEW-FAB")
        dialog.prep_available_list.setCurrentRow(0)
        dialog._assign_preproceso()
        
        with qtbot.waitSignal(dialog.accepted):
            dialog.validate_and_accept()
        
        data = dialog.get_fabricacion_data()
        assert data.codigo == "NEW-FAB"

    def test_backward_compatibility_properties(self, qtbot, dialog_data):
        preps, prods = dialog_data
        dialog = CreateFabricacionDialog(preps, prods, None)
        assert dialog.search_entry == dialog.prep_search_entry
        assert dialog.available_list == dialog.prep_available_list
        assert dialog.assigned_list == dialog.prep_assigned_list
        assert dialog.add_button == dialog.prep_add_button
        assert dialog.remove_button == dialog.prep_remove_button
        
        # Methods — no deben lanzar; verificamos que los atributos existen
        assert dialog.prep_search_entry is not None
        dialog.filter_available_list()
        dialog.assign_preproceso()
        dialog.unassign_preproceso()
        dialog.update_available_list()
        dialog.update_assigned_list()

class TestCreateFabricacionPresenter:
    def test_init(self, dialog_data, mock_view):
        preps, prods = dialog_data
        presenter = CreateFabricacionPresenter(preps, prods)
        assert presenter.all_preprocesos is not None
        assert len(presenter.all_preprocesos) == 2

    # Add more presenter tests if needed, but usually dialog tests cover the logic
    # since the logic is in the dialog methods (patrón histórico)
