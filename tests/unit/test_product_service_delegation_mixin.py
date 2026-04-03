# -*- coding: utf-8 -*-
"""Cobertura de delegaciones de ProductService."""

from unittest.mock import MagicMock, create_autospec
import pytest

from core.services.product_service import ProductService
from database.database_manager import DatabaseManager
from database.repositories.product_repository import ProductRepository
from database.repositories.iteration_repository import IterationRepository
from database.repositories.material_repository import MaterialRepository

pytestmark = pytest.mark.unit

@pytest.fixture
def db_manager():
    mgr = create_autospec(DatabaseManager, instance=True)
    mgr.product_repo = create_autospec(ProductRepository, instance=True)
    mgr.iteration_repo = create_autospec(IterationRepository, instance=True)
    mgr.material_repo = create_autospec(MaterialRepository, instance=True)
    return mgr

@pytest.fixture
def service(db_manager):
    return ProductService(db_manager)

def test_iteration_delegations(service, db_manager):
    repo = db_manager.iteration_repo
    repo.get_product_iterations.return_value = ["it"]
    repo.add_product_iteration.return_value = 10
    repo.update_product_iteration.return_value = True
    repo.delete_product_iteration.return_value = True
    repo.get_all_iterations_with_dates.return_value = ["d"]
    repo.add_image.return_value = True
    repo.delete_image.return_value = True
    repo.update_iteration_file_path.return_value = True

    # Verificaciones
    assert service.get_product_iterations("P") == ["it"]
    repo.get_product_iterations.assert_called_once_with("P")

    assert service.add_product_iteration("P", "R", "D", "F", []) == 10
    repo.add_product_iteration.assert_called_once_with("P", "R", "D", "F", [], None, None)

    assert service.update_product_iteration_details(1, "R", "D", "F") is True
    repo.update_product_iteration.assert_called_once_with(1, "R", "D", "F")

    assert service.update_product_iteration(2, "R2", "D2", "F2") is True
    repo.update_product_iteration.assert_called_with(2, "R2", "D2", "F2")

    assert service.delete_product_iteration(1) is True
    repo.delete_product_iteration.assert_called_once_with(1)

    assert service.get_all_iterations_with_dates() == ["d"]
    repo.get_all_iterations_with_dates.assert_called_once_with()

    assert service.add_iteration_image(1, "/tmp/a.png") is True
    repo.add_image.assert_called_once_with(1, "/tmp/a.png")

    assert service.delete_iteration_image(1) is True
    repo.delete_image.assert_called_once_with(1)

    assert service.update_iteration_file_path(1, "ruta_imagen", "/tmp/a.png") is True
    repo.update_iteration_file_path.assert_called_once_with(1, "ruta_imagen", "/tmp/a.png")

def test_material_delegations(service, db_manager):
    p_repo = db_manager.product_repo
    i_repo = db_manager.iteration_repo
    m_repo = db_manager.material_repo
    
    p_repo.get_materials_for_product.return_value = ["m"]
    m_repo.add_material.return_value = 5
    m_repo.link_material_to_iteration.return_value = True
    m_repo.get_all_materials.return_value = ["allm"]
    m_repo.update_material.return_value = True
    m_repo.delete_material_link_from_iteration.return_value = True
    m_repo.delete_material.return_value = True
    m_repo.link_material_to_product.return_value = True
    m_repo.unlink_material_from_product.return_value = True
    m_repo.add_material.return_value = 3

    assert service.get_materials_for_product("P") == ["m"]
    p_repo.get_materials_for_product.assert_called_once_with("P")

    # add_material_to_iteration ahora hace dos llamadas
    assert service.add_material_to_iteration(1, "M", "Desc") == 3
    m_repo.add_material.assert_called_once_with("M", "Desc")
    m_repo.link_material_to_iteration.assert_called_once_with(1, 3)

    assert service.get_all_materials_for_selection() == ["allm"]
    m_repo.get_all_materials.assert_called_once_with()

    assert service.update_material(1, "M2", "Desc2") is True
    m_repo.update_material.assert_called_once_with(1, "M2", "Desc2")

    assert service.delete_material_link(1, 2) is True
    m_repo.delete_material_link_from_iteration.assert_called_once_with(1, 2)

    assert service.delete_material(2) is True
    m_repo.delete_material.assert_called_once_with(2)

    assert service.link_material_to_product("P", 2) is True
    m_repo.link_material_to_product.assert_called_once_with("P", 2)

    assert service.unlink_material_from_product("P", 2) is True
    m_repo.unlink_material_from_product.assert_called_once_with("P", 2)

    # Reset mock para la última llamada de add_material
    m_repo.add_material.reset_mock()
    m_repo.add_material.return_value = 7
    assert service.add_material("M3", "Desc3") == 7
    m_repo.add_material.assert_called_once_with("M3", "Desc3")
