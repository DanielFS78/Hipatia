"""
Tests unitarios para AppModel.
Actualizado para la arquitectura de servicios (2026):
AppModel delega a FabricacionService, PilaService, ProductService, ReportService.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from core.app_model import AppModel
from core.dtos import ProductDTO, PreprocesoDTO, ConfigurationDTO

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_db_manager():
    """Mock completo de DatabaseManager y sus repositorios."""
    db_manager = MagicMock(spec=[
        "product_repo",
        "worker_repo",
        "machine_repo",
        "pila_repo",
        "preproceso_repo",
        "lote_repo",
        "iteration_repo",
        "tracking_repo",
        "config_repo",
        "material_repo",
        "reports_repo",
    ])
    # Repos: mocks sin autospec (no Qt), pero con spec mínimo para evitar loose_mocks.
    db_manager.product_repo = MagicMock(spec=[])
    db_manager.worker_repo = MagicMock(spec=[])
    db_manager.machine_repo = MagicMock(spec=[])
    db_manager.pila_repo = MagicMock(spec=[])
    db_manager.preproceso_repo = MagicMock(spec=[])
    db_manager.lote_repo = MagicMock(spec=[])
    db_manager.iteration_repo = MagicMock(spec=[])
    db_manager.tracking_repo = MagicMock(spec=[])
    db_manager.config_repo = MagicMock(spec=[])
    db_manager.material_repo = MagicMock(spec=[])
    db_manager.reports_repo = MagicMock(spec=[])
    return db_manager


@pytest.fixture
def app_model(mock_db_manager):
    """Instancia de AppModel con servicios internos mockeados."""
    with patch('core.app_model.ProductService'), \
         patch('core.app_model.PilaService'), \
         patch('core.app_model.WorkerService'), \
         patch('core.app_model.MachineService'), \
         patch('core.app_model.PreparationService'), \
         patch('core.app_model.FabricacionService'), \
         patch('core.app_model.ReportService'), \
         patch('core.app_model.TrackingAssignmentService'):
        model = AppModel(mock_db_manager)
    return model


@pytest.mark.unit
class TestAppModel:

    # --- Fabricaciones & Preprocesos (delegados a fabricacion_service) ---

    def test_get_latest_fabricaciones(self, app_model):
        app_model.get_latest_fabricaciones(limit=10)
        assert app_model.fabricacion_service.get_latest_fabricaciones.call_count == 1
        app_model.fabricacion_service.get_latest_fabricaciones.assert_called_once_with(10)

    def test_search_fabricaciones(self, app_model):
        app_model.search_fabricaciones("test")
        assert app_model.fabricacion_service.search_fabricaciones.call_count == 1
        app_model.fabricacion_service.search_fabricaciones.assert_called_once_with("test")

    def test_search_fabricaciones_error(self, app_model):
        app_model.fabricacion_service.search_fabricaciones.side_effect = Exception("DB Error")
        with pytest.raises(Exception, match="DB Error"):
            app_model.search_fabricaciones("test")
        assert app_model.fabricacion_service.search_fabricaciones.called

    def test_create_fabricacion(self, app_model):
        app_model.create_fabricacion("CODE1", "Desc")
        assert app_model.fabricacion_service.create_fabricacion.call_count == 1
        app_model.fabricacion_service.create_fabricacion.assert_called_once_with("CODE1", "Desc")

    def test_update_fabricacion_preprocesos(self, app_model):
        app_model.update_fabricacion_preprocesos(1, [1, 2, 3])
        assert app_model.fabricacion_service.update_fabricacion_preprocesos.call_count == 1
        app_model.fabricacion_service.update_fabricacion_preprocesos.assert_called_once_with(1, [1, 2, 3])

    def test_get_all_preprocesos_with_components(self, app_model):
        app_model.get_all_preprocesos_with_components()
        assert app_model.fabricacion_service.get_all_preprocesos_with_components.call_count == 1
        app_model.fabricacion_service.get_all_preprocesos_with_components.assert_called_once_with()

    def test_create_preproceso(self, app_model):
        data = {"nombre": "Test", "tiempo": 10}
        app_model.fabricacion_service.create_preproceso.return_value = True
        result = app_model.create_preproceso(data)
        assert result is True
        assert app_model.fabricacion_service.create_preproceso.call_count == 1
        (dto_arg,), _ = app_model.fabricacion_service.create_preproceso.call_args
        assert isinstance(dto_arg, PreprocesoDTO)
        assert dto_arg.nombre == "Test"
        assert dto_arg.tiempo == 10.0

    def test_update_preproceso(self, app_model):
        data = {"nombre": "Updated", "tiempo": 20}
        app_model.update_preproceso(1, data)
        assert app_model.fabricacion_service.update_preproceso.call_count == 1
        args, _ = app_model.fabricacion_service.update_preproceso.call_args
        assert args[0] == 1
        assert isinstance(args[1], PreprocesoDTO)
        assert args[1].id == 1
        assert args[1].nombre == "Updated"
        assert args[1].tiempo == 20.0

    def test_delete_preproceso(self, app_model):
        app_model.delete_preproceso(1)
        assert app_model.fabricacion_service.delete_preproceso.call_count == 1
        app_model.fabricacion_service.delete_preproceso.assert_called_once_with(1)

    # --- Iteraciones (delegadas a product_service) ---

    def test_get_product_iterations(self, app_model):
        app_model.get_product_iterations("PROD1")
        assert app_model.product_service.get_product_iterations.call_count == 1
        app_model.product_service.get_product_iterations.assert_called_once_with("PROD1")

    def test_add_product_iteration(self, app_model):
        app_model.add_product_iteration("PROD1", "Resp", "Desc", "Fallo", [])
        assert app_model.product_service.add_product_iteration.call_count == 1
        app_model.product_service.add_product_iteration.assert_called_once_with(
            "PROD1", "Resp", "Desc", "Fallo", [], None, None
        )

    def test_delete_product_iteration(self, app_model):
        app_model.delete_product_iteration(1)
        assert app_model.product_service.delete_product_iteration.call_count == 1
        app_model.product_service.delete_product_iteration.assert_called_once_with(1)

    # --- Pilas (delegadas a planning_facade / pila_service vía facade) ---

    def test_save_pila_success(self, app_model):
        app_model.pila_service.save_pila.return_value = 1
        result = app_model.save_pila("Name", "Desc", {}, [], [], "P1")
        assert result == 1

    def test_save_pila_duplicate(self, app_model):
        app_model.pila_service.save_pila.return_value = "UNIQUE_CONSTRAINT"
        result = app_model.save_pila("Name", "Desc", {}, [], [], "P1")
        assert result == "UNIQUE_CONSTRAINT"

    def test_delete_pila_success(self, app_model):
        app_model.pila_service.delete_pila.return_value = True
        result = app_model.delete_pila(1)
        assert result is True

    # --- Materiales (delegados a product_service) ---

    def test_get_materials_for_product(self, app_model):
        app_model.get_materials_for_product("PROD1")
        assert app_model.product_service.get_materials_for_product.call_count == 1
        app_model.product_service.get_materials_for_product.assert_called_once_with("PROD1")

    def test_get_all_materials_for_selection(self, app_model):
        app_model.get_all_materials_for_selection()
        assert app_model.product_service.get_all_materials_for_selection.call_count == 1
        app_model.product_service.get_all_materials_for_selection.assert_called_once_with()

    def test_add_material_to_iteration(self, app_model):
        app_model.product_service.add_material_to_iteration.return_value = 10
        result = app_model.add_material_to_iteration(1, "MAT1", "Desc")
        assert result == 10
        assert app_model.product_service.add_material_to_iteration.call_count == 1
        app_model.product_service.add_material_to_iteration.assert_called_once_with(1, "MAT1", "Desc")

    def test_add_material_to_iteration_propagates_none(self, app_model):
        app_model.product_service.add_material_to_iteration.return_value = None
        result = app_model.add_material_to_iteration(2, "X", "Y")
        assert result is None
        app_model.product_service.add_material_to_iteration.assert_called_once_with(2, "X", "Y")

    # --- Calculations (delegados a pila_service) ---

    def test_get_data_for_calculation(self, app_model):
        app_model.pila_service.get_data_for_calculation.return_value = [{"codigo": "P1"}]
        result = app_model.get_data_for_calculation("P1")
        assert result == [{"codigo": "P1"}]
        assert app_model.pila_service.get_data_for_calculation.call_count == 1
        app_model.pila_service.get_data_for_calculation.assert_called_once_with("P1")

    # --- Workers (delegados a worker_service) ---

    def test_get_all_workers(self, app_model):
        app_model.get_all_workers()
        assert app_model.worker_service.get_all_workers.call_count == 1
        app_model.worker_service.get_all_workers.assert_called_once_with(False)

    def test_add_worker_success(self, app_model):
        app_model.worker_service.add_worker.return_value = True
        result = app_model.add_worker("Name", "Notes")
        assert result is True

    def test_update_worker_success(self, app_model):
        app_model.worker_service.update_worker.return_value = True
        result = app_model.update_worker(1, "Name", True, "Notes", 1)
        assert result is True
        assert app_model.worker_service.update_worker.call_count == 1
        app_model.worker_service.update_worker.assert_called_once_with(
            1, "Name", True, "Notes", 1, None, None, None
        )

    def test_delete_worker(self, app_model):
        app_model.worker_service.delete_worker.return_value = True
        result = app_model.delete_worker(1)
        assert result is True
        assert app_model.worker_service.delete_worker.call_count == 1
        app_model.worker_service.delete_worker.assert_called_once_with(1)

    def test_get_worker_load_stats(self, app_model):
        app_model.worker_service.get_worker_load_stats.return_value = {"W1": 60}
        stats = app_model.get_worker_load_stats()
        assert stats == {"W1": 60}

    # --- Products (delegados a product_service) ---

    def test_add_product_validation_error(self, app_model):
        app_model.product_service.add_product.return_value = "MISSING_FIELDS"
        result = app_model.add_product({})
        assert result == "MISSING_FIELDS"

    def test_add_product_success(self, app_model):
        app_model.product_service.add_product.return_value = "SUCCESS"
        data = {
            "codigo": "P1", "descripcion": "D1",
            "tiene_subfabricaciones": False, "tiempo_optimo": "10.5"
        }
        result = app_model.add_product(data)
        assert result == "SUCCESS"

    def test_get_groups_for_machine(self, app_model):
        app_model.preparation_service.get_groups_for_machine.return_value = []
        result = app_model.get_groups_for_machine(1)
        assert result == []
        assert app_model.preparation_service.get_groups_for_machine.call_count == 1
        app_model.preparation_service.get_groups_for_machine.assert_called_once_with(1)

    def test_add_prep_group(self, app_model):
        app_model.preparation_service.add_prep_group.return_value = 1
        result = app_model.add_prep_group(1, "G", "D")
        assert result == 1
        assert app_model.preparation_service.add_prep_group.call_count == 1
        app_model.preparation_service.add_prep_group.assert_called_once_with(1, "G", "D", None)

    def test_update_prep_group(self, app_model):
        app_model.preparation_service.update_prep_group.return_value = True
        result = app_model.update_prep_group(1, "G", "D")
        assert result is True
        assert app_model.preparation_service.update_prep_group.call_count == 1
        app_model.preparation_service.update_prep_group.assert_called_once_with(1, "G", "D", None)

    def test_delete_prep_group(self, app_model):
        app_model.preparation_service.delete_prep_group.return_value = True
        result = app_model.delete_prep_group(1)
        assert result is True
        assert app_model.preparation_service.delete_prep_group.call_count == 1
        app_model.preparation_service.delete_prep_group.assert_called_once_with(1)

    def test_get_steps_for_group(self, app_model):
        app_model.preparation_service.get_steps_for_group.return_value = []
        result = app_model.get_steps_for_group(1)
        assert result == []
        assert app_model.preparation_service.get_steps_for_group.call_count == 1
        app_model.preparation_service.get_steps_for_group.assert_called_once_with(1)

    def test_add_prep_step(self, app_model):
        app_model.preparation_service.add_prep_step.return_value = 1
        result = app_model.add_prep_step(1, "S", 10.0, "D", False)
        assert result == 1
        assert app_model.preparation_service.add_prep_step.call_count == 1
        app_model.preparation_service.add_prep_step.assert_called_once_with(1, "S", 10.0, "D", False)

    # --- Assign task ---

    def test_assign_task_to_worker(self, app_model):
        app_model.worker_service.assign_task_to_worker.return_value = (True, "OK")
        result = app_model.assign_task_to_worker(1, "P1", 5)
        assert result == (True, "OK")

    # --- Dashboard ---

    def test_get_dashboard_stats(self, app_model):
        app_model.fabricacion_service.get_machine_history_summary = MagicMock(return_value={})
        app_model.worker_service.get_worker_load_stats.return_value = {}
        app_model.report_service.get_problematic_components_stats.return_value = {}
        stats = app_model.get_dashboard_stats()
        assert "machine_stats" in stats
        assert "worker_stats" in stats
        assert "component_stats" in stats
