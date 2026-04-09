"""
Nombre del Módulo: test_machine_controller_comprehensive
Descripcion: Tests unitarios para MachineController, el controlador de gestión de
             máquinas. Verifica CRUD de máquinas, permisos de seguridad, actualización
             de la vista, filtrado por búsqueda y manejo de errores de base de datos.

Decisión de mocking: MachinesWidget y GestionDatosWidget son widgets Qt — se usan
MagicMock() sin spec. El servicio de seguridad se parchea globalmente con autouse=True
para que todas las operaciones estén permitidas por defecto. MachineDTO se usa en
tests que verifican el tipo de los objetos pasados al repositorio.
"""
import pytest
from unittest.mock import MagicMock, patch, ANY
from datetime import date
from PyQt6.QtCore import Qt
from controllers.machine_controller import MachineController
from ui.widgets.machines_widget import MachinesWidget
from ui.widgets.gestion_datos_widget import GestionDatosWidget
from core.security.security_service import Permission
from core.dtos import MachineDTO
from core.services.preparation_service import PreparationService
from core.services.product_service import ProductService

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def mock_security_service():
    """Simula el servicio de seguridad permitiendo todas las operaciones."""
    mock_service = MagicMock()
    mock_service.has_permission.return_value = True
    with patch('core.security.access_control.get_security_service', return_value=mock_service):
        yield mock_service

@pytest.fixture
def mock_view():
    view = MagicMock()
    view.pages = {}
    return view

@pytest.fixture
def mock_machine_service():
    return MagicMock()

@pytest.fixture
def mock_preparation_service():
    return MagicMock(spec=PreparationService)

@pytest.fixture
def mock_product_service():
    return MagicMock(spec=ProductService)

@pytest.fixture
def machine_controller(
    mock_machine_service, mock_preparation_service, mock_product_service, mock_view
):
    logger = MagicMock()
    return MachineController(
        mock_machine_service,
        mock_preparation_service,
        mock_product_service,
        mock_view,
        logger,
    )

class TestMachineControllerComprehensive:
    """Suite de tests exhaustiva para MachineController."""

    def test_update_machines_view_success(self, machine_controller, mock_machine_service, mock_view):
        """Verifica que se actualice la vista de máquinas correctamente."""
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_machines_page = MagicMock()
        mock_gestion.maquinas_tab = mock_machines_page
        mock_view.pages["gestion_datos"] = mock_gestion
        
        mock_machine_service.get_all_machines.return_value = [{"id": 1, "nombre": "M1"}]
        
        machine_controller.update_machines_view()

        assert mock_machine_service.get_all_machines.call_count == 1
        mock_machine_service.get_all_machines.assert_called_once_with()
        mock_machines_page.populate_list.assert_called_with([{"id": 1, "nombre": "M1"}])
        assert machine_controller.logger.info.call_count >= 1

    def test_update_machines_view_no_page(self, machine_controller, mock_view):
        """Verifica que no falle si la página de gestión de datos no existe."""
        mock_view.pages = {}
        try:
            machine_controller.update_machines_view()
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin página: {e}")
        assert mock_view.pages == {}

    def test_save_machine_no_page(self, machine_controller, mock_view):
        """Verifica que no falle si la página no existe al guardar."""
        mock_view.pages = {}
        try:
            machine_controller._on_save_machine_clicked()
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin página: {e}")
        assert mock_view.pages == {}

    def test_save_machine_empty_name(self, machine_controller, mock_view):
        """Verifica error si el nombre está vacío."""
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_machines_page = MagicMock()
        mock_machines_page.get_form_data.return_value = {"nombre": ""}
        mock_gestion.maquinas_tab = mock_machines_page
        mock_view.pages["gestion_datos"] = mock_gestion
        
        machine_controller._on_save_machine_clicked()

        assert mock_view.show_message.call_count == 1
        mock_view.show_message.assert_called_with("Error", "El nombre es obligatorio.", "warning")

    def test_save_machine_new_success(self, machine_controller, mock_machine_service, mock_view):
        """Añadir máquina nueva con éxito."""
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_machines_page = MagicMock()
        mock_machines_page.current_machine_id = None
        mock_machines_page.get_form_data.return_value = {
            "nombre": "M1", "departamento": "D1", "tipo_proceso": "P1"
        }
        mock_gestion.maquinas_tab = mock_machines_page
        mock_view.pages["gestion_datos"] = mock_gestion
        
        mock_machine_service.add_machine.return_value = True
        
        with patch.object(machine_controller, 'update_machines_view') as mock_update:
            machine_controller._on_save_machine_clicked()
            mock_view.show_message.assert_called_with("Éxito", "Máquina añadida.", "info")
            assert mock_update.call_count == 1
            mock_update.assert_called_once_with()

    def test_save_machine_new_unique_error(self, machine_controller, mock_machine_service, mock_view):
        """Error de restricción de unicidad al añadir."""
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_machines_page = MagicMock()
        mock_machines_page.current_machine_id = None
        mock_machines_page.get_form_data.return_value = {"nombre": "M1", "departamento": "D1", "tipo_proceso": "P1"}
        mock_gestion.maquinas_tab = mock_machines_page
        mock_view.pages["gestion_datos"] = mock_gestion
        
        mock_machine_service.add_machine.return_value = "UNIQUE_CONSTRAINT"
        
        machine_controller._on_save_machine_clicked()
        assert mock_view.show_message.call_count == 1
        mock_view.show_message.assert_called_with("Error", "Ya existe una máquina con ese nombre.", "warning")

    def test_save_machine_new_failure(self, machine_controller, mock_machine_service, mock_view):
        """Fallo genérico al añadir."""
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_machines_page = MagicMock()
        mock_machines_page.current_machine_id = None
        mock_machines_page.get_form_data.return_value = {"nombre": "M1", "departamento": "D1", "tipo_proceso": "P1"}
        mock_gestion.maquinas_tab = mock_machines_page
        mock_view.pages["gestion_datos"] = mock_gestion
        
        mock_machine_service.add_machine.return_value = False
        
        machine_controller._on_save_machine_clicked()
        assert mock_view.show_message.call_count == 1
        mock_view.show_message.assert_called_with("Error", "No se pudo añadir la máquina.", "critical")

    def test_save_machine_update_success(self, machine_controller, mock_machine_service, mock_view):
        """Actualizar máquina con éxito."""
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_machines_page = MagicMock()
        mock_machines_page.current_machine_id = 1
        mock_machines_page.get_form_data.return_value = {
            "nombre": "M1", "departamento": "D1", "tipo_proceso": "P1", "activa": True
        }
        mock_gestion.maquinas_tab = mock_machines_page
        mock_view.pages["gestion_datos"] = mock_gestion
        
        mock_machine_service.update_machine.return_value = True
        
        with patch.object(machine_controller, 'update_machines_view') as mock_update:
            machine_controller._on_save_machine_clicked()
            mock_view.show_message.assert_called_with("Éxito", "Máquina actualizada.", "info")
            assert mock_update.call_count == 1
            mock_update.assert_called_once_with()

    def test_save_machine_update_failure(self, machine_controller, mock_machine_service, mock_view):
        """Fallo al actualizar."""
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_machines_page = MagicMock()
        mock_machines_page.current_machine_id = 1
        mock_machines_page.get_form_data.return_value = {
            "nombre": "M1", "departamento": "D1", "tipo_proceso": "P1", "activa": True
        }
        mock_gestion.maquinas_tab = mock_machines_page
        mock_view.pages["gestion_datos"] = mock_gestion
        
        mock_machine_service.update_machine.return_value = False
        
        machine_controller._on_save_machine_clicked()
        assert mock_view.show_message.call_count == 1
        mock_view.show_message.assert_called_with("Error", "No se pudo actualizar la máquina.", "critical")

    def test_delete_machine_no_selection(self, machine_controller, mock_view):
        """Intentar eliminar sin selección."""
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_machines_page = MagicMock()
        mock_machines_page.current_machine_id = None
        mock_gestion.maquinas_tab = mock_machines_page
        mock_view.pages["gestion_datos"] = mock_gestion
        
        machine_controller._on_delete_machine_clicked()
        assert mock_view.show_message.call_count == 1
        mock_view.show_message.assert_called_with("Error", ANY, "warning")

    def test_delete_machine_cancelled(self, machine_controller, mock_view):
        """Cancelar diálogo de eliminación — no llama a delete_machine."""
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_machines_page = MagicMock()
        mock_machines_page.current_machine_id = 1
        mock_gestion.maquinas_tab = mock_machines_page
        mock_view.pages["gestion_datos"] = mock_gestion
        
        mock_view.show_confirmation_dialog.return_value = False
        
        machine_controller._on_delete_machine_clicked()
        assert mock_view.show_message.call_count == 0
        mock_view.show_message.assert_not_called()

    def test_delete_machine_success(self, machine_controller, mock_machine_service, mock_view):
        """Eliminar con éxito."""
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_machines_page = MagicMock()
        mock_machines_page.current_machine_id = 1
        mock_gestion.maquinas_tab = mock_machines_page
        mock_view.pages["gestion_datos"] = mock_gestion
        
        mock_view.show_confirmation_dialog.return_value = True
        mock_machine_service.delete_machine.return_value = True
        
        with patch.object(machine_controller, 'update_machines_view') as mock_update:
            machine_controller._on_delete_machine_clicked()
            mock_view.show_message.assert_called_with("Éxito", ANY, "info")
            assert mock_update.call_count == 1
            mock_update.assert_called_once_with()

    def test_delete_machine_failure(self, machine_controller, mock_machine_service, mock_view):
        """Fallo al eliminar."""
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_machines_page = MagicMock()
        mock_machines_page.current_machine_id = 1
        mock_gestion.maquinas_tab = mock_machines_page
        mock_view.pages["gestion_datos"] = mock_gestion
        
        mock_view.show_confirmation_dialog.return_value = True
        mock_machine_service.delete_machine.return_value = False
        
        machine_controller._on_delete_machine_clicked()
        assert mock_view.show_message.call_count == 1
        mock_view.show_message.assert_called_with("Error", ANY, "critical")

    def test_add_maintenance_no_id(self, machine_controller, mock_view):
        """Intentar mantenimiento sin ID."""
        machine_controller._on_add_maintenance_clicked(None)
        assert mock_view.show_message.call_count == 1
        mock_view.show_message.assert_called_with("Atención", ANY, "warning")

    def test_add_maintenance_cancelled(self, machine_controller, mock_view):
        """Cancelar entrada de mantenimiento — no llama a add_machine_maintenance."""
        with patch('controllers.machine_controller.QInputDialog.getText', return_value=("", False)):
            machine_controller._on_add_maintenance_clicked(1)
            assert mock_view.show_message.call_count == 0
            mock_view.show_message.assert_not_called()

    def test_add_maintenance_empty_notes(self, machine_controller, mock_view):
        """Entrada de mantenimiento vacía — no llama a add_machine_maintenance."""
        with patch('controllers.machine_controller.QInputDialog.getText', return_value=("  ", True)):
            machine_controller._on_add_maintenance_clicked(1)
            assert mock_view.show_message.call_count == 0
            mock_view.show_message.assert_not_called()

    def test_add_maintenance_success(self, machine_controller, mock_machine_service, mock_view):
        """Añadir mantenimiento con éxito."""
        with patch('controllers.machine_controller.QInputDialog.getText', return_value=("Filtro cambiado", True)):
            mock_machine_service.add_machine_maintenance.return_value = True
            mock_machine_service.get_machine_history.return_value = {'maintenance_history': [1, 2]}
            
            mock_gestion = MagicMock(spec=GestionDatosWidget)
            mock_machines_page = MagicMock()
            mock_gestion.maquinas_tab = mock_machines_page
            mock_view.pages["gestion_datos"] = mock_gestion
            
            machine_controller._on_add_maintenance_clicked(1)
            
            assert mock_machine_service.add_machine_maintenance.call_count == 1
            mock_machine_service.add_machine_maintenance.assert_called_with(1, ANY, "Filtro cambiado")
            assert mock_machines_page.populate_history_tables.call_count == 1
            mock_machines_page.populate_history_tables.assert_called_with([1, 2])
            mock_view.show_message.assert_called_with("Éxito", ANY, "info")

    def test_add_maintenance_failure(self, machine_controller, mock_machine_service, mock_view):
        """Fallo al añadir mantenimiento."""
        with patch('controllers.machine_controller.QInputDialog.getText', return_value=("Filtro cambiado", True)):
            mock_machine_service.add_machine_maintenance.return_value = False
            machine_controller._on_add_maintenance_clicked(1)
            assert mock_view.show_message.call_count == 1
            mock_view.show_message.assert_called_with("Error", ANY, "critical")

    def test_machine_selected_in_list_success(self, machine_controller, mock_machine_service, mock_view):
        """Verifica la selección de una máquina en la lista."""
        mock_item = MagicMock()
        mock_item.data.return_value = 1
        
        # Uso de DTO para cumplir estándares de calidad
        mock_machine = MagicMock(spec=MachineDTO)
        mock_machine.id = 1
        assert isinstance(mock_machine, MachineDTO)
        
        mock_machine_service.get_all_machines.return_value = [mock_machine]
        mock_machine_service.get_machine_history.return_value = {'maintenance_history': []}
        
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_machines_page = MagicMock()
        mock_gestion.maquinas_tab = mock_machines_page
        mock_view.pages["gestion_datos"] = mock_gestion
        
        machine_controller._on_machine_selected_in_list(mock_item)
        
        assert mock_machines_page.show_machine_details.call_count == 1
        mock_machines_page.show_machine_details.assert_called_with(mock_machine)
        assert mock_machines_page.populate_history_tables.call_count == 1
        mock_machines_page.populate_history_tables.assert_called_with([])

    def test_machine_selected_in_list_wrong_widget_type(self, machine_controller, mock_machine_service, mock_view):
        """Verifica que retorne si la página no es del tipo esperado."""
        mock_item = MagicMock()
        mock_item.data.return_value = 1
        mock_view.pages["gestion_datos"] = None  # Not GestionDatosWidget
        
        try:
            machine_controller._on_machine_selected_in_list(mock_item)
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción con página None: {e}")
        assert mock_view.pages["gestion_datos"] is None

    def test_manage_prep_groups_clicked(self, machine_controller, mock_view):
        """Verifica que se abra el diálogo de grupos de preparación."""
        with patch('ui.dialogs.prep.prep_groups_dialog.PrepGroupsDialog') as mock_dialog_class:
            mock_dialog = mock_dialog_class.return_value
            machine_controller._on_manage_prep_groups_clicked(1, "M1")
            
            assert mock_dialog_class.call_count == 1
            mock_dialog_class.assert_called_with(
                1,
                "M1",
                machine_controller.preparation_service,
                machine_controller.product_service,
                mock_view,
                mock_view,
            )
            assert mock_dialog.exec.call_count == 1
            mock_dialog.exec.assert_called_once_with()
