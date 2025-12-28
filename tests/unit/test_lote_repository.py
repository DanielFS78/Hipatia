import pytest
from database.repositories.lote_repository import LoteRepository
from database.models import Lote, Producto, Fabricacion
from core.dtos import LoteDTO, ProductDTO, FabricacionDTO

@pytest.fixture
def lote_repo(session):
    return LoteRepository(lambda: session)

@pytest.fixture
def seed_lote_data(session):
    # Create products
    p1 = Producto(codigo="P-LOTE-1", descripcion="Prod 1", departamento="A", tipo_trabajador=1, tiene_subfabricaciones=False)
    p2 = Producto(codigo="P-LOTE-2", descripcion="Prod 2", departamento="B", tipo_trabajador=1, tiene_subfabricaciones=False)
    session.add_all([p1, p2])
    
    # Create fabrications
    f1 = Fabricacion(codigo="F-LOTE-1", descripcion="Fab 1")
    f2 = Fabricacion(codigo="F-LOTE-2", descripcion="Fab 2")
    session.add_all([f1, f2])
    
    session.commit()
    return [p1.codigo, p2.codigo], [f1.id, f2.id]

def test_create_lote(lote_repo, seed_lote_data, session):
    prod_codes, fab_ids = seed_lote_data
    
    data = {
        "codigo": "LOTE-TEST-1",
        "descripcion": "Test Lote Description",
        "product_codes": prod_codes,
        "fabricacion_ids": fab_ids
    }
    
    lote_id = lote_repo.create_lote(data)
    assert lote_id is not None
    
    # Verify DB
    lote = session.query(Lote).filter_by(id=lote_id).first()
    assert lote is not None
    assert lote.codigo == "LOTE-TEST-1"
    assert len(lote.productos) == 2
    assert len(lote.fabricaciones) == 2

def test_create_lote_minimal(lote_repo):
    data = {
        "codigo": "LOTE-MIN",
        "descripcion": "Minimal Lote"
    }
    lote_id = lote_repo.create_lote(data)
    assert lote_id is not None

def test_get_lote_details(lote_repo, seed_lote_data):
    prod_codes, fab_ids = seed_lote_data
    data = {
        "codigo": "LOTE-DET",
        "descripcion": "Details",
        "product_codes": [prod_codes[0]],
        "fabricacion_ids": [fab_ids[0]]
    }
    lote_id = lote_repo.create_lote(data)
    
    # Test
    dto = lote_repo.get_lote_details(lote_id)
    assert isinstance(dto, LoteDTO)
    assert dto.id == lote_id
    assert dto.codigo == "LOTE-DET"
    assert len(dto.productos) == 1
    assert dto.productos[0].codigo == prod_codes[0]
    assert len(dto.fabricaciones) == 1
    assert dto.fabricaciones[0].id == fab_ids[0]

def test_get_lote_details_not_found(lote_repo):
    result = lote_repo.get_lote_details(99999)
    assert result is None

def test_search_lotes(lote_repo):
    lote_repo.create_lote({"codigo": "SEARCH-1", "descripcion": "Alpha"})
    lote_repo.create_lote({"codigo": "SEARCH-2", "descripcion": "Beta"})
    
    # Search by code
    results = lote_repo.search_lotes("SEARCH-1")
    assert len(results) == 1
    assert results[0].codigo == "SEARCH-1"
    assert isinstance(results[0], LoteDTO)
    
    # Search by desc
    results = lote_repo.search_lotes("Beta")
    assert len(results) == 1
    assert results[0].descripcion == "Beta"
    
    # No match
    results = lote_repo.search_lotes("ZULU")
    assert len(results) == 0

def test_update_lote(lote_repo, seed_lote_data, session):
    prod_codes, fab_ids = seed_lote_data
    # Initial
    lid = lote_repo.create_lote({"codigo": "UPD-1", "descripcion": "Orig"})
    
    # Update
    new_data = {
        "codigo": "UPD-1-NEW",
        "descripcion": "New Desc",
        "product_codes": prod_codes,
        "fabricacion_ids": fab_ids
    }
    
    success = lote_repo.update_lote(lid, new_data)
    assert success is True
    
    # Verify
    lote = session.query(Lote).filter_by(id=lid).first()
    assert lote.codigo == "UPD-1-NEW"
    assert len(lote.productos) == 2
    assert len(lote.fabricaciones) == 2

def test_update_lote_not_found(lote_repo):
    success = lote_repo.update_lote(99999, {})
    assert success is False

def test_delete_lote(lote_repo):
    lid = lote_repo.create_lote({"codigo": "DEL-1", "descripcion": "To Delete"})
    
    success = lote_repo.delete_lote(lid)
    assert success is True
    
    # Verify
    assert lote_repo.get_lote_details(lid) is None

def test_delete_lote_not_found(lote_repo):
    success = lote_repo.delete_lote(99999)
    assert success is False
