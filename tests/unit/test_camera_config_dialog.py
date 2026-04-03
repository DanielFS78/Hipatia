# -*- coding: utf-8 -*-
"""
Tests for CameraConfigDialog following the AAA pattern and strict testing guidelines.
"""
import pytest
from unittest.mock import ANY, MagicMock, patch
from PyQt6.QtWidgets import QDialog, QMessageBox, QApplication

from ui.worker.camera_config_dialog import CameraConfigDialog
from core.camera_manager import CameraManager, CameraInfo, CameraBackend
from core.dtos import ConfigurationDTO, CameraConfigDTO, CameraDetailDTO

@pytest.fixture
def mock_camera_manager():
    manager = MagicMock(spec=CameraManager)
    
    def create_mock_cam(idx, name, is_working=True):
        cam = MagicMock(spec=CameraInfo)
        # El presenter usa estos atributos para mapear al DTO
        cam.configure_mock(
            index=idx, name=name, is_working=is_working,
            is_external=(idx == 1), width=640 if is_working else 0,
            height=480 if is_working else 0, fps=30.0 if is_working else 0.0,
            backend="AUTO", error_message=None if is_working else "Error"
        )
        return cam

    # Setup default returns
    manager.detect_cameras.return_value = [create_mock_cam(0, "Cam 1"), create_mock_cam(1, "Cam 2")]
    manager.get_camera_info.side_effect = lambda idx: create_mock_cam(idx, f"Cam {idx+1}")
    manager.test_camera_with_preview.return_value = True
    manager.validate_camera.return_value = (True, "")
    return manager

@pytest.fixture
def dialog(qtbot, mock_camera_manager):
    dlg = CameraConfigDialog(mock_camera_manager, current_camera_index=1)
    qtbot.addWidget(dlg)
    # Carga manual para evitar asincronía de QTimer
    dlg._load_cameras()
    return dlg

@pytest.mark.unit
class TestCameraConfigDialogInitAndLoad:
    
    def test_init_sets_up_ui(self, mock_camera_manager, qtbot):
        dlg = CameraConfigDialog(mock_camera_manager, current_camera_index=0)
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() == "⚙️ Configuración de Cámara QR (Optimizado)"
        
    def test_load_cameras_success(self, dialog):
        assert dialog.selector_panel.camera_combo.count() == 2
        selected_cam = dialog.selector_panel.get_selected_camera()
        assert selected_cam.index == 1

@pytest.mark.unit
class TestCameraConfigDialogSelections:
    
    def test_camera_selection_changed_valid_camera(self, dialog):
        cam_dto = dialog.selector_panel.get_selected_camera()
        dialog._on_camera_selection_changed(cam_dto)
        assert "Cámara actual guardada" in dialog.info_panel.info_label.text()

@pytest.mark.unit
class TestCameraConfigDialogActionButtons:
    
    def test_on_test_camera_success(self, dialog, mock_camera_manager):
        heavy_cam = MagicMock(spec=CameraInfo)
        heavy_cam.configure_mock(index=1, name="Cam 2", width=1280, height=720, is_working=True, backend="AUTO", fps=30.0, error_message=None)
        mock_camera_manager.get_camera_info.side_effect = None
        mock_camera_manager.get_camera_info.return_value = heavy_cam
        
        with patch("ui.worker.camera_config_dialog.QMessageBox.information") as mock_msg:
            dialog._on_test_camera()
            assert mock_msg.called
            assert "Hardware validado" in dialog.info_panel.info_label.text()

    def test_on_test_camera_failure(self, dialog, mock_camera_manager):
        mock_camera_manager.test_camera_with_preview.return_value = False
        heavy_cam = MagicMock(spec=CameraInfo)
        heavy_cam.configure_mock(index=1, name="Cam 2", is_working=False, error_message="No signal", width=0, height=0, fps=0.0, backend="AUTO")
        mock_camera_manager.get_camera_info.side_effect = None
        mock_camera_manager.get_camera_info.return_value = heavy_cam
        
        with patch("ui.worker.camera_config_dialog.QMessageBox.warning") as mock_msg:
            dialog._on_test_camera()
            assert mock_msg.called
            assert "No signal" in dialog.info_panel.info_label.text()

    def test_on_save_clicked_success(self, dialog, mock_camera_manager):
        mock_info = MagicMock(spec=CameraInfo)
        mock_info.configure_mock(index=1, name="Cam 2", is_working=True, width=1280, height=720, fps=30.0, backend="AUTO", error_message=None)
        mock_camera_manager.get_camera_info.side_effect = None
        mock_camera_manager.get_camera_info.return_value = mock_info
        
        with patch.object(dialog, 'accept', autospec=True) as mock_accept:
            dialog.save_btn.click()
            assert mock_accept.called
