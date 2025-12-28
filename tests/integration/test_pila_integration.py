import pytest
from core.dtos import PilaDTO

@pytest.mark.integration
def test_pila_product_integration(repos):
    """
    Verify integration between Pila and Product repositories.
    Scenario:
    1. Create a Product.
    2. Create a Pila linked to that Product.
    3. Verify retrieval by product code works correctly.
    4. Verify cascade delete (if configured) or at least data consistency.
    """
    pila_repo = repos["pila"]
    prod_repo = repos["product"]
    
    # 1. Create Product
    prod_code = "INT-PROD-001"
    prod_repo.add_product({
        "codigo": prod_code,
        "descripcion": "Integration Product",
        "departamento": "Montaje",
        "tipo_trabajador": 1,
        "tiene_subfabricaciones": False,
        "tiempo_optimo": 100
    })
    
    # 2. Create Pila linked to Product
    pila_id = pila_repo.save_pila(
        nombre="Integration Pila",
        descripcion="Pila for Product",
        pila_de_calculo={},
        production_flow=[],
        simulation_results=[],
        producto_origen_codigo=prod_code
    )
    
    # 3. Verify retrieval
    pilas = pila_repo.find_pilas_by_producto_codigo(prod_code)
    assert len(pilas) == 1
    assert pilas[0].id == pila_id
    assert pilas[0].producto_origen_codigo == prod_code
    
    # 4. Verify DTO integrity
    pila_dto = pilas[0]
    assert isinstance(pila_dto, PilaDTO)
    assert pila_dto.nombre == "Integration Pila"

@pytest.mark.integration
def test_pila_bitacora_persistence(repos, session):
    """
    Verify that Bitacora entries persist correctly in the database context.
    """
    pila_repo = repos["pila"]
    
    # Create Pila
    pila_id = pila_repo.save_pila("Bitacora Persist", "Desc", {}, [], [])
    
    # Add entry
    from datetime import date
    today = date.today()
    pila_repo.add_diario_entry(pila_id, today, 1, "Plan", "Real", "Note")
    
    # Commit session (simulating app behavior)
    session.commit()
    
    # Retrieve in a "new" lookup (same session for text, but verifying query works)
    bid, entries = pila_repo.get_diario_bitacora(pila_id)
    assert len(entries) == 1
    assert entries[0][0] == today
