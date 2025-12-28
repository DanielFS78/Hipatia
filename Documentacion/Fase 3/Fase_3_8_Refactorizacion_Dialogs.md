# Fase 3.8: Refactorización de Diálogos

## Objetivo
Modularizar el archivo monolítico `ui/dialogs.py` (7,946 líneas, 36 clases) en un paquete Python con módulos especializados por dominio.

## Estado: ✅ Primera Iteración Completada

## Resumen de Cambios

### 1. Código Muerto Eliminado (95 líneas)

| Clase | Método | Líneas |
|-------|--------|--------|
| `DefineProductionFlowDialog` | `_on_worker_selected` | 18 |
| `DefineProductionFlowDialog` | `_on_prep_step_selected` | 18 |
| `ProcessingGlowEffect` | `_update_pulse` | 14 |
| `EnhancedProductionFlowDialog` | `_highlight_dependencies_in_tree` | 41 |
| `EnhancedProductionFlowDialog` | `_is_task_in_cycle_chain` (duplicado) | 4 |

### 2. Nueva Estructura de Archivos

```
ui/
├── dialogs/                      # NUEVO: Paquete modular
│   ├── __init__.py              # Exportaciones centralizadas
│   ├── canvas_widgets.py        # CanvasWidget, CardWidget
│   └── visual_effects.py        # 5 clases de efectos visuales
├── dialogs_legacy.py            # RENOMBRADO: dialogs.py original
├── main_window.py
└── widgets.py
```

### 3. Módulos Extraídos

#### canvas_widgets.py (~460 líneas)
- `CanvasWidget`: Canvas para drag & drop de tareas
- `CardWidget`: Tarjetas visuales movibles

#### visual_effects.py (~520 líneas)
- `GoldenGlowEffect`: Efecto dorado para inicio de ciclo
- `SimulationProgressEffect`: Efecto azulado para simulación
- `GreenCycleEffect`: Efecto verde para tareas intermedias
- `MixedGoldGreenEffect`: Efecto mixto para tareas finales
- `ProcessingGlowEffect`: Efecto naranja pulsante

### 4. Compatibilidad Mantenida
El archivo `__init__.py` re-exporta todas las clases, permitiendo que los imports existentes sigan funcionando sin cambios:

```python
from ui.dialogs import CanvasWidget, CardWidget  # ✅ Funciona
from ui.dialogs import EnhancedProductionFlowDialog  # ✅ Funciona
```

## Verificación

### Tests
```
984 passed in 4.12s
✓ Tests Exitosos: 984
✗ Tests Fallidos: 0
```

### Imports
```python
>>> from ui.dialogs import CanvasWidget, CardWidget
>>> print('Canvas imports OK')
Canvas imports OK

>>> from ui.dialogs import PreprocesosSelectionDialog  
>>> print('Legacy imports OK')
Legacy imports OK
```

## Métricas

| Métrica | Valor |
|---------|-------|
| Código eliminado | 95 líneas |
| Módulos nuevos | 2 |
| Clases extraídas | 7 |
| Tests pasando | 984/984 |
| Compatibilidad | 100% |

## Próximas Fases (Opcional)

La modularización puede continuar extrayendo las siguientes clases del archivo `dialogs_legacy.py`:

| Módulo | Clases | Líneas Estimadas |
|--------|--------|------------------|
| `production_flow.py` | DefineProductionFlowDialog, EnhancedProductionFlowDialog, CycleEndConfigDialog, ReassignmentRuleDialog, DefinirCantidadesDialog | ~4,480 |
| `fabricacion_dialogs.py` | CreateFabricacionDialog, PreprocesosSelectionDialog, PreprocesosForCalculationDialog, AssignPreprocesosDialog, FabricacionBitacoraDialog | ~720 |
| `product_dialogs.py` | ProductDetailsDialog, AddIterationDialog, SubfabricacionesDialog, ProcesosMecanicosDialog, AddProcesoMecanicoDialog | ~715 |
| `prep_dialogs.py` | PrepGroupsDialog, PrepStepsDialog, PreprocesoDialog | ~450 |
| `utility_dialogs.py` | AddBreakDialog, LoginDialog, ChangePasswordDialog, SavePilaDialog, LoadPilaDialog, SyncDialog, etc. | ~410 |

## Archivos Modificados

1. `ui/dialogs/` - Nuevo directorio de paquete
2. `ui/dialogs/__init__.py` - Exportaciones centralizadas
3. `ui/dialogs/canvas_widgets.py` - Widgets de canvas
4. `ui/dialogs/visual_effects.py` - Efectos visuales
5. `ui/dialogs_legacy.py` - Renombrado de dialogs.py
6. `tests/setup/test_dialogs_setup.py` - Actualizado paths

## Fecha
2025-12-27
