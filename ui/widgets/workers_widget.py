"""
Nombre del Módulo: workers_widget.py
Descripción: Widget orquestador para la gestión de trabajadores en el panel de administración.
             Gestiona la lista, detalles, asignaciones y sincronización con el controlador.
"""
from .base import *
from typing import Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.dtos import WorkerFormDataDTO
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QListWidget,
    QPushButton, QListWidgetItem, QTabWidget, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ui.widgets.worker.worker_details_panel import WorkerDetailsPanel
from ui.widgets.worker.worker_activity_panel import WorkerActivityPanel
from ui.widgets.worker.worker_incidence_dialog import WorkerIncidenceDialog

class WorkersWidget(QWidget):
    """
    Widget principal para la gestión de trabajadores (Orquestador).

    Centraliza la vista de lista de trabajadores y los paneles de detalle.
    Gestiona la comunicación entre sub-widgets y el WorkerController.
    Incluye un área de scroll para asegurar la visibilidad de los botones de acción.
    """
    save_signal = pyqtSignal()
    delete_signal = pyqtSignal(int)
    change_password_signal = pyqtSignal(int)
    product_search_signal = pyqtSignal(str)
    of_search_signal = pyqtSignal(str)
    add_annotation_signal = pyqtSignal(int)
    assign_task_signal = pyqtSignal()
    cancel_task_signal = pyqtSignal(int)

    def __init__(self, controller: Any = None) -> None:
        super().__init__()
        from core.di_container import DIContainer
        from controllers.worker.controller import WorkerController
        self.worker_controller = DIContainer.get_instance().resolve(WorkerController)
        self.current_worker_id: Optional[int] = None
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Configura la interfaz principal con lista y paneles de detalle."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Panel Izquierdo: Lista de Trabajadores
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("<b>Trabajadores Actuales</b>"))
        self.workers_list = QListWidget()
        left_layout.addWidget(self.workers_list)
        self.add_button = QPushButton("Añadir Nuevo Trabajador")
        left_layout.addWidget(self.add_button)

        # Panel Derecho: Detalles y Actividad (Tabs)
        self.right_tabs = QTabWidget()
        self.details_panel = WorkerDetailsPanel()
        self.activity_panel = WorkerActivityPanel()
        
        self.right_tabs.addTab(self.details_panel, "Detalles y Asignación")
        self.right_tabs.addTab(self.activity_panel, "Actividad e Historial")
        
        # Wrap right tabs in a ScrollArea to prevent clipping on small screens
        self.right_scroll = QScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setWidget(self.right_tabs)
        self.right_scroll.setFrameStyle(QFrame.Shape.NoFrame)
        
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(self.right_scroll, 3)

        self.right_tabs.setVisible(False)
        self.placeholder = QLabel("Seleccione un trabajador para ver detalles.")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.placeholder, 3)

    def _connect_signals(self) -> None:
        """Conecta las señales de los sub-componentes con las del orquestador."""
        self.details_panel.save_signal.connect(self.save_signal.emit)
        self.details_panel.delete_signal.connect(lambda: self.delete_signal.emit(self.current_worker_id or 0))
        self.details_panel.change_password_signal.connect(lambda: self.change_password_signal.emit(self.current_worker_id or 0))
        self.details_panel.product_search_signal.connect(self.product_search_signal.emit)
        self.details_panel.of_search_signal.connect(self.of_search_signal.emit)
        self.details_panel.assign_task_signal.connect(self.assign_task_signal.emit)
        
        self.activity_panel.cancel_task_signal.connect(self.cancel_task_signal.emit)
        self.activity_panel.show_incidences_signal.connect(self.show_incidences_dialog)
        
        self.add_button.clicked.connect(self.show_add_new_form)

    def populate_list(self, workers_data: List[Any]) -> None:
        """Puebla la lista lateral de trabajadores."""
        self.workers_list.blockSignals(True)
        self.workers_list.clear()
        for worker in workers_data:
            item_text = f"{worker.nombre_completo} {'(Activo)' if worker.activo else '(Inactivo)'}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, worker.id)
            if not worker.activo:
                item.setForeground(QColor("gray"))
            self.workers_list.addItem(item)
        self.workers_list.blockSignals(False)
        self.clear_details_area()

    def clear_details_area(self) -> None:
        """Oculta los paneles y muestra el placeholder."""
        self.right_tabs.setVisible(False)
        self.placeholder.setVisible(True)
        self.current_worker_id = None

    def show_worker_details(self, worker_data: Any) -> None:
        """Muestra la información de un trabajador en los paneles correspondientes."""
        self.placeholder.setVisible(False)
        self.right_tabs.setVisible(True)
        self.current_worker_id = worker_data.id if worker_data else None
        
        self.details_panel.set_worker_data(worker_data)
        self.right_tabs.setTabVisible(1, True)

        if self.current_worker_id and self.worker_controller:
            ws = self.worker_controller.worker_service
            history, _ = ws.get_worker_history(self.current_worker_id)
            self.activity_panel.populate_history(history)
            logs = ws.get_worker_activity_log(self.current_worker_id)
            self.activity_panel.populate_activity_log(logs)

    def show_add_new_form(self) -> None:
        """Configura el panel de detalles para un nuevo trabajador."""
        self.placeholder.setVisible(False)
        self.right_tabs.setVisible(True)
        self.current_worker_id = None
        self.details_panel.set_worker_data(None)
        self.right_tabs.setTabVisible(1, False)
        self.right_tabs.setCurrentIndex(0)

    def get_form_data(self) -> "WorkerFormDataDTO":
        """Delega la extracción de datos de formulario al panel de detalles."""
        from core.dtos import WorkerFormDataDTO
        return self.details_panel.get_form_data()

    def get_assignment_data(self) -> Optional[dict[str, Any]]:
        """Delega la extracción de datos de asignación al panel de detalles."""
        data = self.details_panel.get_assignment_data()
        if data:
            data["worker_id"] = self.current_worker_id
        return data

    def update_product_search_results(self, results: List[Any]) -> None:
        """Actualiza los resultados de búsqueda en el panel de detalles."""
        self.details_panel.update_product_results(results)

    def setup_of_completer(self, of_list: List[str]) -> None:
        """Configura el autocompletado de O.F. en el panel de detalles."""
        self.details_panel.set_of_completer(of_list)

    def show_incidences_dialog(self, incidences: List[Any]) -> None:
        """Abre el diálogo modal de incidencias."""
        dialog = WorkerIncidenceDialog(incidences, self)
        dialog.exec()

    # --- Métodos de Compatibilidad Layer (Fase 12C / Retrocompatibilidad) ---

    def populate_history_tables(self, fabrication_history: List[Any], annotations: List[Any]) -> None:
        """Método de compatibilidad para el controlador."""
        self.activity_panel.populate_history(fabrication_history)

    def clear_assignment_form(self) -> None:
        """Limpia los campos de asignación de tareas en el panel de detalles."""
        self.update_product_search_results([])
        self.details_panel.clear_assignment_search_fields()

    @property
    def form_widgets(self) -> dict[str, Any]:
        """Propiedad de compatibilidad para acceder a los widgets del formulario."""
        return self.details_panel.form_widgets
