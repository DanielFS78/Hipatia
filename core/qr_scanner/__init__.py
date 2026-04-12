# core/qr_scanner/__init__.py

"""
Nombre del Módulo: core.qr_scanner

Descripción: Concentra datos de configuración o catálogos estáticos: ``__all__``, consumidos por la UI y controladores. Integración típica con: ``scanner``, ``detector``, ``base``.
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
