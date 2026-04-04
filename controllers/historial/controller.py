# -*- coding: utf-8 -*-
"""
Nombre del Módulo: controller.py (Historial)
Descripción: Controlador principal del sub-paquete de historial. Utiliza composición 
             para delegar la gestión de UI, interacciones y reportes.
"""
from __future__ import annotations
import logging
from typing import Optional, Any, List, TYPE_CHECKING
from .view_manager import HistorialViewManager
from .interaction_manager import HistorialInteractionManager
from .report_manager import HistorialReportManager

if TYPE_CHECKING:
    from core.app_model import AppModel

class HistorialController:
    """
    Controlador central para el historial.

    Orquestra los diferentes gestores (Vista, Interacción, Reportes) para 
    proporcionar una interfaz unificada de consulta de auditoría y bitácoras.
    """

    def __init__(self, db: Any, pila_service: Any, worker_service: Any, view: Any, logger: Optional[logging.Logger] = None) -> None:
        """
        Inicializa el controlador y compone sus gestores.

        Args:
            db: Referencia a la base de datos.
            pila_service: Servicio de gestión de pilas de fabricación.
            worker_service: Servicio de gestión de operarios.
            view: Referencia a la vista principal.
            logger: Instancia de logging (opcional).
        """
        self.db = db
        self.pila_service = pila_service
        self.worker_service = worker_service
        self.view = view
        self.logger = logger or logging.getLogger(__name__)

        # Composición de gestores
        self.view_manager = HistorialViewManager(db, pila_service, view, self)
        self.interaction_manager = HistorialInteractionManager(db, pila_service, view, self)
        self.report_manager = HistorialReportManager(db, pila_service, worker_service, view, self)

    @property
    def historial_data(self) -> List[Any]:
        return self.view_manager.historial_data
    
    @historial_data.setter
    def historial_data(self, value: List[Any]) -> None:
        self.view_manager.historial_data = value

    def connect_signals(self, page: Any) -> None:
        """Conecta las señales de la vista del historial delegando en los gestores."""
        page.search_text_changed_signal.connect(self.populate_list)
        page.filter_changed_signal.connect(self.populate_list)
        page.item_selected_signal.connect(self.on_item_selected)
        page.calendar_date_selected_signal.connect(self.on_calendar_clicked)
        page.print_report_signal.connect(self.on_print_report_clicked)
        # Sincronizar actualización cuando cambia el modo
        page.mode_changed_signal.connect(lambda _: self.update_view())

    # Delegación de métodos de ViewManager
    def update_view(self) -> None:
        self.view_manager.update_view()

    def populate_list(self) -> None:
        self.view_manager.populate_list()

    def update_calendar_highlights(self) -> None:
        self.view_manager.update_calendar_highlights()

    def update_activity_chart(self) -> None:
        self.view_manager.update_activity_chart()

    # Delegación de métodos de InteractionManager
    def on_item_selected(self, item: Any) -> None:
        self.interaction_manager.on_item_selected(item)

    def on_calendar_clicked(self, q_date: Any) -> None:
        self.interaction_manager.on_calendar_clicked(q_date)

    # Delegación de métodos de ReportManager
    def on_print_report_clicked(self) -> None:
        self.report_manager.on_print_report_clicked()
