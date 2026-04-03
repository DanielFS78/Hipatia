# -*- coding: utf-8 -*-
"""Tests para MachineService."""
import pytest
from unittest.mock import MagicMock
from core.services.machine_service import MachineService
from core.dtos import MachineDTO
from database.database_manager import DatabaseManager

@pytest.mark.unit
class TestMachineService:
    """
    Tests unitarios para MachineService.
    Sigue el estándar de strict_testing.
    """

    @pytest.fixture
    def mock_db(self):
        db = MagicMock(spec=DatabaseManager)
        db.machine_repo = MagicMock(
            spec=[
                "get_all_machines",
                "add_machine",
                "update_machine",
                "get_machine_maintenance_history",
                "get_distinct_machine_processes",
            ]
        )
        return db

    @pytest.fixture
    def service(self, mock_db):
        return MachineService(mock_db)

    def test_get_all_machines(self, service, mock_db):
        """Prueba que obtiene todas las máquinas delegando al repo."""
        mock_machines = [MachineDTO(id=1, nombre="M1", departamento="DEP", tipo_proceso="T1", activa=True)]
        mock_db.machine_repo.get_all_machines.return_value = mock_machines
        
        result = service.get_all_machines(include_inactive=True)
        
        assert result == mock_machines
        mock_db.machine_repo.get_all_machines.assert_called_once_with(True)

    def test_add_machine_success(self, service, mock_db):
        """Prueba la adición exitosa de una máquina y la emisión de señal."""
        mock_db.machine_repo.add_machine.return_value = True
        
        signal_mock = MagicMock(spec=[])
        service.machines_changed_signal.connect(signal_mock)
        
        result = service.add_machine("M1", "DEP", "T1")
        
        assert result is True
        assert signal_mock.call_count == 1
        signal_mock.assert_called_once_with()
        mock_db.machine_repo.add_machine.assert_called_once_with("M1", "DEP", "T1")

    def test_update_machine_success(self, service, mock_db):
        """Prueba la actualización exitosa de una máquina."""
        mock_db.machine_repo.update_machine.return_value = True
        
        signal_mock = MagicMock(spec=[])
        service.machines_changed_signal.connect(signal_mock)
        
        result = service.update_machine(1, "M1", "DEP", "T1", True)
        
        assert result is True
        assert signal_mock.call_count == 1
        signal_mock.assert_called_once_with()
        mock_db.machine_repo.update_machine.assert_called_once_with(1, "M1", "DEP", "T1", True)

    def test_get_machine_history(self, service, mock_db):
        """Prueba la obtención del historial de mantenimiento."""
        mock_history = [{"date": "2025-01-01", "notes": "Test"}]
        mock_db.machine_repo.get_machine_maintenance_history.return_value = mock_history
        
        history = service.get_machine_history(1)
        
        assert history['maintenance_history'] == mock_history
        assert history['num_fabrications'] == 0 # Default current implementation
        mock_db.machine_repo.get_machine_maintenance_history.assert_called_once_with(1)

    def test_get_distinct_machine_processes(self, service, mock_db):
        """Prueba la obtención de procesos distintos."""
        mock_processes = ["CORTE", "PLEGADO"]
        mock_db.machine_repo.get_distinct_machine_processes.return_value = mock_processes
        
        result = service.get_distinct_machine_processes()
        
        assert result == mock_processes
        assert mock_db.machine_repo.get_distinct_machine_processes.call_count == 1
        mock_db.machine_repo.get_distinct_machine_processes.assert_called_once_with()
