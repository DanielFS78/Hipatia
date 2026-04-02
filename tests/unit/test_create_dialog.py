import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt

from ui.dialogs.fabrication.create_dialog import CreateFabricacionDialog

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_dependencies():
    with patch("ui.dialogs.fabrication.create_dialog.QMessageBox") as mock_msg:
        yield {"msg": mock_msg}

@pytest.fixture
def sample_data():
    class MockPreproceso:
        def __init__(self, id, nombre, descripcion):
            self.id = id
            self.nombre = nombre
            self.descripcion = descripcion

    class MockProduct:
        def __init__(self, codigo, descripcion):
            self.codigo = codigo
            self.descripcion = descripcion

    preps = [
        MockPreproceso(1, "Prep A", "Corte"),
        MockPreproceso(2, "Prep B", "Pintura"),
    ]
    prods = [
        MockProduct("P01", "Mesa"),
        MockProduct("P02", "Silla"),
    ]
    return preps, prods

@pytest.mark.unit
class TestCreateFabricacionDialog:
    
    def test_init_and_load(self, qtbot, sample_data):
        preps, prods = sample_data
        dialog = CreateFabricacionDialog(preps, prods)
        qtbot.addWidget(dialog)
        
        # Verify initial available lists
        assert dialog.prep_available_list.count() == 2
        assert dialog.prod_available_list.count() == 2
        
        # Lists should be populated correctly based on presenter logic
        item0 = dialog.prep_available_list.item(0)
        assert item0 is not None
        assert "Prep A - Corte" in item0.text() or \
               "Prep B - Pintura" in item0.text()

    def test_search_filtering(self, qtbot, sample_data):
        preps, prods = sample_data
        dialog = CreateFabricacionDialog(preps, prods)
        qtbot.addWidget(dialog)
        
        # Filter Preps
        dialog.prep_search_entry.setText("corte")
        # Ensure the filter signal is processed
        assert dialog.prep_available_list.count() == 1
        item_corte = dialog.prep_available_list.item(0)
        assert item_corte is not None
        assert "Corte" in item_corte.text()
        
        # Filter Prods
        dialog.prod_search_entry.setText("silla")
        assert dialog.prod_available_list.count() == 1
        item_silla = dialog.prod_available_list.item(0)
        assert item_silla is not None
        assert "Silla" in item_silla.text()

    def test_assign_unassign_preprocesos(self, qtbot, sample_data):
        preps, prods = sample_data
        dialog = CreateFabricacionDialog(preps, prods)
        qtbot.addWidget(dialog)
        
        # Select first item and assign
        item = dialog.prep_available_list.item(0)
        assert item is not None
        item.setSelected(True)
        dialog.prep_add_button.click()
        
        assert dialog.prep_assigned_list.count() == 1
        assert dialog.prep_available_list.count() == 1  # the other one is left
        
        # Select in assigned and unassign
        assigned_item = dialog.prep_assigned_list.item(0)
        assert assigned_item is not None
        assigned_item.setSelected(True)
        dialog.prep_remove_button.click()
        
        assert dialog.prep_assigned_list.count() == 0
        assert dialog.prep_available_list.count() == 2

    def test_assign_unassign_products_and_spinbox(self, qtbot, sample_data):
        preps, prods = sample_data
        dialog = CreateFabricacionDialog(preps, prods)
        qtbot.addWidget(dialog)
        
        # Select first item and assign
        item = dialog.prod_available_list.item(0)
        assert item is not None
        item.setSelected(True)
        dialog.prod_add_button.click()
        
        assert dialog.prod_assigned_table.rowCount() == 1
        assert dialog.prod_available_list.count() == 1
        
        # Change spinbox value
        from PyQt6.QtWidgets import QSpinBox
        spinbox = dialog.prod_assigned_table.cellWidget(0, 2)
        assert isinstance(spinbox, QSpinBox)
        spinbox.setValue(5)
        
        # Verify it updated presenter
        assigned = dialog.presenter.get_assigned_products()
        assert assigned[0][1] == 5
        
        # Unassign
        dialog.prod_assigned_table.selectRow(0)
        dialog.prod_remove_button.click()
        
        assert dialog.prod_assigned_table.rowCount() == 0
        assert dialog.prod_available_list.count() == 2

    def test_validate_and_accept_empty_code(self, qtbot, sample_data, mock_dependencies):
        preps, prods = sample_data
        dialog = CreateFabricacionDialog(preps, prods)
        qtbot.addWidget(dialog)
        
        dialog.validate_and_accept()
        assert mock_dependencies["msg"].warning.call_count >= 1
        mock_dependencies["msg"].warning.assert_called_with(dialog, "Error de Validación", "El código de la fabricación es obligatorio.")

    def test_validate_and_accept_no_items(self, qtbot, sample_data, mock_dependencies):
        preps, prods = sample_data
        dialog = CreateFabricacionDialog(preps, prods)
        qtbot.addWidget(dialog)
        
        dialog.codigo_entry.setText("FAB-01")
        dialog.validate_and_accept()
        assert mock_dependencies["msg"].warning.call_count >= 1
        mock_dependencies["msg"].warning.assert_called_with(dialog, "Error de Validación", "Debe asignar al menos un preproceso O un producto a la fabricación.")

    def test_validate_and_accept_success(self, qtbot, sample_data):
        preps, prods = sample_data
        dialog = CreateFabricacionDialog(preps, prods)
        qtbot.addWidget(dialog)
        
        # Mock accept method
        dialog.accept = MagicMock()  # type: ignore[method-assign]
        
        dialog.codigo_entry.setText("FAB-01")
        
        # Assign prep
        item = dialog.prep_available_list.item(0)
        assert item is not None
        item.setSelected(True)
        dialog.prep_add_button.click()
        
        dialog.validate_and_accept()
        assert dialog.accept.call_count == 1
        dialog.accept.assert_called_once_with()

    def test_get_fabricacion_data(self, qtbot, sample_data):
        preps, prods = sample_data
        dialog = CreateFabricacionDialog(preps, prods)
        qtbot.addWidget(dialog)
        
        dialog.codigo_entry.setText("FAB-ABC")
        dialog.descripcion_entry.setText("Test")
        
        # Assign prep and prod
        item = dialog.prep_available_list.item(0)
        assert item is not None
        item.setSelected(True)
        dialog.prep_add_button.click()
        
        item = dialog.prod_available_list.item(0)
        assert item is not None
        item.setSelected(True)
        dialog.prod_add_button.click()
        
        data = dialog.get_fabricacion_data()
        assert data.codigo == "FAB-ABC"
        assert data.descripcion == "Test"
        assert data.preprocesos_ids is not None
        assert len(data.preprocesos_ids) == 1
        assert data.productos is not None
        assert len(data.productos) == 1

    def test_compat_properties(self, qtbot, sample_data):
        preps, prods = sample_data
        dialog = CreateFabricacionDialog(preps, prods)
        qtbot.addWidget(dialog)
        
        # Test backward-comp properties
        assert dialog.search_entry is dialog.prep_search_entry
        assert dialog.available_list is dialog.prep_available_list
        assert dialog.assigned_list is dialog.prep_assigned_list
        assert dialog.add_button is dialog.prep_add_button
        assert dialog.remove_button is dialog.prep_remove_button
        
        # We can just call them to ensure no Exception
        dialog.filter_available_list()
        
        # Select and assign via API histórica
        item = dialog.available_list.item(0)
        assert item is not None
        item.setSelected(True)
        dialog.assign_preproceso()
        
        assert dialog.assigned_list.count() == 1
        
        item = dialog.assigned_list.item(0)
        assert item is not None
        item.setSelected(True)
        dialog.unassign_preproceso()
        
        assert dialog.assigned_list.count() == 0
        
        # Other methods
        dialog.update_available_list()
        dialog.update_assigned_list()
