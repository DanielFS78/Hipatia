# Listado de archivos de test — Orden de trabajo

> **Fuente:** generado desde `test_reports/compliance_data.json`.  
> **Criterio de orden:** más trabajo pendiente primero (Gap = Techo − Score), luego por score.  
> **Estado hecho/pendiente:** la fuente de verdad es **`.agents/skills/orden_trabajo_tests/SKILL.md`** — ahí se marca ✅ al completar cada archivo y se sabe cuál es el siguiente a realizar.

---

## Leyenda

| Campo | Significado |
|-------|-------------|
| **#** | Orden de trabajo recomendado (1 = primero a abordar). |
| **Score** | Puntuación actual del analizador de calidad. |
| **Techo** | Puntuación máxima alcanzable (según analizador). |
| **Gap** | Techo − Score; mayor gap = más margen de mejora. |
| **Nivel Fase B** | **Sí** = archivo con revisión dura aplicada (checklist Fase B cumplido). **—** = pendiente de revisión. |

Solo 6 archivos tienen actualmente **Nivel Fase B** (revisados a mano con el estándar alto):  
`test_session_controller_comprehensive.py`, `test_simulation_controller_comprehensive.py`, `test_report_controller_comprehensive.py`, `test_settings_widget.py`, `test_camera_config_dialog.py`, `test_features_worker_controller.py`.

---

## Cómo usar este listado

1. Trabajar **en orden** desde el #1 (más trabajo) hasta el último (casi listos / en techo).
2. Por cada archivo: aplicar las reglas del backlog y el **Checklist Revisión Fase B**; ejecutar `pytest <archivo> -x -q`.
3. Marcar ✅ en el backlog **solo** cuando el checklist esté cumplido y los tests pasen.
4. Cuando un archivo alcance el estándar de revisión Fase B, se puede anotar aquí **Nivel Fase B: Sí** en una futura actualización del documento.

---

## Listado completo (orden: más trabajo → menos trabajo)

| # | Ruta | Score | Techo | Gap | Nivel Fase B |
|---|------|-------|-------|-----|--------------|
| 1 | `tests/unit/test_schedule_controller_comprehensive.py` | 43 | 85 | 42 | — |
| 2 | `tests/unit/test_worker_controller_comprehensive.py` | 0 | 36 | 36 | — |
| 3 | `tests/unit/test_define_flow_dialog_edge.py` | 35 | 65 | 30 | — |
| 4 | `tests/unit/test_label_manager.py` | 55 | 85 | 30 | — |
| 5 | `tests/unit/test_lote_controller_comprehensive.py` | 55 | 85 | 30 | — |
| 6 | `tests/unit/test_lote_manager_isolated.py` | 55 | 85 | 30 | — |
| 7 | `tests/unit/test_pila_manager_isolated.py` | 55 | 85 | 30 | — |
| 8 | `tests/unit/test_navigation_controller_comprehensive.py` | 60 | 90 | 30 | — |
| 9 | `tests/unit/test_product_controller_preprocesos.py` | 62 | 92 | 30 | — |
| 10 | `tests/unit/test_historial_controller_comprehensive.py` | 70 | 100 | 30 | — |
| 11 | `tests/unit/test_machine_controller_comprehensive.py` | 70 | 100 | 30 | — |
| 12 | `tests/unit/test_product_dialogs_coverage.py` | 70 | 100 | 30 | — |
| 13 | `tests/unit/test_ui_controller_comprehensive.py` | 70 | 100 | 30 | — |
| 14 | `tests/unit/test_worker_main_window.py` | 70 | 100 | 30 | — |
| 15 | `tests/unit/test_camera_config_dialog.py` | 65 | 85 | 20 | Sí |
| 16 | `tests/unit/test_calculation_controller_comprehensive.py` | 37 | 55 | 18 | — |
| 17 | `tests/unit/test_main_window.py` | 0 | 15 | 15 | — |
| 18 | `tests/unit/test_enhanced_flow_dialog.py` | 2 | 17 | 15 | — |
| 19 | `tests/unit/test_report_controller_comprehensive.py` | 53 | 68 | 15 | Sí |
| 20 | `tests/controllers/product/test_product_manager.py` | 55 | 70 | 15 | — |
| 21 | `tests/unit/test_create_fabricacion_dialog.py` | 45 | 55 | 10 | — |
| 22 | `tests/unit/test_fabrication_dialogs.py` | 0 | 9 | 9 | — |
| 23 | `tests/unit/test_file_controller.py` | 14 | 22 | 8 | — |
| 24 | `tests/unit/test_canvas_widgets_coverage.py` | 20 | 25 | 5 | — |
| 25 | `tests/e2e/test_backup_audit_e2e.py` | 40 | 45 | 5 | — |
| 26 | `tests/unit/test_bitacora_dialog.py` | 50 | 55 | 5 | — |
| 27 | `tests/unit/test_create_dialog.py` | 50 | 55 | 5 | — |
| 28 | `tests/unit/test_flow_builder_service.py` | 0 | 0 | 0 | — |
| 29 | `tests/unit/test_machines_widget.py` | 0 | 0 | 0 | — |
| 30 | `tests/unit/test_simulation_events_comprehensive.py` | 0 | 0 | 0 | — |
| 31 | `tests/unit/test_timeline_widget.py` | 0 | 0 | 0 | — |
| 32 | `tests/unit/test_ui_scaler.py` | 0 | 0 | 0 | — |
| 33 | `tests/unit/test_worker_validation_service.py` | 0 | 0 | 0 | — |
| 34 | `tests/unit/test_report_strategy_comprehensive.py` | 1 | 1 | 0 | — |
| 35 | `tests/unit/test_qr_scanner.py` | 2 | 2 | 0 | — |
| 36 | `tests/unit/test_security_phase2_integration.py` | 2 | 2 | 0 | — |
| 37 | `tests/unit/test_startup_controller.py` | 2 | 2 | 0 | — |
| 38 | `tests/unit/test_audit_report_generator.py` | 7 | 7 | 0 | — |
| 39 | `tests/unit/test_scheduler_logic.py` | 7 | 7 | 0 | — |
| 40 | `tests/integration/test_widgets_integration.py` | 7 | 7 | 0 | — |
| 41 | `tests/unit/test_canvas_widgets.py` | 9 | 9 | 0 | — |
| 42 | `tests/unit/test_lotes_widget.py` | 10 | 10 | 0 | — |
| 43 | `tests/unit/test_camera_manager_no_cv2.py` | 15 | 15 | 0 | — |
| 44 | `tests/unit/test_database_config.py` | 15 | 15 | 0 | — |
| 45 | `tests/unit/test_flow_simulation_service.py` | 15 | 15 | 0 | — |
| 46 | `tests/setup/test_label_counter_setup.py` | 15 | 15 | 0 | — |
| 47 | `tests/unit/test_report_sheets.py` | 15 | 15 | 0 | — |
| 48 | `tests/unit/test_security_validation.py` | 15 | 15 | 0 | — |
| 49 | `tests/unit/test_smart_search.py` | 15 | 15 | 0 | — |
| 50 | `tests/unit/test_sync_service.py` | 15 | 15 | 0 | — |
| 51 | `tests/unit/test_tracking_dialogs.py` | 15 | 15 | 0 | — |
| 52 | `tests/unit/test_utility_dialogs_coverage.py` | 15 | 15 | 0 | — |
| 53 | `tests/unit/test_worker_db_sync.py` | 17 | 17 | 0 | — |
| 54 | `tests/unit/test_app_model.py` | 18 | 18 | 0 | — |
| 55 | `tests/unit/test_historial_widget.py` | 18 | 18 | 0 | — |
| 56 | `tests/integration/test_dialogs_integration.py` | 20 | 20 | 0 | — |
| 57 | `tests/unit/test_fabrications_widget.py` | 20 | 20 | 0 | — |
| 58 | `tests/unit/test_home_widget.py` | 20 | 20 | 0 | — |
| 59 | `tests/e2e/test_main_window_flows.py` | 20 | 20 | 0 | — |
| 60 | `tests/unit/test_reportes_widget.py` | 20 | 20 | 0 | — |
| 61 | `tests/unit/test_preprocesos_widget.py` | 22 | 22 | 0 | — |
| 62 | `tests/unit/test_product_service.py` | 22 | 22 | 0 | — |
| 63 | `tests/integration/test_pila_integration.py` | 24 | 24 | 0 | — |
| 64 | `tests/integration/test_app_model_integration.py` | 25 | 25 | 0 | — |
| 65 | `tests/integration/test_app_model_services_setup.py` | 25 | 25 | 0 | — |
| 66 | `tests/unit/test_code_quality_config.py` | 25 | 25 | 0 | — |
| 67 | `tests/unit/test_fabrication_module_structure.py` | 25 | 25 | 0 | — |
| 68 | `tests/setup/test_pila_setup.py` | 25 | 25 | 0 | — |
| 69 | `tests/pre_migration/test_tracking_repository_setup.py` | 25 | 25 | 0 | — |
| 70 | `tests/unit/test_flow_canvas.py` | 27 | 27 | 0 | — |
| 71 | `tests/unit/test_tracking_repository_stats_export.py` | 27 | 27 | 0 | — |
| 72 | `tests/unit/test_charts_widget.py` | 30 | 30 | 0 | — |
| 73 | `tests/unit/test_define_flow_presenter.py` | 30 | 30 | 0 | — |
| 74 | `tests/unit/test_event_engine_comprehensive.py` | 30 | 30 | 0 | — |
| 75 | `tests/unit/test_hardware_controller.py` | 30 | 30 | 0 | — |
| 76 | `tests/integration/test_iteration_integration.py` | 30 | 30 | 0 | — |
| 77 | `tests/unit/test_lote_repository.py` | 30 | 30 | 0 | — |
| 78 | `tests/unit/test_machine_controller.py` | 30 | 30 | 0 | — |
| 79 | `tests/unit/test_machine_repository.py` | 30 | 30 | 0 | — |
| 80 | `tests/unit/test_order_list_widget.py` | 30 | 30 | 0 | — |
| 81 | `tests/unit/test_reports_infrastructure.py` | 30 | 30 | 0 | — |
| 82 | `tests/integration/test_reports_ui_integration.py` | 30 | 30 | 0 | — |
| 83 | `tests/pre_migration/test_tracking_repository_unit.py` | 30 | 30 | 0 | — |
| 84 | `tests/db/test_product_repository.py` | 34 | 34 | 0 | — |
| 85 | `tests/unit/test_detect_dead_code.py` | 35 | 35 | 0 | — |
| 86 | `tests/unit/test_fabrication_dialogs_coverage.py` | 35 | 35 | 0 | — |
| 87 | `tests/unit/test_order_list.py` | 35 | 35 | 0 | — |
| 88 | `tests/unit/test_ui_signals_controller_comprehensive.py` | 35 | 35 | 0 | — |
| 89 | `tests/integration/test_configuration_integration.py` | 37 | 37 | 0 | — |
| 90 | `tests/unit/test_enhanced_flow_presenter.py` | 37 | 37 | 0 | — |
| 91 | `tests/unit/test_tracking_repository_coverage_fix.py` | 37 | 37 | 0 | — |
| 92 | `tests/unit/test_tracking_repository_full.py` | 37 | 37 | 0 | — |
| 93 | `tests/unit/test_camera_manager_main.py` | 40 | 40 | 0 | — |
| 94 | `tests/unit/test_common_production_dialogs.py` | 40 | 40 | 0 | — |
| 95 | `tests/unit/test_create_presenter.py` | 40 | 40 | 0 | — |
| 96 | `tests/unit/test_gestion_datos_widget.py` | 40 | 40 | 0 | — |
| 97 | `tests/unit/test_inspector_presenter.py` | 40 | 40 | 0 | — |
| 98 | `tests/unit/test_macos_fix.py` | 40 | 40 | 0 | — |
| 99 | `tests/utils/test_macos_setup.py` | 40 | 40 | 0 | — |
| 100 | `tests/unit/test_pila_repository.py` | 40 | 40 | 0 | — |
| 101 | `tests/integration/test_reports_integration.py` | 40 | 40 | 0 | — |
| 102 | `tests/unit/test_reports_repository.py` | 40 | 40 | 0 | — |
| 103 | `tests/unit/test_reports_widgets.py` | 40 | 40 | 0 | — |
| 104 | `tests/unit/test_widgets_coverage.py` | 40 | 40 | 0 | — |
| 105 | `tests/unit/test_define_flow_dialog.py` | 42 | 42 | 0 | — |
| 106 | `tests/unit/test_app_coverage.py` | 45 | 45 | 0 | — |
| 107 | `tests/unit/test_controller_interface.py` | 45 | 45 | 0 | — |
| 108 | `tests/unit/test_dialog_integration_smoke.py` | 45 | 45 | 0 | — |
| 109 | `tests/unit/test_inspector_panel.py` | 45 | 45 | 0 | — |
| 110 | `tests/unit/test_library_panel.py` | 45 | 45 | 0 | — |
| 111 | `tests/unit/test_prep_steps_widget.py` | 45 | 45 | 0 | — |
| 112 | `tests/unit/test_configuration_repository.py` | 47 | 47 | 0 | — |
| 113 | `tests/unit/test_database_manager_full.py` | 47 | 47 | 0 | — |
| 114 | `tests/setup/test_iteration_setup.py` | 47 | 47 | 0 | — |
| 115 | `tests/e2e/test_machine_workflow.py` | 47 | 47 | 0 | — |
| 116 | `tests/e2e/test_product_workflow.py` | 47 | 47 | 0 | — |
| 117 | `tests/unit/test_dialogs.py` | 49 | 49 | 0 | — |
| 118 | `tests/unit/test_maintenance_service.py` | 49 | 49 | 0 | — |
| 119 | `tests/unit/test_widgets_dashboard.py` | 49 | 49 | 0 | — |
| 120 | `tests/unit/test_worker_service.py` | 49 | 49 | 0 | — |
| 121 | `tests/reporting/test_audit_infra.py` | 50 | 50 | 0 | — |
| 122 | `tests/unit/test_backup_controller_comprehensive.py` | 50 | 50 | 0 | — |
| 123 | `tests/unit/test_common_dialogs.py` | 50 | 50 | 0 | — |
| 124 | `tests/unit/test_connection_dialog_comprehensive.py` | 50 | 50 | 0 | — |
| 125 | `tests/setup/test_dialogs_setup.py` | 50 | 50 | 0 | — |
| 126 | `tests/unit/test_help_widget.py` | 50 | 50 | 0 | — |
| 127 | `tests/e2e/test_label_counter_e2e.py` | 50 | 50 | 0 | — |
| 128 | `tests/unit/test_label_counter_repository.py` | 50 | 50 | 0 | — |
| 129 | `tests/integration/test_machine_integration.py` | 50 | 50 | 0 | — |
| 130 | `tests/setup/test_machine_setup.py` | 50 | 50 | 0 | — |
| 131 | `tests/data/test_package_compliance.py` | 50 | 50 | 0 | — |
| 132 | `tests/e2e/test_pila_workflow.py` | 50 | 50 | 0 | — |
| 133 | `tests/integration/test_preproceso_integration.py` | 50 | 50 | 0 | — |
| 134 | `tests/setup/test_preproceso_setup.py` | 50 | 50 | 0 | — |
| 135 | `tests/e2e/test_preproceso_workflow.py` | 50 | 50 | 0 | — |
| 136 | `tests/integration/test_product_integration.py` | 50 | 50 | 0 | — |
| 137 | `tests/setup/test_product_setup.py` | 50 | 50 | 0 | — |
| 138 | `tests/setup/test_widgets_setup.py` | 50 | 50 | 0 | — |
| 139 | `tests/integration/test_worker_integration.py` | 50 | 50 | 0 | — |
| 140 | `tests/setup/test_worker_setup.py` | 50 | 50 | 0 | — |
| 141 | `tests/e2e/test_worker_workflow.py` | 50 | 50 | 0 | — |
| 142 | `tests/unit/test_product_repository.py` | 52 | 52 | 0 | — |
| 143 | `tests/e2e/test_security_workflow.py` | 52 | 52 | 0 | — |
| 144 | `tests/unit/test_prep_dialogs_coverage.py` | 53 | 53 | 0 | — |
| 145 | `tests/unit/test_app_model_coverage.py` | 55 | 55 | 0 | — |
| 146 | `tests/e2e/test_app_services_e2e_setup.py` | 55 | 55 | 0 | — |
| 147 | `tests/unit/test_dashboard_widget.py` | 55 | 55 | 0 | — |
| 148 | `tests/e2e/test_dialogs_e2e.py` | 55 | 55 | 0 | — |
| 149 | `tests/unit/test_dialogs_flow.py` | 55 | 55 | 0 | — |
| 150 | `tests/controllers/product/test_fabricacion_manager.py` | 55 | 55 | 0 | — |
| 151 | `tests/integration/test_label_counter_integration.py` | 55 | 55 | 0 | — |
| 152 | `tests/controllers/worker/test_management_manager.py` | 55 | 55 | 0 | — |
| 153 | `tests/unit/test_security_improvements.py` | 55 | 55 | 0 | — |
| 154 | `tests/controllers/worker/test_task_manager.py` | 55 | 55 | 0 | — |
| 155 | `tests/unit/test_workers_widget.py` | 55 | 55 | 0 | — |
| 156 | `tests/unit/test_fabricacion_controller_comprehensive.py` | 56 | 56 | 0 | — |
| 157 | `tests/unit/test_preproceso_repository.py` | 56 | 56 | 0 | — |
| 158 | `tests/unit/test_tracking_exceptions.py` | 56 | 56 | 0 | — |
| 159 | `tests/unit/test_visual_effects.py` | 60 | 60 | 0 | — |
| 160 | `tests/unit/test_machine_service.py` | 61 | 61 | 0 | — |
| 161 | `tests/unit/test_simulation_controller_comprehensive.py` | 61 | 61 | 0 | Sí |
| 162 | `tests/unit/test_backup_controller.py` | 62 | 62 | 0 | — |
| 163 | `tests/unit/test_backup_integration.py` | 62 | 62 | 0 | — |
| 164 | `tests/repositories/test_material_repository.py` | 62 | 62 | 0 | — |
| 165 | `tests/unit/test_password_service.py` | 62 | 62 | 0 | — |
| 166 | `tests/unit/test_preproceso_controller_comprehensive.py` | 62 | 62 | 0 | — |
| 167 | `tests/unit/test_iteration_repository.py` | 65 | 65 | 0 | — |
| 168 | `tests/unit/test_products_widget.py` | 65 | 65 | 0 | — |
| 169 | `tests/unit/test_worker_repository.py` | 65 | 65 | 0 | — |
| 170 | `tests/unit/test_backup_service.py` | 69 | 69 | 0 | — |
| 171 | `tests/integration/test_app_startup_integration.py` | 70 | 70 | 0 | — |
| 172 | `tests/controllers/worker/test_auth_manager.py` | 70 | 70 | 0 | — |
| 173 | `tests/controllers/product/test_material_manager.py` | 70 | 70 | 0 | — |
| 174 | `tests/controllers/product/test_preproceso_manager.py` | 70 | 70 | 0 | — |
| 175 | `tests/unit/test_qapp_crash.py` | 75 | 75 | 0 | — |
| 176 | `tests/unit/test_session_controller_comprehensive.py` | 77 | 77 | 0 | Sí |
| 177 | `tests/unit/ui/test_backup_restore_dialog.py` | 80 | 80 | 0 | — |
| 178 | `tests/unit/test_preparation_service.py` | 80 | 80 | 0 | — |
| 179 | `tests/unit/test_tracking_assignment_service.py` | 82 | 82 | 0 | — |
| 180 | `tests/unit/test_calculate_times_widget.py` | 85 | 85 | 0 | — |
| 181 | `tests/unit/test_camera_manager_full.py` | 85 | 85 | 0 | — |
| 182 | `tests/unit/test_charts_container.py` | 85 | 85 | 0 | — |
| 183 | `tests/test_cycle_reproduction.py` | 85 | 85 | 0 | — |
| 184 | `tests/unit/test_features_worker_controller.py` | 85 | 85 | 0 | Sí |
| 185 | `tests/e2e/test_iteration_workflow.py` | 85 | 85 | 0 | — |
| 186 | `tests/unit/test_settings_widget.py` | 85 | 85 | 0 | Sí |
| 187 | `tests/unit/test_pila_controller_comprehensive.py` | 100 | 100 | 0 | — |
| 188 | `tests/unit/test_product_controller_v2_comprehensive.py` | 100 | 100 | 0 | — |

---

**Resumen:** 188 archivos. 6 con Nivel Fase B. Orden de trabajo: del #1 al #188. Los que tienen Gap = 0 pero Nivel Fase B = — pueden requerir solo revisión de checklist (sin subir score) para considerarse “listos”.
