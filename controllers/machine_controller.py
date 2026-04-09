# controllers/machine_controller.py
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: machine_controller.py
Descripción: Controlador encargado de la gestión de maquinaria, mantenimientos 
             y configuración de grupos de preparación de máquinas.
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any, Optional, List, Dict, cast

from PyQt6.QtCore import QObject, Qt
from PyQt6.QtWidgets import QInputDialog, QWidget
from datetime import date
from core.security.access_control import require_permission
from core.security.security_service import Permission
from core.services.preparation_service import PreparationService
from core.services.product_service import ProductService

if TYPE_CHECKING:
    from controllers.app_controller import AppController
    from core.services.machine_service import MachineService
    from core.interfaces.view_interface import IView
    from core.dtos import MachineDTO

class MachineController(QObject):
    """
    Controlador para la gestión de máquinas.

    Coordina la creación, edición y eliminación de maquinaria, además de supervisar 
    los registros de mantenimiento preventivo/correctivo y los grupos de preparación.
    """
    def __init__(
        self,
        machine_service: MachineService,
        preparation_service: PreparationService,
        product_service: ProductService,
        view: IView,
        logger: logging.Logger,
    ) -> None:
        """
        Inicializa el controlador de máquinas con sus dependencias.

        Args:
            machine_service: Servicio lógico de gestión de máquinas.
            preparation_service: Grupos y pasos de preparación de máquinas.
            product_service: Catálogo de productos (diálogos de prep).
            view: Interfaz de usuario para interacciones y mensajes.
            logger: Sistema de registro de eventos.
        """
        super().__init__()
        self.machine_service: MachineService = machine_service
        self.preparation_service: PreparationService = preparation_service
        self.product_service: ProductService = product_service
        self.view: IView = view
        self.logger: logging.Logger = logger

    def update_machines_view(self) -> None:
        """Actualiza la vista de máquinas con TODAS las máquinas."""
        self.logger.info("Actualizando la vista de máquinas...")
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if gestion_datos_page:
            machines_page = gestion_datos_page.maquinas_tab
            # CAMBIO: Usar get_all_machines en lugar de get_latest_machines
            machines_data = self.machine_service.get_all_machines()
            machines_page.populate_list(machines_data)

    @require_permission(Permission.MANAGE_MACHINES)
    def _on_save_machine_clicked(self) -> None:
        """
        Maneja el evento de guardado de una máquina (nueva o existente).
        Valida los datos del formulario y actualiza la persistencia.
        """
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if not gestion_datos_page: return
        
        machines_page = gestion_datos_page.maquinas_tab
        machine_id = machines_page.current_machine_id
        data = machines_page.get_form_data()

        if not data or not data["nombre"]:
            self.view.show_message("Error", "El nombre es obligatorio.", "warning")
            return

        if machine_id is None:  # Es una máquina nueva
            result = self.machine_service.add_machine(data["nombre"], data["departamento"], data["tipo_proceso"])
            if result is True:
                self.view.show_message("Éxito", "Máquina añadida.", "info")
                self.update_machines_view()
            elif result == "UNIQUE_CONSTRAINT":
                self.view.show_message("Error", "Ya existe una máquina con ese nombre.", "warning")
            else:
                self.view.show_message("Error", "No se pudo añadir la máquina.", "critical")
        else:  # Es una actualización
            if self.machine_service.update_machine(machine_id, data["nombre"], data["departamento"], data["tipo_proceso"],
                                         data["activa"]):
                self.view.show_message("Éxito", "Máquina actualizada.", "info")
                self.update_machines_view()
            else:
                self.view.show_message("Error", "No se pudo actualizar la máquina.", "critical")

    @require_permission(Permission.MANAGE_MACHINES)
    def _on_delete_machine_clicked(self) -> None:
        """
        Maneja la eliminación de la máquina seleccionada tras confirmación del usuario.
        """
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if not gestion_datos_page: return

        machines_page = gestion_datos_page.maquinas_tab
        machine_id = machines_page.current_machine_id

        if machine_id is None:
            self.view.show_message("Error", "No hay máquina seleccionada para eliminar.", "warning")
            return

        confirm = self.view.show_confirmation_dialog("Confirmar Eliminación",
                                                     "¿Está seguro de que desea eliminar esta máquina? Esta acción no se puede deshacer.")
        if confirm:
            if self.machine_service.delete_machine(machine_id):
                self.view.show_message("Éxito", "Máquina eliminada.", "info")
                self.update_machines_view()
            else:
                self.view.show_message("Error", "No se pudo eliminar la máquina (puede tener registros asociados).",
                                       "critical")

    @require_permission(Permission.MANAGE_MACHINES)
    def _on_add_maintenance_clicked(self, machine_id: Optional[int]) -> None:
        """
        Muestra un diálogo para añadir una nota de mantenimiento a la máquina.

        Args:
            machine_id: ID de la máquina a la que se le añade el registro.
        """
        if machine_id is None:
            self.view.show_message("Atención", "Debe haber una máquina seleccionada para añadir un registro.",
                                   "warning")
            return
        notes, ok = QInputDialog.getText(cast(QWidget, self.view), "Añadir Registro de Mantenimiento", "Notas del Mantenimiento:")
        if ok and notes.strip():
            if self.machine_service.add_machine_maintenance(machine_id, date.today(), notes.strip()):
                self.view.show_message("Éxito", "Registro de mantenimiento añadido.", "info")
                gestion_datos_page = self.view.pages.get("gestion_datos")
                if gestion_datos_page:
                    machines_page = gestion_datos_page.maquinas_tab
                    history_data = self.machine_service.get_machine_history(machine_id)
                    machines_page.populate_history_tables(history_data.get('maintenance_history', []))
            else:
                self.view.show_message("Error", "No se pudo añadir el registro.", "critical")

    def _on_machine_selected_in_list(self, item: Any) -> None:
        """
        Carga y muestra los detalles de la máquina seleccionada en la lista.

        Args:
            item: Elemento de la lista (QListWidgetItem) seleccionado.
        """
        machine_id: int = item.data(Qt.ItemDataRole.UserRole)
        all_machines: List[MachineDTO] = self.machine_service.get_all_machines(include_inactive=True)
        # Ahora usamos atributo DTO .id en lugar de índice [0]
        machine_data: Optional[MachineDTO] = next((m for m in all_machines if m.id == machine_id), None)
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if not gestion_datos_page:
            return
        machines_page = gestion_datos_page.maquinas_tab
        if machine_data:
            machines_page.show_machine_details(machine_data)
            history_data: Dict[str, Any] = self.machine_service.get_machine_history(machine_id)
            machines_page.populate_history_tables(history_data.get('maintenance_history', []))

    @require_permission(Permission.MANAGE_MACHINES)
    def _on_manage_prep_groups_clicked(self, machine_id: int, machine_name: str) -> None:
        """
        Abre el diálogo de gestión de grupos de preparación para una máquina.

        Args:
            machine_id: ID único de la máquina.
            machine_name: Nombre descriptivo de la máquina.
        """
        from controllers.ui_class_loader import ui_class

        PrepGroupsDialog = ui_class("ui.dialogs.prep.prep_groups_dialog", "PrepGroupsDialog")
        dialog = PrepGroupsDialog(
            machine_id,
            machine_name,
            self.preparation_service,
            self.product_service,
            self.view,
            cast(QWidget, self.view),
        )
        dialog.exec()

    def get_distinct_machine_processes(self) -> List[str]:
        """
        Obtiene el conjunto de procesos únicos (ej. 'Inyección', 'Montaje') 
        asignados a las máquinas registradas.
        """
        return self.machine_service.get_distinct_machine_processes()
