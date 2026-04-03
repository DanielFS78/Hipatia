# -*- coding: utf-8 -*-
"""
Nombre del Módulo: fabricacion_manager.py (Product)
Descripción: Gestor de órdenes de fabricación, encargado de coordinar la creación 
             y edición de producciones junto con sus preprocesos y productos asociados.
"""
import logging
from typing import Any, List, Dict, Optional, Tuple, TYPE_CHECKING, cast
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QWidget
from ui.dialogs import CreateFabricacionDialog, PreprocesosSelectionDialog, ProductsSelectionDialog
from core.dtos import FabricacionDTO, PreprocesoDTO, CalculationProductDTO
from .fabricacion_products_handler import (
    FabricacionProductsHandler,
    IPlanningCalculationProvider,
)
from .protocols import ProductControllerProtocol, IProductView, IProductService, IFabricacionService


class FabricacionManager:
    """
    Gestor de fabricaciones y órdenes de trabajo.

    Facilita la creación de nuevas fabricaciones mediante diálogos interactivos, 
    gestiona la búsqueda y filtrado de las mismas, y sincroniza sus preprocesos.
    """

    def __init__(
        self, 
        app: Any, 
        view: IProductView, 
        fabricacion_service: IFabricacionService, 
        product_facade: IProductService,
        planning_facade: IPlanningCalculationProvider,
        state: Any, 
        controller_ref: Optional[ProductControllerProtocol] = None
    ) -> None:
        """
        Inicializa el gestor de fabricaciones.

        Args:
            app: Referencia a la aplicación principal (AppController).
            view: Referencia a la vista principal (IProductView).
            fabricacion_service: Servicio lógico de fabricaciones (IFabricacionService).
            product_facade: Fachada de catálogo de productos (IProductService).
            planning_facade: Fachada de planificación (datos para motor de cálculo).
            state: Estado compartido de la aplicación (ApplicationState).
            controller_ref: Referencia opcional al controlador.
        """
        self.app = app
        self.view = view
        self.fabricacion_service = fabricacion_service
        self.product_facade = product_facade
        self.state = state
        self.controller_ref = controller_ref
        self.logger = logging.getLogger("EvolucionTiemposApp")
        self._products_handler = FabricacionProductsHandler(
            view,
            self.logger,
            fabricacion_service,
            product_facade,
            planning_facade,
        )

    def show_fabricacion_products(self, fabricacion_id: int) -> None:
        """Muestra el diálogo para asignar/editar productos de una fabricación."""
        self._products_handler.show_fabricacion_products(fabricacion_id)

    def _on_fabrication_result_selected_by_id(self, fabricacion_id: int) -> None:
        """Refresca visualización de fabricación usando ID directamente."""
        self._products_handler.refresh_fabrication_display(fabricacion_id)

    def get_fabricacion_products_for_calculation(self, fabricacion_id: int) -> List[CalculationProductDTO]:
        """Obtiene productos de la fabricación preparados para el motor de cálculo."""
        return self._products_handler.get_fabricacion_products_for_calculation(fabricacion_id)

    def _on_fabrication_search_changed(self, text: str) -> None:
        """Maneja el cambio de texto en la búsqueda de fabricaciones."""
        fab_page = self.view.get_fabrications_tab()
        if not fab_page: return
        results = self.fabricacion_service.search_fabricaciones(text)
        fab_page.update_fabrications_table(results)

    def show_create_fabricacion_dialog(self) -> None:
        """Muestra el diálogo para crear fabricación con preprocesos y productos."""
        dialog_key = "create_fabricacion"
        if self.state.active_dialogs.get(dialog_key) and self.state.active_dialogs[dialog_key].isVisible():
            self.state.active_dialogs[dialog_key].activateWindow()
            self.state.active_dialogs[dialog_key].raise_()
            return

        try:
            all_preprocesos = self.fabricacion_service.get_all_preprocesos_with_components()
            all_products = self.product_facade.search_products("")
            if not all_preprocesos and not all_products:
                self.view.show_message("Información", "No hay preprocesos ni productos. Cree alguno antes.", "info")
                return

            dialog = CreateFabricacionDialog(all_preprocesos, all_products, cast(QWidget, self.view))
            self.state.active_dialogs[dialog_key] = dialog

            if dialog.exec() == QDialog.DialogCode.Accepted:
                data: FabricacionDTO = dialog.get_fabricacion_data()
                if not data: return
                success = self.fabricacion_service.create_fabricacion_with_preprocesos(data)
                if success:
                    fab_codigo = data.codigo
                    if data.productos and fab_codigo:
                        fab_dto = self.fabricacion_service.get_fabricacion_by_codigo(fab_codigo)
                        if fab_dto and data.productos:
                            self.fabricacion_service.set_products_for_fabricacion(fab_dto.id, data.productos)
                    
                    self.view.show_message("Éxito", f"Fabricación '{fab_codigo}' creada.", "info")
                    if hasattr(self.app, 'session_controller') and self.app.session_controller:
                        user = self.app.session_controller.current_user
                        self.app.session_controller.audit_logger.log(
                           username=user.username if user else 'System',
                           action='CREATE', entity_type='FABRICATION', entity_id=0,
                           description=f"Fabricación creada: {fab_codigo}", user_id=user.id if user else None
                        )
                    
                    fab_tab = self.view.get_fabrications_tab()
                    if fab_tab and hasattr(fab_tab, 'search_entry'):
                        self._on_fabrication_search_changed(fab_tab.search_entry.text())
                    self.app.ui_controller.on_data_changed()
                else:
                    self.view.show_message("Error", "No se pudo crear. El código podría ya existir.", "critical")
        except Exception as e:
            self.logger.error(f"Error crítico en creación de fabricación: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Error inesperado: {e}", "critical")
        finally:
             self.state.active_dialogs[dialog_key] = None

    def search_fabricaciones(self, query: str) -> list[Any]:
        """Busca fabricaciones usando el repositorio de preprocesos."""
        try:
            result = self.fabricacion_service.search_fabricaciones(query)
            return result if result is not None else []
        except Exception as e:
            self.logger.error(f"Error buscando fabricaciones: {e}")
            return []

    def _on_fabrication_result_selected(self, item: Any) -> None:
        """Maneja la selección de una fabricación en la lista."""
        try:
            fabrications_page = self.view.get_fabrications_tab()
            if not fabrications_page: return
            fabricacion_id = item.data(Qt.ItemDataRole.UserRole)
            if not fabricacion_id: return

            fabricacion_data = self.fabricacion_service.get_fabricacion_by_id(fabricacion_id)
            if fabricacion_data:
                preprocesos = fabricacion_data.preprocesos or []
                if hasattr(fabrications_page, 'display_fabricacion_form'):
                    fabrications_page.display_fabricacion_form(fabricacion_data, preprocesos)
            else:
                self.view.show_message("Error", f"No se encontraron detalles para la fabricación ID {fabricacion_id}.", "warning")
                if hasattr(fabrications_page, 'clear_edit_area'):
                    fabrications_page.clear_edit_area()
        except Exception as e:
            self.logger.error(f"Error al seleccionar fabricación: {e}", exc_info=True)

    def _on_update_fabricacion(self, fabricacion_id: int) -> bool:
        """Actualiza una fabricación existente."""
        try:
            fabrications_page = self.view.get_fabrications_tab()
            if not fabrications_page: return False
            data = fabrications_page.get_fabricacion_form_data()
            if not data: return False

            if self.fabricacion_service.update_fabricacion_and_preprocesos(fabricacion_id, data, None):
                self.view.show_message("Éxito", "Fabricación editada correctamente", "info")
                if hasattr(self.app, 'session_controller') and self.app.session_controller:
                     user = self.app.session_controller.current_user
                     self.app.session_controller.audit_logger.log(
                         username=user.username if user else 'System',
                         action='UPDATE', entity_type='FABRICATION', entity_id=fabricacion_id,
                         description=f"Fabricación actualizada: {data.codigo}", user_id=user.id if user else None
                     )
                self.app.ui_controller.on_data_changed()
                self._refresh_fabricaciones_list()
                return True
            else:
                self.view.show_message("Error", "No se pudo actualizar.", "critical")
                return False
        except Exception as e:
            self.view.show_message("Error", f"Error inesperado: {e}", "critical")
            self.logger.error(f"Error actualizando fabricación: {e}", exc_info=True)
            return False

    def _on_delete_fabricacion(self, fabricacion_id: int) -> bool:
        """Elimina una fabricación."""
        try:
            if self.view.show_confirmation_dialog("Confirmar Eliminación", "¿Está seguro?"):
                if self.fabricacion_service.delete_fabricacion(fabricacion_id):
                    self.view.show_message("Éxito", "Fabricación eliminada", "info")
                    if hasattr(self.app, 'session_controller') and self.app.session_controller:
                         user = self.app.session_controller.current_user
                         self.app.session_controller.audit_logger.log_delete(
                             username=user.username if user else 'System',
                             entity_type='FABRICATION', entity_id=fabricacion_id,
                             description=f"Fabricación eliminada ID: {fabricacion_id}", user_id=user.id if user else None
                         )
                    self.app.ui_controller.on_data_changed()
                    self._refresh_fabricaciones_list()
                    fab_tab = self.view.get_fabrications_tab()
                    if fab_tab: fab_tab.clear_edit_area()
                    return True
                else:
                    self.view.show_message("Error", "No se pudo eliminar.", "critical")
                    return False
        except Exception as e:
            self.view.show_message("Error", f"Error inesperado: {e}", "critical")
            self.logger.error(f"Error eliminando fabricación: {e}", exc_info=True)
            return False
        return False

    def show_fabricacion_preprocesos(self, fabricacion_id: int) -> None:
        """Muestra el diálogo para asignar/editar preprocesos de una fabricación."""
        try:
            fabricacion_dto = self.fabricacion_service.get_fabricacion_by_id(fabricacion_id)
            if not fabricacion_dto:
                self.view.show_message("Error", "Fabricación no encontrada.", "critical")
                return

            fabricacion_tuple = (fabricacion_dto.id, fabricacion_dto.codigo, fabricacion_dto.descripcion)
            all_preprocesos = self.fabricacion_service.get_all_preprocesos_with_components()
            assigned_preprocesos = self.fabricacion_service.get_preprocesos_by_fabricacion(fabricacion_id)
            assigned_ids = [p.id for p in assigned_preprocesos]
            
            dialog = PreprocesosSelectionDialog(fabricacion_tuple, all_preprocesos, assigned_ids, cast(QWidget, self.view))
            if dialog.exec() == QDialog.DialogCode.Accepted:
                if self.fabricacion_service.update_fabricacion_preprocesos(fabricacion_id, dialog.get_selected_preprocesos()):
                    self.view.show_message("Éxito", "Preprocesos guardados con éxito", "info")
                    self._refresh_fabricaciones_list()
                    self._on_fabrication_result_selected_by_id(fabricacion_id)
        except Exception as e:
            self.view.show_message("Error", f"No se pudo abrir la gestión de preprocesos: {e}", "critical")
            self.logger.error(f"Error gestión preprocesos: {e}", exc_info=True)

    def _refresh_fabricaciones_list(self) -> None:
        try:
            fab_tab = self.view.get_fabrications_tab()
            if fab_tab:
                self._on_fabrication_search_changed(fab_tab.search_entry.text())
        except Exception as e:
            self.logger.error(f"Error refrescando fabricaciones: {e}")

