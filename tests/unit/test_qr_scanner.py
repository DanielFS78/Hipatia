# -*- coding: utf-8 -*-
"""Tests unitarios para QrScanner, validate_qr y get_qr_info.

Cubre init, validate_qr, get_qr_info, scan_frame, cooldown, release_camera,
draw_qr_detection, parse_qr_data, get_qr_info_for_display, scan_once, set_camera_index
y detector WeChat. Decisión de mocking: cv2/externos sin spec; VideoCapture con spec.
"""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from datetime import datetime
from core.qr_scanner import QrScanner, validate_qr, get_qr_info

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_camera_manager():
    return MagicMock(spec=[])

@pytest.fixture
def mock_video_capture():
    mock = MagicMock(spec=['isOpened', 'release', 'read'])
    mock.isOpened.return_value = True
    return mock

def test_qr_scanner_init(mock_camera_manager, mock_video_capture):
    with patch('core.qr_scanner.detector.HAS_WECHAT_QR', False):
        scanner = QrScanner(mock_camera_manager, 0, mock_video_capture)
        assert scanner.camera_index == 0
        assert scanner.camera == mock_video_capture
        assert scanner.is_camera_ready is True
        assert scanner.detector.use_wechat is False

def test_qr_scanner_init_fail(mock_camera_manager):
    mock_bad_cap = MagicMock(spec=["isOpened"])
    mock_bad_cap.isOpened.return_value = False
    scanner = QrScanner(mock_camera_manager, 1, mock_bad_cap)
    assert scanner.is_camera_ready is False

def test_validate_qr():
    assert validate_qr("FAB123-PROD001-UNIT1-20250131143022-A3F9") is True
    assert validate_qr("INVALID-QR") is False

def test_get_qr_info():
    qr = "FAB123-PROD001-UNIT1-20250131143022-A3F9"
    info = get_qr_info(qr)
    assert info is not None
    assert info['fabricacion_id'] == 123
    assert info['producto_codigo'] == "PROD001"
    assert info['unit_number'] == 1
    assert info['hash'] == "A3F9"
    assert isinstance(info['timestamp'], datetime)

def test_scan_frame_no_qr(mock_camera_manager, mock_video_capture):
    scanner = QrScanner(mock_camera_manager, 0, mock_video_capture)
    # create a dummy frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    with patch.object(scanner.detector.detector, 'detectAndDecode', return_value=(None, None, None)):
        data, bbox = scanner.scan_frame(frame)
        assert data is None
        assert bbox is None

def test_scan_frame_with_qr_fallback(mock_camera_manager, mock_video_capture):
    scanner = QrScanner(mock_camera_manager, 0, mock_video_capture)
    scanner.detector.use_wechat = False
    
    # Create a dummy detector that returns a tuple of 3: (data, bbox, extra)
    scanner.detector.detector = MagicMock(spec=["detectAndDecode"])
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_bbox = np.array([[[10, 10], [100, 10], [100, 100], [10, 100]]], dtype=np.float32)
    
    # fallback uses d, b, _ = self.detector.detectAndDecode(img)
    scanner.detector.detector.detectAndDecode.return_value = ("FAB123-PROD001-UNIT1-20250131143022-A3F9", mock_bbox, None)
    
    # Mock scale_factor logic to ensure it reaches detector
    with patch('core.qr_scanner.scanner.cv2.resize', return_value=frame):
        data, bbox = scanner.scan_frame(frame)
        assert data == "FAB123-PROD001-UNIT1-20250131143022-A3F9"
        assert bbox is not None

def test_cooldown(mock_camera_manager, mock_video_capture):
    scanner = QrScanner(mock_camera_manager, 0, mock_video_capture)
    qr = "TEST-QR"
    
    # First scan
    assert scanner._check_cooldown(qr) is False
    # Immediate second scan of same QR
    assert scanner._check_cooldown(qr) is True
    
    # Different QR
    assert scanner._check_cooldown("OTHER-QR") is False

def test_release_camera(mock_camera_manager, mock_video_capture):
    scanner = QrScanner(mock_camera_manager, 0, mock_video_capture)
    scanner.release_camera()
    assert mock_video_capture.release.call_count == 1
    mock_video_capture.release.assert_called_once_with()
    assert scanner.camera is None
    assert scanner.is_camera_ready is False

def test_draw_qr_detection(mock_camera_manager, mock_video_capture):
    scanner = QrScanner(mock_camera_manager, 0, mock_video_capture)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    bbox = np.array([[[10, 10], [100, 10], [100, 100], [10, 100]]], dtype=np.float32)
    
    result_frame = scanner.draw_qr_detection(frame, "DATA", bbox)
    assert result_frame is not None
    assert result_frame.shape == (480, 640, 3)

def test_parse_qr_data_invalid(mock_camera_manager, mock_video_capture):
    scanner = QrScanner(mock_camera_manager, 0, mock_video_capture)
    assert scanner.parse_qr_data("INVALID") is None

def test_get_qr_info_for_display(mock_camera_manager, mock_video_capture):
    scanner = QrScanner(mock_camera_manager, 0, mock_video_capture)
    valid_qr = "FAB123-PROD001-UNIT1-20250131143022-A3F9"
    display = scanner.get_qr_info_for_display(valid_qr)
    assert "✓ QR VÁLIDO" in display
    # Check parts without assuming exact labels
    assert "123" in display
    assert "PROD001" in display
    
    invalid_display = scanner.get_qr_info_for_display("INVALID")
    assert "⚠️ QR NO VÁLIDO" in invalid_display

def test_scan_once_timeout(mock_camera_manager, mock_video_capture):
    scanner = QrScanner(mock_camera_manager, 0, mock_video_capture)
    mock_video_capture.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    
    with patch('core.qr_scanner.scanner.cv2.imshow'):
        with patch('core.qr_scanner.scanner.cv2.waitKey', return_value=27): # ESC key
            result = scanner.scan_once(timeout=1)
            assert result is None

def test_set_camera_index(mock_camera_manager, mock_video_capture):
    scanner = QrScanner(mock_camera_manager, 0, mock_video_capture)
    
    with patch.object(scanner, 'initialize_camera', return_value=True):
        assert scanner.set_camera_index(1) is True
        assert scanner.camera_index == 1

def test_init_detector_wechat_success(mock_camera_manager, mock_video_capture):
    with patch('core.qr_scanner.detector.HAS_WECHAT_QR', True):
        with patch('os.path.exists', return_value=True):
            with patch('core.qr_scanner.detector.cv2.wechat_qrcode_WeChatQRCode') as mock_wechat:
                scanner = QrScanner(mock_camera_manager, 0, mock_video_capture)
                assert scanner.detector.use_wechat is True
                assert mock_wechat.call_count >= 1
                mock_wechat.assert_called()

def test_init_detector_wechat_fail(mock_camera_manager, mock_video_capture):
    with patch('core.qr_scanner.detector.HAS_WECHAT_QR', True):
        with patch('os.path.exists', return_value=True):
            with patch('core.qr_scanner.detector.cv2.wechat_qrcode_WeChatQRCode', side_effect=Exception("Load error")):
                scanner = QrScanner(mock_camera_manager, 0, mock_video_capture)
                assert scanner.detector.use_wechat is False

def test_scan_frame_wechat_success(mock_camera_manager, mock_video_capture):
    with patch('core.qr_scanner.detector.HAS_WECHAT_QR', True), patch('os.path.exists', return_value=True), patch('core.qr_scanner.detector.cv2.wechat_qrcode_WeChatQRCode'):
        scanner = QrScanner(mock_camera_manager, 0, mock_video_capture)
        scanner.detector.use_wechat = True
        scanner.detector.detector = MagicMock(spec=["detectAndDecode"])
        scanner.detector.detector.detectAndDecode.return_value = (["FAB123-PROD001-UNIT1-20250131143022-A3F9"], [np.array([[0,0], [1,0], [1,1], [0,1]])])
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        data, bbox = scanner.scan_frame(frame)
        assert data == "FAB123-PROD001-UNIT1-20250131143022-A3F9"
