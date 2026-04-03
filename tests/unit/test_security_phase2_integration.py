# -*- coding: utf-8 -*-
"""Tests de integración Fase 2: auditoría y seguridad en controladores.

Verifica que creación de producto/trabajador genera log de auditoría y que
el controlador rechaza contraseñas débiles. Decisión de mocking: app/session/view
completos por integración.
"""
import pytest
from unittest.mock import MagicMock, patch, ANY

from core.facades.product_facade import ProductFacade
from core.facades.planning_facade import PlanningFacade
from controllers.worker.controller import WorkerController
from core.security.password_service import PasswordService
from core.dtos import WorkerFormDataDTO

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_app_integration():
    """Mock completo de la app para tests de integración de controladores."""
    app = MagicMock(spec=["session_controller", "model", "view", "db", "ui_controller"])
    app.session_controller = MagicMock(spec=["current_user", "audit_logger"])
    app.session_controller.current_user = MagicMock(id=1, username="admin_audit", role="Responsable")
    app.session_controller.audit_logger = MagicMock(spec=["log"])
    app.model = MagicMock(
        spec=[
            "product_service",
            "product_facade",
            "planning_facade",
            "worker_service",
            "fabricacion_service",
            "material_service",
        ]
    )
    app.model.product_service = MagicMock(spec=["add_product", "get_product_by_code"])
    app.model.pila_service = MagicMock(spec=["get_data_for_calculation", "get_data_for_calculation_from_session"])
    app.model.product_facade = ProductFacade(app.model.product_service)
    app.model.planning_facade = PlanningFacade(app.model.pila_service)
    app.model.worker_service = MagicMock(spec=["add_worker"])
    app.model.fabricacion_service = MagicMock(spec=[])
    app.model.material_service = MagicMock(spec=[])
    app.model.machine_service = MagicMock(spec=["get_all_machines"])
    app.model.workers_changed_signal = MagicMock(spec=["connect"])
    app.view = MagicMock(spec=["pages", "get_page", "show_message", "get_products_tab", "show_confirmation_dialog"])
    app.view.pages = {}
    app.db = MagicMock(spec=[])
    app.ui_controller = MagicMock(spec=["on_data_changed"])
    return app

class TestAuditIntegration:
    """Tests de integración para verificar que los controladores llaman al AuditLogger."""

    def test_product_creation_audited(self, mock_app_integration):
        """Verifica que crear un producto genera un log de auditoría."""
        # 1. Mockear dependencias de UI ANTES de importar ProductController
        # Esto previene errores por QWidgets no inicializados o imports circulares
        with patch.dict('sys.modules', {
            'ui.dialogs': MagicMock(spec=[]),
            'ui.widgets': MagicMock(spec=[]),
            'ui.widgets.GestionDatosWidget': MagicMock(spec=[]),
        }):
            # Importar LOCALMENTE dentro del parche
            from controllers.product_controller_v2 import ProductController

            state = MagicMock(spec=["active_dialogs"])
            state.active_dialogs = {}
            controller = ProductController(
                app_shell=mock_app_integration,
                db=mock_app_integration.db,
                product_model=mock_app_integration.model,
                view=mock_app_integration.view,
                product_facade=mock_app_integration.model.product_facade,
                fabricacion_service=mock_app_integration.model.fabricacion_service,
                planning_facade=mock_app_integration.model.planning_facade,
                material_service=mock_app_integration.model.material_service,
                machine_service=mock_app_integration.model.machine_service,
                state=state,
            )

            # 2. Configurar mocks para la creación en el SERVICIO
            mock_app_integration.model.product_service.add_product.return_value = "SUCCESS"

            # Mockear la página de productos (dentro de gestion_datos)
            mock_add_page = MagicMock(spec=["get_product_form_data", "clear_all", "display_product_form"])
            mock_data = {
                "codigo": "PROD-AUDIT-01",
                "descripcion": "Producto Auditado",
                "departamento": "Montaje",
                "tipo_trabajador": 2,
                "tiene_subfabricaciones": False,
                "tiempo_optimo": 60.0,
                "sub_partes": [],
            }
            mock_add_page.get_product_form_data.return_value = mock_data

            # Sincronizar con la estructura real de MainView
            mock_app_integration.view.pages = {"gestion_datos": MagicMock(productos_tab=mock_add_page)}
            mock_app_integration.view.get_page.return_value = mock_app_integration.view.pages["gestion_datos"]
            mock_app_integration.view.get_products_tab.return_value = mock_add_page
            mock_app_integration.model.product_service.get_product_by_code.return_value = None

            # 3. Ejecutar la acción real
            with patch("controllers.product.product_manager.ValidatorService") as mock_validator:
                # Hacer que todo sea válido
                mock_res = MagicMock(spec=["is_valid"])
                mock_res.is_valid = True
                mock_validator.validate_product_code.return_value = mock_res
                mock_validator.validate_product_description.return_value = mock_res
                mock_validator.validate_positive_number.return_value = mock_res
                controller.product_manager._on_update_product("")

            # 4. Verificar log
            assert mock_app_integration.model.product_service.add_product.call_count >= 1
            mock_app_integration.model.product_service.add_product.assert_called()

            assert mock_app_integration.session_controller.audit_logger.log.call_count >= 1
            mock_app_integration.session_controller.audit_logger.log.assert_called()
            call_args = mock_app_integration.session_controller.audit_logger.log.call_args[1]
            assert call_args['action'] == 'CREATE'
            assert call_args['entity_type'] == 'PRODUCT'
            assert "PROD-AUDIT-01" in call_args['description']

    def test_worker_creation_audited(self, mock_app_integration):
        """Verifica que crear un trabajador genera un log de auditoría."""
        controller = WorkerController(
            app_controller=mock_app_integration,
            view=mock_app_integration.view,
            worker_service=mock_app_integration.model.worker_service,
            product_service=mock_app_integration.model.product_service,
            fabricacion_service=mock_app_integration.model.fabricacion_service,
            workers_changed_signal=mock_app_integration.model.workers_changed_signal,
        )
        
        # Setup mocks en el SERVICIO
        mock_app_integration.model.worker_service.add_worker.return_value = True
        mock_workers_page = MagicMock(spec=["get_form_data", "current_worker_id"])
        mock_workers_page.get_form_data.return_value = WorkerFormDataDTO(
            nombre_completo="Audit Worker",
            username="worker_audit",
            password="SecurePass1",
            confirm_password="SecurePass1",
            role="Trabajador",
            tipo_trabajador=1,
            activo=True,
            notas=""
        )
        mock_workers_page.current_worker_id = None
        mock_app_integration.view.pages = {"gestion_datos": MagicMock(spec=["trabajadores_tab"])}
        mock_app_integration.view.pages["gestion_datos"].trabajadores_tab = mock_workers_page
        
        # Ejecutar acción
        with patch('controllers.worker.management_manager.isinstance', return_value=True), \
             patch.object(controller, 'update_workers_view', create=True):
            controller.management_manager._on_save_worker_clicked()
            
        assert mock_app_integration.session_controller.audit_logger.log.call_count >= 1
        mock_app_integration.session_controller.audit_logger.log.assert_called()
        call_args = mock_app_integration.session_controller.audit_logger.log.call_args[1]
        assert call_args['action'] == 'CREATE'
        assert call_args['entity_type'] == 'WORKER'
        assert "Audit Worker" in call_args['description']

    def test_password_complexity_enforcement_in_controller(self, mock_app_integration):
        """Verifica que el controlador rechaza contraseñas débiles antes de llamar al modelo."""
        controller = WorkerController(
            app_controller=mock_app_integration,
            view=mock_app_integration.view,
            worker_service=mock_app_integration.model.worker_service,
            product_service=mock_app_integration.model.product_service,
            fabricacion_service=mock_app_integration.model.fabricacion_service,
            workers_changed_signal=mock_app_integration.model.workers_changed_signal,
        )
        
        # Setup mocks con contraseña débil
        mock_workers_page = MagicMock(spec=["get_form_data", "current_worker_id"])
        mock_workers_page.get_form_data.return_value = WorkerFormDataDTO(
            nombre_completo="Weak Worker",
            username="weakp",
            password="123", # Débil
            confirm_password="123",
            role="Trabajador",
            tipo_trabajador=1,
            activo=True,
            notas=""
        )
        mock_workers_page.current_worker_id = None
        mock_app_integration.view.pages = {"gestion_datos": MagicMock(spec=["trabajadores_tab"])}
        mock_app_integration.view.pages["gestion_datos"].trabajadores_tab = mock_workers_page
        
        # Ejecutar acción
        with patch('controllers.worker.management_manager.isinstance', return_value=True):
            controller.management_manager._on_save_worker_clicked()
            
        assert mock_app_integration.model.worker_service.add_worker.call_count == 0
        mock_app_integration.model.worker_service.add_worker.assert_not_called()
        assert mock_app_integration.view.show_message.call_count >= 1
        mock_app_integration.view.show_message.assert_called_with("Contraseña Débil", ANY, "warning")


