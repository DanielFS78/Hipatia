"""
Pruebas Unitarias para WorkerTaskManager.

Este módulo verifica la asignación de tareas a trabajadores y la búsqueda
de productos dentro del contexto del gestor de tareas.
"""
import pytest
from unittest.mock import MagicMock, ANY, patch
from controllers.worker.task_manager import WorkerTaskManager
from controllers.worker.protocols import IWorkerView, IWorkerService, IWorkerModel, WorkerControllerProtocol
from core.security.access_control import set_security_service
from core.security.security_service import SecurityService

@pytest.mark.unit
class TestWorkerTaskManager:
    """Suite de pruebas para el gestor de asignación de tareas."""

    @pytest.fixture(autouse=True)
    def setup_security(self):
        """Configura un mock de seguridad para las pruebas de tareas."""
        mock_security = MagicMock(spec=SecurityService)
        mock_security.has_permission.return_value = True
        set_security_service(mock_security)
        yield
        set_security_service(None)

    @pytest.fixture
    def mock_view(self):
        """Crea un mock de la interfaz de vista con estructura anidada."""
        view = MagicMock(spec=["pages", "show_message"])
        # Mock de la estructura anidada
        gestion_datos = MagicMock(spec=["trabajadores_tab"])
        workers_tab = MagicMock(
            spec=[
                "update_product_search_results",
                "get_assignment_data",
                "form_widgets",
                "workers_list",
            ]
        )
        workers_tab.workers_list = MagicMock(spec=["currentItem"])
        workers_tab.form_widgets = {
            "product_search": MagicMock(spec=["clear"]),
            "quantity_spinbox": MagicMock(spec=["setValue"]),
        }
        gestion_datos.trabajadores_tab = workers_tab
        view.pages = {"gestion_datos": gestion_datos}
        return view

    @pytest.fixture
    def mock_service(self):
        """Crea un mock del servicio de trabajadores."""
        return MagicMock(spec=IWorkerService)

    @pytest.fixture
    def mock_model(self):
        """Crea un mock del modelo de la aplicación."""
        model = MagicMock(spec=IWorkerModel)
        model.product_service = MagicMock(spec=["search_products"])
        model.worker_service = MagicMock(spec=[])
        return model

    @pytest.fixture
    def mock_controller(self):
        """Crea un mock del controlador principal de trabajadores."""
        controller = MagicMock(spec=WorkerControllerProtocol)
        controller.management_manager = MagicMock(spec=["_on_worker_selected_in_list"])
        return controller

    @pytest.fixture
    def mock_app(self):
        """Crea un mock de la aplicación principal."""
        return MagicMock(spec=[])

    @pytest.fixture
    def manager(self, mock_app, mock_model, mock_view, mock_service, mock_controller):
        """Instancia WorkerTaskManager con sus dependencias."""
        return WorkerTaskManager(app=mock_app, model=mock_model, view=mock_view, worker_service=mock_service, controller_ref=mock_controller)

    def test_search_products(self, manager, mock_view, mock_model):
        """Prueba que el cambio en la búsqueda de productos actualiza los resultados."""
        # Configurar data
        mock_model.product_service.search_products.return_value = [{'codigo': 'P1'}]
        
        # Ejecutar (con texto suficientemente largo según constants)
        manager._on_worker_product_search_changed("PRODUCTO_LARGO")
        
        # Verificar
        mock_model.product_service.search_products.assert_called_once_with("PRODUCTO_LARGO")
        # Verificar en el tab anidado
        mock_view.pages["gestion_datos"].trabajadores_tab.update_product_search_results.assert_called_once_with([{'codigo': 'P1'}])

    def test_on_assign_task_success(self, manager, mock_view, mock_service, mock_controller):
        """Prueba la asignación exitosa de una tarea a un trabajador."""
        # Configurar mock de datos de la UI
        tab = mock_view.pages["gestion_datos"].trabajadores_tab
        tab.get_assignment_data.return_value = {
            "worker_id": 1,
            "product_code": "P1",
            "quantity": 10
        }
        # Asegurar que workers_list.currentItem() devuelva algo para el refresh final
        tab.workers_list.currentItem.return_value = MagicMock(spec=[])
        
        mock_service.assign_task_to_worker.return_value = (True, "OK")
        
        # Ejecutar
        manager._on_assign_task_to_worker_clicked()
        
        # Verificar
        mock_service.assign_task_to_worker.assert_called_once_with(1, "P1", 10)
        mock_view.show_message.assert_called_with("Éxito", ANY, "info")
        # Verificar refresh
        mock_controller.management_manager._on_worker_selected_in_list.assert_called_once_with(ANY)
