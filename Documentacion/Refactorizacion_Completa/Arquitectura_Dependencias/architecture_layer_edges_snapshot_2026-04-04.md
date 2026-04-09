# Arquitectura — aristas entre capas (imports AST)

Generado por `scripts/architecture_layer_edges.py`.

## Matriz resumen (conteo de aristas módulo→módulo por capa)

| Desde \ Hacia | controllers | core | database | features | ui |
|:--|:--:|:--:|:--:|:--:|:--:|
| **controllers** | 0 | 137 | 13 | 2 | 55 |
| **core** | 0 | 0 | 23 | 0 | 1 |
| **database** | 0 | 39 | 0 | 0 | 0 |
| **features** | 0 | 4 | 0 | 0 | 2 |
| **ui** | 18 | 103 | 2 | 0 | 0 |

## Violaciones duras (reglas arquitectura)

### `database` → `ui` (0 aristas)
- *(ninguna)*

### `database` → `controllers` (0 aristas)
- *(ninguna)*

### `core` → `ui` (1 aristas)
- `core.qr_scanner.scanner` importa `ui`

## Advertencias (revisar / reducir acoplamiento)

### `ui` → `database` (2 aristas)
- `ui.dialogs.fabrication.create_dialog` importa `database.models`
- `ui.dialogs.fabrication.selection_dialogs` importa `database.models`

### `controllers` → `ui` (55 aristas)
- `controllers.backup_controller` importa `ui.dialogs.backup_restore_dialog`
- `controllers.backup_controller` importa `ui.main_window`
- `controllers.backup_controller_io_manager` importa `ui.dialogs`
- `controllers.backup_controller_io_manager` importa `ui.main_window`
- `controllers.calculation_controller` importa `ui.widgets.calculate_times_widget`
- `controllers.hardware_controller` importa `ui.main_view`
- `controllers.hardware_controller` importa `ui.widgets`
- `controllers.historial.controller` importa `ui.main_window`
- `controllers.historial.interaction_manager` importa `ui.main_window`
- `controllers.historial.report_manager` importa `ui.main_window`
- `controllers.historial.view_manager` importa `ui.main_window`
- `controllers.lote_controller` importa `ui.widgets.calculate_times_widget`
- `controllers.machine_controller` importa `ui.dialogs.prep.prep_groups_dialog`
- `controllers.machine_controller` importa `ui.widgets.gestion_datos_widget`
- `controllers.navigation_controller` importa `ui.widgets.calculate_times_widget`
- `controllers.navigation_controller` importa `ui.widgets.gestion_datos_widget`
- `controllers.navigation_controller` importa `ui.widgets.lotes_widget`
- `controllers.pila.pila_manager` importa `ui.dialogs`
- `controllers.product.fabricacion_manager` importa `ui.dialogs`
- `controllers.product.fabricacion_products_handler` importa `ui.dialogs`
- `controllers.product.preproceso_manager` importa `ui.dialogs`
- `controllers.product.product_manager` importa `ui.dialogs`
- `controllers.product.product_manager` importa `ui.dialogs.product.bom_import_preview_dialog`
- `controllers.product.product_manager` importa `ui.widgets`
- `controllers.report_controller` importa `ui.main_view`
- `controllers.report_controller` importa `ui.widgets.historial_widget`
- `controllers.report_controller` importa `ui.widgets.reportes_widget`
- `controllers.schedule_controller` importa `ui.dialogs`
- `controllers.schedule_controller` importa `ui.widgets.settings_widget`
- `controllers.session_controller` importa `ui.dialogs`
- `controllers.session_controller` importa `ui.main_view`
- `controllers.session_controller` importa `ui.widgets`
- `controllers.session_controller` importa `ui.worker.main_window.window`
- `controllers.simulation.editor_manager` importa `ui.dialogs`
- `controllers.simulation.execution_manager` importa `ui.dialogs`
- `controllers.startup_controller` importa `ui.main_window`
- `controllers.ui_controller` importa `ui.widgets.home_widget`
- `controllers.ui_signals_controller` importa `ui.dialogs.product`
- `controllers.ui_signals_controller` importa `ui.main_window`
- `controllers.ui_signals_controller` importa `ui.widgets.calculate_times_widget`
- … *y 15 más*

### `features` → `ui` (2 aristas)
- `features.worker_controller` importa `ui.dialogs.tracking_dialogs`
- `features.worker_controller_io_manager` importa `ui.worker.camera_config_dialog`

### `features` → `controllers` (0 aristas)
- *(ninguna)*

### `features` → `database` (0 aristas)
- *(ninguna)*

## Ciclos simples entre capas (2- y 3-aristas)

- `database → core → database`
- `database → core → ui → database`
- `ui → core → ui`
- `ui → controllers → ui`
- `ui → controllers → core → ui`
- `ui → controllers → features → ui`
- `ui → database → core → ui`
- `features → ui → controllers → features`
- `core → ui → controllers → core`
- `core → ui → database → core`
- `controllers → core → ui → controllers`
- `controllers → features → ui → controllers`
