"""
Pruebas Unitarias para FabricacionManager.

Este módulo contiene los tests para el gestor de fabricación, verificando
la búsqueda, actualización y visualización de preprocesos.
"""
import pytest
from unittest.mock import MagicMock, patch
from controllers.product.fabricacion_manager import FabricacionManager

@pytest.mark.unit
@pytest.fixture
def mock_view():
    """Crea un mock de la vista principal con los métodos necesarios."""
    view = MagicMock(spec=["get_fabrications_tab", "get_page", "show_message"])
    view.get_fabrications_tab.return_value = MagicMock(spec=["search_entry", "update_fabrications_table"])
    view.get_fabrications_tab.return_value.search_entry = MagicMock(spec=["text"])
    view.get_page.return_value = MagicMock(spec=[])
    return view

@pytest.fixture
def mock_fabricacion_service():
    """Crea un mock del servicio de fabricación."""
    from core.services.fabricacion_service import FabricacionService
    return MagicMock(spec=FabricacionService)

@pytest.fixture
def mock_product_facade():
    """Crea un mock de la fachada de catálogo (misma superficie que ProductService)."""
    from core.services.product_service import ProductService
    return MagicMock(spec=ProductService)

@pytest.fixture
def mock_planning_facade():
    """PlanningFacade mínimo para datos de cálculo."""
    return MagicMock(spec=["get_data_for_calculation"])

@pytest.fixture
def mock_controller():
    """Crea un mock del controlador referente."""
    return MagicMock(spec=[])

@pytest.fixture
def manager(mock_view, mock_fabricacion_service, mock_product_facade, mock_planning_facade, mock_controller):
    """Instancia el FabricacionManager con sus dependencias mockeadas."""
    return FabricacionManager(
        app=MagicMock(spec=[]),
        view=mock_view,
        fabricacion_service=mock_fabricacion_service,
        product_facade=mock_product_facade,
        planning_facade=mock_planning_facade,
        state=MagicMock(spec=[]),
        controller_ref=mock_controller
    )

def test_on_fabrication_search_changed(manager, mock_view, mock_fabricacion_service):
    """Prueba que el cambio en la búsqueda actualiza la tabla de fabricaciones."""
    # Setup
    text = "FAB001"
    fab_page = mock_view.get_fabrications_tab.return_value
    mock_fabricacion_service.search_fabricaciones.return_value = ["Fab1"]
    
    # Execute
    manager._on_fabrication_search_changed(text)
    
    # Verify
    mock_fabricacion_service.search_fabricaciones.assert_called_once_with(text)
    fab_page.update_fabrications_table.assert_called_once_with(["Fab1"])

def test_refresh_fabricaciones_list(manager, mock_view, mock_fabricacion_service):
    """Prueba que el refresco de la lista utiliza el texto de búsqueda actual."""
    # Setup
    fab_page = mock_view.get_fabrications_tab.return_value
    fab_page.search_entry.text.return_value = "query"
    mock_fabricacion_service.search_fabricaciones.return_value = ["Fab1"]
    
    # Execute
    manager._refresh_fabricaciones_list()
    
    # Verify
    mock_fabricacion_service.search_fabricaciones.assert_called_once_with("query")
    fab_page.update_fabrications_table.assert_called_once_with(["Fab1"])

def test_show_fabricacion_preprocesos(manager, mock_view, mock_fabricacion_service):
    """Prueba que se obtienen los preprocesos para una fabricación específica."""
    # Setup
    fab_id = 123
    mock_fabricacion_service.get_fabricacion_by_id.return_value = MagicMock(
        spec=["id", "codigo", "descripcion"],
        id=fab_id,
        codigo="FAB001",
        descripcion="Fabricación test",
    )
    mock_fabricacion_service.get_all_preprocesos_with_components.return_value = []
    mock_fabricacion_service.get_preprocesos_by_fabricacion.return_value = [
        MagicMock(spec=["id"], id=1),
    ]
    
    # Execute
    manager.show_fabricacion_preprocesos(fab_id)
    
    # Verify
    mock_fabricacion_service.get_preprocesos_by_fabricacion.assert_called_once_with(fab_id)


def test_show_fabricacion_products_returns_when_not_found(manager, mock_fabricacion_service):
    """Cubre rama temprana cuando no existe la fabricación."""
    mock_fabricacion_service.get_fabricacion_by_id.return_value = None
    manager.show_fabricacion_products(999)
    mock_fabricacion_service.get_fabricacion_by_id.assert_called_once_with(999)
