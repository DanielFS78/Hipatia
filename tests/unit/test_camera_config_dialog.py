import pytest
from unittest.mock import MagicMock, patch, call
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import Qt
from ui.worker.camera_config_dialog import CameraConfigDialog
from core.camera_manager import CameraManager, CameraInfo

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_camera_manager():
    """Mock estricto para CameraManager."""
    return MagicMock(spec=CameraManager)

@pytest.fixture
def dialog(mock_camera_manager, qapp, qtbot):
    """Fixture para crear el diálogo con dependencias mockeadas."""
    # Patch QTimer to prevent async execution during tests unless explicitly needed
    with patch('PyQt6.QtCore.QTimer.singleShot') as mock_timer:
        idx = 0
        dlg = CameraConfigDialog(mock_camera_manager, idx)
        qtbot.addWidget(dlg)
        
        # Manually trigger what the timer would have done if we want to test init flow
        # But for unit tests, strictly controlling when _load_cameras_light runs is better.
        
        return dlg

# =============================================================================
# TESTS
# =============================================================================

class TestCameraConfigDialogInit:
    """Tests para la inicialización del diálogo."""

    def test_init_sets_up_ui_and_timer(self, mock_camera_manager, qapp, qtbot):
        """Verifica que __init__ configura la UI y programa la carga inicial."""
        with patch('PyQt6.QtCore.QTimer.singleShot') as mock_timer:
            dlg = CameraConfigDialog(mock_camera_manager, 0)
            
            assert dlg.windowTitle() == "⚙️ Configuración de Cámara QR (Optimizado)"
            assert dlg.current_camera_index == 0
            
            # Verify timer scheduled _load_cameras_light
            mock_timer.assert_called_once_with(50, dlg._load_cameras_light)


class TestLoadCamerasLight:
    """Tests para _load_cameras_light (Sondeo Ligero)."""

    def test_load_cameras_light_success(self, dialog, mock_camera_manager):
        """Verifica carga exitosa de cámaras y selección de la actual."""
        # Setup mocks
        # CameraInfo(index, name, backend, width, height, fps, is_working, is_external, error_message)
        cam1 = CameraInfo(0, "Cam 0", "TEST", 640, 480, 30.0, True)
        cam2 = CameraInfo(1, "Cam 1", "TEST", 640, 480, 30.0, True, is_external=True)
        # We assume detect_cameras only returns partial info if heavy is False, but here
        # we mock full objects to satisfy constructor.
        mock_camera_manager.detect_cameras.return_value = [cam1, cam2]
        
        dialog.current_camera_index = 1
        
        # Execute
        dialog._load_cameras_light()
        
        # Verify
        mock_camera_manager.detect_cameras.assert_called_once_with(force_refresh=True)
        assert dialog.camera_combo.count() == 2
        assert dialog.camera_combo.currentIndex() == 1  # Should select Cam 1
        assert dialog.test_btn.isEnabled() is True
        assert dialog.save_btn.isEnabled() is True
        
        # Check combo texts
        assert "Cam 0 [Integrada]" in dialog.camera_combo.itemText(0)
        assert "Cam 1 [USB EXTERNA]" in dialog.camera_combo.itemText(1)

    def test_load_cameras_light_no_cameras(self, dialog, mock_camera_manager):
        """Verifica comportamiento cuando no se detectan cámaras."""
        mock_camera_manager.detect_cameras.return_value = []
        
        dialog._load_cameras_light()
        
        assert dialog.camera_combo.count() == 1
        assert "No se encontraron cámaras" in dialog.camera_combo.itemText(0)
        assert dialog.camera_combo.currentData() == -1 # Placeholder data
        
        # Info label should show error
        assert "No se detectaron cámaras" in dialog.info_label.text()

    def test_load_cameras_light_exception(self, dialog, mock_camera_manager):
        """Verifica manejo de errores durante el sondeo."""
        mock_camera_manager.detect_cameras.side_effect = Exception("Test Error")
        
        dialog._load_cameras_light()
        
        assert dialog.camera_combo.count() == 1
        assert "Error" in dialog.camera_combo.itemText(0)
        assert "Error crítico" in dialog.info_label.text()
        assert dialog.detect_btn.isEnabled() is True # Should re-enable button

    def test_detect_cameras_button_reloads(self, dialog):
        """Verifica que el botón de re-sondear llama a _load_cameras_light."""
        with patch.object(dialog, '_load_cameras_light') as mock_load:
            dialog._on_detect_cameras()
            mock_load.assert_called_once()
    
    def test_on_combo_selection_changed_updates_info(self, dialog, mock_camera_manager):
        """Verifica la actualización de la etiqueta de información al cambiar selección."""
        dialog.camera_combo.clear()
        cam1 = CameraInfo(0, "Cam Test", "TEST", 640, 480, 30.0, True)
        dialog.camera_combo.addItem("Cam Test", cam1)
        dialog.camera_combo.setCurrentIndex(0)
        
        # Trigger
        dialog._on_combo_selection_changed()
        
        info_text = dialog.info_label.text()
        assert "Cámara 0 (Cam Test)" in info_text
        assert "Resolución: 640x480 @ 30 FPS" in info_text

    def test_on_combo_selection_changed_invalid_selection(self, dialog):
        """Verifica que no explota si la selección no es válida (placeholder)."""
        dialog.camera_combo.addItem("Placeholder", -1)
        dialog.camera_combo.setCurrentIndex(0)
        
        dialog._on_combo_selection_changed()
        
        assert "Selecciona una cámara" in dialog.info_label.text()


class TestTestCamera:
    """Tests para _on_test_camera (Validación Pesada)."""

    def test_test_camera_success(self, dialog, mock_camera_manager):
        """Verifica flujo exitoso de prueba de cámara."""
        # Setup combo with valid camera
        dialog.camera_combo.clear()
        cam_info = CameraInfo(0, "Cam 0", "TEST", 640, 480, 30.0, True)
        dialog.camera_combo.addItem("Cam 0", cam_info)
        dialog.camera_combo.setCurrentIndex(0)
        
        # Setup mocks
        mock_camera_manager.test_camera_with_preview.return_value = True
        # Return updated info after test
        updated_info = CameraInfo(0, "Cam 0", "TEST", 1920, 1080, 30.0, True)
        mock_camera_manager.get_camera_info.return_value = updated_info
        
        with patch('PyQt6.QtWidgets.QMessageBox.information') as mock_msg:
            dialog._on_test_camera()
            
            mock_camera_manager.test_camera_with_preview.assert_called_once_with(0, duration=3.0)
            
            # Verify combo data updated
            assert dialog.camera_combo.itemData(0).width == 1920
            
            # Success message
            mock_msg.assert_called_once()
            assert "Prueba Exitosa" in mock_msg.call_args[0][1]

    def test_test_camera_failure_no_frames(self, dialog, mock_camera_manager):
        """Verifica flujo de fallo cuando no se leen frames."""
        dialog.camera_combo.clear()
        cam_info = CameraInfo(0, "Cam 0", "TEST", 640, 480, 30.0, True)
        dialog.camera_combo.addItem("Cam 0", cam_info)
        dialog.camera_combo.setCurrentIndex(0)
        
        mock_camera_manager.test_camera_with_preview.return_value = False
        mock_camera_manager.get_camera_info.return_value = None # Or info with error
        
        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_msg:
            dialog._on_test_camera()
            
            assert "Error en Prueba" in mock_msg.call_args[0][1]
            assert "Fallo en la validación" in dialog.info_label.text()

    def test_test_camera_exception(self, dialog, mock_camera_manager):
        """Verifica manejo de excepción durante prueba."""
        dialog.camera_combo.clear()
        cam_info = CameraInfo(0, "Cam 0", "TEST", 640, 480, 30.0, True)
        dialog.camera_combo.addItem("Cam 0", cam_info)
        dialog.camera_combo.setCurrentIndex(0)
        
        mock_camera_manager.test_camera_with_preview.side_effect = Exception("Test Crash")
        
        with patch('PyQt6.QtWidgets.QMessageBox.critical') as mock_msg:
            dialog._on_test_camera()
            
            assert "Error" in mock_msg.call_args[0][1] # Title "Error"
            assert "Test Crash" in mock_msg.call_args[0][2] # Body contains error msg
            
        # Ensure buttons re-enabled
        assert dialog.test_btn.isEnabled() is True

    def test_test_camera_invalid_selection(self, dialog):
        """Verifica alerta si no hay cámara seleccionada."""
        dialog.camera_combo.clear()
        dialog.camera_combo.addItem("Select...", -1)
        dialog.camera_combo.setCurrentIndex(0)
        
        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_msg:
            dialog._on_test_camera()
            mock_msg.assert_called()


class TestSaveClicked:
    """Tests para _on_save_clicked."""
    
    def test_save_already_validated(self, dialog):
        """Verifica guardado directo si la cámara ya está validada."""
        dialog.camera_combo.clear()
        cam_info = CameraInfo(5, "Cam 5", "TEST", 640, 480, 30.0, True)
        dialog.camera_combo.addItem("Cam 5", cam_info)
        dialog.camera_combo.setCurrentIndex(0)
        
        with patch.object(dialog, 'accept') as mock_accept:
            dialog._on_save_clicked()
            mock_accept.assert_called_once()
            
    def test_save_validates_if_not_validated(self, dialog, mock_camera_manager):
        """Verifica que se valida primero si la cámara no estaba marcada como working."""
        dialog.camera_combo.clear()
        cam_info = CameraInfo(2, "Cam 2", "TEST", 640, 480, 30.0, False)
        dialog.camera_combo.addItem("Cam 2", cam_info)
        dialog.camera_combo.setCurrentIndex(0)
        
        # Validation succeeds
        mock_camera_manager.validate_camera.return_value = (True, "")
        mock_camera_manager.get_camera_info.return_value = CameraInfo(2, "Cam 2", "TEST", 640, 480, 30.0, True)
        
        with patch.object(dialog, 'accept') as mock_accept:
            dialog._on_save_clicked()
            
            mock_camera_manager.validate_camera.assert_called_once_with(2)
            mock_accept.assert_called_once()

    def test_save_fails_validation(self, dialog, mock_camera_manager):
        """Verifica que se bloquea el guardado si falla la validación."""
        dialog.camera_combo.clear()
        cam_info = CameraInfo(2, "Cam 2", "TEST", 640, 480, 30.0, False)
        dialog.camera_combo.addItem("Cam 2", cam_info)
        dialog.camera_combo.setCurrentIndex(0)
        
        # Validation fails
        mock_camera_manager.validate_camera.return_value = (False, "Device busy")
        
        with patch.object(dialog, 'accept') as mock_accept, \
             patch('PyQt6.QtWidgets.QMessageBox.critical') as mock_msg:
            
            dialog._on_save_clicked()
            
            mock_accept.assert_not_called()
            mock_msg.assert_called_once()
            assert "Error de Validación" in mock_msg.call_args[0][1]

    def test_get_selected_camera(self, dialog):
        """Verifica método getter final."""
        # Valid selection
        dialog.camera_combo.clear()
        cam_info = CameraInfo(99, "Cam 99", "TEST", 640, 480, 60.0, True)
        dialog.camera_combo.addItem("Cam 99", cam_info)
        dialog.camera_combo.setCurrentIndex(0)
        
        assert dialog.get_selected_camera() == 99
        
        # Invalid selection
        dialog.camera_combo.clear()
        dialog.camera_combo.addItem("None", -1)
        dialog.camera_combo.setCurrentIndex(0)
        
        assert dialog.get_selected_camera() is None
