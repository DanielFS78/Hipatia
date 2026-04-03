# Estado herencia múltiple / mixins — abril 2026

Registro único para evitar divergencia entre clones (worktree Cursor vs iCloud).

## Inventario reproducible

- Archivos `*_mixin.py` en el repo (excl. nombre genérico del script de análisis): búsqueda `**/*_mixin.py` → solo `tests/unit/test_product_service_delegation_mixin.py` (test) y `scripts/analyze_mixin.py` (herramienta). **No** hay `*_mixin.py` bajo `controllers/`.
- `scripts/analyze_mixin.py` espera rutas de archivos como argumentos; para inspeccionar un archivo concreto: `python3 scripts/analyze_mixin.py ruta/al/archivo.py`.
- Herencia múltiple en controladores: sin coincidencias obvias con `class Foo(A, B)` en `controllers/*.py` en el barrido de abril 2026.

## Schedule / legacy API

- `ScheduleLegacyApiHelper` y `controllers/schedule_legacy_helper.py` **eliminados**; la API programática vive en `ScheduleUiOpsHelper` (`controllers/schedule_ui_helper.py`). `ScheduleController` delega en `ui_helper` únicamente.

## Otros ítems del plan

- `core/simulation/simulation_adapter.py`: **no** presente en este árbol (cierre: ya retirado o nunca existió aquí).
- `core/simulation/event_engine.py`: **eliminado**; punto de entrada del motor: `core.simulation.engine.motor.MotorDeEventos`.
- `controllers/backup_controller_io_mixin.py`: **no** existe; composición vía `BackupIOManager` (`backup_controller_io_manager.py`).

## Mypy — brecha `core.services`

- Script: `python3 scripts/list_mypy_core_services_gaps.py` (opcional `--json reports/mypy_core_services_gaps.json`).
- Los módulos endurecidos en el mismo lote que este documento se añaden progresivamente en `mypy.ini` bajo bloques `[mypy-core.services....]` con `disallow_untyped_defs = True`.

## Grafo de imports (arquitectura)

- `python3 scripts/audit_import_graph.py` → `reports/import_graph_audit.md` (tabla `controllers.*` → `core.services.*` y resumen por prefijo).
