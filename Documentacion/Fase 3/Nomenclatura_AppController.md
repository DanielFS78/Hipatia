# Nomenclatura AppController

> Generado automáticamente el 2025-12-27 (Actualizado)

## Resumen

| Métrica | Valor |
|---------|-------|
| Total de líneas | ~5030 |
| Clases | 1 |
| Métodos totales | ~149 |

## Clase: `AppController`

### Métodos Públicos y Privados Detectados

| Método | Línea Aprox. |
|--------|--------------|
| `__init__` | 278 |
| `handle_login` | 389 |
| `_launch_worker_interface` | 417 |
| `_update_ui_for_role` | 497 |
| `connect_signals` | 518 |
| `_connect_preprocesos_signals` | 550 |
| `_update_simulation_progress` | 578 |
| `handle_save_flow_only` | 584 |
| `_load_preprocesos_data` | 626 |
| `get_all_preprocesos_with_components` | 650 |
| `_on_add_new_iteration_clicked` | 661 |
| `handle_attach_file` | 691 |
| `handle_view_file` | 712 |
| `_connect_navigation_signals` | 727 |
| `_on_import_task_data` | 761 |
| `_on_add_holiday` | 824 |
| `_on_remove_holiday` | 841 |
| `_initialize_qr_scanner` | 857 |
| `_on_detect_cameras` | 960 |
| `_load_hardware_settings` | 1012 |
| `_on_save_hardware_settings` | 1027 |
| `_on_test_camera` | 1120 |
| `_on_change_worker_password_clicked` | 1222 |
| `_on_change_own_password_clicked` | 1252 |
| `_connect_products_signals` | 1283 |
| `_connect_fabrications_signals` | 1297 |
| `_connect_add_product_signals` | 1309 |
| `_connect_calculate_signals` | 1317 |
| `_on_calc_lote_search_changed` | 1393 |
| `_on_add_lote_to_pila_clicked` | 1404 |
| `_on_remove_lote_from_pila_clicked` | 1449 |
| `_update_lote_content_table` | 1477 |
| `_clear_canvas_and_reset` | 1515 |
| `_handle_clear_visual_editor` | 1549 |
| `_on_go_home_and_reset_calc` | 1566 |
| `_on_export_audit_log` | 1576 |
| `_map_task_keys` | 1605 |
| `_handle_save_pila_from_visual_editor` | 1693 |
| `_handle_load_pila_into_visual_editor` | 1746 |
| `_on_define_flow_clicked` | 1789 |
| `_on_run_manual_plan_clicked` | 1854 |
| `_on_clear_simulation` | 1927 |
| `_on_optimize_by_deadline_clicked` | 1946 |
| `_handle_run_manual_from_visual_editor` | 2007 |
| `_handle_run_optimizer_from_visual_editor` | 2103 |
| `_on_optimization_finished` | 2185 |
| `_save_chunk_results` | 2219 |
| `_consolidate_chunk_results` | 2253 |
| `_connect_historial_signals` | 2298 |
| `_connect_definir_lote_signals` | 2309 |
| `_on_lote_def_product_search_changed` | 2329 |
| `_on_lote_def_fab_search_changed` | 2343 |
| `_on_add_product_to_lote_template` | 2356 |
| `_on_add_fab_to_lote_template` | 2368 |
| `_on_remove_item_from_lote_template` | 2380 |
| `_on_save_lote_template_clicked` | 2400 |
| `_connect_lotes_management_signals` | 2428 |
| `update_lotes_view` | 2442 |
| `_on_lote_management_result_selected` | 2460 |
| `_on_update_lote_template_clicked` | 2472 |
| `_on_delete_lote_template_clicked` | 2494 |
| `_on_manage_procesos_for_new_product` | 2503 |
| `handle_update_product_iteration` | 2511 |
| `_on_report_result_selected` | 2518 |
| `_connect_reportes_signals` | 2542 |
| `_connect_workers_signals` | 2549 |
| `_connect_machines_signals` | 2565 |
| `_on_calc_product_result_selected` | 2577 |
| `_on_context_help_clicked` | 2585 |
| `_on_save_product_clicked` | 2597 |
| `_on_delete_machine_clicked` | 2631 |
| `_on_manage_subs_for_new_product` | 2640 |
| `update_historial_view` | 2648 |
| `_populate_historial_list` | 2674 |
| `_update_historial_calendar_highlights` | 2729 |
| `_on_historial_item_selected` | 2759 |
| `_on_historial_calendar_clicked` | 2833 |
| `_on_print_historial_report_clicked` | 2857 |
| `_update_historial_activity_chart` | 2897 |
| `_on_product_search_changed` | 2943 |
| `_on_product_result_selected` | 2949 |
| `show_create_fabricacion_dialog` | 2976 |
| `_on_update_fabricacion` | 3011 |
| `_on_delete_fabricacion` | 3042 |
| `_on_fabrication_search_in_gestion_changed` | 3062 |
| `_on_fabrication_result_selected` | 3068 |
| `_connect_fabrications_signals` | 3090 |
| `_on_edit_fabricacion_preprocesos_clicked` | 3103 |
| `_reparse_simulation_results_dates` | 3151 |
| `_on_load_pila_clicked` | 3169 |
| `_on_update_product` | 3245 |
| `_on_delete_product` | 3309 |
| `_on_manage_subs_clicked` | 3317 |
| `_on_manage_procesos_clicked` | 3339 |
| `_on_manage_details_clicked` | 3360 |
| `_start_simulation_thread` | 3365 |
| `_on_simulation_finished` | 3399 |
| `get_preprocesos_for_fabricacion` | 3443 |
| `_on_save_pila_clicked` | 3468 |
| `_on_ver_bitacora_pila_clicked` | 3527 |
| `_add_task_to_products` | 3542 |
| `_open_editor_with_loaded_flow` | 3568 |
| `_on_export_to_excel_clicked` | 3652 |
| `_on_export_gantt_to_pdf_clicked` | 3722 |
| `_on_import_databases` | 3755 |
| `_on_export_databases` | 3808 |
| `_on_sync_databases_clicked` | 3830 |
| `_create_backup_directory_structure` | 3854 |
| `create_automatic_backup` | 3895 |
| `_backup_and_clean_log` | 3933 |
| `_on_add_break_clicked` | 3958 |
| `_on_remove_break_clicked` | 3969 |
| `_on_edit_break_clicked` | 3996 |
| `_on_save_schedule_settings` | 4039 |
| `_on_add_break` | 4068 |
| `_load_schedule_settings` | 4102 |
| `_on_manage_prep_groups_clicked` | 4127 |
| `handle_image_attachment` | 4131 |
| `handle_delete_product_iteration` | 4152 |
| `handle_add_product_iteration` | 4158 |
| `handle_import_materials_to_product` | 4197 |
| `_on_save_worker_clicked` | 4241 |
| `_on_delete_worker_clicked` | 4329 |
| `_on_worker_product_search_changed` | 4336 |
| `_on_assign_task_to_worker_clicked` | 4352 |
| `_on_cancel_task_clicked` | 4398 |
| `update_dashboard_view` | 4457 |
| `update_workers_view` | 4468 |
| `_on_save_machine_clicked` | 4480 |
| `_on_add_maintenance_clicked` | 4507 |
| `update_machines_view` | 4524 |
| `_on_worker_selected_in_list` | 4534 |
| `_on_machine_selected_in_list` | 4555 |
| `_on_report_search_changed` | 4569 |
| `_on_generar_informe_clicked` | 4593 |
| `_on_data_changed` | 4653 |
| `search_fabricaciones` | 4661 |
| `show_fabricacion_preprocesos` | 4670 |
| `_refresh_fabricaciones_list` | 4722 |
| `get_fabricacion_products_for_calculation` | 4735 |
| `show_add_preproceso_dialog` | 4769 |
| `show_edit_preproceso_dialog` | 4786 |
| `delete_preproceso` | 4803 & 4900 |
| `_on_nav_button_clicked` | 4829 |
| `_safe_update_calculate_page` | 4876 |
| `_on_edit_search_type_changed` | 4889 |
| `get_preprocesos_by_fabricacion` | 4928 |
| `add_preprocesos_to_current_pila` | 4960 |
| `_convert_preproceso_to_pila_step` | 4990 |

*Nota: `delete_preproceso` aparece duplicado en las líneas 4803 y 4900. Se recomienda eliminar la redundancia en la refactorización.*
