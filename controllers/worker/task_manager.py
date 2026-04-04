# -*- coding: utf-8 -*-
"""
Nombre del Módulo: task_manager.py (Worker)
Descripción: Gestor de asignación de tareas. Permite buscar productos y asignar 
             órdenes de fabricación específicas a los trabajadores.
"""
import logging
from typing import TYPE_CHECKING, Any
from core.security.access_control import require_permission
from core.security.security_service import Permission
from core import constants

from .protocols import IWorkerView, IWorkerService, IProductService, WorkerControllerProtocol

class WorkerTaskManager:
    """
    Gestor para la asignación y cancelación de tareas a trabajadores.
    """
    def __init__(
        self,
        app: Any,
        view: IWorkerView,
        worker_service: IWorkerService,
        product_service: IProductService,
        controller_ref: WorkerControllerProtocol,
    ):
        self.app = app
        self.view = view
        self.worker_service = worker_service
        self.product_service = product_service
        self.controller = controller_ref  # p.ej. management_manager vía protocolo
        self.logger = logging.getLogger("EvolucionTiemposApp")

    def _on_worker_product_search_changed(self, text: str) -> None:
        """Maneja la búsqueda de productos en la pestaña de asignación de tareas del trabajador."""
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if not gestion_datos_page:
            return

        workers_page = getattr(gestion_datos_page, "trabajadores_tab", None)
        if not workers_page:
            return

        if len(text) < constants.VALIDATION['MIN_SEARCH_LENGTH']:
            workers_page.update_product_search_results([])
            return

        results = self.product_service.search_products(text)
        workers_page.update_product_search_results(results)

    @require_permission(Permission.CREATE_FABRICATION)
    def _on_assign_task_to_worker_clicked(self) -> None:
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if not gestion_datos_page:
            return

        workers_page = getattr(gestion_datos_page, "trabajadores_tab", None)
        if not workers_page:
            return
        data = workers_page.get_assignment_data()

        if not data:
            self.view.show_message("Error", "Debe seleccionar un producto de la lista.", "warning")
            return

        worker_id = data.get("worker_id")
        product_code = data.get("product_code")
        quantity = data.get("quantity")

        if not all([worker_id, product_code, quantity]):
            self.view.show_message("Error de Datos", "Faltan datos (Trabajador, Producto o Cantidad).", "critical")
            return

        try:
            self.logger.info(f"Creando nueva Tarea/OF para producto {product_code}")
            success, message = self.worker_service.assign_task_to_worker(worker_id, product_code, quantity)

            if success:
                self.view.show_message("Éxito", message, "info")
                # Usamos el nuevo método de alto nivel para desacoplar el controlador de la UI
                if hasattr(workers_page, "clear_assignment_form"):
                    workers_page.clear_assignment_form()
                # Delegamos de vuelta al otro gestor (o al controller) para refrescar detalles
                item = workers_page.workers_list.currentItem()
                if item:
                    self.controller.management_manager._on_worker_selected_in_list(item)
            else:
                self.view.show_message("Error", message, "critical")

        except Exception as e:
            self.logger.error(f"Error crítico en _on_assign_task_to_worker_clicked: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Error inesperado: {e}", "critical")

    @require_permission(Permission.DELETE_FABRICATION)
    def _on_cancel_task_clicked(self, fabricacion_id: int) -> None:
        try:
            gestion_datos_page = self.view.pages.get("gestion_datos")
            if not gestion_datos_page:
                return

            workers_page = getattr(gestion_datos_page, "trabajadores_tab", None)
            if not workers_page:
                return
            worker_id = workers_page.current_worker_id

            if not worker_id:
                self.view.show_message("Error", "No hay trabajador seleccionado.", "warning")
                return

            reply = self.view.show_confirmation_dialog(
                "Cancelar Tarea",
                "¿Está seguro que desea cancelar esta tarea?\n\n"
                "La tarea quedará marcada como 'cancelada' y el trabajador ya no la verá en su lista."
            )

            if not reply:
                return

            success = self.worker_service.actualizar_estado_asignacion(
                trabajador_id=worker_id,
                fabricacion_id=fabricacion_id,
                nuevo_estado='cancelado'
            )

            if success:
                self.view.show_message("Éxito", "La tarea ha sido cancelada correctamente.", "info")
                fabrication_history, annotations = self.worker_service.get_worker_history(worker_id)
                workers_page.populate_history_tables(fabrication_history, annotations)
            else:
                self.view.show_message("Error", "No se pudo cancelar la tarea. Verifique los logs para más detalles.", "critical")

        except Exception as e:
            self.logger.error(f"Error cancelando tarea: {e}", exc_info=True)
            self.view.show_message("Error", f"Error inesperado al cancelar la tarea:\n\n{str(e)}", "critical")
