# -*- coding: utf-8 -*-
"""
Nombre del Módulo: flow_toolbar

Descripción: Barra inferior del planificador visual: limpiar, cargar, guardar y calcular (señales Qt).
"""
from __future__ import annotations

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QFrame
)
from PyQt6.QtCore import pyqtSignal

class FlowToolbarWidget(QFrame):
    """
    Barra de herramientas inferior para el Planificador Visual de Producción.
    Gestiona las acciones principales (limpiar, cargar, guardar, calcular).
    """
    clear_requested = pyqtSignal()
    load_requested = pyqtSignal()
    save_requested = pyqtSignal()
    calculate_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet("""
            FlowToolbarWidget {
                background-color: #f0f0f0; 
                border-top: 1px solid #ccc;
            }
            QPushButton {
                padding: 5px 15px;
                border-radius: 4px;
            }
        """)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.clear_button = QPushButton("🗑 Limpiar Canvas")
        self.clear_button.clicked.connect(self.clear_requested.emit)
        
        self.load_button = QPushButton("📂 Cargar Pila")
        self.load_button.clicked.connect(self.load_requested.emit)
        
        self.save_button = QPushButton("💾 Guardar Pila")
        self.save_button.setStyleSheet("background-color: #17a2b8; color: white;")
        self.save_button.clicked.connect(self.save_requested.emit)
        
        self.calc_button = QPushButton("🧮 Calcular Manualmente")
        self.calc_button.clicked.connect(self.calculate_requested.emit)

        layout.addWidget(self.clear_button)
        layout.addWidget(self.load_button)
        layout.addWidget(self.save_button)
        layout.addStretch()
        layout.addWidget(self.calc_button)

    def set_buttons_enabled(self, enabled: bool) -> None:
        """Habilita o deshabilita los botones de la barra."""
        for btn in [self.clear_button, self.load_button, self.save_button, self.calc_button]:
            btn.setEnabled(enabled)
