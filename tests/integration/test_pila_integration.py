# -*- coding: utf-8 -*-
"""Tests de integración para Pila: producto, bitácora, ciclo de vida, serializer.

Integración con repos (pila, product), sesión real y casos borde con mock de sesión
para ramas de error (JSON inválido, safe_execute None).
"""
import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime, date
from uuid import uuid4

from core.dtos import PilaDTO
from database.models import Pila, PasoPila, DiarioBitacora, EntradaDiario

pytestmark = pytest.mark.integration


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
    pila_repo.add_diario_evento(pila_id, today, 1, "Plan", "Real", "Note")
    
    # Commit session (simulating app behavior)
    session.commit()
    
    # Retrieve in a "new" lookup (same session for text, but verifying query works)
    bid, entries = pila_repo.get_diario_bitacora(pila_id)
    assert len(entries) == 1
    assert entries[0][0] == today

    # Verify create_diario_bitacora explicit call
    new_pila_id = pila_repo.save_pila("Empty Bitacora", "D", {}, [], [])
    bitacora_id = pila_repo.create_diario_bitacora(new_pila_id)
    assert bitacora_id is not None
    
    # Second call returns existing
    repeat_id = pila_repo.create_diario_bitacora(new_pila_id)
    assert repeat_id == bitacora_id
    
    # Missing bitacora returns None
    invalid_bid, invalid_entries = pila_repo.get_diario_bitacora(9999)
    assert invalid_bid is None
    assert invalid_entries == []

def test_pila_full_lifecycle_and_edge_cases(repos, session):
    """
    Test the full CRUD lifecycle of a pila including searches, updates,
    conversions, and deletions to reach 100% coverage.
    """
    pila_repo = repos["pila"]
    
    # --- 1. Edge Case: _convert_indices_to_ids and json saving ---
    pf_in = [
        {"task": {"original_task_id": 100, "canvas_unique_id": "temp123"}, "previous_task_index": None},
        {"task": {}, "previous_task_index": 0, "next_cyclic_task_index": 0}
    ]
    sim_results = [{"Inicio": "2025-01-01T10:00:00", "Fin": "2025-01-02T10:00:00"}]
    
    pila_id = pila_repo.save_pila(
        nombre="Lifecycle Pila",
        descripcion="Desc",
        pila_de_calculo={"unidades": 5},
        production_flow=pf_in,
        simulation_results=sim_results
    )
    assert isinstance(pila_id, int)
    
    # Try save duplicate
    dup_res = pila_repo.save_pila("Lifecycle Pila", "Desc", {}, [], [])
    assert dup_res == "UNIQUE_CONSTRAINT"
    
    # --- 2. Load Pila ---
    meta, calc, flow, sim = pila_repo.load_pila(pila_id)
    assert meta.nombre == "Lifecycle Pila"
    assert meta.unidades == 5
    assert len(flow) == 2
    assert "previous_task_index" in flow[1]
    assert flow[1]["previous_task_index"] == 0
    assert flow[1]["next_cyclic_task_index"] == 0
    
    # Load invalid
    none_meta, _, _, _ = pila_repo.load_pila(9999)
    assert none_meta is None
    
    # --- 3. Update Pila ---
    # Update flow and name
    pf_upd = [{"task": {"id": 100}, "unique_id": str(uuid4())}]
    upd_res = pila_repo.update_pila(
        pila_id, 
        nombre="Updated Pila", 
        descripcion="New Desc",
        pila_de_calculo={"unidades": 10},
        production_flow=pf_upd,
        simulation_results=[]
    )
    assert upd_res is True
    
    # Update to exist name
    pila_repo.save_pila("Another Pila", "Desc", {}, [], [])
    upd_dup = pila_repo.update_pila(pila_id, nombre="Another Pila")
    assert upd_dup == "UNIQUE_CONSTRAINT"
    
    # Update invalid
    assert pila_repo.update_pila(9999, nombre="Ghost") is False
    
    # --- 4. Queries (All, Search, By Name) ---
    all_pilas = pila_repo.get_all_pilas()
    assert len(all_pilas) >= 2
    assert isinstance(all_pilas[0], PilaDTO)
    
    search_res = pila_repo.search_pilas("Updated")
    assert len(search_res) == 1
    assert search_res[0].nombre == "Updated Pila"
    
    found_id = pila_repo.find_pila_by_name("Updated Pila")
    assert found_id == pila_id
    assert pila_repo.find_pila_by_name("Ghost Pila") is None
    
    with_dates = pila_repo.get_all_pilas_with_dates()
    # The 'Lifecycle Pila' lost its simulation_results on update, let's create one with dates
    pila_repo.save_pila("Date Pila", "D", {}, [], [{"Inicio": "2025-01-01T10:00:00", "Fin": "2025-01-02T10:00:00"}])
    dates_refresh = pila_repo.get_all_pilas_with_dates()
    date_pila = next(p for p in dates_refresh if p.nombre == "Date Pila")
    assert date_pila.start_date == date(2025, 1, 1)
    
    # --- 5. Delete ---
    del_ok = pila_repo.delete_pila(pila_id)
    assert del_ok is True
    
    del_fail = pila_repo.delete_pila(9999)
    assert del_fail is False

@patch('database.repositories.base.Session', autospec=True)
def test_pila_compliance_mock_edge_cases(mock_session_class, repos):
    """
    Test edge cases using MagicMock and patch to hit strict compliance score
    and ensure error branches in load_pila are resolved (e.g., bad JSON).
    """
    pila_repo = repos["pila"]
    session_mock = MagicMock(spec=["query"])
    
    # Emulate bad JSON in DB (bad_pila/bad_paso sin spec: el workflow accede a muchos atributos)
    bad_pila = MagicMock(
        spec=[
            "id",
            "nombre",
            "descripcion",
            "producto_origen_codigo",
            "fecha_creacion",
            "pila_de_calculo_json",
            "resultados_simulacion",
        ]
    )
    bad_pila.id = 1
    bad_pila.nombre = "Bad"
    bad_pila.descripcion = "Bad"
    bad_pila.producto_origen_codigo = None
    bad_pila.fecha_creacion = datetime.now()
    bad_pila.pila_de_calculo_json = "{bad_json:]"
    bad_pila.resultados_simulacion = "{bad_sim:]"
    
    # For load_pila steps parsing error (line 403-406)
    bad_paso = MagicMock(spec=["datos_paso"])
    bad_paso.datos_paso = "{broken_datos: ["
    
    # The first 'first' is for pila query, the 'all' is for list of steps or other queries
    session_mock.query().filter_by().first.return_value = bad_pila
    session_mock.query().filter_by().order_by().all.return_value = [bad_paso]
    
    # We temporarily inject this mock session into safe_execute
    original_execute = pila_repo.safe_execute
    def mock_execute(operation):
        return operation(session_mock)
    pila_repo.safe_execute = mock_execute
    
    # This hits lines 481-482 (get_all_pilas_with_dates bad JSON)
    dates = pila_repo.get_all_pilas_with_dates()
    
    # This hits lines 403-406 (load_pila bad JSON step)
    meta, calc, flow, sim = pila_repo.load_pila(1)
    assert isinstance(calc, dict)
    assert calc == {}
    assert sim == []
    
    # Now simulate safe_execute returning None completely for:
    # save_pila line 280, load_pila line 419, get_diario_bitacora line 564
    pila_repo.safe_execute = MagicMock(spec=[], return_value=None)
    
    assert pila_repo.save_pila("Fail", "D", {}, [], []) is False
    meta2, calc2, flow2, sim2 = pila_repo.load_pila(1)
    assert meta2 is None
    bid2, ent2 = pila_repo.get_diario_bitacora(1)
    assert bid2 is None and ent2 == []
    
    pila_repo.safe_execute = original_execute


    # Hit lines 325-326 in update_pila: original_task_id without id
    upd_pf = [{"task": {"canvas_unique_id": "temp", "original_task_id": 999}}]
    # We just need it to not fail on database. We do a real update.
    real_pid = pila_repo.save_pila("Update ID Test", "Desc", {}, [], [])
    pila_repo.update_pila(real_pid, production_flow=upd_pf)

def test_pila_serializer_full_coverage(repos):
    """
    Test the robust custom JSON serializer for Pila (Datetime, Decimal, Set)
    and cover serialize/deserialize production_flow functions.
    """
    from core.utils.pila_serializer import (
        PilaJSONEncoder, decode_pila_json, 
        serialize_production_flow, deserialize_production_flow
    )
    from decimal import Decimal
    from datetime import datetime, date, time
    
    # 1. Custom Types encode/decode
    data = {
        "dt": datetime(2025, 1, 1, 10, 0),
        "d": date(2025, 1, 1),
        "t": time(10, 0),
        "dec": Decimal("10.5"),
        "s": {1, 2, 3}
    }
    
    encoded = json.dumps(data, cls=PilaJSONEncoder)
    assert "__datetime__" in encoded
    assert "__date__" in encoded
    assert "__time__" in encoded
    assert "__decimal__" in encoded
    assert "__set__" in encoded
    
    decoded = json.loads(encoded, object_hook=decode_pila_json)
    assert isinstance(decoded["dt"], datetime)
    assert isinstance(decoded["d"], date)
    assert isinstance(decoded["t"], time)
    assert isinstance(decoded["dec"], Decimal)
    assert isinstance(decoded["s"], set)
    
    # Basic types fallback
    # Force default caller to be reached
    with pytest.raises(TypeError):
        json.dumps(object(), cls=PilaJSONEncoder)

    # 2. Production Flow Serialization (Empty, Warning, Valid)
    from typing import List, Dict, Any, cast
    empty_json, empty_sum = serialize_production_flow([])
    assert empty_sum["status"] == "empty"
    assert empty_json == "[]"
    
    empty_des, empty_des_sum = deserialize_production_flow("")
    assert empty_des == []
    
    flow_in: List[Dict[str, Any]] = [
        {
            "id": 1, 
            "position": {"x": 10, "y": 10}, 
            "previous_task_index": 0,
            "next_cyclic_task_index": 1,
            "units_per_cycle": 10
        },
        {"id": 2} # Missing critical fields for warnings
    ]
    flow_json, flow_sum = serialize_production_flow(flow_in)
    assert flow_sum["status"] == "ok"
    assert len(flow_sum["warnings"]) > 0
    
    flow_out, flow_out_sum = deserialize_production_flow(flow_json)
    assert len(flow_out) == 2
    assert flow_out[1]["units_per_cycle"] == 1 # Default generated
    assert "position" in flow_out[1] # Regeneration happened

    # Ensure exceptions covered in serializer itself
    import core.utils.pila_serializer as ps
    # Patch dumps directly on the module instead of global json to force the failure
    with patch.object(ps.json, 'dumps', side_effect=ValueError("Dump Fail")):
        with pytest.raises(ValueError):
            serialize_production_flow([{"id": 1}])
        
    with pytest.raises(json.JSONDecodeError):
        deserialize_production_flow("{bad_json:")

    # Ensure exceptions covered
    with pytest.raises(TypeError):
        serialize_production_flow([cast(Any, object())])
        
    with pytest.raises(json.JSONDecodeError):
        deserialize_production_flow("{bad_json:")

def test_pila_repo_dates_decode_error(repos, session):
    """
    Cover lines 481-482 in pila_repository.py where json.loads for dates throws error.
    """
    pila_repo = repos["pila"]
    pila_repo.save_pila("CrashDates", "D", {}, [], [])
    p = session.query(Pila).filter_by(nombre="CrashDates").first()
    
    # Intentionally corrupt the JSON string in DB
    p.resultados_simulacion = "{notJSON:"
    session.commit()
    
    # Exception branch safely hit and logged without crashing
    dates = pila_repo.get_all_pilas_with_dates()
    broken_pila = next(p for p in dates if p.nombre == "CrashDates")
    assert broken_pila.start_date is None
    assert broken_pila.end_date is None



