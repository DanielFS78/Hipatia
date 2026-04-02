"""
Nombre del Módulo: camera_manager.base
Descripcion: Tipos base para detección de cámaras y metadatos de dispositivos.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None  # type: ignore[assignment]
    CV2_AVAILABLE = False

class CameraBackend(Enum):
    AUTO = cv2.CAP_ANY if CV2_AVAILABLE else 0
    DSHOW = cv2.CAP_DSHOW if CV2_AVAILABLE else 700
    MSMF = cv2.CAP_MSMF if CV2_AVAILABLE else 1400
    V4L2 = cv2.CAP_V4L2 if CV2_AVAILABLE else 200
    AVFOUNDATION = cv2.CAP_AVFOUNDATION if CV2_AVAILABLE else 1200

@dataclass
class CameraInfo:
    index: int
    name: str
    backend: str
    width: int
    height: int
    fps: float
    is_working: bool
    is_external: bool = False
    error_message: Optional[str] = None

    def __str__(self) -> str:
        if self.is_working:
            ext = " [USB EXTERNA]" if self.is_external else " [INTEGRADA]"
            return f"Cámara {self.index}: {self.name}{ext} ({self.width}x{self.height} @ {self.fps:.1f}fps)"
        return f"Cámara {self.index}: ERROR - {self.error_message}"
