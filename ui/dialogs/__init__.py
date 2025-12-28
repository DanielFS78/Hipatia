# =================================================================================
# ui/dialogs/__init__.py
# Módulo de Diálogos - Exporta todas las clases públicas.
# =================================================================================
"""
Este módulo sirve como punto de entrada para todos los diálogos de la aplicación.
Refactorización Phase 3 Extended completada: Todas las clases han sido extraídas.
"""

# Importar desde módulos ya extraídos
from .canvas_widgets import CanvasWidget, CardWidget
from .visual_effects import (
    GoldenGlowEffect, GreenCycleEffect, MixedGoldGreenEffect,
    ProcessingGlowEffect, SimulationProgressEffect
)

# Importar desde nuevos módulos refactorizados
from .production_flow_dialogs import (
    DefineProductionFlowDialog,
    EnhancedProductionFlowDialog,
    CycleEndConfigDialog,
    ReassignmentRuleDialog,
    DefinirCantidadesDialog
)

from .fabrication_dialogs import (
    CreateFabricacionDialog,
    PreprocesosSelectionDialog,
    PreprocesosForCalculationDialog,
    AssignPreprocesosDialog,
    FabricacionBitacoraDialog,
    GetLoteInstanceParametersDialog,
    GetOptimizationParametersDialog,
    GetUnitsDialog,
    SavePilaDialog,
    LoadPilaDialog,
    ProductsSelectionDialog
)

from .product_dialogs import (
    ProductDetailsDialog,
    AddIterationDialog,
    SubfabricacionesDialog,
    ProcesosMecanicosDialog,
    AddProcesoMecanicoDialog
)

from .prep_dialogs_v2 import (
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
    # Canvas y Cards
    'CanvasWidget', 'CardWidget',
    
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
