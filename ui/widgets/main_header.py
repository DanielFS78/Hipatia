# -*- coding: utf-8 -*-
"""
Nombre del Módulo: main_header

Descripción: Define protocolos o tipos principales: ``MainHeader``. Widget de cabecera que contiene el botón de auto-ajuste de escala. Integración típica con: ``PyQt6``.
"""
from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QFrame, QPushButton
)

class MainHeader(QFrame):
    """
    Widget de cabecera que contiene el botón de auto-ajuste de escala.
    """
    
    # Señal emitida cuando el usuario solicita un ajuste automático de UI
    auto_adjust_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Inicializa la cabecera y sus componentes."""
        super().__init__(parent)
        self.setFixedHeight(45)
        self.setStyleSheet("background-color: #ecf0f1; border-bottom: 1px solid #bdc3c7;")
        self._init_ui()

    def _init_ui(self) -> None:
        """Crea el layout de la cabecera y el botón de auto-ajuste."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 20, 5)
        layout.addStretch()

        self.btn_auto_ajustar = QPushButton("📐 Auto Ajustar UI")
        self.btn_auto_ajustar.setToolTip(
            "Recalcula el tamaño de la interfaz gráfica si se ve cortada en pantallas pequeñas."
        )
        self.btn_auto_ajustar.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; border: none;
                padding: 6px 15px; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.btn_auto_ajustar.clicked.connect(self.auto_adjust_requested.emit)
        layout.addWidget(self.btn_auto_ajustar)
