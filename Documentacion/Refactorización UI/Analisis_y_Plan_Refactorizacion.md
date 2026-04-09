# Documentación de Interfaz de Usuario: Hipatia

> **Generado el:** 2026-03-10 19:32:54
> **Autor de la documentación:** Antigravity (IA)

## 📸 Visión General (Área UI)

### Propósito de este Informe
Este documento se centra en la auditoría y documentación de la capa visual de Hipatia, cubriendo widgets y diálogos críticos para la simulación y trazabilidad.

### Arquitectura UI
La interfaz está construida con **PyQt6**, siguiendo patrones de desacoplamiento para permitir el testeo de la lógica de presentación independientemente de los widgets de Qt.

### Estado arquitectónico (abril 2026)

Los informes antiguos que describen solo el **riesgo de «objeto dios» en `AppModel`** o la **necesidad de inyectar fachadas** siguen siendo **válidos como tendencia**, pero **no reflejan el trabajo ya cerrado** en coordinación con producción (**B5**, reducción de dependencia en controladores y puntos de UI acordados). Fuente de verdad: [`.agents/skills/reduccion_god_objects/SKILL.md`](../../.agents/skills/reduccion_god_objects/SKILL.md) (B5 **finalizada**; tabla de controladores con servicios inyectados; exclusiones explícitas: señales y orquestación que siguen en `AppModel`).

Sobre **widgets que recibían `AppController` solo para extraer sub-controladores**: el patrón **sigue en pantallas como reportes o diálogos de flujo**; la mitigación es **incremental**. **Gestión de datos:** las pestañas usan **DI** (`ProductController`, `MachineController`, etc.) y el primer argumento que envía `MainView` es **`_app_controller` ignorado** salvo compatibilidad. **`PreprocesosWidget`** ya no guarda el hub: abre `AssignPreprocesosDialog` con `FabricacionService` del contenedor y `ProductController` como `opens_fabricacion_preprocesos`. **`SettingsWidget`:** `ScheduleController` + fallback `config_repo` sin retener `AppController`. **`ReportesWidget`:** el hub solo al enlazar (`set_controller` / `connect_reportes_signals` con `self.app`); listas y gráficas reciben `ReportService` y `fallback_reports_model`, no el orquestador. Mapa de capas: [`ANALISIS_CAPAS.md`](../Refactorizacion_Completa/Arquitectura_Dependencias/ANALISIS_CAPAS.md).

---
## 📑 Índice de Componentes UI

### 📂 Componentes en: dialogs
  - [ui/dialogs/backup_restore_dialog.py](#uidialogsbackuprestoredialogpy)
  - [ui/dialogs/canvas_widgets.py](#uidialogscanvaswidgetspy)
  - [ui/dialogs/connection_dialog.py](#uidialogsconnectiondialogpy)
  - [ui/dialogs/effects/golden_glow.py](#uidialogseffectsgoldenglowpy)
  - [ui/dialogs/effects/green_cycle.py](#uidialogseffectsgreencyclepy)
  - [ui/dialogs/effects/mixed_gold_green.py](#uidialogseffectsmixedgoldgreenpy)
  - [ui/dialogs/effects/processing_glow.py](#uidialogseffectsprocessingglowpy)
  - [ui/dialogs/effects/progress.py](#uidialogseffectsprogresspy)
  - [ui/dialogs/fabrication/assignment_dialogs.py](#uidialogsfabricationassignmentdialogspy)
  - [ui/dialogs/fabrication/bitacora_dialog.py](#uidialogsfabricationbitacoradialogpy)
  - [ui/dialogs/fabrication/create_dialog.py](#uidialogsfabricationcreatedialogpy)
  - [ui/dialogs/fabrication/create_presenter.py](#uidialogsfabricationcreatepresenterpy)
  - [ui/dialogs/fabrication/input_dialogs.py](#uidialogsfabricationinputdialogspy)
  - [ui/dialogs/fabrication/persistence_dialogs.py](#uidialogsfabricationpersistencedialogspy)
  - [ui/dialogs/fabrication/products_dialog.py](#uidialogsfabricationproductsdialogpy)
  - [ui/dialogs/fabrication/selection_dialogs.py](#uidialogsfabricationselectiondialogspy)
  - [ui/dialogs/prep/prep_groups_dialog.py](#uidialogsprepprepgroupsdialogpy)
  - [ui/dialogs/prep/prep_steps_dialog.py](#uidialogsprepprepstepsdialogpy)
  - [ui/dialogs/prep/preproceso_dialog.py](#uidialogspreppreprocesodialogpy)
  - [ui/dialogs/product/add_iteration_dialog.py](#uidialogsproductadditerationdialogpy)
  - [ui/dialogs/product/procesos_mecanicos_dialog.py](#uidialogsproductprocesosmecanicosdialogpy)
  - [ui/dialogs/product/product_details_dialog.py](#uidialogsproductproductdetailsdialogpy)
  - [ui/dialogs/product/subfabricaciones_dialog.py](#uidialogsproductsubfabricacionesdialogpy)
  - [ui/dialogs/production_flow/common_dialogs.py](#uidialogsproductionflowcommondialogspy)
  - [ui/dialogs/production_flow/define_flow_dialog.py](#uidialogsproductionflowdefineflowdialogpy)
  - [ui/dialogs/production_flow/define_flow_presenter.py](#uidialogsproductionflowdefineflowpresenterpy)
  - [ui/dialogs/production_flow/enhanced_flow_dialog.py](#uidialogsproductionflowenhancedflowdialogpy)
  - [ui/dialogs/production_flow/enhanced_flow_presenter.py](#uidialogsproductionflowenhancedflowpresenterpy)
  - [ui/dialogs/tracking_dialogs.py](#uidialogstrackingdialogspy)
  - [ui/dialogs/utility_dialogs.py](#uidialogsutilitydialogspy)
### 📂 Componentes en: widgets
  - [ui/widgets/base.py](#uiwidgetsbasepy)
  - [ui/widgets/calculate_times_widget.py](#uiwidgetscalculatetimeswidgetpy)
  - [ui/widgets/dashboard_widget.py](#uiwidgetsdashboardwidgetpy)
  - [ui/widgets/fabrications_widget.py](#uiwidgetsfabricationswidgetpy)
  - [ui/widgets/gestion_datos_widget.py](#uiwidgetsgestiondatoswidgetpy)
  - [ui/widgets/help_widget.py](#uiwidgetshelpwidgetpy)
  - [ui/widgets/historial_widget.py](#uiwidgetshistorialwidgetpy)
  - [ui/widgets/home_widget.py](#uiwidgetshomewidgetpy)
  - [ui/widgets/lotes_widget.py](#uiwidgetsloteswidgetpy)
  - [ui/widgets/machines_widget.py](#uiwidgetsmachineswidgetpy)
  - [ui/widgets/prep_steps_widget.py](#uiwidgetsprepstepswidgetpy)
  - [ui/widgets/preprocesos_widget.py](#uiwidgetspreprocesoswidgetpy)
  - [ui/widgets/product/iterations_widget.py](#uiwidgetsproductiterationswidgetpy)
  - [ui/widgets/product/materials_widget.py](#uiwidgetsproductmaterialswidgetpy)
  - [ui/widgets/production_flow/define_control_panel.py](#uiwidgetsproductionflowdefinecontrolpanelpy)
  - [ui/widgets/production_flow/flow_canvas.py](#uiwidgetsproductionflowflowcanvaspy)
  - [ui/widgets/production_flow/flow_graph_manager.py](#uiwidgetsproductionflowflowgraphmanagerpy)
  - [ui/widgets/production_flow/inspector_panel.py](#uiwidgetsproductionflowinspectorpanelpy)
  - [ui/widgets/production_flow/inspector_presenter.py](#uiwidgetsproductionflowinspectorpresenterpy)
  - [ui/widgets/production_flow/library_panel.py](#uiwidgetsproductionflowlibrarypanelpy)
  - [ui/widgets/products_widget.py](#uiwidgetsproductswidgetpy)
  - [ui/widgets/reportes_widget.py](#uiwidgetsreporteswidgetpy)
  - [ui/widgets/reports/charts_container.py](#uiwidgetsreportschartscontainerpy)
  - [ui/widgets/reports/order_list.py](#uiwidgetsreportsorderlistpy)
  - [ui/widgets/reports/smart_search.py](#uiwidgetsreportssmartsearchpy)
  - [ui/widgets/settings_widget.py](#uiwidgetssettingswidgetpy)
  - [ui/widgets/timeline_widget.py](#uiwidgetstimelinewidgetpy)
  - [ui/widgets/workers_widget.py](#uiwidgetsworkerswidgetpy)

<div style='page-break-after: always;'></div>

# Detalles de UI: dialogs

## <a name='uidialogsbackuprestoredialogpy'></a> 📄 ui/dialogs/backup_restore_dialog.py

### Descripción General
Backup Restore Dialog
Permite visualizar, seleccionar y restaurar backups automáticos.

### Clases

#### 🏛 Clase: `BackupRestoreDialog`
Diálogo para gestionar la restauración de backups.

**Métodos:**
- `init_ui`: Inicializa la interfaz del diálogo.
- `load_backups`: Carga la lista de backups disponibles.
- `_on_selection_changed`: Maneja el cambio de selección en la tabla.
- `_on_restore_clicked`: Maneja el clic en el botón de restaurar.

---

## <a name='uidialogscanvaswidgetspy'></a> 📄 ui/dialogs/canvas_widgets.py

> **Estado 2026-04:** `canvas_widgets` reexporta `CanvasWidget` desde `canvas_widget.py` (dialogo legacy).
> El canvas de flujo de produccion reutilizable es `ui/widgets/production_flow/flow_canvas.py` (`ProductionFlowCanvas`)
> con conexiones en `flow_connection_painter.py` (enrutado ortogonal, obstaculos, capa de pintado). La descripcion
> de `_calculate_smart_path` siguiente corresponde **solo** a la implementacion legacy del dialogo, no al pintor moderno.

### Clases

#### 🏛 Clase: `CanvasWidget`
Un widget personalizado que actúa como un canvas para arrastrar, soltar y visualizar
las tareas del flujo de producción (dialogo legacy; ver nota arriba).

**Métodos:**
- `set_connections`: Recibe la lista de conexiones desde el diálogo principal y fuerza un redibujado.
- `paintEvent`: Este método se llama automáticamente cada vez que el widget necesita ser redibujado. Dibuja el grid de fondo y las conexiones inteligentes con el estilo adecuado según su tipo.
- `_get_task_index_by_widget`: Obtiene el índice de una tarea por su widget.
- `_draw_cyclic_arrow_with_glow`: Dibuja una flecha cíclica con efecto neón y gradiente de color.
- `_draw_grid`: Dibuja una cuadrícula de fondo tipo papel milimétrico.
- `_calculate_smart_path`: En el dialogo legacy, ruta en L con ajuste simple en grid; **no** equivale a `FlowConnectionPainter.calculate_smart_path` (Manhattan, codos, todos los widgets como obstaculo, terminales visuales).
- `_count_path_collisions`: Cuenta cuántos segmentos del path colisionan con obstáculos.
- `_line_intersects_rect`: Comprueba si una línea intersecta con un rectángulo.
- `_adjust_path_to_avoid_obstacles`: Intenta ajustar el path para evitar obstáculos desplazándolo verticalmente.
- `_draw_arrowhead`: Función auxiliar para dibujar la punta de una flecha (sin cambios lógicos).
- `mousePressEvent`: Detecta clics en el canvas (fondo) para ocultar el inspector.

#### 🏛 Clase: `CardWidget`
Una tarjeta visual y MOVIBLE que representa una tarea en el canvas.
Emite 'clicked' al ser seleccionada y 'moved' al ser movida.

**Métodos:**
- `mousePressEvent`: Se activa al hacer clic en la tarjeta.
- `mouseMoveEvent`: Se activa al mover el ratón mientras se mantiene presionado.
- `mouseReleaseEvent`: Se activa al soltar el botón del ratón.
- `_snap_to_grid`: Ajusta la posición de la tarjeta al punto más cercano de la cuadrícula.

---

## <a name='uidialogsconnectiondialogpy'></a> 📄 ui/dialogs/connection_dialog.py

### Descripción General
Connection Mode Selection Dialog
================================
Allows the user to choose between Local (SQLite) and Server (PostgreSQL) 
modes at application startup.

### Clases

#### 🏛 Clase: `ConnectionDialog`
Dialog displayed at startup to select database connection mode.

**Métodos:**
- `get_selection`: Returns a tuple: (mode_string, remember_bool) mode_string: 'sqlite' or 'postgresql'

---

## <a name='uidialogseffectsgoldenglowpy'></a> 📄 ui/dialogs/effects/golden_glow.py

### Clases

#### 🏛 Clase: `GoldenGlowEffect`
Widget que dibuja un círculo dorado giratorio alrededor de una tarjeta
para indicar que es una tarea de inicio de ciclo.

**Métodos:**
- `eventFilter`: Filtra eventos de la tarjeta padre y del canvas para actualizar la geometría cuando sea necesario.
- `_update_geometry`: Actualiza posición y tamaño para rodear la tarjeta. CORREGIDO: Usa mapTo() para obtener las coordenadas correctas relativas al canvas.
- `paintEvent`: Dibuja un efecto neón con luz circulante continua, sin puntos discretos.
- `stop_animation`: Detiene la animación y limpia recursos.

---

## <a name='uidialogseffectsgreencyclepy'></a> 📄 ui/dialogs/effects/green_cycle.py

### Clases

#### 🏛 Clase: `GreenCycleEffect`
Widget que dibuja un aro verde con efecto neón para tareas intermedias del ciclo.

**Métodos:**
- `paintEvent`: Efecto neón verde ESTÁTICO (sin animación).

---

## <a name='uidialogseffectsmixedgoldgreenpy'></a> 📄 ui/dialogs/effects/mixed_gold_green.py

### Clases

#### 🏛 Clase: `MixedGoldGreenEffect`
Widget que dibuja un aro con efecto mixto dorado-verde para tareas finales de ciclo.

**Métodos:**
- `paintEvent`: Efecto neón mixto ESTÁTICO (sin animación).

---

## <a name='uidialogseffectsprocessingglowpy'></a> 📄 ui/dialogs/effects/processing_glow.py

### Clases

#### 🏛 Clase: `ProcessingGlowEffect`
Widget que dibuja un círculo naranja pulsante alrededor de una tarjeta
para indicar que está siendo procesada por la simulación.

**Métodos:**
- `_update_geometry`: Actualiza posición y tamaño para rodear la tarjeta.
- `paintEvent`: Dibuja el círculo naranja pulsante con efecto neón.
- `stop_animation`: Detiene la animación del pulso.

---

## <a name='uidialogseffectsprogresspy'></a> 📄 ui/dialogs/effects/progress.py

### Clases

#### 🏛 Clase: `SimulationProgressEffect`
Widget que dibuja un aro azulado grisáceo giratorio con efecto neón
para indicar que una tarjeta está siendo procesada por la simulación.

**Métodos:**
- `eventFilter`: Filtra eventos para actualizar geometría cuando sea necesario.
- `_update_geometry`: Actualiza posición y tamaño para rodear la tarjeta.
- `paintEvent`: Dibuja un efecto neón azulado con luz circulante continua.

---

## <a name='uidialogsfabricationassignmentdialogspy'></a> 📄 ui/dialogs/fabrication/assignment_dialogs.py

### Clases

#### 🏛 Clase: `AssignPreprocesosDialog`
Diálogo para asignar preprocesos a fabricaciones desde el menú de Preprocesos.

**Métodos:**
- `load_fabricaciones`: Carga todas las fabricaciones disponibles.
- `on_fabricacion_selected`: Maneja la selección de una fabricación.
- `load_current_preprocesos`: Carga los preprocesos actuales de la fabricación.
- `modify_selected_fabricacion`: Abre el diálogo para modificar preprocesos de la fabricación seleccionada.

---

## <a name='uidialogsfabricationbitacoradialogpy'></a> 📄 ui/dialogs/fabrication/bitacora_dialog.py

### Clases

#### 🏛 Clase: `FabricacionBitacoraDialog`
Diálogo para gestionar el diario de bitácora de una pila de fabricación
con un calendario interactivo.

**Datos (2026-04):** persistencia mediante `_bitacora_backend` (`PilaService` inyectado desde `pila_manager`, o `resolve_pila_service`, o `model.planning_facade`). Ya no existen en `AppModel` los delegadores `get_diario_bitacora` / `add_diario_evento` / `create_diario_bitacora`.

**Métodos:**
- `_load_and_process_data`: Carga los datos iniciales, formatea el calendario y selecciona el día actual.
- `_highlight_work_days`: Resalta en el calendario los días con trabajo planificado.
- `_on_calendar_date_selected`: Actualiza la vista de detalles cuando se selecciona una fecha.
- `_update_history_table`: Rellena la tabla del historial con las entradas guardadas.
- `_get_planned_work_for_day`: Genera un resumen del trabajo planificado para una fecha específica.
- `_add_diario_evento`: Guarda o actualiza la entrada para la fecha seleccionada.

---

## <a name='uidialogsfabricationcreatedialogpy'></a> 📄 ui/dialogs/fabrication/create_dialog.py

### Clases

#### 🏛 Clase: `CreateFabricacionDialog`
Diálogo para crear una fabricación asignándole preprocesos Y productos.

**Métodos:**
- `_setup_preprocesos_tab`: Configura la pestaña de Preprocesos.
- `_setup_productos_tab`: Configura la pestaña de Productos.
- `load_initial_data`: Carga los datos iniciales en las listas.
- `get_fabricacion_data`: Retorna los datos de la fabricación incluyendo preprocesos y productos.

---

## <a name='uidialogsfabricationinputdialogspy'></a> 📄 ui/dialogs/fabrication/input_dialogs.py

### Clases

#### 🏛 Clase: `GetLoteInstanceParametersDialog`
Diálogo para solicitar los parámetros de una instancia de Lote al añadirla a la Pila.

**Métodos:**
- `get_data`: Devuelve un diccionario con los parámetros introducidos por el usuario.

#### 🏛 Clase: `GetOptimizationParametersDialog`
Diálogo para solicitar fecha de inicio, fecha de fin y unidades para la optimización.


#### 🏛 Clase: `GetUnitsDialog`
Diálogo simple para solicitar el número de unidades a producir.


---

## <a name='uidialogsfabricationpersistencedialogspy'></a> 📄 ui/dialogs/fabrication/persistence_dialogs.py

### Clases

#### 🏛 Clase: `SavePilaDialog`
Diálogo para pedir nombre y descripción al guardar una pila.

**Métodos:**
- `get_data`: Retorna (nombre, descripcion).

#### 🏛 Clase: `LoadPilaDialog`
Diálogo para mostrar y seleccionar pilas guardadas.

**Métodos:**
- `get_selected_id`: Devuelve el ID seleccionado, ya sea para cargar o eliminar.

---

## <a name='uidialogsfabricationproductsdialogpy'></a> 📄 ui/dialogs/fabrication/products_dialog.py

### Clases

#### 🏛 Clase: `ProductsSelectionDialog`
Diálogo para asignar/editar productos de una fabricación existente.
Permite añadir, quitar y modificar cantidades.

**Métodos:**
- `get_products_data`: Retorna la lista de productos configurada. Returns:     list: Lista de tuplas (producto_codigo, cantidad)

---

## <a name='uidialogsfabricationselectiondialogspy'></a> 📄 ui/dialogs/fabrication/selection_dialogs.py

### Clases

#### 🏛 Clase: `PreprocesosSelectionDialog`
Diálogo para seleccionar qué preprocesos asignar a una fabricación.

**Métodos:**
- `get_selected_preprocesos`: Retorna lista de IDs de preprocesos seleccionados.

#### 🏛 Clase: `PreprocesosForCalculationDialog`
Diálogo para mostrar y seleccionar preprocesos disponibles
para añadir al cálculo de tiempos de una fabricación.

**Métodos:**
- `select_all`: Selecciona todos los preprocesos.
- `clear_selection`: Limpia la selección.
- `get_selected_preprocesos`: Retorna lista de preprocesos seleccionados.  Returns:     list: Lista de diccionarios con datos de preprocesos

---

## <a name='uidialogsprepprepgroupsdialogpy'></a> 📄 ui/dialogs/prep/prep_groups_dialog.py

### Clases

#### 🏛 Clase: `PrepGroupsDialog`
Diálogo para gestionar los Grupos de Preparación de una máquina.
Permite organizar fases de preparación en grupos lógicos.

**Métodos:**
- `__init__`: Inicializa el diálogo de grupos de preparación.  Args:     machine_id: ID de la máquina.     machine_name: Nombre de la máquina.     controller: Controlador de máquinas.     parent: Widget padre.
- `_toggle_form`: Habilita o deshabilita los campos del formulario.
- `_load_groups`: Carga los grupos de preparación de la máquina en la lista.
- `_on_group_selected`: Carga los datos del grupo seleccionado en el formulario.
- `_add_group`: Prepara el formulario para añadir un nuevo grupo.
- `_save_group`: Guarda o actualiza el grupo actual.
- `_delete_group`: Elimina el grupo seleccionado.
- `_manage_steps`: Abre el diálogo de pasos para el grupo seleccionado.

---

## <a name='uidialogsprepprepstepsdialogpy'></a> 📄 ui/dialogs/prep/prep_steps_dialog.py

### Clases

#### 🏛 Clase: `PrepStepsDialog`
Diálogo para gestionar los pasos individuales de un grupo de preparación.
Permite visualizar, añadir, actualizar y eliminar pasos.

**Métodos:**
- `__init__`: Inicializa el diálogo de pasos de preparación.  Args:     group_id: ID del grupo de preparación.     group_name: Nombre del grupo para el título.     controller: Controlador de máquinas.     parent: Widget padre.
- `_load_steps`: Carga los pasos del grupo y los muestra en la tabla.
- `_on_step_selected`: Carga los datos de un paso seleccionado en el formulario.
- `_clear_form`: Limpia el formulario para añadir un nuevo paso.
- `_add_or_update_step`: Añade un nuevo paso o actualiza el seleccionado en el grupo.
- `_delete_step`: Elimina el paso seleccionado.

---

## <a name='uidialogspreppreprocesodialogpy'></a> 📄 ui/dialogs/prep/preproceso_dialog.py

### Clases

#### 🏛 Clase: `PreprocesoDialog`
Diálogo para crear o editar un Preproceso, permitiendo la asignación
de materiales (componentes).

**Métodos:**
- `__init__`: Inicializa el diálogo de preproceso.  Args:     preproceso_existente: Datos del preproceso a editar (opcional).     all_materials: Lista de todos los materiales disponibles.     controller: Controlador de preprocesos/materiales.     parent: Widget padre.
- `setup_ui`: Configura la interfaz gráfica del diálogo.
- `_populate_materials_list`: Rellena la lista con los materiales disponibles. Marca como seleccionados aquellos que ya pertenecen al preproceso.
- `_refresh_data`: Recarga los materiales desde el modelo a través del controlador y actualiza la visualización de la lista.
- `_update_assigned_ids_from_selection`: Sincroniza el conjunto interno de IDs asignados con los elementos actualmente seleccionados en el widget de lista.
- `_on_add_material`: Inicia el flujo para crear un nuevo componente/material en el sistema.
- `_on_edit_material`: Inicia el flujo para editar un componente existente seleccionado.
- `_on_delete_material`: Elimina los componentes seleccionados del sistema completo. Requiere confirmación del usuario debido al impacto global.
- `get_data`: Recolecta los datos del formulario y los devuelve como un diccionario.  Returns:     Diccionario con datos del preproceso o None si la validación falla.

---

## <a name='uidialogsproductadditerationdialogpy'></a> 📄 ui/dialogs/product/add_iteration_dialog.py

### Clases

#### 🏛 Clase: `AddIterationDialog`
Diálogo para añadir una nueva iteración con todos los campos requeridos.


---

## <a name='uidialogsproductprocesosmecanicosdialogpy'></a> 📄 ui/dialogs/product/procesos_mecanicos_dialog.py

### Clases

#### 🏛 Clase: `ProcesosMecanicosDialog`
Diálogo para gestionar los procesos mecánicos de un producto.
Similar a SubfabricacionesDialog pero sin máquinas.


#### 🏛 Clase: `AddProcesoMecanicoDialog`
Diálogo para añadir un nuevo proceso mecánico.


---

## <a name='uidialogsproductproductdetailsdialogpy'></a> 📄 ui/dialogs/product/product_details_dialog.py

### Clases

#### 🏛 Clase: `ProductDetailsDialog`
Diálogo rediseñado que utiliza sub-widgets para gestionar Componentes e Iteraciones.

**Métodos:**
- `load_all_data`: Carga los datos en ambos sub-widgets.

---

## <a name='uidialogsproductsubfabricacionesdialogpy'></a> 📄 ui/dialogs/product/subfabricaciones_dialog.py

### Clases

#### 🏛 Clase: `SubfabricacionesDialog`
Diálogo para gestionar (CRUD) la lista de sub-fabricaciones de un producto.

**Métodos:**
- `accept`: Sobrescribe el método accept para avisar si hay datos en el formulario sin guardar.

---

## <a name='uidialogsproductionflowcommondialogspy'></a> 📄 ui/dialogs/production_flow/common_dialogs.py

### Clases

#### 🏛 Clase: `CycleEndConfigDialog`
Diálogo para configurar el fin de ciclo de una tarea.
Permite seleccionar a qué tarea de inicio de ciclo regresar.

**Métodos:**
- `get_configuration`: Retorna la configuración seleccionada.  Returns:     dict: {'is_cycle_end': bool, 'return_to_index': int|None}

#### 🏛 Clase: `ReassignmentRuleDialog`
Diálogo para definir la regla de reasignación de un trabajador para una tarea.

**Métodos:**
- `get_rule`: Construye y devuelve el diccionario de la regla a partir del estado del formulario. CORREGIDO: Define y usa 'mode'.

#### 🏛 Clase: `DefinirCantidadesDialog`
Diálogo para que el usuario defina la cantidad a producir para cada
tarea o grupo de tareas en el flujo de producción.

**Métodos:**
- `get_cantidades`: Devuelve un diccionario que mapea el índice de cada paso del flujo con la cantidad de unidades especificada por el usuario.

---

## <a name='uidialogsproductionflowdefineflowdialogpy'></a> 📄 ui/dialogs/production_flow/define_flow_dialog.py

### Clases

#### 🏛 Clase: `DefineProductionFlowDialog`
Diálogo para definir la secuencia de tareas, dependencias y trabajadores.

**Métodos:**
- `_on_save_flow`: Gestiona el guardado de un flujo de producción sin calcular.
- `_on_machine_selected`: Carga las fases de preparación de la máquina seleccionada.
- `_on_task_selected`: Actualiza el menú de máquinas según la tarea seleccionada.
- `_add_or_update_step`: Añade un nuevo paso o actualiza uno existente usando el panel y el presenter.
- `_update_flow_display`: Refresca la visualización de la lista de pasos en el panel derecho.
- `_create_step_widget`: Crea el widget visual para un paso individual.
- `_create_group_widget`: Crea el widget visual para un grupo secuencial.
- `_reset_form`: Limpia el control panel y sincroniza estados.
- `_edit_step`: Activa el modo edición para un paso.
- `_toggle_start_condition`: Actualiza la habilitación de componentes de condición en el control panel.
- `_update_previous_task_menu`: Puebla el menú de dependencias del control panel.
- `_delete_step`: Elimina un paso solicitando confirmación.
- `get_production_flow`: Retorna el flujo final.
- `_assign_worker_to_group`: Asigna trabajadores a un grupo.
- `_group_selected_steps`: Lógica para agrupar pasos.

---

## <a name='uidialogsproductionflowdefineflowpresenterpy'></a> 📄 ui/dialogs/production_flow/define_flow_presenter.py

### Clases

#### 🏛 Clase: `DefineFlowPresenter`
Presenter/Lógica para aislar el ensamblado de datos y configuraciones 
de la vista (DefineProductionFlowDialog).

**Datos (2026-04):** consultas de máquinas y preparación solo vía `machine_service`, `preparation_service` y `fabricacion_service` (resueltos en el diálogo). No mantiene referencia a `AppModel`.

**Métodos:**
- `prepare_task_data`: Organiza la lista plana de tareas primarias en un diccionario agrupado por producto.
- `set_production_flow`: Inicializa el flujo de producción.
- `get_production_flow`: Retorna el flujo de producción actual.
- `add_step`: Añade un nuevo paso al flujo.
- `update_step`: Actualiza un paso existente.
- `delete_step`: Elimina un paso y limpia dependencias rotas.
- `get_step`: Obtiene un paso por su índice.
- `get_machines_for_task`: Obtiene las máquinas compatibles con el tipo de proceso de la tarea.
- `get_prep_info`: Obtiene información de preparación por defecto para un producto.
- `get_prep_steps_for_machine`: Obtiene todas las fases de preparación asociadas a una máquina.
- `get_default_step_ids`: Obtiene los IDs de los pasos pertenecientes a un grupo.
- `group_tasks`: Crea un grupo secuencial a partir de las tareas seleccionadas y recalcula  todos los índices de dependencia para mantener la integridad del flujo.

---

## <a name='uidialogsproductionflowenhancedflowdialogpy'></a> 📄 ui/dialogs/production_flow/enhanced_flow_dialog.py

### Clases

#### 🏛 Clase: `EnhancedProductionFlowDialog`
Diálogo para la planificación visual del flujo de producción.
Delegado en FlowGraphManager (UI Canvas) y EnhancedFlowPresenter (Lógica).


---

## <a name='uidialogsproductionflowenhancedflowpresenterpy'></a> 📄 ui/dialogs/production_flow/enhanced_flow_presenter.py

### Clases

#### 🏛 Clase: `EnhancedFlowPresenter`
Presenter/Lógica para aislar el ensamblado de datos y configuraciones 
de la vista (EnhancedProductionFlowDialog).

**Métodos:**
- `add_task`: Agrega una nueva tarea al estado lógico y devuelve su payload.
- `remove_task`: Elimina una tarea y reajusta las dependencias del resto de tareas.
- `clear_tasks`: Limpia todo el estado lógico del canvas.
- `get_task`: Devuelve el payload de una tarea por su índice.
- `update_task_config`: Actualiza un valor de configuración de una tarea específica.
- `apply_cycle_end_config`: Aplica la configuración de fin de ciclo, encargándose de reconciliar `next_cyclic_task_index`.
- `get_worker_config`: Busca la configuración de un trabajador específico en una tarea.
- `get_inspector_data`: Prepara todos los datos necesarios para poblar el inspector.
- `identify_last_tasks_in_cycles`: Identifica los índices de las tareas que cierran ciclos.
- `start_simulation_preview`: Inicia una sesión de simulación para previsualización.
- `get_next_simulation_step`: Obtiene el siguiente índice de tarea en la simulación.
- `stop_simulation_preview`: Finaliza la sesión de simulación.
- `get_simulation_progress_text`: Genera el texto informativo para el progreso de la simulación.
- `get_logical_connections`: Calcula todas las conexiones lógicas (padres, hijos, ciclos)  para una tarea seleccionada.
- `load_flow`: Inicializa el estado del Presenter desde datos externos. Retorna la lista de tareas procesadas con sus posiciones para que la vista cree los widgets.
- `prepare_task_data`: Organiza la lista plana de tareas primarias en un diccionario agrupado por producto.
- `build_production_flow`: Construye el flujo final extraído del estado lógico o de la lista proporcionada.

---

## <a name='uidialogstrackingdialogspy'></a> 📄 ui/dialogs/tracking_dialogs.py

### Clases

#### 🏛 Clase: `OrderSetupDialog`
Dialog to setup the start of a production session.
Asks for the Order Number (OF) and the Total Quantity to produce.


---

## <a name='uidialogsutilitydialogspy'></a> 📄 ui/dialogs/utility_dialogs.py

### Clases

#### 🏛 Clase: `AddBreakDialog`
Diálogo simple para añadir un nuevo descanso.

**Métodos:**
- `get_times`: Devuelve las horas seleccionadas en formato de texto.

#### 🏛 Clase: `LoginDialog`
Diálogo para la autenticación de usuarios.

**Métodos:**
- `get_credentials`: Devuelve el usuario y la contraseña introducidos.

#### 🏛 Clase: `ChangePasswordDialog`
Diálogo para cambiar la contraseña de un usuario.

**Métodos:**
- `get_passwords`: Devuelve las contraseñas introducidas.

#### 🏛 Clase: `SyncDialog`
Diálogo para mostrar diferencias entre dos bases de datos y seleccionar cuáles importar.

**Métodos:**
- `_populate_tabs`: Crea una pestaña por cada tabla con diferencias.
- `get_selected_changes`: Recopila todos los elementos marcados por el usuario para ser importados.

#### 🏛 Clase: `SeleccionarHojasExcelDialog`
Diálogo para que el usuario elija qué hojas incluir en el informe Excel.

**Métodos:**
- `get_opciones`: Devuelve un diccionario con las opciones seleccionadas.

#### 🏛 Clase: `MultiWorkerSelectionDialog`
Diálogo para seleccionar múltiples trabajadores de una lista.

**Métodos:**
- `get_selected_workers`: Devuelve una lista con los nombres de los trabajadores seleccionados.

---

# Detalles de UI: widgets

## <a name='uiwidgetscalculatetimeswidgetpy'></a> 📄 ui/widgets/calculate_times_widget.py

### Clases

#### 🏛 Clase: `CalculateTimesWidget`
Widget para la pantalla de cálculo de tiempos de fabricación.

**Métodos:**
- `add_step_to_pila`: Añade un paso (tarea/preproceso) a la pila manualmente.

---

## <a name='uiwidgetsdashboardwidgetpy'></a> 📄 ui/widgets/dashboard_widget.py

### Clases

#### 🏛 Clase: `DashboardWidget`
Widget para mostrar gráficos y estadísticas de producción.

**Métodos:**
- `set_controller`: Asigna el controlador al widget.
- `setup_ui`: Configura la interfaz del dashboard.
- `_create_chart_view`: Función auxiliar para crear un QChartView con un título.
- `update_machine_usage`: Actualiza el gráfico de uso de máquinas.
- `update_worker_load`: Actualiza el gráfico de carga de trabajo.
- `update_problematic_components`: Actualiza el gráfico de componentes problemáticos.
- `update_monthly_activity`: Actualiza el nuevo gráfico de actividad mensual.

---

## <a name='uiwidgetsfabricationswidgetpy'></a> 📄 ui/widgets/fabrications_widget.py

### Descripción General
Nombre del Módulo: FabricationsWidget
Descripción: Componente de interfaz para la gestión (CRUD) de órdenes de fabricación y preprocesos.

### Clases

#### 🏛 Clase: `FabricationsWidget`
Widget específico para la gestión de Fabricaciones (CRUD).

**Métodos:**
- `__init__`: Inicializa el widget de fabricaciones.  Args:     controller: Controlador que gestiona la lógica de fabricaciones.
- `update_fabrications_table`: Bridge method para compatibilidad con FabricacionManager.

---

## <a name='uiwidgetsgestiondatoswidgetpy'></a> 📄 ui/widgets/gestion_datos_widget.py

### Clases

#### 🏛 Clase: `GestionDatosWidget`
Widget unificado que contiene pestañas para gestionar los datos
principales de la aplicación.


---

## <a name='uiwidgetshelpwidgetpy'></a> 📄 ui/widgets/help_widget.py

### Clases

#### 🏛 Clase: `HelpWidget`
Widget para mostrar la página de ayuda 'Cómo Funciona'.


---

## <a name='uiwidgetshistorialwidgetpy'></a> 📄 ui/widgets/historial_widget.py

### Clases

#### 🏛 Clase: `HistorialWidget`
Widget para la nueva sección de historial de iteraciones y fabricaciones.


---

## <a name='uiwidgetshomewidgetpy'></a> 📄 ui/widgets/home_widget.py

### Clases

#### 🏛 Clase: `HomeWidget`
Widget para la pantalla de inicio.


---

## <a name='uiwidgetsloteswidgetpy'></a> 📄 ui/widgets/lotes_widget.py

### Clases

#### 🏛 Clase: `DefinirLoteWidget`
Widget para crear y editar plantillas de Lote.

**Métodos:**
- `populate_fabrications_list`: Obtiene todas las fabricaciones y llena la lista, excluyendo las tareas generadas automáticamente.
- `filter_fabrications`: Filtra la lista de fabricaciones según el texto ingresado.
- `populate_products_list`: Obtiene todos los productos y llena la lista.
- `filter_products`: Filtra la lista de productos según el texto ingresado.

#### 🏛 Clase: `LotesWidget`
Widget específico para editar y visualizar las plantillas de Lote.


---

## <a name='uiwidgetsmachineswidgetpy'></a> 📄 ui/widgets/machines_widget.py

### Clases

#### 🏛 Clase: `MachinesWidget`
Widget para gestionar la base de datos de máquinas (CRUD).

**Métodos:**
- `__init__`: Inicializa el widget de máquinas y sus dependencias (DI).  Args:     controller: Controlador opcional (obsoleto, usa DIContainer).

---

## <a name='uiwidgetsprepstepswidgetpy'></a> 📄 ui/widgets/prep_steps_widget.py

### Clases

#### 🏛 Clase: `PrepStepsWidget`
Widget para gestionar la base de datos de fases de preparación (CRUD).

**Métodos:**
- `set_controller`: Asigna el controlador al widget.
- `load_preprocesos_data`: Carga los datos de los preprocesos en la lista.
- `clear_details_area`: Limpia el panel de detalles.
- `_create_form_widgets`: Crea la estructura del formulario de detalles.

---

## <a name='uiwidgetspreprocesoswidgetpy'></a> 📄 ui/widgets/preprocesos_widget.py

### Clases

#### 🏛 Clase: `PreprocesosWidget`
Widget rediseñado para la gestión de Preprocesos.
Muestra una lista a la izquierda y los detalles del seleccionado a la derecha.


---

## <a name='uiwidgetsproductiterationswidgetpy'></a> 📄 ui/widgets/product/iterations_widget.py

### Clases

#### 🏛 Clase: `ProductIterationsWidget`
Widget especializado en la gestión del Historial de Iteraciones e imágenes de un producto.


---

## <a name='uiwidgetsproductmaterialswidgetpy'></a> 📄 ui/widgets/product/materials_widget.py

### Clases

#### 🏛 Clase: `ProductMaterialsWidget`
Widget especializado en la gestión de la Lista de Materiales (Componentes) de un producto.

**Métodos:**
- `load_data`: Carga la lista de materiales del producto en la tabla.

---

## <a name='uiwidgetsproductionflowdefinecontrolpanelpy'></a> 📄 ui/widgets/production_flow/define_control_panel.py

### Clases

#### 🏛 Clase: `DefineControlPanel`
Panel de control lateral para añadir y editar pasos en el flujo de producción.
Encapsula la interfaz de configuración de tareas, condiciones de inicio y recursos.

**Métodos:**
- `get_form_data`: Recoge todos los datos configurados en el panel.
- `populate_form`: Puebla el formulario con datos de un paso existente.

---

## <a name='uiwidgetsproductionflowflowcanvaspy'></a> 📄 ui/widgets/production_flow/flow_canvas.py

### Clases

#### 🏛 Clase: `CardWidget`
Una tarjeta visual y MOVIBLE que representa una tarea en el canvas.
Emite 'clicked' al ser seleccionada y 'moved' al ser movida.

**Métodos:**
- `mousePressEvent`: Se activa al hacer clic en la tarjeta.
- `mouseMoveEvent`: Se activa al mover el ratón mientras se mantiene presionado.
- `mouseReleaseEvent`: Se activa al soltar el botón del ratón.
- `_snap_to_grid`: Ajusta la posición de la tarjeta al punto más cercano de la cuadrícula.
- `set_selected`: Marca visualmente la tarjeta como seleccionada.
- `set_highlighted`: Resalta la tarjeta con un color específico (para dependencias/relaciones). Si highlighted es False, restaura el estilo base (o seleccionado si lo estuviera).
- `update_workers`: Actualiza la visualización de los trabajadores asignados via tooltip o icono.

#### 🏛 Clase: `ProductionFlowCanvas`
Canvas desacoplado del flujo de produccion: rejilla en el propio widget y **capa hija** transparente
que pinta flechas encima de las tarjetas (`FlowConnectionPainter`). No confundir con `CanvasWidget` legacy del dialogo.

**Métodos:**
- `set_connections`: Normaliza conexiones (`CanvasVisualConnection` o dicts) y redibuja la capa de conexiones.
- `add_task_widget`: Registra `FlowCardWidget`, conecta señales y mantiene la capa al frente.
- `clear_widgets`: Elimina tarjetas y conexiones.
- `mousePressEvent`: Clic en fondo (ignora la capa transparente) para `backgroundClicked`.

---

## <a name='uiwidgetsproductionflowflowgraphmanagerpy'></a> 📄 ui/widgets/production_flow/flow_graph_manager.py

### Clases

#### 🏛 Clase: `FlowGraphManager`
Coordina presenter y `ProductionFlowCanvas`; escucha `cardSelected` / `cardMoved`. Las aristas se obtienen con
`canvas_state_all_logical_connections` y se envian al canvas con `set_connections`; con seleccion, resalta tarjetas relacionadas.

**Métodos:**
- `add_task_widget`: Crea un widget para una tarea y lo sincroniza con el presenter.
- `load_from_flow`: Reconstruye el canvas y el estado lógico desde datos de flujo.
- `remove_task_widget`: Elimina el widget y actualiza el estado lógico.
- `clear`: Limpia todo el canvas y el estado.
- `select_task`: Marca visualmente una tarea como seleccionada y actualiza relaciones.
- `update_connections`: Calcula y dibuja las conexiones basadas en el estado lógico.
- `apply_mother_effect`: Aplica o quita el efecto de GoldenGlowEffect.
- `update_all_cycle_effects`: Sincroniza todos los efectos de ciclo intermedios y finales.
- `highlight_processing_task`: Aplica el efecto azul de simulación.
- `clear_simulation_effects`: Limpia todos los efectos de resaltado de procesamiento.
- `synchronize_positions`: Sincroniza las posiciones de los widgets con el estado del presenter.
- `_on_card_selected`: Busca el índice basado en el ID y emite la señal.
- `_on_card_moved`: Redibuja conexiones al mover.

---

## <a name='uiwidgetsproductionflowinspectorpanelpy'></a> 📄 ui/widgets/production_flow/inspector_panel.py

### Clases

#### 🏛 Clase: `ProductionTaskInspector`
Panel lateral para inspeccionar y editar las propiedades de una tarea
seleccionada en el flujo de producción.

**Métodos:**
- `_init_ui`: Inicializa la interfaz gráfica del inspector.
- `_toggle_start_widgets`: Habilita/deshabilita widgets según el modo seleccionado.
- `_emit_change`: Emite la señal de cambio si hay una tarea activa.
- `_toggle_form`: Muestra u oculta el formulario del inspector y el placeholder.
- `get_selected_assigned_worker`: Devuelve el nombre del trabajador asignado seleccionado, o None.
- `set_task`: Carga una tarea en el inspector.  Args:     task_data (dict): Datos de la tarea (configuración).     all_tasks (list): Lista de todas las tareas para llenar dependencias.     machines (list): Lista de máquinas disponibles.     available_workers (list): Lista de nombres de todos los trabajadores.
- `clear`: Limpia el inspector ocultando el formulario y mostrando el placeholder.

---

## <a name='uiwidgetsproductionflowinspectorpresenterpy'></a> 📄 ui/widgets/production_flow/inspector_presenter.py

### Clases

#### 🏛 Clase: `InspectorPresenter`
**Métodos:**
- `set_task`: Stores the current task data and possible workers.
- `get_workers_lists`: Returns (assigned_worker_names, available_worker_names).
- `assign_workers`: Given a list of worker names to assign, returns the new full assigned workers list.
- `unassign_workers`: Given a list of worker names to unassign, returns the new assigned workers list.
- `build_dependency_list`: Returns a list of (display text, index/id) for the dependency combo boxes. Ignores the current task itself.

---

## <a name='uiwidgetsproductionflowlibrarypanelpy'></a> 📄 ui/widgets/production_flow/library_panel.py

### Clases

#### 🏛 Clase: `TaskLibraryPanel`
Panel lateral que muestra la biblioteca de tareas disponibles agrupadas por producto.
Permite arrastrar tareas al canvas.

**Métodos:**
- `_on_item_double_clicked`: Maneja el doble clic para emitir la señal con los datos de la tarea.
- `populate_tasks`: Rellena el árbol con los datos de tareas agrupados por producto.
- `set_canvas_tasks`: Actualiza la lista de IDs de tareas que están en el canvas para dar feedback visual.
- `update_visual_state`: Colorea las tareas que ya están en el canvas.

---

## <a name='uiwidgetsproductswidgetpy'></a> 📄 ui/widgets/products_widget.py

### Clases

#### 🏛 Clase: `AddProductWidget`
Widget para añadir un nuevo producto con formulario dinámico.


#### 🏛 Clase: `ProductsWidget`
Widget para editar y visualizar Productos.


---

## <a name='uiwidgetsreporteswidgetpy'></a> 📄 ui/widgets/reportes_widget.py

### Descripción General
========================================================================
REPORTES WIDGET - Módulo Principal de Reportes de Producción
========================================================================
Widget principal que integra los componentes de búsqueda inteligente,
lista de órdenes de fabricación y gráficas de análisis.

Estructura:
- Panel Izquierdo: Búsqueda inteligente
- Panel Derecho Superior: Lista de órdenes de fabricación
- Panel Derecho Inferior: Gráficas y análisis
========================================================================

### Clases

#### 🏛 Clase: `ReportesWidget`
Widget principal para el módulo de Reportes de Producción.

Integra búsqueda inteligente, lista de órdenes y gráficas de análisis.

**Datos (2026-04):** si `controller.container` tiene `ReportService` registrado, se pasa a `SmartSearchWidget`, `OrderListWidget` y `ReportsChartsWidget`; órdenes y gráficas usan `controller=AppController` y priorizan el servicio sobre `controller.model`.

**Métodos:**
- `__init__`: Inicializa el widget de reportes.  Args:     controller: Controlador de la aplicación
- `_setup_ui`: Configura la interfaz de usuario.
- `_connect_signals`: Conecta las señales entre widgets.
- `_on_search_result_selected`: Maneja la selección de un resultado de búsqueda.  Args:     tipo: 'producto' o 'orden'     codigo: Código del elemento seleccionado
- `_on_search_cleared`: Maneja el evento de búsqueda limpiada.
- `_on_order_selected`: Maneja la selección de una orden de fabricación.  Args:     orden_fabricacion: Identificador de la orden
- `set_controller`: Establece el controlador para todos los sub-widgets.  Args:     controller: Controlador de la aplicación
- `refresh`: Refresca el contenido del widget.

---

## <a name='uiwidgetsreportschartscontainerpy'></a> 📄 ui/widgets/reports/charts_container.py

### Descripción General
========================================================================
CHARTS CONTAINER WIDGET - Contenedor de Gráficas de Análisis
========================================================================
Widget contenedor que muestra múltiples gráficas de análisis para
un producto seleccionado: tiempo promedio, evolución temporal,
tiempos por trabajador y patrón de incidencias.
========================================================================

### Clases

#### 🏛 Clase: `StatCard`
Tarjeta de estadística individual.


#### 🏛 Clase: `ReportsChartsWidget`
Widget contenedor para las gráficas de análisis.
Muestra estadísticas y gráficas para un producto seleccionado.

**Datos (2026-04):** parámetro opcional `report_service=`; `set_report_service` al actualizar el controlador.

**Métodos:**
- `_setup_ui`: Configura la interfaz.
- `_create_placeholder_tabs`: Crea tabs con placeholders.
- `update_charts`: Actualiza todas las gráficas para un producto.  Args:     producto_codigo: Código del producto
- `_update_stats_cards`: Actualiza las tarjetas de estadísticas.
- `_update_evolution_chart`: Actualiza la gráfica de evolución temporal.
- `_update_workers_chart`: Actualiza la gráfica de tiempos por trabajador.
- `_update_incidents_chart`: Actualiza la gráfica de incidencias (pie chart).
- `set_controller`: Establece el controlador.
- `clear`: Limpia el widget.

---

## <a name='uiwidgetsreportsorderlistpy'></a> 📄 ui/widgets/reports/order_list.py

### Descripción General
========================================================================
ORDER LIST WIDGET - Widget de Lista de Órdenes de Fabricación
========================================================================
Widget que muestra las órdenes de fabricación de un producto,
con información resumida y opción de expandir para ver detalles.
========================================================================

### Clases

#### 🏛 Clase: `OrderCard`
Tarjeta individual para mostrar resumen de una orden de fabricación.

**Métodos:**
- `__init__`: Args:     order_data: OrdenFabricacionResumenDTO
- `_setup_ui`: Configura la interfaz de la tarjeta.
- `mousePressEvent`: Emite señal al hacer clic.

#### 🏛 Clase: `OrderListWidget`
Widget que muestra lista de órdenes de fabricación.

Signals:
    order_selected(str): Emitido cuando se selecciona una orden.

**Datos (2026-04):** `report_service=` opcional; `set_report_service`.

**Métodos:**
- `_setup_ui`: Configura la interfaz del widget.
- `load_orders_for_product`: Carga las órdenes de fabricación de un producto.  Args:     producto_codigo: Código del producto
- `_display_orders`: Muestra las órdenes en tarjetas.
- `_clear_cards`: Elimina todas las tarjetas.
- `_on_order_clicked`: Maneja clic en una orden.
- `set_controller`: Establece el controlador.
- `clear`: Limpia el widget.

---

## <a name='uiwidgetsreportssmartsearchpy'></a> 📄 ui/widgets/reports/smart_search.py

### Clases

#### 🏛 Clase: `SmartSearchWidget`
Widget de búsqueda inteligente que ofrece autocompletado y
filtrado en tiempo real para el módulo de reportes.

**Métodos:**
- `_on_text_changed`: Maneja el cambio de texto con debounce.
- `_perform_search`: Ejecuta la búsqueda contra `ReportService` (si está configurado) o el fallback `app_model`.
- `_update_results_list`: Actualiza la lista visual de resultados.
- `_on_item_clicked`: Maneja el clic en un resultado.
- `clear_search`: Limpia el campo de búsqueda y resultados.
- `set_controller`: Actualiza el modelo desde el controlador.

---

## <a name='uiwidgetssettingswidgetpy'></a> 📄 ui/widgets/settings_widget.py

### Clases

#### 🏛 Clase: `SettingsWidget`
Widget para la página de Configuración.

**Métodos:**
- `__init__`: Inicializa el widget de configuración general.  Args:     controller: Controlador opcional (obsoleto, usa DIContainer).
- `_on_edit_break`: Edita el descanso seleccionado.
- `_on_remove_break`: Elimina el descanso seleccionado.
- `_on_add_holiday`: Añade el día seleccionado a la lista de festivos.
- `_on_remove_holiday`: Elimina el día seleccionado de la lista de festivos.
- `_highlight_holidays`: Marca los días festivos en el calendario con color rojo.
- `set_controller`: Set fallback controller dynamically (used in some contexts/tests).

---

## <a name='uiwidgetstimelinewidgetpy'></a> 📄 ui/widgets/timeline_widget.py

### Clases

#### 🏛 Clase: `TimelineVisualizationWidget`
Widget que dibuja un diagrama de Gantt interactivo y detallado.


#### 🏛 Clase: `TaskAnalysisPanel`
Widget que muestra el detalle de una tarea seleccionada.


---

## <a name='uiwidgetsworkerswidgetpy'></a> 📄 ui/widgets/workers_widget.py

### Clases

#### 🏛 Clase: `WorkersWidget`
Widget para gestionar la base de datos de trabajadores (CRUD).

**Métodos:**
- `show_incidences_dialog`: Muestra un diálogo con el detalle de las incidencias.

---

