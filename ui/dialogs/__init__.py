# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs
Descripción: Paquete de diálogos PyQt6 (fabricación, flujo, productos, preparación y utilidades).

Reexporta las clases públicas más usadas para simplificar ``from ui.dialogs import …``.

El grafo visual de flujo de producción vive en ``ui.widgets.production_flow``
(``ProductionFlowCanvas``, ``FlowCardWidget``); no se reexportan widgets de canvas aquí.
"""

from .effects import (
    GoldenGlowEffect, GreenCycleEffect, MixedGoldGreenEffect,
    ProcessingGlowEffect, SimulationProgressEffect
)

from .production_flow import (
    DefineProductionFlowDialog,
    EnhancedProductionFlowDialog,
    CycleEndConfigDialog,
    ReassignmentRuleDialog,
    DefinirCantidadesDialog
)

from .fabrication.create_dialog import CreateFabricacionDialog
from .fabrication.selection_dialogs import (
    PreprocesosSelectionDialog,
    PreprocesosForCalculationDialog
)
from .fabrication.assignment_dialogs import AssignPreprocesosDialog
from .fabrication.bitacora_dialog import FabricacionBitacoraDialog
from .fabrication.input_dialogs import (
    GetLoteInstanceParametersDialog,
    GetOptimizationParametersDialog,
    GetUnitsDialog
)
from .fabrication.persistence_dialogs import (
    SavePilaDialog,
    LoadPilaDialog
)
from .fabrication.products_dialog import ProductsSelectionDialog

from .product import (
    ProductDetailsDialog,
    AddIterationDialog,
    SubfabricacionesDialog,
    ProcesosMecanicosDialog,
    AddProcesoMecanicoDialog
)

from .prep import (
    PrepStepsDialog,
    PrepGroupsDialog,
    PreprocesoDialog
)

from .utility_dialogs import (
    AddBreakDialog,
    LoginDialog,
    ChangePasswordDialog,
    SyncDialog,
    SeleccionarHojasExcelDialog,
    MultiWorkerSelectionDialog
)

__all__ = [
    # Efectos visuales
    'GoldenGlowEffect', 'GreenCycleEffect', 'MixedGoldGreenEffect',
    'ProcessingGlowEffect', 'SimulationProgressEffect',
    
    # Flujo de producción
    'DefineProductionFlowDialog', 'EnhancedProductionFlowDialog',
    'CycleEndConfigDialog', 'ReassignmentRuleDialog', 'DefinirCantidadesDialog',
    
    # Fabricación
    'CreateFabricacionDialog', 'PreprocesosSelectionDialog',
    'PreprocesosForCalculationDialog', 'AssignPreprocesosDialog',
    'FabricacionBitacoraDialog', 'GetLoteInstanceParametersDialog',
    'GetOptimizationParametersDialog', 'GetUnitsDialog', 'SavePilaDialog',
    'LoadPilaDialog',
    
    # Productos
    'ProductDetailsDialog', 'AddIterationDialog', 'SubfabricacionesDialog',
    'ProcesosMecanicosDialog', 'AddProcesoMecanicoDialog',
    
    # Preparación
    'PrepGroupsDialog', 'PrepStepsDialog', 'PreprocesoDialog',
    
    # Utilidades
    'AddBreakDialog', 'LoginDialog', 'ChangePasswordDialog', 'SavePilaDialog',
    'LoadPilaDialog', 'SyncDialog', 'GetUnitsDialog',
    'SeleccionarHojasExcelDialog', 'MultiWorkerSelectionDialog',
]
