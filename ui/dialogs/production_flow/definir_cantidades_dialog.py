# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.production_flow.definir_cantidades_dialog
Descripción: Definición o simulación del flujo de producción (estado, presentadores, reglas y diálogos auxiliares).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.definir_cantidades_dialog_io import definir_cantidades_step_row_label
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class DefinirCantidadesDialog(QDialog):
    """
    Diálogo para definir la cantidad a producir para cada tarea/grupo.
    """

    def __init__(self, production_flow: List[Dict[str, Any]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.production_flow = production_flow
        self.spin_boxes: List[QSpinBox] = []
        self.setWindowTitle("Definir Cantidades de Producción")
        self.setMinimumSize(600, 400)
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Introduce la cantidad a fabricar para cada ítem del plan:</b>"))

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Ítem del Plan", "Cantidad a Producir"])
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setRowCount(len(self.production_flow))
        for i, step in enumerate(self.production_flow):
            task_name = definir_cantidades_step_row_label(step)

            name_item = QTableWidgetItem(task_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            spin_box = QSpinBox()
            spin_box.setRange(1, 99999)
            spin_box.setValue(1)
            self.table.setItem(i, 0, name_item)
            self.table.setCellWidget(i, 1, spin_box)
            self.spin_boxes.append(spin_box)

        layout.addWidget(self.table)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_cantidades(self) -> Dict[int, int]:
        return {i: spin_box.value() for i, spin_box in enumerate(self.spin_boxes)}

