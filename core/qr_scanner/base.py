# core/qr_scanner/base.py

"""
Nombre del Módulo: core.qr_scanner.base

Descripción: Concentra datos de configuración o catálogos estáticos: ``logger``, consumidos por la UI y controladores. Integración típica con: ``re``, ``datetime``.
"""

import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger("EvolucionTiemposApp.QrScanner.Base")

def validate_qr(qr_data: str) -> bool:
    """Valida que un QR tenga el formato correcto de trazabilidad."""
    pattern = r'FAB(\d+)-([A-Z0-9/]+)-UNIT(\d+)-(\d{14})-([A-F0-9]{4})'
    return re.match(pattern, qr_data) is not None

def get_qr_info(qr_data: str) -> Optional[Dict[str, Any]]:
    """Obtiene información de un QR de trazabilidad."""
    pattern = r'FAB(\d+)-([A-Z0-9/]+)-UNIT(\d+)-(\d{14})-([A-F0-9]{4})'
    match = re.match(pattern, qr_data)
    if not match: return None
    
    fabricacion_id, producto_codigo, unit_number, timestamp_str, hash_code = match.groups()
    try:
        timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
    except ValueError:
        return None
    
    return {
        'valido': True,
        'fabricacion_id': int(fabricacion_id),
        'producto_codigo': producto_codigo,
        'unit_number': int(unit_number),
        'timestamp': timestamp,
        'hash': hash_code,
        'qr_completo': qr_data
    }
