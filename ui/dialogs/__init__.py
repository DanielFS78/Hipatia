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
from .effects import (
    GoldenGlowEffect, GreenCycleEffect, MixedGoldGreenEffect,
    ProcessingGlowEffect, SimulationProgressEffect
)

# Importar desde nuevos módulos refactorizados
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
