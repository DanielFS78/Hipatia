from __future__ import annotations
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.production_flow.enhanced_flow_dialog
Descripción: Definición o simulación del flujo de producción (estado, presentadores, reglas y diálogos auxiliares).
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QMessageBox, QSplitter,
    QPushButton, QFrame, QApplication, QLabel, QInputDialog, QWidget
)
from PyQt6.QtCore import Qt, QTimer, QPoint

from core.schedule_config import ScheduleConfig

# Widgets y Managers
from ui.widgets.production_flow.inspector_panel import ProductionTaskInspector
from ui.widgets.production_flow.flow_canvas import ProductionFlowCanvas
from ui.widgets.production_flow.library_panel import TaskLibraryPanel
from ui.widgets.production_flow.flow_graph_manager import FlowGraphManager
from ui.widgets.production_flow.flow_toolbar import FlowToolbarWidget

# Diálogos y Presenter
from .common_dialogs import CycleEndConfigDialog, ReassignmentRuleDialog
from .enhanced_flow_presenter import EnhancedFlowPresenter
from .flow_simulation_handler import FlowSimulationHandler
from .flow_action_handler import FlowActionHandler
from core.services.flow_simulation_service import FlowSimulationService


class EnhancedProductionFlowDialog(QDialog):
    """
    Diálogo para la planificación visual del flujo de producción.
    Delegado en FlowGraphManager (UI Canvas) y EnhancedFlowPresenter (Lógica).
    """
    selected_index: Optional[int]
    simulation_session: Any # typed via presenter/service session

    def __init__(
        self, 
        tasks_data: List[Dict[str, Any]], 
        workers: List[str], 
        units: int, 
        hub: Any,
        schedule_config: Optional[ScheduleConfig],
        parent: Optional[QWidget] = None, 
        existing_flow: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        super().__init__(parent)
        self.schedule_config = schedule_config
        self.setWindowTitle("Planificador Visual de Producción")
        self.resize(1400, 900)

        self.workers = sorted(workers)
        self.units = units
        self.hub = hub
        self.logger = logging.getLogger("VisualFlowPlanner")
        self.selected_index = None

        # Presenter y Manager
        self.presenter = EnhancedFlowPresenter(schedule_config=self.schedule_config, default_units=self.units)
        self.simulation_service = FlowSimulationService()
        
        # --- UI SETUP (Compacto) ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.library_panel = TaskLibraryPanel({})
        self.library_panel.task_requested.connect(self._add_task_from_library)
        self.canvas = ProductionFlowCanvas()
        self.canvas.taskDropped.connect(self._on_task_dropped)
        self.inspector = ProductionTaskInspector()
        self.inspector.configChanged.connect(self._on_task_config_changed)
        self.inspector.actionTriggered.connect(self._on_inspector_action_triggered)

        splitter.addWidget(self.library_panel)
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.inspector)
        splitter.setSizes([300, 800, 300])

        self.toolbar = FlowToolbarWidget()
        self.toolbar.clear_requested.connect(self._clear_canvas)
        self.toolbar.load_requested.connect(self._load_saved_pila)
        self.toolbar.save_requested.connect(self._save_pila_only)
        self.toolbar.calculate_requested.connect(self.accept)

        main_layout.addWidget(splitter)
        main_layout.addWidget(self.toolbar)

        # Managers y Handlers
        self.graph_manager = FlowGraphManager(self.canvas, self.presenter, self.workers, self)
        self.graph_manager.task_selected_signal.connect(self._on_task_selected)
        
        self.action_handler = FlowActionHandler(self, self.presenter, self.graph_manager, self.hub)
        self.action_handler.initialize_library(tasks_data, self.library_panel)

        self.preview_button, self.simulation_label = self.action_handler.setup_floating_widgets(self.canvas, self._preview_execution_order)

        self.simulation_handler = FlowSimulationHandler(self.presenter, self.graph_manager, self.simulation_label, self)
        self.simulation_handler.finished.connect(lambda: self._set_ui_enabled(True))

        if existing_flow:
            self._load_flow_onto_canvas(existing_flow)


            self.preview_button.move(self.width() - 200, self.height() - 110)

    def closeEvent(self, event: Any) -> None:
        """Asegura la limpieza de recursos antes de cerrar."""
        self.cleanup()
        super().closeEvent(event)

    def cleanup(self) -> None:
        """Detiene timers y libera referencias circulares para evitar SegFaults."""
        if hasattr(self, 'simulation_handler'):
            self.simulation_handler.stop()
        if hasattr(self, 'graph_manager'):
            self.graph_manager.cleanup()

    # --- Acciones de Canvas/UI ---

    def _add_task_from_library(self, task_data: Dict[str, Any]) -> None:
        pos = QPoint((self.canvas.width()-250)//2, (self.canvas.height()-150)//2)
        self.graph_manager.add_task_widget(task_data, pos)
        self.graph_manager.select_task(len(self.graph_manager.widgets) - 1)

    def _on_task_dropped(self, task_data: Dict[str, Any], pos: QPoint) -> None:
        self.graph_manager.add_task_widget(task_data, pos)

    def _on_task_selected(self, index: int) -> None:
        self.selected_index = index
        ctx = self.graph_manager.get_task_inspector_context(index, self.workers)
        if ctx is None:
            return

        self.inspector.set_task(
            ctx.inspector_step_payload(),
            ctx.all_tasks_rows,
            [],
            ctx.workers,
        )
        self.graph_manager.select_task(index)

    def _on_task_config_changed(self, task_id: str, key: str, value: Any) -> None:
        if self.selected_index is None: return
        self.graph_manager.update_task_config(self.selected_index, key, value, self.simulation_service)

    def _on_inspector_action_triggered(self, action: str, task_id: str) -> None:
        if action == 'configure_cycle_end': self._handle_cycle_end()
        elif action == 'configure_reassignment': self._handle_reassignment()
        elif action == 'delete': self._delete_task()

    def _handle_cycle_end(self) -> None:
        self.action_handler.handle_cycle_end(self.selected_index, self.simulation_service)

    def _handle_reassignment(self) -> None:
        worker_name = self.inspector.get_selected_assigned_worker()
        self.action_handler.handle_reassignment(self.selected_index, worker_name)

    def _delete_task(self) -> None:
        self.selected_index = self.action_handler.delete_task(self.selected_index, self.inspector)

    def _clear_canvas(self) -> None:
        res = self.action_handler.clear_canvas(self.inspector)
        if res is None: self.selected_index = None

    # --- Persistencia ---

    def _load_flow_onto_canvas(self, flow_data: List[Dict[str, Any]]) -> None:
        self.graph_manager.load_from_flow(flow_data)
        self.graph_manager.update_all_cycle_effects(self.simulation_service)
        self.graph_manager.update_connections()

    def _load_saved_pila(self) -> None:
        self.action_handler.load_saved_pila(self._load_flow_onto_canvas)

    def _save_pila_only(self) -> None:
        self.action_handler.save_pila_only()

    # --- Simulación ---

    def _preview_execution_order(self) -> None:
        """Lanza la previsualización delegando en el handler."""
        if self.simulation_handler.start(self.simulation_service):
            self._set_ui_enabled(False)

    def _set_ui_enabled(self, enabled: bool) -> None:
        self.toolbar.set_buttons_enabled(enabled)
        self.preview_button.setEnabled(enabled)

    def get_production_flow(self) -> List[Dict[str, Any]]:
        self.graph_manager.synchronize_positions()
        return self.presenter.build_production_flow()
