# -*- coding: utf-8 -*-
"""
Nombre del Módulo: auth_manager.py (Worker)
Descripción: Gestor encargado de la seguridad y autenticación de trabajadores, 
             específicamente el cambio de contraseñas propias y ajenas.
"""
from typing import TYPE_CHECKING, Any
from PyQt6.QtWidgets import QDialog
from ui.dialogs import ChangePasswordDialog
from core.security.access_control import require_permission
from core.security.security_service import Permission

from .protocols import IWorkerView, IWorkerService

class WorkerAuthManager:
    """
    Gestor para el cambio de contraseñas de trabajadores y administración.
    """
    def __init__(self, app: Any, view: IWorkerView, worker_service: IWorkerService):
        self.app = app
        self.view = view
        self.worker_service = worker_service

    @require_permission(Permission.MANAGE_USERS)
    def _on_change_worker_password_clicked(self, worker_id: int) -> None:
        if not self.app.current_user or getattr(self.app.current_user, 'role', '') != 'Responsable':
            self.view.show_message("Acceso Denegado", "No tienes permisos para esta acción.", "warning")
            return

        worker_data = self.worker_service.get_worker_details(worker_id)
        if not worker_data:
            self.view.show_message("Error", "No se encontró al trabajador.", "critical")
            return

        dialog = ChangePasswordDialog(require_current_password=False, parent=self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            passwords = dialog.get_passwords()
            new_pass = passwords['new']
            confirm_pass = passwords['confirm']

            if not new_pass:
                self.view.show_message("Error", "La nueva contraseña no puede estar vacía.", "warning")
                return

            if new_pass != confirm_pass:
                self.view.show_message("Error", "Las contraseñas no coinciden.", "warning")
                return

            from core.security.password_service import PasswordService
            is_valid, error_msg = PasswordService.validate_password(new_pass)
            if not is_valid:
                self.view.show_message("Contraseña Débil", error_msg, "warning")
                return

            if self.worker_service.update_user_password(worker_id, new_pass):
                worker_name = (
                    worker_data.get("nombre_completo", "el trabajador")
                    if isinstance(worker_data, dict)
                    else getattr(worker_data, "nombre_completo", "el trabajador")
                )
                self.view.show_message("Éxito", f"Contraseña actualizada para {worker_name}.", "info")
            else:
                self.view.show_message("Error", "No se pudo actualizar la contraseña en la base de datos.", "critical")

    def _on_change_own_password_clicked(self) -> None:
        if not self.app.current_user:
            return

        admin_id = self.app.current_user.id
        dialog = ChangePasswordDialog(require_current_password=True, parent=self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            passwords = dialog.get_passwords()
            current_pass = passwords['current']
            new_pass = passwords['new']
            confirm_pass = passwords['confirm']

            user_data = self.worker_service.authenticate_user(self.app.current_user.username, current_pass)
            if not user_data:
                self.view.show_message("Error", "La contraseña actual es incorrecta.", "warning")
                return

            if not new_pass:
                self.view.show_message("Error", "La nueva contraseña no puede estar vacía.", "warning")
                return

            if new_pass != confirm_pass:
                self.view.show_message("Error", "Las nuevas contraseñas no coinciden.", "warning")
                return

            from core.security.password_service import PasswordService
            is_valid, error_msg = PasswordService.validate_password(new_pass)
            if not is_valid:
                self.view.show_message("Contraseña Débil", error_msg, "warning")
                return

            if self.worker_service.update_user_password(admin_id, new_pass):
                self.view.show_message("Éxito", "Tu contraseña ha sido actualizada.", "info")
            else:
                self.view.show_message("Error", "No se pudo actualizar tu contraseña en la base de datos.", "critical")
