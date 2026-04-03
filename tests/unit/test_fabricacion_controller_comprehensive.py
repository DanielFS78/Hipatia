# -*- coding: utf-8 -*-
"""
Tests comprensivos unitarios para FabricacionController.
Verifica la delegación correcta al ProductController y manejo de productos.
"""

import pytest
import logging
from unittest.mock import MagicMock, patch, create_autospec

# Global mock for pyqtSignal to avoid SIGABRT on import
with patch('PyQt6.QtCore.pyqtSignal', return_value=MagicMock(spec=["connect", "emit"])):
    from controllers.fabricacion_controller import FabricacionController
from controllers.product_controller_v2 import ProductController
from database.database_manager import DatabaseManager
from core.dtos import ProductDTO

@pytest.mark.unit
class TestFabricacionControllerComprehensive:
    """Suite de tests comprensivos para FabricacionController."""

    @pytest.fixture
    def mock_db(self):
        """Fixture para mockear el DatabaseManager usando create_autospec."""
        db = create_autospec(DatabaseManager, instance=True)
        db.product_repo = MagicMock(spec=[])
        return db

    @pytest.fixture
    def mock_view(self):
        """Fixture para mockear la vista."""
        return MagicMock(spec=["show_message"])

    @pytest.fixture
    def mock_product_controller(self):
        """Fixture para mockear el ProductController usando create_autospec."""
        return create_autospec(ProductController, instance=True)

    @pytest.fixture
    def mock_logger(self):
        """Fixture para mockear el logger."""
        return MagicMock(spec=["debug", "info", "warning", "error", "exception"])

    @pytest.fixture
    def controller(self, mock_db, mock_view, mock_product_controller, mock_logger):
        """Fixture para obtener una instancia del controlador."""
        # Patching pyqtSignal again for the instance emission checks
        with patch('PyQt6.QtCore.pyqtSignal', return_value=MagicMock(spec=["connect", "emit"])):
             ctrl = FabricacionController(mock_db, mock_view, mock_product_controller, mock_logger)
             # Manually mock signals since we patched pyqtSignal during import
             ctrl.fabricacion_created = MagicMock(spec=["connect", "emit"])
             ctrl.fabricaciones_updated = MagicMock(spec=["connect", "emit"])
             return ctrl

    # =========================================================================
    # TESTS DE INICIALIZACIÓN Y SEÑALES
    # =========================================================================

    def test_init_assignment(self, mock_db, mock_view, mock_product_controller, mock_logger):
        """Verifica que el constructor asigna correctamente las dependencias."""
        ctrl = FabricacionController(mock_db, mock_view, mock_product_controller, mock_logger)
        assert ctrl.db == mock_db
        assert ctrl.view == mock_view
        assert ctrl.product_controller == mock_product_controller
        assert ctrl.logger == mock_logger

    def test_connect_signals(self, controller):
        """Verifica que el método de conexión de señales se ejecuta sin error."""
        try:
            controller.connect_signals()
        except Exception:
            pytest.fail("connect_signals no debería propagar excepciones")
        assert controller is not None

    # =========================================================================
    # TESTS DE DELEGACIÓN A PRODUCT_CONTROLLER
    # =========================================================================

    def test_show_create_fabricacion_dialog(self, controller, mock_product_controller):
        """Verifica delegación de creación de fabricación."""
        controller.show_create_fabricacion_dialog()
        assert mock_product_controller.show_create_fabricacion_dialog.call_count == 1
        mock_product_controller.show_create_fabricacion_dialog.assert_called_once_with()

    def test_search_fabricaciones(self, controller, mock_product_controller):
        """Verifica delegación de búsqueda de fabricaciones."""
        controller.search_fabricaciones("test search")
        mock_product_controller.search_fabricaciones.assert_called_with("test search")

    def test_show_fabricacion_preprocesos(self, controller, mock_product_controller):
        """Verifica delegación de visualización de preprocesos."""
        controller.show_fabricacion_preprocesos(123)
        mock_product_controller.show_fabricacion_preprocesos.assert_called_with(123)

    def test_refresh_fabricaciones_list(self, controller, mock_product_controller):
        """Verifica actualización de lista y emisión de señal."""
        controller.refresh_fabricaciones_list()
        assert mock_product_controller._refresh_fabricaciones_list.call_count == 1
        mock_product_controller._refresh_fabricaciones_list.assert_called_once_with()
        assert controller.fabricaciones_updated.emit.call_count == 1
        controller.fabricaciones_updated.emit.assert_called_once_with()

    # =========================================================================
    # TESTS DE LÓGICA DE NEGOCIO (PRODUCTOS PARA CÁLCULO)
    # =========================================================================

    def test_get_fabricacion_products_for_calculation_success(self, controller, mock_product_controller):
        """Verifica la obtención y formateo de productos exitosa."""
        from core.dtos import CalculationProductDTO
        
        dto1 = CalculationProductDTO(
            codigo="P01", descripcion="Desc 01", departamento="DEP1", 
            tipo_trabajador=1, donde="Taller", tiene_subfabricaciones=False, 
            tiempo_optimo=10.0, sub_partes=[], cantidad_en_kit=1, fabricacion_id=55
        )
        dto2 = CalculationProductDTO(
            codigo="P02", descripcion="", departamento="DEP1", 
            tipo_trabajador=1, donde="Taller", tiene_subfabricaciones=False, 
            tiempo_optimo=20.0, sub_partes=[], cantidad_en_kit=1, fabricacion_id=55
        )
        
        mock_product_controller.get_fabricacion_products_for_calculation.return_value = [dto1, dto2]
        
        result = controller.get_fabricacion_products_for_calculation(55)
        
        assert len(result) == 2
        assert result[0].codigo == "P01"
        assert result[1].codigo == "P02"
        assert result[1].descripcion == ""

    def test_get_fabricacion_products_for_calculation_empty(self, controller, mock_product_controller):
        """Verifica el manejo de lista vacía de productos."""
        mock_product_controller.get_fabricacion_products_for_calculation.return_value = []
        result = controller.get_fabricacion_products_for_calculation(1)
        assert result == []

    def test_get_fabricacion_products_for_calculation_exception(self, controller, mock_product_controller, mock_logger):
        """Verifica el manejo de excepciones en la delegación."""
        mock_product_controller.get_fabricacion_products_for_calculation.side_effect = Exception("Crash")
        
        result = controller.get_fabricacion_products_for_calculation(99)
        
        assert result == []
        mock_logger.error.assert_called()
        assert "Error obteniendo productos de fabricación 99" in mock_logger.error.call_args[0][0]
