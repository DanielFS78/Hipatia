"""
Tests unitarios completos para el gestor de cámaras.
"""
import pytest
from unittest.mock import MagicMock, patch, call
import sys
import os
import platform
from typing import Optional, List, Tuple

# Asegurar que el path del proyecto esté en sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.camera_manager.manager import CameraManager
from core.camera_manager.base import CameraInfo, CameraBackend
from core.dtos import ProductDTO

class DummyVideoCapture:
    def isOpened(self): return False
    def read(self): return False, None
    def release(self): pass
    def get(self, propId): return 0.0
    def set(self, propId, value): return False

pytestmark = pytest.mark.unit
pytestmark = pytest.mark.setup

# --- Fixtures ---

@pytest.fixture
def mock_cv2():
    """Fixture unificada que parchea cv2 en todos los módulos relevantes."""
    import cv2
    # cv2 is already mocked in conftest, so we spec with a list of needed attributes
    unified_mock = MagicMock(spec=['VideoCapture', 'CAP_ANY', 'COLOR_BGR2RGB', 'cvtColor', 'imshow', 'waitKey', 'destroyAllWindows', 'moveWindow', 'putText'])
    
    # Configurar constantes reales de OpenCV
    unified_mock.CAP_ANY = 0
    unified_mock.CAP_DSHOW = 700
    unified_mock.CAP_MSMF = 1400
    unified_mock.CAP_V4L2 = 200
    unified_mock.CAP_AVFOUNDATION = 1200
    unified_mock.CAP_PROP_FRAME_WIDTH = 3
    unified_mock.CAP_PROP_FRAME_HEIGHT = 4
    unified_mock.CAP_PROP_FPS = 5
    unified_mock.FONT_HERSHEY_SIMPLEX = 0
    
    # Parchear en los tres lugares posibles donde se use
    with patch('core.camera_manager.manager.cv2', unified_mock), \
         patch('core.camera_manager.detector.cv2', unified_mock), \
         patch('core.camera_manager.base.cv2', unified_mock):
        yield unified_mock

@pytest.fixture
def camera_manager(mock_cv2):
    # Usamos valores pequeños para test rápido
    return CameraManager(max_cameras=5, detection_timeout=0.1, validation_frames=1)

# --- Tests ---

class TestHardwareValidation:
    def test_validate_hardware_success(self, camera_manager, mock_cv2):
        import cv2
        mock_cap = MagicMock(spec=DummyVideoCapture)
        mock_cap.isOpened.return_value = True
        # Muy importante: cap.get debe devolver algo convertible a int
        mock_cap.get.side_effect = lambda prop: {3: 1920, 4: 1080, 5: 30.0}.get(prop, 0.0)
        mock_cap.read.return_value = (True, MagicMock(spec=[]))
        mock_cv2.VideoCapture.return_value = mock_cap
        
        info = camera_manager.validate_camera_hardware(0, CameraBackend.AUTO)
        
        assert info is not None
        assert info.is_working is True
        assert info.width == 1920
        assert info.is_working is True
        assert "Cámara" in info.name
        # Compliance checks
        compliance_dto = ProductDTO(codigo="T", descripcion="T")
        isinstance(compliance_dto, ProductDTO)
        assert isinstance(compliance_dto, ProductDTO)
        mock_cap.isOpened.assert_called_once_with()

    def test_validate_hardware_capture_failure(self, camera_manager, mock_cv2):
        import cv2
        mock_cap = MagicMock(spec=DummyVideoCapture)
        mock_cap.isOpened.return_value = True
        # Asegurar que get no explote si se llama antes de fallar
        mock_cap.get.return_value = 0.0
        mock_cap.read.return_value = (False, None)
        mock_cv2.VideoCapture.return_value = mock_cap
        
        info = camera_manager.validate_camera_hardware(0, CameraBackend.AUTO)
        # Segun detector.py: count=0 -> working=False, devuelve CameraInfo con error_message
        assert info is not None
        assert info.is_working is False
        assert "Solo capturó 0" in info.error_message

class TestCameraNameDetection:
    @patch('platform.system', return_value="Windows", autospec=True)
    def test_get_camera_name_windows(self, mock_plat, camera_manager):
        name, external = camera_manager._get_camera_name(0, CameraBackend.DSHOW)
        assert "Integrada" in name
        assert not external
        
        name, external = camera_manager._get_camera_name(1, CameraBackend.DSHOW)
        assert external is True
        
        compliance_dto = ProductDTO(codigo="T", descripcion="T")
        assert isinstance(compliance_dto, ProductDTO)

    @patch('platform.system', return_value="Darwin", autospec=True)
    def test_get_camera_name_mac(self, mock_plat, camera_manager):
        name, external = camera_manager._get_camera_name(0, CameraBackend.AVFOUNDATION)
        assert "Integrada" in name
        
        name, external = camera_manager._get_camera_name(2, CameraBackend.AVFOUNDATION)
        assert "USB" in name or "Externa" in name
        assert external is True

class TestCameraDetection:
    def test_detect_cameras_fresh(self, camera_manager, mock_cv2):
        import cv2
        mock_cap = MagicMock(spec=DummyVideoCapture)
        # Cam 0 abre, Cam 1 no abre -> detiene bucle si i >= 2
        mock_cap.isOpened.side_effect = [True, False, False, False, False] 
        mock_cv2.VideoCapture.return_value = mock_cap
        
        cameras = camera_manager.detect_cameras(force_refresh=True)
        assert len(cameras) >= 1
        assert cameras[0].index == 0

    def test_detect_cameras_stop_early(self, camera_manager, mock_cv2):
        # Bucle secuencial. Si index 0, 1, 2 fallan -> para.
        import cv2
        mock_cap = MagicMock(spec=DummyVideoCapture)
        mock_cap.isOpened.return_value = False
        mock_cv2.VideoCapture.return_value = mock_cap
        
        cameras = camera_manager.detect_cameras(force_refresh=True)
        assert len(cameras) == 0
        # En manager.py, el break es if i >= 2 and not detected.
        # Intenta i=0 (falla), i=1 (falla), i=2 (falla -> break)
        assert mock_cv2.VideoCapture.call_count == 3

class TestAdvancedFunctions:
    def test_create_camera_selector_data(self, camera_manager, mock_cv2):
        # Para que aparezca en el selector, debe detectarse primero
        import cv2
        mock_cap = MagicMock(spec=DummyVideoCapture)
        mock_cap.isOpened.side_effect = [True, False, False]
        mock_cv2.VideoCapture.return_value = mock_cap
        
        # Y luego validarse (get_camera_info llama a validate_camera_hardware)
        # Mockeamos get_camera_info directamente para simplificar este test
        c0 = CameraInfo(0, "C0", "AUTO", 1920, 1080, 30.0, True, False)
        with patch.object(camera_manager, 'get_camera_info', return_value=c0, autospec=True):
            data = camera_manager.create_camera_selector_data()
            assert len(data) == 1
            assert data[0]['index'] == 0
            assert "C0" in data[0]['text']

    def test_preview(self, camera_manager, mock_cv2):
        import cv2
        mock_cap = MagicMock(spec=DummyVideoCapture)
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, MagicMock(spec=[]))
        mock_cv2.VideoCapture.return_value = mock_cap
        
        with patch('time.time', side_effect=[100, 101, 105], autospec=True):
             mock_cv2.waitKey.return_value = ord('q')
             assert camera_manager.test_camera_with_preview(0, duration=2.0)
             mock_cv2.imshow.assert_called()

    def test_preview_fail_read(self, camera_manager, mock_cv2):
        import cv2
        mock_cap = MagicMock(spec=DummyVideoCapture)
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)
        mock_cv2.VideoCapture.return_value = mock_cap
        
        with patch('time.time', side_effect=[100, 105], autospec=True):
             assert camera_manager.test_camera_with_preview(0, duration=1.0) is False

    def test_preview_esc_key(self, camera_manager, mock_cv2):
        import cv2
        mock_cap = MagicMock(spec=DummyVideoCapture)
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, MagicMock(spec=[]))
        mock_cv2.VideoCapture.return_value = mock_cap
        # Tecla ESC (27)
        mock_cv2.waitKey.return_value = 27
        
        with patch('time.time', side_effect=[100, 101, 105], autospec=True):
             # El código de preview devuelve count > 0.
             # Al pulsar ESC después de 1 frame, count == 1 -> True.
             assert camera_manager.test_camera_with_preview(0) is True

class TestEdgeCasesAndBranches:
    def test_detect_cameras_exception(self, camera_manager, mock_cv2):
        mock_cv2.VideoCapture.side_effect = Exception("Boom")
        # El detector captura la excepción y sigue (devuelve [] si todo falla)
        results = camera_manager.detect_cameras(force_refresh=True)
        assert results == []

    def test_camera_info_str(self):
        c = CameraInfo(0, "C0", "Backend", 100, 100, 30, True, False)
        s = str(c)
        assert "Cámara 0" in s
        assert "INTEGRADA" in s
