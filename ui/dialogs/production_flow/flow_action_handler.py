"""
Interfaz PyQt6 (`flow_action_handler`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""
from __future__ import annotations

from typing import Optional, Any, List, Dict, TYPE_CHECKING
from PyQt6.QtWidgets import QMessageBox, QInputDialog, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt
from core.flow_canvas_io import (
    canvas_task_body,
    cycle_end_dialog_configuration_values,
    worker_line_config_display_name,
    worker_line_config_reassignment_rule,
    worker_line_config_set_reassignment_rule,
)
from .common_dialogs import CycleEndConfigDialog, ReassignmentRuleDialog

if TYPE_CHECKING:
    from controllers.app_controller import AppController

class FlowActionHandler:
    """
    Gestiona las acciones de configuración (ciclos, reasignaciones)
    y persistencia (guardar/cargar) del diálogo visual.
    """
    def __init__(self, parent: QWidget, presenter: Any, graph_manager: Any, controller: AppController) -> None:
        self.parent = parent
        self.presenter = presenter
        self.graph_manager = graph_manager
        self.controller = controller
        from core.di_container import DIContainer
        from core.services.pila_service import PilaService
        _c = DIContainer.get_instance()
        self._pila_service: Any = _c.resolve(PilaService) if _c.is_registered(PilaService) else None

    def handle_cycle_end(self, selected_index: Optional[int], simulation_service: Any) -> None:
        if selected_index is None: return
        dialog = CycleEndConfigDialog(selected_index, self.presenter.canvas_tasks, self.parent)
        if dialog.exec():
            cfg = dialog.get_configuration()
            ice, rti = cycle_end_dialog_configuration_values(cfg)
            if self.presenter.apply_cycle_end_config(selected_index, ice, rti):
                self.graph_manager.update_connections(selected_index)
                self.graph_manager.update_all_cycle_effects(simulation_service)

    def handle_reassignment(self, selected_index: Optional[int], worker_name: Optional[str]) -> None:
        if selected_index is None or not worker_name: return
        
        config = self.presenter.get_worker_config(selected_index, worker_name)
        if not config: return
        
        task = self.presenter.get_task(selected_index)
        if not task: return

        dialog = ReassignmentRuleDialog(
            worker_line_config_display_name(config, worker_name),
            canvas_task_body(task),
            self.presenter.canvas_tasks,
            worker_line_config_reassignment_rule(config),
            self.parent,
        )
        if dialog.exec():
            worker_line_config_set_reassignment_rule(config, dialog.get_rule())

    def delete_task(self, selected_index: Optional[int], inspector: Any) -> Optional[int]:
        if selected_index is None: return selected_index
        if QMessageBox.question(self.parent, "Eliminar", "¿Eliminar tarea?") == QMessageBox.StandardButton.Yes:
            self.graph_manager.remove_task_widget(selected_index)
            inspector.clear()
            return None
        return selected_index

    def clear_canvas(self, inspector: Any) -> Optional[int]:
        if QMessageBox.question(self.parent, "Limpiar", "¿Limpiar todo?") == QMessageBox.StandardButton.Yes:
            self.graph_manager.clear()
            inspector.clear()
            return None
        # Devolvemos el índice actual si no se borra
        return -1 # Marcador de no cambio

    def load_saved_pila(self, flow_loader_callback: Any) -> None:
        if self._pila_service is not None:
            pilas = self._pila_service.get_all_pilas()
        else:
            pilas = self.controller.model.get_all_pilas()
        if not pilas: return
        
        items = [f"{p.nombre} (ID: {p.id})" for p in pilas]
        item, ok = QInputDialog.getItem(self.parent, "Cargar Pila", "Seleccione:", items, 0, False)
        if ok and item:
            pila_id = pilas[items.index(item)].id
            if self._pila_service is not None:
                _, _, flow, _ = self._pila_service.load_pila(pila_id)
            else:
                _, _, flow, _ = self.controller.model.load_pila(pila_id)
            if flow: flow_loader_callback(flow)

    def save_pila_only(self) -> None:
        nombre, ok = QInputDialog.getText(self.parent, "Guardar", "Nombre:")
        if ok and nombre:
            desc, _ = QInputDialog.getText(self.parent, "Guardar", "Descripción:")
            self.graph_manager.synchronize_positions()
            self.controller.handle_save_flow_only(nombre, desc, self.presenter.build_production_flow())

    def initialize_library(self, tasks_data: List[Dict[str, Any]], library_panel: Any) -> None:
        """Prepara y carga los datos en el panel de la biblioteca."""
        structured_data = self.presenter.prepare_task_data(tasks_data)
        library_panel.task_data_by_product = structured_data
        library_panel.populate_tasks()

    def setup_floating_widgets(self, canvas: QWidget, preview_callback: Any) -> tuple[QPushButton, QLabel]:
        """Crea y configura el botón de previsualización y la etiqueta de estado."""
        preview_button = QPushButton("▶️ Previsualizar Orden", self.parent)
        preview_button.resize(180, 40)
        preview_button.setStyleSheet(
            "background-color: #6f42c1; color: white; border-radius: 20px; font-weight: bold;"
        )
        preview_button.clicked.connect(preview_callback)
        
        simulation_label = QLabel(canvas)
        simulation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        simulation_label.setStyleSheet(
            "background-color: rgba(44,62,80,230); color: white; "
            "border: 2px solid #3498db; border-radius: 10px; padding: 15px;"
        )
        simulation_label.hide()
        
        return preview_button, simulation_label
