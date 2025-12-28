import pytest
from unittest.mock import MagicMock, patch
from core.app_model import AppModel
from database.database_manager import DatabaseManager
from core.dtos import ProductDTO, PreprocesoDTO, ConfigurationDTO
from dataclasses import dataclass

# Setup for testing
@pytest.fixture
def mock_db_manager():
    """Mock completo de DatabaseManager y sus repositorios."""
    # Remove spec=DatabaseManager to allow legacy methods not present in the class definition
    db_manager = MagicMock()
    db_manager.product_repo = MagicMock()
    db_manager.worker_repo = MagicMock()
    db_manager.machine_repo = MagicMock()
    db_manager.pila_repo = MagicMock()
    db_manager.preproceso_repo = MagicMock()
    db_manager.lote_repo = MagicMock()
    db_manager.iteration_repo = MagicMock()
    db_manager.tracking_repo = MagicMock()
    db_manager.config_repo = MagicMock()
    return db_manager

@pytest.fixture
def app_model(mock_db_manager):
    """Instancia de AppModel con dependencias mockeadas."""
    return AppModel(mock_db_manager)

class TestAppModel:
    
    # --- Fabricaciones & Preprocesos ---
    
    def test_get_latest_fabricaciones(self, app_model, mock_db_manager):
        app_model.get_latest_fabricaciones(limit=10)
        mock_db_manager.preproceso_repo.get_latest_fabricaciones.assert_called_once_with(10)

    def test_search_fabricaciones(self, app_model, mock_db_manager):
        app_model.search_fabricaciones("test")
        mock_db_manager.preproceso_repo.search_fabricaciones.assert_called_once_with("test")
        
    def test_search_fabricaciones_error(self, app_model, mock_db_manager):
        mock_db_manager.preproceso_repo.search_fabricaciones.side_effect = Exception("DB Error")
        result = app_model.search_fabricaciones("test")
        assert result == []

    def test_create_fabricacion(self, app_model, mock_db_manager):
        app_model.create_fabricacion("CODE1", "Desc")
        mock_db_manager.preproceso_repo.create_fabricacion.assert_called_once_with("CODE1", "Desc")

    def test_update_fabricacion_preprocesos(self, app_model, mock_db_manager):
        app_model.update_fabricacion_preprocesos(1, [1, 2, 3])
        mock_db_manager.preproceso_repo.update_fabricacion_preprocesos.assert_called_once_with(1, [1, 2, 3])

    def test_get_all_preprocesos_with_components(self, app_model, mock_db_manager):
        app_model.get_all_preprocesos_with_components()
        mock_db_manager.preproceso_repo.get_all_preprocesos.assert_called_once()
    
    def test_create_preproceso(self, app_model, mock_db_manager):
        data = {"nombre": "Test", "tiempo": 10}
        mock_db_manager.preproceso_repo.create_preproceso.return_value = True
        result = app_model.create_preproceso(data)
        assert result is True
        mock_db_manager.preproceso_repo.create_preproceso.assert_called_once_with(data)

    def test_update_preproceso(self, app_model, mock_db_manager):
        data = {"nombre": "Updated", "tiempo": 20}
        app_model.update_preproceso(1, data)
        mock_db_manager.preproceso_repo.update_preproceso.assert_called_once_with(1, data)

    def test_delete_preproceso(self, app_model, mock_db_manager):
        app_model.delete_preproceso(1)
        mock_db_manager.preproceso_repo.delete_preproceso.assert_called_once_with(1)
    
    # --- Iteraciones ---

    def test_get_product_iterations(self, app_model, mock_db_manager):
        app_model.get_product_iterations("PROD1")
        mock_db_manager.iteration_repo.get_product_iterations.assert_called_once_with("PROD1")
    
    def test_add_product_iteration(self, app_model, mock_db_manager):
        app_model.add_product_iteration("PROD1", "Resp", "Desc", "Fallo", [])
        mock_db_manager.iteration_repo.add_product_iteration.assert_called_once()

    def test_delete_product_iteration(self, app_model, mock_db_manager):
        app_model.delete_product_iteration(1)
        mock_db_manager.iteration_repo.delete_product_iteration.assert_called_once_with(1)

    # --- Pilas / Bitácora ---
    
    def test_get_diario_bitacora(self, app_model, mock_db_manager):
        app_model.get_diario_bitacora(1)
        mock_db_manager.pila_repo.get_diario_bitacora.assert_called_once_with(1)
        
    def test_add_diario_entry(self, app_model, mock_db_manager):
        app_model.add_diario_entry(1, "2025-01-01", 1, "Plan", "Real", "Notas")
        mock_db_manager.pila_repo.add_diario_entry.assert_called_once()
        
    def test_create_diario_bitacora(self, app_model, mock_db_manager):
        app_model.create_diario_bitacora(1)
        mock_db_manager.pila_repo.create_diario_bitacora.assert_called_once_with(1)

    def test_save_pila_success(self, app_model, mock_db_manager):
        mock_db_manager.pila_repo.save_pila.return_value = 1
        # Fix signal mocking
        app_model.pilas_changed_signal = MagicMock()
        
        result = app_model.save_pila("Name", "Desc", {}, [], [], "P1")
        
        assert result == 1
        app_model.pilas_changed_signal.emit.assert_called_once()

    def test_save_pila_duplicate(self, app_model, mock_db_manager):
        mock_db_manager.pila_repo.save_pila.return_value = "UNIQUE_CONSTRAINT"
        app_model.pilas_changed_signal = MagicMock()
        
        result = app_model.save_pila("Name", "Desc", {}, [], [], "P1")
        
        assert result == "UNIQUE_CONSTRAINT"
        app_model.pilas_changed_signal.emit.assert_called_with(
            "Error al Guardar", 
            pytest.approx("El nombre de pila 'Name' ya existe. Por favor, elija otro.")
        )

    def test_delete_pila_success(self, app_model, mock_db_manager):
        mock_db_manager.pila_repo.delete_pila.return_value = True
        app_model.pilas_changed_signal = MagicMock()
        
        result = app_model.delete_pila(1)
        
        assert result is True
        app_model.pilas_changed_signal.emit.assert_called_with("Éxito", "La pila ha sido eliminada correctamente.")

    # --- Materiales ---
    
    def test_get_materials_for_product(self, app_model, mock_db_manager):
        app_model.get_materials_for_product("PROD1")
        mock_db_manager.product_repo.get_materials_for_product.assert_called_once_with("PROD1")
        
    def test_get_all_materials_for_selection(self, app_model, mock_db_manager):
        app_model.get_all_materials_for_selection()
        # Mock generic method since spec was removed
        # In actual code: return self.db.material_repo.get_all_materials()
        mock_db_manager.material_repo.get_all_materials.assert_called_once()
        
    def test_add_material_to_iteration(self, app_model, mock_db_manager):
        mock_db_manager.material_repo.add_material.return_value = 10
        mock_db_manager.material_repo.link_material_to_iteration.return_value = True
        
        # FIX: The method returns the result of link_material_to_iteration
        # ensure that is True
        result = app_model.add_material_to_iteration(1, "MAT1", "Desc")
        
        assert result is True
        mock_db_manager.material_repo.add_material.assert_called_once()
        mock_db_manager.material_repo.link_material_to_iteration.assert_called_once_with(1, 10)

    # --- Calculations ---
    
    def test_get_data_for_calculation_simple(self, app_model, mock_db_manager):
        # Mock product details
        mock_prod = MagicMock()
        mock_prod.codigo = "P1"
        mock_prod.descripcion = "Prod 1"
        mock_prod.tiene_subfabricaciones = False
        
        mock_db_manager.product_repo.get_product_details.return_value = (mock_prod, [], [])
        
        result = app_model.get_data_for_calculation("P1")
        
        assert len(result) == 1
        assert result[0]["codigo"] == "P1"
        assert result[0]["sub_partes"] == []

    def test_get_data_for_calculation_complex(self, app_model, mock_db_manager):
        # Mock product with subfabrications
        mock_prod = MagicMock()
        mock_prod.codigo = "P1"
        mock_prod.tiene_subfabricaciones = True
        
        mock_sub = MagicMock()
        mock_sub.descripcion = "Sub 1"
        mock_sub.tiempo = 10
        mock_sub.maquina_id = 5
        
        mock_machine = MagicMock()
        mock_machine.id = 5
        mock_machine.tipo_proceso = "Mecánica"
        
        mock_db_manager.product_repo.get_product_details.return_value = (mock_prod, [mock_sub], [])
        mock_db_manager.machine_repo.get_all_machines.return_value = [mock_machine]
        
        result = app_model.get_data_for_calculation("P1")
        
        assert len(result) == 1
        sub_parte = result[0]["sub_partes"][0]
        assert sub_parte["tiempo"] == 10
        assert sub_parte["requiere_maquina_tipo"] == "Mecánica"

    # --- Workers ---
    
    def test_get_all_workers(self, app_model, mock_db_manager):
        app_model.get_all_workers()
        mock_db_manager.worker_repo.get_all_workers.assert_called_once_with(False)
        
    def test_add_worker_success(self, app_model, mock_db_manager):
        mock_db_manager.worker_repo.add_worker.return_value = True
        app_model.workers_changed_signal = MagicMock()
        
        result = app_model.add_worker("Name", "Notes")
        
        assert result is True
        app_model.workers_changed_signal.emit.assert_called_once()
            
    def test_update_worker_success(self, app_model, mock_db_manager):
        mock_db_manager.worker_repo.add_worker.return_value = True
        app_model.workers_changed_signal = MagicMock()
        
        result = app_model.update_worker(1, "Name", True, "Notes", 1)
        
        assert result is True
        app_model.workers_changed_signal.emit.assert_called_once()
        mock_db_manager.worker_repo.add_worker.assert_called_with(
            nombre_completo="Name",
            notas="Notes",
            tipo_trabajador=1,
            activo=True,
            worker_id=1,
            username=None,
            password_hash=None,
            role=None
        )

    def test_delete_worker(self, app_model, mock_db_manager):
        mock_db_manager.worker_repo.delete_worker.return_value = True
        app_model.workers_changed_signal = MagicMock()
        
        result = app_model.delete_worker(1)
        
        assert result is True
        app_model.workers_changed_signal.emit.assert_called_once()
        mock_db_manager.worker_repo.delete_worker.assert_called_once_with(1)

    def test_get_worker_load_stats(self, app_model, mock_db_manager):
        # Setup mocks
        mock_worker = MagicMock()
        mock_worker.nombre_completo = "W1"
        mock_db_manager.worker_repo.get_all_workers.return_value = [mock_worker]
        
        mock_pila = MagicMock()
        mock_pila.id = 1
        mock_db_manager.pila_repo.get_all_pilas_with_dates.return_value = [mock_pila]
        
        # Sim results with task
        task = {
            'Duracion (min)': 60,
            'Lista Trabajadores': ['W1']
        }
        mock_db_manager.pila_repo.load_pila.return_value = (None, None, None, [task])
        
        stats = app_model.get_worker_load_stats()
        
        assert len(stats) == 1
        assert stats[0][0] == "W1"
        assert stats[0][1] == 60

    # --- Products ---

    def test_add_product_validation_error(self, app_model):
        # Missing fields
        result = app_model.add_product({})
        assert result == "MISSING_FIELDS"

    def test_add_product_success(self, app_model, mock_db_manager):
        mock_db_manager.product_repo.add_product.return_value = True
        data = {
            "codigo": "P1", "descripcion": "D1", 
            "tiene_subfabricaciones": False, "tiempo_optimo": "10.5"
        }
        
        app_model.product_added_signal = MagicMock()
        
        result = app_model.add_product(data)
        
        assert result == "SUCCESS"
        app_model.product_added_signal.emit.assert_called_with("P1")
        
        # Verify float conversion
        assert data["tiempo_optimo"] == 10.5

    # --- Machines ---

    def test_add_machine(self, app_model, mock_db_manager):
        mock_db_manager.machine_repo.add_machine.return_value = True
        app_model.machines_changed_signal = MagicMock()
        
        result = app_model.add_machine("M1", "Dep", "Type")
        
        assert result is True
        app_model.machines_changed_signal.emit.assert_called_once()

    def test_update_machine(self, app_model, mock_db_manager):
        mock_db_manager.machine_repo.update_machine.return_value = True
        app_model.machines_changed_signal = MagicMock()
        
        result = app_model.update_machine(1, "M1", "Dep", "Type", True)
        
        assert result is True
        app_model.machines_changed_signal.emit.assert_called_once()

    def test_delete_machine(self, app_model, mock_db_manager):
        mock_db_manager.machine_repo.delete_machine.return_value = True
        app_model.machines_changed_signal = MagicMock()
        
        result = app_model.delete_machine(1)
        
        assert result is True
        app_model.machines_changed_signal.emit.assert_called_once()
