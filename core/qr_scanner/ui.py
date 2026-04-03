# core/qr_scanner/ui.py

"""
Lógica o utilidades del núcleo (`ui`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

from typing import Any, Optional
try:
    import cv2
except ImportError:
    from unittest.mock import MagicMock
    cv2 = MagicMock()

def draw_qr_detection(frame: Any, qr_data: Optional[str], bbox: Optional[Any]) -> Any:
    """Dibuja indicadores visuales en el frame."""
    try:
        if bbox is not None:
            pts = bbox
            if len(pts.shape) == 3: pts = pts[0]
            pts = pts.astype(int)
            for i in range(4):
                cv2.line(frame, tuple(pts[i]), tuple(pts[(i + 1) % 4]), (0, 255, 0), 3)
            if qr_data:
                x, y = pts[0]
                text = qr_data[:35] + "..." if len(qr_data) > 35 else qr_data
                size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(frame, (x, y - 35), (x + size[0] + 5, y - 5), (0, 0, 0), -1)
                cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        if qr_data:
            msg = "QR DETECTADO!"
            size = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
            cv2.rectangle(frame, (5, 5), (size[0] + 15, 45), (0, 255, 0), -1)
            cv2.putText(frame, msg, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)

        cv2.putText(frame, "Presiona ESC para cancelar", (10, frame.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        return frame
    except Exception:
        return frame
