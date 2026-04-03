# -*- coding: utf-8 -*-
"""Tests para el punto de entrada del gestor de cámaras."""
import pytest
from unittest.mock import patch, MagicMock
from core.camera_manager import main

pytestmark = pytest.mark.unit

def test_camera_manager_main_function(caplog):
    """
    Tests the main() function directly to ensure coverage.
    """
    caplog.set_level("INFO")
    # Mock input to return 'n' for the prompt
    with patch('builtins.input', return_value='n'):
        # Let's mock CameraManager to control the flow and avoid delays
        with patch('core.camera_manager.CameraManager') as MockManager:
            instance = MockManager.return_value
            # Setup mock behavior
            instance.detect_cameras.return_value = [MagicMock(index=0), MagicMock(index=1)]
            instance.get_best_camera.return_value = MagicMock(index=0, name="MockCam")
            
            main()
            
            # Verify interactions
            instance.detect_cameras.assert_called()
            instance.get_best_camera.assert_called()
            
            # Verify output in logs
            assert "GESTOR DE CÁMARAS" in caplog.text
            assert "Mejor cámara" in caplog.text

    # Test case where no cameras are found
    caplog.clear()
    with patch('builtins.input', return_value='n'):
        with patch('core.camera_manager.CameraManager') as MockManager:
            instance = MockManager.return_value
            instance.detect_cameras.return_value = []
            
            main()
            
            assert "No se encontraron cámaras" in caplog.text

    # Test case with YES response to preview
    with patch('builtins.input', return_value='s'):
        with patch('core.camera_manager.CameraManager') as MockManager:
            instance = MockManager.return_value
            instance.detect_cameras.return_value = [MagicMock(index=0)]
            instance.get_best_camera.return_value = MagicMock(index=0)
            instance.test_camera_with_preview.return_value = True
            
            main()
            
            instance.test_camera_with_preview.assert_called()

    # Test case with Exception during input
    caplog.clear()
    with patch('builtins.input', side_effect=Exception("Input error")):
        with patch('core.camera_manager.CameraManager') as MockManager:
            instance = MockManager.return_value
            instance.detect_cameras.return_value = [MagicMock(index=0)]
            instance.get_best_camera.return_value = MagicMock(index=0)
            
            # Should handle exception and finish gracefully
            main()
            
            assert "Test completado" in caplog.text
