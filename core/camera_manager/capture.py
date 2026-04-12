# -*- coding: utf-8 -*-
"""
Nombre del Módulo: camera_manager.capture

Descripción: Apertura unificada de ``cv2.VideoCapture`` con el mismo criterio que ``CameraManager``
             (vía ``get_system_backend``). En Windows el primario es DirectShow y se prueban a continuación
             MSMF y AUTO como respaldo si una webcam no abre con un solo API.
"""

from __future__ import annotations

import platform
from typing import Any, Sequence

from .base import CameraBackend
from .utils import get_system_backend

try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore[assignment]


def _cv2() -> Any:
    if cv2 is None:
        raise RuntimeError("OpenCV (cv2) no está disponible")
    return cv2


def default_capture_backend_chain() -> list[CameraBackend]:
    """
    Construye la lista ordenada de backends a probar al abrir una cámara.

    Returns:
        Cadena sin duplicados: primero el backend del SO (p. ej. DSHOW en Windows,
        AVFoundation en macOS), luego en Windows MSMF y AUTO; en el resto, AUTO si faltaba.
    """
    primary = get_system_backend()
    chain: list[CameraBackend] = []
    for b in (primary,):
        if b not in chain:
            chain.append(b)
    sysn = platform.system()
    if sysn == "Windows":
        for b in (CameraBackend.MSMF, CameraBackend.DSHOW, CameraBackend.AUTO):
            if b not in chain:
                chain.append(b)
    else:
        if CameraBackend.AUTO not in chain:
            chain.append(CameraBackend.AUTO)
    return chain


def merge_backend_priority(primary: CameraBackend) -> list[CameraBackend]:
    """
    Prioriza un backend explícito y añade el resto según ``default_capture_backend_chain``.

    Args:
        primary: Backend solicitado por el llamador (p. ej. validación con backend concreto).

    Returns:
        Lista de backends sin duplicados, con ``primary`` en primer lugar.
    """
    out: list[CameraBackend] = []
    for b in (primary, *default_capture_backend_chain()):
        if b not in out:
            out.append(b)
    return out


def open_video_capture_with_backends(index: int, backends: Sequence[CameraBackend]) -> Any | None:
    """
    Intenta ``VideoCapture(index, backend)`` en orden hasta que ``isOpened()`` sea verdadero.

    Libera cada captura que no abre antes de probar la siguiente. Si ``cv2`` no está
    disponible, devuelve ``None`` sin lanzar excepción.

    Args:
        index: Índice de dispositivo de vídeo.
        backends: Secuencia de backends OpenCV a probar (valores del enum ``CameraBackend``).

    Returns:
        Instancia de ``cv2.VideoCapture`` abierta, o ``None`` si ningún backend abre el índice.
    """
    cv_mod = cv2
    if cv_mod is None:
        return None
    seen: set[int] = set()
    for backend in backends:
        bid = int(backend.value)
        if bid in seen:
            continue
        seen.add(bid)
        cap = cv_mod.VideoCapture(index, backend.value)
        if cap.isOpened():
            return cap
        try:
            cap.release()
        except Exception:
            pass
    return None


def open_video_capture(index: int) -> Any | None:
    """
    Abre la cámara en ``index`` usando ``default_capture_backend_chain``.

    Args:
        index: Índice de dispositivo de vídeo.

    Returns:
        ``VideoCapture`` listo para usar, o ``None`` si no hay ``cv2`` o no abre con ningún backend.
    """
    return open_video_capture_with_backends(index, default_capture_backend_chain())
