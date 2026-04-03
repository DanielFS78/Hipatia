"""
Interfaz PyQt6 (`cycle_end_config_dialog`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.flow_canvas_io import (
    canvas_task_display_name,
    flow_task_config_cycle_return_to_index,
    flow_task_config_is_cycle_end_flag,
    legacy_canvas_task_config,
    legacy_canvas_task_is_cycle_start,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class CycleEndConfigDialog(QDialog):
    """
    Diálogo para configurar el fin de ciclo de una tarea.
    Permite seleccionar a qué tarea de inicio de ciclo regresar.
    """

    def __init__(
        self,
        current_task_index: int,
        all_canvas_tasks: List[Dict[str, Any]],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.current_task_index = current_task_index
        self.all_canvas_tasks = all_canvas_tasks
        self.selected_return_index = None

        self.current_return_index_from_config = None
        self.is_currently_marked_as_end = False
        if 0 <= self.current_task_index < len(self.all_canvas_tasks):
            current_config = legacy_canvas_task_config(
                self.all_canvas_tasks[self.current_task_index]
            )
            self.current_return_index_from_config = flow_task_config_cycle_return_to_index(
                current_config
            )
            self.is_currently_marked_as_end = flow_task_config_is_cycle_end_flag(current_config)

        self.setWindowTitle("Configurar Fin de Ciclo")
        self.setModal(True)
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("🔄 <b>Configuración de Fin de Ciclo</b>")
        title.setStyleSheet("font-size: 16px; color: #28a745;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        explanation = QLabel(
            "Al completar un ciclo en esta tarea, el programa regresará\n"
            "a la tarea seleccionada para iniciar el siguiente ciclo.\n\n"
            "Seleccione la tarea a la que desea regresar:"
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(explanation)

        self.tasks_list = QListWidget()
        self.tasks_list.setStyleSheet(
            """
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
                border: 2px solid #0056b3;
                border-radius: 3px;
            }
            QListWidget::item:hover { background-color: #e9ecef; }
            QListWidget::item { padding: 8px; margin: 2px; }
            """
        )
        self.tasks_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        no_return_item = QListWidgetItem("➡️ (No regresar a ninguna tarea específica)")
        no_return_item.setData(Qt.ItemDataRole.UserRole, None)
        no_return_item.setForeground(Qt.GlobalColor.gray)
        no_return_item.setFont(QFont("Segoe UI", 10, italic=True))
        self.tasks_list.addItem(no_return_item)

        cycle_start_indices = set()
        for i, task in enumerate(self.all_canvas_tasks):
            if i == self.current_task_index:
                continue
            is_cycle_start = legacy_canvas_task_is_cycle_start(task)
            task_name = canvas_task_display_name(task, "Tarea Desconocida")
            if is_cycle_start:
                item = QListWidgetItem(f"⭐ {task_name} (Inicio de Ciclo)")
                item.setData(Qt.ItemDataRole.UserRole, i)
                font = QFont("Segoe UI", 10)
                font.setBold(True)
                item.setFont(font)
                item.setForeground(Qt.GlobalColor.darkYellow)
                item.setToolTip(
                    "Esta es una tarea de Inicio de Ciclo.\n"
                    "Es el punto natural de retorno para ciclos repetitivos."
                )
                self.tasks_list.addItem(item)
                cycle_start_indices.add(i)

        for i, task in enumerate(self.all_canvas_tasks):
            if i == self.current_task_index or i in cycle_start_indices:
                continue
            task_name = canvas_task_display_name(task, "Tarea Desconocida")
            item = QListWidgetItem(f"📋 {task_name}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.tasks_list.addItem(item)

        layout.addWidget(self.tasks_list)
        current_name = "Ninguna"
        item_to_select = no_return_item
        if self.current_return_index_from_config is not None:
            if 0 <= self.current_return_index_from_config < len(self.all_canvas_tasks):
                current_name = canvas_task_display_name(
                    self.all_canvas_tasks[self.current_return_index_from_config],
                    "Desconocida",
                )
                for i in range(self.tasks_list.count()):
                    list_item: Optional[QListWidgetItem] = self.tasks_list.item(i)
                    if list_item and list_item.data(Qt.ItemDataRole.UserRole) == self.current_return_index_from_config:
                        item_to_select = list_item
                        break

        info_label = QLabel(f"✅ Actualmente configurado para regresar a: <b>{current_name}</b>")
        info_label.setStyleSheet("background-color: #d1ecf1; padding: 5px; border-radius: 3px; color: #0c5460;")
        layout.addWidget(info_label)
        self.tasks_list.setCurrentItem(item_to_select)

        self.mark_as_end_checkbox = QCheckBox("🏁 Marcar esta tarea como Fin de Ciclo")
        self.mark_as_end_checkbox.setStyleSheet("font-weight: bold; color: #28a745;")
        self.mark_as_end_checkbox.setChecked(self.is_currently_marked_as_end)
        layout.addWidget(self.mark_as_end_checkbox)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_configuration(self) -> Dict[str, Any]:
        selected_items = self.tasks_list.selectedItems()
        return_index = None
        if selected_items:
            return_index = selected_items[0].data(Qt.ItemDataRole.UserRole)
        return {"is_cycle_end": self.mark_as_end_checkbox.isChecked(), "return_to_index": return_index}

