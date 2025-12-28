# Fase 3.7: Análisis Completo de `ui/dialogs.py`

> **Fecha de generación:** 27 de December de 2025, 16:21
> **Archivo analizado:** `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/ui/dialogs.py`
> **Generado por:** `scripts/analyze_dialogs.py`

---

## 1. Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Líneas totales** | 7,947 |
| **Clases definidas** | 36 |
| **Métodos totales** | 239 |
| **Señales PyQt** | 4 |
| **Bytes** | 363,669 |

### 1.1 Clasificación por Tipo

| Categoría | Cantidad | Clases |
|-----------|----------|--------|
| Diálogos (QDialog) | 29 | `AddBreakDialog`, `AddIterationDialog`, `AddProcesoMecanicoDialog` (+26 más) |
| Otros | 1 | `CardWidget` |
| Widgets (QWidget) | 6 | `CanvasWidget`, `GoldenGlowEffect`, `GreenCycleEffect` (+3 más) |

### 1.2 Top 10 Clases por Tamaño

| Clase | Líneas | Métodos | Complejidad Total |
|-------|--------|---------|-------------------|
| `EnhancedProductionFlowDialog` | 3080 | 54 | 442 |
| `DefineProductionFlowDialog` | 1035 | 21 | 155 |
| `CanvasWidget` | 399 | 15 | 55 |
| `ProductDetailsDialog` | 342 | 19 | 68 |
| `FabricacionBitacoraDialog` | 204 | 7 | 23 |
| `SubfabricacionesDialog` | 180 | 8 | 25 |
| `GoldenGlowEffect` | 179 | 5 | 16 |
| `PrepStepsDialog` | 179 | 6 | 26 |
| `CycleEndConfigDialog` | 176 | 3 | 16 |
| `CreateFabricacionDialog` | 173 | 10 | 27 |

---

## 2. Detalle de Clases

### 2.1 `AddBreakDialog`

- **Líneas:** 1056 - 1079 (23 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo simple para añadir un nuevo descanso.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 15 | 1 |  | 2 deps |
| `get_times` | 6 | 1 |  | 2 deps |

---

### 2.2 `AddIterationDialog`

- **Líneas:** 6620 - 6672 (52 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para añadir una nueva iteración con todos los campos requeridos.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 35 | 1 |  | 5 deps |
| `_attach_plano` | 6 | 2 | ✓ | 2 deps |
| `get_data` | 7 | 1 |  | 3 deps |

---

### 2.3 `AddProcesoMecanicoDialog`

- **Líneas:** 7591 - 7627 (36 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para añadir un nuevo proceso mecánico.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 6 | 1 |  | 4 deps |
| `setup_ui` | 19 | 1 |  | 3 deps |
| `get_proceso_data` | 7 | 1 |  | 4 deps |

---

### 2.4 `AssignPreprocesosDialog`

- **Líneas:** 905 - 1054 (149 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para asignar preprocesos a fabricaciones desde el menú de Preprocesos.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 5 | 1 |  | 2 deps |
| `setup_ui` | 61 | 1 |  | 15 deps |
| `load_fabricaciones` | 22 | 6 |  | 6 deps |
| `on_fabricacion_selected` | 17 | 3 |  | 7 deps |
| `load_current_preprocesos` | 22 | 6 |  | 4 deps |
| `modify_selected_fabricacion` | 13 | 2 |  | 4 deps |

---

### 2.5 `CanvasWidget`

- **Líneas:** 32 - 431 (399 líneas)
- **Herencia:** `QWidget`
- **Descripción:** Un widget personalizado que actúa como un canvas para arrastrar, soltar y visualizar
las tareas del flujo de producción.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 12 | 1 |  | 2 deps |
| `set_connections` | 6 | 1 |  | 1 deps |
| `dragEnterEvent` | 2 | 1 |  | 1 deps |
| `dragMoveEvent` | 2 | 1 |  | 1 deps |
| `dropEvent` | 6 | 1 |  | 4 deps |
| `paintEvent` | 67 | 7 |  | 18 deps |
| `_get_task_index_by_widget` | 6 | 3 | ✓ | 1 deps |
| `_draw_cyclic_arrow_with_glow` | 69 | 7 | ✓ | 16 deps |
| `_draw_grid` | 28 | 3 | ✓ | 6 deps |
| `_calculate_smart_path` | 51 | 8 | ✓ | 11 deps |
| `_count_path_collisions` | 18 | 4 | ✓ | 1 deps |
| `_line_intersects_rect` | 34 | 5 | ✓ | 9 deps |
| `_adjust_path_to_avoid_obstacles` | 47 | 9 | ✓ | 8 deps |
| `_draw_arrowhead` | 12 | 1 | ✓ | 10 deps |
| `mousePressEvent` | 16 | 3 |  | 3 deps |

---

### 2.6 `CardWidget`

- **Líneas:** 433 - 525 (92 líneas)
- **Herencia:** `QLabel`
- **Descripción:** Una tarjeta visual y MOVIBLE que representa una tarea en el canvas.
Emite 'clicked' al ser seleccionada y 'moved' al ser movida.
- **Señales:** `clicked`, `moved`

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 28 | 1 |  | 6 deps |
| `mousePressEvent` | 12 | 2 |  | 3 deps |
| `mouseMoveEvent` | 10 | 2 |  | 4 deps |
| `mouseReleaseEvent` | 12 | 2 |  | 3 deps |
| `_snap_to_grid` | 16 | 1 | ✓ | 3 deps |

---

### 2.7 `ChangePasswordDialog`

- **Líneas:** 7446 - 7484 (38 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para cambiar la contraseña de un usuario.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 28 | 2 |  | 7 deps |
| `get_passwords` | 7 | 1 |  | 3 deps |

---

### 2.8 `CreateFabricacionDialog`

- **Líneas:** 613 - 786 (173 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo rediseñado para crear una fabricación asignándole preprocesos.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 8 | 1 |  | 2 deps |
| `setup_ui` | 67 | 1 |  | 16 deps |
| `load_initial_data` | 11 | 3 |  | 3 deps |
| `filter_available_list` | 6 | 2 |  | 5 deps |
| `assign_preproceso` | 13 | 5 |  | 4 deps |
| `unassign_preproceso` | 13 | 5 |  | 4 deps |
| `update_available_list` | 12 | 4 |  | 6 deps |
| `update_assigned_list` | 11 | 2 |  | 4 deps |
| `validate_and_accept` | 12 | 3 |  | 3 deps |
| `get_fabricacion_data` | 7 | 1 |  | 3 deps |

---

### 2.9 `CycleEndConfigDialog`

- **Líneas:** 2589 - 2765 (176 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para configurar el fin de ciclo de una tarea.
Permite seleccionar a qué tarea de inicio de ciclo regresar.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 20 | 2 |  | 5 deps |
| `_setup_ui` | 132 | 12 | ✓ | 25 deps |
| `get_configuration` | 18 | 2 |  | 2 deps |

---

### 2.10 `DefineProductionFlowDialog`

- **Líneas:** 1081 - 2116 (1035 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para definir la secuencia de tareas, dependencias y trabajadores.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 50 | 2 |  | 13 deps |
| `_populate_from_flow` | 12 | 1 | ✓ | 5 deps |
| `_create_add_and_edit_panel` | 135 | 4 | ✓ | 37 deps |
| `_on_save_flow` | 19 | 4 | ✓ | 5 deps |
| `_prepare_task_data` | 54 | 12 | ✓ | 6 deps |
| `_is_task_auto_triggered` | 63 | 9 | ✓ | 5 deps |
| `_create_right_panel` | 29 | 1 | ✓ | 9 deps |
| `_on_machine_selected` | 50 | 11 | ✓ | 16 deps |
| `_on_worker_selected` | 18 | 4 | ✓ | 4 deps |
| `_on_prep_step_selected` | 18 | 2 | ✓ | 4 deps |
| `_on_task_selected` | 59 | 11 | ✓ | 14 deps |
| `_add_or_update_step` | 89 | 19 | ✓ | 22 deps |
| `_update_flow_display` | 127 | 18 | ✓ | 24 deps |
| `_group_selected_steps` | 130 | 24 | ✓ | 13 deps |
| `_assign_worker_to_group` | 21 | 3 | ✓ | 6 deps |
| `_reset_form` | 22 | 2 | ✓ | 13 deps |
| `_edit_step` | 38 | 8 | ✓ | 19 deps |
| `_toggle_start_condition` | 23 | 4 | ✓ | 10 deps |
| `_update_previous_task_menu` | 29 | 8 | ✓ | 5 deps |
| `_delete_step` | 23 | 7 | ✓ | 6 deps |
| `get_production_flow` | 2 | 1 |  | - |

---

### 2.11 `DefinirCantidadesDialog`

- **Líneas:** 7847 - 7908 (61 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para que el usuario defina la cantidad a producir para cada
tarea o grupo de tareas en el flujo de producción.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 8 | 1 |  | 3 deps |
| `setup_ui` | 37 | 4 |  | 14 deps |
| `get_cantidades` | 9 | 2 |  | 1 deps |

---

### 2.12 `EnhancedProductionFlowDialog`

- **Líneas:** 2882 - 5962 (3080 líneas)
- **Herencia:** `QDialog`
- **Señales:** `simulation_processing_task`, `simulation_finished`

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 119 | 2 |  | 26 deps |
| `_show_inspector_panel` | 29 | 8 | ✓ | 8 deps |
| `_hide_inspector_panel` | 33 | 8 | ✓ | 9 deps |
| `_prepare_task_data` | 83 | 13 | ✓ | 6 deps |
| `_highlight_processing_task` | 4 | 1 | ✓ | 1 deps |
| `_clear_all_simulation_effects` | 4 | 1 | ✓ | 1 deps |
| `_create_library_panel` | 53 | 5 | ✓ | 12 deps |
| `_toggle_library_panel` | 14 | 2 | ✓ | 4 deps |
| `_update_task_tree_visual_states` | 55 | 13 | ✓ | 10 deps |
| `_create_canvas_panel` | 34 | 1 | ✓ | 9 deps |
| `_create_inspector_panel` | 62 | 1 | ✓ | 14 deps |
| `_create_inspector_widgets` | 266 | 3 | ✓ | 27 deps |
| `_handle_delete_selected_task` | 57 | 8 | ✓ | 9 deps |
| `_load_flow_onto_canvas` | 161 | 26 | ✓ | 20 deps |
| `_add_task_to_canvas` | 129 | 13 | ✓ | 29 deps |
| `_clear_canvas_and_reset` | 33 | 5 | ✓ | 9 deps |
| `_on_card_selected` | 142 | 39 | ✓ | 24 deps |
| `_on_sidebar_task_clicked` | 34 | 7 | ✓ | 5 deps |
| `_highlight_dependencies_in_tree` | 40 | 10 | ✓ | 12 deps |
| `_is_task_auto_triggered` | 49 | 8 | ✓ | 5 deps |
| `_populate_inspector_panel` | 407 | 68 | ✓ | 63 deps |
| `_update_canvas_size` | 76 | 12 | ✓ | 10 deps |
| `_on_card_moved` | 4 | 1 | ✓ | 2 deps |
| `_update_canvas_connections` | 41 | 7 | ✓ | 6 deps |
| `_update_task_config` | 148 | 25 | ✓ | 10 deps |
| `_apply_cycle_start_effect` | 34 | 4 | ✓ | 8 deps |
| `_remove_cycle_start_effect` | 17 | 3 | ✓ | 4 deps |
| `_update_all_cycle_start_effects` | 38 | 5 | ✓ | 9 deps |
| `_toggle_start_condition_widgets` | 21 | 2 | ✓ | 1 deps |
| `_handle_assign_worker` | 16 | 3 | ✓ | 2 deps |
| `_handle_unassign_worker` | 15 | 4 | ✓ | 2 deps |
| `_open_cycle_end_dialog` | 86 | 12 | ✓ | 9 deps |
| `_handle_configure_reassignment` | 34 | 6 | ✓ | 4 deps |
| `get_production_flow` | 87 | 16 |  | 12 deps |
| `_position_preview_button` | 19 | 2 | ✓ | 7 deps |
| `_on_dialog_resized` | 9 | 3 | ✓ | 2 deps |
| `_preview_execution_order` | 56 | 4 | ✓ | 20 deps |
| `_calculate_preview_order` | 89 | 22 | ✓ | 17 deps |
| `_traverse_from_task` | 47 | 9 | ✓ | 7 deps |
| `_show_next_preview_step` | 43 | 8 | ✓ | 6 deps |
| `_end_preview` | 34 | 5 | ✓ | 10 deps |
| `_create_simulation_message_label` | 17 | 1 | ✓ | 4 deps |
| `_show_simulation_message` | 38 | 3 | ✓ | 8 deps |
| `_hide_simulation_message` | 4 | 2 | ✓ | 1 deps |
| `_highlight_processing_task` | 43 | 5 | ✓ | 8 deps |
| `_clear_all_simulation_effects` | 24 | 4 | ✓ | 9 deps |
| `_apply_green_cycle_effect` | 27 | 4 | ✓ | 6 deps |
| `_remove_green_cycle_effect` | 13 | 3 | ✓ | 4 deps |
| `_apply_mixed_effect` | 26 | 4 | ✓ | 6 deps |
| `_remove_mixed_effect` | 13 | 3 | ✓ | 4 deps |
| `_update_all_cycle_effects` | 39 | 6 | ✓ | 7 deps |
| `_identify_last_tasks_in_cycles` | 40 | 10 | ✓ | 6 deps |
| `_is_task_in_cycle_chain` | 3 | 1 | ✓ | - |
| `_is_task_in_cycle_chain` | 3 | 1 | ✓ | - |

---

### 2.13 `FabricacionBitacoraDialog`

- **Líneas:** 7018 - 7222 (204 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para gestionar el diario de bitácora de una pila de fabricación
con un calendario interactivo.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 64 | 1 |  | 22 deps |
| `_load_and_process_data` | 33 | 5 | ✓ | 7 deps |
| `_highlight_work_days` | 15 | 4 | ✓ | 3 deps |
| `_on_calendar_date_selected` | 28 | 3 | ✓ | 14 deps |
| `_update_history_table` | 10 | 2 | ✓ | 4 deps |
| `_get_planned_work_for_day` | 16 | 5 | ✓ | 1 deps |
| `_add_diario_entry` | 25 | 3 | ✓ | 4 deps |

---

### 2.14 `GetLoteInstanceParametersDialog`

- **Líneas:** 7739 - 7784 (45 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para solicitar los parámetros de una instancia de Lote al añadirla a la Pila.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 33 | 1 |  | 10 deps |
| `get_data` | 7 | 1 |  | 3 deps |

---

### 2.15 `GetOptimizationParametersDialog`

- **Líneas:** 7786 - 7820 (34 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para solicitar fecha de inicio, fecha de fin y unidades para la optimización.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 24 | 1 |  | 10 deps |
| `get_parameters` | 6 | 1 |  | 3 deps |

---

### 2.16 `GetUnitsDialog`

- **Líneas:** 7822 - 7845 (23 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo simple para solicitar el número de unidades a producir.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 18 | 1 |  | 6 deps |
| `get_units` | 2 | 1 |  | 1 deps |

---

### 2.17 `GoldenGlowEffect`

- **Líneas:** 2118 - 2297 (179 líneas)
- **Herencia:** `QWidget`
- **Descripción:** Widget que dibuja un círculo dorado giratorio alrededor de una tarjeta
para indicar que es una tarea de inicio de ciclo.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 23 | 2 |  | 7 deps |
| `eventFilter` | 19 | 5 |  | 3 deps |
| `_update_geometry` | 33 | 4 | ✓ | 12 deps |
| `paintEvent` | 86 | 2 |  | 10 deps |
| `stop_animation` | 9 | 3 |  | 3 deps |

---

### 2.18 `GreenCycleEffect`

- **Líneas:** 2384 - 2478 (94 líneas)
- **Herencia:** `QWidget`
- **Descripción:** Widget que dibuja un aro verde con efecto neón para tareas intermedias del ciclo.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 15 | 2 |  | 7 deps |
| `eventFilter` | 11 | 5 |  | 3 deps |
| `_update_geometry` | 21 | 4 | ✓ | 12 deps |
| `paintEvent` | 30 | 2 |  | 7 deps |
| `stop_animation` | 7 | 4 |  | 3 deps |

---

### 2.19 `LoadPilaDialog`

- **Líneas:** 7262 - 7324 (62 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para mostrar y seleccionar pilas guardadas.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 40 | 4 |  | 8 deps |
| `_request_delete` | 9 | 2 | ✓ | 4 deps |
| `get_selected_id` | 10 | 3 |  | 2 deps |

---

### 2.20 `LoginDialog`

- **Líneas:** 7349 - 7372 (23 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para la autenticación de usuarios.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 17 | 1 |  | 4 deps |
| `get_credentials` | 3 | 1 |  | 2 deps |

---

### 2.21 `MixedGoldGreenEffect`

- **Líneas:** 2480 - 2587 (107 líneas)
- **Herencia:** `QWidget`
- **Descripción:** Widget que dibuja un aro con efecto mixto dorado-verde para tareas finales de ciclo.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 14 | 2 |  | 7 deps |
| `eventFilter` | 11 | 5 |  | 3 deps |
| `_update_geometry` | 21 | 4 | ✓ | 12 deps |
| `paintEvent` | 44 | 3 |  | 7 deps |
| `stop_animation` | 7 | 4 |  | 3 deps |

---

### 2.22 `MultiWorkerSelectionDialog`

- **Líneas:** 7910 - 7947 (37 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para seleccionar múltiples trabajadores de una lista.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 31 | 4 |  | 8 deps |
| `get_selected_workers` | 3 | 2 |  | 2 deps |

---

### 2.23 `PrepGroupsDialog`

- **Líneas:** 6458 - 6618 (160 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para gestionar los Grupos de Preparación de una máquina.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 68 | 2 |  | 17 deps |
| `_toggle_form` | 5 | 3 | ✓ | 3 deps |
| `_load_groups` | 12 | 2 | ✓ | 7 deps |
| `_on_group_selected` | 24 | 5 | ✓ | 6 deps |
| `_add_group` | 8 | 1 | ✓ | 6 deps |
| `_save_group` | 15 | 3 | ✓ | 4 deps |
| `_delete_group` | 10 | 3 | ✓ | 2 deps |
| `_manage_steps` | 9 | 2 | ✓ | 2 deps |

---

### 2.24 `PrepStepsDialog`

- **Líneas:** 6277 - 6456 (179 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para gestionar los pasos individuales de un grupo de preparación.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 50 | 1 |  | 15 deps |
| `_load_steps` | 21 | 2 | ✓ | 8 deps |
| `_on_step_selected` | 17 | 2 | ✓ | 9 deps |
| `_clear_form` | 11 | 1 | ✓ | 8 deps |
| `_add_or_update_step` | 60 | 16 | ✓ | 21 deps |
| `_delete_step` | 13 | 4 | ✓ | 3 deps |

---

### 2.25 `PreprocesoDialog`

- **Líneas:** 7629 - 7737 (108 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para crear o editar un Preproceso, permitiendo la asignación
de materiales (componentes).

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 18 | 6 |  | 4 deps |
| `setup_ui` | 61 | 8 |  | 13 deps |
| `get_data` | 23 | 6 |  | 7 deps |

---

### 2.26 `PreprocesosForCalculationDialog`

- **Líneas:** 788 - 899 (111 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para mostrar y seleccionar preprocesos disponibles
para añadir al cálculo de tiempos de una fabricación.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 7 | 1 |  | 1 deps |
| `setup_ui` | 72 | 6 |  | 15 deps |
| `select_all` | 6 | 3 |  | 4 deps |
| `clear_selection` | 3 | 1 |  | 1 deps |
| `get_selected_preprocesos` | 14 | 3 |  | 3 deps |

---

### 2.27 `PreprocesosSelectionDialog`

- **Líneas:** 527 - 611 (84 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para seleccionar qué preprocesos asignar a una fabricación.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 8 | 1 |  | 1 deps |
| `setup_ui` | 64 | 7 |  | 14 deps |
| `get_selected_preprocesos` | 6 | 2 |  | 2 deps |

---

### 2.28 `ProcesosMecanicosDialog`

- **Líneas:** 7486 - 7589 (103 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para gestionar los procesos mecánicos de un producto.
Similar a SubfabricacionesDialog pero sin máquinas.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 9 | 1 |  | 6 deps |
| `setup_ui` | 34 | 1 |  | 6 deps |
| `populate_table` | 17 | 2 |  | 6 deps |
| `add_proceso` | 6 | 2 |  | 4 deps |
| `delete_proceso` | 4 | 2 |  | 1 deps |
| `get_updated_procesos_mecanicos` | 23 | 9 |  | 7 deps |

---

### 2.29 `ProcessingGlowEffect`

- **Líneas:** 2767 - 2880 (113 líneas)
- **Herencia:** `QWidget`
- **Descripción:** Widget que dibuja un círculo naranja pulsante alrededor de una tarjeta
para indicar que está siendo procesada por la simulación.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 22 | 4 |  | 5 deps |
| `_update_geometry` | 14 | 3 | ✓ | 8 deps |
| `_update_pulse` | 14 | 3 | ✓ | 1 deps |
| `paintEvent` | 47 | 2 |  | 12 deps |
| `stop_animation` | 3 | 1 |  | 1 deps |

---

### 2.30 `ProductDetailsDialog`

- **Líneas:** 6674 - 7016 (342 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo rediseñado con pestañas para gestionar Componentes e Iteraciones de un producto.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 21 | 1 |  | 7 deps |
| `load_all_data` | 4 | 1 |  | 2 deps |
| `_create_components_tab` | 30 | 1 | ✓ | 10 deps |
| `load_components` | 11 | 2 |  | 5 deps |
| `_on_add_material` | 8 | 6 | ✓ | 5 deps |
| `_on_edit_material` | 17 | 7 | ✓ | 8 deps |
| `_on_delete_material` | 12 | 4 | ✓ | 6 deps |
| `_on_import_materials_clicked` | 6 | 3 | ✓ | 3 deps |
| `_create_iterations_tab` | 40 | 1 | ✓ | 11 deps |
| `_create_details_panel_widgets` | 42 | 1 | ✓ | 15 deps |
| `_clear_details_panel` | 16 | 4 | ✓ | 10 deps |
| `_show_details_panel` | 9 | 5 | ✓ | 5 deps |
| `load_iterations` | 14 | 3 |  | 5 deps |
| `_on_iteration_selected` | 26 | 4 | ✓ | 14 deps |
| `_on_view_plano_clicked` | 11 | 5 | ✓ | 3 deps |
| `_on_add_new_iteration_clicked` | 17 | 5 | ✓ | 5 deps |
| `_on_edit_iteration_clicked` | 13 | 7 | ✓ | 9 deps |
| `_on_delete_iteration_clicked` | 8 | 4 | ✓ | 4 deps |
| `_on_attach_image_clicked` | 13 | 4 | ✓ | 4 deps |

---

### 2.31 `ReassignmentRuleDialog`

- **Líneas:** 5964 - 6093 (129 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para definir la regla de reasignación de un trabajador para una tarea.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 61 | 1 |  | 12 deps |
| `_populate_fields` | 25 | 7 | ✓ | 8 deps |
| `get_rule` | 37 | 6 |  | 5 deps |

---

### 2.32 `SavePilaDialog`

- **Líneas:** 7326 - 7347 (21 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para pedir nombre y descripción al guardar una pila.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 17 | 1 |  | 3 deps |
| `get_data` | 2 | 1 |  | 2 deps |

---

### 2.33 `SeleccionarHojasExcelDialog`

- **Líneas:** 7224 - 7260 (36 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para que el usuario elija qué hojas incluir en el informe Excel.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 27 | 1 |  | 4 deps |
| `get_opciones` | 7 | 1 |  | 3 deps |

---

### 2.34 `SimulationProgressEffect`

- **Líneas:** 2299 - 2382 (83 líneas)
- **Herencia:** `QWidget`
- **Descripción:** Widget que dibuja un aro azulado grisáceo giratorio con efecto neón
para indicar que una tarjeta está siendo procesada por la simulación.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 23 | 2 |  | 7 deps |
| `eventFilter` | 14 | 5 |  | 3 deps |
| `_update_geometry` | 25 | 4 | ✓ | 12 deps |
| `paintEvent` | 11 | 1 |  | 3 deps |

---

### 2.35 `SubfabricacionesDialog`

- **Líneas:** 6095 - 6275 (180 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para gestionar (CRUD) la lista de sub-fabricaciones de un producto.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 58 | 2 |  | 17 deps |
| `_refresh_table` | 18 | 4 | ✓ | 7 deps |
| `_on_item_selected` | 29 | 4 | ✓ | 11 deps |
| `_add_or_update` | 31 | 7 | ✓ | 8 deps |
| `_delete_selected` | 5 | 2 | ✓ | 3 deps |
| `_clear_form` | 9 | 1 | ✓ | 7 deps |
| `get_updated_subfabricaciones` | 2 | 1 |  | - |
| `accept` | 17 | 4 |  | 3 deps |

---

### 2.36 `SyncDialog`

- **Líneas:** 7374 - 7444 (70 líneas)
- **Herencia:** `QDialog`
- **Descripción:** Diálogo para mostrar diferencias entre dos bases de datos y seleccionar cuáles importar.

#### Métodos

| Método | Líneas | Complejidad | Privado | Dependencias |
|--------|--------|-------------|---------|--------------|
| `__init__` | 18 | 1 |  | 5 deps |
| `_populate_tabs` | 30 | 5 | ✓ | 12 deps |
| `get_selected_changes` | 18 | 5 |  | 6 deps |

---

## 3. Nomenclatura y Patrones Detectados

### 3.1 Prefijos de Métodos

| Prefijo | Cantidad | Ejemplos de uso |
|---------|----------|-----------------|
| `get_*` | 26 | `_get_task_index_by_widget`, `get_selected_preprocesos` |
| `on_*` | 24 | `on_fabricacion_selected`, `_on_save_flow` |
| `update_*` | 17 | `update_available_list`, `update_assigned_list` |
| `load_*` | 10 | `load_initial_data`, `load_fabricaciones` |
| `create_*` | 10 | `_create_add_and_edit_panel`, `_create_right_panel` |
| `setup_*` | 9 | `setup_ui`, `setup_ui` |
| `clear_*` | 7 | `clear_selection`, `_clear_all_simulation_effects` |
| `add_*` | 7 | `_add_or_update_step`, `_add_task_to_canvas` |
| `populate_*` | 5 | `_populate_from_flow`, `_populate_inspector_panel` |
| `delete_*` | 5 | `_delete_step`, `_delete_selected` |
| `is_*` | 4 | `_is_task_auto_triggered`, `_is_task_auto_triggered` |
| `toggle_*` | 4 | `_toggle_start_condition`, `_toggle_library_panel` |
| `stop_*` | 4 | `stop_animation`, `stop_animation` |
| `show_*` | 4 | `_show_inspector_panel`, `_show_next_preview_step` |
| `highlight_*` | 4 | `_highlight_processing_task`, `_highlight_dependencies_in_tree` |

### 3.2 Atributos de Instancia Comunes

| Atributo | Apariciones | Probable Propósito |
|----------|-------------|-------------------|
| `self.controller` | 7 |  |
| `self.parent_card` | 5 |  |
| `self.buttons` | 5 | Botón |
| `self.logger` | 4 |  |
| `self.production_flow` | 4 |  |
| `self.rotation_angle` | 4 |  |
| `self.layout` | 4 | Layout de UI |
| `self.delete_button` | 3 | Botón |
| `self.assigned_material_ids` | 3 |  |
| `self.units_spinbox` | 3 |  |
| `self.parent_dialog` | 2 |  |
| `self.all_preprocesos` | 2 |  |
| `self.checkboxes` | 2 | Checkbox |
| `self.schedule_config` | 2 |  |
| `self.tasks_data` | 2 |  |

---

## 4. Información para Creación de Tests

### 4.1 Clases Prioritarias para Testing

Basado en complejidad y líneas de código:

| Prioridad | Clase | Líneas | Complejidad | Categoría Sugerida |
|-----------|-------|--------|-------------|-------------------|
| 1 | `EnhancedProductionFlowDialog` | 3080 | 442 | Alta |
| 2 | `DefineProductionFlowDialog` | 1035 | 155 | Alta |
| 3 | `ProductDetailsDialog` | 342 | 68 | Alta |
| 4 | `CanvasWidget` | 399 | 55 | Alta |
| 5 | `CreateFabricacionDialog` | 173 | 27 | Media |
| 6 | `PrepStepsDialog` | 179 | 26 | Media |
| 7 | `SubfabricacionesDialog` | 180 | 25 | Media |
| 8 | `FabricacionBitacoraDialog` | 204 | 23 | Media |
| 9 | `PrepGroupsDialog` | 160 | 21 | Media |
| 10 | `PreprocesoDialog` | 108 | 20 | Baja |
| 11 | `AssignPreprocesosDialog` | 149 | 19 | Baja |
| 12 | `MixedGoldGreenEffect` | 107 | 18 | Baja |
| 13 | `GreenCycleEffect` | 94 | 17 | Baja |
| 14 | `ProcesosMecanicosDialog` | 103 | 17 | Baja |
| 15 | `GoldenGlowEffect` | 179 | 16 | Baja |

### 4.2 Dependencias Internas

Clases que llaman a otras clases del mismo módulo:

*No se detectaron dependencias internas significativas.*

---

## 5. Lista Completa de Clases y Métodos

```
class AddBreakDialog(QDialog):
    __init__(self, parent)
    get_times(self)

class AddIterationDialog(QDialog):
    __init__(self, product_code, parent)
    _attach_plano(self)
    get_data(self)

class AddProcesoMecanicoDialog(QDialog):
    __init__(self, parent)
    setup_ui(self)
    get_proceso_data(self)

class AssignPreprocesosDialog(QDialog):
    __init__(self, parent_controller, parent)
    setup_ui(self)
    load_fabricaciones(self)
    on_fabricacion_selected(self)
    load_current_preprocesos(self, fabricacion_id)
    modify_selected_fabricacion(self)

class CanvasWidget(QWidget):
    __init__(self, parent_dialog)
    set_connections(self, new_connections)
    dragEnterEvent(self, event)
    dragMoveEvent(self, event)
    dropEvent(self, event)
    paintEvent(self, event)
    _get_task_index_by_widget(self, widget)
    _draw_cyclic_arrow_with_glow(self, painter, start_point, end_point, start_widget, end_widget, is_from_mother, is_to_mother)
    _draw_grid(self, painter)
    _calculate_smart_path(self, start_point, end_point, start_widget, end_widget)
    _count_path_collisions(self, path, obstacles)
    _line_intersects_rect(self, line, rect)
    _adjust_path_to_avoid_obstacles(self, path, obstacles, grid_size)
    _draw_arrowhead(self, painter, p1, p2, size)
    mousePressEvent(self, event)

class CardWidget(QLabel):
    __init__(self, task_data, parent)
    mousePressEvent(self, event)
    mouseMoveEvent(self, event)
    mouseReleaseEvent(self, event)
    _snap_to_grid(self)

class ChangePasswordDialog(QDialog):
    __init__(self, require_current_password, parent)
    get_passwords(self)

class CreateFabricacionDialog(QDialog):
    __init__(self, all_preprocesos, parent)
    setup_ui(self)
    load_initial_data(self)
    filter_available_list(self)
    assign_preproceso(self)
    unassign_preproceso(self)
    update_available_list(self)
    update_assigned_list(self)
    validate_and_accept(self)
    get_fabricacion_data(self)

class CycleEndConfigDialog(QDialog):
    __init__(self, current_task_index, all_canvas_tasks, parent)
    _setup_ui(self)
    get_configuration(self)

class DefineProductionFlowDialog(QDialog):
    __init__(self, tasks_data, workers, units, controller, schedule_config, parent, existing_flow)
    _populate_from_flow(self, flow_data)
    _create_add_and_edit_panel(self)
    _on_save_flow(self)
    _prepare_task_data(self)
    _is_task_auto_triggered(self, task_index)
    _create_right_panel(self)
    _on_machine_selected(self)
    _on_worker_selected(self, item)
    _on_prep_step_selected(self, item)
    _on_task_selected(self)
    _add_or_update_step(self)
    _update_flow_display(self)
    _group_selected_steps(self)
    _assign_worker_to_group(self, group_index)
    _reset_form(self)
    _edit_step(self, index)
    _toggle_start_condition(self, checked)
    _update_previous_task_menu(self)
    _delete_step(self, index)
    get_production_flow(self)

class DefinirCantidadesDialog(QDialog):
    __init__(self, production_flow, parent)
    setup_ui(self)
    get_cantidades(self)

class EnhancedProductionFlowDialog(QDialog):
    __init__(self, tasks_data, workers, units, controller, schedule_config, parent, existing_flow)
    _show_inspector_panel(self)
    _hide_inspector_panel(self)
    _prepare_task_data(self)
    _highlight_processing_task(self, task_index)
    _clear_all_simulation_effects(self)
    _create_library_panel(self)
    _toggle_library_panel(self)
    _update_task_tree_visual_states(self)
    _create_canvas_panel(self)
    _create_inspector_panel(self)
    _create_inspector_widgets(self)
    _handle_delete_selected_task(self)
    _load_flow_onto_canvas(self, flow_data)
    _add_task_to_canvas(self, task_data, position, skip_confirmation)
    _clear_canvas_and_reset(self)
    _on_card_selected(self, task_data)
    _on_sidebar_task_clicked(self, item, column)
    _highlight_dependencies_in_tree(self, parent_index, children_indices)
    _is_task_auto_triggered(self, task_index)
    _populate_inspector_panel(self, canvas_task)
    _update_canvas_size(self)
    _on_card_moved(self)
    _update_canvas_connections(self)
    _update_task_config(self)
    _apply_cycle_start_effect(self, task_index)
    _remove_cycle_start_effect(self, task_index)
    _update_all_cycle_start_effects(self)
    _toggle_start_condition_widgets(self)
    _handle_assign_worker(self)
    _handle_unassign_worker(self)
    _open_cycle_end_dialog(self)
    _handle_configure_reassignment(self)
    get_production_flow(self)
    _position_preview_button(self)
    _on_dialog_resized(self, event)
    _preview_execution_order(self)
    _calculate_preview_order(self)
    _traverse_from_task(self, task_idx, order, visited)
    _show_next_preview_step(self)
    _end_preview(self)
    _create_simulation_message_label(self)
    _show_simulation_message(self, message, is_processing)
    _hide_simulation_message(self)
    _highlight_processing_task(self, task_index)
    _clear_all_simulation_effects(self)
    _apply_green_cycle_effect(self, task_index)
    _remove_green_cycle_effect(self, task_index)
    _apply_mixed_effect(self, task_index)
    _remove_mixed_effect(self, task_index)
    _update_all_cycle_effects(self)
    _identify_last_tasks_in_cycles(self)
    _is_task_in_cycle_chain(self, task_index, cycle_chains)
    _is_task_in_cycle_chain(self, task_index, cycle_chains)

class FabricacionBitacoraDialog(QDialog):
    __init__(self, pila_id, pila_nombre, simulation_results, controller, time_calculator, parent)
    _load_and_process_data(self)
    _highlight_work_days(self)
    _on_calendar_date_selected(self)
    _update_history_table(self)
    _get_planned_work_for_day(self, target_date)
    _add_diario_entry(self)

class GetLoteInstanceParametersDialog(QDialog):
    __init__(self, lote_codigo, parent)
    get_data(self)

class GetOptimizationParametersDialog(QDialog):
    __init__(self, parent)
    get_parameters(self)

class GetUnitsDialog(QDialog):
    __init__(self, parent)
    get_units(self)

class GoldenGlowEffect(QWidget):
    __init__(self, parent_card)
    eventFilter(self, obj, event)
    _update_geometry(self)
    paintEvent(self, event)
    stop_animation(self)

class GreenCycleEffect(QWidget):
    __init__(self, parent_card)
    eventFilter(self, obj, event)
    _update_geometry(self)
    paintEvent(self, event)
    stop_animation(self)

class LoadPilaDialog(QDialog):
    __init__(self, pilas, parent)
    _request_delete(self)
    get_selected_id(self)

class LoginDialog(QDialog):
    __init__(self, parent)
    get_credentials(self)

class MixedGoldGreenEffect(QWidget):
    __init__(self, parent_card)
    eventFilter(self, obj, event)
    _update_geometry(self)
    paintEvent(self, event)
    stop_animation(self)

class MultiWorkerSelectionDialog(QDialog):
    __init__(self, all_workers, previously_selected, parent)
    get_selected_workers(self)

class PrepGroupsDialog(QDialog):
    __init__(self, machine_id, machine_name, controller, parent)
    _toggle_form(self, enabled)
    _load_groups(self)
    _on_group_selected(self)
    _add_group(self)
    _save_group(self)
    _delete_group(self)
    _manage_steps(self)

class PrepStepsDialog(QDialog):
    __init__(self, group_id, group_name, controller, parent)
    _load_steps(self)
    _on_step_selected(self)
    _clear_form(self)
    _add_or_update_step(self)
    _delete_step(self)

class PreprocesoDialog(QDialog):
    __init__(self, preproceso_existente, all_materials, parent)
    setup_ui(self)
    get_data(self)

class PreprocesosForCalculationDialog(QDialog):
    __init__(self, fabricacion_id, available_preprocesos, parent)
    setup_ui(self)
    select_all(self)
    clear_selection(self)
    get_selected_preprocesos(self)

class PreprocesosSelectionDialog(QDialog):
    __init__(self, fabricacion, all_preprocesos, assigned_ids, parent)
    setup_ui(self)
    get_selected_preprocesos(self)

class ProcesosMecanicosDialog(QDialog):
    __init__(self, current_procesos, parent)
    setup_ui(self)
    populate_table(self)
    add_proceso(self)
    delete_proceso(self, row)
    get_updated_procesos_mecanicos(self)

class ProcessingGlowEffect(QWidget):
    __init__(self, parent_card)
    _update_geometry(self)
    _update_pulse(self)
    paintEvent(self, event)
    stop_animation(self)

class ProductDetailsDialog(QDialog):
    __init__(self, product_code, controller, parent)
    load_all_data(self)
    _create_components_tab(self)
    load_components(self)
    _on_add_material(self)
    _on_edit_material(self)
    _on_delete_material(self)
    _on_import_materials_clicked(self)
    _create_iterations_tab(self)
    _create_details_panel_widgets(self)
    _clear_details_panel(self)
    _show_details_panel(self)
    load_iterations(self)
    _on_iteration_selected(self, item)
    _on_view_plano_clicked(self)
    _on_add_new_iteration_clicked(self)
    _on_edit_iteration_clicked(self)
    _on_delete_iteration_clicked(self)
    _on_attach_image_clicked(self)

class ReassignmentRuleDialog(QDialog):
    __init__(self, worker_name, current_task, all_canvas_tasks, current_rule, parent)
    _populate_fields(self, rule)
    get_rule(self)

class SavePilaDialog(QDialog):
    __init__(self, parent)
    get_data(self)

class SeleccionarHojasExcelDialog(QDialog):
    __init__(self, parent)
    get_opciones(self)

class SimulationProgressEffect(QWidget):
    __init__(self, parent_card)
    eventFilter(self, obj, event)
    _update_geometry(self)
    paintEvent(self, event)

class SubfabricacionesDialog(QDialog):
    __init__(self, subfabricaciones_actuales, available_machines, parent)
    _refresh_table(self)
    _on_item_selected(self)
    _add_or_update(self)
    _delete_selected(self)
    _clear_form(self)
    get_updated_subfabricaciones(self)
    accept(self)

class SyncDialog(QDialog):
    __init__(self, differences, parent)
    _populate_tabs(self)
    get_selected_changes(self)

```

---

*Documento generado automáticamente - 27/12/2025 16:21*