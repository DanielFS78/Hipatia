# -*- coding: utf-8 -*-
"""
Nombre del Módulo: camera_manager.detector

Descripción: Detección y prueba de cámaras vía OpenCV: nombres heurísticos por SO,
             validación de hardware con lectura de frames y vista previa. La apertura
             de ``VideoCapture`` se delega en ``capture.open_video_capture_with_backends``
             para mantener la misma cadena de backends que el resto del gestor de cámara.
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
from .capture import merge_backend_priority, open_video_capture_with_backends

logger = logging.getLogger("EvolucionTiemposApp.CameraManager.Detector")

def _get_cv2() -> Any:
    return cv2

def get_camera_name(index: int, backend: CameraBackend) -> Tuple[str, bool]:
    """
    Devuelve un nombre legible y si la cámara se considera externa (heurística por índice y SO).

    Args:
        index: Índice del dispositivo de vídeo.
        backend: Backend OpenCV asociado (se usa sobre todo para trazas; la heurística es por SO).

    Returns:
        Tupla ``(nombre, es_externa)``.
    """
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
    """
    Abre la cámara con la cadena de backends fusionada y valida lectura de frames.

    Args:
        index: Índice del dispositivo de vídeo.
        backend: Backend preferido; se combina con ``default_capture_backend_chain`` vía ``merge_backend_priority``.
        frames: Número de intentos de lectura para decidir si la cámara ``is_working``.

    Returns:
        ``CameraInfo`` con dimensiones y estado, o ``None`` si no hay ``cv2`` o no abre la cámara.
    """
    cv_mod = _get_cv2()
    if not cv_mod:
        return None
    cap = None
    try:
        chain = merge_backend_priority(backend)
        logger.debug("Intentando VideoCapture(%s) con backends %s", index, [b.name for b in chain])
        cap = open_video_capture_with_backends(index, chain)
        if not cap or not cap.isOpened():
            logger.debug("VideoCapture(%s) no abrió con ningún backend de la cadena", index)
            return None

        logger.debug("VideoCapture(%s) abierto con éxito", index)
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
    """
    Muestra una ventana de previsualización durante ``duration`` segundos (o hasta ESC).

    Args:
        index: Índice del dispositivo de vídeo.
        backend: Backend preferido para construir la cadena de apertura.
        duration: Segundos máximos de bucle de captura.

    Returns:
        True si se mostró al menos un frame; False si no hay OpenCV, no abre la cámara o no hay frames.
    """
    cv_mod = _get_cv2()
    if not cv_mod:
        return False
    cap = open_video_capture_with_backends(index, merge_backend_priority(backend))
    if not cap or not cap.isOpened():
        return False
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
