# -*- coding: utf-8 -*-
"""Cobertura de rutas principales/validación de ProductService."""

from unittest.mock import MagicMock

import pytest

from core.services.product_service import ProductService

pytestmark = pytest.mark.unit


@pytest.fixture
def db_manager():
    mgr = MagicMock(spec=["product_repo", "iteration_repo", "material_repo"])
    mgr.product_repo = MagicMock(
        spec=["search_products", "get_latest_products", "get_product_details", "add_product", "update_product", "delete_product"]
    )
    mgr.iteration_repo = MagicMock(
        spec=[
            "get_product_iterations",
            "add_product_iteration",
            "update_product_iteration_details",
            "delete_product_iteration",
            "get_all_iterations_with_dates",
            "add_image",
            "delete_image",
            "update_iteration_file_path",
            "get_materials_for_product",
            "add_material_to_iteration",
            "delete_material_link",
        ]
    )
    mgr.material_repo = MagicMock(
        spec=[
            "get_all_materials",
            "update_material",
            "delete_material",
            "link_material_to_product",
            "unlink_material_from_product",
            "add_material",
        ]
    )
    return mgr


@pytest.fixture
def service(db_manager):
    return ProductService(db_manager)


def test_basic_delegation_paths(service, db_manager):
    db_manager.product_repo.search_products.return_value = ["a"]
    db_manager.product_repo.get_latest_products.return_value = ["b"]
    db_manager.product_repo.get_product_details.return_value = ("p", [], [])
    
    assert service.search_products("x") == ["a"]
    db_manager.product_repo.search_products.assert_called_once_with("x")
    
    assert service.get_latest_products(3) == ["b"]
    db_manager.product_repo.get_latest_products.assert_called_once_with(3)
    
    assert service.get_product_details("P1") == ("p", [], [])
    db_manager.product_repo.get_product_details.assert_called_once_with("P1")


def test_add_product_missing_fields(service):
    assert service.add_product({"codigo": "", "descripcion": ""}) == "MISSING_FIELDS"


@pytest.mark.parametrize("tiempo", [None, "", "0", "-3", "abc"])
def test_add_product_invalid_time(service, tiempo):
    data = {"codigo": "P1", "descripcion": "Desc", "tiene_subfabricaciones": False, "tiempo_optimo": tiempo}
    assert service.add_product(data) == "INVALID_TIME"


def test_add_product_success_emits_signal(service, db_manager):
    db_manager.product_repo.add_product.return_value = True
    data = {"codigo": "P2", "descripcion": "Desc", "tiene_subfabricaciones": False, "tiempo_optimo": "3,5"}
    emitted: list[str] = []
    service.product_added_signal.connect(lambda code: emitted.append(code))
    assert service.add_product(data) == "SUCCESS"
    db_manager.product_repo.add_product.assert_called_once_with(data, None)
    assert emitted == ["P2"]


def test_add_product_db_error(service, db_manager):
    db_manager.product_repo.add_product.return_value = False
    data = {"codigo": "P3", "descripcion": "Desc", "tiene_subfabricaciones": True}
    assert service.add_product(data) == "DB_ERROR"
    db_manager.product_repo.add_product.assert_called_once_with(data, None)


def test_update_delete_emit_signals(service, db_manager):
    db_manager.product_repo.update_product.return_value = True
    db_manager.product_repo.delete_product.return_value = True
    updated_hits: list[int] = []
    deleted_hits: list[int] = []
    service.product_updated_signal.connect(lambda: updated_hits.append(1))
    service.product_deleted_signal.connect(lambda: deleted_hits.append(1))
    assert service.update_product("P1", {"codigo": "P1"}) is True
    db_manager.product_repo.update_product.assert_called_once_with("P1", {"codigo": "P1"}, None)
    
    assert service.delete_product("P1") is True
    db_manager.product_repo.delete_product.assert_called_once_with("P1")
    
    assert len(updated_hits) == 1
    assert len(deleted_hits) == 1


def test_update_delete_no_emit_when_false(service, db_manager):
    db_manager.product_repo.update_product.return_value = False
    db_manager.product_repo.delete_product.return_value = False
    updated_hits: list[int] = []
    deleted_hits: list[int] = []
    service.product_updated_signal.connect(lambda: updated_hits.append(1))
    service.product_deleted_signal.connect(lambda: deleted_hits.append(1))
    assert service.update_product("P1", {"codigo": "P1"}) is False
    db_manager.product_repo.update_product.assert_called_once_with("P1", {"codigo": "P1"}, None)
    
    assert service.delete_product("P1") is False
    db_manager.product_repo.delete_product.assert_called_once_with("P1")
    
    assert updated_hits == []
    assert deleted_hits == []

