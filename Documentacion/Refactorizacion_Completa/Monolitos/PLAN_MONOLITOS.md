## Plan integral — Fase Monolitos (2026)

### Estado actual (baseline)

- Reporte generado por: `python3 scripts/monolith_analyzer.py --min-loc 250 --top 30`
- Output:
  - `Documentacion/Refactorizacion_Completa/Monolitos/monolith_report.md`
  - `Documentacion/Refactorizacion_Completa/Monolitos/monolith_report.json`

El reporte actual identifica:
- Un conjunto de **archivos grandes (250+ LOC)** priorizados por LOC e impacto (in/out degree).
- **0 ciclos (SCC)** en runtime (los imports bajo `TYPE_CHECKING` se ignoran en el analizador).

### Objetivo de la fase

- Reducir **tamaño** y **acoplamiento** de los top monolitos (250+ LOC).
- Romper ciclos de dependencias (SCC) cuando sea razonable.
- Mantener estabilidad:
  - `python3 run_tests.py` debe pasar siempre.
  - Calidad de tests no debe empeorar.
  - **Obligatorio**: cualquier cambio en código exige **tests nuevos/actualizados** cumpliendo reglas estrictas y persiguiendo **100% de cobertura** en los archivos tocados.

### Estrategia (orden de ejecución)

1) **Cortes “seguros” en UI** (alto LOC, bajo in_degree):
   - Extraer estilos/QSS, helpers de formateo, renderers, y sub-widgets a módulos específicos.
   - Ventaja: mínimo riesgo sobre lógica de negocio.

2) **Cortes en controllers con acoplamiento** (alto in_degree):
   - Extraer “adaptadores” y “managers” (ya hay precedentes: `product_manager`, `preproceso_manager`, etc.).
   - Convertir imports cruzados a:
     - interfaces/protocols
     - inyección por DIContainer
     - imports locales donde aplique

3) **Romper ciclos (SCC)**
   - Atacar el ciclo de 2 módulos primero (`controllers/report_controller.py` ↔ `ui/widgets/reportes_widget.py`).
   - Luego el SCC de 15 módulos con estrategia incremental:
     - extraer interfaces (core/interfaces)
     - mover wiring a Startup/DI
     - evitar que UI importe controllers y viceversa (una sola dirección)

### Métrica de salida (“Definition of Done”)

- No quedan archivos por encima del umbral objetivo (o quedan documentados como “techo real” con justificación).
- Los SCC se reducen (ideal: 0 ciclos) o quedan documentados con razón.
- `run_tests.py` pasa.
- `python3 scripts/coverage_focus.py --paths <tocados> ...` confirma **100%** en los archivos tocados.

### Operativa (autopilot)

Ver `.agents/skills/fase_monolitos_autopilot/SKILL.md`.

### Registro de iteraciones (progreso)

#### 2026-03-17 — Iteración 1

- **Corte aplicado**: `ui/dialogs/canvas_widgets.py` → módulos más pequeños con compat:
  - **Nuevo**: `ui/dialogs/canvas_widget.py` (`CanvasWidget`)
  - **Nuevo**: `ui/dialogs/card_widget.py` (`CardWidget`)
  - **Compat**: `ui/dialogs/canvas_widgets.py` re-exporta ambos (`__all__`).
- **Tests**: se mantienen `tests/unit/test_canvas_widgets.py` y `tests/unit/test_canvas_widgets_coverage.py`.
- **Cobertura**: `coverage_focus` exige 100% en los 3 archivos tocados ✅

#### 2026-03-17 — Iteración 2

- **Corte aplicado**: `ui/dialogs/production_flow/enhanced_flow_presenter.py` (monolito 385+ LOC) dividido en mixins:
  - **Nuevo**: `ui/dialogs/production_flow/enhanced_flow_presenter_state.py`
  - **Nuevo**: `ui/dialogs/production_flow/enhanced_flow_presenter_builder.py`
  - `ui/dialogs/production_flow/enhanced_flow_presenter.py` queda como façade + constructor.
- **Tests**:
  - `tests/unit/test_enhanced_flow_presenter.py` ampliado para cubrir ramas nuevas (skip de steps/subtasks inválidos).
- **Cobertura**: `coverage_focus` 100% en los 3 archivos del presenter ✅
- **Suite**: `python3 run_tests.py` ✅

#### 2026-03-17 — Iteración 3

- **Corte aplicado**: `ui/startup_screen.py` (432 → 356 LOC):
  - **Nuevo**: `ui/startup_screen_constants.py` (`STATUS_COLORS`, `AUTO_ADVANCE_SECONDS`).
  - **Nuevo**: `ui/startup_screen_report.py` (`generate_startup_report_text(report, log_path=None)`).
  - `ui/startup_screen.py` importa ambos y delega la generación del informe.
- **Tests**:
  - `tests/unit/test_startup_screen_constants.py` (constantes).
  - `tests/unit/test_startup_screen_report.py` (generación de informe, 100% cobertura).
- **Cobertura**: 100% en los dos módulos nuevos ✅
- **Suite**: `python3 run_tests.py` ✅

#### 2026-03-19 — Iteración 4

- **Corte aplicado**: `controllers/simulation/execution_manager.py` (>=250 LOC) con extracción de bloques repetidos de ejecución.
  - **Nuevo**: `controllers/simulation/execution_helpers.py`
  - Bloques extraídos: construcción de scheduler, arranque de hilo de optimizador, habilitación de botones de resultados y set de unidades de planning.
- **Resultado**: `execution_manager.py` sale del ranking de monolitos (`min_loc=250`) ✅
- **Validación**:
  - `python3 -m mypy controllers/simulation/execution_manager.py controllers/simulation/execution_helpers.py controllers/simulation/controller.py` ✅
  - `python3 -m pytest -q tests/unit/test_simulation_controller_comprehensive.py` ✅ (35 passed)

#### 2026-03-19 — Iteración 5

- **Corte aplicado**: `core/health/health_checker.py` (>=250 LOC) con extracción de constantes de dominio.
  - **Nuevo**: `core/health/constants.py`
  - Constantes extraídas: `TABLE_FRIENDLY`, `CRITICAL_TABLES`, `THRESHOLDS`.
- **Resultado**: `health_checker.py` sale del ranking de monolitos (`min_loc=250`) ✅
- **Validación**:
  - `python3 -m mypy core/health/health_checker.py core/health/constants.py` ✅
  - `python3 -m pytest -q tests/unit/test_health_checker.py tests/unit/test_health_test_runner.py` ✅ (25 passed)

#### 2026-03-19 — Iteración 6

- **Corte aplicado**: `ui/dialogs/fabrication/create_dialog.py` (>=250 LOC) con extracción de compatibilidad legacy.
  - **Nuevo**: `ui/dialogs/fabrication/create_dialog_compat.py`
  - API legacy movida a mixin: `search_entry`, `available_list`, `assigned_list`, `add_button`, `remove_button` y wrappers legacy.
- **Resultado**: `create_dialog.py` sale del ranking de monolitos (`min_loc=250`) ✅
- **Validación**:
  - `python3 -m mypy ui/dialogs/fabrication/create_dialog.py ui/dialogs/fabrication/create_dialog_compat.py` ✅
  - `python3 -m pytest -q tests/unit/test_create_dialog.py tests/unit/test_create_fabricacion_dialog.py tests/unit/test_fabrication_dialogs_coverage.py` ✅ (41 passed)

#### Estado del ranking tras Iteración 6

- `python3 scripts/monolith_analyzer.py --min-loc 250 --top 30` → **26** monolitos restantes.
- Eliminados en este ciclo: `controllers/simulation/execution_manager.py`, `core/health/health_checker.py`, `ui/dialogs/fabrication/create_dialog.py`.

#### 2026-03-19 — Iteración 7

- **Corte aplicado**: `core/services/backup_service.py` (>=250 LOC) con separación de utilidades de checksum/verificación.
  - **Nuevo**: `core/services/backup_utils.py`
  - Se mantiene **API legacy privada** (`_check_disk_space`, `_verify_backup`, `_create_checksum`, `_verify_checksum`) para no romper tests ni monkeypatches existentes.
- **Resultado**: `backup_service.py` sale del ranking de monolitos (`min_loc=250`) ✅
- **Validación**:
  - `python3 -m mypy core/services/backup_service.py core/services/backup_utils.py` ✅
  - `python3 -m pytest -q tests/unit/test_backup_service.py tests/unit/test_backup_controller.py tests/unit/test_backup_controller_comprehensive.py` ✅ (44 passed)

#### Estado del ranking tras Iteración 7

- `python3 scripts/monolith_analyzer.py --min-loc 250 --top 30` → **25** monolitos restantes.

#### 2026-03-19 — Iteración 8

- **Corte aplicado**: `controllers/schedule_controller.py` (>=250 LOC) con extracción de helpers y operaciones UI.
  - **Nuevo**: `controllers/schedule_helpers.py` (parse/normalización JSON).
  - **Nuevo**: `controllers/schedule_ui_ops.py` (operaciones UI: breaks + save/load).
  - **Nuevo**: `controllers/schedule_legacy_api.py` (API legacy duplicada aislada).
- **Compatibilidad de tests**: `ScheduleUiOpsMixin` hace lookup de `AddBreakDialog/QDialog/...` vía `controllers.schedule_controller` para respetar parches existentes.
- **Resultado**: `schedule_controller.py` sale del ranking de monolitos (`min_loc=250`) ✅
- **Validación**:
  - `python3 -m mypy controllers/schedule_controller.py controllers/schedule_helpers.py controllers/schedule_ui_ops.py controllers/schedule_legacy_api.py` ✅
  - `python3 -m pytest -q tests/unit/test_schedule_controller_comprehensive.py` ✅ (24 passed)

#### 2026-03-19 — Iteración 9

- **Corte aplicado**: `ui/widgets/production_flow/inspector_panel.py` (>=250 LOC) con extracción de construcción de UI y carga de tarea.
  - **Nuevo**: `ui/widgets/production_flow/inspector_ui.py` (builder UI + wiring de señales, conserva `widgets[...]`).
  - **Nuevo**: `ui/widgets/production_flow/inspector_task_loader.py` (lógica de `set_task`).
- **Resultado**: `inspector_panel.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 132)
- **Validación**:
  - `python3 -m mypy ui/widgets/production_flow/inspector_panel.py ui/widgets/production_flow/inspector_ui.py ui/widgets/production_flow/inspector_task_loader.py` ✅
  - `python3 -m pytest -q tests/unit/test_inspector_panel.py` ✅ (6 passed)

#### 2026-03-19 — Iteración 10

- **Corte aplicado**: `ui/startup_screen.py` (>=250 LOC) con extracción de helpers de UI para construcción/render.
  - **Nuevo**: `ui/startup_screen_ui.py`
    - `build_startup_ui(screen)` (construye la UI y asigna atributos del diálogo).
    - `render_db_report(screen, report)` (pinta resultados del `HealthReport` en la sección de BD).
- **Resultado**: `startup_screen.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 223)
- **Validación**:
  - `python3 -m mypy ui/startup_screen.py ui/startup_screen_ui.py` ✅
  - `python3 -m pytest -q tests/unit/test_startup_screen_constants.py tests/unit/test_startup_screen_report.py` ✅ (10 passed)

#### 2026-03-19 — Iteración 11

- **Corte aplicado**: `core/app_model.py` (>=250 LOC) con extracción conservadora por dominios a mixins (sin cambiar API pública).
  - **Nuevo**: `core/app_model_fabricacion_mixin.py` (fabricaciones + preprocesos).
  - **Nuevo**: `core/app_model_product_mixin.py` (productos + iteraciones + materiales).
  - **Nuevo**: `core/app_model_pila_mixin.py` (pilas + diario + cálculo).
  - **Nuevo**: `core/app_model_resources_mixin.py` (trabajadores/máquinas/preparación + stats dashboard).
  - **Nuevo**: `core/app_model_reports_mixin.py` (reporting).
  - **Nuevo**: `core/app_model_legacy_repos_mixin.py` (delegación legacy a repos: lotes/config/tracking).
- **Nota técnica**: se evitó `Protocol` en mixins por conflicto de metaclases con `PyQt6.QtCore.QObject`.
- **Resultado**: `app_model.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 193)
- **Validación**:
  - `python3 -m mypy core/app_model.py core/app_model_*_mixin.py` ✅
  - `python3 -m pytest -q tests/unit/test_app_model.py tests/unit/test_app_model_coverage.py` ✅ (41 passed)

#### 2026-03-19 — Iteración 12

- **Corte aplicado**: `features/worker_controller.py` (>=250 LOC) con extracción de UI/IO y diálogo de incidencias.
  - **Nuevo**: `features/worker_incidence_dialog.py` (`IncidenceDialog`).
  - **Nuevo**: `features/worker_controller_io_mixin.py` (`_handle_generate_labels`, `_process_label_document`, `_handle_export_data`, `_handle_camera_config`).
  - `features/worker_controller.py` conserva API/handlers y re-exporta `IncidenceDialog` para compatibilidad con parches de tests por ruta.
- **Resultado**: `worker_controller.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 206)
- **Validación**:
  - `python3 -m mypy features/worker_controller.py features/worker_controller_io_mixin.py features/worker_incidence_dialog.py` ✅
  - `python3 -m pytest -q tests/unit/test_features_worker_controller.py` ✅ (7 passed)

#### 2026-03-19 — Iteración 13

- **Corte aplicado**: `core/simulation/timeline_task.py` (>=250 LOC) con extracción de lógica de instancias paralelas.
  - **Nuevo**: `core/simulation/timeline_task_parallel.py`
    - `agregar_instancia_paralela_ops(...)`
    - `completar_unidad_instancia_ops(...)`
  - `LineaTemporalTarea` mantiene su API pública; los métodos delegan a helpers puros para reducir tamaño y acoplamiento.
- **Resultado**: `timeline_task.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 225)
- **Validación**:
  - `python3 -m mypy core/simulation/timeline_task.py core/simulation/timeline_task_parallel.py` ✅
  - `python3 -m pytest -q tests/unit/test_simulation_events_comprehensive.py` ✅ (22 passed)

#### 2026-03-19 — Iteración 14

- **Corte aplicado**: `database/repositories/product_repository.py` (>=250 LOC) con extracción de mapeos y consulta por fabricación.
  - **Nuevo**: `database/repositories/product_repository_helpers.py`
    - `to_product_dto`, `to_subfabricacion_dto`, `to_proceso_mecanico_dto`, `normalize_machine_id`.
  - **Nuevo**: `database/repositories/product_repository_fabricacion_mixin.py`
    - `get_products_by_fabricacion(...)` extraído para reducir tamaño y mantener interfaz.
  - `ProductRepository` mantiene API pública y comportamiento; solo delega internamente.
- **Resultado**: `product_repository.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 245)
- **Validación**:
  - `python3 -m mypy database/repositories/product_repository.py database/repositories/product_repository_helpers.py database/repositories/product_repository_fabricacion_mixin.py` ✅
  - `python3 -m pytest -q tests/unit/test_product_repository.py tests/db/test_product_repository.py` ✅ (44 passed)

#### 2026-03-19 — Iteración 15

- **Corte aplicado**: `ui/dialogs/production_flow/common_dialogs.py` (>=250 LOC) con separación por diálogo y façade de compatibilidad.
  - **Nuevo**: `ui/dialogs/production_flow/cycle_end_config_dialog.py`
  - **Nuevo**: `ui/dialogs/production_flow/reassignment_rule_dialog.py`
  - **Nuevo**: `ui/dialogs/production_flow/definir_cantidades_dialog.py`
  - `common_dialogs.py` queda como re-export/compat (`CycleEndConfigDialog`, `ReassignmentRuleDialog`, `DefinirCantidadesDialog`) y además re-exporta `QBrush`, `QColor`, `QFont`, `QListWidgetItem` para respetar tests que parchean por ruta.
- **Resultado**: `common_dialogs.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 15)
- **Validación**:
  - `python3 -m mypy ui/dialogs/production_flow/common_dialogs.py ui/dialogs/production_flow/cycle_end_config_dialog.py ui/dialogs/production_flow/reassignment_rule_dialog.py ui/dialogs/production_flow/definir_cantidades_dialog.py` ✅
  - `python3 -m pytest -q tests/unit/test_common_production_dialogs.py tests/unit/test_common_dialogs.py tests/unit/test_dialog_integration_smoke.py` ✅ (65 passed)

#### 2026-03-19 — Iteración 16

- **Corte aplicado**: `core/dtos.py` (>=250 LOC) con separación de definiciones y façade estable.
  - **Nuevo**: `core/dtos_models.py` (definiciones dataclass de todos los DTOs).
  - `core/dtos.py` se mantiene como punto de import público y re-exporta exactamente los mismos símbolos (`__all__` explícito).
- **Resultado**: `dtos.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 75)
- **Validación**:
  - `python3 -m mypy core/dtos.py core/dtos_models.py` ✅
  - `python3 -m pytest -q tests/unit/test_app_model.py tests/unit/test_define_flow_dialog.py tests/unit/test_define_flow_presenter.py tests/unit/test_camera_config_dialog.py tests/unit/test_camera_config_presenter.py tests/unit/test_product_repository.py tests/db/test_product_repository.py` ✅ (131 passed)

#### 2026-03-19 — Iteración 17

- **Corte aplicado**: `controllers/report_controller.py` (>=250 LOC) con extracción de exportaciones de alto tamaño.
  - **Nuevo**: `controllers/report_controller_export_mixin.py`
    - `on_export_to_excel_clicked(...)`
    - `on_export_gantt_to_pdf_clicked(...)`
    - helper `_extract_fab_info_from_calc_page(...)`
  - Compatibilidad de tests preservada: el mixin resuelve símbolos parcheables (`QFileDialog`, `QApplication`, `GeneradorDeInformes`, estrategias) desde `controllers.report_controller`.
- **Resultado**: `report_controller.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 219)
- **Validación**:
  - `python3 -m mypy controllers/report_controller.py controllers/report_controller_export_mixin.py` ✅
  - `python3 -m pytest -q tests/unit/test_report_controller_comprehensive.py tests/unit/test_reportes_widget.py tests/unit/test_ui_signals_controller_comprehensive.py` ✅ (65 passed)

#### 2026-03-19 — Iteración 18

- **Corte aplicado**: `core/dtos_models.py` (>=250 LOC) con partición por dominios manteniendo contrato estable.
  - **Nuevo**: `core/dtos_catalog.py` (DTOs de catálogo/producción).
  - **Nuevo**: `core/dtos_flow_camera.py` (DTOs de flujo de producción/cámara).
  - `core/dtos_models.py` queda como agregador tipado y `core/dtos.py` mantiene fachada pública.
- **Resultado**: `dtos_models.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 135)
- **Validación**:
  - `python3 -m mypy core/dtos.py core/dtos_models.py core/dtos_catalog.py core/dtos_flow_camera.py` ✅
  - `python3 -m pytest -q tests/unit/test_app_model.py tests/unit/test_define_flow_dialog.py tests/unit/test_define_flow_presenter.py tests/unit/test_camera_config_dialog.py tests/unit/test_camera_config_presenter.py tests/unit/test_product_repository.py tests/db/test_product_repository.py` ✅ (131 passed)

#### 2026-03-19 — Iteración 19

- **Corte aplicado**: `ui/widgets/reports/charts_container.py` (>=250 LOC) con extracción de componentes reutilizables sin alterar comportamiento de gráficos.
  - **Nuevo**: `ui/widgets/reports/stat_card.py` (`StatCard` aislado).
  - **Nuevo**: `ui/widgets/reports/charts_renderers.py` (helpers seguros: limpieza y tarjetas).
  - `charts_container.py` conserva lógica de QtCharts inline para respetar patching de tests existentes.
- **Resultado**: `charts_container.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 246)
- **Validación**:
  - `python3 -m mypy ui/widgets/reports/charts_container.py ui/widgets/reports/charts_renderers.py ui/widgets/reports/stat_card.py` ✅
  - `python3 -m pytest -q tests/unit/test_charts_container.py tests/unit/test_charts_widget.py tests/unit/test_reports_widgets.py` ✅ (65 passed)

#### 2026-03-19 — Iteración 22

- **Corte aplicado**: `controllers/backup_controller.py` (>=250 LOC) con extracción conservadora de operaciones manuales I/O.
  - **Nuevo**: `controllers/backup_controller_io_mixin.py`
    - `on_import_databases(...)`
    - `on_export_databases(...)`
    - `on_sync_databases(...)`
  - `BackupController` mantiene API pública; la lógica de backup automático permanece in-place.
  - Compatibilidad de tests preservada: el mixin resuelve símbolos parcheables (`QFileDialog`, `QApplication`, `QDialog`, `resource_path`, `zipfile`) desde `controllers.backup_controller`.
- **Resultado**: `backup_controller.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 169)
- **Validación**:
  - `python3 -m mypy controllers/backup_controller.py controllers/backup_controller_io_mixin.py` ✅
  - `python3 -m pytest -q tests/unit/test_backup_controller.py tests/unit/test_backup_controller_comprehensive.py tests/unit/test_backup_integration.py tests/unit/test_ui_signals_controller_comprehensive.py` ✅ (66 passed)
  - `python3 scripts/coverage_focus.py --paths controllers/backup_controller.py controllers/backup_controller_io_mixin.py --tests tests/unit/test_backup_controller.py tests/unit/test_backup_controller_comprehensive.py tests/unit/test_backup_integration.py` ✅ (cobertura 100% en archivos tocados)

#### 2026-03-19 — Iteración 23

- **Corte aplicado**: `database/repositories/iteration_repository.py` (>=250 LOC) con extracción de operaciones CRUD a mixin dedicado.
  - **Nuevo**: `database/repositories/iteration_repository_crud_mixin.py`
    - `add_product_iteration(...)`
    - `update_product_iteration(...)`
    - `delete_product_iteration(...)`
    - `update_iteration_image_path(...)`
    - `update_iteration_file_path(...)`
  - `IterationRepository` mantiene API pública, delega CRUD al mixin y conserva consultas/listados en el archivo principal.
- **Resultado**: `iteration_repository.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 75)
- **Validación**:
  - `python3 -m mypy database/repositories/iteration_repository.py database/repositories/iteration_repository_crud_mixin.py` ✅
  - `python3 -m pytest -q tests/unit/test_iteration_repository.py tests/integration/test_iteration_integration.py tests/e2e/test_iteration_workflow.py` ✅ (25 passed)
  - `python3 scripts/coverage_focus.py --paths database/repositories/iteration_repository.py database/repositories/iteration_repository_crud_mixin.py --tests tests/unit/test_iteration_repository.py tests/integration/test_iteration_integration.py tests/e2e/test_iteration_workflow.py` ✅ (cobertura 100% en archivos tocados)

#### 2026-03-19 — Iteración 24

- **Ajuste de criterio (usuario)**:
  - Un archivo <= 300 LOC no se considera monolito por tamaño.
  - Priorizar solo archivos cercanos a 400 LOC o archivos con alta densidad funcional.
- **Corte aplicado por densidad funcional**: `controllers/product/product_manager.py` (18 funciones en 295 LOC).
  - **Nuevo**: `controllers/product/product_manager_iteration_mixin.py`
    - `handle_add_product_iteration(...)`
    - `handle_update_product_iteration(...)`
    - `handle_delete_product_iteration(...)`
    - `handle_add_iteration_image(...)`
    - `handle_delete_iteration_image(...)`
  - `ProductManager` mantiene la API pública y delega esas operaciones al mixin.
- **Validación**:
  - `python3 -m mypy controllers/product/product_manager.py controllers/product/product_manager_iteration_mixin.py` ✅
  - `python3 -m pytest -q tests/controllers/product/test_product_manager.py tests/unit/test_product_controller_v2_comprehensive.py tests/unit/test_product_controller_preprocesos.py tests/unit/test_security_phase2_integration.py` ✅ (117 passed)
  - `python3 scripts/coverage_focus.py --paths controllers/product/product_manager.py controllers/product/product_manager_iteration_mixin.py --tests tests/controllers/product/test_product_manager.py tests/unit/test_product_controller_v2_comprehensive.py tests/unit/test_product_controller_preprocesos.py tests/unit/test_security_phase2_integration.py` ✅ (cobertura 100% en archivos tocados)
- **Estado del nuevo umbral de tamaño**:
  - `python3 scripts/monolith_analyzer.py --min-loc 400 --out-dir Documentacion/Refactorizacion_Completa/Monolitos` → `ranked_monoliths = 0`.

#### 2026-03-19 — Iteración 25

- **Corte aplicado por densidad funcional**: `database/repositories/material_repository.py` (alta concentración de métodos de relación/CRUD).
  - **Nuevo**: `database/repositories/material_repository_links_mixin.py`
    - `link_material_to_product(...)`
    - `unlink_material_from_product(...)`
    - `link_material_to_iteration(...)`
    - `delete_material_link_from_iteration(...)`
  - `MaterialRepository` mantiene API pública; delega relaciones al mixin.
- **Ajuste conservador adicional**:
  - Simplificación de ramas redundantes en `add_material(...)` y `delete_material(...)` para reducir complejidad accidental sin cambiar contrato externo.
- **Tests añadidos/mejorados**:
  - `tests/repositories/test_material_repository.py` cubre casos de éxito/idempotencia/entidades ausentes para vínculos de producto e iteración, actualización exitosa, borrado y stats.
- **Validación**:
  - `python3 -m mypy database/repositories/material_repository.py database/repositories/material_repository_links_mixin.py tests/repositories/test_material_repository.py` ✅
  - `python3 -m pytest -q tests/repositories/test_material_repository.py` ✅ (14 passed)
  - `python3 scripts/coverage_focus.py --paths database/repositories/material_repository.py database/repositories/material_repository_links_mixin.py --tests tests/repositories/test_material_repository.py` ✅ (cobertura 100% en archivos tocados)
- **Estado del criterio de tamaño**:
  - `python3 scripts/monolith_analyzer.py --min-loc 400 --out-dir Documentacion/Refactorizacion_Completa/Monolitos` → `ranked_monoliths = 0`.

#### 2026-03-19 — Iteración 26

- **Corte aplicado por densidad funcional**: `core/services/product_service.py` (múltiples métodos de delegación en un único archivo).
  - **Nuevo**: `core/services/product_service_delegation_mixin.py`
    - delegaciones de iteraciones:
      - `get_product_iterations(...)`
      - `add_product_iteration(...)`
      - `update_product_iteration_details(...)`
      - `update_product_iteration(...)`
      - `delete_product_iteration(...)`
      - `get_all_iterations_with_dates(...)`
      - `add_iteration_image(...)`
      - `delete_iteration_image(...)`
      - `update_iteration_file_path(...)`
    - delegaciones de materiales:
      - `get_materials_for_product(...)`
      - `add_material_to_iteration(...)`
      - `get_all_materials_for_selection(...)`
      - `update_material(...)`
      - `delete_material_link(...)`
      - `delete_material(...)`
      - `link_material_to_product(...)`
      - `unlink_material_from_product(...)`
      - `add_material(...)`
  - `ProductService` conserva lógica de validación y señales de producto, delegando el bloque repetitivo al mixin.
- **Tests añadidos**:
  - `tests/unit/test_product_service_delegation_mixin.py` (delegaciones completas).
  - `tests/unit/test_product_service_core_paths.py` (rutas de validación y señales de `add_product`, `update_product`, `delete_product`).
- **Validación**:
  - `python3 -m mypy core/services/product_service.py core/services/product_service_delegation_mixin.py tests/unit/test_product_service.py tests/unit/test_product_service_delegation_mixin.py tests/unit/test_product_service_core_paths.py` ✅
  - `python3 -m pytest -q tests/unit/test_product_service.py tests/unit/test_product_service_delegation_mixin.py tests/unit/test_product_service_core_paths.py` ✅ (17 passed)
  - `python3 scripts/coverage_focus.py --paths core/services/product_service.py core/services/product_service_delegation_mixin.py --tests tests/unit/test_product_service.py tests/unit/test_product_service_delegation_mixin.py tests/unit/test_product_service_core_paths.py` ✅ (cobertura 100% en archivos tocados)
- **Estado del criterio de tamaño**:
  - `python3 scripts/monolith_analyzer.py --min-loc 400 --out-dir Documentacion/Refactorizacion_Completa/Monolitos` → `ranked_monoliths = 0`.

#### 2026-03-19 — Iteración 27

- **Corte aplicado por densidad funcional**: `controllers/product/fabricacion_manager.py` (métodos de gestión de productos de fabricación agrupados en un mismo archivo).
  - **Nuevo**: `controllers/product/fabricacion_manager_products_mixin.py`
    - `show_fabricacion_products(...)`
    - `_on_fabrication_result_selected_by_id(...)`
    - `get_fabricacion_products_for_calculation(...)`
  - `FabricacionManager` mantiene API pública y delega ese bloque al mixin.
  - Compatibilidad de tests preservada resolviendo símbolos parcheables (`ProductsSelectionDialog`, `QDialog`) vía `controllers.product.fabricacion_manager`.
- **Tests añadidos/mejorados**:
  - `tests/controllers/product/test_fabricacion_manager.py`: cobertura de la rama temprana cuando la fabricación no existe en `show_fabricacion_products(...)`.
- **Validación**:
  - `python3 -m mypy controllers/product/fabricacion_manager.py controllers/product/fabricacion_manager_products_mixin.py` ✅
  - `python3 -m pytest -q tests/controllers/product/test_fabricacion_manager.py tests/unit/test_product_controller_v2_comprehensive.py tests/unit/test_product_controller_preprocesos.py` ✅ (115 passed)
  - `python3 scripts/coverage_focus.py --paths controllers/product/fabricacion_manager.py controllers/product/fabricacion_manager_products_mixin.py --tests tests/controllers/product/test_fabricacion_manager.py tests/unit/test_product_controller_v2_comprehensive.py tests/unit/test_product_controller_preprocesos.py` ✅ (cobertura 100% en archivos tocados)
- **Estado del criterio de tamaño**:
  - `python3 scripts/monolith_analyzer.py --min-loc 400 --out-dir Documentacion/Refactorizacion_Completa/Monolitos` → `ranked_monoliths = 0`.

#### 2026-03-19 — Iteración 23

- **Corte aplicado**: `database/repositories/iteration_repository.py` (>=250 LOC) con extracción conservadora de mapeos y bloque de imágenes.
  - **Nuevo**: `database/repositories/iteration_repository_helpers.py`
    - `material_to_dto(...)`
    - `iteration_to_dto(...)`
  - **Nuevo**: `database/repositories/iteration_repository_images_mixin.py`
    - `add_image(...)`
    - `get_images(...)`
    - `delete_image(...)`
  - `IterationRepository` mantiene API pública; delega mapeos/helpers y hereda mixin de imágenes.
- **Resultado**: `iteration_repository.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 214)
- **Validación**:
  - `python3 -m mypy database/repositories/iteration_repository.py database/repositories/iteration_repository_helpers.py database/repositories/iteration_repository_images_mixin.py` ✅
  - `python3 -m pytest -q tests/unit/test_iteration_repository.py tests/integration/test_iteration_integration.py tests/e2e/test_iteration_workflow.py` ✅ (20 passed)
  - `python3 scripts/coverage_focus.py --paths database/repositories/iteration_repository.py database/repositories/iteration_repository_helpers.py database/repositories/iteration_repository_images_mixin.py --tests tests/unit/test_iteration_repository.py tests/integration/test_iteration_integration.py tests/e2e/test_iteration_workflow.py` ✅ (cobertura 100% en archivos tocados)

#### 2026-03-19 — Iteración 20

- **Corte aplicado**: `core/services/reporting/pdf_report_strategy.py` (>=250 LOC) con extracción de secciones de diagnóstico/auditoría.
  - **Nuevo**: `core/services/reporting/pdf_report_sections.py`
    - `add_diagnostics_section(...)`
    - `add_sequential_group_diagnostics_section(...)`
    - `add_audit_log_table_section(...)`
  - `ReporteHistorialFabricacion` delega esas secciones manteniendo API y formato final.
- **Resultado**: `pdf_report_strategy.py` sale del ranking de monolitos (`min_loc=250`) ✅
- **Validación**:
  - `python3 -m mypy core/services/reporting/pdf_report_strategy.py core/services/reporting/pdf_report_sections.py` ✅
  - `python3 -m pytest -q tests/unit/test_report_controller_comprehensive.py tests/unit/test_reportes_widget.py` ✅ (36 passed)

#### 2026-03-19 — Iteración 21

- **Corte aplicado**: `ui/widgets/settings_widget.py` (>=250 LOC) con extracción de lógica de horario/festivos a mixin conservador.
  - **Nuevo**: `ui/widgets/settings_widget_schedule_mixin.py`
    - altas/edición/borrado de descansos
    - alta/baja/paint de festivos
    - guardado/carga de configuración de horario
  - `SettingsWidget` mantiene señales, wiring UI y contrato de métodos públicos.
  - Compatibilidad de tests preservada resolviendo `QDialog/QTimeEdit/QFormLayout/QDialogButtonBox/QTextCharFormat/QBrush/QColor` desde `ui.widgets.settings_widget` (targets de patch existentes).
- **Resultado**: `settings_widget.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 167)
- **Validación**:
  - `python3 -m mypy ui/widgets/settings_widget.py ui/widgets/settings_widget_schedule_mixin.py` ✅
  - `python3 -m pytest -q tests/unit/test_settings_widget.py` ✅ (26 passed)

#### 2026-03-19 — Iteración 18

- **Corte aplicado**: `core/dtos_models.py` (>=250 LOC) con partición por dominio manteniendo fachada estable.
  - **Nuevo**: `core/dtos_catalog.py` (DTOs de catálogo/producción).
  - **Nuevo**: `core/dtos_flow_camera.py` (DTOs de flujo de producción y cámara).
  - `core/dtos_models.py` pasa a ser agregador interno (re-export de ambos dominios + DTOs de máquina/trabajador).
  - `core/dtos.py` mantiene el contrato público de import sin cambios.
- **Resultado**: `dtos_models.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 135)
- **Validación**:
  - `python3 -m mypy core/dtos.py core/dtos_models.py core/dtos_catalog.py core/dtos_flow_camera.py` ✅
  - `python3 -m pytest -q tests/unit/test_app_model.py tests/unit/test_define_flow_dialog.py tests/unit/test_define_flow_presenter.py tests/unit/test_camera_config_dialog.py tests/unit/test_camera_config_presenter.py tests/unit/test_product_repository.py tests/db/test_product_repository.py` ✅ (131 passed)

#### 2026-03-19 — Iteración 19

- **Corte aplicado**: `ui/widgets/reports/charts_container.py` (>=250 LOC) con extracción conservadora de utilidades no críticas.
  - **Nuevo**: `ui/widgets/reports/stat_card.py` (widget `StatCard` aislado y reutilizable).
  - **Nuevo**: `ui/widgets/reports/charts_renderers.py` (helpers seguros para limpieza y tarjetas).
  - `charts_container.py` conserva la lógica de graficado principal in-place para respetar parches/mocks de tests existentes.
- **Resultado**: `charts_container.py` sale del ranking de monolitos (`min_loc=250`) ✅ (LOC en reporte: 246)
- **Validación**:
  - `python3 -m mypy ui/widgets/reports/charts_container.py ui/widgets/reports/charts_renderers.py ui/widgets/reports/stat_card.py` ✅
  - `python3 -m pytest -q tests/unit/test_charts_container.py tests/unit/test_charts_widget.py tests/unit/test_reports_widgets.py` ✅ (65 passed)

#### 2026-03-19 — Iteración 28

- **Corte aplicado**: `ui/widgets/product/iterations_widget.py` (alta densidad funcional) con extracción del bloque de galería de imágenes a mixin conservador.
  - **Nuevo**: `ui/widgets/product/iterations_widget_gallery_mixin.py`
    - `_add_image_to_gallery(...)`
    - `_on_gallery_item_double_clicked(...)`
    - `_on_add_image_clicked(...)`
    - `_on_delete_image_clicked(...)`
  - Compatibilidad de tests preservada: el mixin resuelve `QFileDialog/QPixmap/QIcon/QListWidgetItem` desde `ui.widgets.product.iterations_widget` para mantener intactos los targets de patch existentes.
- **Tests**:
  - Se añadió `test_load_iterations_logs_error_on_exception` en `tests/unit/test_product_dialogs_coverage.py` para cubrir la rama de excepción de `load_data` en el widget.
- **Resultado**: reducción de complejidad funcional del widget sin cambios de contrato público.
- **Validación**:
  - `python3 -m mypy ui/widgets/product/iterations_widget.py ui/widgets/product/iterations_widget_gallery_mixin.py tests/unit/test_product_dialogs_coverage.py` ✅
  - `python3 -m pytest -q tests/unit/test_product_dialogs_coverage.py` ✅ (108 passed)
  - `python3 scripts/coverage_focus.py --paths ui/widgets/product/iterations_widget.py ui/widgets/product/iterations_widget_gallery_mixin.py --tests tests/unit/test_product_dialogs_coverage.py` ✅ (100% en ambos archivos)

#### 2026-03-19 — Iteración 29

- **Corte aplicado**: `controllers/product_controller_v2.py` (alta densidad funcional, 41 métodos) con extracción de delegaciones a mixin de compatibilidad.
  - **Nuevo**: `controllers/product/product_controller_v2_delegation_mixin.py`
    - Delegaciones de `ProductManager`, `FabricacionManager`, `PreprocesoManager` y `MaterialManager`.
  - `ProductController` mantiene composición, inicialización y API pública; ahora hereda del mixin para reducir tamaño y carga cognitiva en el archivo principal.
- **Tests**:
  - Se añadió `test_on_data_changed_bridge` en `tests/unit/test_product_controller_v2_comprehensive.py` para cubrir explícitamente la rama puente de `on_data_changed`.
- **Resultado**: separación clara entre wiring/orquestación y capa de delegación, sin cambios de comportamiento.
- **Validación**:
  - `python3 -m mypy controllers/product_controller_v2.py controllers/product/product_controller_v2_delegation_mixin.py tests/unit/test_product_controller_v2_comprehensive.py` ✅
  - `python3 -m pytest -q tests/unit/test_product_controller_v2_comprehensive.py tests/unit/test_product_controller_preprocesos.py` ✅ (112 passed)
  - `python3 scripts/coverage_focus.py --paths controllers/product_controller_v2.py controllers/product/product_controller_v2_delegation_mixin.py --tests tests/unit/test_product_controller_v2_comprehensive.py tests/unit/test_product_controller_preprocesos.py` ✅ (100% en ambos archivos)

#### 2026-03-19 — Iteración 30

- **Corte aplicado**: `controllers/ui_signals_controller.py` (alta densidad funcional, muchos métodos `_connect_*`) con extracción a mixin de conexiones UI.
  - **Nuevo**: `controllers/ui_signals_controller_mixin.py`
    - `_connect_navigation_signals`
    - `_connect_preprocesos_signals`
    - `_connect_products_signals`
    - `_connect_fabrications_signals`
    - `_connect_add_product_signals`
    - `_connect_calculate_signals`
    - `_connect_historial_signals`
    - `_connect_definir_lote_signals`
    - `_connect_lotes_management_signals`
    - `_connect_reportes_signals`
    - `_connect_workers_signals`
    - `_connect_machines_signals`
  - `UISignalsController` conserva `__init__` y `connect_all_signals` como fachada/orquestador.
- **Tests**:
  - Se ampliaron tests en `tests/unit/test_ui_signals_controller_comprehensive.py` para cubrir ramas del mixin:
    - `test_settings_page_with_test_camera_and_warning_fallback`
    - `test_settings_page_uses_tracking_repo_import_tasks_when_app_lacks_method`
    - `test_preprocesos_widget_connects_add_edit_delete_buttons`
- **Resultado**: separación explícita entre orquestación y detalle de wiring de señales, sin cambios de comportamiento.
- **Validación**:
  - `python3 -m mypy controllers/ui_signals_controller.py controllers/ui_signals_controller_mixin.py tests/unit/test_ui_signals_controller_comprehensive.py` ✅
  - `python3 -m pytest -q tests/unit/test_ui_signals_controller_comprehensive.py` ✅ (32 passed)
  - `python3 scripts/coverage_focus.py --paths controllers/ui_signals_controller.py controllers/ui_signals_controller_mixin.py --tests tests/unit/test_ui_signals_controller_comprehensive.py` ✅ (100% en ambos archivos)

#### 2026-03-19 — Iteración 31

- **Corte aplicado**: `controllers/simulation/controller.py` (alta densidad funcional por delegación a managers) con extracción de métodos de passthrough.
  - **Nuevo**: `controllers/simulation/controller_delegation_mixin.py`
    - Delegaciones a `SimulationExecutionManager`:
      - `_on_run_manual_plan_clicked`
      - `_on_execute_optimizer_simulation_clicked`
      - `_start_simulation_thread`
      - `_on_simulation_finished`
      - `_on_optimization_finished`
      - `_handle_run_manual_from_visual_editor`
      - `_handle_run_optimizer_from_visual_editor`
    - Delegaciones a `SimulationEditorManager`:
      - `_on_define_flow_clicked`
      - `_open_editor_with_loaded_flow`
  - `SimulationController` mantiene `__init__`, estado y métodos propios no delegados (`_on_clear_simulation`, `handle_save_flow_only`, `_update_simulation_progress`, `clear_simulation_state`).
- **Tests**:
  - Se añadió `test_handle_save_flow_only_with_dto_steps` en `tests/unit/test_simulation_controller_comprehensive.py` para cubrir la rama de `handle_save_flow_only` cuando el `step` no es `dict` (ruta DTO).
- **Resultado**: archivo principal de simulación más enfocado en orquestación/estado, con delegación explícita y sin cambios de comportamiento.
- **Validación**:
  - `python3 -m mypy controllers/simulation/controller.py controllers/simulation/controller_delegation_mixin.py tests/unit/test_simulation_controller_comprehensive.py` ✅
  - `python3 -m pytest -q tests/unit/test_simulation_controller_comprehensive.py` ✅ (36 passed)
  - `python3 scripts/coverage_focus.py --paths controllers/simulation/controller.py controllers/simulation/controller_delegation_mixin.py --tests tests/unit/test_simulation_controller_comprehensive.py` ✅ (100% en ambos archivos)

#### 2026-03-19 — Iteración 32

- **Corte aplicado**: `controllers/pila/controller.py` (alta densidad funcional) con extracción de delegaciones puras a mixin.
  - **Nuevo**: `controllers/pila/controller_delegation_mixin.py`
    - Delegaciones de `LoteManager`:
      - `_on_calc_lote_search_changed`
      - `_on_lote_def_product_search_changed`
      - `_on_lote_def_fab_search_changed`
      - `_on_add_product_to_lote_template`
      - `_on_add_fab_to_lote_template`
      - `_on_remove_item_from_lote_template`
      - `update_lotes_view`
      - `_on_save_lote_template_clicked`
      - `_on_update_lote_template_clicked`
      - `_on_delete_lote_template_clicked`
    - Delegaciones de `PilaManager`:
      - `_on_load_pila_clicked`
      - `_on_save_pila_clicked`
      - `_on_ver_bitacora_pila_clicked`
  - `PilaController` mantiene métodos de lógica UI/puente y consulta (`_on_add_lote_to_pila_clicked`, `_on_remove_lote_from_pila_clicked`, `get_preprocesos_for_fabricacion`, `_connect_lotes_management_signals`, `_on_lote_management_result_selected`).
- **Resultado**: el controlador queda más enfocado en lógica propia de fachada/UI, con delegación explícita y estable.
- **Validación**:
  - `python3 -m mypy controllers/pila/controller.py controllers/pila/controller_delegation_mixin.py tests/unit/test_pila_controller_comprehensive.py` ✅
  - `python3 -m pytest -q tests/unit/test_pila_controller_comprehensive.py` ✅ (30 passed)
  - `python3 scripts/coverage_focus.py --paths controllers/pila/controller.py controllers/pila/controller_delegation_mixin.py --tests tests/unit/test_pila_controller_comprehensive.py` ✅ (100% en ambos archivos)

#### 2026-03-19 — Iteración 33

- **Corte aplicado**: `controllers/app_controller.py` (último candidato de alta densidad funcional en controllers) con extracción ultra conservadora de métodos de compatibilidad/delegación.
  - **Nuevo**: `controllers/app_controller_compat_mixin.py`
    - `handle_save_flow_only(...)`
    - `search_fabricaciones(...)`
    - `show_fabricacion_preprocesos(...)`
    - `logout_user()`
    - `handle_login(...)`
    - `_on_export_gantt_to_pdf_clicked()`
    - `load_schedule_settings()`
    - `on_nav_button_clicked(...)`
  - `AppController` mantiene la orquestación central (`__init__`, `initialize_infra`, `connect_all_signals`, `initialize`, `cleanup`, `current_user`, `on_data_changed`).
- **Análisis previo de seguridad**:
  - Se midió cobertura base de `app_controller` antes del corte para identificar ramas no cubiertas y definir un plan de tests controlado.
- **Tests añadidos/ajustados**:
  - **Nuevo**: `tests/unit/test_app_controller_orchestration.py` con cobertura explícita de:
    - éxito/error en `initialize_infra` y `connect_all_signals`
    - `initialize` secuencial
    - `cleanup`
    - property `current_user` getter/setter
    - ramas de delegación/compatibilidad extraídas al mixin
    - ramas de `on_data_changed`
- **Resultado**: separación de responsabilidades en el orquestador principal sin alterar comportamiento público ni contratos existentes.
- **Validación**:
  - `python3 -m mypy controllers/app_controller.py controllers/app_controller_compat_mixin.py tests/unit/test_app_controller_orchestration.py` ✅
  - `python3 -m pytest -q tests/unit/test_app_controller_orchestration.py tests/unit/test_controller_interface.py tests/unit/test_startup_controller.py tests/unit/test_app_coverage.py tests/integration/test_app_startup_integration.py` ✅ (24 passed)
  - `python3 scripts/coverage_focus.py --paths controllers/app_controller.py controllers/app_controller_compat_mixin.py --tests tests/unit/test_app_controller_orchestration.py tests/unit/test_controller_interface.py tests/unit/test_startup_controller.py tests/unit/test_app_coverage.py tests/integration/test_app_startup_integration.py` ✅ (100% en ambos archivos)

