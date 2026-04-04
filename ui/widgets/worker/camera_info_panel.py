# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`camera_info_panel`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from PyQt6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget
from typing import Optional
from core.dtos import CameraDetailDTO

class CameraInfoPanel(QGroupBox):
    """
    Panel para mostrar información detallada y estados de validación.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("ℹ️ Información y Validación de Hardware", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.info_label = QLabel("Seleccione una cámara para ver detalles.")
        self.info_label.setWordWrap(True)
        self.info_label.setMinimumHeight(80)
        self._set_style("info")
        layout.addWidget(self.info_label)

    def update_info(self, detail: Optional[CameraDetailDTO], message: str = "", level: str = "info") -> None:
        """Actualiza el texto y estilo del panel."""
        text = ""
        if detail:
            text = f"ℹ️ Cámara {detail.index} ({detail.name})\n"
            if detail.is_working:
                text += f"Resolución: {detail.width}x{detail.height} @ {detail.fps:.0f} FPS\n"
                text += f"Backend: {detail.backend}\n"
        
        if message:
            text += f"\n{message}" if text else message
            
        self.info_label.setText(text if text else "Sin información disponible.")
        self._set_style(level)

    def _set_style(self, level: str) -> None:
        if level == "error":
            style = "padding: 10px; background-color: #ffe6e6; border-radius: 5px; color: #c0392b;"
        elif level == "success":
            style = "padding: 10px; background-color: #d5f4e6; border-radius: 5px; color: #27ae60;"
        elif level == "warning":
            style = "padding: 10px; background-color: #fef9e7; border-radius: 5px; color: #f39c12;"
        else: # info
            style = "padding: 10px; background-color: #ecf0f1; border-radius: 5px; color: #34495e;"
        
        self.info_label.setStyleSheet(style)
