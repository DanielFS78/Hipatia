"""Tests para `run_worker_camera_config_dialog` (controllers/worker)."""

from __future__ import annotations

import logging
import sys
from unittest.mock import ANY, MagicMock, patch

import pytest
from PyQt6.QtWidgets import QDialog

from controllers.worker.worker_camera_config import run_worker_camera_config_dialog

pytestmark = pytest.mark.unit


@pytest.fixture
def feature_ctrl() -> MagicMock:
    fc = MagicMock(spec=["qr_scanner", "camera_manager", "db_manager"])
    qs = MagicMock(spec=["camera_index", "release_camera"])
    qs.camera_index = 0
    qs.release_camera = MagicMock(spec=[])
    fc.qr_scanner = qs
    cm = MagicMock(spec=["get_system_backend"])
    backend = MagicMock(spec=["value"])
    backend.value = 0
    cm.get_system_backend.return_value = backend
    fc.camera_manager = cm
    db = MagicMock(spec=["config_repo"])
    db.config_repo = MagicMock(spec=["set_setting"])
    fc.db_manager = db
    return fc


def test_run_worker_camera_config_accepted_updates_scanner(feature_ctrl: MagicMock) -> None:
    previous_scanner = feature_ctrl.qr_scanner
    mock_dlg = MagicMock(spec=["exec", "get_selected_camera"])
    mock_dlg.exec.return_value = QDialog.DialogCode.Accepted
    mock_dlg.get_selected_camera.return_value = 1
    cap_instance = MagicMock(spec=["set"])
    mock_cv2 = MagicMock(spec=["VideoCapture", "CAP_PROP_FRAME_WIDTH", "CAP_PROP_FRAME_HEIGHT"])
    mock_cv2.VideoCapture = MagicMock(return_value=cap_instance)
    mock_cv2.CAP_PROP_FRAME_WIDTH = 3
    mock_cv2.CAP_PROP_FRAME_HEIGHT = 4

    with patch.dict(sys.modules, {"cv2": mock_cv2}):
        with patch("ui.worker.camera_config_dialog.CameraConfigDialog", return_value=mock_dlg):
            with patch("core.qr_scanner.QrScanner") as mock_qr_cls:
                with patch("controllers.worker.worker_camera_config.QMessageBox"):
                    run_worker_camera_config_dialog(feature_ctrl, None, logger=logging.getLogger("test"))

    previous_scanner.release_camera.assert_called_once_with()
    mock_cv2.VideoCapture.assert_called_once_with(1, 0)
    mock_qr_cls.assert_called_once_with(feature_ctrl.camera_manager, 1, cap_instance)
    feature_ctrl.db_manager.config_repo.set_setting.assert_called_once_with("camera_index", "1")


def test_run_worker_camera_config_logs_on_error(feature_ctrl: MagicMock) -> None:
    log = MagicMock(spec=logging.Logger)
    with patch(
        "ui.worker.camera_config_dialog.CameraConfigDialog",
        side_effect=RuntimeError("boom"),
    ):
        run_worker_camera_config_dialog(feature_ctrl, None, logger=log)
    log.error.assert_called_once_with("Error cámara: %s", ANY, exc_info=True)
