"""
Interfaz PyQt6 (`__init__`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from .product_details_dialog import ProductDetailsDialog
from .add_iteration_dialog import AddIterationDialog
from .subfabricaciones_dialog import SubfabricacionesDialog
from .procesos_mecanicos_dialog import ProcesosMecanicosDialog, AddProcesoMecanicoDialog

__all__ = [
    'ProductDetailsDialog',
    'AddIterationDialog',
    'SubfabricacionesDialog',
    'ProcesosMecanicosDialog',
    'AddProcesoMecanicoDialog'
]
