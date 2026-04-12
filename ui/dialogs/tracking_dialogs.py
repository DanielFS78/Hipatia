# -*- coding: utf-8 -*-
"""
Nombre del Módulo: tracking_dialogs
Descripción: Diálogos auxiliares de trazabilidad y arranque de sesión de producción (orden y cantidad).

Formularios simples reutilizados desde controladores de fabricación o seguimiento.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QSpinBox, 
    QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt
from typing import Any

class OrderSetupDialog(QDialog):
    """
    Solicita número de orden de fabricación (O.F.) y cantidad total al iniciar una serie de producción.
    """
    def __init__(self, parent: Any = None, default_order: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("Iniciar Nueva Producción")
        self.setModal(True)
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        # Header Info
        info_label = QLabel("Se ha detectado el inicio de una nueva serie.\nPor favor, configure los datos del pedido:")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # Form
        form_layout = QFormLayout()
        
        self.order_input = QLineEdit()
        self.order_input.setText(default_order)
        self.order_input.setPlaceholderText("Ej: OF-2024-001")
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 99999)
        self.quantity_spin.setValue(100)  # Default value
        
        form_layout.addRow("Nº Orden Fabricación:", self.order_input)
        form_layout.addRow("Cantidad Total:", self.quantity_spin)
        
        layout.addLayout(form_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> dict[str, Any]:
        return {
            "order_number": self.order_input.text().strip().upper(),
            "total_units": self.quantity_spin.value()
        }
