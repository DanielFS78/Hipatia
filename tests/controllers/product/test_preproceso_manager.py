"""
Pruebas Unitarias para PreprocesoManager.

Este módulo contiene los tests para el gestor de preprocesos, verificando
la carga de datos y la gestión de preprocesos individuales.
"""
import pytest
from unittest.mock import MagicMock
from controllers.product.preproceso_manager import PreprocesoManager

@pytest.mark.unit
@pytest.fixture
def mock_view():
    """Crea un mock de la vista para PreprocesoManager."""
    view = MagicMock(spec=["get_page", "show_confirmation_dialog", "show_message"])
    view.get_page.return_value = MagicMock(spec=["load_preprocesos_data"])
    return view

@pytest.fixture
def mock_fabricacion_service():
    """Crea un mock del servicio de fabricación."""
    from core.services.fabricacion_service import FabricacionService
    return MagicMock(spec=FabricacionService)

@pytest.fixture
def mock_material_service():
    """Crea un mock del servicio de materiales (usando ProductService)."""
    return MagicMock(spec=["get_all_materials_for_selection"])

@pytest.fixture
def mock_controller():
    """Crea un mock del controlador referente."""
    return MagicMock(spec=[])

@pytest.fixture
def manager(mock_view, mock_fabricacion_service, mock_material_service, mock_controller):
    """Instancia PreprocesoManager con mocks."""
    return PreprocesoManager(
        view=mock_view,
        fabricacion_service=mock_fabricacion_service,
        material_service=mock_material_service,
        controller_ref=mock_controller
    )

def test_get_preprocesos_by_fabricacion(manager, mock_fabricacion_service):
    """Prueba la obtención de preprocesos para una fabricación dada."""
    # Setup
    fab_id = 1
    mock_fabricacion_service.get_preprocesos_by_fabricacion.return_value = ["Prep1", "Prep2"]
    
    # Execute
    result = manager.get_preprocesos_by_fabricacion(fab_id)
    
    # Verify
    mock_fabricacion_service.get_preprocesos_by_fabricacion.assert_called_once_with(fab_id)
    assert result == ["Prep1", "Prep2"]

def test_load_preprocesos_data(manager, mock_view, mock_fabricacion_service):
    """Prueba la carga de datos de preprocesos en el widget correspondiente."""
    # Setup
    widget = mock_view.get_page.return_value
    data = [{"id": 1, "nombre": "P1"}]
    mock_fabricacion_service.get_all_preprocesos_with_components.return_value = data
    
    # Execute
    manager._load_preprocesos_data()
    
    # Verify
    mock_fabricacion_service.get_all_preprocesos_with_components.assert_called_once_with()
    widget.load_preprocesos_data.assert_called_once_with(data)

def test_delete_preproceso_confirmed(manager, mock_view, mock_fabricacion_service):
    """Prueba la eliminación de un preproceso tras confirmación del usuario."""
    # Setup
    pre_id = 10
    mock_view.show_confirmation_dialog.return_value = True
    mock_fabricacion_service.delete_preproceso.return_value = True
    
    # Execute
    manager.delete_preproceso(pre_id, "Test Prep")
    
    # Verify
    mock_fabricacion_service.delete_preproceso.assert_called_once_with(pre_id)
    mock_view.show_message.assert_called_with("Éxito", "El preproceso 'Test Prep' ha sido eliminado.", "info")
