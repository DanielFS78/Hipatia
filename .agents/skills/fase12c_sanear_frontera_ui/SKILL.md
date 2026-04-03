---
name: Fase 12C — Sanear Frontera UI/DTO
description: Frontera UI/DTO (cerrada 2026-03-20). Catálogo estricto en 0; bucle de mantenimiento y enlaces a scripts y doc en Fase_12C.
---

# Fase 12C — Sanear Frontera UI/DTO

## Objetivo

Garantizar que la capa **UI** consume **DTOs tipados** (atributos) y no datos sin tipar (dicts), eliminando:

- `obj["campo"]`
- `obj.get("campo")`

en rutas de `ui/` cuando el objeto debería ser un DTO.

> No se pretende eliminar todos los diccionarios: hay configuración serializable (canvas, production_flow) donde dict es legítimo. El objetivo es sanear la **frontera UI** (lo que viene de controllers/servicios/presenters).

---

## Fuente de verdad y documentación

| Recurso | Ruta |
|---------|------|
| Plan de calidad (hub) | `.agents/skills/plan_mejora_calidad/SKILL.md` |
| Docstrings / doc generada | `.agents/skills/estandar_documentacion/SKILL.md` |
| Testing | `.agents/skills/strict_testing/SKILL.md` y skills de testing |
| Guía del catálogo | `Documentacion/Refactorizacion_Completa/Fase_12C/README_catalogo_ui_dto.md` |

Tras cerrar un lote de archivos: `python3 scripts/generate_daniel_doc.py`.

---

## Inventario maestro (hallazgos + conexiones)

### Generar / actualizar catálogo

```bash
# Todos los .py bajo ui/, incluyendo production_flow (métrica estricta)
python3 scripts/ui_dto_findings_catalog.py

# Misma heurística que el analizador “relajado” (excluye production_flow por defecto)
python3 scripts/ui_dto_findings_catalog.py --no-production-flow
```

### Salidas

| Archivo | Contenido |
|---------|-----------|
| `Documentacion/Refactorizacion_Completa/Fase_12C/ui_dto_findings_catalog.json` | Cada ítem: `id` (F0001…), `file`, `line`, `kind`, `key`, `receiver`, `group_id`, `related_ids` (mismo receptor+archivo), `imports_sample`, `signature`, `status`. |
| `.../ui_dto_findings_catalog.md` | Vista legible (muestra). |
| `.../ui_dto_findings_checklist.md` | Tabla con `[ ]` / `[x]` por hallazgo. |

**Conexiones:** dos hallazgos con el mismo `group_id` comparten **archivo** y **expresión receptora** (AST); conviene corregirlos en la misma iteración.

**Persistencia de estado:** al regenerar el JSON, los ítems con `status: "hecho"` se restauran por **`signature`** (`file|kind|key|receiver`), no por `id`.

### Informe clásico (comparar métricas)

```bash
python3 scripts/ui_dto_boundary_analyzer.py
python3 scripts/ui_dto_boundary_analyzer.py --include-production-flow
```

- Sin `--include-production-flow`: foco fuera de `production_flow` / exclusiones por defecto.
- Con flag: alineado con el catálogo estricto.

---

## Progreso (actualizar tras cada lote cerrado)

| Lote | Fecha | Archivos / tema | Hallazgos cerrados (resumen) | Verificación |
|------|-------|-----------------|------------------------------|--------------|
| 1 | 2026-03-20 | `card_widget`, `workers_widget`+`worker_details_panel`, `main_window`; analizador ignora `os.environ.get` | Dict legado → `FlowTaskDataDTO.from_legacy_mapping`; asignación rápida encapsulada en panel; detección pytest con `os.getenv` | pytest: canvas_widgets, canvas_widgets_coverage, workers_widget, main_window; mypy en módulos tocados |
| 2 | 2026-03-20 | Biblioteca flujo: `ProductFlowLibraryProductDTO` + `prepare_task_data` (define + enhanced); `library_panel`, `define_control_panel`, `flow_graph_manager`; canvas: `core/flow_canvas_io.py`, `CanvasCyclicConnectionFlags`, `flow_canvas`+`flow_connection_painter`; `set_of_completer` en panel trabajador | Catálogo estricto 395→385 (~10 hallazgos); UI sin subíndices sobre `product_info` / `conn_data` en rutas tocadas | pytest: define/enhanced presenter, library_panel, flow_canvas, define_flow_dialog*, workers_widget; `mypy` 642 archivos OK |
| 3 | 2026-03-20 | `FlowInspectorTaskContext` + `get_task_inspector_context`; `enhanced_flow_dialog`; `core/flow_card_labels`, `core/flow_dialog_bridges`; `flow_card_widget`, `flow_canvas`, `flow_action_handler` | Catálogo 385→373 (~12 hallazgos); inspector sin `data['…']` en diálogo; tarjeta/canvas sin accesos dict locales; ciclo/reasignación vía core | pytest: flow_action_handler, flow_canvas, canvas_widgets_coverage, enhanced_flow_dialog; mypy 645 archivos OK |
| 4 | 2026-03-20 | `StartupSectionWidgets` en `startup_screen_ui` + `startup_screen`; `core/holidays_config_io.py`; festivos en `settings_widget_schedule_mixin`; `schedule_helpers` delega en core | Catálogo estricto 373→355 (~18); secciones de arranque por atributos; festivos sin `h[...]` en UI | pytest: schedule_controller_comprehensive, startup_* unit; mypy módulos tocados OK; `generate_daniel_doc` |
| 5 | 2026-03-20 | `CanvasVisualConnection` + helpers legacy en `core/flow_canvas_io.py`; `ui/dialogs/canvas_widget.py` sin `[]`/`.get` en pintado e indice de tarea | Catálogo 355→348 (~7); `set_connections` acepta dict o DTO | pytest: test_canvas_widgets, test_canvas_widgets_coverage; mypy `flow_canvas_io` + `canvas_widget` |
| 6 | 2026-03-20 | `cycle_end_config_dialog` + `flow_dialog_bridges` (`canvas_task_display_name`, flags fin/retorno ciclo); reutiliza `legacy_*` de `flow_canvas_io` | Catálogo 348→340 (~8); UI sin `.get`/`[]` sobre tareas canvas en ese dialogo | pytest: common_production_dialogs, common_dialogs CycleEnd, dialog_integration_smoke CycleEnd; mypy OK |
| 7 | 2026-03-20 | `core/flow_graph_manager_io.py`; `flow_graph_manager` + `ProductionFlowCanvas`; `CanvasVisualConnection` con flags ciclo; `connection_cyclic_paint_flags` | Catálogo 340→286 (~54); conexiones logicas y carga de flujo fuera de subscripts en UI | pytest: test_flow_canvas, ProductionFlowCanvas coverage, enhanced_flow_dialog, flow_action_handler; mypy OK |
| 8 | 2026-03-20 | `core/define_flow_form_io.py`; `define_flow_dialog` usa `define_form_data_to_flow_task_config` (sin `form_data[...]`) | Catálogo 286→278 (~8) | pytest: test_define_flow_dialog, test_define_flow_dialog_edge; mypy OK |
| 9 | 2026-03-20 | `core/define_flow_presenter_io.py`; `DefineFlowPresenter.prepare_task_data` + `set_production_flow` sin `.get`/`[]` sobre mapas crudos | Catálogo 278→247 (~31) | pytest: test_define_flow_presenter, define_flow_dialog*; mypy OK |
| 10 | 2026-03-20 | `core/enhanced_flow_presenter_io.py`; mixin `enhanced_flow_presenter_builder` delega carga/export/normalizacion; reutiliza `flow_graph_manager_io` + `flow_dialog_bridges` | Catálogo 247→184 (~63) | pytest: test_enhanced_flow_presenter; mypy OK |
| 11 | 2026-03-20 | `InspectorWidgets` + `build_inspector_ui`; `inspector_panel` / `inspector_task_loader`; `core/inspector_task_payload_io.py`; fechas en `QDateTimeEdit` tipadas (`QDate`→medianoche) | Catálogo 184→64 (~120); `inspector_ui`/`inspector_task_loader` fuera del catálogo | pytest: test_inspector_panel; mypy módulos inspector + payload_io; `generate_daniel_doc` |
| 12 | 2026-03-20 | `inspector_presenter.py` delega en `inspector_task_payload_io` (`inspector_row_id`, workers, dependencias); lectura de listas sin mutar `config` vacío | Catálogo 64→52 (~12); eje inspector cerrado en catálogo | pytest: test_inspector_presenter, test_inspector_panel; mypy payload_io + presenter |
| 13 | 2026-03-20 | `core/enhanced_flow_canvas_state_io.py`; `enhanced_flow_presenter_state.py` delega CRUD/reindex/ciclo/inspector/simulación/conexiones | Catálogo 52→16 (~36); `enhanced_flow_presenter_state` fuera del catálogo | pytest: test_enhanced_flow_presenter, test_enhanced_flow_dialog; mypy |
| 14 | 2026-03-20 | `reassignment_rule_dialog_io`, `definir_cantidades_dialog_io`; `flow_task_payload_set_canvas_unique_id` | Catálogo estricto **16 → 0** (incl. `production_flow`) | `run_tests.py` en verde; mypy en módulos tocados; `generate_daniel_doc` |
| 15 | 2026-04-03 | Regresión menor: helpers en `core/flow_canvas_io.py` (`flow_task_config_cycle_return_to_index`, `cycle_end_dialog_configuration_values`, `worker_line_config_*`); `cycle_end_config_dialog` + `flow_action_handler` sin `.get`/`[]` en UI | Catálogo estricto **6 → 0** | pytest: `test_flow_action_handler`, `TestCycleEndConfigDialog` (common_dialogs + common_production); `generate_daniel_doc` |

### Estado tras cierre (2026-04-03)

- Catálogo estricto en **0** hallazgos — `python3 scripts/ui_dto_findings_catalog.py` y `ui_dto_boundary_analyzer.py --include-production-flow`.
- Suite completa: ejecutar `python3 run_tests.py` tras cambios amplios (esta pasada: tests focalizados arriba).

**Mantenimiento:** si en `ui/` reaparecen `[]` / `.get` sobre datos que deban tratarse como DTO, regenerar el catálogo y cerrar en `core/` con helpers (mismo criterio que en los lotes 1–14).

---

## Reglas de actuación (conservadoras)

- Máximo **2–3 archivos** de producción por iteración (tests aparte).
- Preferir que **presenter/servicio/controller** entregue DTO; la UI solo atributos.
- Evitar `getattr(x, "k", x.get("k"))` como parche permanente.
- Tras tocar `.py`: docstrings en español (módulo/clase/método según alcance).

---

## Bucle determinista (un ítem o un grupo por vuelta)

1. `python3 scripts/ui_dto_findings_catalog.py` (o leer JSON existente).
2. Elegir el **primer** ítem con `status != "hecho"` (idealmente todo un `group_id` junto).
3. Corregir con contrato DTO / encapsulación; no expandir el alcance.
4. Tests de scope: `python3 -m pytest <archivos> -x -q`.
5. `python3 run_tests.py` cuando el cambio sea transversal.
6. `python3 -m mypy . --config-file mypy.ini` si se tocan tipos.
7. Marcar en **`ui_dto_findings_catalog.json`** los ítems cerrados como `"status": "hecho"` (o marcar `[x]` en el checklist y volver a generar JSON manualmente coherente).
8. `python3 scripts/ui_dto_findings_catalog.py` de nuevo para refrescar totales y conservar `hecho` por firma.
9. Actualizar la tabla **Progreso** de esta skill.
10. `python3 scripts/generate_daniel_doc.py` si hubo cambios documentables.

---

## Criterio de cierre de fase

**Satisfecho el 2026-03-20:**

- Catálogo estricto (`include_production_flow=True`): **0** hallazgos.
- `python3 run_tests.py`: todos los tests pasan.
- Documentación técnica al día (`python3 scripts/generate_daniel_doc.py`).

Si en el futuro el catálogo deja de estar en cero, aplicar de nuevo el bucle determinista de arriba hasta recuperar **0** o documentar explícitamente los dicts que sigan siendo aceptables fuera de la frontera UI→DTO.
