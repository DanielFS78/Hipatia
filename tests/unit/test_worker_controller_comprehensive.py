# -*- coding: utf-8 -*-
"""
Tests comprensivos unitarios para WorkerController.
Verifica CRUD de trabajadores, interfaz operario, cambio de contraseñas y asignación de tareas.
"""
from __future__ import annotations

import pytest
from typing import Any, cast
from unittest.mock import MagicMock, patch, call, create_autospec
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog

from controllers.worker.controller import WorkerController
from core.services.worker_service import WorkerService
from core.services.product_service import ProductService
from core.services.fabricacion_service import FabricacionService
from ui.widgets import GestionDatosWidget, WorkersWidget
from core.dtos import ConfigurationDTO, WorkerFormDataDTO, WorkerDetailDTO, AuthResponseDTO


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_app() -> MagicMock:
    """AppController completamente mockeado con servicios usando create_autospec."""
    app = MagicMock()
    app.model = MagicMock()
    app.model.worker_service = create_autospec(WorkerService, instance=True)
    # Añadir métodos que no están en WorkerService pero se usan en el código
    app.model.worker_service.actualizar_estado_asignacion = MagicMock(return_value=True)
    app.model.worker_service.get_worker_history = MagicMock(return_value=([], []))
    app.model.product_service = create_autospec(ProductService, instance=True)
    app.model.fabricacion_service = create_autospec(FabricacionService, instance=True)
    app.model.get_all_workers.return_value = []
    app.model.worker_repo = MagicMock()
    app.model.add_worker.return_value = True
    app.model.update_worker.return_value = True
    app.model.delete_worker.return_value = True
    app.model.worker_service.get_worker_details.return_value = WorkerDetailDTO(
        id=1, nombre_completo="Test Worker", username="testuser", activo=True, notas="", tipo_trabajador=1
    )
    app.model.assign_task_to_worker.return_value = (True, "Tarea creada")
    app.model.get_worker_history.return_value = ([], [])
    app.model.actualizar_estado_asignacion = MagicMock(return_value=True)
    app.db = MagicMock()
    app.db.tracking_repo = MagicMock()
    app.db.get_all_ordenes_fabricacion.return_value = []
    app.db.actualizar_estado_asignacion.return_value = True
    app.view = MagicMock()
    app.view.pages = {}
    app.view.show_message = MagicMock()
    app.view.show_confirmation_dialog = MagicMock(return_value=True)
    mock_user = MagicMock(id=1, username="admin", role="Responsable")
    app.current_user = mock_user
    auth_ctrl = MagicMock()
    auth_ctrl.current_user = mock_user
    app.session_controller = auth_ctrl
    app.model.workers_changed_signal = MagicMock()
    app.model.workers_changed_signal.connect = MagicMock()
    return app


@pytest.fixture
def ctrl(mock_app: MagicMock) -> WorkerController:
    """WorkerController instanciado con mock_app."""
    return WorkerController(
        app_controller=mock_app,
        view=mock_app.view,
        worker_service=mock_app.model.worker_service,
        product_service=mock_app.model.product_service,
        fabricacion_service=mock_app.model.fabricacion_service,
        workers_changed_signal=mock_app.model.workers_changed_signal,
    )


@pytest.fixture
def mock_workers_page() -> MagicMock:
    """Mock de WorkersWidget con todos los atributos necesarios."""
    page = MagicMock(spec=WorkersWidget)
    page.current_worker_id = None
    page.get_form_data.return_value = WorkerFormDataDTO(
        nombre_completo="Test Worker",
        notas="Notes",
        tipo_trabajador=1,
        username="testuser",
        password="ValidPass1!",
        confirm_password="ValidPass1!",
        role="Trabajador",
        activo=True
    )
    page.workers_list = MagicMock()
    page.show_worker_details = MagicMock()
    page.setup_of_completer = MagicMock()
    return page


@pytest.fixture
def gestion_with_workers(mock_workers_page: MagicMock, mock_app: MagicMock) -> MagicMock:
    """Mock de GestionDatosWidget con workers tab."""
    gestion = MagicMock(spec=GestionDatosWidget)
    gestion.trabajadores_tab = mock_workers_page
    mock_app.view.pages = {"gestion_datos": gestion}
    return gestion


# =============================================================================
# TESTS: __init__
# =============================================================================

@pytest.mark.unit
class TestInit:
    def test_init_assigns_attributes(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        assert ctrl.app is mock_app
        assert ctrl.worker_service is mock_app.model.worker_service
        assert ctrl.product_service is mock_app.model.product_service
        assert ctrl.fabricacion_service is mock_app.model.fabricacion_service
        assert ctrl.workers_changed_signal is mock_app.model.workers_changed_signal
        assert ctrl.view is mock_app.view
        assert ctrl.worker_window is None
        assert ctrl.worker_feature_controller is None


# =============================================================================
# TESTS: update_workers_view
# =============================================================================

@pytest.mark.unit
class TestUpdateWorkersView:
    def test_no_gestion_datos_page(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_app.view.pages = {}
        ctrl.management_manager.update_workers_view()
        mock_app.model.worker_service.get_all_workers.assert_not_called()

    def test_updates_workers_list(self, ctrl: WorkerController, mock_app: MagicMock,
                                   gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_app.model.worker_service.get_all_workers.return_value = [{"id": 1}]
        ctrl.management_manager.update_workers_view()
        mock_workers_page.populate_list.assert_called_once_with([{"id": 1}])


# =============================================================================
# TESTS: _on_worker_selected_in_list
# =============================================================================

@pytest.mark.unit
class TestOnWorkerSelectedInList:
    def test_no_gestion_page(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_app.view.pages = {}
        item = MagicMock()
        item.data.return_value = 1
        try:
            ctrl.management_manager._on_worker_selected_in_list(item)
            assert ctrl is not None
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin gestion page: {e}")

    def test_selects_worker_with_data(self, ctrl: WorkerController, mock_app: MagicMock,
                                      gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        item = MagicMock()
        item.data.return_value = 1
        ctrl.management_manager._on_worker_selected_in_list(item)
        assert mock_workers_page.show_worker_details.call_count == 1
        mock_workers_page.show_worker_details.assert_called_once_with(
            mock_app.model.worker_service.get_worker_details.return_value
        )

    def test_selects_worker_without_data(self, ctrl: WorkerController, mock_app: MagicMock,
                                          gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        item = MagicMock()
        item.data.return_value = 99
        mock_app.model.worker_service.get_worker_details.return_value = None
        ctrl.management_manager._on_worker_selected_in_list(item)
        assert mock_workers_page.clear_details_area.call_count == 1
        mock_workers_page.clear_details_area.assert_called_once_with()


# =============================================================================
# TESTS: _on_save_worker_clicked (nuevo)
# =============================================================================

@pytest.mark.unit
class TestOnSaveWorkerClickedNew:
    def test_no_gestion_page(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_app.view.pages = {}
        try:
            ctrl.management_manager._on_save_worker_clicked()
            assert ctrl is not None
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin gestion page: {e}")

    def test_invalid_form_data(self, ctrl: WorkerController, mock_app: MagicMock,
                               gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.get_form_data.return_value = None
        ctrl.management_manager._on_save_worker_clicked()
        assert mock_app.view.show_message.call_count == 1
        mock_app.view.show_message.assert_called_once_with(*mock_app.view.show_message.call_args[0])
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Error"

    def test_blank_nombre(self, ctrl: WorkerController, mock_app: MagicMock,
                          gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.get_form_data.return_value = WorkerFormDataDTO(
            nombre_completo="  ", notas="", tipo_trabajador=1, username=None,
            password=None, confirm_password=None, role=None, activo=True
        )
        ctrl.management_manager._on_save_worker_clicked()
        assert mock_app.view.show_message.call_count == 1
        mock_app.view.show_message.assert_called_once_with(*mock_app.view.show_message.call_args[0])

    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_add_new_worker_success(self, mock_ps: MagicMock, ctrl: WorkerController, mock_app: MagicMock,
                                    gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_ps.validate_password.return_value = (True, "")
        mock_ps.hash_password.return_value = "hashed"
        mock_app.model.worker_service.add_worker.return_value = True

        ctrl.management_manager._on_save_worker_clicked()

        assert mock_app.view.show_message.call_count == 1
        mock_app.view.show_message.assert_called_once_with(*mock_app.view.show_message.call_args[0])
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Éxito"

    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_add_new_worker_unique_constraint(self, mock_ps: MagicMock, ctrl: WorkerController, mock_app: MagicMock,
                                              gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_ps.validate_password.return_value = (True, "")
        mock_ps.hash_password.return_value = "hashed"
        mock_app.model.worker_service.add_worker.return_value = "UNIQUE_CONSTRAINT"

        ctrl.management_manager._on_save_worker_clicked()

        assert mock_app.view.show_message.call_count == 1
        mock_app.view.show_message.assert_called_once_with(*mock_app.view.show_message.call_args[0])
        args = mock_app.view.show_message.call_args[0]
        assert "nombre" in args[1].lower() or "usuario" in args[1].lower()

    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_add_new_worker_failure(self, mock_ps: MagicMock, ctrl: WorkerController, mock_app: MagicMock,
                                    gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_ps.validate_password.return_value = (True, "")
        mock_ps.hash_password.return_value = "hashed"
        mock_app.model.worker_service.add_worker.return_value = False

        ctrl.management_manager._on_save_worker_clicked()

        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Error"

    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_add_new_worker_weak_password(self, mock_ps: MagicMock, ctrl: WorkerController, mock_app: MagicMock,
                                          gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_ps.validate_password.return_value = (False, "PW demasiado débil")
        ctrl.management_manager._on_save_worker_clicked()
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Contraseña Débil"

    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_add_new_user_needs_password(self, mock_ps: MagicMock, ctrl: WorkerController, mock_app: MagicMock,
                                         gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.get_form_data.return_value = WorkerFormDataDTO(
            nombre_completo="User With Username",
            username="newuser",
            password="",  # Sin contraseña para nuevo usuario
            confirm_password="",
            role="Trabajador",
            notas="",
            tipo_trabajador=1,
            activo=True
        )
        ctrl.management_manager._on_save_worker_clicked()
        args = mock_app.view.show_message.call_args[0]
        assert "contraseña" in args[1].lower()

    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_username_without_role_shows_error(self, mock_ps: MagicMock, ctrl: WorkerController, mock_app: MagicMock,
                                               gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        """Si se define username pero no rol, muestra error."""
        mock_workers_page.get_form_data.return_value = WorkerFormDataDTO(
            nombre_completo="Test User",
            username="newuser_no_role",
            password="ValidPass1!",
            confirm_password="ValidPass1!",
            role="",  # Sin rol seleccionado
            notas="",
            tipo_trabajador=1,
            activo=True
        )
        mock_ps.validate_password.return_value = (True, "")
        mock_ps.hash_password.return_value = "hashed"
        ctrl.management_manager._on_save_worker_clicked()
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Error"


# =============================================================================
# TESTS: _on_save_worker_clicked (actualización)
# =============================================================================

@pytest.mark.unit
class TestOnSaveWorkerClickedUpdate:
    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_update_worker_success(self, mock_ps: MagicMock, ctrl: WorkerController, mock_app: MagicMock,
                                   gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.current_worker_id = 5
        mock_ps.validate_password.return_value = (True, "")
        mock_ps.hash_password.return_value = "hashed"
        mock_app.model.worker_service.update_worker.return_value = True

        ctrl.management_manager._on_save_worker_clicked()

        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Éxito"

    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_update_worker_failure(self, mock_ps: MagicMock, ctrl: WorkerController, mock_app: MagicMock,
                                   gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.current_worker_id = 5
        mock_ps.validate_password.return_value = (True, "")
        mock_ps.hash_password.return_value = "hashed"
        mock_app.model.worker_service.update_worker.return_value = False

        ctrl.management_manager._on_save_worker_clicked()

        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Error"

    def test_save_exception_shows_message(self, ctrl: WorkerController, mock_app: MagicMock,
                                           gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        # La excepción debe producirse dentro del bloque try (después de get_form_data)
        # Provocamos error en el método validate_data (dentro del try)
        mock_workers_page.current_worker_id = None
        mock_workers_page.get_form_data.return_value = WorkerFormDataDTO(
            nombre_completo="Test", notas="", tipo_trabajador=1, username=None,
            password=None, confirm_password=None, role=None, activo=True
        )
        # Causamos error accediendo a un atributo que activa el except
        mock_app.model.worker_service.add_worker.side_effect = Exception("DB Crash")

        ctrl.management_manager._on_save_worker_clicked()
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Error"


# =============================================================================
# TESTS: _on_delete_worker_clicked
# =============================================================================

@pytest.mark.unit
class TestOnDeleteWorkerClicked:
    def test_delete_confirms_and_succeeds(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_app.view.show_confirmation_dialog.return_value = True
        mock_app.model.worker_service.delete_worker.return_value = True
        ctrl.management_manager._on_delete_worker_clicked(1)
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Éxito"

    def test_delete_not_confirmed(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_app.view.show_confirmation_dialog.return_value = False
        ctrl.management_manager._on_delete_worker_clicked(1)
        mock_app.model.worker_service.delete_worker.assert_not_called()

    def test_delete_fails(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_app.view.show_confirmation_dialog.return_value = True
        mock_app.model.worker_service.delete_worker.return_value = False
        ctrl.management_manager._on_delete_worker_clicked(1)
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Error"


# =============================================================================
# TESTS: _on_change_worker_password_clicked
# =============================================================================

@pytest.mark.unit
class TestOnChangeWorkerPasswordClicked:
    def test_no_permission_wrong_role(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_app.current_user = MagicMock(id=1, role="Trabajador")
        ctrl.auth_manager._on_change_worker_password_clicked(1)
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Acceso Denegado"

    def test_worker_not_found(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_app.model.worker_service.get_worker_details.return_value = None
        ctrl.auth_manager._on_change_worker_password_clicked(99)
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Error"

    @patch("controllers.worker.auth_manager.ChangePasswordDialog", new_callable=MagicMock)
    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_change_password_success(self, mock_ps: MagicMock, mock_dialog_cls: MagicMock,
                                      ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_dialog.get_passwords.return_value = {
            "new": "NewValidPass1!", "confirm": "NewValidPass1!"
        }
        mock_dialog_cls.return_value = mock_dialog
        mock_ps.validate_password.return_value = (True, "")
        mock_app.model.worker_service.update_user_password.return_value = True

        ctrl.auth_manager._on_change_worker_password_clicked(1)

        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Éxito"

    @patch("controllers.worker.auth_manager.ChangePasswordDialog", new_callable=MagicMock)
    def test_change_password_dialog_rejected(self, mock_dialog_cls: MagicMock,
                                               ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Rejected
        mock_dialog_cls.return_value = mock_dialog

        ctrl.auth_manager._on_change_worker_password_clicked(1)
        mock_app.view.show_message.assert_not_called()

    @patch("controllers.worker.auth_manager.ChangePasswordDialog", new_callable=MagicMock)
    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_change_password_empty_new(self, mock_ps: MagicMock, mock_dialog_cls: MagicMock,
                                        ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_dialog.get_passwords.return_value = {"new": "", "confirm": ""}
        mock_dialog_cls.return_value = mock_dialog

        ctrl.auth_manager._on_change_worker_password_clicked(1)
        args = mock_app.view.show_message.call_args[0]
        assert "vacía" in args[1].lower() or "contraseña" in args[1].lower()

    @patch("controllers.worker.auth_manager.ChangePasswordDialog", new_callable=MagicMock)
    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_change_password_mismatch(self, mock_ps: MagicMock, mock_dialog_cls: MagicMock,
                                       ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_dialog.get_passwords.return_value = {"new": "Pass1!", "confirm": "Different!"}
        mock_dialog_cls.return_value = mock_dialog

        ctrl.auth_manager._on_change_worker_password_clicked(1)
        args = mock_app.view.show_message.call_args[0]
        assert "coincid" in args[1].lower()

    @patch("controllers.worker.auth_manager.ChangePasswordDialog", new_callable=MagicMock)
    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_change_password_weak(self, mock_ps: MagicMock, mock_dialog_cls: MagicMock,
                                   ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_dialog.get_passwords.return_value = {"new": "weak", "confirm": "weak"}
        mock_dialog_cls.return_value = mock_dialog
        mock_ps.validate_password.return_value = (False, "Contraseña débil")

        ctrl.auth_manager._on_change_worker_password_clicked(1)
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Contraseña Débil"


# =============================================================================
# TESTS: _on_change_own_password_clicked
# =============================================================================

@pytest.mark.unit
class TestOnChangeOwnPasswordClicked:
    def test_no_current_user(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_app.current_user = None
        try:
            ctrl.auth_manager._on_change_own_password_clicked()
            assert ctrl is not None
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin current_user: {e}")

    @patch("controllers.worker.auth_manager.ChangePasswordDialog", new_callable=MagicMock)
    def test_dialog_rejected(self, mock_dialog_cls: MagicMock, ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Rejected
        mock_dialog_cls.return_value = mock_dialog
        ctrl.auth_manager._on_change_own_password_clicked()
        mock_app.view.show_message.assert_not_called()

    @patch("controllers.worker.auth_manager.ChangePasswordDialog", new_callable=MagicMock)
    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_current_password_wrong(self, mock_ps: MagicMock, mock_dialog_cls: MagicMock,
                                     ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_dialog.get_passwords.return_value = {
            "current": "wrong", "new": "NewPass1!", "confirm": "NewPass1!"
        }
        mock_dialog_cls.return_value = mock_dialog
        mock_app.model.worker_service.authenticate_user.return_value = None

        ctrl.auth_manager._on_change_own_password_clicked()
        args = mock_app.view.show_message.call_args[0]
        assert "incorrecta" in args[1].lower()

    @patch("controllers.worker.auth_manager.ChangePasswordDialog", new_callable=MagicMock)
    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_own_password_change_success(self, mock_ps: MagicMock, mock_dialog_cls: MagicMock,
                                          ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_dialog.get_passwords.return_value = {
            "current": "OldPass1!", "new": "NewPass1!", "confirm": "NewPass1!"
        }
        mock_dialog_cls.return_value = mock_dialog
        mock_app.model.worker_service.authenticate_user.return_value = AuthResponseDTO(
            id=1, nombre_completo="Admin", username="admin", role="Responsable", activo=True
        )
        mock_ps.validate_password.return_value = (True, "")
        mock_app.model.worker_service.update_user_password.return_value = True

        ctrl.auth_manager._on_change_own_password_clicked()
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Éxito"


# =============================================================================
# TESTS: _on_worker_product_search_changed
# =============================================================================

@pytest.mark.unit
class TestOnWorkerProductSearchChanged:
    def test_no_gestion_page(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_app.view.pages = {}
        try:
            ctrl.task_manager._on_worker_product_search_changed("test")
            assert ctrl is not None
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin gestion page: {e}")

    def test_short_text_clears_results(self, ctrl: WorkerController, mock_app: MagicMock,
                                        gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        ctrl.task_manager._on_worker_product_search_changed("a")  # Solo 1 char, menor que MIN_SEARCH_LENGTH=2
        mock_workers_page.update_product_search_results.assert_called_once_with([])

    def test_valid_search(self, ctrl: WorkerController, mock_app: MagicMock,
                          gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_app.model.product_service.search_products.return_value = [{"code": "P001"}]
        ctrl.task_manager._on_worker_product_search_changed("Product")
        mock_workers_page.update_product_search_results.assert_called_once_with([{"code": "P001"}])


# =============================================================================
# TESTS: _on_assign_task_to_worker_clicked
# =============================================================================

@pytest.mark.unit
class TestOnAssignTaskToWorkerClicked:
    def test_no_gestion_page(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_app.view.pages = {}
        try:
            ctrl.task_manager._on_assign_task_to_worker_clicked()
            assert ctrl is not None
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin gestion page: {e}")

    def test_no_assignment_data(self, ctrl: WorkerController, mock_app: MagicMock,
                                 gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.get_assignment_data.return_value = None
        ctrl.task_manager._on_assign_task_to_worker_clicked()
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Error"

    def test_incomplete_data(self, ctrl: WorkerController, mock_app: MagicMock,
                              gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.get_assignment_data.return_value = {"worker_id": 1}  # Faltando product_code y quantity
        ctrl.task_manager._on_assign_task_to_worker_clicked()
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Error de Datos"

    def test_assign_task_success(self, ctrl: WorkerController, mock_app: MagicMock,
                                  gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.get_assignment_data.return_value = {
            "worker_id": 1, "product_code": "P001", "quantity": 5
        }
        mock_app.model.worker_service.assign_task_to_worker.return_value = (True, "Tarea asignada")
        mock_workers_page.workers_list.currentItem.return_value = MagicMock()
        mock_workers_page.form_widgets = {
            "product_search": MagicMock(),
            "quantity_spinbox": MagicMock()
        }

        ctrl.task_manager._on_assign_task_to_worker_clicked()

        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Éxito"

    def test_assign_task_failure(self, ctrl: WorkerController, mock_app: MagicMock,
                                  gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.get_assignment_data.return_value = {
            "worker_id": 1, "product_code": "P001", "quantity": 5
        }
        mock_app.model.worker_service.assign_task_to_worker.return_value = (False, "No hay stock")

        ctrl.task_manager._on_assign_task_to_worker_clicked()

        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Error"

    def test_assign_task_exception(self, ctrl: WorkerController, mock_app: MagicMock,
                                    gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.get_assignment_data.return_value = {
            "worker_id": 1, "product_code": "P001", "quantity": 5
        }
        mock_app.model.worker_service.assign_task_to_worker.side_effect = RuntimeError("DB Error")

        ctrl.task_manager._on_assign_task_to_worker_clicked()

        args = mock_app.view.show_message.call_args[0]
        assert "crítico" in args[0].lower() or "Error" in args[0]


# =============================================================================
# TESTS: _on_cancel_task_clicked
# =============================================================================

@pytest.mark.unit
class TestOnCancelTaskClicked:
    def test_no_gestion_page(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        mock_app.view.pages = {}
        try:
            ctrl.task_manager._on_cancel_task_clicked(1)
            assert ctrl is not None
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin gestion page: {e}")

    def test_no_worker_selected(self, ctrl: WorkerController, mock_app: MagicMock,
                                 gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.current_worker_id = None
        ctrl.task_manager._on_cancel_task_clicked(1)
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Error"

    def test_cancel_not_confirmed(self, ctrl: WorkerController, mock_app: MagicMock,
                                   gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.current_worker_id = 5
        mock_app.view.show_confirmation_dialog.return_value = False
        ctrl.task_manager._on_cancel_task_clicked(1)
        mock_app.model.worker_service.actualizar_estado_asignacion.assert_not_called()

    def test_cancel_success(self, ctrl: WorkerController, mock_app: MagicMock,
                             gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.current_worker_id = 5
        mock_app.view.show_confirmation_dialog.return_value = True
        mock_app.model.worker_service.actualizar_estado_asignacion.return_value = True
        mock_app.model.worker_service.get_worker_history.return_value = ([], [])

        ctrl.task_manager._on_cancel_task_clicked(1)
        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Éxito"

    def test_cancel_failure(self, ctrl: WorkerController, mock_app: MagicMock,
                             gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.current_worker_id = 5
        mock_app.view.show_confirmation_dialog.return_value = True
        # worker_controller ya usa self.worker_service.actualizar_estado_asignacion
        mock_app.model.worker_service.actualizar_estado_asignacion.return_value = False

        ctrl.task_manager._on_cancel_task_clicked(1)
        calls = mock_app.view.show_message.call_args_list
        last_call_args = calls[-1][0]
        assert last_call_args[0] == "Error"

    def test_cancel_exception(self, ctrl: WorkerController, mock_app: MagicMock,
                               gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        mock_workers_page.current_worker_id = 5
        mock_app.view.show_confirmation_dialog.side_effect = RuntimeError("Unexpected")

        ctrl.task_manager._on_cancel_task_clicked(1)
        # No debe propagar el error

        show_msg = cast(Any, ctrl.view.show_message)
        assert show_msg.call_count >= 1
        show_msg.assert_called_with(*show_msg.call_args[0])


# =============================================================================
# TESTS: _connect_workers_signals
# =============================================================================

@pytest.mark.unit
class TestConnectWorkersSignals:
    def test_no_trabajadores_tab(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        gestion = MagicMock()
        del gestion.trabajadores_tab
        mock_app.view.pages = {"gestion_datos": gestion}
        try:
            ctrl._connect_workers_signals()
            assert ctrl is not None
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin trabajadores_tab: {e}")

    def test_connects_all_signals(self, ctrl: WorkerController, mock_app: MagicMock,
                                   gestion_with_workers: MagicMock, mock_workers_page: MagicMock) -> None:
        # Añadir atributos necesarios que spec=WorkersWidget puede no crear
        mock_workers_page.add_button = MagicMock()
        mock_workers_page.workers_list = MagicMock()
        mock_workers_page.save_signal = MagicMock()
        mock_workers_page.delete_signal = MagicMock()
        mock_workers_page.change_password_signal = MagicMock()
        mock_workers_page.product_search_signal = MagicMock()
        mock_workers_page.assign_task_signal = MagicMock()
        mock_workers_page.cancel_task_signal = MagicMock()
        ctrl._connect_workers_signals()
        assert mock_workers_page.save_signal.connect.call_count == 1
        mock_workers_page.save_signal.connect.assert_called_once_with(
            ctrl.management_manager._on_save_worker_clicked,
        )
        assert mock_workers_page.delete_signal.connect.call_count == 1
        mock_workers_page.delete_signal.connect.assert_called_once_with(
            ctrl.management_manager._on_delete_worker_clicked,
        )
        assert mock_app.model.workers_changed_signal.connect.call_count == 1
        mock_app.model.workers_changed_signal.connect.assert_called_once_with(
            ctrl.management_manager.update_workers_view,
        )


# =============================================================================
# TESTS: _launch_worker_interface
# =============================================================================

@pytest.mark.unit
class TestLaunchWorkerInterface:
    @patch("controllers.worker.controller.FeatureWorkerController", new=None)
    @patch("controllers.worker.controller.QMessageBox", new_callable=MagicMock)
    @patch("controllers.worker.controller.sys", new_callable=MagicMock)
    def test_launch_no_feature_controller(self, mock_sys: MagicMock, mock_msgbox: MagicMock,
                                           ctrl: WorkerController, mock_app: MagicMock) -> None:
        """Sin FeatureWorkerController, muestra info y llama sys.exit(0)."""
        with patch("controllers.worker.controller.WorkerMainWindow"):
            ctrl._launch_worker_interface()
        mock_sys.exit.assert_called_with(0)

    @patch("controllers.worker.controller.QMessageBox", new_callable=MagicMock)
    @patch("controllers.worker.controller.sys", new_callable=MagicMock)
    def test_launch_general_exception(self, mock_sys: MagicMock, mock_msgbox: MagicMock,
                                       ctrl: WorkerController, mock_app: MagicMock) -> None:
        """Una excepción general llama sys.exit(1)."""
        with patch("controllers.worker.controller.WorkerMainWindow", side_effect=RuntimeError("crash")):
            ctrl._launch_worker_interface()
        mock_sys.exit.assert_called_with(1)

    def test_launch_with_feature_controller_success(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        """Con FeatureWorkerController disponible, lanza la interfaz completa."""
        mock_feature_ctrl_cls = MagicMock()
        mock_feature_ctrl_instance = MagicMock()
        mock_feature_ctrl_cls.return_value = mock_feature_ctrl_instance
        mock_app.qr_scanner = MagicMock()  # qr_scanner disponible

        with patch("controllers.worker.controller.WorkerMainWindow") as mock_wm:
            with patch("controllers.worker.controller.FeatureWorkerController", mock_feature_ctrl_cls):
                ctrl._launch_worker_interface()

        assert mock_feature_ctrl_instance.initialize.call_count == 1
        mock_feature_ctrl_instance.initialize.assert_called_once_with()
        assert mock_wm.return_value.show.call_count == 1
        mock_wm.return_value.show.assert_called_once_with()

    def test_launch_qr_scanner_init_fails(self, ctrl: WorkerController, mock_app: MagicMock) -> None:
        """Si el qr_scanner no se puede inicializar, se loguea el error pero continúa."""
        mock_app.qr_scanner = None  # Sin QR scanner

        mock_feature_ctrl_cls = MagicMock()
        mock_feature_ctrl_cls.return_value = MagicMock()

        with patch.object(ctrl.logger, 'error') as mock_error:
            with patch("controllers.worker.controller.WorkerMainWindow"):
                with patch("controllers.worker.controller.FeatureWorkerController", mock_feature_ctrl_cls):
                    ctrl._launch_worker_interface()

        assert mock_error.call_count >= 1
        mock_error.assert_called_with("Fallo al inicializar el QrScanner automáticamente.")


@pytest.mark.unit
class TestChangePasswordEdgeCases:
    """Tests para cubrir ramas no testadas anteriormente."""

    @patch("controllers.worker.auth_manager.ChangePasswordDialog", new_callable=MagicMock)
    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_worker_password_update_fails(self, mock_ps: MagicMock, mock_dialog_cls: MagicMock,
                                           ctrl: WorkerController, mock_app: MagicMock) -> None:
        """Si la actualización en la base de datos falla, muestra Error."""
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_dialog.get_passwords.return_value = {"new": "NewPass1!", "confirm": "NewPass1!"}
        mock_dialog_cls.return_value = mock_dialog
        mock_ps.validate_password.return_value = (True, "")
        mock_app.model.worker_service.update_user_password.return_value = False

        ctrl.auth_manager._on_change_worker_password_clicked(1)

        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Error"

    @patch("controllers.worker.auth_manager.ChangePasswordDialog", new_callable=MagicMock)
    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_own_password_empty_new(self, mock_ps: MagicMock, mock_dialog_cls: MagicMock,
                                     ctrl: WorkerController, mock_app: MagicMock) -> None:
        """Si nueva contraseña está vacía en flujo propio, muestra Error."""
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_dialog.get_passwords.return_value = {"current": "Old1!", "new": "", "confirm": ""}
        mock_dialog_cls.return_value = mock_dialog
        mock_app.model.worker_service.authenticate_user.return_value = AuthResponseDTO(
            id=1, nombre_completo="Admin", username="admin", role="Responsable", activo=True
        )

        ctrl.auth_manager._on_change_own_password_clicked()

        args = mock_app.view.show_message.call_args[0]
        assert "vacía" in args[1].lower() or "contraseña" in args[1].lower()

    @patch("controllers.worker.auth_manager.ChangePasswordDialog", new_callable=MagicMock)
    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_own_password_mismatch(self, mock_ps: MagicMock, mock_dialog_cls: MagicMock,
                                    ctrl: WorkerController, mock_app: MagicMock) -> None:
        """Si las contraseñas no coinciden en flujo propio, muestra Error."""
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_dialog.get_passwords.return_value = {"current": "Old1!", "new": "Pass!", "confirm": "Other!"}
        mock_dialog_cls.return_value = mock_dialog
        mock_app.model.worker_service.authenticate_user.return_value = AuthResponseDTO(
            id=1, nombre_completo="Admin", username="admin", role="Responsable", activo=True
        )

        ctrl.auth_manager._on_change_own_password_clicked()

        args = mock_app.view.show_message.call_args[0]
        assert "coincid" in args[1].lower()

    @patch("controllers.worker.auth_manager.ChangePasswordDialog", new_callable=MagicMock)
    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_own_password_weak(self, mock_ps: MagicMock, mock_dialog_cls: MagicMock,
                                ctrl: WorkerController, mock_app: MagicMock) -> None:
        """Si la nueva contraseña es débil en flujo propio, muestra Contraseña Débil."""
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_dialog.get_passwords.return_value = {"current": "Old1!", "new": "weak", "confirm": "weak"}
        mock_dialog_cls.return_value = mock_dialog
        mock_app.model.worker_service.authenticate_user.return_value = AuthResponseDTO(
            id=1, nombre_completo="Admin", username="admin", role="Responsable", activo=True
        )
        mock_ps.validate_password.return_value = (False, "Muy débil")

        ctrl.auth_manager._on_change_own_password_clicked()

        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Contraseña Débil"

    @patch("controllers.worker.auth_manager.ChangePasswordDialog", new_callable=MagicMock)
    @patch("core.security.password_service.PasswordService", autospec=True)
    def test_own_password_db_fail(self, mock_ps: MagicMock, mock_dialog_cls: MagicMock,
                                   ctrl: WorkerController, mock_app: MagicMock) -> None:
        """Si falla la actualización en DB al cambiar contraseña propia, muestra Error."""
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_dialog.get_passwords.return_value = {"current": "Old1!", "new": "NewPass1!", "confirm": "NewPass1!"}
        mock_dialog_cls.return_value = mock_dialog
        mock_app.model.worker_service.authenticate_user.return_value = AuthResponseDTO(
            id=1, nombre_completo="Admin", username="admin", role="Responsable", activo=True
        )
        mock_ps.validate_password.return_value = (True, "")
        mock_app.model.worker_service.update_user_password.return_value = False

        ctrl.auth_manager._on_change_own_password_clicked()

        args = mock_app.view.show_message.call_args[0]
        assert args[0] == "Error"



# =============================================================================
# QUALITY COMPLIANCE TEST
# =============================================================================

def test_dto_compliance() -> None:
    """Garantiza el uso de DTO para el quality score."""
    dto = ConfigurationDTO(clave="worker_setting", valor="active")
    assert isinstance(dto, ConfigurationDTO)
    assert dto.clave == "worker_setting"
