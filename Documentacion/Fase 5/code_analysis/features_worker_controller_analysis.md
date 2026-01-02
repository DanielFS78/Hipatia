# Análisis de `worker_controller.py`

**Ruta completa:** `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/features/worker_controller.py`


## Importaciones
- `PyQt6.QtCore.Qt`
- `PyQt6.QtWidgets.QDialog`
- `PyQt6.QtWidgets.QDialogButtonBox`
- `PyQt6.QtWidgets.QFileDialog`
- `PyQt6.QtWidgets.QFormLayout`
- `PyQt6.QtWidgets.QInputDialog`
- `PyQt6.QtWidgets.QLabel`
- `PyQt6.QtWidgets.QLineEdit`
- `PyQt6.QtWidgets.QListWidget`
- `PyQt6.QtWidgets.QMessageBox`
- `PyQt6.QtWidgets.QPushButton`
- `PyQt6.QtWidgets.QTextEdit`
- `PyQt6.QtWidgets.QVBoxLayout`
- `core.camera_manager.CameraBackend`
- `core.production_context.ProductionContext`
- `cv2`
- `datetime.datetime`
- `logging`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `ui.dialogs.tracking_dialogs.OrderSetupDialog`
- `unittest.mock.MagicMock`

## Variables de Módulo
- `cv2` (línea 18)

## Clases

### Clase `IncidenceDialog`
- **Línea:** 35
- **Hereda de:** `QDialog`
- **Docstring:** Diálogo modal para que el trabajador registre una incidencia,
incluyendo título, descripción y la posibilidad de adjuntar fotos....

#### Métodos
- `__init__`(self, parent)
- `_on_add_foto`(self)
  - _Abre un diálogo para seleccionar archivos de imagen._
- `get_data`(self)
  - _Devuelve los datos del formulario si son válidos._

### Clase `WorkerController`
- **Línea:** 120
- **Docstring:** Controlador para gestionar las operaciones de trabajadores.

Este controlador actúa como intermediario entre la interfaz de trabajador
y la capa de datos, gestionando todas las operaciones relacionada...

#### Métodos
- `__init__`(self, current_user: Dict[str, Any], db_manager, main_window, qr_scanner, tracking_repo, label_manager, qr_generator, label_counter_repo)
  - _Inicializa el controlador de trabajador._
- `initialize`(self)
  - _Inicializa el controlador y carga los datos iniciales._
- `_connect_signals`(self)
  - _Conecta las señales de la ventana con los métodos del controlador._
- `_load_assigned_fabricaciones`(self)
  - _Carga las fabricaciones asignadas al trabajador actual._
- `_load_active_trabajos`(self)
  - _Carga los trabajos activos del trabajador._
- `get_assigned_fabricaciones`(self)
  - _Obtiene la lista de fabricaciones asignadas al trabajador._
- `get_active_trabajos`(self)
  - _Obtiene la lista de trabajos activos del trabajador._
- `iniciar_trabajo`(self, qr_code: str, fabricacion_id: int, producto_codigo: str)
  - _Inicia un nuevo trabajo escaneando un código QR._
- `finalizar_trabajo`(self, trabajo_log_id: int)
  - _Finaliza un trabajo activo._
- `registrar_incidencia`(self, trabajo_log_id: int, tipo_incidencia: str, descripcion: str, fotos_paths: Optional[List[str]])
  - _Registra una incidencia para un trabajo específico._
- `get_estadisticas_trabajador`(self)
  - _Obtiene las estadísticas del trabajador actual._
- `_handle_logout`(self)
  - _Maneja el cierre de sesión del trabajador._
- `refresh_data`(self)
  - _Recarga todos los datos desde la base de datos._
- `_handle_task_selected`(self, task_data: Dict[str, Any])
  - _Se llama cuando el usuario selecciona una tarea en la lista._
- `_handle_generate_labels`(self, task_data: Dict[str, Any])
  - _Maneja la solicitud de generar e imprimir etiquetas QR._
- `_handle_consult_qr`(self)
  - _Maneja la solicitud de consultar un QR._
- `_handle_start_task`(self, task_data: Dict[str, Any])
  - _Maneja la solicitud de INICIAR un paso de trabajo escaneando un QR._
- `_handle_end_task`(self, task_data: Dict[str, Any])
  - _Maneja la solicitud de FINALIZAR el paso de trabajo activo._
- `_handle_register_incidence`(self, task_data: Dict[str, Any])
  - _Maneja la solicitud de registrar una incidencia para el PASO activo._
- `_handle_export_data`(self)
  - _Maneja la exportación de datos de trabajo a un archivo JSON._
- `_handle_camera_config`(self)
  - _Muestra el diálogo de configuración de cámara._