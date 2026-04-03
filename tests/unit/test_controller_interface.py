# -*- coding: utf-8 -*-
"""Tests unitarios para verificar que los controladores implementan IController."""
import pytest
from unittest.mock import MagicMock, create_autospec, ANY, patch

from core.interfaces.controller_interface import IController
from controllers.app_controller import AppController
from controllers.navigation_controller import NavigationController
from controllers.report_controller import ReportController
from core.app_model import AppModel
from core.services.product_service import ProductService
from core.services.worker_service import WorkerService
from core.services.pila_service import PilaService
from core.schedule_config import ScheduleConfig
from ui.main_window import MainView


@pytest.fixture
def mock_app_model():
    """Mock estricto de AppModel."""
    model = create_autospec(AppModel, instance=True)
    model.db = MagicMock(spec=[])  # evitar loose mock
    return model


@pytest.fixture
def mock_view():
    """Mock estricto de MainView."""
    return create_autospec(MainView, instance=True)


@pytest.fixture
def mock_schedule_config():
    """Mock estricto de ScheduleConfig."""
    return create_autospec(ScheduleConfig, instance=True)


@pytest.mark.unit
class TestControllerInterface:
    """Tests unitarios para verificar la implementación de IController."""

    def test_app_controller_implements_interface(self):
        """Verifica que AppController hereda de IController y tiene los métodos requeridos."""
        assert issubclass(AppController, IController)
        assert hasattr(AppController, 'initialize')
        assert hasattr(AppController, 'cleanup')
        assert hasattr(AppController, 'handle_error')

    def test_navigation_controller_implements_interface(self, mock_app_model, mock_view):
        """Verifica que NavigationController implementa IController y sus métodos son invocables."""
        mock_product_service = create_autospec(ProductService, instance=True)
        mock_logger = MagicMock(spec=["debug", "info", "warning", "error"])
        mock_app = MagicMock(spec=[])
        controller = NavigationController(
            mock_app, mock_view, mock_product_service, mock_logger
        )

        assert isinstance(controller, IController)

        with patch.object(controller, "initialize", wraps=controller.initialize) as init_spy, \
             patch.object(controller, "cleanup", wraps=controller.cleanup) as cleanup_spy, \
             patch.object(controller, "handle_error", wraps=controller.handle_error) as handle_spy:
            controller.initialize()
            controller.cleanup()
            assert init_spy.call_count == 1
            init_spy.assert_called_once_with()
            assert cleanup_spy.call_count == 1
            cleanup_spy.assert_called_once_with()

            # handle_error debe registrar el error sin propagar excepción
            controller.handle_error(Exception("error de prueba"), "contexto_test")
            assert handle_spy.call_count == 1
            handle_spy.assert_called_once_with(ANY, "contexto_test")
        # Verificar que el controlador procesó el error (no lanzó excepción)
        assert isinstance(controller, IController)

    def test_report_controller_implements_interface(
        self, mock_app_model, mock_view, mock_schedule_config
    ):
        """Verifica que ReportController implementa IController y sus métodos son invocables."""
        mock_worker_service = create_autospec(WorkerService, instance=True)
        mock_product_service = create_autospec(ProductService, instance=True)
        mock_pila_service = create_autospec(PilaService, instance=True)

        controller = ReportController(
            mock_app_model,
            mock_view,
            mock_worker_service,
            mock_product_service,
            mock_pila_service,
            mock_schedule_config,
        )

        assert isinstance(controller, IController)

        with patch.object(controller, "initialize", wraps=controller.initialize) as init_spy, \
             patch.object(controller, "cleanup", wraps=controller.cleanup) as cleanup_spy, \
             patch.object(controller, "handle_error", wraps=controller.handle_error) as handle_spy:
            controller.initialize()
            controller.cleanup()
            assert init_spy.call_count == 1
            init_spy.assert_called_once_with()
            assert cleanup_spy.call_count == 1
            cleanup_spy.assert_called_once_with()

            controller.handle_error(Exception("error de prueba"), "contexto_test")
            assert handle_spy.call_count == 1
            handle_spy.assert_called_once_with(ANY, "contexto_test")
        assert isinstance(controller, IController)
