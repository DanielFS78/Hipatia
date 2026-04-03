# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`camera_selector_panel`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtCore import pyqtSignal
from typing import List, Optional
from core.dtos import CameraConfigDTO

class CameraSelectorPanel(QGroupBox):
    """
    Panel para la selección y detección de cámaras.
    """
    camera_selected_signal = pyqtSignal(object) # Emite CameraConfigDTO o None
    redetect_requested_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("📹 Cámaras Detectadas (Sondeo Rápido)", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        camera_select_layout = QHBoxLayout()
        camera_label = QLabel("Seleccionar cámara:")
        camera_label.setMinimumWidth(120)

        self.camera_combo = QComboBox()
        self.camera_combo.setMinimumHeight(35)
        self.camera_combo.currentIndexChanged.connect(self._on_selection_changed)

        camera_select_layout.addWidget(camera_label)
        camera_select_layout.addWidget(self.camera_combo, 1)
        layout.addLayout(camera_select_layout)

        self.detect_btn = QPushButton("🔄 Volver a Sondear")
        self.detect_btn.setMinimumHeight(35)
        self.detect_btn.clicked.connect(self.redetect_requested_signal.emit)
        self.detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; border: none;
                padding: 8px 15px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        layout.addWidget(self.detect_btn)

    def set_loading(self, message: str = "🔄 Sondeando...") -> None:
        """Muestra estado de carga en el combo."""
        self.camera_combo.clear()
        self.camera_combo.addItem(message, None)
        self.detect_btn.setEnabled(False)

    def update_cameras(self, cameras: List[CameraConfigDTO], current_index: int) -> None:
        """Puebla el combo con la lista de cámaras y selecciona la actual."""
        self.camera_combo.blockSignals(True)
        self.camera_combo.clear()
        
        if not cameras:
            self.camera_combo.addItem("❌ No se encontraron cámaras", None)
        else:
            for cam in cameras:
                text = f"📹 {cam.name}"
                if cam.is_external:
                    text += " [USB EXTERNA]"
                else:
                    text += " [Integrada]"
                self.camera_combo.addItem(text, cam)
            
            # Seleccionar actual
            for i in range(self.camera_combo.count()):
                cam_dto = self.camera_combo.itemData(i)
                if isinstance(cam_dto, CameraConfigDTO) and cam_dto.index == current_index:
                    self.camera_combo.setCurrentIndex(i)
                    break

        self.camera_combo.blockSignals(False)
        self.detect_btn.setEnabled(True)
        self._on_selection_changed()

    def _on_selection_changed(self) -> None:
        """Emite la señal con el DTO seleccionado."""
        data = self.camera_combo.currentData()
        self.camera_selected_signal.emit(data if isinstance(data, CameraConfigDTO) else None)

    def get_selected_camera(self) -> Optional[CameraConfigDTO]:
        """Devuelve el DTO seleccionado actualmente."""
        data = self.camera_combo.currentData()
        return data if isinstance(data, CameraConfigDTO) else None
