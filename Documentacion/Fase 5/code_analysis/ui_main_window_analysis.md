# Análisis de `main_window.py`

**Ruta completa:** `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/ui/main_window.py`


## Importaciones
- `PyQt6.QtCore.Qt`
- `PyQt6.QtGui.QIcon`
- `PyQt6.QtWidgets.QApplication`
- `PyQt6.QtWidgets.QFrame`
- `PyQt6.QtWidgets.QHBoxLayout`
- `PyQt6.QtWidgets.QLabel`
- `PyQt6.QtWidgets.QMainWindow`
- `PyQt6.QtWidgets.QMenu`
- `PyQt6.QtWidgets.QMessageBox`
- `PyQt6.QtWidgets.QPushButton`
- `PyQt6.QtWidgets.QStackedWidget`
- `PyQt6.QtWidgets.QVBoxLayout`
- `PyQt6.QtWidgets.QWidget`
- `logging`
- `os`
- `sys`
- `ui.widgets.AddProductWidget`
- `ui.widgets.CalculateTimesWidget`
- `ui.widgets.DashboardWidget`
- `ui.widgets.DefinirLoteWidget`
- `ui.widgets.GestionDatosWidget`
- `ui.widgets.HelpWidget`
- `ui.widgets.HistorialWidget`
- `ui.widgets.HomeWidget`
- `ui.widgets.PreprocesosWidget`
- `ui.widgets.ReportesWidget`
- `ui.widgets.SettingsWidget`

## Funciones

### `resource_path`
- **Línea:** 21
- **Firma:** `relative_path`
- **Docstring:** Obtiene la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller....

## Clases

### Clase `MainView`
- **Línea:** 33
- **Hereda de:** `QMainWindow`
- **Docstring:** Vista principal de la aplicación (la ventana)....

#### Métodos
- `__init__`(self, parent)
  - _Inicializa la ventana principal y sus componentes de UI._
- `init_ui`(self)
  - _Inicializa todos los componentes de la interfaz._
- `set_controller`(self, controller)
  - _Asigna el controlador a esta vista y a sus widgets hijos._
- `_create_main_layout`(self)
- `_create_nav_panel`(self)
  - _Crea el panel de navegación lateral con el nuevo menú de Planificación._
- `_on_nav_button_clicked`(self, page_name)
  - _Maneja el clic en botones de navegación desde la vista._
- `switch_page`(self, page_name)
  - _Cambia la página visible en el widget apilado._
- `_update_button_style`(self, active_page)
  - _Actualiza el estilo de los botones de navegación._
- `show_message`(self, title: str, message: str, level: str)
  - _Muestra un diálogo de mensaje al usuario y un mensaje temporal en la barra de es_
- `show_confirmation_dialog`(self, title: str, message: str)
  - _Muestra un diálogo de confirmación (Sí/No) y devuelve la elección del usuario._
- `run_simulation_and_display`(self, production_flow, workers, units, schedule_manager)
  - _Ejecuta la simulación de forma síncrona y devuelve ambos logs._
- `display_simulation_results`(self, results, audit)
  - _Pasa los resultados y la auditoría al widget de cálculo para su visualización._
- `closeEvent`(self, event)
  - _Se ejecuta cuando el usuario cierra la ventana. Pide confirmación_