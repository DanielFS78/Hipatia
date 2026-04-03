# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock
from core.camera_manager import CameraManager, CameraInfo
from ui.worker.camera_config_presenter import CameraConfigPresenter
from core.dtos import CameraConfigDTO, CameraDetailDTO

@pytest.fixture
def mock_manager():
    return MagicMock(spec=CameraManager)

@pytest.fixture
def presenter(mock_manager):
    return CameraConfigPresenter(mock_manager)

def test_detect_cameras_light_success(presenter, mock_manager):
    # Arrange
    cam1 = MagicMock(spec=CameraInfo)
    cam1.index = 0
    cam1.name = "Cam 1"
    cam1.is_external = False
    mock_manager.detect_cameras.return_value = [cam1]
    
    # Act
    result = presenter.detect_cameras_light()
    
    # Assert
    assert len(result) == 1
    assert isinstance(result[0], CameraConfigDTO)
    assert result[0].name == "Cam 1"
    mock_manager.detect_cameras.assert_called_once_with(force_refresh=True)

def test_detect_cameras_light_error(presenter, mock_manager):
    # Arrange
    mock_manager.detect_cameras.side_effect = Exception("Error")
    
    # Act
    result = presenter.detect_cameras_light()
    
    # Assert
    assert result == []

def test_get_camera_detail(presenter, mock_manager):
    # Arrange
    cam = MagicMock(spec=CameraInfo)
    cam.configure_mock(
        index=0, name="Cam 1", width=640, height=480, 
        fps=30.0, backend="MSMF", is_working=True, error_message=None
    )
    mock_manager.get_camera_info.return_value = cam
    
    # Act
    detail = presenter.get_camera_detail(0)
    
    # Assert
    assert isinstance(detail, CameraDetailDTO)
    assert detail.width == 640
    assert detail.is_working is True

def test_test_camera_success(presenter, mock_manager):
    # Arrange
    mock_manager.test_camera_with_preview.return_value = True
    cam = MagicMock(spec=CameraInfo)
    cam.configure_mock(
        index=0, name="Cam 1", width=640, height=480, 
        fps=30.0, backend="MSMF", is_working=True, error_message=None
    )
    mock_manager.get_camera_info.return_value = cam
    
    # Act
    success, detail = presenter.test_camera(0)
    
    # Assert
    assert success is True
    assert detail.is_working is True

def test_validate_before_save_already_working(presenter, mock_manager):
    # Arrange
    cam = MagicMock(spec=CameraInfo)
    cam.configure_mock(
        index=0, name="Cam 1", width=640, height=480, 
        fps=30.0, backend="MSMF", is_working=True, error_message=None
    )
    mock_manager.get_camera_info.return_value = cam
    
    # Act
    valid, msg, detail = presenter.validate_before_save(0)
    
    # Assert
    assert valid is True
    assert detail.is_working is True
    mock_manager.validate_camera.assert_not_called()

def test_validate_before_save_success(presenter, mock_manager):
    # Arrange
    cam_not_working = MagicMock(spec=CameraInfo)
    cam_not_working.configure_mock(is_working=False)
    
    cam_working = MagicMock(spec=CameraInfo)
    cam_working.configure_mock(
        index=0, name="Cam 1", width=640, height=480, 
        fps=30.0, backend="MSMF", is_working=True, error_message=None
    )
    
    mock_manager.get_camera_info.side_effect = [cam_not_working, cam_working]
    mock_manager.validate_camera.return_value = (True, "")
    
    # Act
    valid, msg, detail = presenter.validate_before_save(0)
    
    # Assert
    assert valid is True
    assert detail.is_working is True
    mock_manager.validate_camera.assert_called_once_with(0)
