# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.production_flow.flow_simulation_handler
Descripción: Definición o simulación del flujo de producción (estado, presentadores, reglas y diálogos auxiliares).
"""

from __future__ import annotations

from typing import Optional, Any
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QLabel, QWidget

class FlowSimulationHandler(QObject):
    """
    Gestiona la lógica de previsualización de simulación en el editor visual.
    Controla el timer, las actualizaciones de la etiqueta de progreso y 
    la interacción con el presenter y canvas.
    """
    finished = pyqtSignal()
    step_executed = pyqtSignal(int)

    def __init__(self, presenter: Any, graph_manager: Any, simulation_label: Optional[QLabel], parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.presenter = presenter
        self.graph_manager = graph_manager
        self.simulation_label = simulation_label
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.simulation_service: Any = None

    def start(self, simulation_service: Any, interval_ms: int = 500) -> bool:
        """Inicia el proceso de previsualización."""
        self.simulation_service = simulation_service
        if not self.presenter.start_simulation_preview(self.simulation_service):
            return False
            
        self.timer.start(interval_ms)
        return True

    def stop(self) -> None:
        """Detiene la previsualización y limpia efectos."""
        self.timer.stop()
        if self.graph_manager:
            try:
                self.graph_manager.clear_simulation_effects()
            except RuntimeError:
                pass
        
        if self.simulation_label:
            try:
                self.simulation_label.hide()
            except RuntimeError:
                pass
        self.finished.emit()

    def _on_tick(self) -> None:
        """Ejecuta un paso de la simulación con guardias ultra-estrictas."""
        try:
            # Si el objeto C++ ha sido borrado, esto lanzará RuntimeError
            if self.simulation_label is None or not self.simulation_label.isEnabled():
                self.timer.stop()
                return
        except RuntimeError:
            self.timer.stop()
            return

        try:
            idx = self.presenter.get_next_simulation_step()
            if idx is None or idx == -1:
                self.stop()
                return

            self.graph_manager.highlight_processing_task(idx)
            text = self.presenter.get_simulation_progress_text(idx)
            self.simulation_label.setText(text)
            self._position_label()
            self.simulation_label.show()
            self.step_executed.emit(idx)
        except RuntimeError:
            self.timer.stop()

    def _position_label(self) -> None:
        """Posicion la etiqueta de simulación centrada en el canvas."""
        if not self.simulation_label: return
        
        try:
            parent = self.simulation_label.parentWidget()
            if not parent: return
            
            canvas_width = parent.width()
            canvas_height = parent.height()
            
            self.simulation_label.adjustSize()
            label_w = self.simulation_label.width()
            label_h = self.simulation_label.height()
            
            self.simulation_label.move(
                (canvas_width - label_w) // 2,
                (canvas_height - label_h) // 2
            )
        except RuntimeError:
            pass
