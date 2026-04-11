# Informe de Código Legacy — Fase 4

> **Fecha:** 2026-04-11 08:28:46
> **Generado por:** `scripts/legacy_analyzer.py`

---

## 1. Resumen

| Categoría | Cantidad |
|-----------|----------|
| print_en_produccion | 0 |
| bare_except | 0 |
| deprecated_markers | 0 |
| docstring_legacy | 20 |
| simple_delegation | 0 |
| legacy_comment | 8 |

---

## 5. Docstrings con obsoleto/legacy/deprecated

Revisar si el símbolo debe eliminarse o actualizar el docstring.

| Archivo | Línea | Símbolo | Tipo | Palabra clave |
|---------|-------|---------|------|---------------|
| controllers/schedule_controller.py | 34 | `ScheduleController` | class | legacy |
| controllers/schedule_controller.py | 94 | `on_add_break` | function | legacy |
| controllers/schedule_helpers.py | 55 | `normalize_holidays` | function | legacy |
| controllers/schedule_ui_helper.py | 187 | `on_add_break` | function | legacy |
| controllers/schedule_ui_helper.py | 220 | `add_break` | function | legacy |
| controllers/schedule_ui_helper.py | 232 | `delete_break` | function | legacy |
| controllers/schedule_ui_helper.py | 246 | `save_work_hours` | function | legacy |
| controllers/worker/protocols.py | 84 | `IWorkerModel` | class | legacy |
| core/define_flow_presenter_io.py | 67 | `find_first_positive_duration` | function | legacy |
| core/flow_canvas_io.py | 53 | `legacy_canvas_task_widget` | function | legacy |
| core/flow_canvas_io.py | 58 | `legacy_canvas_task_config` | function | legacy |
| core/flow_canvas_io.py | 64 | `legacy_canvas_task_is_cycle_start` | function | legacy |
| core/flow_canvas_io.py | 96 | `flow_task_config_cycle_return_to_index` | function | legacy |
| core/flow_canvas_io.py | 136 | `connection_cyclic_paint_flags` | function | legacy |
| scripts/test_quality_analyzer.py | 490 | `resolve_analyzer_status` | function | legacy |
| ui/dialogs/canvas_widget.py | 27 | `CanvasWidget` | class | legacy |
| ui/dialogs/canvas_widget.py | 48 | `set_connections` | function | legacy |
| ui/dialogs/product/procesos_mecanicos_dialog.py | 62 | `_normalize_procesos` | function | legacy |
| ui/main_window.py | 190 | `buttons` | function | legacy |
| ui/main_window.py | 256 | `run_simulation_and_display` | function | legacy |

---

## 7. Comentarios legacy / re-export

| Archivo | Línea | Contexto |
|---------|-------|----------|
| controllers/product/protocols.py | 19 | `# Reexport para imports existentes `from controllers.product.protocols` |
| controllers/schedule_ui_helper.py | 218 | `# --- API programática (antes ScheduleLegacyApiHelper; composición uni` |
| core/services/backup_service.py | 7 | `import hashlib  # Compatibilidad para tests legacy que parchean este s` |
| core/services/backup_service.py | 248 | `# Compatibilidad API legacy (tests y callers antiguos)` |
| core/simulation/engine/motor.py | 108 | `# Compatibilidad para dicts legacy que puedan tener 'tiempo' en lugar ` |
| tests/unit/test_define_flow_presenter.py | 208 | `# 10 / 0 guard -> total_cycles no se calcula en group_tasks ahora sino` |
| ui/dialogs/fabrication/create_dialog.py | 39 | `# API legacy (alias de la pestaña de preprocesos; sin capa intermedia)` |
| ui/dialogs/product/bom_import_preview_dialog.py | 290 | `# Compat: mantener hint legacy alineado con subfabricación explícita` |

---

## 8. Orden de actuación recomendado

1. **print → logger** en producción (evitar falsos positivos en scripts/tests).
2. **Bare except** → `except Exception` + logging.
3. **Docstrings legacy**: actualizar o eliminar API obsoleta.
4. **Delegaciones**: comprobar referencias; si no hay usos, eliminar y redirigir.
5. **Marcadores y comentarios**: eliminar código marcado o actualizar documentación.

Tras cada cambio: ejecutar `python3 -m pytest <scope> -x -q` y `python3 run_tests.py`.

*Generado — 2026-04-11*