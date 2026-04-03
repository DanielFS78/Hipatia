"""Tests de integración para `MaterialRepository` (SQLite en memoria).

Regla de calidad Hipatia: los repositorios se validan contra una BD real en memoria,
evitando mocks de `Session` (falsos positivos / contratos irreales).
"""

import pytest

from core.dtos import MaterialDTO
from database.models import Producto

pytestmark = pytest.mark.integration


def test_get_all_materials_returns_dtos(repos):
    repo = repos["material"]

    assert repo.get_all_materials() == []

    material_id = repo.add_material("MAT001", "Test Material")
    assert isinstance(material_id, int)

    materials = repo.get_all_materials()
    assert len(materials) == 1
    assert isinstance(materials[0], MaterialDTO)
    assert materials[0].id == material_id
    assert materials[0].codigo_componente == "MAT001"
    assert materials[0].descripcion_componente == "Test Material"


def test_add_material_updates_description_if_exists(repos):
    repo = repos["material"]

    mid1 = repo.add_material("EXISTING_CODE", "Old Description")
    assert isinstance(mid1, int)

    mid2 = repo.add_material("EXISTING_CODE", "New Description")
    assert mid2 == mid1

    materials = repo.get_all_materials()
    mat = next(m for m in materials if m.id == mid1)
    assert mat.descripcion_componente == "New Description"


def test_update_material_not_found(repos):
    repo = repos["material"]
    assert repo.update_material(99999, "CODE", "Desc") is False


def test_update_material_duplicate_code_is_rejected(repos):
    repo = repos["material"]

    mid1 = repo.add_material("CODE-1", "Desc1")
    mid2 = repo.add_material("CODE-2", "Desc2")
    assert isinstance(mid1, int)
    assert isinstance(mid2, int)

    # intentar poner CODE-2 al material 1 => debe fallar por duplicado
    assert repo.update_material(mid1, "CODE-2", "New Desc") is False


def test_update_material_success(repos):
    repo = repos["material"]
    mid = repo.add_material("CODE-OK", "Desc1")
    assert isinstance(mid, int)
    assert repo.update_material(mid, "CODE-OK-2", "Desc2") is True

    mats = repo.get_all_materials()
    updated = next(m for m in mats if m.id == mid)
    assert updated.codigo_componente == "CODE-OK-2"
    assert updated.descripcion_componente == "Desc2"


def test_link_and_unlink_material_to_product_is_idempotent(repos, session):
    repo = repos["material"]

    prod = Producto(
        codigo="PROD-01",
        descripcion="Prod",
        departamento="D",
        tipo_trabajador=1,
        tiene_subfabricaciones=False,
        tiempo_optimo=10.0,
    )
    session.add(prod)
    session.commit()

    material_id = repo.add_material("MAT-LINK", "Desc")
    assert isinstance(material_id, int)

    assert repo.link_material_to_product("PROD-01", material_id) is True
    assert repo.link_material_to_product("PROD-01", material_id) is True

    assert repo.unlink_material_from_product("PROD-01", material_id) is True
    assert repo.unlink_material_from_product("PROD-01", material_id) is True


def test_link_material_to_product_returns_false_when_product_missing(repos):
    repo = repos["material"]
    material_id = repo.add_material("MAT-404", "Desc")
    assert isinstance(material_id, int)

    assert repo.link_material_to_product("PROD-NOT-FOUND", material_id) is False


def test_add_material_existing_without_changes_returns_same_id(repos):
    repo = repos["material"]
    mid1 = repo.add_material("MAT-SAME", "Desc")
    mid2 = repo.add_material("MAT-SAME", "Desc")
    assert isinstance(mid1, int)
    assert mid2 == mid1


def test_unlink_material_from_product_edge_cases(repos, session):
    repo = repos["material"]
    material_id = repo.add_material("MAT-U", "Desc")
    assert isinstance(material_id, int)

    # Producto no existe
    assert repo.unlink_material_from_product("PROD-NOT-FOUND", material_id) is False

    # Producto existe y material inexistente => éxito idempotente
    prod = Producto(
        codigo="PROD-U",
        descripcion="Prod",
        departamento="D",
        tipo_trabajador=1,
        tiene_subfabricaciones=False,
        tiempo_optimo=10.0,
    )
    session.add(prod)
    session.commit()
    assert repo.unlink_material_from_product("PROD-U", 999999) is True


def test_link_and_unlink_material_to_iteration_is_idempotent(repos, session):
    material_repo = repos["material"]
    iteration_repo = repos["iteration"]

    prod = Producto(
        codigo="PROD-IT",
        descripcion="Prod",
        departamento="D",
        tipo_trabajador=1,
        tiene_subfabricaciones=False,
        tiempo_optimo=10.0,
    )
    session.add(prod)
    session.commit()

    iteration_id = iteration_repo.add_product_iteration(
        "PROD-IT", "Resp", "Desc", "Fallo", materiales_list=[]
    )
    assert isinstance(iteration_id, int)
    material_id = material_repo.add_material("MAT-IT", "Desc")
    assert isinstance(material_id, int)

    assert material_repo.link_material_to_iteration(iteration_id, material_id) is True
    assert material_repo.link_material_to_iteration(iteration_id, material_id) is True
    assert material_repo.delete_material_link_from_iteration(iteration_id, material_id) is True
    assert material_repo.delete_material_link_from_iteration(iteration_id, material_id) is True


def test_link_and_unlink_material_to_iteration_missing_entities(repos, session):
    material_repo = repos["material"]
    iteration_repo = repos["iteration"]
    material_id = material_repo.add_material("MAT-MISS", "Desc")
    assert isinstance(material_id, int)

    # Iteración inexistente
    assert material_repo.link_material_to_iteration(999999, material_id) is False
    assert material_repo.delete_material_link_from_iteration(999999, material_id) is False

    # Iteración existe, material inexistente => unlink true por idempotencia
    prod = Producto(
        codigo="PROD-MISS",
        descripcion="Prod",
        departamento="D",
        tipo_trabajador=1,
        tiene_subfabricaciones=False,
        tiempo_optimo=10.0,
    )
    session.add(prod)
    session.commit()
    iteration_id = iteration_repo.add_product_iteration(
        "PROD-MISS", "Resp", "Desc", "Fallo", materiales_list=[]
    )
    assert isinstance(iteration_id, int)
    assert material_repo.link_material_to_iteration(iteration_id, 999999) is False
    assert material_repo.delete_material_link_from_iteration(iteration_id, 999999) is True


def test_delete_material_and_not_found(repos):
    repo = repos["material"]
    mid = repo.add_material("MAT-DEL", "Desc")
    assert isinstance(mid, int)
    assert repo.delete_material(mid) is True
    assert repo.delete_material(999999) is False


def test_get_default_error_value_is_none(repos):
    repo = repos["material"]
    assert repo._get_default_error_value() is None


def test_get_problematic_components_stats_returns_frequency(repos, session):
    material_repo = repos["material"]
    iteration_repo = repos["iteration"]

    prod = Producto(
        codigo="PROD-ST",
        descripcion="Prod",
        departamento="D",
        tipo_trabajador=1,
        tiene_subfabricaciones=False,
        tiempo_optimo=10.0,
    )
    session.add(prod)
    session.commit()

    m1 = material_repo.add_material("MAT-S1", "Desc1")
    m2 = material_repo.add_material("MAT-S2", "Desc2")
    assert isinstance(m1, int) and isinstance(m2, int)

    it1 = iteration_repo.add_product_iteration("PROD-ST", "R", "D1", "F", materiales_list=[])
    it2 = iteration_repo.add_product_iteration("PROD-ST", "R", "D2", "F", materiales_list=[])
    assert isinstance(it1, int) and isinstance(it2, int)

    assert material_repo.link_material_to_iteration(it1, m1) is True
    assert material_repo.link_material_to_iteration(it2, m1) is True
    assert material_repo.link_material_to_iteration(it2, m2) is True

    stats = material_repo.get_problematic_components_stats(limit=10)
    assert len(stats) >= 2
    # MAT-S1 aparece más veces que MAT-S2
    s1 = next(s for s in stats if s.codigo_componente == "MAT-S1")
    s2 = next(s for s in stats if s.codigo_componente == "MAT-S2")
    assert s1.frecuencia >= s2.frecuencia

