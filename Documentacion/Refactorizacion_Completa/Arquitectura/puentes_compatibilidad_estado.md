# Estado de puentes de compatibilidad (2026-04-02)

## Inventario activo real

- `core/flow_dialog_bridges.py`: puente vigente entre estructuras legacy del canvas y la frontera DTO/UI.
- `ui/dialogs/fabrication/create_dialog_compat.py`: adaptador de compatibilidad para API histórica del diálogo de creación.

## Estado del retiro incremental aplicado

- Subflujo seleccionado de bajo riesgo: `ui/dialogs/production_flow`.
- Se retiraron helpers de puente usados solo en ese subflujo (`cycle_end_config_values`, `flow_task_config_cycle_return_to_index`, `worker_config_*`).
- La lógica quedó localizada en `flow_action_handler` y `cycle_end_config_dialog`, reduciendo superficie pública del bridge sin tocar el motor de simulación.

## Inventario retirado del runtime

- `core/simulation/simulation_adapter.py` (`AdaptadorScheduler`) ya no forma parte del código ejecutable.
- El scheduler activo de simulación se construye desde `controllers/simulation/execution_helpers.py` usando `MotorDeEventos`.

## Riesgos si no se gestiona retiro incremental

- Capa de indirección extra que dificulta depuración de flujo real.
- Confusión documental entre arquitectura vigente y piezas históricas.
- Falsos positivos en mantenibilidad (puentes “temporales” que se vuelven permanentes).

## Plan de eliminación incremental conservador

1. **Fase 1 (actual):** consolidar puentes necesarios y eliminar mixins de delegación ya migrados.
2. **Fase 2:** mover utilidades de `flow_dialog_bridges` a colaboradores de dominio cuando no haya consumo dict-only.
3. **Fase 3:** retirar adaptadores de compatibilidad de UI cuando tests y callers usen API DTO-first exclusivamente.
4. **Fase 4:** regenerar documentación técnica y validar ausencia de referencias obsoletas (`AdaptadorScheduler`).

## Criterio de retiro por puente

Un puente puede eliminarse cuando:

- no tiene imports desde runtime activo,
- no hay tests que dependan de su API legacy,
- existe ruta equivalente tipada (DTO/servicio) con cobertura.


## Actualización de retiro (2026-04-02, bloque shims/mixins)

- Se eliminó `core/app_model_bridges/` del runtime (`compat.py`, `planning.py`, `product.py`).
- `AppModel` dejó de heredar bridges y conserva la API legacy mediante delegación directa a fachadas/servicios dentro de `core/app_model.py`.
- Se retiraron mixins supervivientes en favor de composición explícita:
  - `features/worker_controller_io_mixin.py` -> `features/worker_controller_io_manager.py` inyectado en `WorkerController`.
  - `core/services/product_service_delegation_mixin.py` -> métodos integrados en `core/services/product_service.py`.
  - `ui/dialogs/production_flow/enhanced_flow_presenter_state.py` -> `ui/dialogs/production_flow/enhanced_flow_state_manager.py` inyectado en `EnhancedFlowPresenter`.
- Validación de cierre tras retiro:
  - `python3 -m mypy .` -> verde.
  - `pytest -q` -> verde.
