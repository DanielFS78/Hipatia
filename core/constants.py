"""
Nombre del Módulo: core.constants

Descripción: Mapas estáticos compartidos por widgets y controladores: ``ICONS`` y ``DEPARTMENT_COLORS``
             para la UI, ``PILA_STATES`` para etiquetas de estado de pilas y ``VALIDATION`` con límites de
             búsqueda y longitud de textos de producto.
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