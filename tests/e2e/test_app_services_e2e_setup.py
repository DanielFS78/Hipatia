"""Tests E2E de setup de la aplicación y modelo."""
import pytest
from unittest.mock import MagicMock, patch
from typing import Any, cast
from core.app_model import AppModel

pytestmark = pytest.mark.e2e


class TestAppE2ESetup:
    """
    Test E2E de Setup.
    Verifica que la aplicación arranca y el modelo se integra con la UI correctamente
    utilizando la nueva arquitectura de servicios.
    """

    @pytest.fixture
    def mock_db_manager(self
):

        """Proporciona un DatabaseManager simulado con repositorios básicos mockeados."""
        db = MagicMock(
            spec=[
                "get_all_products",
                "get_all_workers",
                "get_all_machines",
                "get_all_pilas_with_dates",
                "get_all_preprocesos",
            ]
        )
        db.get_all_products.return_value = []
        db.get_all_workers.return_value = []
        db.get_all_machines.return_value = []
        db.get_all_pilas_with_dates.return_value = []
        db.get_all_preprocesos.return_value = []
        return db

    @pytest.fixture
    def app_model(self, mock_db_manager):

        """Crea un AppModel con la BD simulada."""
        return AppModel(mock_db_manager)
#     @pytest.mark.skip("Verificar manualmente en entorno con display o en CI con Xvfb.")
    def test_main_window_startup_with_services(self, qapp, qtbot, app_model):

        """
        Verifica que MainView se inicializa sin errores con el nuevo AppModel
        y que los controladores tienen acceso a los datos (via facade
.
        Requiere qapp (offscreen) para evitar crash en entornos sin display.
        """
        # Import aquí para asegurar que qapp (offscreen) ya está activo
        from ui.main_window import MainView

        # Arrange
        window = MainView()
        qtbot.addWidget(window)
        controller = MagicMock(spec=["model"])
        controller.model = app_model

        # Act
        window.set_controller(controller)
        window.show()
        # Assert
        assert window.isVisible()
        assert cast(Any, window.controller).model is app_model

    def test_full_application_flow_simulation_mock(self, app_model):

        """
        Simula un flujo simple donde la UI llama al modelo (facade
y este
        usa los servicios. No requiere UI real.
        """
        # Arrange
        app_model.product_service.search_products = MagicMock(spec=[], return_value=[])
        # Act
        results = app_model.search_products("test")
        # Assert
        app_model.product_service.search_products.assert_called_with("test")
        assert results == []
