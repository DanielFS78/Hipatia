# core/qr_scanner/__init__.py

"""
Lógica o utilidades del núcleo (`__init__`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

from .scanner import QrScanner, QrScannerCallback
from .detector import QRDetector
from .base import validate_qr, get_qr_info

__all__ = [
    'QrScanner',
    'QrScannerCallback',
    'QRDetector',
    'validate_qr',
    'get_qr_info'
]
