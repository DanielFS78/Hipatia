"""
Módulo de Constantes Globales.

Define iconos, colores, estados y parámetros de configuración compartidos 
por toda la aplicación Hipatia.
"""
from typing import Dict, Union

# Iconos para la interfaz
ICONS: Dict[str, str] = {
    'product': '📦',
    'pila': '📋',
    'iteration': '📜',
    'worker': '👤',
    'machine': '🔧',
    'report': '📊'
}

# Colores para departamentos
DEPARTMENT_COLORS: Dict[str, str] = {
    "Mecánica": "#3498db",
    "Electrónica": "#2ecc71",
    "Montaje": "#f1c40f",
    "Default": "#95a5a6"
}

# Estados de las pilas
PILA_STATES: Dict[str, str] = {
    'PENDIENTE': 'Pendiente',
    'EN_PROGRESO': 'En Progreso',
    'FINALIZADO': 'Finalizado'
}

# Configuración de validación
VALIDATION: Dict[str, Union[int, int]] = {
    'MIN_SEARCH_LENGTH': 2,
    'MAX_PRODUCT_CODE_LENGTH': 50,
    'MAX_DESCRIPTION_LENGTH': 200
}