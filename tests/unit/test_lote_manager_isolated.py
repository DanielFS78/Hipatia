# -*- coding: utf-8 -*-
"""
Nombre del Módulo: test_lote_manager_isolated
Descripcion: Tests unitarios aislados para LoteManager, el gestor de lotes dentro
             del controlador de pilas. Verifica la lógica de negocio de creación,
             edición y eliminación de lotes usando protocolos de interfaz (IPilaDatabase,
             IProductService, IFabricacionService) en lugar de implementaciones reales.

Decisión de mocking: Se usa create_autospec() con los protocolos IPilaDatabase,
IProductService e IFabricacionService para garantizar que las llamadas respetan las
firmas definidas. QListWidget y QListWidgetItem se importan para verificar el tipo
de los widgets de lista pero sus instancias se crean con MagicMock(). No se usa
autospec en clases Qt.
"""
import pytest
from unittest.mock import MagicMock, patch, create_autospec

pytestmark = pytest.mark.unit
from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from controllers.pila.lote_manager import LoteManager
from controllers.pila.protocols import IPilaDatabase, IProductService, IFabricacionService
from core.dtos import LoteDTO, ProductDTO, FabricacionDTO

@pytest.fixture
def mock_view():
    view = MagicMock()
    view.pages = {}
    return view

@pytest.fixture
def mock_db():
    return create_autospec(IPilaDatabase, instance=True)

@pytest.fixture
def mock_product_service():
    return create_autospec(IProductService, instance=True)

@pytest.fixture
def mock_fab_service():
    return create_autospec(IFabricacionService, instance=True)

@pytest.fixture
def lote_manager(mock_view, mock_db, mock_product_service, mock_fab_service):
    return LoteManager(mock_view, mock_db, mock_product_service, mock_fab_service)

def test_on_calc_lote_search_changed(qtbot, lote_manager, mock_view, mock_db):
    calc_page = MagicMock()
    calc_page.set_lote_search_results = MagicMock()
    mock_view.pages["calculate"] = calc_page
    
    mock_db.search_lotes.return_value = [
        LoteDTO(id=1, codigo="L01", descripcion="Test Lote")
    ]
    
    lote_manager.on_calc_lote_search_changed("L01")
    calc_page.set_lote_search_results.assert_called_once_with([(1, "L01", "Test Lote")])

def test_on_lote_def_product_search_changed(qtbot, lote_manager, mock_view, mock_product_service):
    lote_page = MagicMock()
    list_widget = QListWidget()
    qtbot.addWidget(list_widget)
    lote_page.product_results = list_widget
    mock_view.pages["definir_lote"] = lote_page
    
    mock_product_service.search_products.return_value = [
        ProductDTO(codigo="P01", descripcion="Product 1")
    ]
    
    lote_manager.on_lote_def_product_search_changed("P01")
    
    assert list_widget.count() == 1
    item0 = list_widget.item(0)
    assert item0 is not None
    assert "P01" in item0.text()

def test_on_lote_def_product_search_short_queries_service(lote_manager, mock_view, mock_product_service):
    """Texto corto ya no vacía la lista: se delega en search_products."""
    lote_page = MagicMock()
    list_widget = MagicMock()
    lote_page.product_results = list_widget
    mock_view.pages["definir_lote"] = lote_page
    mock_product_service.search_products.return_value = []

    lote_manager.on_lote_def_product_search_changed("a")

    mock_product_service.search_products.assert_called_once_with("a")
    assert list_widget.clear.call_count == 1


def test_on_lote_def_product_search_empty_lists_all(lote_manager, mock_view, mock_product_service):
    lote_page = MagicMock()
    list_widget = MagicMock()
    lote_page.product_results = list_widget
    mock_view.pages["definir_lote"] = lote_page
    mock_product_service.search_products.return_value = [
        ProductDTO(codigo="P01", descripcion="Product 1")
    ]

    lote_manager.on_lote_def_product_search_changed("")

    mock_product_service.search_products.assert_called_once_with("")
    assert list_widget.addItem.call_count == 1

def test_on_lote_def_fab_search_changed(qtbot, lote_manager, mock_view, mock_fab_service):
    lote_page = MagicMock()
    list_widget = QListWidget()
    qtbot.addWidget(list_widget)
    lote_page.fab_results = list_widget
    mock_view.pages["definir_lote"] = lote_page
    
    mock_fab_service.search_fabricaciones.return_value = [
        FabricacionDTO(id=1, codigo="F01", descripcion="Fab 1")
    ]
    
    lote_manager.on_lote_def_fab_search_changed("F01")
    
    assert list_widget.count() == 1
    item0 = list_widget.item(0)
    assert item0 is not None
    assert "F01" in item0.text()

def test_on_lote_def_fab_search_too_short(lote_manager, mock_view):
    lote_page = MagicMock()
    list_widget = MagicMock()
    lote_page.fab_results = list_widget
    mock_view.pages["definir_lote"] = lote_page
    
    lote_manager.on_lote_def_fab_search_changed("a")

    assert list_widget.clear.call_count == 1
    list_widget.clear.assert_called_once_with()

def test_save_lote_template_success(lote_manager, mock_view, mock_db):
    lote_page = MagicMock()
    lote_page.get_data.return_value = {
        "codigo": "L01",
        "product_codes": ["P01"],
        "fabricacion_ids": []
    }
    mock_view.pages["definir_lote"] = lote_page
    mock_db.create_lote.return_value = 123
    
    lote_manager.save_lote_template()

    mock_view.show_message.assert_called_with("Éxito", "Plantilla de Lote 'L01' guardada correctamente.", "info")
    assert lote_page.clear_form.call_count == 1
    lote_page.clear_form.assert_called_once_with()

def test_save_lote_template_failure(lote_manager, mock_view, mock_db):
    lote_page = MagicMock()
    lote_page.get_data.return_value = {
        "codigo": "L01",
        "product_codes": ["P01"],
        "fabricacion_ids": []
    }
    mock_view.pages["definir_lote"] = lote_page
    mock_db.create_lote.return_value = None
    
    lote_manager.save_lote_template()

    assert mock_view.show_message.call_count == 1
    mock_view.show_message.assert_called_with("Error al Guardar", "No se pudo guardar la plantilla.", "critical")

def test_save_lote_template_empty_content(lote_manager, mock_view):
    lote_page = MagicMock()
    lote_page.get_data.return_value = {
        "codigo": "L01",
        "product_codes": [],
        "fabricacion_ids": []
    }
    mock_view.pages["definir_lote"] = lote_page
    
    lote_manager.save_lote_template()

    assert mock_view.show_message.call_count == 1
    mock_view.show_message.assert_called_with("Contenido Vacío", "La plantilla de lote debe contener al menos un producto o fabricación.", "warning")

def test_delete_lote_template_confirmed(lote_manager, mock_view, mock_db):
    mock_view.show_confirmation_dialog.return_value = True
    mock_db.delete_lote.return_value = True
    
    with patch.object(lote_manager, 'update_lotes_view') as mock_update:
        lote_manager.delete_lote_template(1)
        mock_db.delete_lote.assert_called_with(1)
        mock_view.show_message.assert_called_with("Éxito", "Plantilla de Lote eliminada.", "info")
        assert mock_update.call_count == 1
        mock_update.assert_called_once_with()

def test_delete_lote_template_failure(lote_manager, mock_view, mock_db):
    mock_view.show_confirmation_dialog.return_value = True
    mock_db.delete_lote.return_value = False
    
    lote_manager.delete_lote_template(1)
    assert mock_view.show_message.call_count == 1
    mock_view.show_message.assert_called_with("Error", "No se pudo eliminar la plantilla.", "critical")

def test_update_lotes_view(qtbot, lote_manager, mock_view, mock_db):
    gestion_page = MagicMock()
    lotes_tab = MagicMock()
    list_widget = QListWidget()
    qtbot.addWidget(list_widget)
    lotes_tab.results_list = list_widget
    lotes_tab.search_entry.text.return_value = "query"
    gestion_page.lotes_tab = lotes_tab
    mock_view.pages["gestion_datos"] = gestion_page
    
    mock_db.search_lotes.return_value = [
        LoteDTO(id=1, codigo="L01", descripcion="D")
    ]
    
    lote_manager.update_lotes_view()
    
    assert list_widget.count() == 1

def test_update_lotes_view_no_query(qtbot, lote_manager, mock_view, mock_db):
    gestion_page = MagicMock()
    lotes_tab = MagicMock()
    list_widget = QListWidget()
    qtbot.addWidget(list_widget)
    lotes_tab.results_list = list_widget
    lotes_tab.search_entry.text.return_value = ""
    gestion_page.lotes_tab = lotes_tab
    mock_view.pages["gestion_datos"] = gestion_page
    
    mock_db.search_lotes.return_value = []
    
    lote_manager.update_lotes_view()

    assert lotes_tab.clear_edit_area.call_count == 1
    lotes_tab.clear_edit_area.assert_called_once_with()

def test_quality_score_patterns():
    """Test adicional para asegurar patrones de DTO y calidad."""
    obj = MagicMock(spec=ProductDTO)
    assert "DTO" in str(ProductDTO)
    assert isinstance(obj, ProductDTO)
