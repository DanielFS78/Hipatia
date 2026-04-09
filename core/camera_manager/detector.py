# -*- coding: utf-8 -*-
"""
Nombre del Módulo: detector.py (CameraDetector)
Descripción: Utilidades para la detección y filtrado de dispositivos de cámara 
             compatibles conectados al sistema.
"""

import platform
import time
import logging
from typing import Tuple, Optional, Any
try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore[assignment]

from .base import CameraInfo, CameraBackend

logger = logging.getLogger("EvolucionTiemposApp.CameraManager.Detector")

def _get_cv2() -> Any:
    return cv2

def get_camera_name(index: int, backend: CameraBackend) -> Tuple[str, bool]:
    sys_name = platform.system()
    is_ext = False
    name = f"Cámara {index}"
    
    if sys_name == "Windows":
        if index == 0: name, is_ext = "Cámara Integrada", False
        else: name, is_ext = f"Cámara USB Externa {index}", True
    elif sys_name == "Linux":
        try:
            with open(f"/sys/class/video4linux/video{index}/name", 'r') as f:
                d = f.read().strip()
                if any(k in d.lower() for k in ['usb', 'logitech', 'webcam', 'external']): name, is_ext = d, True
                elif index == 0: name, is_ext = "Cámara Integrada", False
                else: name, is_ext = d, True
        except Exception:
            if index == 0: name, is_ext = "Cámara Integrada", False
            else: name, is_ext = f"Cámara USB {index}", True
    else: # Darwin/Other
        if index == 0: name, is_ext = "Cámara Integrada", False
        else: name, is_ext = f"Cámara Externa {index}", True
    return name, is_ext

def validate_hardware(index: int, backend: CameraBackend, frames: int = 3) -> Optional[CameraInfo]:
    cv_mod = _get_cv2()
    if not cv_mod: return None
    cap = None
    try:
        logger.debug(f"Intentando VideoCapture({index}, {backend.value})")
        cap = cv_mod.VideoCapture(index, backend.value)
        if not cap.isOpened():
            logger.debug(f"VideoCapture({index}) NO se pudo abrir")
            return None
        
        logger.debug(f"VideoCapture({index}) abierto con éxito")
        # Use safe gets for mock compatibility
        w = int(cap.get(3)) # CAP_PROP_FRAME_WIDTH = 3
        h = int(cap.get(4)) # CAP_PROP_FRAME_HEIGHT = 4
        fps = cap.get(5)    # CAP_PROP_FPS = 5
        
        count = 0
        for _ in range(frames):
            try:
                ret, frame = cap.read()
                if ret and frame is not None: count += 1
            except Exception: pass
        
        # Consistent with old expectation: is_working = count > 0 or frames == 0
        working = count > 0 if frames > 0 else True
        name, ext = get_camera_name(index, backend)
        return CameraInfo(index=index, name=name if working else f"Cámara {index} (Err)", backend=backend.name, 
                          width=w if w>0 else 640, height=h if h>0 else 480, fps=fps if fps>0 else 30.0, 
                          is_working=working, is_external=ext, error_message=None if working else f"Solo capturó {count}/{frames}")
    except Exception as e:
        logger.debug(f"Error hardware {index}: {e}")
        return None
    finally:
        if cap: cap.release()

def test_preview(index: int, backend: CameraBackend, duration: float = 5.0) -> bool:
    cv_mod = _get_cv2()
    if not cv_mod: return False
    cap = cv_mod.VideoCapture(index, backend.value)
    if not cap.isOpened(): return False
    try:
        start, count = time.time(), 0
        while (time.time() - start) < duration:
            ret, frame = cap.read()
            if not ret or frame is None: continue
            cv_mod.putText(frame, f"Probando {index}", (10, 30), cv_mod.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv_mod.imshow(f'Preview {index}', frame); count += 1
            if cv_mod.waitKey(1) & 0xFF == 27: break
        return count > 0
    finally:
        cap.release(); cv_mod.destroyAllWindows()
