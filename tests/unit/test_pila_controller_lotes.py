"""
Tests unitarios para AppController - Gestión de Lotes.

Cobertura objetivo: Métodos relacionados con lotes, plantillas y definición.
Incluye tests de comportamiento para búsqueda, añadir/remover, y gestión de plantillas.
"""
import pytest
from unittest.mock import MagicMock, patch, ANY
from PyQt6.QtCore import Qt, QObject
from PyQt6.QtWidgets import QListWidgetItem

from controllers.pila_controller import PilaController
from ui.widgets import CalculateTimesWidget, DefinirLoteWidget


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def controller():
    """Crea PilaController con dependencias mockeadas."""
    mock_app = MagicMock()
    mock_app.model = MagicMock()
    mock_app.model.get_all_lotes.return_value = []
    mock_app.model.search_products.return_value = []
    mock_app.model.search_fabricaciones.return_value = []
    
    view = MagicMock()
    view.pages = {}
    view.show_message = MagicMock()
    view.show_confirmation_dialog = MagicMock(return_value=True)
    mock_app.view = view
    mock_app.schedule_manager = MagicMock()
    mock_app.db = mock_app.model.db
    
    ctrl = PilaController(mock_app)
    return ctrl


# =============================================================================
# TESTS: _on_add_lote_to_pila_clicked
# =============================================================================

class TestOnAddLoteToPilaClicked:
    """Tests para _on_add_lote_to_pila_clicked."""

    def test_add_lote_success(self, controller):
        """Test añadir lote seleccionado a la sesión de planificación."""
        mock_calc = MagicMock(spec=CalculateTimesWidget)
        mock_calc.lote_search_results = MagicMock()
        mock_calc.planning_session = []
        mock_calc.define_flow_button = MagicMock()
        mock_calc._update_plan_display = MagicMock()
        
        controller.view.pages = {"calculate": mock_calc}
        
        mock_item = MagicMock()
        mock_item.data.return_value = (1, "LOTE-TEMPL")
        mock_calc.lote_search_results.currentItem.return_value = mock_item
        
        controller._on_add_lote_to_pila_clicked()
        
        assert len(mock_calc.planning_session) == 1
        assert mock_calc.planning_session[0]['lote_codigo'] == "LOTE-TEMPL"
        mock_calc.define_flow_button.setEnabled.assert_called_with(True)
        mock_calc._update_plan_display.assert_called_once()

    def test_add_lote_no_selection(self, controller):
        """Test warning cuando no hay lote seleccionado."""
        mock_calc = MagicMock(spec=CalculateTimesWidget)
        mock_calc.lote_search_results = MagicMock()
        controller.view.pages = {"calculate": mock_calc}
        mock_calc.lote_search_results.currentItem.return_value = None
        
        controller._on_add_lote_to_pila_clicked()
        
        controller.view.show_message.assert_called_with("Selección Requerida", ANY, "warning")

    def test_add_lote_from_search(self, controller):
        """Test añadir lote desde resultados de búsqueda."""
        mock_calc = MagicMock(spec=CalculateTimesWidget)
        mock_calc.lote_search_results = MagicMock()
        mock_calc.planning_session = []
        mock_calc.define_flow_button = MagicMock()
        mock_calc._update_plan_display = MagicMock()
        
        controller.view.pages = {"calculate": mock_calc}
        
        mock_item = MagicMock()
        mock_item.data.return_value = (99, "LOTE-BUSQUEDA")
        mock_calc.lote_search_results.currentItem.return_value = mock_item
        
        controller._on_add_lote_to_pila_clicked()
        
        # Verifica que se añadió a la sesión
        assert len(mock_calc.planning_session) == 1


# =============================================================================
# TESTS: _on_remove_lote_from_pila_clicked
# =============================================================================

class TestOnRemoveLoteFromPilaClicked:
    """Tests para _on_remove_lote_from_pila_clicked."""

    def test_remove_lote_success(self, controller):
        """Test eliminar item de la sesión de planificación."""
        mock_calc = MagicMock(spec=CalculateTimesWidget)
        mock_calc.pila_content_table = MagicMock()
        mock_calc._update_plan_display = MagicMock()
        controller.view.pages = {"calculate": mock_calc}
        
        # Mock selección de tabla
        mock_calc.pila_content_table.selectionModel().selectedRows.return_value = [MagicMock(row=lambda: 0)]
        mock_calc.planning_session = [{"id": 1}, {"id": 2}]
        
        controller._on_remove_lote_from_pila_clicked()
        
        assert len(mock_calc.planning_session) == 1
        assert mock_calc.planning_session[0]["id"] == 2
        mock_calc._update_plan_display.assert_called()

    def test_remove_lote_last_item(self, controller):
        """Test eliminar el último item de la planificación."""
        mock_calc = MagicMock(spec=CalculateTimesWidget)
        mock_calc.pila_content_table = MagicMock()
        mock_calc._update_plan_display = MagicMock()
        mock_calc.define_flow_button = MagicMock()
        controller.view.pages = {"calculate": mock_calc}
        
        mock_calc.pila_content_table.selectionModel().selectedRows.return_value = [MagicMock(row=lambda: 0)]
        mock_calc.planning_session = [{"id": 1}]
        
        controller._on_remove_lote_from_pila_clicked()
        
        assert len(mock_calc.planning_session) == 0


# =============================================================================
# TESTS: _on_lote_def_product_search_changed
# =============================================================================

class TestOnLoteDefProductSearchChanged:
    """Tests para _on_lote_def_product_search_changed."""

    def test_product_search_with_results(self, controller):
        """Test búsqueda de productos con resultados."""
        mock_page = MagicMock(spec=DefinirLoteWidget)
        mock_page.product_results = MagicMock()
        controller.view.pages = {"definir_lote": mock_page}
        
        controller.model.product_repo.search_products.return_value = [("CODE1", "Producto 1"), ("CODE2", "Producto 2")]
        
        controller._on_lote_def_product_search_changed("prod")
        
        mock_page.product_results.clear.assert_called()
        assert mock_page.product_results.addItem.call_count == 2

    def test_product_search_short_query(self, controller):
        """Test que queries cortos no ejecutan búsqueda."""
        mock_page = MagicMock(spec=DefinirLoteWidget)
        mock_page.product_results = MagicMock()
        controller.view.pages = {"definir_lote": mock_page}
        
        controller._on_lote_def_product_search_changed("p")
        
        # No debería llamar a search con query muy corto
        controller.model.search_products.assert_not_called()


# =============================================================================
# TESTS: _on_lote_def_fab_search_changed
# =============================================================================

class TestOnLoteDefFabSearchChanged:
    """Tests para _on_lote_def_fab_search_changed."""

    def test_fab_search_with_results(self, controller):
        """Test búsqueda de fabricaciones con resultados."""
        mock_page = MagicMock(spec=DefinirLoteWidget)
        mock_page.fab_results = MagicMock()
        controller.view.pages = {"definir_lote": mock_page}
        
        mock_fab = MagicMock(id=1, codigo="FAB-001")
        controller.model.search_fabricaciones.return_value = [mock_fab]
        
        controller._on_lote_def_fab_search_changed("fab")
        
        mock_page.fab_results.clear.assert_called()


# =============================================================================
# TESTS: _on_add_product_to_lote_template
# =============================================================================

class TestOnAddProductToLoteTemplate:
    """Tests para _on_add_product_to_lote_template."""

    def test_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller._on_add_product_to_lote_template)


# =============================================================================
# TESTS: _on_save_lote_template_clicked
# =============================================================================

class TestOnSaveLoteTemplateClicked:
    """Tests para _on_save_lote_template_clicked."""

    def test_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller._on_save_lote_template_clicked)


# =============================================================================
# TESTS: update_lotes_view
# =============================================================================

class TestUpdateLotesView:
    """Tests para update_lotes_view."""

    def test_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller.update_lotes_view)


# =============================================================================
# TESTS: _connect_lotes_management_signals
# =============================================================================

class TestConnectLotesManagementSignals:
    """Tests para _connect_lotes_management_signals."""

    def test_connect_signals_with_page(self, controller):
        """Test conexión de señales con página presente."""
        mock_gestion = MagicMock()
        mock_gestion.lotes_tab = MagicMock()
        mock_gestion.lotes_tab.search_entry = MagicMock()
        mock_gestion.lotes_tab.add_button = MagicMock()
        mock_gestion.lotes_tab.edit_button = MagicMock()
        mock_gestion.lotes_tab.delete_button = MagicMock()
        controller.view.pages = {"gestion_datos": mock_gestion}
        
        controller._connect_lotes_management_signals()

    def test_connect_signals_no_page(self, controller):
        """Test que no crashea sin página."""
        controller.view.pages = {}
        controller._connect_lotes_management_signals()


# =============================================================================
# TESTS: _on_delete_lote_template_clicked
# =============================================================================

class TestOnDeleteLoteTemplateClicked:
    """Tests para _on_delete_lote_template_clicked."""

    def test_delete_lote_method_exists(self, controller):
        """Verifica que el método existe."""
        assert callable(controller._on_delete_lote_template_clicked)


# =============================================================================
# TESTS: _on_calc_lote_search_changed
# =============================================================================

class TestOnCalcLoteSearchChanged:
    """Tests para _on_calc_lote_search_changed."""

    def test_search_with_results(self, controller):
        """Test búsqueda de lotes con resultados."""
        mock_calc = MagicMock(spec=CalculateTimesWidget)
        mock_calc.lote_search_results = MagicMock()
        controller.view.pages = {"calculate": mock_calc}
        
        mock_lote = MagicMock(id=1, codigo="LOTE-TEST")
        controller.model.search_lotes.return_value = [mock_lote]
        
        controller._on_calc_lote_search_changed("test")
        
        mock_calc.lote_search_results.clear.assert_called()
