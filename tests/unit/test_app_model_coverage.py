
import pytest
from unittest.mock import MagicMock, call, patch
from datetime import datetime
from core.app_model import AppModel

@pytest.fixture
def mock_app_model():
    db_manager = MagicMock()
    # Ensure repos are mocked on db_manager so AppModel picks them up
    db_manager.product_repo = MagicMock()
    db_manager.worker_repo = MagicMock()
    db_manager.machine_repo = MagicMock()
    db_manager.pila_repo = MagicMock()
    db_manager.preproceso_repo = MagicMock()
    db_manager.lote_repo = MagicMock()
    db_manager.iteration_repo = MagicMock()
    db_manager.tracking_repo = MagicMock()
    db_manager.material_repo = MagicMock()
    
    model = AppModel(db_manager)
    return model

class TestAppModelCoverage:

    def test_get_worker_load_stats(self, mock_app_model):
        """Test calculation of worker load from pila results."""
        # Setup data
        mock_app_model.worker_repo.get_all_workers.return_value = [
            MagicMock(nombre_completo="Juan Perez", tipo_trabajador=1),
            MagicMock(nombre_completo="Maria Lopez", tipo_trabajador=2)
        ]
        
        # Pila with date
        pila = MagicMock(id=1)
        mock_app_model.pila_repo.get_all_pilas_with_dates.return_value = [pila]
        
        # Simulation results for load_pila
        # Case 1: Lista Trabajadores (List)
        task1 = {"Duracion (min)": 100, "Lista Trabajadores": ["Juan Perez"]}
        # Case 2: Trabajador Asignado (String legacy)
        task2 = {"Duracion (min)": 50, "Trabajador Asignado": "Maria Lopez"}
        # Case 3: Trabajador Asignado list (Legacy list)
        task3 = {"Duracion (min)": 30, "Trabajador Asignado": ["Juan Perez", "Maria Lopez"]}
        
        mock_app_model.pila_repo.load_pila.return_value = (None, None, None, [task1, task2, task3])
        
        stats = mock_app_model.get_worker_load_stats()
        
        # Verify Juan: 100 + 30 = 130
        # Verify Maria: 50 + 30 = 80
        stats_dict = dict(stats)
        assert stats_dict["Juan Perez"] == 130
        assert stats_dict["Maria Lopez"] == 80

    def test_assign_task_to_worker_success(self, mock_app_model):
        """Test successful task assignment logic."""
        worker_id = 1
        product_code = "P1"
        qty = 10
        of = "OF123"
        
        mock_app_model.worker_repo.get_worker_details.return_value = {"nombre_completo": "Juan Perez"}
        mock_app_model.product_repo.get_product_details.return_value = (MagicMock(descripcion="Desc"), None, None)
        
        mock_app_model.preproceso_repo.create_fabricacion_with_preprocesos.return_value = True
        
        # Mock search to return the ID
        mock_res = MagicMock(codigo="TASK-JUAN-P1-...", id=123)
        mock_app_model.preproceso_repo.search_fabricaciones.return_value = [mock_res]
        
        mock_app_model.preproceso_repo.add_product_to_fabricacion.return_value = True
        mock_app_model.tracking_repo.asignar_trabajador_a_fabricacion.return_value = True
        
        # Since timestamp is dynamic, we patch datetime
        with patch('core.app_model.datetime') as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "TIME"
            # Adjust search mock to match exact code generated
            code_expected = "TASK-JUAN-P1-TIME"
            mock_res.codigo = code_expected
            
            success, msg = mock_app_model.assign_task_to_worker(worker_id, product_code, qty, of)
            
            assert success is True
            assert "asignada a Juan Perez" in msg
            mock_app_model.db.tracking_repo.asignar_trabajador_a_fabricacion.assert_called_with(worker_id, 123)

    def test_get_data_for_calculation_from_session_complex(self, mock_app_model):
        """Test the complex logic of session data gathering."""
        # 1. Lote with 'pila_de_calculo_directa' (Complex dicts)
        lote1 = {
            "unidades": 5,
            "deadline": "2025-01-01",
            "identificador": 1,
            "pila_de_calculo_directa": {
                "productos": {"P1": {"descripcion": "Desc1"}},
                "fabricaciones": {"10": {"id": 10, "codigo": "F1"}}
            }
        }
        
        # Mock product details
        mock_app_model.product_repo.get_product_details.return_value = (
            MagicMock(codigo="P1", descripcion="Desc1", tiene_subfabricaciones=False, tiempo_optimo=10.0), 
            [], []
        )
        
        # Mock fabrication details (Preprocesos)
        fab_mock = MagicMock(preprocesos=[MagicMock(id=99, nombre="Prep1", tiempo=5.0)])
        mock_app_model.preproceso_repo.get_fabricacion_by_id.return_value = fab_mock
        mock_app_model.db.preproceso_repo.get_products_for_fabricacion.return_value = [] # No products inside fab for simplicity
        
        results = mock_app_model.get_data_for_calculation_from_session([lote1])
        
        # Check results
        # 1 Product (P1)
        # 1 Preproceso (Prep1) from Fabrication F1
        assert len(results) >= 2
        
        # Verify Preproceso Task
        prep_task = next((t for t in results if t["codigo"] == "PREP_99"), None)
        assert prep_task is not None
        assert prep_task["tiempo_optimo"] == 5.0
        assert prep_task["units_for_this_instance"] == 5
        
        # Verify Product Task
        prod_task = next((t for t in results if t["codigo"] == "P1"), None)
        assert prod_task is not None
        assert prod_task["units_for_this_instance"] == 5

    def test_get_data_for_calculation_subfabs(self, mock_app_model):
        """Test product with subfabrications and machine types."""
        prod_code = "P_COMPLEX"
        
        # Mock machine types
        mock_app_model.machine_repo.get_all_machines.return_value = [
            MagicMock(id=1, nombre="M1", tipo_proceso="CORTE")
        ]
        
        # Mock return for get_product_details
        sub_dto = MagicMock(descripcion="Sub1", tiempo=20.0, tipo_trabajador=1, maquina_id=1)
        prod_data = MagicMock(
            codigo=prod_code, 
            descripcion="Complex", 
            tiene_subfabricaciones=True,
            tiempo_optimo=0
        )
        mock_app_model.product_repo.get_product_details.return_value = (prod_data, [sub_dto], [])
        
        data = mock_app_model.get_data_for_calculation(prod_code)
        
        assert len(data) == 1
        sub_part = data[0]["sub_partes"][0]
        assert sub_part["tiempo"] == 20.0
        assert sub_part["requiere_maquina_tipo"] == "CORTE" # Verified rehydration
