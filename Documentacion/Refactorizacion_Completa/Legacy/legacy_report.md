# Informe de Código Legacy — Fase 4

> **Fecha:** 2026-03-18 06:43:00
> **Generado por:** `scripts/legacy_analyzer.py`

---

## 1. Resumen

| Categoría | Cantidad |
|-----------|----------|
| print_en_produccion | 15 |
| bare_except | 0 |
| deprecated_markers | 11 |
| docstring_legacy | 11 |
| simple_delegation | 41 |
| legacy_comment | 19 |

---

## 2. `print()` en código de producción

Sustituir por `logger.debug()` o `logger.info()` según corresponda.

| Archivo | Línea | Contexto |
|---------|-------|----------|
| ui/dialogs/connection_dialog.py | 130 | `print(f"Selected: {dialog.get_selection()}")...` |
| ui/widgets/lotes_widget.py | 83 | `print(f"Error cargando fabricaciones: {e}")...` |
| ui/widgets/lotes_widget.py | 117 | `print(f"Error cargando productos: {e}")...` |
| ui/widgets/settings_widget.py | 308 | `print("Error: Controller or necessary attributes not set.")...` |
| ui/widgets/settings_widget.py | 336 | `print("Error: Controller or model not set.")...` |
| ui/widgets/settings_widget.py | 355 | `print(f"Warning: Error loading breaks: {e}")...` |
| ui/widgets/settings_widget.py | 365 | `print(f"Warning: Error loading holidays: {e}")...` |
| ui/worker/camera_config_dialog.py | 430 | `print("=" * 70)...` |
| ui/worker/camera_config_dialog.py | 431 | `print("DIÁLOGO DE CONFIGURACIÓN DE CÁMARA - Test (Optimizado...` |
| ui/worker/camera_config_dialog.py | 432 | `print("=" * 70)...` |
| ui/worker/camera_config_dialog.py | 448 | `print(f"\n✅ Usuario seleccionó cámara: {selected}")...` |
| ui/worker/camera_config_dialog.py | 450 | `print("\n❌ Usuario canceló la configuración")...` |
| ui/worker/camera_config_dialog.py | 452 | `print("\n" + "=" * 70)...` |
| ui/worker/camera_config_dialog.py | 453 | `print("Test completado")...` |
| ui/worker/camera_config_dialog.py | 454 | `print("=" * 70)...` |

---

## 4. Marcadores @deprecated / TODO: Remove

| Archivo | Línea | Contexto |
|---------|-------|----------|
| scripts/analysis/detect_obsolete_code.py | 71 | `def check_deprecated(file_path: str) -> List[str]:` |
| scripts/analysis/detect_obsolete_code.py | 72 | `"""Check for @deprecated decorators or TODO: Remove comments."""` |
| scripts/analysis/detect_obsolete_code.py | 79 | `if "@deprecated" in line or "TODO: Remove" in line or "DEPRECATED" in ` |
| scripts/analysis/detect_obsolete_code.py | 105 | `# Check for obsolete/deprecated markers` |
| scripts/analysis/detect_obsolete_code.py | 106 | `print("\\n--- Deprecated/Obsolete Code Markers ---")` |
| scripts/analysis/detect_obsolete_code.py | 107 | `found_deprecated = False` |
| scripts/analysis/detect_obsolete_code.py | 109 | `issues = check_deprecated(file)` |
| scripts/analysis/detect_obsolete_code.py | 111 | `found_deprecated = True` |
| scripts/analysis/detect_obsolete_code.py | 117 | `if not found_deprecated:` |
| scripts/analysis/detect_obsolete_code.py | 118 | `print("No explicit @deprecated or 'TODO: Remove' markers found.")` |
| tests/unit/test_product_dialogs_coverage.py | 782 | `# --- Reselect & Deprecated ---` |

---

## 5. Docstrings con obsoleto/legacy/deprecated

Revisar si el símbolo debe eliminarse o actualizar el docstring.

| Archivo | Línea | Símbolo | Tipo | Palabra clave |
|---------|-------|---------|------|---------------|
| core/dtos.py | 77 | `AuthResponseDTO` | class | legacy |
| scripts/analysis/detect_obsolete_code.py | 71 | `check_deprecated` | function | deprecated |
| tests/unit/test_enhanced_flow_presenter.py | 111 | `test_normalize_workers_strings` | function | legacy |
| tests/unit/test_product_dialogs_coverage.py | 367 | `test_on_iteration_selected_with_legacy_image` | function | legacy |
| tests/unit/test_product_dialogs_coverage.py | 381 | `test_on_iteration_selected_no_legacy_image` | function | legacy |
| tests/unit/test_product_dialogs_coverage.py | 392 | `test_on_iteration_selected_with_additional_images` | function | legacy |
| tests/unit/test_product_dialogs_coverage.py | 410 | `test_on_iteration_selected_additional_same_as_legacy` | function | legacy |
| tests/unit/test_product_dialogs_coverage.py | 716 | `test_on_delete_image_legacy` | function | legacy |
| tests/unit/test_product_dialogs_coverage.py | 730 | `test_on_delete_image_confirmed_success` | function | legacy |
| ui/widgets/machines_widget.py | 12 | `__init__` | function | obsoleto |
| ui/widgets/settings_widget.py | 21 | `__init__` | function | obsoleto |

---

## 6. Delegaciones simples (posibles shims)

Verificar si hay callers; si no, eliminar y usar el destino directo.

| Archivo | Línea | Función | Delega en |
|---------|-------|---------|-----------|
| controllers/product/product_manager.py | 333 | `handle_delete_iteration_image` | `delete_iteration_image` |
| core/app_model.py | 204 | `add_iteration_image` | `add_image` |
| core/app_model.py | 210 | `delete_iteration_image` | `delete_image` |
| core/app_model.py | 471 | `config_get_setting` | `get_setting` |
| core/app_model.py | 474 | `config_set_setting` | `set_setting` |
| core/application_state.py | 46 | `get` | `getattr` |
| core/camera_manager/__init__.py | 11 | `quick_detect_cameras` | `detect_cameras` |
| core/camera_manager/manager.py | 39 | `validate_camera_hardware` | `validate_hardware` |
| core/camera_manager/manager.py | 111 | `test_camera_with_preview` | `test_preview` |
| core/dtos.py | 89 | `get` | `getattr` |
| core/qr_scanner/scanner.py | 61 | `parse_qr_data` | `get_qr_info` |
| core/qr_scanner/scanner.py | 64 | `validate_qr_format` | `validate_qr` |
| core/services/fabricacion_service.py | 101 | `get_all_preprocesos_with_components` | `get_all_preprocesos` |
| core/services/maintenance_service.py | 23 | `run` | `perform_maintenance` |
| core/services/pila_service.py | 79 | `add_diario_entry` | `add_diario_evento` |
| core/services/product_service.py | 121 | `add_iteration_image` | `add_image` |
| core/services/product_service.py | 124 | `delete_iteration_image` | `delete_image` |
| core/services/product_service.py | 142 | `get_all_materials_for_selection` | `get_all_materials` |
| core/services/report_service.py | 24 | `search_reports_data` | `buscar_por_codigo` |
| core/services/report_service.py | 27 | `get_orders_for_product` | `obtener_ordenes_por_producto` |
| core/services/report_service.py | 30 | `get_order_details` | `obtener_detalle_orden` |
| core/services/report_service.py | 33 | `get_product_time_stats` | `calcular_promedio_tiempo_unidad` |
| core/services/report_service.py | 36 | `get_worker_time_stats` | `obtener_tiempos_por_trabajador` |
| core/services/report_service.py | 39 | `get_incidents_stats` | `obtener_incidencias_por_producto` |
| core/services/report_service.py | 42 | `get_evolution_stats` | `obtener_evolucion_temporal` |
| core/services/report_service.py | 45 | `get_product_summary` | `obtener_resumen_producto` |
| core/services/report_service.py | 48 | `get_order_units` | `obtener_unidades_de_orden` |
| database/database_manager.py | 139 | `get_iteration_images` | `get_images` |
| database/repositories/tracking/core_manager.py | 52 | `iniciar_trabajo` | `obtener_o_crear_trabajo_log_por_qr` |
| ui/dialogs/canvas_widget.py | 41 | `dragEnterEvent` | `acceptProposedAction` |

---

## 7. Comentarios legacy / re-export

| Archivo | Línea | Contexto |
|---------|-------|----------|
| controllers/app_controller.py | 19 | `# Re-export for compatibility` |
| controllers/app_controller.py | 243 | `# Se usaba en tests/legacy code` |
| controllers/app_controller.py | 259 | `# --- Métodos Legacy / Re-Exports ---` |
| controllers/startup_controller.py | 82 | `# 4. Delegaciones (Legacy support) eliminado` |
| controllers/ui_signals_controller.py | 78 | `# on_data_changed es legacy en AppController, pero útil como hub` |
| core/services/report_strategy.py | 3 | `# Re-exporta las clases desde el nuevo paquete core.services.reporting` |
| core/simulation/event_engine.py | 3 | `# Re-exporta MotorDeEventos desde el nuevo paquete core.simulation.eng` |
| database/database_manager.py | 7 | `# Se ha eliminado el soporte legacy para SQLite directo y migraciones ` |
| scripts/analysis/detect_obsolete_code.py | 122 | `# We will just list the files that might be candidates for deletion ba` |
| scripts/codebase_analyzer.py | 31 | `# Legacy indicators` |
| tests/integration/test_preproceso_integration.py | 32 | `# 4. Verificar recuperación mediante repositorio (método legacy que de` |
| tests/unit/test_create_dialog.py | 210 | `# Select and assign via legacy API` |
| tests/unit/test_create_fabricacion_dialog.py | 210 | `# since the logic is in the dialog methods (legacy pattern)` |
| tests/unit/test_product_controller_preprocesos.py | 947 | `# Legacy attachment` |
| tests/unit/test_product_dialogs_coverage.py | 389 | `# Sin ruta_imagen, la galería no debe tener imágenes legacy` |
| ui/dialogs/fabrication/persistence_dialogs.py | 50 | `# Support both DTOs and legacy tuples if necessary, or assume DTOs` |
| ui/main_window.py | 23 | `from core.utils.helpers import resource_path  # re-exported for backwa` |
| ui/widgets/production_flow/flow_graph_manager.py | 146 | `# Aplicar resaltados a widgets (Colores del diseño legacy)` |
| ui/widgets/production_flow/inspector_panel.py | 333 | `# Removed legacy refresh method` |

---

## 8. Orden de actuación recomendado

1. **print → logger** en producción (evitar falsos positivos en scripts/tests).
2. **Bare except** → `except Exception` + logging.
3. **Docstrings legacy**: actualizar o eliminar API obsoleta.
4. **Delegaciones**: comprobar referencias; si no hay usos, eliminar y redirigir.
5. **Marcadores y comentarios**: eliminar código marcado o actualizar documentación.

Tras cada cambio: ejecutar `python3 -m pytest <scope> -x -q` y `python3 run_tests.py`.

*Generado — 2026-03-18*