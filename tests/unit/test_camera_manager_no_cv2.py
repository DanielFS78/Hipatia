# -*- coding: utf-8 -*-
"""Tests unitarios para CameraManager sin cv2: fallback y valores mock del backend."""
import sys
from unittest.mock import patch, MagicMock
import pytest
from importlib import reload
import core.camera_manager

pytestmark = pytest.mark.unit


def test_no_cv2_fallback():
    """
    Test that CameraManager handles missing cv2 gracefully.
    This covers the 'try-except ImportError' block at the top level
    and the mock Enum values.
    """
    # 1. Force cv2 to be missing
    with patch.dict(sys.modules, {'cv2': None}):
        # 2. Reload modules to trigger top-level execution
        for mod in ['core.camera_manager.base', 'core.camera_manager.detector', 'core.camera_manager.manager', 'core.camera_manager']:
            if mod in sys.modules:
                reload(sys.modules[mod])
        
        # 3. Import from reloaded module
        from core.camera_manager import CameraManager, CameraBackend, CV2_AVAILABLE
        
        # 4. Assertions
        assert CV2_AVAILABLE is False
        assert core.camera_manager.cv2 is None
        
        # Verify fallback Enum values (lines 48-52)
        assert CameraBackend.AUTO.value == 0
        assert CameraBackend.DSHOW.value == 700
        
        # Verify Manager behavior
        manager = CameraManager()
        
        # detect_cameras should catch the AttributeError/Exception when accessing cv2.VideoCapture
        spy_detect = MagicMock(wraps=manager.detect_cameras)
        manager.detect_cameras = spy_detect
        cameras = manager.detect_cameras()
        assert spy_detect.call_count == 1
        spy_detect.assert_called_once_with()
        assert cameras == []
        
        # validate_camera_hardware should return None
        spy_validate = MagicMock(wraps=manager.validate_camera_hardware)
        manager.validate_camera_hardware = spy_validate
        info = manager.validate_camera_hardware(0, CameraBackend.AUTO)
        assert spy_validate.call_count == 1
        spy_validate.assert_called_once_with(0, CameraBackend.AUTO)
        assert info is None

    # 5. Restore core.camera_manager to normal state (with mocked cv2 from conftest)
    # We remove the patch implicitly by exiting 'with', but module is still loaded with 'None' cv2 logic
    # We must reload it to restore normal 'cv2' usage for other tests
    reload(core.camera_manager)
