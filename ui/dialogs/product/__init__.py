# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.product
Descripción: Diálogos del catálogo de productos (detalle, iteraciones, subfabricaciones, procesos mecánicos).
"""

from .product_details_dialog import ProductDetailsDialog
from .add_iteration_dialog import AddIterationDialog
from .subfabricaciones_dialog import SubfabricacionesDialog
from .procesos_mecanicos_dialog import ProcesosMecanicosDialog, AddProcesoMecanicoDialog

__all__ = [
    "ProductDetailsDialog",
    "AddIterationDialog",
    "SubfabricacionesDialog",
    "ProcesosMecanicosDialog",
    "AddProcesoMecanicoDialog",
]
