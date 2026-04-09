# -*- coding: utf-8 -*-
"""
Diálogo para añadir iteración de producto (PyQt6).

``AddIterationFormData`` concentra los campos del formulario; el widget de iteraciones
pasa ``asdict(form)`` al controlador para mantener la firma histórica basada en dict.
"""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QDialogButtonBox, QLabel,
    QComboBox, QTextEdit, QFileDialog, QWidget
)

from PyQt6.QtCore import Qt


@dataclass(frozen=True)
class AddIterationFormData:
    """Valores del formulario de nueva iteración (frontera tipada frente a dict opaco)."""

    responsable: str
    descripcion: str
    tipo_fallo: str
    ruta_plano_origen: Optional[str]


class AddIterationDialog(QDialog):
    """Diálogo para añadir una nueva iteración con todos los campos requeridos."""

    def __init__(self, product_code: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Añadir Nueva Iteración")
        self.setMinimumWidth(500)
        self.product_code = product_code
        self.attached_plano_path: Optional[str] = None

        self.main_layout = QFormLayout(self)
        self.responsable_edit = QLineEdit()
        self.tipo_fallo_combo = QComboBox()
        self.tipo_fallo_combo.addItems([
            "No especificado",
            "Fallo de Proveedor",
            "Fallo de Producción",
            "Mejora de Diseño",
            "Observación de Cliente"
        ])
        self.description_edit = QTextEdit()

        plano_layout = QHBoxLayout()
        self.plano_label = QLabel("Ningún plano adjunto.")
        attach_plano_button = QPushButton("Adjuntar Plano...")
        attach_plano_button.clicked.connect(self._attach_plano)
        plano_layout.addWidget(self.plano_label)
        plano_layout.addWidget(attach_plano_button)

        self.main_layout.addRow("<b>Responsable:</b>", self.responsable_edit)
        self.main_layout.addRow("<b>Categoría:</b>", self.tipo_fallo_combo)
        self.main_layout.addRow("<b>Descripción del Cambio:</b>", self.description_edit)
        self.main_layout.addRow("<b>Plano (Opcional):</b>", plano_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addRow(self.buttons)

    def _attach_plano(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Plano", "",
                                                   "Archivos PDF (*.pdf);;Todos los archivos (*.*)")
        if file_path:
            self.attached_plano_path = file_path
            self.plano_label.setText(os.path.basename(file_path))

    def get_data(self) -> AddIterationFormData:
        return AddIterationFormData(
            responsable=self.responsable_edit.text().strip(),
            descripcion=self.description_edit.toPlainText().strip(),
            tipo_fallo=self.tipo_fallo_combo.currentText(),
            ruta_plano_origen=self.attached_plano_path,
        )


