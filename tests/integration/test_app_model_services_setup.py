# -*- coding: utf-8 -*-
"""Tests de integración de setup de AppModel: inicialización de servicios y señales.

Verifica que AppModel crea ProductService, PilaService, FabricacionService, ReportService
y que las señales de los servicios están puenteadas al AppModel.
"""
import pytest
from unittest.mock import MagicMock
from core.app_model import AppModel
from core.services.product_service import ProductService
from core.services.pila_service import PilaService
from core.services.fabricacion_service import FabricacionService
from core.services.report_service import ReportService

pytestmark = pytest.mark.integration


class TestAppModelServiceIntegration:
    """
    Test especifico de Integración de Setup para AppModel.
    Verifica que AppModel inicializa y conecta correctamente los servicios.
    """
    
    @pytest.fixture
    def db_manager(self):
        return MagicMock(spec=[])

    def test_app_model_initializes_services(self, db_manager):
        """Verifica que los servicios se crean y asignan en __init__."""
        app_model = AppModel(db_manager)
        
        assert isinstance(app_model.product_service, ProductService)
        assert isinstance(app_model.pila_service, PilaService)
        assert isinstance(app_model.fabricacion_service, FabricacionService)
        assert isinstance(app_model.report_service, ReportService)
        
        # Verificar que comparten el mismo db_manager
        assert app_model.product_service.db is db_manager
        assert app_model.pila_service.db is db_manager
        assert app_model.fabricacion_service.db is db_manager
        assert app_model.report_service.db is db_manager

    def test_service_signals_connected(self, db_manager):
        """Verifica que las señales de los servicios están puenteadas a AppModel."""
        app_model = AppModel(db_manager)
        
        # Mock signal emits from services and verify AppModel signal emits
        mock_product_signal = MagicMock(spec=[])
        app_model.product_added_signal.connect(mock_product_signal)
        app_model.product_service.product_added_signal.emit("TEST_CODE")
        assert mock_product_signal.call_count >= 1
        mock_product_signal.assert_called_with("TEST_CODE")
        
        mock_pila_signal = MagicMock(spec=[])
        app_model.pilas_changed_signal.connect(mock_pila_signal)
        app_model.pila_service.pilas_changed_signal.emit("Title", "Msg")
        assert mock_pila_signal.call_count >= 1
        mock_pila_signal.assert_called_with("Title", "Msg")
