"""
Servicio para la validación de reglas de negocio en la interfaz de trabajador.
Maneja comprobaciones de formatos QR, transiciones de estado y coherencia de datos.
"""

import logging
from typing import Any, Dict, Optional, Protocol, Tuple


class QRScannerProtocol(Protocol):
    def parse_qr_data(self, qr_data: str) -> Optional[Dict[str, Any]]: ...

class WorkerValidationService:
    """
    Gestiona la lógica de validación para procesos de trabajadores.
    Desacopla la lógica de decisión del controlador UI.
    """

    def __init__(self, qr_scanner: Optional[QRScannerProtocol] = None, logger: Optional[logging.Logger] = None) -> None:
        self.qr_scanner = qr_scanner
        self.logger = logger or logging.getLogger("EvolucionTiemposApp.WorkerValidationService")

    def validate_qr_data(self, qr_data: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Valida el formato de un código QR.
        
        Returns:
            Tuple (is_valid, parsed_data, error_message)
        """
        if not self.qr_scanner:
            return False, None, "Escáner de QR no disponible"
            
        parsed_data = self.qr_scanner.parse_qr_data(qr_data)
        if not parsed_data:
            return False, None, f"El formato del QR no es válido.\nContenido: {qr_data}"
            
        return True, parsed_data, ""

    def validate_product_match(self, qr_product_code: str, task_product_code: str) -> Tuple[bool, str]:
        """
        Verifica si el producto del QR coincide con el de la tarea seleccionada.
        """
        if qr_product_code != task_product_code:
            return False, f"El QR ({qr_product_code}) no coincide con la tarea seleccionada ({task_product_code})."
        return True, ""

    def is_step_duplicated(self, trabajo_log: Any, step_name: str) -> bool:
        """
        Comprueba si un paso ya ha sido completado para una unidad específica.
        """
        if not trabajo_log or not hasattr(trabajo_log, 'pasos_trazabilidad'):
            return False
            
        for p in trabajo_log.pasos_trazabilidad:
            if p.paso_nombre == step_name and p.estado_paso == 'completado':
                return True
        return False
