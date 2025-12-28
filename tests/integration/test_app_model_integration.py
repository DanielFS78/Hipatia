import pytest
from app import AppModel
from core.dtos import ProductDTO

@pytest.fixture
def integrated_app_model(in_memory_db_manager):
    """AppModel conectado a una BD real en memoria."""
    return AppModel(in_memory_db_manager)

class TestAppModelIntegration:

    def test_product_lifecycle(self, integrated_app_model):
        """Test completo de ciclo de vida de un producto."""
        # 1. Crear producto
        prod_data = {
            "codigo": "P-INTEG-01",
            "descripcion": "Producto Integración",
            "departamento": "Mecánica",
            "tipo_trabajador": 1,
            "tiene_subfabricaciones": False,
            "tiempo_optimo": 60.0,
            "donde": "Taller"
        }
        result = integrated_app_model.add_product(prod_data)
        assert result == "SUCCESS"
        
        # 2. Leer producto
        details = integrated_app_model.get_product_details("P-INTEG-01")
        assert details[0].codigo == "P-INTEG-01"
        assert details[0].tiempo_optimo == 60.0
        
        # 3. Calcular datos (lógica de negocio importante)
        calc_data = integrated_app_model.get_data_for_calculation("P-INTEG-01")
        assert len(calc_data) == 1
        assert calc_data[0]["tiempo_optimo"] == 60.0
        
        # 4. Eliminar producto
        success = integrated_app_model.delete_product("P-INTEG-01")
        assert success is True
        
        # 5. Verificar eliminación
        details_deleted = integrated_app_model.get_product_details("P-INTEG-01")
        assert details_deleted == (None, [], [])

    def test_assign_task_to_worker_flow(self, integrated_app_model, in_memory_db_manager):
        """Test de flujo complejo: Asignar tarea a trabajador."""
        # Setup: Crear Trabajador y Producto
        in_memory_db_manager.worker_repo.add_worker("Worker Test", "Notes", 1)
        workers = in_memory_db_manager.worker_repo.get_all_workers()
        worker_id = workers[0].id
        
        prod_data = {
            "codigo": "P-TASK-01",
            "descripcion": "Producto para Tarea",
            "departamento": "Montaje",
            "tipo_trabajador": 1,
            "tiene_subfabricaciones": False,
            "tiempo_optimo": 30.0
        }
        integrated_app_model.add_product(prod_data)
        
        # Action: Asignar tarea
        success, message = integrated_app_model.assign_task_to_worker(
            worker_id=worker_id,
            product_code="P-TASK-01",
            quantity=5,
            orden_fabricacion="OF-123"
        )
        
        assert success is True
        assert "asignada" in message
        
        # Verifica que se creó la fabricación
        fabs = integrated_app_model.get_latest_fabricaciones(1)
        assert len(fabs) == 1
        assert "OF: OF-123" in fabs[0].descripcion
        
        # Verifica link con tracking
        tasks_worker = integrated_app_model.db.tracking_repo.get_fabricaciones_por_trabajador(worker_id)
        assert len(tasks_worker) == 1
        assert tasks_worker[0].codigo == fabs[0].codigo

    def test_machine_management_flow(self, integrated_app_model):
        """Test de gestión de máquinas y tipos de proceso."""
        # 1. Añadir máquinas
        integrated_app_model.add_machine("CNC-TEST", "Mecánica", "Fresado")
        
        # 2. Verificar tipos de proceso distintos
        processes = integrated_app_model.get_distinct_machine_processes()
        assert "Fresado" in processes
        
        # 3. Buscar máquina por tipo
        machines = integrated_app_model.get_machines_by_process_type("Fresado")
        assert len(machines) == 1
        assert machines[0].nombre == "CNC-TEST"
        
        # 4. Mantenimiento
        m_id = machines[0].id
        integrated_app_model.add_machine_maintenance(m_id, "2025-01-01", "Revision")
        
        # 5. Historial
        history = integrated_app_model.get_machine_history(m_id)
        assert len(history['maintenance_history']) == 1
        assert history['maintenance_history'][0].notes == "Revision"

    def test_save_and_load_pila(self, integrated_app_model):
        """Test de persistencia de Pilas de Cálculo."""
        # Datos simulados
        pila_calc = {"productos": {"P1": {"unidades": 10}}}
        flow = [{"task": "T1"}]
        results = [{"task": "T1", "time": 10}]
        
        # Crear producto origen para satisfacer FK
        integrated_app_model.add_product({
            "codigo": "PROD-ORIGEN",
            "descripcion": "Producto Origen",
            "tiempo_optimo": 10.0,
            "tiene_subfabricaciones": False,
            "departamento": "Test",
            "tipo_trabajador": 1
        })

        # Guardar
        result_id = integrated_app_model.save_pila(
            "Pila Test 1", "Descripción", 
            pila_calc, flow, results, "PROD-ORIGEN"
        )
        assert isinstance(result_id, int)
        
        # Listar
        pilas = integrated_app_model.get_all_pilas()
        assert len(pilas) >= 1
        assert pilas[0].nombre == "Pila Test 1"
        
        # Cargar detalles
        loaded = integrated_app_model.load_pila(result_id)
        # Retorna: (metadata, pila_de_calculo, production_flow, simulation_results)
        assert loaded[0]["nombre"] == "Pila Test 1"
        assert loaded[1] == pila_calc
        # production_flow (loaded[2]) se modifica al guardar (IDs únicos), difícil comparar directo
        assert len(loaded[2]) == 1
        assert loaded[2][0]["task"] == "T1"
        assert loaded[0]["producto_origen"] == "PROD-ORIGEN" # Metadata contains prod orig
        assert loaded[3] == results
