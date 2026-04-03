# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`flow_display_panel`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, QFrame, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Any, List
from ui.widgets.production_flow.flow_item_widget import FlowItemWidget

class FlowDisplayPanel(QFrame):
    """
    Panel derecho de DefineProductionFlowDialog.
    Gestiona la visualización de la secuencia de tareas y las acciones sobre el flujo.
    """
    edit_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    assign_workers_requested = pyqtSignal(int)
    group_selected_requested = pyqtSignal()
    save_flow_requested = pyqtSignal()

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.flow_item_widgets: List[FlowItemWidget] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("<b>Pila de Producción (Secuencia de Tareas)</b>"))
        
        # Acciones globales del flujo
        flow_actions_layout = QHBoxLayout()
        self.group_steps_button = QPushButton("🔗 Agrupar Tareas Seleccionadas")
        self.group_steps_button.clicked.connect(self.group_selected_requested.emit)
        flow_actions_layout.addStretch()
        flow_actions_layout.addWidget(self.group_steps_button)
        layout.addLayout(flow_actions_layout)

        # Área de scroll para los pasos
        flow_scroll = QScrollArea()
        flow_scroll.setWidgetResizable(True)
        self.flow_display_widget = QWidget()
        self.flow_display_layout = QVBoxLayout(self.flow_display_widget)
        self.flow_display_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        flow_scroll.setWidget(self.flow_display_widget)
        layout.addWidget(flow_scroll)

        # Botón de guardado rápido
        self.save_flow_button = QPushButton("💾 Guardar Flujo (sin calcular)")
        self.save_flow_button.setStyleSheet("background-color: #28a745; color: white; padding: 5px;")
        self.save_flow_button.clicked.connect(self.save_flow_requested.emit)
        layout.addWidget(self.save_flow_button)

    def update_display(self, flow: List[Any], presenter: Any) -> None:
        """Refresca la visualización de la lista de pasos."""
        # Limpiar layout
        while self.flow_display_layout.count():
            child = self.flow_display_layout.takeAt(0)
            if child:
                child_widget = child.widget()
                if child_widget:
                    child_widget.deleteLater()
        self.flow_item_widgets = []

        if not flow:
            self.flow_display_layout.addWidget(QLabel("Añada pasos desde el panel izquierdo..."))
            return

        for i in range(len(flow)):
            vm = presenter.get_step_view_model(i)
            widget = FlowItemWidget(vm, self.flow_display_widget)
            
            # Conectar señales del componente individual al panel
            widget.edit_requested.connect(self.edit_requested.emit)
            widget.delete_requested.connect(self.delete_requested.emit)
            widget.assign_workers_requested.connect(self.assign_workers_requested.emit)
            
            self.flow_display_layout.addWidget(widget)
            self.flow_item_widgets.append(widget)

    def get_selected_indices(self) -> List[int]:
        """Retorna los índices de los pasos seleccionados mediante checkbox."""
        return [i for i, w in enumerate(self.flow_item_widgets) if w.is_selected()]
