"""
Pruebas Unitarias para ProductManager.

Este módulo verifica la gestión de productos, incluyendo búsqueda, selección
y eliminación de productos en el catálogo.
"""
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from PyQt6.QtWidgets import QDialog

from controllers.product.product_manager import ProductManager
from core.dtos import ProductDetailsDTO
from core.services.product_service import ProductService

pytestmark = pytest.mark.unit


class _StubProductController:
    """Sustituto mínimo para `controller_ref` (ProductManager solo lo guarda salvo diálogos)."""


@pytest.fixture
def mock_view():
    """Crea un mock de la vista para ProductManager."""
    view = MagicMock(
        spec=[
            "get_products_tab",
            "get_page",
            "show_confirmation_dialog",
            "show_message",
        ]
    )
    products_tab = MagicMock(
        spec=[
            "update_search_results",
            "display_product_form",
            "clear_all",
            "search_entry",
            "clear_edit_area",
        ]
    )
    products_tab.search_entry = MagicMock(spec=["text"])
    products_tab.search_entry.text.return_value = ""
    view.get_products_tab.return_value = products_tab
    view.get_page.return_value = MagicMock(spec=["set_selected_product"])
    return view


@pytest.fixture
def mock_service():
    """Mock estricto del servicio de productos (firma de métodos)."""
    return create_autospec(ProductService, instance=True)


@pytest.fixture
def mock_controller():
    """Mock del controlador referente con tipo concreto mínimo."""
    return create_autospec(_StubProductController, instance=True)


@pytest.fixture
def manager(mock_view, mock_service, mock_controller):
    """Instancia ProductManager con mocks."""
    app = MagicMock(spec=["ui_controller"])
    app.ui_controller = MagicMock(spec=["on_data_changed"])
    machine_service = MagicMock(spec=["get_all_machines"])
    machine_service.get_all_machines.return_value = []
    return ProductManager(
        app=app,
        machine_service=machine_service,
        view=mock_view,
        product_facade=mock_service,
        state=MagicMock(spec=['selected_product']),
        controller_ref=mock_controller,
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
    d_args, _d_kw = products_page.display_product_form.call_args
    assert d_args[0] is details.producto
    assert d_args[1] == details.subfabricaciones

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


def test_manage_subs_clicked_persists_when_product_exists(manager, mock_view, mock_service):
    """Tras aceptar el diálogo, producto ya existente debe llamar a update (persistencia)."""
    cod_widget = MagicMock(spec=["text"])
    cod_widget.text.return_value = "EXIST-01"

    products_tab = MagicMock(
        spec=["current_subfabricaciones", "form_widgets", "get_product_form_data"]
    )
    products_tab.current_subfabricaciones = []
    products_tab.form_widgets = {"codigo": cod_widget}

    def _form_data() -> dict[str, Any]:
        return {
            "codigo": "EXIST-01",
            "descripcion": "Desc",
            "departamento": "Dep",
            "tipo_trabajador": 1,
            "donde": "Taller",
            "tiene_subfabricaciones": True,
            "tiempo_optimo": 3.0,
            "sub_partes": list(products_tab.current_subfabricaciones),
            "procesos_mecanicos": [],
        }

    products_tab.get_product_form_data.side_effect = _form_data
    mock_view.get_products_tab.return_value = products_tab

    ms = MagicMock(spec=["get_all_machines"])
    ms.get_all_machines.return_value = []
    manager.machine_service = ms

    mock_service.get_product_by_code.return_value = SimpleNamespace(codigo="EXIST-01")
    mock_service.update_product.return_value = True

    updated = [
        {
            "id": 99,
            "producto_codigo": "X",
            "descripcion": "Nueva",
            "tiempo": 7.0,
            "tipo_trabajador": 2,
        }
    ]
    with patch("controllers.product.product_manager.SubfabricacionesDialog") as MockDlg:
        inst = MockDlg.return_value
        inst.exec.return_value = QDialog.DialogCode.Accepted
        inst.get_updated_subfabricaciones.return_value = updated

        manager._on_manage_subs_clicked()

    assert products_tab.current_subfabricaciones == updated
    # Una vez antes de guardar y otra dentro de _on_update_product.
    assert mock_service.get_product_by_code.call_count == 2
    assert all(c.args[0] == "EXIST-01" for c in mock_service.get_product_by_code.call_args_list)

    expected_payload: dict[str, Any] = {
        "codigo": "EXIST-01",
        "descripcion": "Desc",
        "departamento": "Dep",
        "tipo_trabajador": 1,
        "donde": "Taller",
        "tiene_subfabricaciones": True,
        "tiempo_optimo": 7.0,
        "sub_partes": updated,
        "procesos_mecanicos": [],
    }
    mock_service.update_product.assert_called_once_with(
        "EXIST-01", expected_payload, updated
    )
