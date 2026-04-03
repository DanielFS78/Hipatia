"""
Pruebas Unitarias para ProductManager.

Este módulo verifica la gestión de productos, incluyendo búsqueda, selección
y eliminación de productos en el catálogo.
"""
import pytest
from unittest.mock import MagicMock, ANY
from typing import Any
from PyQt6.QtCore import Qt
from controllers.product.product_manager import ProductManager
from core.dtos import ProductDetailsDTO

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_view():
    """Crea un mock de la vista para ProductManager."""
    view = MagicMock(spec=['get_products_tab', 'get_page', 'show_confirmation_dialog', 'show_message'])
    products_tab = MagicMock(spec=['update_search_results', 'display_product_form', 'clear_all', 'search_entry', 'clear_edit_area'])
    products_tab.search_entry = MagicMock(spec=['text'])
    products_tab.search_entry.text.return_value = ""
    view.get_products_tab.return_value = products_tab
    view.get_page.return_value = MagicMock(spec=[])
    return view

@pytest.fixture
def mock_service():
    """Crea un mock del servicio de productos."""
    from core.services.product_service import ProductService
    return MagicMock(spec=ProductService)

@pytest.fixture
def mock_model():
    """Crea un mock del modelo de la aplicación."""
    from app import AppModel
    return MagicMock(spec=AppModel)

@pytest.fixture
def mock_controller():
    """Crea un mock del controlador referente."""
    return MagicMock(spec=[])

@pytest.fixture
def manager(mock_model, mock_view, mock_service, mock_controller):
    """Instancia ProductManager con mocks."""
    app = MagicMock(spec=['ui_controller'])
    app.ui_controller = MagicMock(spec=['on_data_changed'])
    return ProductManager(
        app=app,
        model=mock_model,
        view=mock_view,
        product_facade=mock_service,
        state=MagicMock(spec=['selected_product']),
        controller_ref=mock_controller
    )

def test_on_product_search_changed(manager, mock_view, mock_service):
    """Prueba que el cambio en la búsqueda actualiza los resultados en la vista."""
    # Setup
    text = "test_query"
    products_page = mock_view.get_products_tab.return_value
    mock_service.search_products.return_value = ["Product1", "Product2"]
    
    # Execute
    manager._on_product_search_changed(text)
    
    # Verify
    assert mock_service.search_products.call_count == 1
    mock_service.search_products.assert_called_once_with(text)
    assert products_page.update_search_results.call_count == 1
    products_page.update_search_results.assert_called_once_with(["Product1", "Product2"])

def test_on_product_result_selected_success(manager, mock_view, mock_service):
    """Prueba la visualización de detalles al seleccionar un producto."""
    # Setup
    item = MagicMock(spec=['data'])
    item.data.return_value = "PROD001"
    products_page = mock_view.get_products_tab.return_value
    
    # Simulamos retorno de DTOs
    details = ProductDetailsDTO(
        producto=MagicMock(codigo="PROD001", descripcion="Desc"),
        subfabricaciones=[],
        procesos_mecanicos=[]
    )
    mock_service.get_product_details.return_value = details
    
    # Execute
    manager._on_product_result_selected(item)
    
    # Verify
    assert mock_service.get_product_details.call_count == 1
    mock_service.get_product_details.assert_called_once_with("PROD001")
    assert products_page.display_product_form.call_count == 1
    products_page.display_product_form.assert_called_once_with(ANY, ANY)

def test_on_delete_product_confirmed(manager, mock_view, mock_service):
    """Prueba la eliminación de un producto tras confirmación."""
    # Setup
    codigo = "PROD001"
    mock_view.show_confirmation_dialog.return_value = True
    mock_service.delete_product.return_value = True
    
    # Execute
    manager._on_delete_product(codigo)
    
    # Verify
    assert mock_service.delete_product.call_count == 1
    mock_service.delete_product.assert_called_once_with(codigo)
    assert mock_view.show_message.call_count >= 1
    mock_view.show_message.assert_called_with("Éxito", "Producto eliminado.", "info")
