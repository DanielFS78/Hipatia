# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.fabrication
Descripción: Diálogos de fabricación: crear orden, seleccionar preprocesos/productos, bitácora y asignaciones.

Reexporta las clases más usadas para imports desde ``ui.dialogs`` o controladores.
"""

from .input_dialogs import GetLoteInstanceParametersDialog, GetOptimizationParametersDialog, GetUnitsDialog
from .persistence_dialogs import SavePilaDialog, LoadPilaDialog
from .products_dialog import ProductsSelectionDialog
from .selection_dialogs import PreprocesosSelectionDialog, PreprocesosForCalculationDialog
from .bitacora_dialog import FabricacionBitacoraDialog
from .assignment_dialogs import AssignPreprocesosDialog
from .create_dialog import CreateFabricacionDialog
