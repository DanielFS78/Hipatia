# -*- coding: utf-8 -*-
"""Tests unitarios para ProductService.

Cubre add_material, get_all_materials_for_selection, link/unlink material.
DB manager mockeado con spec (material_repo).
"""
import pytest
from unittest.mock import MagicMock, patch
from core.services.product_service import ProductService
from core.dtos import ProductDTO, MaterialDTO

pytestmark = pytest.mark.unit


@pytest.fixture
def db_manager():
    repo = MagicMock(spec=['add_material', 'get_all_materials', 'link_material_to_product', 'unlink_material_from_product'])
    mgr = MagicMock(spec=['material_repo'])
    mgr.material_repo = repo
    return mgr

@pytest.fixture
def product_service(db_manager):
    return ProductService(db_manager)

def test_add_material(product_service, db_manager):
    db_manager.material_repo.add_material.return_value = 1
    
    result = product_service.add_material("M001", "Desc")
    
    assert result == 1
    assert db_manager.material_repo.add_material.call_count == 1
    db_manager.material_repo.add_material.assert_called_once_with("M001", "Desc")

def test_get_all_materials_for_selection(product_service, db_manager):
    materials = [MaterialDTO(id=1, codigo_componente="M1", descripcion_componente="D1")]
    db_manager.material_repo.get_all_materials.return_value = materials
    
    result = product_service.get_all_materials_for_selection()
    
    assert result == materials
    assert db_manager.material_repo.get_all_materials.call_count == 1
    db_manager.material_repo.get_all_materials.assert_called_once_with()

def test_link_material_to_product(product_service, db_manager):
    db_manager.material_repo.link_material_to_product.return_value = True
    
    result = product_service.link_material_to_product("P1", 1)
    
    assert result is True
    assert db_manager.material_repo.link_material_to_product.call_count == 1
    db_manager.material_repo.link_material_to_product.assert_called_once_with("P1", 1)

def test_unlink_material_from_product(product_service, db_manager):
    db_manager.material_repo.unlink_material_from_product.return_value = True
    
    result = product_service.unlink_material_from_product("P1", 1)
    
    assert result is True
    assert db_manager.material_repo.unlink_material_from_product.call_count == 1
    db_manager.material_repo.unlink_material_from_product.assert_called_once_with("P1", 1)
