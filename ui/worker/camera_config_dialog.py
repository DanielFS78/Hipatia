# -*- coding: utf-8 -*-
"""
Nombre del Módulo: camera_config_dialog

Descripción: Diálogo modal de configuración de cámara QR para la vista trabajador: selector,
             panel de detalle y ``CameraConfigPresenter`` sobre ``CameraManager``.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMessageBox, QWidget, QApplication
)
from PyQt6.QtCore import QTimer

from core.camera_manager import CameraManager
from core.dtos import CameraConfigDTO, CameraDetailDTO
from ui.worker.camera_config_presenter import CameraConfigPresenter
from ui.widgets.worker.camera_selector_panel import CameraSelectorPanel
from ui.widgets.worker.camera_info_panel import CameraInfoPanel

class CameraConfigDialog(QDialog):
    """Configuración de cámara con presenter y paneles reutilizables."""

    def __init__(self, camera_manager: CameraManager, current_camera_index: int, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.presenter = CameraConfigPresenter(camera_manager)
        self.current_camera_index = current_camera_index
        self.logger = logging.getLogger("EvolucionTiemposApp.CameraConfigDialog")

        self.setWindowTitle("⚙️ Configuración de Cámara QR (Optimizado)")
        self.setModal(True)
        self.setMinimumWidth(550)
        self.setMaximumWidth(700)

        self._setup_ui()
        self._connect_signals()

        QTimer.singleShot(50, self._load_cameras)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("🎥 Configuración de Cámara QR")
        title_font = title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        description_label = QLabel(
            "Aquí puedes cambiar la cámara que utiliza el sistema.\n"
            "La lista se carga al instante. Usa 'Probar Cámara' para validar el hardware."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(description_label)

        # Paneles Extraídos
        self.selector_panel = CameraSelectorPanel(self)
        self.info_panel = CameraInfoPanel(self)
        layout.addWidget(self.selector_panel)
        layout.addWidget(self.info_panel)

        # Botones de Acción
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.test_btn = QPushButton("🎬 Probar Cámara (Validar Hardware)")
        self.test_btn.setMinimumHeight(40)
        self.test_btn.clicked.connect(self._on_test_camera)
        self.test_btn.setEnabled(False)
        self.test_btn.setStyleSheet(self._get_btn_style("#9b59b6", "#8e44ad"))

        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(self._get_btn_style("#95a5a6", "#7f8c8d"))

        self.save_btn = QPushButton("✅ Guardar y Usar")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet(self._get_btn_style("#27ae60", "#229954"))

        buttons_layout.addWidget(self.test_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(self.save_btn)
        layout.addLayout(buttons_layout)

    def _get_btn_style(self, main_color: str, hover_color: str) -> str:
        return f"""
            QPushButton {{
                background-color: {main_color}; color: white; border: none;
                padding: 10px 20px; border-radius: 5px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {hover_color}; }}
            QPushButton:disabled {{ background-color: #95a5a6; }}
        """

    def _connect_signals(self) -> None:
        self.selector_panel.camera_selected_signal.connect(self._on_camera_selection_changed)
        self.selector_panel.redetect_requested_signal.connect(self._load_cameras)

    def _load_cameras(self) -> None:
        self.selector_panel.set_loading()
        self.info_panel.update_info(None, "Sondeando índices de cámara...", "warning")
        self.repaint()
        QApplication.processEvents()

        cameras = self.presenter.detect_cameras_light()
        self.selector_panel.update_cameras(cameras, self.current_camera_index)
        
        self.test_btn.setEnabled(len(cameras) > 0)
        self.save_btn.setEnabled(len(cameras) > 0)

    def _on_camera_selection_changed(self, cam_dto: Optional[CameraConfigDTO]) -> None:
        if not cam_dto:
            self.info_panel.update_info(None, f"Cámara actual guardada: {self.current_camera_index}\nSelecciona una cámara para validar.")
            return

        detail = self.presenter.get_camera_detail(cam_dto.index)
        self.info_panel.update_info(
            detail, 
            f"Cámara actual guardada: {self.current_camera_index}\nPulsa 'Probar Cámara' para validar hardware."
        )

    def _on_test_camera(self) -> None:
        cam_dto = self.selector_panel.get_selected_camera()
        if not cam_dto: return

        self._set_ui_enabled(False)
        self.info_panel.update_info(None, "Validando hardware (leyendo frames)... Por favor, espera.", "info")
        self.repaint()
        QApplication.processEvents()

        success, detail = self.presenter.test_camera(cam_dto.index)
        self._set_ui_enabled(True)

        if success and detail:
            QMessageBox.information(self, "✅ Prueba Exitosa", f"Cámara {detail.index} OK.\nResolución: {detail.width}x{detail.height}")
            self.info_panel.update_info(detail, "¡Hardware validado con éxito!", "success")
        else:
            msg = detail.error_message if detail else "Error desconocido."
            QMessageBox.warning(self, "❌ Error en Prueba", f"Fallo en cámara {cam_dto.index}: {msg}")
            self.info_panel.update_info(None, f"Fallo en la validación: {msg}", "error")

    def _on_save_clicked(self) -> None:
        cam_dto = self.selector_panel.get_selected_camera()
        if not cam_dto: return

        self._set_ui_enabled(False)
        self.info_panel.update_info(None, "Validando hardware antes de guardar...", "info")
        self.repaint()
        QApplication.processEvents()

        success, error_msg, detail = self.presenter.validate_before_save(cam_dto.index)
        self._set_ui_enabled(True)

        if not success:
            QMessageBox.critical(self, "Error de Validación", f"No se puede guardar: {error_msg}")
            self.info_panel.update_info(None, f"Fallo de validación: {error_msg}", "error")
            return

        self.logger.info(f"Guardando selección: Cámara {cam_dto.index}")
        self.accept()

    def _set_ui_enabled(self, enabled: bool) -> None:
        self.test_btn.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.selector_panel.detect_btn.setEnabled(enabled)
        self.selector_panel.camera_combo.setEnabled(enabled)

    def get_selected_camera(self) -> Optional[int]:
        cam_dto = self.selector_panel.get_selected_camera()
        return cam_dto.index if cam_dto else None