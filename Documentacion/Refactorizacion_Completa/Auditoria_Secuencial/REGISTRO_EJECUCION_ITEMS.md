# Registro de ejecución por ítems

Skill de referencia: `.agents/skills/ejecucion_secuencial_calidad/SKILL.md` (si existe en el árbol principal).

## ITEM 001 — Frontera UI/DTO en `products_widget`

- **Estado:** Completado
- **Prioridad:** P1
- **Alcance:** `ui/widgets/products_widget.py`
- **Cambio:** Serialización de subfabricaciones vía `SubfabricacionDTO` y `getattr` de respaldo (sin `dict.get` en la lista); `print` de depuración sustituido por `logging.debug`; docstring de módulo.
- **Baseline:** pytest focal OK (171 passed); mypy focal OK (2 archivos).
- **Gates post-refactor:** pytest focal OK; mypy focal OK; mypy global OK (657 archivos); pytest global OK (2638 passed).
- **Docs:** `python3 scripts/generate_daniel_doc.py` OK; `python3 scripts/check_documentation_omissions.py` → omitidos=0.
- **UI/DTO:** Tras `ui_dto_boundary_analyzer.py`, ya no hay hallazgos en `products_widget`.
- **Fecha cierre:** 2026-04-02

## ITEM 002 — Frontera UI/DTO y fallback de descansos en `settings_widget`

- **Estado:** Completado
- **Prioridad:** P1 (+ P3: eliminación de `bare except` en el mismo bloque)
- **Alcance:** `ui/widgets/settings_widget.py`, `controllers/schedule_helpers.py`, `tests/unit/test_settings_widget.py`, `tests/unit/test_schedule_helpers.py`
- **Cambio:** Deserialización de descansos vía `break_display_lines_from_json` (reutiliza `load_breaks_list`); el widget solo añade líneas ya formateadas. Eliminado `bare except` y `import json` redundante en el fallback.
- **Gates:** mypy global OK (658 archivos); pytest global OK (2644 passed); `ui_dto_boundary_analyzer.py` → **0 hallazgos**; docs → omitidos=0.
- **Fecha cierre:** 2026-04-02

## ITEM 003 (fase A) — Retiro de `create_dialog_compat`

- **Estado:** Completado
- **Prioridad:** P0
- **Alcance:** `ui/dialogs/fabrication/create_dialog.py`; eliminado `ui/dialogs/fabrication/create_dialog_compat.py`; `Documentacion/.../puentes_compatibilidad_estado.md`.
- **Cambio:** API legacy (propiedades `search_entry`, listas, botones, métodos públicos) inlinada en `CreateFabricacionDialog`; sin clase puente intermedia.
- **Ajuste colateral:** import de `break_display_lines_from_json` movido **dentro** de `load_schedule_settings` en `settings_widget.py` para evitar ciclo `ui.widgets` → `controllers` → `ui.widgets` al importar el paquete.
- **Gates:** mypy global OK (657 archivos); pytest global OK (2644 passed); docs → omitidos=0.
- **Fecha cierre:** 2026-04-02

## ITEM 003 (fase B) — Consolidación de puentes de flujo en `flow_canvas_io`

- **Estado:** Completado
- **Prioridad:** P0
- **Alcance:** `core/flow_canvas_io.py`; eliminado `core/flow_dialog_bridges.py`; imports actualizados en `enhanced_flow_canvas_state_io.py`, `flow_graph_manager_io.py`, `enhanced_flow_presenter_io.py`, `ui/dialogs/production_flow/flow_action_handler.py`, `cycle_end_config_dialog.py`, `flow_builder.py`, `ui/widgets/production_flow/flow_graph_manager.py`.
- **Cambio:** `canvas_task_body`, `canvas_task_display_name`, `flow_task_config_is_cycle_end_flag` y `flow_task_config_is_cycle_start_flag` viven junto a `legacy_canvas_task_*` en `flow_canvas_io`; una sola capa de lectura sobre mapas del canvas.
- **Gates:** mypy global OK (656 archivos); pytest global OK (2644 passed); docs regeneradas y `check_documentation_omissions.py` → omitidos=0.
- **Fecha cierre:** 2026-04-02

## ITEM 004 (lote A) — `disallow_untyped_defs` en `tracking_log_repository`

- **Estado:** Completado (lote A; ITEM 004 puede continuar con lote B)
- **Prioridad:** P2
- **Alcance:** `database/repositories/tracking_log_repository.py`, `mypy.ini` (entrada explícita del módulo en el bloque de repositorios endurecidos).
- **Cambio:** `session_factory` tipado como `Callable[[], Session]`; proxies de mapeo y delegación con firmas alineadas a `TrackingCoreManager` / `TrackingStepsManager` / `TrackingQueriesManager` (sin `*args/**kwargs` opacos en la API pública del repositorio).
- **Gates:** mypy global OK (656 archivos); pytest global OK (2644 passed); docs regeneradas; `check_documentation_omissions.py` → omitidos=0.
- **Fecha cierre lote A:** 2026-04-02

## ITEM 004 (lote B — paso 1) — `procesos_mecanicos_dialog`

- **Estado:** Completado (primer archivo del lote B)
- **Prioridad:** P2
- **Alcance:** `ui/dialogs/product/procesos_mecanicos_dialog.py`, `mypy.ini` (`[mypy-ui.dialogs.product.procesos_mecanicos_dialog]`).
- **Cambio:** Anotaciones en `ProcesosMecanicosDialog` y `AddProcesoMecanicoDialog`; criterio de elección: peor cobertura entre diálogos product/prep en `check_typing_coverage.py` (0/10 funciones tipadas).
- **Gates:** mypy global OK; pytest focal `TestProcesosMecanicosDialog` OK; suite global OK.
- **Fecha:** 2026-04-02

## ITEM 004 (lote B — paso 2) — `subfabricaciones_dialog` + `prep_groups_dialog`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `ui/dialogs/product/subfabricaciones_dialog.py`, `ui/dialogs/prep/prep_groups_dialog.py`, `mypy.ini` (mismo bloque endurecido que paso 1).
- **Cambio:** Anotaciones en métodos y parámetros; `cast` donde `QComboBox`/`QListWidget` devuelven `Any`; `parent` del grupo como `Any` por compatibilidad con `IView` en `MachineController`.
- **Gates:** mypy global OK; pytest focal OK; suite global OK.
- **Fecha:** 2026-04-02

## ITEM 004 (lote B — paso 3) — `prep_steps_dialog`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `ui/dialogs/prep/prep_steps_dialog.py`, `mypy.ini` (módulo añadido al bloque ITEM 004).
- **Cambio:** Firmas explícitas en `PrepStepsDialog`; `current_step_id: int | None`; `cast` en `UserRole`; `parent: Any` como en `PrepGroupsDialog`.
- **Gates:** mypy global OK; pytest focal `TestPrepStepsDialog` OK; suite global OK.
- **Fecha:** 2026-04-02

## ITEM 004 (lote B — paso 4) — `preproceso_dialog`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `ui/dialogs/prep/preproceso_dialog.py`, `mypy.ini`.
- **Cambio:** `-> None` en métodos UI; `all_materials` como `List[Any]` desde `Sequence`; `assigned_material_ids: Set[int]`; `cast` en datos de ítems; `get_data() -> Dict[str, Any] | None`.
- **Gates:** mypy global OK; pytest focal `TestPreprocesoDialog` OK; suite global OK.
- **Fecha:** 2026-04-02

## ITEM 004 (lote C — paso 1) — `fabrications_widget`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `ui/widgets/fabrications_widget.py`, `mypy.ini` (`[mypy-ui.widgets.fabrications_widget]`).
- **Cambio:** Firmas explícitas y `Dict[str, Any]` / `Optional[int]` en estado del formulario; `Iterable[FabricacionDTO]` en actualización de lista; `clear_all` formateado en varias líneas.
- **Gates:** mypy global OK; pytest `test_fabrications_widget` OK; suite global OK.
- **Fecha:** 2026-04-02

## ITEM 004 (lote C — paso 2) — `reportes_widget`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `ui/widgets/reportes_widget.py`, `mypy.ini` (bloque compartido con `fabrications_widget`).
- **Cambio:** `Any` en controlador/modelo resuelto; `-> None` en slots y helpers; `_resolve_app_model(controller: Any) -> Any`.
- **Gates:** mypy global OK; pytest `test_reportes_widget` OK; suite global OK.
- **Fecha:** 2026-04-02

## ITEM 004 (lote C — paso 3) — `worker_service`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `core/services/worker_service.py`, `mypy.ini` (`[mypy-core.services.worker_service]`).
- **Baseline:** pytest `tests/unit/test_worker_service.py` OK (4 passed); mypy focal OK.
- **Cambio:** Anotaciones `-> Any` en propiedades (`worker_repo`, `tracking_repo`, `preproceso_repo`, `product_repo`, `tracking_assignment_service`, `pila_repo`) para cumplir `disallow_untyped_defs` sin acoplar a tipos concretos de repositorio.
- **Gates post-refactor:** pytest focal OK; mypy focal OK; mypy global OK (656 archivos); pytest global OK (2644 passed).
- **Docs:** `scripts/generate_daniel_doc.py` OK; `scripts/check_documentation_omissions.py` → omitidos=0.
- **Fecha cierre:** 2026-04-02

## ITEM 004 (lote C — paso 4) — `pdf_report_strategy`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `core/services/reporting/pdf_report_strategy.py`, `mypy.ini` (`[mypy-core.services.reporting.pdf_report_strategy]`).
- **Scripts ejecutados:** `check_typing_coverage.py` (criterio de cola), `mypy`, `pytest`.
- **Baseline:** pytest `tests/unit/test_report_strategy_comprehensive.py` OK (7 passed); mypy focal OK.
- **Cambio:** Firmas explícitas en `generar_reporte`, `_add_executive_summary`, `_add_gantt_chart_to_pdf`, `_add_resource_analysis_to_pdf`, helpers de diagnóstico/auditoría; `DefaultDict[str, Set[Any]]` para paralelos; clave de departamento vía `str(... or "")` para satisfacer `dict.get` en mypy. Sin cambio de comportamiento.
- **Gates post-refactor:** pytest focal OK; mypy focal OK; mypy global OK (656 archivos); pytest global OK (2644 passed).
- **Docs:** `generate_daniel_doc.py` OK; `check_documentation_omissions.py` → omitidos=0.
- **Sync iCloud:** OK — `mypy.ini`, `core/services/reporting/pdf_report_strategy.py`, `REGISTRO_EJECUCION_ITEMS.md`, `Documentacion/Documentacion Daniel.md`, `Documentacion/Documentacion Daniel.pdf`.
- **Fecha cierre:** 2026-04-02

## ITEM 004 (lote C — paso 5) — `data_importer`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `core/services/data_importer.py`, `mypy.ini` (`[mypy-core.services.data_importer]`).
- **Scripts ejecutados:** `check_typing_coverage.py` (criterio previo), `mypy`, `pytest`.
- **Baseline:** mypy focal OK; pytest focal `test_product_controller_v2_comprehensive.py -k MaterialImporter` OK.
- **Cambio:** `from __future__ import annotations`; tipos en `Material`, `IMaterialImporter.import_materials` → `Optional[List[Material]]`, `ExcelMaterialImporter`, `MaterialImporterFactory.create_importer` → `IMaterialImporter`; cuerpo abstracto con `raise NotImplementedError`; bucle Excel con `codigo_raw` vía `str(...).strip()` (equivalente a `.strip()` sobre celdas rellenadas); extensión `.xls`/`.xlsx` unificada con `in (...)`; eliminado `import os` no usado.
- **Gates post-refactor:** mypy global OK (656 archivos); pytest global OK (2644 passed).
- **Docs:** `generate_daniel_doc.py` OK; `check_documentation_omissions.py` → omitidos=0.
- **Sync iCloud:** OK — `mypy.ini`, `core/services/data_importer.py`, `REGISTRO_EJECUCION_ITEMS.md`, `Documentacion/Documentacion Daniel.md`, `Documentacion/Documentacion Daniel.pdf`.
- **Fecha cierre:** 2026-04-02

## ITEM 004 (lote C — paso 6) — `maintenance_service`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `core/services/maintenance_service.py`, `mypy.ini` (`[mypy-core.services.maintenance_service]`).
- **Baseline:** pytest `tests/unit/test_maintenance_service.py` OK (2 passed); mypy focal OK.
- **Cambio:** `MaintenanceWorker.__init__(service: MaintenanceService) -> None`, `run() -> None`; `run_background_maintenance` y `perform_maintenance` con `-> None`. Sin cambio de comportamiento.
- **Gates post-refactor:** mypy global OK (656 archivos); pytest global OK (2644 passed); tests relacionados `test_scheduler_logic`, `test_startup_controller` OK.
- **Docs:** `generate_daniel_doc.py` OK; `check_documentation_omissions.py` → omitidos=0.
- **Sync iCloud:** OK — `mypy.ini`, `core/services/maintenance_service.py`, `REGISTRO_EJECUCION_ITEMS.md`, `Documentacion/Documentacion Daniel.md`, `Documentacion/Documentacion Daniel.pdf`.
- **Fecha cierre:** 2026-04-02

## ITEM 004 (lote C — paso 7) — `database_manager`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `database/database_manager.py`, `mypy.ini` (`[mypy-database.database_manager]`).
- **Baseline:** pytest `tests/unit/test_database_manager_full.py` OK (16 passed); mypy focal OK.
- **Cambio:** `from __future__ import annotations`; `__init__` con `engine: Optional[Engine | Connection]`, `-> None`; `_create_tables_if_not_exist`, `_init_repositories`, `close` con `-> None`; context manager `__enter__ -> DatabaseManager`, `__exit__` con tipos de excepción y `TracebackType`; delegados `*args: Any, **kwargs: Any` en `add_worker`, `get_all_workers`, `add_machine`, `add_machine_maintenance`; `close()` distingue `Engine.dispose()` vs `Connection.close()`; indentación en `compare_with_db` / `apply_sync_changes`.
- **Gates post-refactor:** mypy global OK (656 archivos); pytest global OK (2644 passed).
- **Docs:** `generate_daniel_doc.py` OK; `check_documentation_omissions.py` → omitidos=0.
- **Sync iCloud:** OK — `mypy.ini`, `database/database_manager.py`, `REGISTRO_EJECUCION_ITEMS.md`, `Documentacion/Documentacion Daniel.md`, `Documentacion/Documentacion Daniel.pdf`.
- **Fecha cierre:** 2026-04-02

## ITEM 004 (lote C — paso 8) — `core/qr_scanner/scanner`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `core/qr_scanner/scanner.py`, `mypy.ini` (`[mypy-core.qr_scanner.scanner]`).
- **Baseline:** pytest `tests/unit/test_qr_scanner.py` OK (16 passed); mypy focal OK.
- **Cambio:** `QrScanner.__init__` → `-> None`; `QrScannerCallback` con `on_consulta` / `on_trabajo` como `Optional[Callable[[Any, Any], None]]` y `Optional[Callable[[Any, Any], bool]]`; `handle_consulta` / `handle_trabajo` anotados; imports `Callable` y orden alfabético en `typing`.
- **Gates post-refactor:** mypy global OK (656 archivos); pytest global OK (2644 passed).
- **Docs:** `generate_daniel_doc.py` OK; `check_documentation_omissions.py` → omitidos=0.
- **Sync iCloud:** OK — `mypy.ini`, `core/qr_scanner/scanner.py`, `REGISTRO_EJECUCION_ITEMS.md`, `Documentacion/Documentacion Daniel.md`, `Documentacion/Documentacion Daniel.pdf`.
- **Fecha cierre:** 2026-04-02

## ITEM 004 (lote C — paso 9) — `product_service`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `core/services/product_service.py`, `core/app_model.py` (alineación de retorno), `mypy.ini` (`[mypy-core.services.product_service]`).
- **Baseline:** pytest `test_product_service*.py` + `test_app_model.py` OK; mypy focal OK.
- **Cambio:** `__init__` → `-> None`; propiedades `product_repo` / `iteration_repo` / `material_repo` tipadas (`ProductRepository`, `IterationRepository`, `MaterialRepository`); `add_material_to_iteration` → `int | None` (coherente con `add_material`); `AppModel.add_material_to_iteration` mismo retorno; imports de repositorios; eliminados `asdict`, `cast`, `PreparationStepDTO` no usados.
- **Gates post-refactor:** mypy global OK (656 archivos); pytest global OK (2644 passed).
- **Docs:** `generate_daniel_doc.py` OK; `check_documentation_omissions.py` → omitidos=0.
- **Sync iCloud:** OK — `mypy.ini`, `core/services/product_service.py`, `core/app_model.py`, `REGISTRO_EJECUCION_ITEMS.md`, `Documentacion/Documentacion Daniel.md`, `Documentacion/Documentacion Daniel.pdf`.
- **Fecha cierre:** 2026-04-02

## ITEM 004 (lote D — paso 1) — `database.repositories.reports`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `database/repositories/reports/repository.py`, `reports_search_manager.py`, `reports_incidences_manager.py`, `reports_orders_manager.py`, `reports_products_manager.py`, `reports_stats_manager.py`, `mypy.ini` (bloque endurecido); corrección de imports inexistentes `database.repositories.reports_repository` → `database.repositories.reports` en `core/services/report_service.py` y `scripts/profile_queries.py`.
- **Cambio:** `ReportsRepository` con `session_factory: Callable[[], Session]`, delegación con firmas explícitas (sin `*args/**kwargs`); `-> None` en `_sync_managers`; cierres internos de managers con tipo de retorno; `tiene_incidencias` vía `len(t.incidencias or [])`; `producto_descripcion` con `or ""` donde aplica.
- **Scripts ejecutados:** `mypy` (focal + global), `pytest` (`test_reports_repository`, `test_reports_infrastructure`), `run_tests.py`, `generate_daniel_doc.py`, `check_documentation_omissions.py`.
- **Gates post-refactor:** mypy global OK (673 archivos); pytest global OK (`run_tests.py` — todos los tests pasados); docs → omitidos=0.
- **Sync iCloud:** N/A (workspace = iCloud)
- **Fecha cierre:** 2026-04-03

## ITEM 004 (lote D — paso 2) — `database.repositories.tracking`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `database/repositories/tracking/core_manager.py`, `steps_manager.py`, `queries_manager.py`, `mappers.py`, `mypy.ini` (bloque `[mypy-database.repositories.tracking.*]`).
- **Cambio:** `disallow_untyped_defs = True` para los cuatro módulos; en `TrackingQueriesManager.get_data_for_export`, anotación de `_to_dict(obj: object) -> Dict[str, Any]` y `data` como `Dict[str, Any]` para cumplir mypy estricto. Sin cambio de comportamiento.
- **Gates:** mypy global OK (673 archivos); pytest focal tracking (p. ej. `test_tracking_repository_*`, `test_tracking_assignment_service`, `test_tracking_exceptions`) OK; `generate_daniel_doc.py` OK; `check_documentation_omissions.py` → omitidos=0.
- **Sync iCloud:** N/A (workspace = iCloud)
- **Fecha cierre:** 2026-04-03

## ITEM 004 (lote D — paso 3) — `tracking_repository` + protocols/helpers

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `database/repositories/tracking_repository.py` (`session_factory: Callable[[], Session]`; `obtener_estadisticas_*` → `Dict[str, Any]`); `protocols.py` (`List[Dict[str, Any]]` en PilaRepositoryProtocol); `iteration_repository_helpers.py`, `product_repository_helpers.py` (import redundante eliminado en `to_material_dto`); `mypy.ini` (bloque explícito paso 3 para `protocols` + helpers).
- **Cambio:** Alineación con `TrackingLogRepository` / `BaseRepository`; `from __future__ import annotations` en la fachada tracking. Sin cambio de comportamiento en runtime.
- **Gates:** mypy global OK (673 archivos); pytest focal (`test_tracking_repository_full`, `test_iteration_repository`, `test_product_service_delegation`, `test_protocols_imports`) OK; `generate_daniel_doc.py` OK; `check_documentation_omissions.py` → omitidos=0.
- **Sync iCloud:** N/A (workspace = iCloud)
- **Fecha cierre:** 2026-04-03

## ITEM 004 (lote D — paso 4) — `tracking_stats_repository`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `database/repositories/tracking_stats_repository.py`, `mypy.ini` (bloque dedicado; retirado del trío satélite).
- **Cambio:** Retornos `obtener_estadisticas_*` → `Dict[str, Any]` (alineado con `TrackingRepository`); import `Any`; bloque mypy explícito para el módulo.
- **Gates:** mypy focal + pytest focal tracking stats/excepciones.
- **Fecha cierre:** 2026-04-04

## ITEM 004 (lote D — paso 5) — `repositories.__init__` + satélites mypy

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `database/repositories/__init__.py` (`__all__` alineado con imports públicos: `LoteRepository`, `LabelCounterRepository`), `mypy.ini` (bloque dedicado `database.repositories.__init__`; `label_counter_repository` e `incidencia_repository` en bloques separados), `incidencia_repository.py` (import `cast` no usado retirado).
- **Gates:** `mypy database/repositories` OK; pytest focal label_counter + tracking OK.
- **Fecha cierre:** 2026-04-04

## ITEM 004 (lote D — paso 6) — servicios dominio + report_sheets + raíz `database`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `mypy.ini` (`database`, `database.config`, bloque servicios fabricación/pila/máquina/preparación/tracking_assignment/system_integration/flow_*; `core.services.report_sheets.*`; `reporting.excel_report_strategy` + `pdf_report_sections`). Ajustes de anotación en esos módulos; `get_prep_step_details_by_ids` implementado en `MachinePreparationManager` / `MachineRepository` (faltaba en capa datos; `PreparationService` ya lo delegaba). Tests en `test_machine_repository`, `test_preparation_service`.
- **Gates:** `mypy .` OK (676 archivos); pytest focal machine + preparation + report_sheets + report_strategy + tracking_assignment + fabricación OK.
- **Fecha cierre:** 2026-04-04

## ITEM 004 (lote D — paso 7) — raíz `features`/`ui`, efectos, `core.protocols`, `core.facades`, `core`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `mypy.ini` — `disallow_untyped_defs` explícito para módulos `features` (paquete), `ui` (paquete), `ui.dialogs.effects.*`, `core.protocols.*`, `core.facades` (solo `__init__` del subpaquete), `core` (solo `__init__` raíz). Sin cambios de runtime; el código ya cumplía al activar los bloques.
- **Gates:** `mypy .` OK (676 archivos); pytest focal `test_visual_effects` + setup efectos en `test_dialogs_setup` OK.
- **Fecha cierre:** 2026-04-04

## ITEM 004 (lote D — paso 8) — `core.health`, `core.interfaces`, startup UI, `camera_manager`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `mypy.ini` — `core.health.*`, `core.interfaces.*`, `ui.startup_screen` + constantes/report/ui auxiliares, `core.camera_manager.*`. Ajustes de tipos en `camera_manager/__init__.py` (`quick_detect_cameras` → `List[CameraInfo]`, índices y `validate_camera_index` → `bool`) y `detector._get_cv2` → `Any`.
- **Gates:** `mypy .` OK (676 archivos); pytest focal cámara + startup + health OK.
- **Fecha cierre:** 2026-04-04

## ITEM 004 (lote D — paso 9) — label/import/validation, widgets.base, worker, ventana principal, utilidades núcleo, simulación

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `mypy.ini` — `core.label_manager.*`, `core.import_manager.*`, `core.validation.validator_service`, `ui.widgets.base`, `ui.worker.*`, `ui.main_window`, `core.constants`, `core.qt_log_handler`, `core.qr_generator`, `core.simulation.*`, `core.flow_canvas_io`. Ajustes en `simulation_events/worker.py`, `production.py` (`motor_eventos: Any`, helpers internos anotados, retornos `List[EventoDeSimulacion]`) y `timeline_task.__repr__ -> str`.
- **Gates:** `mypy .` OK (676 archivos); pytest focal simulación + main_window + worker_main_window + bom_import + label_manager OK.
- **Fecha cierre:** 2026-04-04

## ITEM 004 (lote D — paso 10) — `core.*_io` restantes + ampliación `ui.dialogs` / widgets flujo e informes

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `mypy.ini` — nueve módulos `core` `*_io` (además de `flow_canvas_io` ya listado): `define_flow_presenter_io`, `define_flow_form_io`, `inspector_task_payload_io`, `enhanced_flow_canvas_state_io`, `enhanced_flow_presenter_io`, `reassignment_rule_dialog_io`, `definir_cantidades_dialog_io`, `holidays_config_io`, `flow_graph_manager_io`; `ui.dialogs.fabrication.*`, `production_flow.*`, `product.*`, `prep.*`; diálogos sueltos (`tracking_dialogs`, `utility_dialogs`, `connection_dialog`, `backup_restore_dialog`, `card_widget`, `canvas_widgets`, `canvas_widget`). (Los bloques sueltos `ui.widgets.*` parciales se unificaron en paso 11.) `BOMImportPreviewDialog.__init__`: `parent: Optional[QWidget]`.
- **Gates:** `mypy .` OK (676 archivos); pytest focal BOM preview + define_flow + canvas + fabrication_dialogs OK.
- **Fecha cierre:** 2026-04-04

## ITEM 004 (lote D — paso 11) — `ui.widgets.*` completo + `core.qr_scanner.*`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `mypy.ini` — `[mypy-ui.widgets.*]` sustituye bloques redundantes (`fabrications_widget`/`reportes_widget`, `base`, `reports.*`, `production_flow.*`); `[mypy-core.qr_scanner.*]` sustituye el bloque solo `scanner` (lote C paso 8). Ajustes: `camera_selector_panel` / `camera_info_panel` `__init__(parent: Optional[QWidget]) -> None`; `QRDetector.__init__ -> None`; `products_widget.toggle_subs -> None`.
- **Gates:** `mypy .` OK (676 archivos); pytest focal `test_products_widget`, `test_qr_scanner`, `test_worker_main_window` OK.
- **Fecha cierre:** 2026-04-04

## ITEM 005 (B5 — iteración 1) — `AppController.on_data_changed` y `ProductService` vía DI

- **Estado:** Completado
- **Prioridad:** P2 (Bloque B — `plan_produccion_coordinador`)
- **Alcance:** `controllers/app_controller.py`
- **Cambio:** Tras `product_controller`, si el contenedor tiene `ProductService` registrado, se usa `container.resolve(ProductService).search_products("")` en lugar de `model.product_service` (misma instancia que en startup; sin consumidores nuevos que eliminar de `AppModel`).
- **Gates:** `pytest` focal `test_app_controller_orchestration`; `mypy` sobre `controllers/app_controller.py`.
- **Fecha cierre:** 2026-04-04

## ITEM 006 (B5 — cierre) — `ReportService` en reportes UI + `AppController` config vía `db`

- **Estado:** Completado (**tarea B5 del coordinador FINALIZADA**; sin continuación bajo el nombre B5)
- **Prioridad:** P2
- **Alcance:** `ui/widgets/reportes_widget.py`, `ui/widgets/reports/smart_search.py`, `controllers/app_controller.py`, tests `test_smart_search`, `test_reportes_widget`.
- **Cambio:** `ReportesWidget._resolve_report_service` + `_report_api()`; `SmartSearchWidget` acepta `report_service=` y `set_report_service`; búsqueda y detalle de orden usan el mismo `ReportService` que el DI cuando `AppController.container` lo tiene registrado. Fallback a `AppModel` sin DI. `config_get_setting` / `config_set_setting` usan `self.db` en la rama sin `ScheduleController`.
- **Cierre Bloque B:** `plan_produccion_coordinador` marca B5 **Completada (definitiva)**. `DefineProductionFlowDialog` ya usaba servicios DI en el presenter (sin cambio en este ítem).
- **Qué queda fuera de B5 y por qué (canónico):** `.agents/skills/reduccion_god_objects/SKILL.md` → sección **«Estado de la tarea B5 — FINALIZADA»** (tabla). Incluye: poda masiva de `AppModel`, fallbacks de `ui_dialog_dependency_wiring`, señales en `AppModel`, orquestación multi-servicio, bootstrap, sub-widgets de reportes.
- **Gates:** `pytest` focal reportes + smart_search + app_controller orchestration + `test_reports_widgets`; `mypy` sobre los tres módulos de producto tocados.
- **Fecha cierre:** 2026-04-04

## ITEM 007 — `DatabaseManager.SessionLocal` tipado + borde repo/sesión

- **Estado:** Completado
- **Prioridad:** P1 (datos / arranque / seguridad)
- **Alcance:** `database/database_manager.py` (`SessionLocal: Callable[[], Session] | None`); `controllers/preproceso_controller.py` (retirado `# type: ignore[arg-type]`; guard si `SessionLocal` es `None`); `controllers/session_controller.py` (mismo guard antes de `RateLimiter`/`AuditLogger`); `controllers/startup_controller.py` (narrowing explícito `is not None` en lugar de `cast(Callable[[], Any], …)`).
- **Gates:** `mypy app.py core controllers database features ui tests` OK; pytest focal `test_preproceso_controller_comprehensive`, `test_database_manager_full`, `test_startup_controller`, `test_session_controller_comprehensive` OK.
- **Docs:** La referencia técnica generada (`Documentacion Daniel.md`/PDF) se actualizó en la misma sincronización que ITEM 008 (`generate_daniel_doc.py`).
- **Fecha cierre:** 2026-04-03

## ITEM 008 — Tipado estricto en controladores críticos + `flow_card_widget`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `IFabricacionControllerDelegate` en `controllers/product/protocols.py`; `FabricacionController` (`IView` + delegate); `ScheduleController` / `ScheduleUiOpsHelper` (`DatabaseManager`, `IView`, `ScheduleConfig`; `QDialog` con `cast(QWidget, …)`); `BackupController` + `IBackupControllerDatabase`, `MainView`, `BackupService`/`AuditLogger`; `backup_controller_io_manager` (`MainView`, `AuditLogger`, `statusBar` nulable); `PilaController` (`IPilaDatabase`, servicios pila, `ApplicationState`, `ScheduleConfig`, `QListWidgetItem`); `SystemIntegrationService.search_lotes` → `list[LoteDTO]`; `flow_card_widget` (`QMouseEvent | None`, `isinstance(parent, QWidget)`); `startup_controller` (`cast(MainView)`, `cast(IFabricacionControllerDelegate)`, `resolve(ApplicationState)` para Pila); tests `test_schedule_controller_comprehensive` (`Any` en fixtures), `test_phase5_di_injection` (casts pila), `DummyDB.db_path`.
- **Gates:** `mypy app.py core controllers database features ui tests` OK; pytest focal fabricación + schedule + backup + phase5 + pila OK.
- **Docs (sincronización posterior):** `python3 scripts/generate_daniel_doc.py` → `Documentacion/Documentacion Daniel.md` + `.pdf`; `python3 scripts/check_documentation_omissions.py` → omitidos=0.
- **Fecha cierre:** 2026-04-03

## ITEM 009 — Herramienta y skill de arquitectura por capas (`architecture_layer_edges` + `ANALISIS_CAPAS`)

- **Estado:** Completado
- **Prioridad:** P2 (herramienta y documentación; sin P0 de arranque derivado solo del grafo)
- **Alcance:** `scripts/architecture_layer_edges.py`, `tests/unit/test_architecture_layer_edges.py`, `Documentacion/Refactorizacion_Completa/Arquitectura_Dependencias/ANALISIS_CAPAS.md` y snapshots, `.agents/skills/arquitectura_dependencias_hipatia/`, `.cursor/agents/hipatia-arquitectura-dependencias.md`, `SKILL_INDEX.md`, docstring de `audit_import_graph.py`.
- **Cambio:** Análisis AST de imports entre prefijos de capa; salida MD + JSON; tests del parser; informe maestro con P0/P1/P2 y backlog; skill operativa con `references/gates.md` y plantilla REGISTRO; agente Cursor dedicado.
- **Gates:** `pytest tests/unit/test_architecture_layer_edges.py` OK; `mypy app.py core controllers database features ui tests` OK en el cierre del ítem; `generate_daniel_doc.py` + `check_documentation_omissions.py` → omitidos=0.
- **Fecha cierre:** 2026-04-04

## ITEM 010 — Opt-1: quitar falsa arista `core`→`ui` en `qr_scanner.scanner`

- **Estado:** Completado
- **Prioridad:** P1 (arquitectura por capas)
- **Alcance:** `core/qr_scanner/scanner.py`
- **Cambio:** Sustituir `from .ui import draw_qr_detection` por `from core.qr_scanner.ui import draw_qr_detection`. El import relativo `.ui` se registraba en el AST como el paquete top-level `ui`; el módulo real es `core.qr_scanner.ui` (OpenCV, sin widgets Qt).
- **Gates:** `pytest` focal `test_qr_scanner`, `test_hardware_controller` OK; `mypy core/qr_scanner/scanner.py` OK; `architecture_layer_edges.py` → sección `core`→`ui` con **0 aristas**.
- **Progreso:** `PROGRESO_OPTIMIZACION_CAPAS.md` — Opt-1 → completada.
- **Fecha cierre:** 2026-04-05

## ITEM 011 — Opt-2: retirar imports `database` en diálogos de fabricación (`create_dialog`, `selection_dialogs`)

- **Estado:** Completado
- **Prioridad:** P1 (frontera capas ui/database)
- **Alcance:** `ui/dialogs/fabrication/create_dialog.py`, `ui/dialogs/fabrication/selection_dialogs.py`, `tests/unit/test_ui_opt2_fabrication_dialogs_boundary.py` (nuevo).
- **Cambio:** Eliminados bloques `TYPE_CHECKING` que importaban `database.models`; el analizador AST y `architecture_layer_edges` contaban esas aristas como `ui`→`database` aunque solo fueran tipos. El diálogo ya usaba `List[Any]` / objetos duck-typed en runtime; sin dependencia real del ORM en la capa UI.
- **Tests:** `test_create_dialog`, `test_fabrication_dialogs`, `test_ui_opt2_fabrication_dialogs_boundary`, `test_dialogs_setup` OK; asserts AST sin imports `database`.
- **Gates:** `mypy` OK (603 archivos); `ui_dto_boundary_analyzer` → 0 hallazgos; `architecture_layer_edges` → `ui`→`database` **0 aristas**; `generate_daniel_doc` + `check_documentation_omissions` → omitidos=0.
- **Progreso:** `PROGRESO_OPTIMIZACION_CAPAS.md` — Opt-2 → completada.
- **Fecha cierre:** 2026-04-05

## ITEM 012 — Opt-3: eliminar `features`→`ui` (worker + cámara + import muerto)

- **Estado:** Completado
- **Prioridad:** P1
- **Alcance:** `features/worker_controller.py`, `features/worker_controller_io_manager.py`, `controllers/worker/controller.py`, `controllers/worker/worker_camera_config.py` (nuevo), `controllers/session_controller.py`, tests asociados.
- **Cambio:** Retirado import no usado `OrderSetupDialog` desde `ui.dialogs.tracking_dialogs`. La configuración de cámara que importaba `CameraConfigDialog` se extrajo a `run_worker_camera_config_dialog` en controllers e inyección `camera_config_runner` en `FeatureWorkerController` (lambda desde `WorkerController` y `SessionController`).
- **Gates:** pytest focal + `test_ui_opt3_features_no_ui_imports`; `mypy` OK; `ui_dto_boundary_analyzer` → 0; `architecture_layer_edges` → `features`→`ui` **0 aristas**.
- **Progreso:** Opt-3 → completada.
- **Fecha cierre:** 2026-04-05

## ITEM 013 — Opt-4 (lote 1): `calculation_controller` sin import AST a `ui`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `controllers/calculation_controller.py`, `tests/unit/test_controllers_opt4_calculation_no_ui_import.py`.
- **Cambio:** Retirado `TYPE_CHECKING` → `ui.widgets.calculate_times_widget`; anotaciones `calc_page` como `Optional[Any]`. Sin cambio de runtime; el analizador AST dejaba de contar una arista `controllers`→`ui` por el bloque de tipos.
- **Gates:** pytest `test_calculation_controller_comprehensive` + test de frontera; mypy global OK; `architecture_layer_edges` → **55** aristas `controllers`→`ui` (antes 56); `check_documentation_omissions` → omitidos=0.
- **Docs:** `ANALISIS_CAPAS.md` §1.1 (qué se documenta por ítem vs hitos mayores).
- **Progreso:** Opt-4 — primer sub-ítem en `PROGRESO_OPTIMIZACION_CAPAS.md`.
- **Fecha cierre:** 2026-04-05

## ITEM 014 — Opt-5 (poda 1): retirar `get_all_prep_steps` de `AppModel`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `core/app_model.py`.
- **Cambio:** Eliminado el delegador `get_all_prep_steps` (cero referencias `model.` / `app_model` fuera de la clase; la API equivalente sigue en `SystemFacade` → `PreparationService`).
- **Gates:** pytest `-k app_model` → 48 passed; mypy global OK (607 archivos); `check_documentation_omissions` → omitidos=0.
- **Progreso:** Opt-5 en curso — primer sub-ítem en `PROGRESO_OPTIMIZACION_CAPAS.md`; Opt-4 cerrada para este sprint con backlog de **55** aristas `controllers`→`ui` (Opt-4b).
- **Fecha cierre:** 2026-04-03

## ITEM 015 — Opt-5 (poda 2): retirar `get_all_ordenes_fabricacion` de `AppModel`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `core/app_model.py`.
- **Cambio:** Eliminado el delegador `get_all_ordenes_fabricacion` (cero llamadas `model.*` / `app_model.*`; producción usa `FabricacionService` / `tracking_repo`; API equivalente en `SystemFacade`).
- **Gates:** pytest `-k app_model` → 48 passed; mypy global OK (607 archivos); `check_documentation_omissions` → omitidos=0.
- **Progreso:** Opt-5 — sub-ítem Opt-5b en `PROGRESO_OPTIMIZACION_CAPAS.md`.
- **Fecha cierre:** 2026-04-03

## ITEM 016 — Opt-5 (poda 3): retirar CRUD lote vía `AppModel` (salvo `get_lote_details`)

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `core/app_model.py`.
- **Cambio:** Eliminados `search_lotes`, `create_lote`, `update_lote`, `delete_lote` (cero consumidores `model.*`; `LoteManager` usa el adaptador `_db` / `SystemIntegrationService`; `calculate_times_widget` sigue pudiendo usar `model.get_lote_details`).
- **Gates:** pytest `-k "app_model or lote"` → 132 passed; mypy global OK (607 archivos); `check_documentation_omissions` → omitidos=0.
- **Progreso:** Opt-5 — sub-ítem Opt-5c en `PROGRESO_OPTIMIZACION_CAPAS.md`.
- **Fecha cierre:** 2026-04-03
- **Seguimiento (2026-04, plan viabilidad AppModel):** retirado también `get_lote_details` de `AppModel` (criterio `rg` = 0). `ui/widgets/calculate_times_widget.py` usa `app.model.system_integration.get_lote_details` si no hay `db.lote_repo`; detalle de fabricación en ese bloque vía `db.preproceso_repo.get_fabricacion_by_id`. La mención a «mantener `get_lote_details`» en ITEM 019 queda histórica.

## ITEM 017 — Opt-5 (poda 4): iteraciones / imágenes sin delegación en `AppModel`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `core/app_model.py`, `controllers/product/protocols.py` (`IProductModel`).
- **Cambio:** Eliminados `get_iteration_images`, `update_iteration_file_path` (solo `db`; la UI usa `controller.db` / `product_facade`), `get_product_iterations_by_id_or_similar` y `get_all_iterations_with_dates` (solo `product_facade` sin consumidores `model.*`). Retirado `update_iteration_file_path` del protocolo `IProductModel` para alinear tipos con `AppModel`. Import `IterationImageDTO` innecesario en `app_model`.
- **Gates:** pytest focal `-k "app_model or product_controller_preprocesos or product_dialogs_coverage or historial_controller or app_startup_integration"` → 239 passed; mypy global OK (607 archivos); `check_documentation_omissions` → omitidos=0.
- **Progreso:** Opt-5 — sub-ítem Opt-5d en `PROGRESO_OPTIMIZACION_CAPAS.md`.
- **Fecha cierre:** 2026-04-03

## ITEM 018 — Opt-5 (poda 5): catálogo y trabajador vía servicios, no vía `AppModel`

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `core/app_model.py`.
- **Cambio:** Eliminados `get_latest_products` (solo `product_facade`, sin `model.*`), `get_worker_history` y `get_worker_activity_log` (UI y `TaskManager` usan `WorkerService` inyectado). Retirado import huérfano `WorkerAnnotationDTO`.
- **Gates:** pytest `-k "app_model or worker_controller or workers_widget or worker_service"` → 146 passed; mypy global OK (607 archivos); `check_documentation_omissions` → omitidos=0.
- **Progreso:** Opt-5 — sub-ítem Opt-5e en `PROGRESO_OPTIMIZACION_CAPAS.md`.
- **Fecha cierre:** 2026-04-03

## ITEM 019 — Opt-5 (poda 6 / cierre ciclo): delegadores ya cubiertos por servicios inyectados

- **Estado:** Completado
- **Prioridad:** P2
- **Alcance:** `core/app_model.py`.
- **Cambio:** Retirados del hub los métodos que solo reenviaban a `worker_service`, `machine_service`, `preparation_service`, `product_facade`, `planning_facade` o `system_integration` **sin** referencias `model.<método>` / `getattr(..., "model")` en UI, controladores o tests (criterio `rg` ampliado). Incluye: `get_worker_details`, `authenticate_user`, `update_user_password`, `actualizar_estado_asignacion`, `asignar_trabajador_a_fabricacion`, `desasignar_trabajador_de_fabricacion`, `update_machine`, `delete_machine`, `update_prep_step`, `delete_prep_step`, `get_group_details`, `get_prep_step_details`, `get_prep_step_details_by_ids`, `update_product_iteration_details`, `delete_material_link`, `get_all_pilas_with_dates`, `config_get_setting`, `config_set_setting`. Se mantienen p. ej. `get_fabricaciones_por_trabajador`, `assign_task_to_worker`, `get_lote_details`. Eliminado import `WorkerDetailDTO` al quedar sin uso.
- **Verificación cíclica:** script de patrones `model.*` / `getattr(..., "model")` sobre los 77 métodos restantes → **0** candidatos adicionales; Opt-5 cerrada bajo este criterio hasta nueva migración DI explícita.
- **Gates:** pytest global → 2696 passed; mypy global OK (607 archivos); `check_documentation_omissions` → omitidos=0.
- **Progreso:** Opt-5 → **completada** (poda por consumidores 0); ver `PROGRESO_OPTIMIZACION_CAPAS.md`.
- **Fecha cierre:** 2026-04-03

## ITEM 020 — Opt-4b (lote 2): menos aristas `controllers`→`ui` (TYPE_CHECKING / `Any`)

- **Estado:** Completado
- **Prioridad:** P2 (opcional)
- **Alcance:** `controllers/lote_controller.py`, `controllers/report_controller.py`, `controllers/ui_controller.py`, `controllers/machine_controller.py`.
- **Cambio:** Eliminados imports `ui` muertos o solo tipado (`lote_controller`, `ui_controller`). En `report_controller`, `view` y `historial_widget` tipados como `Any` para evitar imports `ui` en AST. En `machine_controller`, retirados imports `ui` bajo `TYPE_CHECKING` (sigue el import en tiempo de ejecución de `PrepGroupsDialog`). Informe `architecture_layer_edges`: **55 → 49** aristas `controllers`→`ui` (el grafo deduplica por módulo destino).
- **Gates:** pytest `-k "report_controller or lote_controller or machine_controller or ui_controller or opt4"` → 84 passed; mypy `core controllers database ui features` → sin errores; `check_documentation_omissions` → omitidos=0.
- **Progreso:** Opt-4b en `PROGRESO_OPTIMIZACION_CAPAS.md`; `ANALISIS_CAPAS.md` actualizado.
- **Fecha cierre:** 2026-04-03

## ITEM 021 — Opt-4b (cierre): cero aristas AST `controllers`→`ui`

- **Estado:** Completado
- **Prioridad:** P2 (opcional / arquitectura)
- **Alcance:** Todo `controllers/**/*.py`, nuevo `controllers/ui_class_loader.py`, tests (`test_opt4_ast_guard_no_static_ui_imports.py`, ajustes `test_schedule_controller_comprehensive`, `scripts/test_quality_analyzer.py`).
- **Cambio:** Sustituidos los `import`/`from ui…` estáticos por `importlib.import_module` vía `ui_class_loader.ui_class` (sin caché, compatible con parches de tests en `ui.dialogs.*`). Referencias a nivel de módulo donde los tests parchean `controllers.*.Dialog`; resolución perezosa en `show_backup_restore_dialog` para parches a `ui.dialogs.backup_restore_dialog`. Tipos `MainView`/`SettingsWidget` sustituidos por `Any` o duck typing donde aplica. `navigation_controller` usa `ui_class` en ramas para `isinstance`.
- **Informe:** `architecture_layer_edges` → **0** aristas `controllers`→`ui` (matriz y lista de advertencias vacías para ese par).
- **Gates:** pytest global → **2696** passed; mypy `core controllers database ui features` → 362 archivos OK; `check_documentation_omissions` → omitidos=0.
- **Progreso:** Opt-4 y Opt-4b → **completadas** en `PROGRESO_OPTIMIZACION_CAPAS.md`; `ANALISIS_CAPAS.md` actualizado.
- **Fecha cierre:** 2026-04-03

## ITEM 022 — Sincronización documentación interna + `generate_daniel_doc` (2026-04-03)

- **Estado:** Completado
- **Prioridad:** P2 (trazabilidad / informe Daniel)
- **Alcance:** Docstrings de módulos UI tocados por reducción de `AppModel` en el borde (bitácora, `DefineFlowPresenter`, `FlowActionHandler`, `ReportesWidget` y widgets `reports/*`, `dialog_dependencies`); skills `.agents/skills/ui_dialog_dependency_wiring/` (SKILL + REGISTRO filas 12–14), `reduccion_god_objects`, `plan_produccion_coordinador`; `Documentacion/Refactorización UI/Analisis_y_Plan_Refactorizacion.md`; `scripts/generate_daniel_doc.py` (diagrama Core con `PilaService`/`ReportService`, hints `test_bitacora_dialog`, `test_define_flow_presenter`, `test_reports_widgets` unificado).
- **Salida:** `python3 scripts/generate_daniel_doc.py` regenera `Documentacion/Documentacion Daniel.md` y PDF sin referencias a delegadores de bitácora eliminados en `AppModel`.
- **Fecha cierre:** 2026-04-03

## Siguiente ítem sugerido

- **Mantenimiento:** no reintroducir imports estáticos `ui` en `controllers/` (fallará `test_opt4_ast_guard_no_static_ui_imports`).
- **Reducción adicional de `AppModel`:** solo con **migración explícita** a servicios/fachadas inyectados (no poda ciega: los métodos restantes tienen al menos un uso vía `model` en tests o UI).
- **Bloque C (producción Windows):** C1 paths — ver `.agents/skills/plan_produccion_coordinador/SKILL.md`.
- **Mantenimiento mypy:** nuevos módulos bajo `ui`/`core` deben añadirse a `mypy.ini` o cumplir el patrón ya estricto. **Huecos típicos restantes** respecto a `[mypy-ui.*]` / `[mypy-controllers.*]` laxos: solo lo no cubierto por patrones más específicos (revisar con `mypy .` al introducir código). **Lote D (repositorios + servicios + UI densa + widgets + qr_scanner):** cerrado a efectos prácticos para el árbol de producto.
