# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.fabrication.persistence_dialogs
Descripción: Diálogo o presentador de fabricación: órdenes, preprocesos, productos y persistencia de pilas.
"""

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, 
    QDialogButtonBox, QVBoxLayout, QListWidget, 
    QListWidgetItem, QLabel, QHBoxLayout, QPushButton,
    QMessageBox
)
from PyQt6.QtCore import Qt
from typing import Tuple, List, Optional, Any, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget
    # Assuming standard tuple structure or DTO for pila
    # PilaType = Union[Tuple[int, str, Optional[str]], Any] 

class SavePilaDialog(QDialog):
    """Diálogo para pedir nombre y descripción al guardar una pila."""
    def __init__(self, parent: Optional["QWidget"] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Guardar Pila de Producción")
        self.layout_form = QFormLayout(self) # Renamed to avoid conflicts

        self.nombre_edit = QLineEdit()
        self.descripcion_edit = QTextEdit()
        self.descripcion_edit.setFixedHeight(70)

        self.layout_form.addRow("Nombre de la Pila:", self.nombre_edit)
        self.layout_form.addRow("Descripción (Opcional):", self.descripcion_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout_form.addRow(self.buttons)

    def get_data(self) -> Tuple[str, str]:
        """Retorna (nombre, descripcion)."""
        return self.nombre_edit.text().strip(), self.descripcion_edit.toPlainText().strip()


class LoadPilaDialog(QDialog):
    """Diálogo para mostrar y seleccionar pilas guardadas."""
    def __init__(self, pilas: List[Any], parent: Optional["QWidget"] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Cargar Pila de Producción")
        self.setMinimumSize(500, 400)
        self.layout_main = QVBoxLayout(self) # Renamed to avoid conflicts

        self.list_widget = QListWidget()
        for pila in pilas:
            # Soporta tanto DTOs como tuplas antiguas, si fuese necesario
            if hasattr(pila, 'nombre'):
                p_id = pila.id
                nombre = pila.nombre
                desc = pila.descripcion
            else:
                p_id, nombre, desc = pila[0], pila[1], pila[2] # Fixed indexing
            
            item = QListWidgetItem(f"{nombre}\n  └ {desc or 'Sin descripción'}")
            item.setData(Qt.ItemDataRole.UserRole, p_id) # Guardamos el ID
            self.list_widget.addItem(item)

        self.layout_main.addWidget(QLabel("Seleccione una pila para cargar o eliminar:"))
        self.layout_main.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        self.load_button = QPushButton("Cargar")
        self.delete_button = QPushButton("Eliminar")
        self.cancel_button = QPushButton("Cancelar")

        self.load_button.clicked.connect(self.accept)
        self.delete_button.clicked.connect(self._request_delete)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        self.layout_main.addLayout(button_layout)

        self.selected_id: Optional[int] = None
        self.delete_requested: bool = False

    def _request_delete(self) -> None:
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione una pila para eliminar.")
            return

        self.selected_id = current_item.data(Qt.ItemDataRole.UserRole)
        self.delete_requested = True
        self.accept()

    def get_selected_id(self) -> Optional[int]:
        """Devuelve el ID seleccionado, ya sea para cargar o eliminar."""
        if self.delete_requested:
            return self.selected_id 

        # Si no es eliminación, obtener el ID del item seleccionado
        current_item = self.list_widget.currentItem()
        if current_item:
            res = current_item.data(Qt.ItemDataRole.UserRole)
            return int(res) if res is not None else None
        return None
