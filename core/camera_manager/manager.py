# -*- coding: utf-8 -*-
"""
Nombre del Módulo: manager.py (CameraManager)
Descripción: Gestor de hardware de cámara. Controla el acceso, la captura de frames 
             y la liberación de recursos de video.
"""

import time
import logging
import platform
from typing import List, Optional, Tuple, Dict, Any
try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore[assignment]

from .base import CameraInfo, CameraBackend
from .detector import validate_hardware, get_camera_name, test_preview
from .utils import get_system_backend

class CameraManager:
    """
    Gestiona la detección, validación y acceso a cámaras de video conectadas al sistema.
    Proporciona funcionalidades para listar cámaras disponibles, obtener información detallada
    y seleccionar la mejor cámara para una aplicación.
    """
    def __init__(self, max_cameras: int = 10, detection_timeout: float = 2.0, validation_frames: int = 3):
        self.logger = logging.getLogger("EvolucionTiemposApp.CameraManager")
        self.max_cameras, self.detection_timeout, self.validation_frames = max_cameras, detection_timeout, validation_frames
        self.cached_cameras: List[CameraInfo] = []
        self.last_detection_time, self.cache_duration = 0.0, 30.0

    def get_system_backend(self) -> CameraBackend:
        return get_system_backend()

    def _get_camera_name(self, index: int, backend: CameraBackend) -> Tuple[str, bool]:
        return get_camera_name(index, backend)

    def validate_camera_hardware(self, index: int, backend: CameraBackend) -> Optional[CameraInfo]:
        return validate_hardware(index, backend, self.validation_frames)

    def detect_cameras(self, force_refresh: bool = False) -> List[CameraInfo]:
        now = time.time()
        if not force_refresh and self.cached_cameras and (now - self.last_detection_time) < self.cache_duration:
            return self.cached_cameras

        self.logger.info("Detección ligera de cámaras...")
        detected = []
        backend = self.get_system_backend()
        for i in range(self.max_cameras):
            cap = None
            try:
                if cv2: 
                    cap = cv2.VideoCapture(i, backend.value)
                    if cap.isOpened():
                        name, ext = get_camera_name(i, backend)
                        # Lightweight CameraInfo: width=0, height=0, fps=0, is_working=False
                        detected.append(CameraInfo(
                            index=i, name=name, backend=backend.name, 
                            width=0, height=0, fps=0, 
                            is_working=False, is_external=ext, error_message="Pendiente"
                        ))
                    elif i >= 2 and not detected: break
            except Exception: pass
            finally:
                if cap: cap.release()
        self.cached_cameras, self.last_detection_time = detected, now
        return detected

    def get_camera_info(self, index: int) -> Optional[CameraInfo]:
        backend = self.get_system_backend()
        info = self.validate_camera_hardware(index, backend)
        if info is None and backend != CameraBackend.AUTO:
            info = self.validate_camera_hardware(index, CameraBackend.AUTO)
        return info

    def validate_camera(self, index: int) -> Tuple[bool, Optional[str]]:
        info = self.get_camera_info(index)
        if not info: return False, f"No accesible {index}"
        if not info.is_working: return False, info.error_message
        return True, None

    def get_best_camera(self) -> Optional[CameraInfo]:
        found = self.detect_cameras()
        if not found: return None
        working = []
        for f in found:
            info = self.get_camera_info(f.index)
            if info and info.is_working: working.append(info)
        if not working: return None
        
        ext = [c for c in working if c.is_external]
        eval_cams = ext if ext else working
        sorted_c = sorted(eval_cams, key=lambda c: (c.width * c.height, c.fps, -c.index), reverse=True)
        return sorted_c[0]

    def get_fallback_camera(self, exclude_index: int = -1) -> Optional[CameraInfo]:
        cameras = self.detect_cameras()
        avail = [c for c in cameras if c.index != exclude_index]
        return avail[0] if avail else None

    def create_camera_selector_data(self) -> List[Dict[str, Any]]:
        found = self.detect_cameras()
        res = []
        for c in found:
            info = self.get_camera_info(c.index)
            if info and info.is_working:
                res.append({'index': info.index, 'text': f"{info.name} - {info.width}x{info.height}", 'camera_info': info})
        return res

    def test_camera_with_preview(self, index: int, duration: float = 3.0) -> bool:
        return test_preview(index, self.get_system_backend(), duration)
