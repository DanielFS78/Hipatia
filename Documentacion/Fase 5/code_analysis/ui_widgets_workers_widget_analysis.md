# Análisis de `workers_widget.py`

**Ruta completa:** `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/ui/widgets/workers_widget.py`


## Importaciones
- `base.*`

## Clases

### Clase `WorkersWidget`
- **Línea:** 4
- **Hereda de:** `QWidget`
- **Docstring:** Widget para gestionar la base de datos de trabajadores (CRUD)....

#### Variables de Clase
- `save_signal`
- `delete_signal`
- `add_annotation_signal`
- `change_password_signal`
- `product_search_signal`
- `of_search_signal`
- `assign_task_signal`
- `cancel_task_signal`

#### Métodos
- `__init__`(self, controller)
- `populate_list`(self, workers_data)
- `clear_details_area`(self)
- `_create_form_widgets`(self)
- `show_worker_details`(self, worker_data: dict)
- `show_add_new_form`(self)
- `get_form_data`(self)
- `populate_history_tables`(self, fabrication_history, annotations)
- `populate_activity_log_table`(self, activity_logs: list)
- `show_incidences_dialog`(self, incidences: list)
  - _Muestra un diálogo con el detalle de las incidencias._
- `get_assignment_data`(self)
- `update_product_search_results`(self, results)
- `setup_of_completer`(self, of_list)