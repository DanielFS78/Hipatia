import pytest
from datetime import datetime, timedelta

@pytest.mark.e2e
class TestPilaWorkflow:
    """
    End-to-End simulation of Pila management workflow.
    """

    def test_full_pila_workflow(self, repos, session):
        """
        Scenario:
        1. User creates a new Pila for a Product.
        2. User adds simulation results (dates).
        3. User verifies the Pila appears in "with dates" view.
        4. User adds progress to Bitacora.
        5. User searches for the Pila.
        6. User deletes the Pila.
        """
        from database.models import Producto
        
        pila_repo = repos["pila"]
        
        # 1. Create Pila (first create the product to satisfy FK)
        prod_code = "E2E-PROD-XYZ"
        product = Producto(
            codigo=prod_code,
            descripcion="E2E Test Product",
            departamento="Test",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        )
        session.add(product)
        session.commit()
        
        print("\nStep 1: Creating Pila")
        pila_id = pila_repo.save_pila(
            nombre="E2E Pila",
            descripcion="End to End Test",
            pila_de_calculo={"data": "test"},
            production_flow=[],
            simulation_results=[],
            producto_origen_codigo=prod_code
        )
        assert pila_id is not None
        
        # 2. Update with simulation results (Dates)
        print("Step 2: Updating with simulation dates")
        start = datetime(2025, 5, 1, 9, 0)
        end = datetime(2025, 5, 5, 17, 0)
        
        sim_results = [
            {"Tarea": "Start", "Inicio": start.isoformat(), "Fin": start.isoformat()},
            {"Tarea": "End", "Inicio": end.isoformat(), "Fin": end.isoformat()}
        ]
        
        # Save again to update
        success = pila_repo.update_pila(
            pila_id=pila_id,
            descripcion="Updated Description",
            simulation_results=sim_results
        )
        assert success is True
        
        # 3. Verify 'with dates'
        print("Step 3: Verifying dates")
        pilas_with_dates = pila_repo.get_all_pilas_with_dates()
        target = next((p for p in pilas_with_dates if p.id == pila_id), None)
        assert target is not None
        # Note: Repo date logic finds min start and max end from results
        assert target.start_date == start.date()
        assert target.end_date == end.date()
        
        # 4. Add Bitacora Entry
        print("Step 4: Bitacora Entry")
        pila_repo.add_diario_entry(
            pila_id, start.date(), 1, "Plan E2E", "Done E2E", "Notes"
        )
        _, entries = pila_repo.get_diario_bitacora(pila_id)
        assert len(entries) == 1
        
        # 5. Search
        print("Step 5: Searching")
        results = pila_repo.search_pilas("Updated")
        assert len(results) == 1
        assert results[0].id == pila_id
        
        # 6. Delete
        print("Step 6: Deleting")
        pila_repo.delete_pila(pila_id)
        
        # Verify deletion
        assert pila_repo.load_pila(pila_id) == (None, None, None, None)
