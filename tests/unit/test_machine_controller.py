# -*- coding: utf-8 -*-
"""Tests unitarios de MachineController: guardar máquina, validaciones, mensajes."""
import pytest
from unittest.mock import MagicMock, patch, ANY
from controllers.machine_controller import MachineController

pytestmark = pytest.mark.unit
from ui.widgets.machines_widget import MachinesWidget
from ui.widgets.gestion_datos_widget import GestionDatosWidget

@pytest.fixture(autouse=True)
def mock_security_service():
    """Permite todas las operaciones RBAC para los tests."""
    mock_service = MagicMock(spec=["has_permission"])
    mock_service.has_permission.return_value = True
    with patch('core.security.access_control.get_security_service', return_value=mock_service):
        yield mock_service

@pytest.fixture
def mock_view():
    view = MagicMock(spec=["pages", "show_message", "show_confirmation_dialog"])
    view.pages = MagicMock(spec=["get"])
    return view

@pytest.fixture
def mock_machine_service():
    service = MagicMock(
        spec=[
            "add_machine",
            "update_machine",
            "add_machine_maintenance",
            "delete_machine",
            "get_all_machines",
            "get_machine_history",
        ]
    )
    service.get_all_machines.return_value = []
    service.get_machine_history.return_value = {"maintenance_history": []}
    return service

@pytest.fixture
def machine_controller(mock_machine_service, mock_view):
    logger = MagicMock(spec=["debug", "info", "warning", "error", "exception"])
    return MachineController(mock_machine_service, mock_view, logger)

class TestMachineController:
    def test_save_machine_new_success(self, machine_controller):
        mock_machines = MagicMock(spec=MachinesWidget)
        mock_machines.current_machine_id = None
        mock_machines.get_form_data.return_value = {"nombre": "M1", "departamento": "D1", "tipo_proceso": "P1"}
        
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_gestion.maquinas_tab = mock_machines
        
        # Configure view.pages.get side_effect
        machine_controller.view.pages.get.side_effect = lambda k: mock_gestion if k == "gestion_datos" else object()
        
        machine_controller.machine_service.add_machine.return_value = True
        
        machine_controller._on_save_machine_clicked()
        assert machine_controller.view.show_message.call_count >= 1
        machine_controller.view.show_message.assert_called_with("Éxito", ANY, "info")
        assert machine_controller.machine_service.add_machine.call_count == 1
        machine_controller.machine_service.add_machine.assert_called_with("M1", "D1", "P1")

    def test_save_machine_update_success(self, machine_controller):
        mock_machines = MagicMock(spec=MachinesWidget)
        mock_machines.current_machine_id = 99
        mock_machines.get_form_data.return_value = {"nombre": "M1", "departamento": "D1", "tipo_proceso": "P1", "activa": True}
        
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_gestion.maquinas_tab = mock_machines
        
        machine_controller.view.pages.get.side_effect = lambda k: mock_gestion if k == "gestion_datos" else object()
        
        machine_controller.machine_service.update_machine.return_value = True
        
        machine_controller._on_save_machine_clicked()
        assert machine_controller.view.show_message.call_count >= 1
        machine_controller.view.show_message.assert_called_with("Éxito", ANY, "info")
        assert machine_controller.machine_service.update_machine.call_count == 1
        machine_controller.machine_service.update_machine.assert_called_with(99, "M1", "D1", "P1", True)

    def test_add_maintenance_success(self, machine_controller):
        with patch('controllers.machine_controller.QInputDialog.getText', return_value=("Nota", True)):
            machine_controller.machine_service.add_machine_maintenance.return_value = True
            
            mock_gestion = MagicMock(spec=GestionDatosWidget)
            mock_gestion.maquinas_tab = MagicMock(spec=["populate_history_tables"])
            machine_controller.view.pages.get.side_effect = lambda k: mock_gestion if k == "gestion_datos" else object()
            
            machine_controller._on_add_maintenance_clicked(1)
            assert machine_controller.view.show_message.call_count >= 1
            machine_controller.view.show_message.assert_called_with("Éxito", ANY, "info")

    def test_delete_machine_confirmed(self, machine_controller):
        machine_controller.view.show_confirmation_dialog.return_value = True
        machine_controller.machine_service.delete_machine.return_value = True
        
        mock_machines = MagicMock(spec=MachinesWidget)
        mock_machines.current_machine_id = 1
        
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_gestion.maquinas_tab = mock_machines
        
        machine_controller.view.pages.get.side_effect = lambda k: mock_gestion if k == "gestion_datos" else object()
        
        machine_controller._on_delete_machine_clicked() # No args
        assert machine_controller.machine_service.delete_machine.call_count == 1
        machine_controller.machine_service.delete_machine.assert_called_with(1)
        assert machine_controller.view.show_message.call_count >= 1
        machine_controller.view.show_message.assert_called_with("Éxito", ANY, "info")

    def test_delete_machine_failed(self, machine_controller):
        machine_controller.view.show_confirmation_dialog.return_value = True
        machine_controller.machine_service.delete_machine.return_value = False
        
        mock_machines = MagicMock(spec=MachinesWidget)
        mock_machines.current_machine_id = 1
        
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_gestion.maquinas_tab = mock_machines
        
        machine_controller.view.pages.get.side_effect = lambda k: mock_gestion if k == "gestion_datos" else object()

        machine_controller._on_delete_machine_clicked() # No args
        assert machine_controller.view.show_message.call_count >= 1
        machine_controller.view.show_message.assert_called_with("Error", ANY, "critical")
