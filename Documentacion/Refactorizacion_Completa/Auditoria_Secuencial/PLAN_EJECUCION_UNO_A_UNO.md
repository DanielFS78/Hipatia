# Plan de Ejecucion Uno a Uno (Arbol Principal)

Fecha de auditoria: 2026-04-02
Base de datos de analisis: `scripts/analysis/*`, `scripts/legacy_analyzer.py`, `scripts/check_typing_coverage.py`, `scripts/test_quality_analyzer.py`, `scripts/ui_dto_boundary_analyzer.py`.

## Resumen ejecutivo

- Dependencias internas con ciclos detectados: 16 (`analyze_dependencies.txt`).
- Hallazgos UI/DTO: **0** (`ui_dto_boundary_report.md`) — sincronizado tras ITEM 002.
- Cobertura de tipado de funciones: 92.08% (`check_typing_coverage.txt`).
- Legacy activo: pendiente re-ejecutar `legacy_analyzer.py` tras cierres; ITEM 001/002 cubrieron `print` en `products_widget` y `bare except` en fallback de `settings_widget`.
- Calidad de tests: 227/227 archivos en su techo; no hay backlog de tests en progreso (`test_quality_analyzer.txt`).

## Backlog priorizado (orden de implementacion)

### P0 - Arquitectura runtime y deuda de acoplamiento
1. ~~Retirar `flow_dialog_bridges`~~ **Hecho** (ITEM 003 fase B → utilidades en `core/flow_canvas_io.py`; módulo `flow_dialog_bridges` eliminado). ~~`create_dialog_compat`~~ retirado (ITEM 003 fase A).
   - Objetivo: menos indirecciones en flujo real.
   - Evidencia: `Documentacion/Refactorizacion_Completa/Arquitectura/puentes_compatibilidad_estado.md`.
2. Reducir ciclos que involucran `controllers.app_controller`.
   - Objetivo: disminuir acoplamiento transversal entre controladores.
   - Evidencia: `analyze_dependencies.txt`.

### P1 - Frontera UI/DTO (consistencia arquitectonica)
3. ~~Cerrar hallazgos restantes de frontera UI/DTO~~ **Hecho** (ITEM 001 + ITEM 002; catálogo UI/DTO en 0).
   - Objetivo: eliminar accesos tipo `vars(...).get(...)` y `dict` en UI donde deben ser DTO/servicio tipado.
   - Evidencia: `Documentacion/Refactorizacion_Completa/Fase_12C/ui_dto_boundary_report.md`.
   - **ITEM 001:** `ui/widgets/products_widget.py`. **ITEM 002:** `settings_widget` + `schedule_helpers` (ver `REGISTRO_EJECUCION_ITEMS.md`).

### P2 - Tipado estricto por lotes pequenos
4. Subir a estricto archivos con peor cobertura tipada y alta centralidad.
   - Lote sugerido A: `database/repositories/tracking_log_repository.py`.
   - Lote sugerido B: dialogs de `prep` y `product` con 0%.
   - Evidencia: `check_typing_coverage.txt`.

### P3 - Limpieza legacy puntual y segura
5. ~~Sustituir `print` de produccion por logger en `ui/widgets/products_widget.py`.~~ **Hecho** (ITEM 001).
6. ~~Reemplazar `bare except` en `ui/widgets/settings_widget.py`.~~ **Hecho** (ITEM 002, fallback descansos).
7. Normalizar docstrings/comentarios con marcador legacy solo donde aplique.
   - Evidencia: `legacy_report.md`.

## Plantilla operativa obligatoria por item

1. Baseline inicial (antes de tocar codigo)
   - `python3 -m pytest <tests_focales>`
   - `python3 -m mypy <modulos_focales> --config-file=mypy.ini`
2. Refactor minimo (solo alcance del item).
3. Tests del item
   - Crear tests nuevos si se introduce comportamiento nuevo.
   - Ajustar tests existentes si el contrato cambia.
4. Gates del item
   - `python3 -m pytest <tests_focales>`
   - `python3 -m mypy <modulos_focales> --config-file=mypy.ini`
5. Cierre global
   - `python3 -m mypy . --config-file=mypy.ini`
   - `python3 -m pytest -q`
6. Documentacion y cierre
   - `python3 scripts/generate_daniel_doc.py`
   - `python3 scripts/check_documentation_omissions.py`
   - Actualizar estado del item en la skill de ejecucion secuencial.

## Siguiente item candidato (ITEM 004 lote B)

Item: P2 — Mypy estricto en módulos UI de prep/product (o siguiente peor score en `check_typing_coverage.py`). Lote A: ~~`tracking_log_repository`~~ **Hecho** (REGISTRO).

Tests focales: tests de diálogos / widgets del módulo elegido.

### ITEM 001 (completado)

- Alcance: `ui/widgets/products_widget.py` (DTO subfabricaciones + logger).

### ITEM 002 (completado)

- Alcance: `ui/widgets/settings_widget.py`, `controllers/schedule_helpers.py` (`break_display_lines_from_json`).

### ITEM 003 fase A (completado)

- Alcance: `ui/dialogs/fabrication/create_dialog.py`; eliminado `create_dialog_compat.py`; import local en `settings_widget` (ciclo de imports).

### ITEM 003 fase B (completado)

- Alcance: consolidación en `core/flow_canvas_io.py`; eliminado `core/flow_dialog_bridges.py`; consumidores en production_flow y IO de flujo.

- Registro: `REGISTRO_EJECUCION_ITEMS.md`.

## Criterio de completado por item

- Tests focales y globales verdes.
- Mypy focal y global verde.
- Documentacion regenerada y `omitidos=0`.
- Item marcado `completado` en la skill y en este plan.
