# -*- coding: utf-8 -*-
"""
Nombre del Módulo: library_panel

Descripción: Biblioteca de tareas por producto (árbol) para arrastrar plantillas al canvas del flujo.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QFrame,
    QPushButton, QHBoxLayout, QTreeWidgetItemIterator
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPalette, QBrush, QColor
from typing import Any

from core.dtos import FlowTaskDataDTO, ProductFlowLibraryProductDTO
from core.utils.helpers import resource_path

class TaskLibraryPanel(QWidget):
    """
    Panel lateral que muestra la biblioteca de tareas disponibles agrupadas por producto.
    Permite arrastrar tareas al canvas.
    """
    
    task_requested = pyqtSignal(object)  # FlowTaskDataDTO (o dict legado en transición)

    def __init__(
        self,
        task_data_by_product: dict[str, ProductFlowLibraryProductDTO],
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self.task_data_by_product = task_data_by_product
        
        # Estado
        self.tasks_in_canvas_ids: set[Any] = set() # Para marcado visual
        
        self._init_ui()
        self.populate_tasks()

    def _init_ui(self) -> None:
        # Panel principal con marco
        self.start_layout = QVBoxLayout(self)
        self.start_layout.setContentsMargins(0, 0, 0, 0)
        
        self.content_frame = QFrame()
        self.content_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.content_frame.setMinimumWidth(250)
        self.content_frame.setMaximumWidth(350)
        
        layout = QVBoxLayout(self.content_frame)
        
        # Título
        title = QLabel("<b>📚 Biblioteca de Tareas</b>")
        layout.addWidget(title)
        
        # Árbol de tareas
        self.task_tree = QTreeWidget()
        self.task_tree.setDragEnabled(True)
        self.task_tree.setHeaderLabel("Arrastra una tarea al canvas")
        self.task_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.task_tree)
        
        self.start_layout.addWidget(self.content_frame)

    def _on_item_double_clicked(self, item: Any, column: int) -> None:
        """Maneja el doble clic para emitir la señal con los datos de la tarea."""
        # Solo actuar si el item tiene padre (es una tarea, no una categoría)
        if item.parent():
            task_data = item.data(0, Qt.ItemDataRole.UserRole)
            if task_data:
                self.task_requested.emit(task_data)

    def populate_tasks(self) -> None:
        """Rellena el árbol con los datos de tareas agrupados por producto."""
        self.task_tree.clear()
        
        for product_code, product_info in self.task_data_by_product.items():
            product_item = QTreeWidgetItem(
                self.task_tree, [f"{product_info.descripcion} ({product_code})"]
            )
            product_item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
            
            for task in product_info.tasks:
                task_item_text = f"{task.name} ({task.duration:.2f} min)"
                task_item = QTreeWidgetItem(product_item, [task_item_text])
                task_item.setData(0, Qt.ItemDataRole.UserRole, task)
                
                # Intentar cargar icono (opcional, sin crashear si falla)
                # En una app real, gestionariamos recursos mejor
                try:
                    task_item.setIcon(0, QIcon(resource_path("resources/icon.ico")))
                except Exception:
                    pass
            
            product_item.setExpanded(True)
            
        self.update_visual_state()

    def set_canvas_tasks(self, canvas_task_ids: list[Any]) -> None:
        """
        Actualiza la lista de IDs de tareas que están en el canvas para dar feedback visual.
        """
        self.tasks_in_canvas_ids = set(canvas_task_ids)
        self.update_visual_state()

    def update_visual_state(self) -> None:
        """
        Colorea las tareas que ya están en el canvas.
        """
        if not self.task_tree: return

        default_text_color = self.palette().color(QPalette.ColorRole.Text)
        canvas_marker_color = QColor("#f0ad4e")  # Naranja

        for i in range(self.task_tree.topLevelItemCount()):
            cat_item = self.task_tree.topLevelItem(i)
            if cat_item is None: continue
            for j in range(cat_item.childCount()):
                task_item = cat_item.child(j)
                if task_item is None: continue
                task_data = task_item.data(0, Qt.ItemDataRole.UserRole)
                task_id = task_data.id if isinstance(task_data, FlowTaskDataDTO) else None
                
                # Reset
                font = task_item.font(0)
                font.setStrikeOut(False)
                task_item.setFont(0, font)
                task_item.setForeground(0, default_text_color)
                
                if task_id in self.tasks_in_canvas_ids:
                    font.setStrikeOut(True)
                    task_item.setFont(0, font)
                    task_item.setForeground(0, canvas_marker_color)
