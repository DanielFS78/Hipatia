"""
Interfaz PyQt6 (`flow_item_widget`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QCheckBox, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.dtos import FlowItemDTO

class FlowItemWidget(QFrame):
    """
    Widget especializado para representar un paso individual o un grupo 
    en la lista de la pila de producción.
    """
    edit_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    assign_workers_requested = pyqtSignal(int)
    selection_changed = pyqtSignal(int, bool)

    def __init__(self, view_model: FlowItemDTO, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.index = view_model.index
        self.is_group = view_model.is_group
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        if self.is_group:
            self.setObjectName("FlowGroup")
            self.setStyleSheet("QFrame#FlowGroup { border: 2px solid #3498db; border-radius: 5px; background-color: #f7fbfe; }")
        else:
            self.setObjectName("FlowStep")
            self.setStyleSheet("QFrame#FlowStep { border: 1px solid #ddd; border-radius: 4px; padding: 2px; }")

        self._init_ui(view_model)

    def _init_ui(self, vm: FlowItemDTO) -> None:
        if self.is_group:
            self._init_group_ui(vm)
        else:
            self._init_step_ui(vm)

    def _init_step_ui(self, vm: FlowItemDTO) -> None:
        layout = QHBoxLayout(self)
        
        self.checkbox = QCheckBox()
        self.checkbox.toggled.connect(lambda checked: self.selection_changed.emit(self.index, checked))
        layout.addWidget(self.checkbox)

        info_layout = QVBoxLayout()
        title_label = QLabel(f"<b>{vm.title}</b>")
        info_layout.addWidget(title_label)
        
        info_layout.addWidget(QLabel(f"Máquina: {vm.machine}"))
        info_layout.addWidget(QLabel(f"Trabajadores: {vm.workers}"))
        info_layout.addWidget(QLabel(f"<i>{vm.condition}</i>"))
        
        layout.addLayout(info_layout)
        layout.addStretch()

        btn_layout = QVBoxLayout()
        edit_btn = QPushButton("✎ Editar")
        delete_btn = QPushButton("🗑 Eliminar")
        
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.index))
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.index))
        
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()

    def _init_group_ui(self, vm: FlowItemDTO) -> None:
        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        info_label = QLabel(
            f"<b>{vm.title}</b><br>"
            f"<small>Trabajadores: {vm.workers}</small><br>"
            f"<small>{vm.cycle_info}</small>"
        )
        assign_btn = QPushButton("👥 Operarios")
        assign_btn.setFixedWidth(100)
        assign_btn.clicked.connect(lambda: self.assign_workers_requested.emit(self.index))

        header_layout.addWidget(info_label)
        header_layout.addStretch()
        header_layout.addWidget(assign_btn)
        layout.addLayout(header_layout)

        # Línea divisoria
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Lista de tareas
        for task_name in vm.tasks_names:
            task_label = QLabel(f" • {task_name}")
            task_label.setStyleSheet("color: #555; margin-left:10px;")
            layout.addWidget(task_label)
            
    def is_selected(self) -> bool:
        """Retorna si el checkbox está marcado (solo para pasos individuales)."""
        if not self.is_group and hasattr(self, 'checkbox'):
            return self.checkbox.isChecked()
        return False
