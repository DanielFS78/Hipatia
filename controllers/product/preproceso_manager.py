# -*- coding: utf-8 -*-
"""
Nombre del Módulo: preproceso_manager.py (Product)
Descripción: Gestor de rutinas de preproceso, encargado de la definición, edición 
             y eliminación de tareas previas necesarias para la fabricación.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from PyQt6.QtCore import Qt
from core.security.access_control import require_permission
from core.security.security_service import Permission
from core.dtos import PreprocesoDTO
from controllers.ui_class_loader import ui_class

PreprocesoDialog = ui_class("ui.dialogs", "PreprocesoDialog")

from .protocols import ProductControllerProtocol, IProductView, IFabricacionService, IMaterialService

class PreprocesoManager:
    """
    Gestor de rutinas de preproceso.

    Administra el ciclo de vida de los preprocesos, permitiendo su creación, 
    modificación y eliminación, así como su visualización en la interfaz de gestión.
    """

    def __init__(
        self, 
        view: IProductView, 
        fabricacion_service: IFabricacionService, 
        material_service: IMaterialService, 
        controller_ref: Optional[ProductControllerProtocol] = None
    ) -> None:
        """
        Inicializa el gestor de preprocesos.

        Args:
            view: Referencia a la vista principal (IProductView).
            fabricacion_service: Servicio lógico de fabricaciones (IFabricacionService).
            material_service: Servicio lógico de materiales (IMaterialService).
            controller_ref: Referencia opcional al controlador (ProductControllerProtocol).
        """
        self.view = view
        self.fabricacion_service = fabricacion_service
        self.material_service = material_service
        self.controller_ref = controller_ref
        self.logger = logging.getLogger("EvolucionTiemposApp")

    def get_preprocesos_by_fabricacion(self, fabricacion_id: int) -> List[Any]:
        """Obtiene preprocesos vinculados a una fabricación."""
        try:
            return self.fabricacion_service.get_preprocesos_by_fabricacion(fabricacion_id)
        except Exception as e:
            self.logger.error(f"Error obteniendo preprocesos fabricación: {e}")
            return []

    def _load_preprocesos_data(self) -> None:
        """Carga datos de preprocesos en la tabla visual."""
        widget = self.view.get_page("preprocesos")
        if not widget: return
        
        try:
            data = self.fabricacion_service.get_all_preprocesos_with_components()
            if hasattr(widget, 'load_preprocesos_data'):
                widget.load_preprocesos_data(data)
        except Exception as e:
            if hasattr(widget, 'load_preprocesos_data'):
                widget.load_preprocesos_data([])
            self.logger.error(f"Error cargando preprocesos: {e}")

    def show_add_preproceso_dialog(self) -> None:
        """Muestra diálogo para crear preproceso."""
        try:
            all_materials = self.material_service.get_all_materials_for_selection()
            dialog = PreprocesoDialog(all_materials=all_materials, controller=self.controller_ref, parent=self.view)
            if dialog.exec():
                data = dialog.get_data()
                if data:
                    dto = PreprocesoDTO(
                        id=data.get('id', 0),
                        nombre=data.get('nombre', ''),
                        descripcion=data.get('descripcion', ''),
                        tiempo=float(data.get('tiempo', 0.0)),
                        componentes_ids=data.get('componentes_ids', [])
                    )
                    if self.fabricacion_service.create_preproceso(dto):
                        self.view.show_message("Éxito", f"Preproceso '{data['nombre']}' creado.", "info")
                        self._load_preprocesos_data()
                    else:
                        self.view.show_message("Error", "No se pudo crear el preproceso. El nombre podría ya existir.", "critical")
        except Exception as e:
            self.logger.error(f"Error diálogo crear preproceso: {e}", exc_info=True)

    def show_edit_preproceso_dialog(self, preproceso_data: Any) -> None:
        """Muestra diálogo para editar preproceso."""
        try:
            all_materials = self.material_service.get_all_materials_for_selection()
            dialog = PreprocesoDialog(preproceso_existente=preproceso_data, all_materials=all_materials, controller=self.controller_ref, parent=self.view)
            if dialog.exec():
                new_data = dialog.get_data()
                if new_data:
                    dto = PreprocesoDTO(
                        id=preproceso_data.id,
                        nombre=new_data.get('nombre', ''),
                        descripcion=new_data.get('descripcion', ''),
                        tiempo=float(new_data.get('tiempo', 0.0)),
                        componentes_ids=new_data.get('componentes_ids', [])
                    )
                    if self.fabricacion_service.update_preproceso(preproceso_data.id, dto):
                        self.view.show_message("Éxito", f"Preproceso '{new_data['nombre']}' actualizado.", "info")
                        self._load_preprocesos_data()
                    else:
                        self.view.show_message("Error", "No se pudo actualizar el preproceso.", "critical")
        except Exception as e:
            self.logger.error(f"Error diálogo editar preproceso: {e}", exc_info=True)

    @require_permission(Permission.DELETE_PRODUCT)
    def delete_preproceso(self, preproceso_id: int, preproceso_nombre: str) -> None:
        """Solicita confirmación y elimina un preproceso."""
        reply = self.view.show_confirmation_dialog(
            'Confirmar Eliminación',
            f"¿Estás seguro de que quieres eliminar el preproceso '{preproceso_nombre}'?\n\nEsta acción no se puede deshacer."
        )

        if reply:
            try:
                if self.fabricacion_service.delete_preproceso(preproceso_id):
                    self.view.show_message("Éxito", f"El preproceso '{preproceso_nombre}' ha sido eliminado.", "info")
                    self._load_preprocesos_data()
                else:
                    self.view.show_message("Error de Eliminación", "No se pudo eliminar.", "critical")
            except Exception as e:
                self.view.show_message("Error", f"Error al eliminar el preproceso: {e}", "critical")
                self.logger.error(f"Error eliminando preproceso: {e}")
