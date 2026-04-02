"""
Nombre del Módulo: qr_scanner.detector
Descripcion: Detector QR con backend WeChat/OpenCV y fallback automático.
"""

import os
import logging
from typing import Any, Tuple, Optional, List
try:
    import cv2
except ImportError:
    from unittest.mock import MagicMock
    cv2 = MagicMock()

logger = logging.getLogger("EvolucionTiemposApp.QrScanner.Detector")

try:
    from cv2 import wechat_qrcode_WeChatQRCode  # type: ignore[attr-defined]
    HAS_WECHAT_QR = True
except ImportError:
    HAS_WECHAT_QR = False

class QRDetector:
    def __init__(self):
        self.use_wechat = False
        self.detector: Any = None
        self._init_detector()

    def _init_detector(self) -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(base_dir, "qr_scanner", "models")
        
        m = [os.path.join(models_dir, f) for f in ["detect.prototxt", "detect.caffemodel", "sr.prototxt", "sr.caffemodel"]]
        if HAS_WECHAT_QR and all(os.path.exists(p) for p in m):
            try:
                self.detector = cv2.wechat_qrcode_WeChatQRCode(m[0], m[1], m[2], m[3])  # type: ignore[attr-defined]
                self.use_wechat = True
                logger.info("WeChatQRCode inicializado")
            except Exception as e:
                logger.error(f"Error WeChat: {e}")
                self._fallback()
        else:
            self._fallback()

    def _fallback(self) -> None:
        self.detector = cv2.QRCodeDetector()
        self.use_wechat = False

    def scan_frame(self, frame: Any) -> Tuple[Optional[str], Optional[Any]]:
        try:
            h, w = frame.shape[:2]
            target_w = 640
            scale = w / float(target_w) if w > target_w else 1.0
            small = cv2.resize(frame, (target_w, int(h/scale)), interpolation=cv2.INTER_LINEAR) if scale > 1.0 else frame
            
            imgs = [small]
            if not self.use_wechat:
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                imgs = [gray, thresh]

            data, bbox = None, None
            for img in imgs:
                try:
                    if self.use_wechat:
                        res, pts = self.detector.detectAndDecode(img)
                        if res: data, bbox = res[0], pts[0]
                    else:
                        d, b, _ = self.detector.detectAndDecode(img)
                        if d: data, bbox = d, b
                except Exception: continue
                if data: break
            
            scaled_bbox = bbox * scale if bbox is not None else None
            return data, scaled_bbox
        except Exception as e:
            logger.error(f"Error escaneo: {e}")
            return None, None
