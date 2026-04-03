---
name: Orden de trabajo — Tests
description: Lista única de archivos de test en orden de trabajo. El siguiente a realizar es el primero con Estado = —. Al completar (corregir + pytest pasa + checklist Fase B), marcar ✅ en esta skill y pasar al siguiente. LEE ESTA SKILL al iniciar una sesión de mejora de tests para saber siempre qué archivo toca.
---

# Orden de trabajo — Archivos de test

> **Regla:** Trabajar **siempre** el **primer ítem con Estado = —**. Al terminar (corregido, tests pasan, Checklist Revisión Fase B cumplido), **cambiar ese — por ✅** en la tabla y pasar al siguiente. Así la lista se mantiene actualizada y en todo momento se sabe cuál es la siguiente a realizar.

---

## Siguiente a realizar

**Es el primer archivo de la tabla que tenga Estado = —.**  
(Al completar un archivo, editar esta skill y poner ✅ en esa fila; el siguiente — pasa a ser "el que toca".)

---

## Listado (# = orden de trabajo | Estado: — pendiente, ✅ hecho)

| # | Ruta | Estado |
|---|------|--------|
| 1 | `tests/unit/test_schedule_controller_comprehensive.py` | ✅ |
| 2 | `tests/unit/test_worker_controller_comprehensive.py` | ✅ |
| 3 | `tests/unit/test_define_flow_dialog_edge.py` | ✅ |
| 4 | `tests/unit/test_label_manager.py` | ✅ |
| 5 | `tests/unit/test_lote_controller_comprehensive.py` | ✅ |
| 6 | `tests/unit/test_lote_manager_isolated.py` | ✅ |
| 7 | `tests/unit/test_pila_manager_isolated.py` | ✅ |
| 8 | `tests/unit/test_navigation_controller_comprehensive.py` | ✅ |
| 9 | `tests/unit/test_product_controller_preprocesos.py` | ✅ |
| 10 | `tests/unit/test_historial_controller_comprehensive.py` | ✅ |
| 11 | `tests/unit/test_machine_controller_comprehensive.py` | ✅ |
| 12 | `tests/unit/test_product_dialogs_coverage.py` | ✅ |
| 13 | `tests/unit/test_ui_controller_comprehensive.py` | ✅ |
| 14 | `tests/unit/test_worker_main_window.py` | ✅ |
| 15 | `tests/unit/test_camera_config_dialog.py` | ✅ |
| 16 | `tests/unit/test_calculation_controller_comprehensive.py` | ✅ |
| 17 | `tests/unit/test_main_window.py` | ✅ |
| 18 | `tests/unit/test_enhanced_flow_dialog.py` | ✅ |
| 19 | `tests/unit/test_report_controller_comprehensive.py` | ✅ |
| 20 | `tests/controllers/product/test_product_manager.py` | ✅ |
| 21 | `tests/unit/test_create_fabricacion_dialog.py` | ✅ |
| 22 | `tests/unit/test_fabrication_dialogs.py` | ✅ |
| 23 | `tests/unit/test_file_controller.py` | ✅ |
| 24 | `tests/unit/test_canvas_widgets_coverage.py` | ✅ |
| 25 | `tests/e2e/test_backup_audit_e2e.py` | ✅ |
| 26 | `tests/unit/test_bitacora_dialog.py` | ✅ |
| 27 | `tests/unit/test_create_dialog.py` | ✅ |
| 28 | `tests/unit/test_flow_builder_service.py` | ✅ |
| 29 | `tests/unit/test_machines_widget.py` | ✅ |
| 30 | `tests/unit/test_simulation_events_comprehensive.py` | ✅ |
| 31 | `tests/unit/test_timeline_widget.py` | ✅ |
| 32 | `tests/unit/test_ui_scaler.py` | ✅ |
| 33 | `tests/unit/test_worker_validation_service.py` | ✅ |
| 34 | `tests/unit/test_report_strategy_comprehensive.py` | ✅ |
| 35 | `tests/unit/test_qr_scanner.py` | ✅ |
| 36 | `tests/unit/test_security_phase2_integration.py` | ✅ |
| 37 | `tests/unit/test_startup_controller.py` | ✅ |
| 38 | `tests/unit/test_audit_report_generator.py` | ✅ |
| 39 | `tests/unit/test_scheduler_logic.py` | ✅ |
| 40 | `tests/integration/test_widgets_integration.py` | ✅ |
| 41 | `tests/unit/test_canvas_widgets.py` | ✅ |
| 42 | `tests/unit/test_lotes_widget.py` | ✅ |
| 43 | `tests/unit/test_camera_manager_no_cv2.py` | ✅ |
| 44 | `tests/unit/test_database_config.py` | ✅ |
| 45 | `tests/unit/test_flow_simulation_service.py` | ✅ |
| 46 | `tests/setup/test_label_counter_setup.py` | ✅ |
| 47 | `tests/unit/test_report_sheets.py` | ✅ |
| 48 | `tests/unit/test_security_validation.py` | ✅ |
| 49 | `tests/unit/test_smart_search.py` | ✅ |
| 50 | `tests/unit/test_sync_service.py` | ✅ |
| 51 | `tests/unit/test_tracking_dialogs.py` | ✅ |
| 52 | `tests/unit/test_utility_dialogs_coverage.py` | ✅ |
| 53 | `tests/unit/test_worker_db_sync.py` | ✅ |
| 54 | `tests/unit/test_app_model.py` | ✅ |
| 55 | `tests/unit/test_historial_widget.py` | ✅ |
| 56 | `tests/integration/test_dialogs_integration.py` | ✅ |
| 57 | `tests/unit/test_fabrications_widget.py` | ✅ |
| 58 | `tests/unit/test_home_widget.py` | ✅ |
| 59 | `tests/e2e/test_main_window_flows.py` | ✅ |
| 60 | `tests/unit/test_reportes_widget.py` | ✅ |
| 61 | `tests/unit/test_preprocesos_widget.py` | ✅ |
| 62 | `tests/unit/test_product_service.py` | ✅ |
| 63 | `tests/integration/test_pila_integration.py` | ✅ |
| 64 | `tests/integration/test_app_model_integration.py` | ✅ |
| 65 | `tests/integration/test_app_model_services_setup.py` | ✅ |
| 66 | `tests/unit/test_code_quality_config.py` | ✅ |
| 67 | `tests/unit/test_fabrication_module_structure.py` | ✅ |
| 68 | `tests/setup/test_pila_setup.py` | ✅ |
| 69 | `tests/pre_migration/test_tracking_repository_setup.py` | ✅ |
| 70 | `tests/unit/test_flow_canvas.py` | ✅ |
| 71 | `tests/unit/test_tracking_repository_stats_export.py` | ✅ |
| 72 | `tests/unit/test_charts_widget.py` | ✅ |
| 73 | `tests/unit/test_define_flow_presenter.py` | ✅ |
| 74 | `tests/unit/test_event_engine_comprehensive.py` | ✅ |
| 75 | `tests/unit/test_hardware_controller.py` | ✅ |
| 76 | `tests/integration/test_iteration_integration.py` | ✅ |
| 77 | `tests/unit/test_lote_repository.py` | ✅ |
| 78 | `tests/unit/test_machine_controller.py` | ✅ |
| 79 | `tests/unit/test_machine_repository.py` | ✅ |
| 80 | `tests/unit/test_order_list_widget.py` | ✅ |
| 81 | `tests/unit/test_reports_infrastructure.py` | ✅ |
| 82 | `tests/integration/test_reports_ui_integration.py` | ✅ |
| 83 | `tests/pre_migration/test_tracking_repository_unit.py` | ✅ |
| 84 | `tests/db/test_product_repository.py` | ✅ |
| 85 | `tests/unit/test_detect_dead_code.py` | ✅ |
| 86 | `tests/unit/test_fabrication_dialogs_coverage.py` | ✅ |
| 87 | `tests/unit/test_order_list.py` | ✅ |
| 88 | `tests/unit/test_ui_signals_controller_comprehensive.py` | ✅ |
| 89 | `tests/integration/test_configuration_integration.py` | ✅ |
| 90 | `tests/unit/test_enhanced_flow_presenter.py` | ✅ |
| 91 | `tests/unit/test_tracking_repository_coverage_fix.py` | ✅ |
| 92 | `tests/unit/test_tracking_repository_full.py` | ✅ |
| 93 | `tests/unit/test_camera_manager_main.py` | ✅ |
| 94 | `tests/unit/test_common_production_dialogs.py` | ✅ |
| 95 | `tests/unit/test_create_presenter.py` | ✅ |
| 96 | `tests/unit/test_gestion_datos_widget.py` | ✅ |
| 97 | `tests/unit/test_inspector_presenter.py` | ✅ |
| 98 | `tests/unit/test_macos_fix.py` | ✅ |
| 99 | `tests/utils/test_macos_setup.py` | ✅ |
| 100 | `tests/unit/test_pila_repository.py` | ✅ |
| 101 | `tests/integration/test_reports_integration.py` | ✅ |
| 102 | `tests/unit/test_reports_repository.py` | ✅ |
| 103 | `tests/unit/test_reports_widgets.py` | ✅ |
| 104 | `tests/unit/test_widgets_coverage.py` | ✅ |
| 105 | `tests/unit/test_define_flow_dialog.py` | ✅ |
| 106 | `tests/unit/test_app_coverage.py` | ✅ |
| 107 | `tests/unit/test_controller_interface.py` | ✅ |
| 108 | `tests/unit/test_dialog_integration_smoke.py` | ✅ |
| 109 | `tests/unit/test_inspector_panel.py` | ✅ |
| 110 | `tests/unit/test_library_panel.py` | ✅ |
| 111 | `tests/unit/test_prep_steps_widget.py` | ✅ |
| 112 | `tests/unit/test_configuration_repository.py` | ✅ |
| 113 | `tests/unit/test_database_manager_full.py` | ✅ |
| 114 | `tests/setup/test_iteration_setup.py` | ✅ |
| 115 | `tests/e2e/test_machine_workflow.py` | ✅ |
| 116 | `tests/e2e/test_product_workflow.py` | ✅ |
| 117 | `tests/unit/test_dialogs.py` | ✅ |
| 118 | `tests/unit/test_maintenance_service.py` | ✅ |
| 119 | `tests/unit/test_widgets_dashboard.py` | ✅ |
| 120 | `tests/unit/test_worker_service.py` | ✅ |
| 121 | `tests/reporting/test_audit_infra.py` | ✅ |
| 122 | `tests/unit/test_backup_controller_comprehensive.py` | ✅ |
| 123 | `tests/unit/test_common_dialogs.py` | ✅ |
| 124 | `tests/unit/test_connection_dialog_comprehensive.py` | ✅ |
| 125 | `tests/setup/test_dialogs_setup.py` | ✅ |
| 126 | `tests/unit/test_help_widget.py` | ✅ |
| 127 | `tests/e2e/test_label_counter_e2e.py` | ✅ |
| 128 | `tests/unit/test_label_counter_repository.py` | ✅ |
| 129 | `tests/integration/test_machine_integration.py` | ✅ |
| 130 | `tests/setup/test_machine_setup.py` | ✅ |
| 131 | `tests/data/test_package_compliance.py` | ✅ |
| 132 | `tests/e2e/test_pila_workflow.py` | ✅ |
| 133 | `tests/integration/test_preproceso_integration.py` | ✅ |
| 134 | `tests/setup/test_preproceso_setup.py` | ✅ |
| 135 | `tests/e2e/test_preproceso_workflow.py` | ✅ |
| 136 | `tests/integration/test_product_integration.py` | ✅ |
| 137 | `tests/setup/test_product_setup.py` | ✅ |
| 138 | `tests/setup/test_widgets_setup.py` | ✅ |
| 139 | `tests/integration/test_worker_integration.py` | ✅ |
| 140 | `tests/setup/test_worker_setup.py` | ✅ |
| 141 | `tests/e2e/test_worker_workflow.py` | ✅ |
| 142 | `tests/unit/test_product_repository.py` | ✅ |
| 143 | `tests/e2e/test_security_workflow.py` | ✅ |
| 144 | `tests/unit/test_prep_dialogs_coverage.py` | ✅ |
| 145 | `tests/unit/test_app_model_coverage.py` | ✅ |
| 146 | `tests/e2e/test_app_services_e2e_setup.py` | ✅ |
| 147 | `tests/unit/test_dashboard_widget.py` | ✅ |
| 148 | `tests/e2e/test_dialogs_e2e.py` | ✅ |
| 149 | `tests/unit/test_dialogs_flow.py` | ✅ |
| 150 | `tests/controllers/product/test_fabricacion_manager.py` | ✅ |
| 151 | `tests/integration/test_label_counter_integration.py` | ✅ |
| 152 | `tests/controllers/worker/test_management_manager.py` | ✅ |
| 153 | `tests/unit/test_security_improvements.py` | ✅ |
| 154 | `tests/controllers/worker/test_task_manager.py` | ✅ |
| 155 | `tests/unit/test_workers_widget.py` | ✅ |
| 156 | `tests/unit/test_fabricacion_controller_comprehensive.py` | ✅ |
| 157 | `tests/unit/test_preproceso_repository.py` | ✅ |
| 158 | `tests/unit/test_tracking_exceptions.py` | ✅ |
| 159 | `tests/unit/test_visual_effects.py` | ✅ |
| 160 | `tests/unit/test_machine_service.py` | ✅ |
| 161 | `tests/unit/test_simulation_controller_comprehensive.py` | ✅ |
| 162 | `tests/unit/test_backup_controller.py` | ✅ |
| 163 | `tests/unit/test_backup_integration.py` | ✅ |
| 164 | `tests/repositories/test_material_repository.py` | ✅ |
| 165 | `tests/unit/test_password_service.py` | ✅ |
| 166 | `tests/unit/test_preproceso_controller_comprehensive.py` | ✅ |
| 167 | `tests/unit/test_iteration_repository.py` | ✅ |
| 168 | `tests/unit/test_products_widget.py` | ✅ |
| 169 | `tests/unit/test_worker_repository.py` | ✅ |
| 170 | `tests/unit/test_backup_service.py` | ✅ |
| 171 | `tests/integration/test_app_startup_integration.py` | ✅ |
| 172 | `tests/controllers/worker/test_auth_manager.py` | ✅ |
| 173 | `tests/controllers/product/test_material_manager.py` | ✅ |
| 174 | `tests/controllers/product/test_preproceso_manager.py` | ✅ |
| 175 | `tests/unit/test_qapp_crash.py` | ✅ |
| 176 | `tests/unit/test_session_controller_comprehensive.py` | ✅ |
| 177 | `tests/unit/ui/test_backup_restore_dialog.py` | ✅ |
| 178 | `tests/unit/test_preparation_service.py` | ✅ |
| 179 | `tests/unit/test_tracking_assignment_service.py` | ✅ |
| 180 | `tests/unit/test_calculate_times_widget.py` | ✅ |
| 181 | `tests/unit/test_camera_manager_full.py` | ✅ |
| 182 | `tests/unit/test_charts_container.py` | ✅ |
| 183 | `tests/test_cycle_reproduction.py` | ✅ |
| 184 | `tests/unit/test_features_worker_controller.py` | ✅ |
| 185 | `tests/e2e/test_iteration_workflow.py` | ✅ |
| 186 | `tests/unit/test_settings_widget.py` | ✅ |
| 187 | `tests/unit/test_pila_controller_comprehensive.py` | ✅ |
| 188 | `tests/unit/test_product_controller_v2_comprehensive.py` | ✅ |

---

## Resumen

- **Total:** 188 archivos.
- **Hechos (✅):** 188/188 — lista completa optimizada.
- **Siguiente a realizar:** Ninguno (todos los ítems están en ✅).
- **Al completar un archivo:** 1) Verificar que los tests pasan (`pytest <ruta> -x -q`). 2) Verificar Checklist Revisión Fase B (backlog). 3) En esta skill, cambiar — por ✅ en esa fila. 4) Pasar al siguiente — de la lista.

---

## Estado de cierre

**2026-03-17:** Lista cerrada. Esta skill se mantiene como **histórico/auditoría** del trabajo realizado en la fase de tests.
