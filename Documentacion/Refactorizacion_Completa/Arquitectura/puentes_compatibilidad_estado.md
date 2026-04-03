# Estado de puentes de compatibilidad (2026-04-02)

**Aclaración (2026-04):** Cualquier documento que describa como *pendiente* el cierre de `core/app_model_bridges/` (`compat.py`, `planning.py`, `product.py`) está **desfasado**. Ese paquete **no está** en el repositorio; `AppModel` ya habla con `ProductFacade`, `PlanningFacade`, `ReportService` y `SystemIntegrationService` sin capa intermedia homónima.

## Inventario activo real

- Lectura unificada de tareas canvas y flags de ciclo en `core/flow_canvas_io.py` (`canvas_task_body`, `canvas_task_display_name`, `flow_task_config_is_cycle_*`, `legacy_canvas_task_*`).

## Retirado del runtime (2026-04-02, ITEM 003 — fase B)

- `core/flow_dialog_bridges.py`: eliminado; utilidades absorbidas por `flow_canvas_io`.

## Retirado del runtime (2026-04-02, ITEM 003 — fase A)

- `ui/dialogs/fabrication/create_dialog_compat.py`: eliminado; la API legacy del diálogo de creación vive como propiedades y métodos directos en `CreateFabricacionDialog` (`create_dialog.py`).

## Estado del retiro incremental aplicado

- Subflujo seleccionado de bajo riesgo: `ui/dialogs/production_flow`.
- Se retiraron helpers de puente usados solo en ese subflujo (`cycle_end_config_values`, `flow_task_config_cycle_return_to_index`, `worker_config_*`).
- La lógica quedó localizada en `flow_action_handler` y `cycle_end_config_dialog`, reduciendo superficie pública del bridge sin tocar el motor de simulación.

## Inventario retirado del runtime

- `core/simulation/simulation_adapter.py` (`AdaptadorScheduler`) ya no forma parte del código ejecutable.
- `core/simulation/event_engine.py` sigue siendo reexport opcional de `MotorDeEventos`; la ruta canónica es `core.simulation.engine.motor`.
- El scheduler activo de simulación se construye desde `controllers/simulation/execution_helpers.py` y `optimizer_worker.py` usando `MotorDeEventos` directo.

## No existe en este árbol

- El paquete `core/app_model_bridges/` fue eliminado del repo activo; `AppModel` delega directamente en `ProductFacade`, `PlanningFacade`, `ReportService` y `SystemIntegrationService`.
- **No** hay acción abierta del tipo “migrar controladores para eliminar bridges de AppModel”: la carpeta ya no forma parte del código.

## Riesgos si no se gestiona retiro incremental

- Capa de indirección extra que dificulta depuración de flujo real.
- Confusión documental entre arquitectura vigente y piezas históricas.
- Falsos positivos en mantenibilidad (puentes “temporales” que se vuelven permanentes).

## Plan de eliminación incremental conservador

1. **Fase 1 (actual):** consolidar puentes necesarios y eliminar mixins de delegación ya migrados.
2. **Fase 2:** ~~mover utilidades de `flow_dialog_bridges`~~ **Hecho** (ITEM 003 B → `flow_canvas_io`).
3. **Fase 3:** retirar adaptadores de compatibilidad de UI cuando tests y callers usen API DTO-first exclusivamente.
4. **Fase 4:** regenerar documentación (`generate_daniel_doc.py`) tras cambios; retirar skills/autopilots obsoletos del índice `.agents/skills/SKILL_INDEX.md`.

## Criterio de retiro por puente

Un puente puede eliminarse cuando:

- no tiene imports desde runtime activo,
- no hay tests que dependan de su API legacy,
- existe ruta equivalente tipada (DTO/servicio) con cobertura.
