# -*- coding: utf-8 -*-
"""Tests para PreparationService."""
import pytest
from unittest.mock import MagicMock
from core.services.preparation_service import PreparationService
from core.dtos import PreparationGroupDTO, PreparationStepDTO
from database.database_manager import DatabaseManager

@pytest.mark.unit
class TestPreparationService:
    """
    Tests unitarios para PreparationService.
    Verifica la gestión de grupos y pasos de preparación.
    """

    @pytest.fixture
    def mock_db(self):
        db = MagicMock(spec=DatabaseManager)
        db.machine_repo = MagicMock(
            spec=[
                "get_groups_for_machine",
                "get_prep_info_for_product",
                "add_prep_group",
                "get_steps_for_group",
                "add_prep_step",
                "get_prep_step_details",
            ]
        )
        return db

    @pytest.fixture
    def service(self, mock_db):
        return PreparationService(mock_db)

    def test_get_groups_for_machine(self, service, mock_db):
        """Prueba que obtiene grupos de preparación de una máquina."""
        mock_groups = [PreparationGroupDTO(id=1, nombre="G1", descripcion="D1")]
        mock_db.machine_repo.get_groups_for_machine.return_value = mock_groups
        
        result = service.get_groups_for_machine(1)
        
        assert result == mock_groups
        mock_db.machine_repo.get_groups_for_machine.assert_called_once_with(1)

    def test_get_prep_info_for_product(self, service, mock_db):
        mock_db.machine_repo.get_prep_info_for_product.return_value = (3, 5)
        assert service.get_prep_info_for_product("P-01") == (3, 5)
        mock_db.machine_repo.get_prep_info_for_product.assert_called_once_with("P-01")

    def test_add_prep_group(self, service, mock_db):
        """Prueba la adición de un grupo de preparación."""
        mock_db.machine_repo.add_prep_group.return_value = 1
        
        result = service.add_prep_group(1, "G1", "D1")
        
        assert result == 1
        mock_db.machine_repo.add_prep_group.assert_called_once_with(1, "G1", "D1", None)

    def test_get_steps_for_group(self, service, mock_db):
        """Prueba la obtención de pasos de preparación."""
        mock_steps = [PreparationStepDTO(id=1, nombre="S1", tiempo_fase=10.0, descripcion="D1", es_diario=False)]
        mock_db.machine_repo.get_steps_for_group.return_value = mock_steps
        
        result = service.get_steps_for_group(1)
        
        assert result == mock_steps
        mock_db.machine_repo.get_steps_for_group.assert_called_once_with(1)

    def test_add_prep_step(self, service, mock_db):
        """Prueba la adición de un paso de preparación."""
        mock_db.machine_repo.add_prep_step.return_value = 1
        
        result = service.add_prep_step(1, "S1", 10.0, "D1", False)
        
        assert result == 1
        mock_db.machine_repo.add_prep_step.assert_called_once_with(1, "S1", 10.0, "D1", False)

    def test_get_prep_step_details(self, service, mock_db):
        """Prueba la obtención de detalles de un paso."""
        mock_step = PreparationStepDTO(id=1, nombre="S1", tiempo_fase=10.0, descripcion="D1", es_diario=False)
        mock_db.machine_repo.get_prep_step_details.return_value = mock_step
        
        result = service.get_prep_step_details(1)
        
        assert result == mock_step
        mock_db.machine_repo.get_prep_step_details.assert_called_once_with(1)
