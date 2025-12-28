import pytest
from datetime import date, datetime, timedelta
from core.dtos import PilaDTO
import json
from unittest.mock import MagicMock, patch

# Markers for this test file
pytestmark = [pytest.mark.unit, pytest.mark.database]

def test_save_and_get_all_pilas(repos, session):
    """Verify saving a Pila and retrieving it as DTO."""
    from database.models import Producto
    
    # Create product to satisfy FK constraint
    p = Producto(codigo="P-ORIGIN", descripcion="Origin", departamento="Test", tipo_trabajador=1, tiene_subfabricaciones=False)
    session.add(p)
    session.commit()
    
    pila_repo = repos["pila"]
    
    # Save a pila
    pila_id = pila_repo.save_pila(
        nombre="Pila 1",
        descripcion="Test Description",
        pila_de_calculo={"productos": {"P1": {"cantidad": 10}}},
        production_flow=[{"task": {"name": "Task 1"}}],
        simulation_results=[],
        producto_origen_codigo="P-ORIGIN"
    )
    assert isinstance(pila_id, int)
    
    # Get all pilas
    pilas = pila_repo.get_all_pilas()
    assert len(pilas) == 1
    assert isinstance(pilas[0], PilaDTO)
    assert pilas[0].id == pila_id
    assert pilas[0].nombre == "Pila 1"
    assert pilas[0].descripcion == "Test Description"
    assert pilas[0].producto_origen_codigo == "P-ORIGIN"

def test_search_pilas(repos, session):
    """Verify searching pilas returns DTOs."""
    from database.models import Producto
    
    # Create products to satisfy FK constraints
    for code in ["P1", "P2"]:
        session.add(Producto(codigo=code, descripcion=f"Product {code}", departamento="Test", tipo_trabajador=1, tiene_subfabricaciones=False))
    session.commit()
    
    pila_repo = repos["pila"]
    pila_repo.save_pila("Alpha Pila", "First one", {}, [], [], "P1")
    pila_repo.save_pila("Beta Pila", "Second one", {}, [], [], "P2")
    
    results = pila_repo.search_pilas("Alpha")
    assert len(results) == 1
    assert isinstance(results[0], PilaDTO)
    assert results[0].nombre == "Alpha Pila"
    
    results = pila_repo.search_pilas("one")
    assert len(results) == 2

def test_find_pilas_by_producto_codigo(repos, session):
    """Verify finding pilas by product code returns DTOs."""
    from database.models import Producto
    
    # Create products to satisfy FK constraints
    for code in ["PROD-X", "PROD-Y"]:
        session.add(Producto(codigo=code, descripcion=f"Product {code}", departamento="Test", tipo_trabajador=1, tiene_subfabricaciones=False))
    session.commit()
    
    pila_repo = repos["pila"]
    pila_repo.save_pila("Pila A", "Desc", {}, [], [], "PROD-X")
    pila_repo.save_pila("Pila B", "Desc", {}, [], [], "PROD-Y")
    
    results = pila_repo.find_pilas_by_producto_codigo("PROD-X")
    assert len(results) == 1
    assert isinstance(results[0], PilaDTO)
    assert results[0].nombre == "Pila A"
    assert results[0].producto_origen_codigo == "PROD-X"

def test_get_all_pilas_with_dates(repos, session):
    """Verify retrieving pilas with dates returns DTOs with date fields."""
    from database.models import Producto
    
    # Create product to satisfy FK constraint
    session.add(Producto(codigo="P-DATES", descripcion="Dates Product", departamento="Test", tipo_trabajador=1, tiene_subfabricaciones=False))
    session.commit()
    
    pila_repo = repos["pila"]
    
    start = datetime(2025, 1, 1, 8, 0)
    end = datetime(2025, 1, 1, 12, 0)
    
    sim_results = [
        {"Tarea": "T1", "Inicio": start.isoformat(), "Fin": end.isoformat()}
    ]
    
    pila_repo.save_pila(
        "Pila with Dates", 
        "Has simulation", 
        {}, 
        [], 
        sim_results, 
        "P-DATES"
    )
    
    results = pila_repo.get_all_pilas_with_dates()
    assert len(results) >= 1
    pila_dto = next(p for p in results if p.nombre == "Pila with Dates")
    
    assert isinstance(pila_dto, PilaDTO)
    assert pila_dto.start_date == start.date()
    assert pila_dto.end_date == end.date()

def test_load_pila_robustness(repos):
    """Verify loading a pila works (integration)."""
    pila_repo = repos["pila"]
    pila_id = pila_repo.save_pila("Load Test", "Desc", {}, [{"unique_id": "u1"}], [], None)
    
    meta, calc, flow, res = pila_repo.load_pila(pila_id)
    assert meta["nombre"] == "Load Test"
    assert len(flow) == 1
    assert "unique_id" not in flow[0] # Should be cleaned

def test_delete_pila(repos):
    """Verify deleting a pila."""
    pila_repo = repos["pila"]
    pila_id = pila_repo.save_pila("Delete Me", "Desc", {}, [], [], None)
    
    success = pila_repo.delete_pila(pila_id)
    assert success is True
    
    assert pila_repo.load_pila(pila_id) == (None, None, None, None)

# --- NEW TESTS FOR 100% COVERAGE ---

def test_save_pila_unique_constraint(repos):
    """Verify saving a pila with duplicate name raises specific error."""
    pila_repo = repos["pila"]
    pila_repo.save_pila("Duplicate", "Desc", {}, [], [])
    
    # Try to save again with same name
    result = pila_repo.save_pila("Duplicate", "Desc 2", {}, [], [])
    assert result == "UNIQUE_CONSTRAINT"

def test_load_pila_not_found(repos):
    """Verify loading a non-existent pila returns Nones."""
    pila_repo = repos["pila"]
    meta, calc, flow, res = pila_repo.load_pila(99999)
    assert meta is None
    assert calc is None
    assert flow is None
    assert res is None

def test_bitacora_lifecycle(repos):
    """Verify creating, retrieving, and adding entries to a bitacora."""
    pila_repo = repos["pila"]
    pila_id = pila_repo.save_pila("Bitacora Pila", "Desc", {}, [], [])
    
    # 1. Create bitacora
    bitacora_id = pila_repo.create_diario_bitacora(pila_id)
    assert bitacora_id is not None
    
    # 2. Add entry (auto-creates bitacora if needed, but we already created it)
    fecha = date(2025, 1, 15)
    success = pila_repo.add_diario_entry(
        pila_id=pila_id,
        fecha=fecha,
        dia_numero=1,
        plan_previsto="Plan A",
        trabajo_realizado="Hecho A",
        notas="Nota A"
    )
    assert success is True
    
    # 3. Get bitacora
    bid, entradas = pila_repo.get_diario_bitacora(pila_id)
    assert bid == bitacora_id
    assert len(entradas) == 1
    
    # Verify entry content (fecha, dia_numero, plan, real, notas)
    entrada = entradas[0]
    assert entrada[0] == fecha
    assert entrada[1] == 1
    assert entrada[2] == "Plan A"
    assert entrada[3] == "Hecho A"
    assert entrada[4] == "Nota A"
    
    # 4. Update entry (same date)
    pila_repo.add_diario_entry(
        pila_id=pila_id,
        fecha=fecha, 
        dia_numero=1, 
        plan_previsto="Plan B", 
        trabajo_realizado="Hecho B", 
        notas="Nota B"
    )
    
    _, entradas_updated = pila_repo.get_diario_bitacora(pila_id)
    assert len(entradas_updated) == 1
    assert entradas_updated[0][2] == "Plan B"

def test_load_pila_json_errors(repos, session):
    """Verify resilience against corrupted JSON in database."""
    from database.models import Pila, PasoPila
    
    pila_repo = repos["pila"]
    
    # Manually insert corrupted data
    pila = Pila(
        nombre="Corrupt Pila",
        descripcion="Desc",
        pila_de_calculo_json="{bad_json",
        resultados_simulacion="{bad_json",
        fecha_creacion=datetime.now()
    )
    session.add(pila)
    session.commit()
    
    # Add corrupted step
    paso = PasoPila(
        pila_id=pila.id,
        orden=0,
        datos_paso="{bad_json"
    )
    session.add(paso)
    session.commit()
    
    # Load via repo
    meta, calc, flow, res = pila_repo.load_pila(pila.id)
    
    # Should handle errors gracefully
    assert meta["nombre"] == "Corrupt Pila"
    assert calc == {} # Default empty dict
    assert res == []  # Default empty list
    assert flow == [] # Corrupted step skipped

def test_convert_indices_to_ids_logic(repos):
    """Verify internal logic for converting indices to UUIDs (cycles)."""
    pila_repo = repos["pila"]
    
    # Mock data with indices
    flow = [
        {"unique_id": None, "previous_task_index": None, "next_cyclic_task_index": 1}, # 0 -> 1 (cycle start)
        {"unique_id": None, "previous_task_index": 0, "next_cyclic_task_index": None}, # 1 -> 0 (implicit by flow, but here testing direct links)
    ]
    
    # We can access private method since we are in python
    pila_repo._convert_indices_to_ids(flow)
    
    assert "unique_id" in flow[0]
    assert "next_cyclic_task_id" in flow[0]
    assert "next_cyclic_task_index" not in flow[0]
    assert flow[0]["next_cyclic_task_id"] == flow[1]["unique_id"]

def test_convert_ids_to_indices_logic(repos):
    """Verify reconstruction of indices from UUIDs."""
    pila_repo = repos["pila"]
    
    uid1 = "uuid-1"
    uid2 = "uuid-2"
    
    flow = [
        {"unique_id": uid1, "next_cyclic_task_id": uid2},
        {"unique_id": uid2, "previous_task_id": uid1}
    ]
    
    pila_repo._convert_ids_to_indices(flow)
    
    assert flow[0]["next_cyclic_task_index"] == 1
    assert flow[1]["previous_task_index"] == 0
    assert "unique_id" not in flow[0]

def test_bitacora_get_non_existent(repos):
    """Verify get_diario_bitacora returns empty if no bitacora exists."""
    pila_repo = repos["pila"]
    bid, entradas = pila_repo.get_diario_bitacora(99999) # invalid ID
    assert bid is None
    assert entradas == []

def test_create_existing_bitacora(repos):
    """Verify create_diario_bitacora returns existing ID if called twice."""
    pila_repo = repos["pila"]
    pila_id = pila_repo.save_pila("B Pila", "", {}, [], [])
    
    bid1 = pila_repo.create_diario_bitacora(pila_id)
    bid2 = pila_repo.create_diario_bitacora(pila_id)
    
    assert bid1 == bid2

def test_update_pila(repos):
    """Verify updating a pila works correctly."""
    pila_repo = repos["pila"]
    pila_id = pila_repo.save_pila("Old Name", "Desc", {}, [], [])
    
    # Update name and description
    success = pila_repo.update_pila(pila_id, nombre="New Name", descripcion="New Desc")
    assert success is True
    
    updated_pila, _, _, _ = pila_repo.load_pila(pila_id)
    assert updated_pila["nombre"] == "New Name"
    assert updated_pila["descripcion"] == "New Desc"
    
    # Update flow
    new_flow = [{"task": {"name": "New Task"}}]
    pila_repo.update_pila(pila_id, production_flow=new_flow)
    _, _, flow, _ = pila_repo.load_pila(pila_id)
    assert len(flow) == 1
    assert flow[0]["task"]["name"] == "New Task"
    
    # Fail on unique name
    pila_repo.save_pila("Another Pila", "", {}, [], [])
    result = pila_repo.update_pila(pila_id, nombre="Another Pila")
    assert result == "UNIQUE_CONSTRAINT"
    
    # Update non-existent
    result = pila_repo.update_pila(99999, nombre="Ghost")
    assert result is False

def test_save_cleaning_logic(repos):
    """Verify save_pila cleans canvas IDs."""
    pila_repo = repos["pila"]
    flow = [
        {"task": {"name": "T1", "canvas_unique_id": "temp1", "original_task_id": "orig1"}}
    ]
    
    pila_id = pila_repo.save_pila("Clean Save", "Desc", {}, flow, [])
    
    _, _, saved_flow, _ = pila_repo.load_pila(pila_id)
    assert "canvas_unique_id" not in saved_flow[0]["task"]
    assert "original_task_id" not in saved_flow[0]["task"]
    assert saved_flow[0]["task"]["id"] == "orig1"

def test_update_cleaning_logic(repos):
    """Verify update_pila cleans canvas IDs."""
    pila_repo = repos["pila"]
    pila_id = pila_repo.save_pila("Update Clean", "Desc", {}, [], [])
    
    flow = [
        {"task": {"name": "T2", "canvas_unique_id": "temp2"}}
    ]
    
    pila_repo.update_pila(pila_id, production_flow=flow)
    _, _, saved_flow, _ = pila_repo.load_pila(pila_id)
    assert "canvas_unique_id" not in saved_flow[0]["task"]

def test_update_pila_de_calculo(repos):
    """Verify update_pila updates pila_de_calculo definition."""
    pila_repo = repos["pila"]
    pila_id = pila_repo.save_pila("Calc Update", "Desc", {"v": 1}, [], [])
    
    pila_repo.update_pila(pila_id, pila_de_calculo={"v": 2})
    
    meta, calc, _, _ = pila_repo.load_pila(pila_id)
    assert calc["v"] == 2

def test_cyclic_index_conversion(repos):
    """Verify cyclic index conversion hits all branches."""
    pila_repo = repos["pila"]
    # flow: 0 -> 1 -> 0 (cycle)
    # We provide indices, expecting conversion to IDs
    flow = [
        {"task": {"name": "T0", "id": "uuid-0"}, "next_cyclic_task_index": 1, "unique_id": "uuid-0"},
        {"task": {"name": "T1", "id": "uuid-1"}, "next_cyclic_task_index": 0, "unique_id": "uuid-1"}
    ]
    # Note: save_pila calls _convert_indices_to_ids on a COPY.
    
    pila_repo.save_pila("Cyclic", "Desc", {}, flow, [])
    _, _, saved_flow, _ = pila_repo.load_pila_by_name("Cyclic") if hasattr(pila_repo, "load_pila_by_name") else pila_repo.load_pila(pila_repo.search_pilas("Cyclic")[0].id)
    
    # Check if 'next_cyclic_task_index' is present and correct (ID conversion worked and round-tripped)
    assert "next_cyclic_task_index" in saved_flow[0]
    assert saved_flow[0]["next_cyclic_task_index"] == 1

def test_delete_pila_not_found(repos):
    """Verify deleting non-existent pila returns False."""
    pila_repo = repos["pila"]
    assert pila_repo.delete_pila(99999) is False

def test_get_all_pilas_dates_corrupt(repos, session):
    """Verify robust handling of corrupt dates in get_all_pilas_with_dates."""
    from database.models import Producto
    
    # Create product to satisfy FK constraint
    session.add(Producto(codigo="P-BAD", descripcion="Bad Product", departamento="Test", tipo_trabajador=1, tiene_subfabricaciones=False))
    session.commit()
    
    pila_repo = repos["pila"]
    
    # Use update_pila or direct save with raw json to inject bad data
    # Since save_pila serializes, we might need to manually inject or pass bad object that serializes to bad string?
    # Or rely on the fact that existing logic handles bad date STRINGS.
    
    bad_dates = [{"Tarea": "T1", "Inicio": "NOT-A-DATE", "Fin": "Bad"}]
    pila_repo.save_pila("Bad Dates", "Desc", {}, [], bad_dates, "P-BAD")
    
    results = pila_repo.get_all_pilas_with_dates()
    target = next(p for p in results if p.nombre == "Bad Dates")
    assert target.start_date is None
    assert target.end_date is None

def test_bitacora_error_handling(repos):
    """Verify get_diario_bitacora handles errors gracefully."""
    pila_repo = repos["pila"]
    
    # Patch get_session to return None, which causes safe_execute to return _get_default_error_value() -> None
    # Then the get_diario_bitacora method checks `if result is None` and returns (None, [])
    with patch.object(pila_repo, 'get_session', return_value=None):
        result = pila_repo.get_diario_bitacora(1)
        assert result == (None, [])

def test_standard_dependency_conversion(repos):
    """Verify standard previous_task_index conversion."""
    pila_repo = repos["pila"]
    flow = [
        {"task": {"name": "T0"}, "unique_id": "u0"},
        {"task": {"name": "T1"}, "unique_id": "u1", "previous_task_index": 0}
    ]
    pila_repo.save_pila("Standard Dep", "Desc", {}, flow, [])
    
    # Load and verify it was converted to ID (since load restores index, we assume if it loads with index 0 it worked)
    # But wait, load converts ID -> Index. 
    # If save worked, it stored 'previous_task_id'.
    # If load works, it sees 'previous_task_id' and converts to index 0.
    _, _, loaded_flow, _ = pila_repo.load_pila(pila_repo.search_pilas("Standard Dep")[0].id)
    assert loaded_flow[1]["previous_task_index"] == 0

def test_load_pila_exception(repos):
    """Verify load_pila handles exceptions (returns all None)."""
    pila_repo = repos["pila"]
    
    # Patch get_session to return None, which causes safe_execute to return _get_default_error_value() -> None
    # Then the load_pila method checks `if result is None` and returns (None, None, None, None)
    with patch.object(pila_repo, 'get_session', return_value=None):
        res = pila_repo.load_pila(1)
        assert res == (None, None, None, None)

def test_find_pila_by_name(repos):
    """Verify find_pila_by_name works."""
    pila_repo = repos["pila"]
    pila_repo.save_pila("Find Me", "Desc", {}, [], [])
    
    pila_id = pila_repo.find_pila_by_name("Find Me")
    assert pila_id is not None
    
    missing_id = pila_repo.find_pila_by_name("Missing")
    assert missing_id is None

def test_update_cleaning_logic_branches(repos):
    """Verify update cleaning logic (id present vs missing)."""
    pila_repo = repos["pila"]
    pila_id = pila_repo.save_pila("Clean Branch", "Desc", {}, [], [])
    
    # Case 1: id present, original_task_id present -> id preserved, original removed
    flow_1 = [{"task": {"id": "kept-id", "original_task_id": "ignored-id"}}]
    pila_repo.update_pila(pila_id, production_flow=flow_1)
    _, _, flow, _ = pila_repo.load_pila(pila_id)
    assert flow[0]["task"]["id"] == "kept-id"
    assert "original_task_id" not in flow[0]["task"]

    # Case 2: id missing, original_task_id present -> id restored
    flow_2 = [{"task": {"original_task_id": "restored-id"}}]
    pila_repo.update_pila(pila_id, production_flow=flow_2)
    _, _, flow, _ = pila_repo.load_pila(pila_id)
    assert flow[0]["task"]["id"] == "restored-id"

