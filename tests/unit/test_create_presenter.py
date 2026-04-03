"""Tests para CreateFabricacionPresenter."""
import pytest
from unittest.mock import MagicMock
from ui.dialogs.fabrication.create_presenter import CreateFabricacionPresenter
from core.dtos import FabricacionProductoDTO

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
        MockPreproceso(3, "Prep C", "Ensamblaje")
    ]
    prods = [
        MockProduct("P01", "Mesa"),
        MockProduct("P02", "Silla"),
        MockProduct("T01", "Taburete")
    ]
    return preps, prods

@pytest.fixture
def presenter(sample_data):
    preps, prods = sample_data
    return CreateFabricacionPresenter(preps, prods)

@pytest.mark.unit
class TestCreateFabricacionPresenter:
    
    def test_init_sorting(self, sample_data):
        preps, prods = sample_data
        pres = CreateFabricacionPresenter(preps, prods)
        
        # Preprocesos should be sorted by id descending
        assert pres.all_preprocesos[0].id == 3
        assert pres.all_preprocesos[1].id == 2
        assert pres.all_preprocesos[2].id == 1

    def test_filter_preprocesos(self, presenter):
        # Empty string should return all non-assigned
        assert len(presenter.get_filtered_preprocesos("")) == 3
        
        # Search by name
        assert len(presenter.get_filtered_preprocesos("prep a")) == 1
        
        # Search by description
        assert len(presenter.get_filtered_preprocesos("pintura")) == 1
        
        # Assign one and test filter excludes it
        presenter.assign_preprocesos([presenter.all_preprocesos[0]]) # ID 3
        assert len(presenter.get_filtered_preprocesos("")) == 2

    def test_assign_unassign_preprocesos(self, presenter):
        # Assign
        presenter.assign_preprocesos([presenter.all_preprocesos[0], presenter.all_preprocesos[1]])
        assigned = presenter.get_assigned_preprocesos()
        assert len(assigned) == 2
        
        # Unassign
        presenter.unassign_preprocesos([presenter.all_preprocesos[0]])
        assigned = presenter.get_assigned_preprocesos()
        assert len(assigned) == 1
        assert assigned[0].id == presenter.all_preprocesos[1].id

    def test_filter_products(self, presenter):
        # Empty string should return all non-assigned
        assert len(presenter.get_filtered_products("")) == 3
        
        # Search by code
        assert len(presenter.get_filtered_products("p0")) == 2
        
        # Search by description
        assert len(presenter.get_filtered_products("silla")) == 1
        
        # Assign one and test filter excludes it
        presenter.assign_products([presenter.all_products[0]]) # P01
        assert len(presenter.get_filtered_products("")) == 2

    def test_assign_unassign_products(self, presenter):
        # Assign
        presenter.assign_products([presenter.all_products[0], presenter.all_products[1]], default_qty=5)
        assigned = presenter.get_assigned_products()
        assert len(assigned) == 2
        assert assigned[0][0].codigo == "P01"
        assert assigned[0][1] == 5
        
        # Update qty
        presenter.update_product_qty("P01", 10)
        assigned = presenter.get_assigned_products()
        assert [q for p, q in assigned if p.codigo == "P01"][0] == 10
        
        # Unassign
        presenter.unassign_products_by_code(["P01"])
        assigned = presenter.get_assigned_products()
        assert len(assigned) == 1
        assert assigned[0][0].codigo == "P02"

    def test_validation(self, presenter):
        # Empty code
        valid, msg = presenter.validate("")
        assert not valid
        assert "obligatorio" in msg
        
        # No assignments
        valid, msg = presenter.validate("FAB-01")
        assert not valid
        assert "asignar al menos" in msg
        
        # Valid assign prep
        presenter.assign_preprocesos([presenter.all_preprocesos[0]])
        valid, msg = presenter.validate("FAB-01")
        assert valid
        
        # Valid assign prod
        presenter.unassign_preprocesos([presenter.all_preprocesos[0]])
        presenter.assign_products([presenter.all_products[0]])
        valid, msg = presenter.validate("FAB-01")
        assert valid

    def test_get_fabricacion_data(self, presenter):
        presenter.assign_preprocesos([presenter.all_preprocesos[1]]) # ID 2
        presenter.assign_products([presenter.all_products[0]], default_qty=3) # P01
        
        data = presenter.get_fabricacion_data("  FAB-01  ", "  Test Desc  ")
        
        assert data.codigo == "FAB-01"
        assert data.descripcion == "Test Desc"
        assert data.preprocesos_ids == [2]
        assert len(data.productos) == 1
        assert data.productos[0].producto_codigo == "P01"
        assert data.productos[0].cantidad == 3
