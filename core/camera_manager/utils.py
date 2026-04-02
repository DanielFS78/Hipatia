"""
Nombre del Módulo: camera_manager.utils
Descripcion: Utilidades de plataforma para seleccionar backend de captura OpenCV.
"""

import platform
from .base import CameraBackend

def get_system_backend() -> CameraBackend:
    s = platform.system()
    if s == "Windows": return CameraBackend.DSHOW
    if s == "Linux": return CameraBackend.V4L2
    if s == "Darwin": return CameraBackend.AVFOUNDATION
    return CameraBackend.AUTO
