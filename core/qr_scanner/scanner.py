# -*- coding: utf-8 -*-
"""
Paquete: core.qr_scanner
Nombre del Módulo: scanner.py (QrScanner)
Descripción: Sistema de detección y decodificación de códigos QR en tiempo real.
             Implementa la lógica de escaneo mediante visión artificial para la lectura
             de etiquetas de trazabilidad.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple
try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore[assignment]

from core.qr_scanner.ui import draw_qr_detection

from .detector import QRDetector
from .base import get_qr_info, validate_qr

class QrScanner:
    def __init__(self, camera_manager: Any, camera_index: int, camera_object: Any) -> None:
        self.logger = logging.getLogger("EvolucionTiemposApp.QrScanner")
        self.camera_manager = camera_manager
        self.camera_index = camera_index
        self.camera = camera_object
        self.detector = QRDetector()
        self.last_scan: Optional[str] = None
        self.last_scan_time: Optional[datetime] = None
        self.scan_cooldown = 4.0
        self.is_camera_ready = self.initialize_camera()

    def initialize_camera(self) -> bool:
        if self.camera and self.camera.isOpened():
            self.is_camera_ready = True
            return True
        self.is_camera_ready = False
        return False

    def _check_cooldown(self, data: str) -> bool:
        now = datetime.now()
        if self.last_scan == data and self.last_scan_time:
            if (now - self.last_scan_time).total_seconds() < self.scan_cooldown: return True
        self.last_scan, self.last_scan_time = data, now
        return False

    def release_camera(self) -> None:
        if self.camera is not None:
            self.camera.release(); self.camera = None; self.is_camera_ready = False
        if cv2: cv2.destroyAllWindows()

    def scan_frame(self, frame: Any) -> Tuple[Optional[str], Optional[Any]]:
        data, bbox = self.detector.scan_frame(frame)
        if data and self._check_cooldown(data): return None, bbox
        return data, bbox

    def draw_qr_detection(self, frame: Any, qr_data: Optional[str], bbox: Optional[Any]) -> Any:
        return draw_qr_detection(frame, qr_data, bbox)

    def parse_qr_data(self, qr_data: str) -> Optional[Dict[str, Any]]:
        return get_qr_info(qr_data)

    def validate_qr_format(self, qr_data: str) -> bool:
        return validate_qr(qr_data)

    def scan_once(self, timeout: int = 30) -> Optional[str]:
        if not self.is_camera_ready and not self.initialize_camera(): return None
        try:
            start = datetime.now(); win = 'Escaner QR - Acerca un codigo QR a la camara'
            while (datetime.now() - start).total_seconds() < timeout:
                ret, frame = self.camera.read()
                if not ret: continue
                data, bbox = self.scan_frame(frame)
                frame = self.draw_qr_detection(frame, data, bbox)
                if cv2: 
                    cv2.imshow(win, frame)
                    if data: self.logger.info("QR detectado"); return data
                    if cv2.waitKey(1) & 0xFF == 27: break
            return None
        finally:
            if cv2: cv2.destroyWindow(win)

    def get_qr_info_for_display(self, qr_data: str) -> str:
        p = self.parse_qr_data(qr_data)
        if not p or not p.get('valido'): return f"⚠️ QR NO VÁLIDO\n{qr_data}"
        return f"✓ QR VÁLIDO\nFabricación: {p['fabricacion_id']}\nProducto: {p['producto_codigo']}\nUnidad: #{p['unit_number']}"

    def set_camera_index(self, new_index: int) -> bool:
        if new_index == self.camera_index and self.is_camera_ready: return True
        self.release_camera(); self.camera_index = new_index
        self.is_camera_ready = self.initialize_camera()
        return self.is_camera_ready

class QrScannerCallback:
    def __init__(
        self,
        on_consulta: Optional[Callable[[Any, Any], None]] = None,
        on_trabajo: Optional[Callable[[Any, Any], bool]] = None,
    ) -> None:
        self.on_consulta, self.on_trabajo = on_consulta, on_trabajo

    def handle_consulta(self, d: Any, p: Any) -> None:
        if self.on_consulta:
            self.on_consulta(d, p)

    def handle_trabajo(self, d: Any, p: Any) -> bool:
        return self.on_trabajo(d, p) if self.on_trabajo else False
