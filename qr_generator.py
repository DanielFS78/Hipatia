"""
========================================================================
GENERADOR DE CÓDIGOS QR - SISTEMA DE TRAZABILIDAD
========================================================================
Genera códigos QR únicos para trazabilidad de unidades individuales
y proporciona funciones para convertirlos a diferentes formatos.

Características:
- Generación de IDs únicos con timestamp y hash
- Códigos QR con corrección de errores alta (nivel H)
- Conversión a PIL Image y PyQt6 QPixmap
- Generación en lote

Autor: Sistema de Trazabilidad
Fecha: 2025
========================================================================
"""

import logging
import qrcode
from io import BytesIO
from PIL import Image
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QByteArray
from typing import Optional, Tuple, List
from datetime import datetime
import hashlib
import uuid


class QrGenerator:
    """
    Generador de códigos QR para trazabilidad.
    
    Attributes:
        logger: Logger para registro de operaciones
        qr_version: Versión del código QR (tamaño)
        error_correction: Nivel de corrección de errores
        box_size: Tamaño de cada "caja" del QR en píxeles
        border: Tamaño del borde en cajas
    """
    
    def __init__(
        self,
        qr_version: int = 1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size: int = 10,
        border: int = 4
    ):
        """
        Inicializa el generador de QR.
        
        Args:
            qr_version: Versión del QR (1-40, None para auto)
            error_correction: Nivel de corrección (L, M, Q, H)
            box_size: Tamaño de cada caja en píxeles
            border: Tamaño del borde en cajas
        """
        self.logger = logging.getLogger("EvolucionTiemposApp.QrGenerator")
        self.qr_version = qr_version
        self.error_correction = error_correction
        self.box_size = box_size
        self.border = border
        
        self.logger.info(f"QrGenerator inicializado: version={qr_version}, box_size={box_size}")
    
    def generate_unique_id(
        self,
        fabricacion_id: int,
        producto_codigo: str,
        unit_number: int,
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Genera un identificador único para una unidad.
        
        El formato es: FAB{id}-{producto}-UNIT{num}-{timestamp}-{hash}
        Ejemplo: FAB123-PROD001-UNIT1-20250131143022-A3F9
        
        Args:
            fabricacion_id: ID de la fabricación
            producto_codigo: Código del producto
            unit_number: Número de unidad
            timestamp: Timestamp específico (opcional, usa datetime.now() por defecto)
        
        Returns:
            String con el identificador único
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Formato timestamp: YYYYMMDDHHMMSS
        ts_str = timestamp.strftime("%Y%m%d%H%M%S")
        
        # Crear base del ID
        base = f"FAB{fabricacion_id}-{producto_codigo}-UNIT{unit_number}-{ts_str}"
        
        # Añadir hash corto para garantizar unicidad
        hash_input = f"{base}-{uuid.uuid4()}".encode('utf-8')
        hash_short = hashlib.md5(hash_input).hexdigest()[:4].upper()
        
        unique_id = f"{base}-{hash_short}"
        
        self.logger.debug(f"ID único generado: {unique_id}")
        return unique_id
    
    def generate_qr_code(
        self,
        data: str,
        size: Optional[Tuple[int, int]] = None
    ) -> Optional[Image.Image]:
        """
        Genera un código QR a partir de datos.
        
        Args:
            data: Datos a codificar en el QR
            size: Tamaño final de la imagen (ancho, alto) en píxeles (opcional)
        
        Returns:
            PIL Image con el código QR o None si hay error
        """
        try:
            # Crear objeto QR
            qr = qrcode.QRCode(
                version=self.qr_version,
                error_correction=self.error_correction,
                box_size=self.box_size,
                border=self.border,
            )
            
            # Añadir datos
            qr.add_data(data)
            qr.make(fit=True)
            
            # Crear imagen
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Redimensionar si se especifica tamaño
            if size:
                img = img.resize(size, Image.Resampling.LANCZOS)
            
            self.logger.debug(f"QR generado para datos: {data[:50]}...")
            return img
            
        except Exception as e:
            self.logger.error(f"Error generando código QR: {e}")
            return None
    
    def generate_qr_pixmap(
        self,
        data: str,
        size: Tuple[int, int] = (300, 300)
    ) -> Optional[QPixmap]:
        """
        Genera un QPixmap de PyQt6 con el código QR.
        
        Útil para mostrar el QR directamente en la UI de PyQt6.
        
        Args:
            data: Datos a codificar
            size: Tamaño del QPixmap (ancho, alto)
        
        Returns:
            QPixmap con el código QR o None si hay error
        """
        try:
            # Generar imagen PIL
            img = self.generate_qr_code(data, size)
            if not img:
                return None
            
            # Convertir PIL Image a bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Crear QPixmap desde bytes
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(buffer.read()))
            
            self.logger.debug(f"QPixmap generado: {size[0]}x{size[1]}")
            return pixmap
            
        except Exception as e:
            self.logger.error(f"Error generando QPixmap: {e}")
            return None
    
    def save_qr_to_file(
        self,
        data: str,
        filepath: str,
        size: Optional[Tuple[int, int]] = None
    ) -> bool:
        """
        Guarda un código QR en un archivo.
        
        Args:
            data: Datos a codificar
            filepath: Ruta donde guardar el archivo
            size: Tamaño opcional de la imagen
        
        Returns:
            True si se guardó correctamente, False si hubo error
        """
        try:
            img = self.generate_qr_code(data, size)
            if not img:
                return False
            
            img.save(filepath)
            self.logger.info(f"QR guardado en: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando QR: {e}")
            return False
    
    def generate_batch_qr_codes(
        self,
        base_data: str,
        count: int,
        size: Optional[Tuple[int, int]] = None
    ) -> List[Tuple[str, Image.Image]]:
        """
        Genera múltiples códigos QR en lote.
        
        Args:
            base_data: Datos base para el QR
            count: Número de QRs a generar
            size: Tamaño opcional de las imágenes
        
        Returns:
            Lista de tuplas (data, imagen)
        """
        results = []
        
        for i in range(1, count + 1):
            # Generar datos únicos
            data = f"{base_data}-{i:04d}-{uuid.uuid4().hex[:8]}"
            
            # Generar QR
            img = self.generate_qr_code(data, size)
            if img:
                results.append((data, img))
        
        self.logger.info(f"Generados {len(results)} códigos QR en lote")
        return results


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def generate_simple_qr(data: str, size: int = 300) -> Optional[QPixmap]:
    """
    Función de utilidad para generar rápidamente un QR.
    
    Args:
        data: Datos a codificar
        size: Tamaño del QR
        
    Returns:
        QPixmap con el QR o None si hay error
    """
    generator = QrGenerator()
    return generator.generate_qr_pixmap(data, (size, size))


def generate_production_qr_id(
    fabricacion_id: int,
    producto_codigo: str,
    unit_number: int
) -> str:
    """
    Función de utilidad para generar un ID de producción estándar.
    
    Args:
        fabricacion_id: ID de la fabricación
        producto_codigo: Código del producto
        unit_number: Número de unidad
    
    Returns:
        ID único para la unidad
    """
    generator = QrGenerator()
    return generator.generate_unique_id(fabricacion_id, producto_codigo, unit_number)


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Configurar logging para el ejemplo
    logging.basicConfig(level=logging.INFO)
    
    print("=== EJEMPLO DE USO: QrGenerator ===\n")
    
    # Crear generador
    generator = QrGenerator()
    
    # 1. Generar ID único
    unique_id = generator.generate_unique_id(
        fabricacion_id=123,
        producto_codigo="PROD001",
        unit_number=1
    )
    print(f"1. ID único generado: {unique_id}\n")
    
    # 2. Generar QR y guardar
    print("2. Generando código QR...")
    success = generator.save_qr_to_file(
        data=unique_id,
        filepath="ejemplo_qr.png",
        size=(400, 400)
    )
    print(f"   Guardado: {'✓' if success else '✗'}\n")
    
    # 3. Generar QR en lote
    print("3. Generando lote de 5 QRs...")
    batch = generator.generate_batch_qr_codes(
        base_data="FAB123-PROD001",
        count=5,
        size=(200, 200)
    )
    print(f"   Generados: {len(batch)} códigos QR\n")
    
    # Mostrar los datos generados
    for i, (data, img) in enumerate(batch, 1):
        print(f"   QR {i}: {data}")
    
    print("\n=== FIN DEL EJEMPLO ===")
