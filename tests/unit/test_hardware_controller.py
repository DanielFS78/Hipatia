# -*- coding: utf-8 -*-
"""
Tests unitarios para HardwareController.
Sigue los estándares estrictos de calidad de Hipatia.
"""

import pytest
import cv2
from unittest.mock import MagicMock, patch, ANY, create_autospec
from typing import Any, cast
from core.qr_scanner import QrScanner
from ui.widgets import SettingsWidget
from PyQt6.QtWidgets import QMessageBox

pytestmark = pytest.mark.unit


class DummySettingsWidget(SettingsWidget):
    """Clase dummy para simular el widget de configuración sin inicializar Qt."""
    def __init__(self):
        self.camera_combo = MagicMock(
            spec=[
                "currentData",
                "addItem",
                "clear",
                "setEnabled",
                "findData",
                "setCurrentIndex",
            ]
        )
@pytest.fixture
def mock_controller(monkeypatch, qtbot):
    """
    Fixture que proporciona una instancia de HardwareController con dependencias mockeadas.
    """
    # Mock de base de datos y repositorio con spec=object para cumplir estándares
    mock_db = MagicMock(spec=["config_repo"])
    mock_db.config_repo = MagicMock(spec=["get_setting", "set_setting"])
    
    # Mock de la vista principal
    from ui.main_window import MainView
    mock_view = create_autospec(MainView)
    
    # Setup de páginas: usar instancia real (subclase de SettingsWidget) para pasar isinstance(...)
    settings_instance = DummySettingsWidget()
    mock_view.pages = {'settings': settings_instance}
    
    # Mock de QMessageBox con spec para cumplir estándares
    mock_msg_box = MagicMock(spec=QMessageBox)
    mock_msg_box.StandardButton = QMessageBox.StandardButton
    
    # Mocks de dependencias core
    from core.camera_manager import CameraManager
    mock_cam_manager = create_autospec(CameraManager)
    
    # Usar monkeypatch para asegurar que los mocks se inyecten correctamente en el módulo
    import controllers.hardware_controller
    monkeypatch.setattr(controllers.hardware_controller, 'QMessageBox', mock_msg_box)
    
    # Mock de QrScanner con spec=True para mayor rigor
    mock_scanner_class = MagicMock(spec=["__call__"])
    monkeypatch.setattr(controllers.hardware_controller, 'QrScanner', mock_scanner_class)
    
    # Instanciar el controlador
    from controllers.hardware_controller import HardwareController
    ctrl = HardwareController(mock_db, mock_view)
    
    # Inyectar el cam_manager mockeado
    ctrl.camera_manager = mock_cam_manager
    cast(Any, ctrl).mock_scanner_class = mock_scanner_class
    cast(Any, ctrl).mock_msg_box = mock_msg_box
    
    return ctrl

@pytest.mark.unit
class TestHardwareController:
    """Escenarios de prueba para el controlador de hardware."""

    def test_initialize_qr_scanner_success(self, mock_controller):
        """Verifica la inicialización exitosa del escáner QR."""
        mock_controller.db.config_repo.get_setting.return_value = "1"
        
        cam_info = MagicMock(spec=["index", "is_working"])
        cam_info.index = 1
        cam_info.is_working = True
        mock_controller.camera_manager.get_camera_info.return_value = cam_info
        
        with patch('controllers.hardware_controller.cv2.VideoCapture') as mock_vc:
            
            mock_cap = mock_vc.return_value
            mock_cap.isOpened.return_value = True
            
            mock_scanner_inst = mock_controller.mock_scanner_class.return_value
            mock_scanner_inst.is_camera_ready = True
            
            mock_controller.initialize_qr_scanner()
            assert mock_vc.call_count == 1
            mock_vc.assert_called_once_with(1)
            assert mock_controller.mock_scanner_class.call_count == 1
            mock_controller.mock_scanner_class.assert_called_once_with(
                camera_manager=mock_controller.camera_manager,
                camera_index=1,
                camera_object=mock_cap
            )
            assert mock_controller.qr_scanner is not None

    def test_initialize_qr_scanner_fallback(self, mock_controller):
        """Verifica el fallback a la mejor cámara si la guardada falla."""
        mock_controller.db.config_repo.get_setting.return_value = "99"
        
        # Cámara guardada no existe o no funciona
        mock_controller.camera_manager.get_camera_info.return_value = None
        
        best_cam = MagicMock(spec=["index", "is_working", "name"])
        best_cam.index = 0
        best_cam.is_working = True
        best_cam.name = "BestCam"
        mock_controller.camera_manager.get_best_camera.return_value = best_cam
        
        with patch('controllers.hardware_controller.cv2.VideoCapture') as mock_vc:
            
            mock_vc.return_value.isOpened.return_value = True
            mock_controller.mock_scanner_class.return_value.is_camera_ready = True
            
            mock_controller.initialize_qr_scanner()
            assert mock_controller.camera_manager.get_best_camera.call_count == 1
            mock_controller.camera_manager.get_best_camera.assert_called_once_with()
            assert mock_vc.call_count >= 1
            mock_vc.assert_called_with(0)

    def test_detect_cameras_success(self, mock_controller):
        """Verifica que la detección de cámaras actualice el combo box."""
        cam1 = MagicMock(spec=["index", "name", "width", "height"])
        cam1.index = 0
        cam1.name = "Cam1"
        cam1.width = 640
        cam1.height = 480
        
        mock_controller.camera_manager.detect_cameras.return_value = [cam1]
        settings_page = mock_controller.view.pages["settings"]
        
        mock_controller.detect_cameras()
        assert settings_page.camera_combo.clear.call_count >= 1
        settings_page.camera_combo.clear.assert_called()
        settings_page.camera_combo.addItem.assert_any_call(ANY, 0)
        assert mock_controller.mock_msg_box.information.call_count == 1
        mock_controller.mock_msg_box.information.assert_called_once_with(ANY, 'Cámaras Detectadas', ANY)

    def test_detect_cameras_none_found(self, mock_controller):
        """Verifica el comportamiento cuando no se detectan cámaras."""
        mock_controller.camera_manager.detect_cameras.return_value = []
        settings_page = mock_controller.view.pages["settings"]
        
        mock_controller.detect_cameras()
        settings_page.camera_combo.addItem.assert_any_call(ANY, -1)
        assert mock_controller.mock_msg_box.warning.call_count == 1
        mock_controller.mock_msg_box.warning.assert_called_once_with(ANY, 'Sin Cámaras', ANY)

    def test_save_hardware_settings_success(self, mock_controller):
        """Verifica que se guarden los ajustes si la cámara es válida."""
        settings_page = mock_controller.view.pages["settings"]
        settings_page.camera_combo.currentData.return_value = 1
        
        mock_controller.camera_manager.validate_camera.return_value = (True, "")
        cam_info = MagicMock(spec=["index", "name", "is_working", "is_external", "width", "height", "fps"])
        cam_info.index = 1
        cam_info.name = "TestCam"
        cam_info.is_working = True
        cam_info.is_external = True
        cam_info.width = 1280
        cam_info.height = 720
        cam_info.fps = 30.0
        mock_controller.camera_manager.get_camera_info.return_value = cam_info
        
        with patch('controllers.hardware_controller.cv2.VideoCapture') as mock_vc:
            
            mock_vc.return_value.isOpened.return_value = True
            mock_controller.mock_scanner_class.return_value.is_camera_ready = True
            
            mock_controller.save_hardware_settings()
            assert mock_controller.db.config_repo.set_setting.call_count == 1
            mock_controller.db.config_repo.set_setting.assert_called_once_with('camera_index', '1')
            assert mock_controller.view.show_message.call_count >= 1
            mock_controller.view.show_message.assert_called_once_with(ANY, ANY, "info")
            assert mock_controller.qr_scanner is not None

    def test_save_hardware_settings_invalid(self, mock_controller):
        """Verifica que no se guarde si la validación falla."""
        settings_page = mock_controller.view.pages["settings"]
        settings_page.camera_combo.currentData.return_value = 1
        
        mock_controller.camera_manager.validate_camera.return_value = (False, "Error de hardware")
        
        mock_controller.save_hardware_settings()
        assert mock_controller.db.config_repo.set_setting.call_count == 0
        mock_controller.db.config_repo.set_setting.assert_not_called()
        assert mock_controller.mock_msg_box.warning.call_count == 1
        mock_controller.mock_msg_box.warning.assert_called_once_with(ANY, ANY, ANY)

    def test_test_camera_execution(self, mock_controller):
        """Verifica el flujo de prueba de cámara con preview."""
        settings_page = mock_controller.view.pages["settings"]
        settings_page.camera_combo.currentData.return_value = 0
        
        cam_info = MagicMock(spec=["fps", "name", "width", "height", "is_external"])
        cam_info.fps = 30.0
        cam_info.name = "Test"
        cam_info.width = 640
        cam_info.height = 480
        cam_info.is_external = False
        mock_controller.camera_manager.get_camera_info.return_value = cam_info
        
        mock_controller.mock_msg_box.question.return_value = QMessageBox.StandardButton.Yes
        
        mock_controller.test_camera()
        assert mock_controller.camera_manager.test_camera_with_preview.call_count == 1
        mock_controller.camera_manager.test_camera_with_preview.assert_called_once_with(
            index=0, duration=5.0
        )

    def test_load_hardware_settings(self, mock_controller):
        """Verifica la carga de ajustes previos."""
        mock_controller.db.config_repo.get_setting.return_value = "2"
        settings_page = mock_controller.view.pages["settings"]
        settings_page.camera_combo.findData.return_value = 1  # índice en el combo
        
        mock_controller.load_hardware_settings()
        assert mock_controller.camera_manager.detect_cameras.called
        assert settings_page.camera_combo.setCurrentIndex.call_count == 1
        settings_page.camera_combo.setCurrentIndex.assert_called_once_with(1)

    def test_camera_open_error_handling(self, mock_controller):
        """Verifica el manejo de errores si la cámara no se puede abrir."""
        mock_controller.db.config_repo.get_setting.return_value = "0"
        
        cam_info = MagicMock(spec=["index", "is_working", "name", "width", "height", "is_external", "fps"])
        cam_info.index = 0
        cam_info.is_working = True
        cam_info.name = "TestCam"
        cam_info.width = 640
        cam_info.height = 480
        cam_info.is_external = False
        cam_info.fps = 30.0
        mock_controller.camera_manager.get_camera_info.return_value = cam_info
        
        with patch('controllers.hardware_controller.cv2.VideoCapture') as mock_vc:
            mock_cap = mock_vc.return_value
            mock_cap.isOpened.return_value = False
            
            mock_controller.initialize_qr_scanner()
            
            mock_controller.view.show_message.assert_called_once_with(ANY, ANY, "critical")
            assert mock_controller.qr_scanner is None

    def test_release_existing_scanner(self, mock_controller):
        """Verifica que se libere el escáner previo al reinicializar."""
        existing_scanner = MagicMock(spec=QrScanner)
        mock_controller.qr_scanner = existing_scanner
        
        mock_controller.db.config_repo.get_setting.return_value = "0"
        cam_info = MagicMock(spec=["index", "is_working"])
        cam_info.index = 0
        cam_info.is_working = True
        mock_controller.camera_manager.get_camera_info.return_value = cam_info
        
        with patch('controllers.hardware_controller.cv2.VideoCapture') as mock_vc:
            
            mock_vc.return_value.isOpened.return_value = True
            mock_controller.mock_scanner_class.return_value.is_camera_ready = True
            
            mock_controller.initialize_qr_scanner()
            
            assert existing_scanner.release_camera.call_count == 1
            existing_scanner.release_camera.assert_called_once_with()
            assert mock_controller.qr_scanner is not None

    def test_detect_cameras_exception(self, mock_controller):
        """Verifica el manejo de excepciones en la detección."""
        mock_controller.camera_manager.detect_cameras.side_effect = Exception("Fallo total")
        
        mock_controller.detect_cameras()
        assert mock_controller.mock_msg_box.critical.call_count == 1
        mock_controller.mock_msg_box.critical.assert_called_once_with(ANY, ANY, ANY)

    def test_save_not_settings_widget(self, mock_controller):
        """Verifica retorno temprano si no estamos en la página de ajustes."""
        mock_controller.view.pages["settings"] = None # No es SettingsWidget
        mock_controller.save_hardware_settings()
        assert mock_controller.camera_manager.validate_camera.call_count == 0
        mock_controller.camera_manager.validate_camera.assert_not_called()

    def test_init_with_worker_controller(self, mock_controller):
        """Verifica que el scanner se inyecte en el controlador de operario."""
        mock_controller.db.config_repo.get_setting.return_value = "0"
        cam_info = MagicMock(spec=["index", "is_working", "name", "width", "height", "fps"])
        cam_info.index = 0
        cam_info.is_working = True
        cam_info.name = "Test"
        cam_info.width = 640
        cam_info.height = 480
        cam_info.fps = 30.0
        mock_controller.camera_manager.get_camera_info.return_value = cam_info
        
        worker_ctrl = MagicMock(spec=["qr_scanner"])
        
        with patch('controllers.hardware_controller.cv2.VideoCapture') as mock_vc:
            
            mock_vc.return_value.isOpened.return_value = True
            mock_scanner_inst = mock_controller.mock_scanner_class.return_value
            mock_scanner_inst.is_camera_ready = True
            
            mock_controller.initialize_qr_scanner(worker_ctrl)
            
            assert worker_ctrl.qr_scanner == mock_scanner_inst

    def test_scanner_not_ready_exception(self, mock_controller):
        """Verifica el manejo de error cuando el scanner reporta no estar listo."""
        mock_controller.db.config_repo.get_setting.return_value = "0"
        cam_info = MagicMock(spec=["index", "is_working", "name", "width", "height", "fps"])
        cam_info.index = 0
        cam_info.is_working = True
        cam_info.name = "Test"
        cam_info.width = 640
        cam_info.height = 480
        cam_info.fps = 30.0
        mock_controller.camera_manager.get_camera_info.return_value = cam_info
        
        with patch('controllers.hardware_controller.cv2.VideoCapture') as mock_vc:
            
            mock_vc.return_value.isOpened.return_value = True
            mock_scanner_inst = mock_controller.mock_scanner_class.return_value
            mock_scanner_inst.is_camera_ready = False
            
            mock_controller.initialize_qr_scanner()
            
            mock_controller.view.show_message.assert_called_once_with(ANY, ANY, "critical")
            assert mock_controller.qr_scanner is None
            # No se llama a release porque falló antes de abrirse o en el constructor
            # Segun el traceback, falló al asignar el scanner instancia

    def test_save_exception_handling(self, mock_controller):
        """Verifica el manejo de excepciones al guardar la configuración."""
        settings_page = mock_controller.view.pages["settings"]
        settings_page.camera_combo.currentData.return_value = 0
        mock_controller.camera_manager.validate_camera.side_effect = Exception("Crash")
        
        mock_controller.save_hardware_settings()
        assert mock_controller.mock_msg_box.critical.call_count == 1
        mock_controller.mock_msg_box.critical.assert_called_once_with(ANY, ANY, ANY)

    def test_camera_test_fails(self, mock_controller):
        """Verifica el flujo cuando la prueba de cámara falla."""
        settings_page = mock_controller.view.pages["settings"]
        settings_page.camera_combo.currentData.return_value = 0
        mock_controller.camera_manager.test_camera_with_preview.return_value = False
        
        cam_info = MagicMock(spec=["fps", "name", "width", "height", "is_external", "error_message"])
        cam_info.fps = 30.0
        cam_info.name = "Test"
        cam_info.width = 640
        cam_info.height = 480
        cam_info.is_external = False
        cam_info.error_message = "MOCK ERROR"
        mock_controller.camera_manager.get_camera_info.return_value = cam_info
        
        mock_controller.mock_msg_box.question.return_value = QMessageBox.StandardButton.Yes
        
        mock_controller.test_camera()
        assert mock_controller.mock_msg_box.warning.call_count == 1
        mock_controller.mock_msg_box.warning.assert_called_once_with(ANY, ANY, ANY)

