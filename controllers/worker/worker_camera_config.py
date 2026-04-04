# -*- coding: utf-8 -*-
"""Diálogo de configuración de cámara para la interfaz operario (controllers + ui; no features)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from PyQt6.QtWidgets import QDialog, QMessageBox, QWidget


def run_worker_camera_config_dialog(
    feature_controller: Any,
    parent: Optional[QWidget],
    logger: Optional[logging.Logger] = None,
) -> None:
    """Abre `CameraConfigDialog` y actualiza `QrScanner` en el feature controller."""
    log = logger or logging.getLogger("EvolucionTiemposApp.WorkerCameraConfig")
    try:
        import cv2

        from core.qr_scanner import QrScanner
        from controllers.ui_class_loader import ui_class

        CameraConfigDialog = ui_class("ui.worker.camera_config_dialog", "CameraConfigDialog")

        fc = feature_controller
        idx = fc.qr_scanner.camera_index if fc.qr_scanner else 0
        if idx is None:
            idx = 0
        dialog = CameraConfigDialog(fc.camera_manager, idx, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_idx = dialog.get_selected_camera()
            if new_idx is None:
                new_idx = 0
            if fc.qr_scanner:
                fc.qr_scanner.release_camera()
            cap = cv2.VideoCapture(new_idx, fc.camera_manager.get_system_backend().value)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            fc.qr_scanner = QrScanner(fc.camera_manager, new_idx, cap)
            fc.db_manager.config_repo.set_setting("camera_index", str(new_idx))
            QMessageBox.information(None, "OK", "Cámara actualizada.")
    except Exception as e:
        log.error("Error cámara: %s", e, exc_info=True)
