
import pytest
from unittest.mock import MagicMock, patch
from controllers.app_controller import AppController

class TestAppControllerUiSignals:

    @pytest.fixture
    def controller(self):
        model = MagicMock()
        view = MagicMock()
        config = MagicMock()
        
        # Setup view pages for signal connection
        view.pages = {
            "products": MagicMock(),
            "fabrications": MagicMock(),
            "gestion_datos": MagicMock(),
            "calculate": MagicMock(),
            "preprocesos": MagicMock(),
            "definir_lote": MagicMock(),
            "reportes": MagicMock(),
            "workers": MagicMock(),
            "machines": MagicMock(),
            "add_product": MagicMock()  # Sometimes used
        }
        
        with patch('controllers.app_controller.CameraManager'), \
             patch('controllers.app_controller.QrGenerator'), \
             patch('controllers.app_controller.LabelManager'), \
             patch('controllers.app_controller.LabelCounterRepository'):
            return AppController(model, view, config)



    def test_connect_products_signals(self, controller):
        """Test connection of product signals."""
        # Since AppController delegates to ProductController, we verify delegation
        controller.product_controller = MagicMock()
        
        controller._connect_products_signals()
        
        controller.product_controller._connect_products_signals.assert_called_once()

    def test_connect_fabrications_signals(self, controller):
        """Test connection of fabrication signals."""
        with patch('controllers.app_controller.GestionDatosWidget', MagicMock) as MockGestion, \
             patch('controllers.app_controller.HomeWidget', MagicMock): # just in case
            
            fab_page = MagicMock()
            fab_page.search_entry = MagicMock()
            controller.view.pages["fabrications"] = fab_page
            
            gestion_page = MockGestion()
            gestion_page.fabricaciones_tab = MagicMock()
            gestion_page.fabricaciones_tab.search_entry = MagicMock()
            controller.view.pages["gestion_datos"] = gestion_page
            
            controller._connect_fabrications_signals()
            
            # fab_page is not used in the method, only gestion_datos_page.fabricaciones_tab
            gestion_page.fabricaciones_tab.search_entry.textChanged.connect.assert_called_with(controller.product_controller._on_fabrication_search_changed)

    def test_connect_calculate_signals(self, controller):
        """Test connection of calculation page signals."""
        # Check if isinstance used
        with patch('controllers.app_controller.CalculateTimesWidget', MagicMock) as MockCalc:
            calc_page = MockCalc()
            calc_page.lote_search_entry = MagicMock()
            calc_page.add_lote_button = MagicMock()
            
            controller.view.pages["calculate"] = calc_page
            
            controller._connect_calculate_signals()
            
            calc_page.lote_search_entry.textChanged.connect.assert_called_with(controller._on_calc_lote_search_changed)
            calc_page.add_lote_button.clicked.connect.assert_called_with(controller._on_add_lote_to_pila_clicked)

    def test_connect_preprocesos_signals(self, controller):
        """Test connection of preprocesos page signals."""
        with patch('controllers.app_controller.PreprocesosWidget', MagicMock) as MockPrep:
            mock_prep_widget = MockPrep()
            mock_prep_widget.add_button = MagicMock()
            mock_prep_widget.edit_button = MagicMock()
            mock_prep_widget.delete_button = MagicMock()
            
            controller.view.pages["preprocesos"] = mock_prep_widget
            
            controller._connect_preprocesos_signals()
            
            mock_prep_widget.set_controller.assert_called_with(controller)
            mock_prep_widget.add_button.clicked.connect.assert_called()
            mock_prep_widget.edit_button.clicked.connect.assert_called()
            mock_prep_widget.delete_button.clicked.connect.assert_called()

    def test_connect_definir_lote_signals(self, controller):
        """Test connection of defining lote signals."""
        with patch('controllers.app_controller.DefinirLoteWidget', MagicMock) as MockLote:
            lote_page = MockLote()
            lote_page.product_search = MagicMock()
            lote_page.fab_search = MagicMock()
            lote_page.add_product_button = MagicMock()
            lote_page.add_fab_button = MagicMock()
            lote_page.remove_item_button = MagicMock()
            lote_page.new_button = MagicMock()
            lote_page.save_button = MagicMock()
            
            controller.view.pages["definir_lote"] = lote_page
            
            controller._connect_definir_lote_signals()
            
            lote_page.product_search.textChanged.connect.assert_called()
            lote_page.fab_search.textChanged.connect.assert_called()
            lote_page.add_product_button.clicked.connect.assert_called()
            lote_page.add_fab_button.clicked.connect.assert_called()
