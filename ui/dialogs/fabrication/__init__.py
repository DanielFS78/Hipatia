# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`__init__`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from .input_dialogs import GetLoteInstanceParametersDialog, GetOptimizationParametersDialog, GetUnitsDialog
from .persistence_dialogs import SavePilaDialog, LoadPilaDialog
from .products_dialog import ProductsSelectionDialog
from .selection_dialogs import PreprocesosSelectionDialog, PreprocesosForCalculationDialog
from .bitacora_dialog import FabricacionBitacoraDialog
from .assignment_dialogs import AssignPreprocesosDialog
from .create_dialog import CreateFabricacionDialog
