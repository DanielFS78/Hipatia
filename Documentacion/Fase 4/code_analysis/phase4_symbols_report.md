# Extracción de Símbolos de Código - Fase 4

**Fecha de generación:** 2025-12-30 19:03:10

---

## Resumen

| Métrica | Cantidad |
|---------|----------|
| Archivos analizados | 6 |
| Clases | 13 |
| Métodos | 84 |
| Funciones globales | 3 |

---

## production_context.py

**Ruta:** `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/core/production_context.py`

### Clases

#### `ProductionStatus`

> Data class to hold the status of the current production session.

#### `ProductionContext`

> Manages the context of the current production session for a worker.
Keeps track of the current Order (OF), progress (1 of X), and current process layer.

**Atributos de instancia:**
- `self._status` (línea 19)

**Métodos:**

| Método | Línea | Args | Decoradores |
|--------|-------|------|-------------|
| `__init__` | 18 | self | - |
| `start_session` | 27 | self, order_number, total_units, process_name | - |
| `increment_unit` | 37 | self | - |
| `is_complete` | 42 | self | - |
| `get_progress_label` | 46 | self | - |
| `reset` | 52 | self | - |
| `order_number` | 63 | self | property |
| `current_process` | 67 | self | property |
| `is_active` | 71 | self | property |

---

## tracking_dtos.py

**Ruta:** `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/core/tracking_dtos.py`

### Clases

#### `FabricacionAsignadaDTO`

> DTO para fabricaciones asignadas a un trabajador.

#### `IncidenciaAdjuntoDTO`

> DTO para adjuntos de una incidencia.

#### `IncidenciaLogDTO`

> DTO para incidencias registradas.

#### `PasoTrazabilidadDTO`

> DTO para pasos de trazabilidad (sellos).

#### `TrabajoLogDTO`

> DTO para el log principal de trabajo (Pasaporte).

---

## qr_scanner.py

**Ruta:** `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/core/qr_scanner.py`

### Clases

#### `QrScanner`

> Escáner de códigos QR para trazabilidad usando OpenCV.

Esta versión usa el detector QR nativo de OpenCV, eliminando la
dependencia de pyzbar que tiene problemas en Windows.

Soporta dos modos de oper...

**Atributos de instancia:**
- `self.logger` (línea 72)
- `self.camera_manager` (línea 75)
- `self.camera_index` (línea 76)
- `self.camera` (línea 77)
- `self.use_wechat` (línea 81)
- `self.qr_detector` (línea 82)
- `self.last_scan` (línea 85)
- `self.last_scan_time` (línea 86)
- `self.scan_cooldown` (línea 87)
- `self.is_camera_ready` (línea 88)
- `self.is_camera_ready` (línea 89)

**Métodos:**

| Método | Línea | Args | Decoradores |
|--------|-------|------|-------------|
| `__init__` | 62 | self, camera_manager, camera_index, camera_object | - |
| `_init_detector` | 96 | self | - |
| `_fallback_detector` | 128 | self | - |
| `initialize_camera` | 134 | self | - |
| `_check_cooldown` | 148 | self, data | - |
| `release_camera` | 162 | self | - |
| `scan_frame` | 177 | self, frame | - |
| `draw_qr_detection` | 279 | self, frame, qr_data, bbox | - |
| `parse_qr_data` | 353 | self, qr_data | - |
| `validate_qr_format` | 396 | self, qr_data | - |
| `scan_once` | 409 | self, timeout | - |
| `get_qr_info_for_display` | 484 | self, qr_data | - |
| `set_camera_index` | 512 | self, new_index | - |

#### `QrScannerCallback`

> Clase auxiliar para manejar callbacks del escáner.

Permite definir acciones personalizadas cuando se escanea un QR
en diferentes modos (consulta o trabajo).

**Atributos de instancia:**
- `self.on_consulta` (línea 567)
- `self.on_trabajo` (línea 568)

**Métodos:**

| Método | Línea | Args | Decoradores |
|--------|-------|------|-------------|
| `__init__` | 555 | self, on_consulta, on_trabajo | - |
| `handle_consulta` | 570 | self, qr_data, parsed_info | - |
| `handle_trabajo` | 575 | self, qr_data, parsed_info | - |

### Funciones Globales

| Función | Línea | Args |
|---------|-------|------|
| `scan_qr_simple` | 586 | camera_index, timeout |
| `validate_qr` | 606 | qr_data |
| `get_qr_info` | 625 | qr_data |

---

## worker_controller.py

**Ruta:** `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/features/worker_controller.py`

### Clases

#### `IncidenceDialog` (hereda de: QDialog)

> Diálogo modal para que el trabajador registre una incidencia,
incluyendo título, descripción y la posibilidad de adjuntar fotos.

**Atributos de instancia:**
- `self.fotos_paths` (línea 47)
- `self.tipo_incidencia_edit` (línea 54)
- `self.descripcion_edit` (línea 57)
- `self.fotos_list_widget` (línea 67)
- `self.add_foto_btn` (línea 71)

**Métodos:**

| Método | Línea | Args | Decoradores |
|--------|-------|------|-------------|
| `__init__` | 41 | self, parent | - |
| `_on_add_foto` | 81 | self | - |
| `get_data` | 97 | self | - |

#### `WorkerController`

> Controlador para gestionar las operaciones de trabajadores.

Este controlador actúa como intermediario entre la interfaz de trabajador
y la capa de datos, gestionando todas las operaciones relacionada...

**Atributos de instancia:**
- `self.current_user` (línea 157)
- `self.db_manager` (línea 158)
- `self.main_window` (línea 159)
- `self.qr_scanner` (línea 160)
- `self.tracking_repo` (línea 161)
- `self.label_manager` (línea 163)
- `self.qr_generator` (línea 164)
- `self.label_counter_repo` (línea 165)
- `self.camera_manager` (línea 168)
- `self.logger` (línea 170)
- `self._fabricaciones_asignadas` (línea 173)
- `self._trabajos_activos` (línea 174)
- `self.context` (línea 181)

**Métodos:**

| Método | Línea | Args | Decoradores |
|--------|-------|------|-------------|
| `__init__` | 136 | self, current_user, db_manager, main_window, qr_scanner, tracking_repo, label_manager, qr_generator, label_counter_repo | - |
| `initialize` | 183 | self | - |
| `_connect_signals` | 212 | self | - |
| `_load_assigned_fabricaciones` | 237 | self | - |
| `_load_active_trabajos` | 288 | self | - |
| `get_assigned_fabricaciones` | 316 | self | - |
| `get_active_trabajos` | 325 | self | - |
| `iniciar_trabajo` | 334 | self, qr_code, fabricacion_id, producto_codigo | - |
| `finalizar_trabajo` | 398 | self, trabajo_log_id | - |
| `registrar_incidencia` | 442 | self, trabajo_log_id, tipo_incidencia, descripcion, fotos_paths | - |
| `get_estadisticas_trabajador` | 510 | self | - |
| `_handle_logout` | 537 | self | - |
| `refresh_data` | 559 | self | - |
| `_handle_task_selected` | 580 | self, task_data | - |
| `_handle_generate_labels` | 652 | self, task_data | - |
| `_handle_consult_qr` | 843 | self | - |
| `_handle_start_task` | 941 | self, task_data | - |
| `_handle_end_task` | 1134 | self, task_data | - |
| `_handle_register_incidence` | 1209 | self, task_data | - |
| `_handle_export_data` | 1309 | self | - |
| `_handle_camera_config` | 1369 | self | - |

---

## tracking_repository.py

**Ruta:** `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/database/repositories/tracking_repository.py`

### Clases

#### `TrackingRepository` (hereda de: BaseRepository)

> Repositorio para operaciones de tracking y trazabilidad.

Este repositorio maneja toda la lÃ³gica de negocio relacionada con:
- Inicio y finalizaciÃ³n de trabajos
- Registro de incidencias con fotos
-...

**Atributos de instancia:**
- `self.logger` (línea 61)

**Métodos:**

| Método | Línea | Args | Decoradores |
|--------|-------|------|-------------|
| `__init__` | 53 | self, session_factory | - |
| `get_fabricaciones_por_trabajador` | 67 | self, trabajador_id | - |
| `actualizar_estado_asignacion` | 137 | self, trabajador_id, fabricacion_id, nuevo_estado | - |
| `obtener_o_crear_trabajo_log_por_qr` | 181 | self, qr_code, trabajador_id, fabricacion_id, producto_codigo, orden_fabricacion, notas | - |
| `iniciar_trabajo` | 261 | self, qr_code, trabajador_id, fabricacion_id, producto_codigo | - |
| `finalizar_trabajo_log` | 279 | self, trabajo_log_id, notas_finalizacion | - |
| `pausar_trabajo` | 353 | self, qr_code, motivo | - |
| `reanudar_trabajo` | 389 | self, qr_code | - |
| `obtener_trabajo_por_qr` | 424 | self, qr_code | - |
| `obtener_trabajo_por_id` | 452 | self, trabajo_log_id | - |
| `get_paso_activo_por_trabajador` | 484 | self, trabajador_id | - |
| `get_ultimo_paso_para_qr` | 520 | self, trabajo_log_id | - |
| `iniciar_nuevo_paso` | 552 | self, trabajo_log_id, trabajador_id, paso_nombre, tipo_paso, maquina_id | - |
| `finalizar_paso` | 603 | self, paso_id | - |
| `obtener_trabajos_activos` | 668 | self, trabajador_id, fabricacion_id | - |
| `registrar_incidencia` | 715 | self, trabajo_log_id, trabajador_id, tipo_incidencia, descripcion, rutas_fotos | - |
| `_crear_adjunto` | 769 | self, session, incidencia_id, ruta_archivo | - |
| `añadir_foto_a_incidencia` | 816 | self, incidencia_id, ruta_foto, descripcion | - |
| `resolver_incidencia` | 854 | self, incidencia_id, resolucion | - |
| `obtener_incidencias_abiertas` | 898 | self, fabricacion_id | - |
| `asignar_trabajador_a_fabricacion` | 940 | self, trabajador_id, fabricacion_id | - |
| `desasignar_trabajador_de_fabricacion` | 992 | self, trabajador_id, fabricacion_id | - |
| `obtener_trabajadores_de_fabricacion` | 1037 | self, fabricacion_id | - |
| `obtener_estadisticas_trabajador` | 1071 | self, trabajador_id, fecha_inicio, fecha_fin | - |
| `obtener_estadisticas_fabricacion` | 1127 | self, fabricacion_id | - |
| `get_trabajo_logs_por_trabajador` | 1175 | self, trabajador_id | - |
| `upsert_trabajo_log_from_dict` | 1209 | self, data | - |
| `get_data_for_export` | 1314 | self, trabajador_id, since_date | - |
| `get_all_ordenes_fabricacion` | 1460 | self | - |
| `_map_to_trabajo_log_dto` | 1491 | self, trabajo | - |
| `_map_to_incidencia_log_dto` | 1530 | self, incidencia | - |
| `_map_to_incidencia_adjunto_dto` | 1554 | self, adjunto | - |
| `_map_to_paso_trazabilidad_dto` | 1564 | self, paso | - |

---

## tracking_dialogs.py

**Ruta:** `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/ui/dialogs/tracking_dialogs.py`

### Clases

#### `OrderSetupDialog` (hereda de: QDialog)

> Dialog to setup the start of a production session.
Asks for the Order Number (OF) and the Total Quantity to produce.

**Atributos de instancia:**
- `self.order_input` (línea 28)
- `self.quantity_spin` (línea 32)

**Métodos:**

| Método | Línea | Args | Decoradores |
|--------|-------|------|-------------|
| `__init__` | 12 | self, parent, default_order | - |
| `get_data` | 47 | self | - |

---

