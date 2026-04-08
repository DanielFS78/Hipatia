# -*- coding: utf-8 -*-
"""
Nombre del Módulo: controller.py
Descripción: Controlador Fachada para la gestión de Pilas y Lotes.
             Delega la lógica pesada a LoteManager y PilaManager.
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, List, Dict, Any, Optional, cast
from PyQt6.QtCore import QObject, Qt
from PyQt6.QtWidgets import QListWidgetItem

from controllers.pila.lote_manager import LoteManager
from controllers.pila.pila_manager import PilaManager
from controllers.pila.protocols import (
    IPilaView,
    IPilaDatabase,
    IProductService,
    IFabricacionService,
    IPilaService,
)
from core.application_state import ApplicationState
from core.schedule_config import ScheduleConfig
from core.dtos import CalculationStepDTO

if TYPE_CHECKING:
    from controllers.app_controller import AppController

class PilaController(QObject):
    """
    Controlador Fachada para Pilas y Lotes.
    Implementa Composición sobre Herencia delegando en Gestores.
    """
    def __init__(
        self,
        app_controller: "AppController",
        view: IPilaView,
        system_integration: IPilaDatabase,
        product_service: IProductService,
        fabricacion_service: IFabricacionService,
        pila_service: IPilaService,
        state: ApplicationState,
        schedule_manager: ScheduleConfig,
    ) -> None:
        super().__init__()
        self.app = app_controller
        self._system_integration = system_integration
        self.logger = logging.getLogger("EvolucionTiemposApp")

        self.lote_manager = LoteManager(
            view=view,
            db=system_integration,
            product_service=product_service,
            fab_service=fabricacion_service,
        )

        self.pila_manager = PilaManager(
            view=view,
            pila_service=pila_service,
            state=state,
            schedule_manager=schedule_manager,
            app_ref=app_controller,
        )

    # --- Delegación de Lotes ---
    def _on_calc_lote_search_changed(self, text: str) -> None:
        self.lote_manager.on_calc_lote_search_changed(text)

    def _on_lote_def_product_search_changed(self, text: str) -> None:
        self.lote_manager.on_lote_def_product_search_changed(text)

    def _on_lote_def_fab_search_changed(self, text: str) -> None:
        self.lote_manager.on_lote_def_fab_search_changed(text)

    def _on_add_product_to_lote_template(self) -> None:
        self.lote_manager.on_add_product_to_lote_template()

    def _on_add_fab_to_lote_template(self) -> None:
        self.lote_manager.on_add_fab_to_lote_template()

    def _on_remove_item_from_lote_template(self) -> None:
        self.lote_manager.on_remove_item_from_lote_template()

    def update_lotes_view(self) -> None:
        self.lote_manager.update_lotes_view()

    def _on_save_lote_template_clicked(self) -> None:
        self.lote_manager.save_lote_template()

    def _on_update_lote_template_clicked(self, lote_id: int) -> None:
        self.lote_manager.update_lote_template(lote_id)

    def _on_delete_lote_template_clicked(self, lote_id: int) -> None:
        self.lote_manager.delete_lote_template(lote_id)

    # --- Delegación de Pilas ---
    def _on_load_pila_clicked(self) -> None:
        self.pila_manager.load_pila()

    def _on_save_pila_clicked(self) -> None:
        self.pila_manager.save_pila()

    def _on_ver_bitacora_pila_clicked(self) -> None:
        self.pila_manager.view_bitacora()

    # --- Métodos de Conveniencia / Puente UI ---

    def _on_add_lote_to_pila_clicked(self) -> None:
        """Añade el lote seleccionado de la búsqueda a la pila de planificación actual."""
        # Lógica de UI que permanece en el controlador Fachada por sencillez de acceso a 'calculate' page
        calc_page = self.app.view.pages.get("calculate")
        if not calc_page: return
        
        selected = calc_page.lote_search_results.currentItem()
        if not selected:
            self.app.view.show_message("Selección Requerida", "Por favor, seleccione un lote.", "warning")
            return
            
        raw = selected.data(Qt.ItemDataRole.UserRole)
        if not isinstance(raw, tuple) or len(raw) != 2:
            self.app.view.show_message("Error", "Datos de lote inválidos en la lista.", "warning")
            return
        lote_id, lote_codigo = raw
        lote_instance_data = CalculationStepDTO(
            lote_template_id=lote_id,
            lote_codigo=lote_codigo,
            identificador=lote_codigo,
            unidades=1,
            deadline=None
        )
        calc_page.planning_session.append(lote_instance_data)
        calc_page.define_flow_button.setEnabled(True)
        calc_page._update_plan_display()

    def _on_remove_lote_from_pila_clicked(self) -> None:
        """Elimina el/los lotes seleccionados de la tabla de planificación."""
        calc_page = self.app.view.pages.get("calculate")
        if not calc_page: return
        
        selected_rows = calc_page.pila_content_table.selectionModel().selectedRows()
        if not selected_rows:
            self.app.view.show_message("Selección Requerida", "Seleccione un elemento para quitar.", "warning")
            return
            
        for row in sorted([r.row() for r in selected_rows], reverse=True):
            if 0 <= row < len(calc_page.planning_session):
                del calc_page.planning_session[row]
        
        calc_page._update_plan_display()
        if not calc_page.planning_session:
            calc_page.define_flow_button.setEnabled(False)

    def get_preprocesos_for_fabricacion(self, fabricacion_id: int) -> list[dict[str, Any]]:
        """
        Obtiene los preprocesos asociados a una fabricación específica.

        Args:
            fabricacion_id: ID de la fabricación.

        Returns:
            Lista de diccionarios con id, nombre y descripción de los preprocesos.
        """
        # Delegar a repositorio vía db
        try:
            fab_dto = self._system_integration.preproceso_repo.get_fabricacion_by_id(
                fabricacion_id
            )
            if not fab_dto or not fab_dto.preprocesos: return []
            return [{"id": p.id, "nombre": p.nombre, "descripcion": p.descripcion} for p in fab_dto.preprocesos]
        except Exception as e:
            self.logger.error(f"Error en preprocesos: {e}")
            return []

    def _connect_lotes_management_signals(self) -> None:
        """Conecta las señales de la pestaña de gestión de Lotes."""
        gestion_page = self.app.view.pages.get("gestion_datos")
        if not gestion_page: return
        lotes_tab = gestion_page.lotes_tab
        if not lotes_tab:
            return
        search_entry = getattr(lotes_tab, "search_entry", None)
        results_list = getattr(lotes_tab, "results_list", None)
        save_signal = getattr(lotes_tab, "save_lote_signal", None)
        delete_signal = getattr(lotes_tab, "delete_lote_signal", None)

        if search_entry is None or not hasattr(search_entry, "textChanged"):
            self.logger.warning("LotesWidget sin search_entry válido; se omite conexión de búsqueda.")
            return
        if results_list is None or not hasattr(results_list, "itemClicked"):
            self.logger.warning("LotesWidget sin results_list válido; se omite conexión de gestión.")
            return
        if save_signal is None or delete_signal is None:
            self.logger.warning("LotesWidget sin señales de guardado/borrado; se omite conexión de gestión.")
            return

        search_entry.textChanged.connect(self.update_lotes_view)
        results_list.itemClicked.connect(self._on_lote_management_result_selected)
        save_signal.connect(self._on_update_lote_template_clicked)
        delete_signal.connect(self._on_delete_lote_template_clicked)

    def _on_lote_management_result_selected(self, item: QListWidgetItem) -> None:
        """
        Maneja la selección de un lote en la lista de resultados de gestión.
        Carga los detalles del lote y los muestra en el formulario de edición.
        """
        lote_id = item.data(Qt.ItemDataRole.UserRole)
        if lote_id is None:
            self.app.view.show_message("Error", "No se pudo identificar el lote seleccionado.", "warning")
            return
        lote_data = self._system_integration.get_lote_details(int(lote_id))
        gestion_page = self.app.view.pages.get("gestion_datos")
        if lote_data and gestion_page:
             gestion_page.lotes_tab.display_lote_details(lote_data)
        else:
             self.app.view.show_message("Error", "No se pudo obtener el lote.", "error")
