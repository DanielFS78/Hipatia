"""
Nombre del Módulo: core.label_manager.base

Descripción: Concentra datos de configuración o catálogos estáticos: ``LABEL_FORMATS``, consumidos por la UI y controladores. Integración típica con: ``pathlib``.
"""

import logging
from pathlib import Path

# Configuraciones de formatos conocidos
LABEL_FORMATS = {
    'APLI_1857_A5': {
        'nombre': 'APLI 1857 (A5)',
        'tamaño_etiqueta': (8, 12),  # mm
        'formato_hoja': 'A5',
        'descripcion': 'Etiquetas pequeñas 8x12mm para QR mínimo'
    },
    'A4_14_ETIQUETAS': {
        'nombre': 'A4 - 14 etiquetas',
        'tamaño_etiqueta': (105, 42),  # mm
        'formato_hoja': 'A4',
        'etiquetas_por_hoja': 14,
        'descripcion': 'Etiquetas estándar 105x42mm'
    },
    'APLI_1861_A5': {
        'nombre': 'APLI 1861 (A5)',
        'tamaño_etiqueta': (12, 30),  # mm (ancho, alto)
        'formato_hoja': 'A5',
        'etiquetas_por_hoja': 66,
        'columnas': 11,
        'filas': 6,
        'margen_superior': 15,
        'margen_lateral': 8,
        'qr_size_mm': 11,  # Maximizamos el QR para aprovechar los 12mm de ancho
        'plantilla': 'apli_1861_qr.docx',
        'descripcion': 'Etiquetas APLI 1861 12x30mm en A5 (11x6), 66 etiquetas por página'
    }
}
