# -*- coding: utf-8 -*-
"""
Nombre del Módulo: management_manager.py (Worker)
Descripción: Gestor de administración de personal. Maneja el CRUD de trabajadores 
             y la visualización de sus detalles en el panel de administración.
"""
import logging
from typing import Any, TYPE_CHECKING, Optional, List
from PyQt6.QtCore import Qt
from ui.widgets import GestionDatosWidget
from core.security.access_control import require_permission
from core.security.security_service import Permission

from .protocols import IWorkerView, IWorkerService, IFabricacionService, IWorkerModel

from ui.widgets.workers_widget import WorkersWidget

class WorkerManagementManager:
    """
    Gestor para la administración de trabajadores (CRUD).
    Reemplaza al antiguo ManagementMixin.
    """
    def __init__(self, app: Any, model: IWorkerModel, view: IWorkerView, worker_service: IWorkerService, fabricacion_service: Optional[IFabricacionService] = None):
        """
        Inicializa el gestor de administración de trabajadores.

        Args:
            app: Instancia del controlador principal.
            model: Referencia al modelo de datos general.
            view: Interfaz de usuario.
            worker_service: Servicio lógico de gestión de trabajadores.
            fabricacion_service: Servicio opcional para gestión de fabricaciones.
        """
        self.app = app
        self.model = model
        self.view = view
        self.worker_service = worker_service
        self.fabricacion_service = fabricacion_service
        self.logger = logging.getLogger("EvolucionTiemposApp")

    def _on_worker_selected_in_list(self, item: Any) -> None:
        """
        Maneja la selección de un trabajador en la lista de la UI.
        Carga sus detalles y el autocompletado de órdenes de fabricación.

        Args:
            item: Elemento de la lista seleccionado.
        """
        worker_id = item.data(Qt.ItemDataRole.UserRole)
        worker_data = self.worker_service.get_worker_details(worker_id)
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if not gestion_datos_page:
            return

        workers_page = getattr(gestion_datos_page, "trabajadores_tab", None)
        if not workers_page:
            return

        if worker_data:
            workers_page.show_worker_details(worker_data)
            # CAMBIO: Usar el servicio inyectado directamente
            of_list = self.fabricacion_service.get_all_ordenes_fabricacion() if self.fabricacion_service else []
            workers_page.setup_of_completer(of_list)
        else:
            workers_page.clear_details_area()

    @require_permission(Permission.MANAGE_USERS)
    def _on_save_worker_clicked(self) -> None:
        """Maneja el guardado/actualización de trabajadores."""
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if not gestion_datos_page:
            return

        workers_page = getattr(gestion_datos_page, "trabajadores_tab", None)
        if not workers_page:
            return
        worker_id = workers_page.current_worker_id
        data = workers_page.get_form_data()

        try:
            if not data:
                self.view.show_message("Error", "Datos de trabajador inválidos.", "warning")
                return

            nombre = data.nombre_completo
            if not nombre:
                self.view.show_message("Error", "El nombre del trabajador es obligatorio.", "warning")
                return

            username = data.username or ""
            password = data.password or ""
            role = data.role or "Trabajador"

            password_hash = None
            if password:
                from core.security.password_service import PasswordService
                is_valid, error_msg = PasswordService.validate_password(password)
                if not is_valid:
                    self.view.show_message("Contraseña Débil", error_msg, "warning")
                    return

                self.logger.info(f"Hasheando nueva contraseña para {'nuevo usuario' if worker_id is None else f'usuario ID {worker_id}'}")
                password_hash = PasswordService.hash_password(password)

            if username and not role:
                self.view.show_message("Error", "Si se define un nombre de usuario, se debe seleccionar un rol.", "warning")
                return

            username_to_save = username if username else None
            role_to_save = role if username else None

            if worker_id is None:
                if username and not password:
                    self.view.show_message("Error", "Un nuevo usuario debe tener una contraseña.", "warning")
                    return

                result = self.worker_service.add_worker(
                    nombre,
                    data.notas,
                    data.tipo_trabajador,
                    username_to_save,
                    password_hash,
                    role_to_save
                )
                if result is True:
                    self.view.show_message("Éxito", "Trabajador añadido.", "info")
                    
                    if hasattr(self.app, 'session_controller') and self.app.session_controller:
                         user = self.app.session_controller.current_user
                         username_admin = user.username if user else 'System'
                         admin_id = user.id if user else None
                         self.app.session_controller.audit_logger.log(
                             username=username_admin,
                             action='CREATE',
                             entity_type='WORKER',
                             entity_id=0,
                             description=f"Trabajador creado: {nombre}",
                             user_id=admin_id
                         )
                    
                    self.update_workers_view()
                elif result == "UNIQUE_CONSTRAINT":
                    self.view.show_message("Error", "Ya existe un trabajador con ese nombre o nombre de usuario.", "warning")
                else:
                    self.view.show_message("Error", "No se pudo añadir el trabajador.", "critical")
            else:
                if self.worker_service.update_worker(
                        worker_id,
                        nombre,
                        data.activo,
                        data.notas,
                        data.tipo_trabajador,
                        username_to_save,
                        password_hash,
                        role_to_save
                ):
                    self.view.show_message("Éxito", "Trabajador actualizado.", "info")
                    
                    if hasattr(self.app, 'session_controller') and self.app.session_controller:
                         user = self.app.session_controller.current_user
                         username_admin = user.username if user else 'System'
                         admin_id = user.id if user else None
                         self.app.session_controller.audit_logger.log(
                             username=username_admin,
                             action='UPDATE',
                             entity_type='WORKER',
                             entity_id=worker_id,
                             description=f"Trabajador actualizado: {nombre}",
                             user_id=admin_id
                         )
                         
                    self.update_workers_view()
                else:
                    self.view.show_message("Error", "No se pudo actualizar.", "critical")

        except Exception as e:
            self.logger.error(f"Error guardando trabajador: {e}")
            self.view.show_message("Error", f"Error inesperado: {e}", "critical")

    @require_permission(Permission.MANAGE_USERS)
    def _on_delete_worker_clicked(self, worker_id: int) -> None:
        if self.view.show_confirmation_dialog("Confirmar", "¿Seguro que quieres eliminar a este trabajador?"):
            if self.worker_service.delete_worker(worker_id):
                self.view.show_message("Éxito", "Trabajador eliminado.", "info")
                
                if hasattr(self.app, 'session_controller') and self.app.session_controller:
                     user = self.app.session_controller.current_user
                     username_admin = user.username if user else 'System'
                     admin_id = user.id if user else None
                     self.app.session_controller.audit_logger.log_delete(
                         username=username_admin,
                         entity_type='WORKER',
                         entity_id=worker_id,
                         description=f"Trabajador eliminado ID: {worker_id}",
                         user_id=admin_id
                     )
            else:
                self.view.show_message("Error", "No se pudo eliminar.", "critical")

    def update_workers_view(self) -> None:
        """Actualiza la vista de trabajadores con TODOS los trabajadores."""
        self.logger.info("Actualizando la vista de trabajadores...")
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if gestion_datos_page:
            workers_page = getattr(gestion_datos_page, "trabajadores_tab", None)
            if not workers_page:
                return
            workers_data = self.worker_service.get_all_workers()
            workers_page.populate_list(workers_data)
