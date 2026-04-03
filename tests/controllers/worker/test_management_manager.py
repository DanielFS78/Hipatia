"""
Pruebas Unitarias para WorkerManagementManager.

Este módulo verifica la gestión de los datos de los trabajadores, incluyendo
la actualización de la vista, selección de operarios y adición de nuevos registros.
"""
import pytest
from unittest.mock import MagicMock, ANY, patch
from controllers.worker.management_manager import WorkerManagementManager
from controllers.worker.protocols import IWorkerView, IWorkerService
from core.dtos import WorkerFormDataDTO
from core.security.access_control import set_security_service
from core.security.security_service import SecurityService

@pytest.mark.unit
class TestWorkerManagementManager:
    """Suite de pruebas para el gestor de personal."""

    @pytest.fixture(autouse=True)
    def setup_security(self):
        """Configura un mock de seguridad para las pruebas de gestión."""
        mock_security = MagicMock(spec=SecurityService)
        mock_security.has_permission.return_value = True
        set_security_service(mock_security)
        yield
        set_security_service(None)

    @pytest.fixture
    def mock_view(self):
        """Crea un mock de la interfaz de vista con páginas anidadas."""
        view = MagicMock(spec=IWorkerView)
        # Mock de la estructura anidada de páginas
        gestion_datos = MagicMock(spec=["trabajadores_tab"])
        gestion_datos.trabajadores_tab = MagicMock(
            spec=[
                "populate_list",
                "clear_details_area",
                "show_worker_details",
                "setup_of_completer",
                "current_worker_id",
                "get_form_data",
            ]
        )
        view.pages = {"gestion_datos": gestion_datos}
        return view

    @pytest.fixture
    def mock_service(self):
        """Crea un mock del servicio de trabajadores."""
        return MagicMock(spec=IWorkerService)

    @pytest.fixture
    def mock_app(self):
        """Crea un mock de la aplicación principal."""
        app = MagicMock(spec=["current_user"])
        user = MagicMock(spec=["role"])
        user.role = "Responsable"
        app.current_user = user
        return app

    @pytest.fixture
    def manager(self, mock_app, mock_view, mock_service):
        """Instancia WorkerManagementManager con sus dependencias."""
        return WorkerManagementManager(
            app=mock_app,
            view=mock_view,
            worker_service=mock_service,
            fabricacion_service=None,
        )

    def test_update_workers_view(self, manager, mock_view, mock_service):
        """Prueba que el refresco de la vista carga todos los trabajadores correctamente."""
        # Configurar mock
        mock_service.get_all_workers.return_value = [{'id': 1, 'nombre_completo': 'Juan'}]
        
        # Ejecutar
        manager.update_workers_view()
        
        # Verificar
        mock_service.get_all_workers.assert_called_once_with()
        # Verificar que se llamó a populate_list en el tab correspondiente
        mock_view.pages["gestion_datos"].trabajadores_tab.populate_list.assert_called_once_with([{'id': 1, 'nombre_completo': 'Juan'}])

    def test_on_worker_selected_none(self, manager, mock_view, mock_service):
        """Prueba que la selección de un elemento vacío limpia el área de detalles."""
        # Configurar mock del item
        mock_item = MagicMock(spec=["data"])
        mock_item.data.return_value = 10
        mock_service.get_worker_details.return_value = None
        
        # Ejecutar (usando el nombre correcto de la función)
        manager._on_worker_selected_in_list(mock_item)
        
        # Verificar limpieza
        mock_view.pages["gestion_datos"].trabajadores_tab.clear_details_area.assert_called_once_with()

    def test_on_worker_selected_valid(self, manager, mock_view, mock_service):
        """Prueba que la selección de un trabajador válido muestra sus detalles correctamente."""
        # Configurar mock
        mock_item = MagicMock(spec=["data"])
        mock_item.data.return_value = 10
        worker_data = {'id': 10, 'nombre_completo': 'Juan', 'tipo_trabajador': 1}
        mock_service.get_worker_details.return_value = worker_data
        
        # Ejecutar
        manager._on_worker_selected_in_list(mock_item)
        
        # Verificar
        mock_view.pages["gestion_datos"].trabajadores_tab.show_worker_details.assert_called_once_with(worker_data)

    def test_add_worker_success(self, manager, mock_view, mock_service):
        """Prueba la adición exitosa de un nuevo trabajador."""
        # Configurar tab
        tab = mock_view.pages["gestion_datos"].trabajadores_tab
        tab.current_worker_id = None
        tab.get_form_data.return_value = WorkerFormDataDTO(
            nombre_completo='Nuevo',
            notas='Test',
            tipo_trabajador=1,
            activo=True,
            username=None,
            password=None,
            confirm_password=None,
            role=None
        )
        
        mock_service.add_worker.return_value = True
        
        # Ejecutar
        manager._on_save_worker_clicked()
        
        # Verificar
        mock_service.add_worker.assert_called_once_with("Nuevo", "Test", 1, ANY, ANY, ANY)
        mock_view.show_message.assert_called_with("Éxito", ANY, "info")
