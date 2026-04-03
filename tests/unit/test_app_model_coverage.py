# -*- coding: utf-8 -*-
"""Tests unitarios para AppModel — delegación a servicios y cobertura de métodos."""
import pytest
from unittest.mock import MagicMock, patch, create_autospec

from core.app_model import AppModel
from database.database_manager import DatabaseManager


@pytest.fixture
def mock_app_model():
    """AppModel con DatabaseManager mockeado y servicios parcheados."""
    db_manager = create_autospec(DatabaseManager, instance=True)
    db_manager.product_repo = MagicMock(spec=[])
    db_manager.worker_repo = MagicMock(spec=[])
    db_manager.machine_repo = MagicMock(spec=[])
    db_manager.pila_repo = MagicMock(spec=[])
    db_manager.preproceso_repo = MagicMock(spec=[])
    db_manager.lote_repo = MagicMock(spec=[])
    db_manager.iteration_repo = MagicMock(spec=[])
    db_manager.tracking_repo = MagicMock(spec=[])
    db_manager.material_repo = MagicMock(spec=[])
    db_manager.reports_repo = MagicMock(spec=[])

    with patch('core.app_model.ProductService'), \
         patch('core.app_model.PilaService'), \
         patch('core.app_model.WorkerService'), \
         patch('core.app_model.MachineService'), \
         patch('core.app_model.PreparationService'), \
         patch('core.app_model.FabricacionService'), \
         patch('core.app_model.ReportService'):
        model = AppModel(db_manager)
    return model


@pytest.mark.unit
class TestAppModelCoverage:
    """Tests unitarios para AppModel — delegación a servicios."""

    def test_get_worker_load_stats_delega_a_worker_service(self, mock_app_model):
        """Verifica que get_worker_load_stats delega al worker_service."""
        mock_app_model.worker_service.get_worker_load_stats.return_value = [
            ("Juan Perez", 130),
            ("Maria Lopez", 80),
        ]

        stats = mock_app_model.get_worker_load_stats()

        assert stats == [("Juan Perez", 130), ("Maria Lopez", 80)]
        mock_app_model.worker_service.get_worker_load_stats.assert_called_once_with()

    def test_assign_task_to_worker_success(self, mock_app_model):
        """Verifica que assign_task_to_worker delega al worker_service con los args correctos."""
        worker_id = 1
        product_code = "P1"
        qty = 10
        of = "OF123"

        mock_app_model.worker_service.assign_task_to_worker.return_value = (
            True, "Tarea asignada a Juan Perez"
        )

        success, msg = mock_app_model.assign_task_to_worker(worker_id, product_code, qty, of)

        assert success is True
        assert "asignada a Juan Perez" in msg
        mock_app_model.worker_service.assign_task_to_worker.assert_called_once_with(
            worker_id, product_code, qty, of
        )

    def test_get_data_for_calculation_from_session_delega_a_pila_service(self, mock_app_model):
        """Verifica que get_data_for_calculation_from_session delega al pila_service."""
        lote1 = {
            "unidades": 5,
            "deadline": "2025-01-01",
            "identificador": 1,
            "pila_de_calculo_directa": {
                "productos": {"P1": {"descripcion": "Desc1"}},
                "fabricaciones": {"10": {"id": 10, "codigo": "F1"}},
            },
        }
        expected = [
            {"codigo": "P1", "descripcion": "Desc1", "units_for_this_instance": 5},
            {"codigo": "PREP_99", "tiempo_optimo": 5.0, "units_for_this_instance": 5},
        ]
        mock_app_model.pila_service.get_data_for_calculation_from_session.return_value = expected

        results = mock_app_model.get_data_for_calculation_from_session([lote1])

        assert results == expected
        mock_app_model.pila_service.get_data_for_calculation_from_session.assert_called_once_with(
            [lote1]
        )

    def test_get_data_for_calculation_delega_a_pila_service(self, mock_app_model):
        """Verifica que get_data_for_calculation delega al pila_service con el código correcto."""
        prod_code = "P_COMPLEX"
        expected = [
            {
                "codigo": prod_code,
                "descripcion": "Complex",
                "sub_partes": [{"tiempo": 20.0, "requiere_maquina_tipo": "CORTE"}],
            }
        ]
        mock_app_model.pila_service.get_data_for_calculation.return_value = expected

        data = mock_app_model.get_data_for_calculation(prod_code)

        assert data == expected
        assert data[0]["sub_partes"][0]["tiempo"] == 20.0
        mock_app_model.pila_service.get_data_for_calculation.assert_called_once_with(prod_code)
