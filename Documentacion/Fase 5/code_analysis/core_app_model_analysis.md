# Análisis de `app_model.py`

**Ruta completa:** `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/core/app_model.py`


## Importaciones
- `PyQt6.QtCore.QObject`
- `PyQt6.QtCore.pyqtSignal`
- `database.database_manager.DatabaseManager`
- `dataclasses.asdict`
- `datetime.date`
- `datetime.datetime`
- `logging`

## Clases

### Clase `AppModel`
- **Línea:** 10
- **Hereda de:** `QObject`
- **Docstring:** Modelo de la aplicación....

#### Variables de Clase
- `product_added_signal`
- `product_updated_signal`
- `product_deleted_signal`
- `pilas_changed_signal`
- `workers_changed_signal`
- `machines_changed_signal`
- `prep_steps_changed_signal`

#### Métodos
- `__init__`(self, db_manager: DatabaseManager)
- `get_latest_fabricaciones`(self, limit)
  - _Solicita al repositorio las últimas fabricaciones añadidas._
- `search_fabricaciones`(self, query: str)
  - _Busca fabricaciones usando el repositorio de preprocesos._
- `create_fabricacion`(self, codigo: str, descripcion: str)
  - _Pasa la solicitud de crear una fabricación al repositorio._
- `update_fabricacion_preprocesos`(self, fabricacion_id: int, preproceso_ids: list)
  - _Pasa la solicitud de actualizar los preprocesos de una fabricación al repositori_
- `get_product_iterations`(self, codigo_producto)
- `get_diario_bitacora`(self, pila_id: int)
- `add_diario_entry`(self, pila_id, fecha, dia_numero, plan_previsto, trabajo_realizado, notas)
- `create_diario_bitacora`(self, pila_id: int)
- `add_product_iteration`(self, codigo_producto, responsable, descripcion, tipo_fallo, materiales_list, ruta_imagen, ruta_plano)
- `update_product_iteration`(self, iteracion_id, responsable, descripcion, tipo_fallo)
- `get_materials_for_product`(self, producto_codigo: str)
  - _Obtiene los materiales asociados a un producto específico._
- `add_material_to_iteration`(self, iteracion_id, codigo, descripcion)
- `get_all_materials_for_selection`(self)
  - _Obtiene todos los materiales disponibles para usar en diálogos de selección._
- `update_material`(self, material_id, nuevo_codigo, nueva_descripcion)
- `delete_material_link`(self, iteracion_id, material_id)
- `delete_product_iteration`(self, iteracion_id)
- `get_data_for_calculation`(self, producto_codigo: str)
  - _Obtiene datos de un producto, asegurando que el tipo de máquina se resuelva._
- `get_data_for_calculation_from_session`(self, planning_session)
  - _CORREGIDO: Recopila las tareas, AÑADE los preprocesos faltantes,_
- `delete_machine`(self, machine_id)
  - _Elimina una máquina y emite una señal de cambio._
- `get_machine_usage_stats`(self)
- `get_worker_load_stats`(self)
  - _Calcula el tiempo total de trabajo (en minutos) asignado a cada trabajador_
- `get_problematic_components_stats`(self)
- `search_products`(self, query: str)
- `get_latest_products`(self, limit)
  - _Solicita a la BD los últimos productos añadidos._
- `get_product_details`(self, codigo: str)
- `get_prep_step_details_by_ids`(self, step_ids)
- `get_worker_details`(self, worker_id)
- `get_prep_step_details`(self, step_id)
- `get_all_iterations_with_dates`(self)
- `get_all_pilas_with_dates`(self)
- `add_product`(self, data, sub_data)
  - _Valida y añade un producto usando el repositorio._
- `update_product`(self, codigo_original, data, subfabricaciones)
- `delete_product`(self, codigo)
- `update_product_iteration`(self, iteracion_id, responsable, descripcion)
- `get_group_details`(self, group_id)
- `link_material_to_product`(self, producto_codigo, material_id)
- `unlink_material_from_product`(self, producto_codigo, material_id)
- `save_pila`(self, nombre: str, descripcion: str, pila_de_calculo: dict, production_flow: list, simulation_results: list, producto_origen_codigo, unidades)
- `get_all_pilas`(self)
- `load_pila`(self, pila_id: int)
- `delete_pila`(self, pila_id: int)
- `import_database`(self, source_path)
- `get_all_workers`(self, include_inactive)
- `get_latest_workers`(self, limit)
  - _Solicita a la BD los últimos trabajadores añadidos._
- `get_latest_machines`(self, limit)
  - _Solicita a la BD las últimas máquinas añadidas._
- `add_worker`(self, nombre, notas, tipo_trabajador, username, password_hash, role)
- `update_worker`(self, worker_id, nombre, activo, notas, tipo_trabajador, username, password_hash, role)
  - _Actualiza un trabajador existente usando la lógica upsert del repositorio._
- `delete_worker`(self, worker_id)
- `assign_task_to_worker`(self, worker_id, product_code, quantity, orden_fabricacion)
  - _Crea una nueva 'Fabricación' simple, le añade un producto y se la asigna a un tr_
- `get_all_machines`(self, include_inactive)
- `get_machines_by_process_type`(self, tipo_proceso)
- `add_machine`(self, nombre, departamento, tipo_proceso)
- `update_machine`(self, machine_id, nombre, departamento, tipo_proceso, activa)
- `get_groups_for_machine`(self, machine_id)
- `add_prep_group`(self, machine_id, name, description, producto_codigo)
- `update_prep_group`(self, group_id, name, description, producto_codigo)
- `delete_prep_group`(self, group_id)
- `get_steps_for_group`(self, group_id)
- `add_prep_step`(self, group_id, name, time, description, is_daily)
- `update_prep_step`(self, step_id, data)
- `delete_prep_step`(self, step_id)
- `get_prep_info_for_product`(self, producto_codigo)
- `get_distinct_machine_processes`(self)
- `get_all_prep_steps`(self)
- `get_machine_history`(self, machine_id: int)
  - _Obtiene el historial completo de una máquina, incluyendo mantenimientos_
- `add_machine_maintenance`(self, machine_id: int, maintenance_date: date, notes: str)
  - _Pasa la solicitud de añadir un registro de mantenimiento a la BD._
- `get_worker_history`(self, worker_id: int)
  - _Obtiene el historial de un trabajador, incluyendo las fabricaciones asignadas_
- `get_worker_activity_log`(self, worker_id: int)
  - _Obtiene el historial de fichajes (logs de trabajo) de un trabajador._
- `get_all_preprocesos_with_components`(self)
  - _Obtiene todos los preprocesos ya formateados desde el repositorio._
- `create_preproceso`(self, data: dict)
  - _Crea un nuevo preproceso usando el repositorio._
- `update_preproceso`(self, preproceso_id: int, data: dict)
  - _Actualiza un preproceso existente._
- `delete_preproceso`(self, preproceso_id: int)
  - _Elimina un preproceso._