"""
Pruebas Unitarias para MaterialManager.

Este módulo verifica la creación, eliminación y desvinculación de materiales
(componentes) en el sistema.
"""
import pytest
from unittest.mock import MagicMock
from controllers.product.material_manager import MaterialManager

@pytest.mark.unit
@pytest.fixture
def mock_view():
    """Crea un mock de la vista para MaterialManager."""
    return MagicMock(spec=["show_message"])

@pytest.fixture
def mock_material_service():
    """Crea un mock del servicio de materiales (usando ProductService)."""
    return MagicMock(
        spec=[
            "add_material",
            "delete_material",
            "unlink_material_from_product",
        ]
    )

@pytest.fixture
def manager(mock_view, mock_material_service):
    """Instancia MaterialManager con mocks."""
    return MaterialManager(
        view=mock_view,
        material_service=mock_material_service,
        controller_ref=MagicMock(spec=[])
    )

def test_handle_create_material_success(manager, mock_view, mock_material_service):
    """Prueba la creación exitosa de un material."""
    # Setup
    code = "MAT001"
    desc = "Material Test"
    mock_material_service.add_material.return_value = 123
    
    # Execute
    result = manager.handle_create_material(code, desc)
    
    # Verify
    assert result is True
    mock_material_service.add_material.assert_called_once_with(code, desc)
    mock_view.show_message.assert_called_with("Éxito", f"Componente '{code}' creado.", "info")

def test_handle_delete_material_success(manager, mock_view, mock_material_service):
    """Prueba la eliminación exitosa de un material."""
    # Setup
    mat_id = 123
    mock_material_service.delete_material.return_value = True
    
    # Execute
    result = manager.handle_delete_material(mat_id)
    
    # Verify
    assert result is True
    mock_material_service.delete_material.assert_called_once_with(mat_id)
    mock_view.show_message.assert_called_with("Éxito", "Componente eliminado.", "info")

def test_handle_unlink_material_success(manager, mock_view, mock_material_service):
    """Prueba la desvinculación exitosa de un material de un producto."""
    # Setup
    prod_code = "PROD001"
    mat_id = 123
    mock_material_service.unlink_material_from_product.return_value = True
    
    # Execute
    result = manager.handle_unlink_material_from_product(prod_code, mat_id)
    
    # Verify
    assert result is True
    mock_material_service.unlink_material_from_product.assert_called_once_with(prod_code, mat_id)
    mock_view.show_message.assert_called_with("Éxito", "Componente desvinculado.", "info")
