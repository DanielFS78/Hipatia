"""
Nombre del Módulo: camera_manager.utils

Descripción: Funciones puras de apoyo (sin estado de proceso): ``get_system_backend``. Integración típica con: ``platform``, ``base``.
"""

import platform
from .base import CameraBackend

def get_system_backend() -> CameraBackend:
    s = platform.system()
    if s == "Windows": return CameraBackend.DSHOW
    if s == "Linux": return CameraBackend.V4L2
    if s == "Darwin": return CameraBackend.AVFOUNDATION
    return CameraBackend.AUTO
