# =================================================================================
# ui/dialogs.py
# Contiene todas las clases de Diálogos personalizados para la aplicación.
# =================================================================================
import os
import logging
from datetime import datetime, date, timedelta, time
from time_calculator import CalculadorDeTiempos
import math
import uuid # Importado para ID único
import copy # Importado para copias profundas

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QDialogButtonBox, QListWidget,
    QListWidgetItem, QLabel, QCheckBox, QScrollArea,
    QWidget, QTableWidget, QTableWidgetItem, QSpinBox,
    QMessageBox, QComboBox, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QDateEdit, QRadioButton, QButtonGroup,
    QFrame, QSizePolicy, QPlainTextEdit, QTabWidget,
    QHeaderView, QAbstractItemView, QTimeEdit, QApplication,
    QCompleter, QInputDialog, QFileDialog, QCalendarWidget,
    QGroupBox, QStackedWidget, QDateTimeEdit, QTreeWidgetItemIterator,
)

from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QDate, QTimer, QTime, QPoint, QRectF
from PyQt6.QtGui import (
    QFont, QPixmap, QPainter, QColor, QBrush, QTextCharFormat, QIcon, QPen, QPalette,
    QPolygonF
)


# --- Split Dialogs Imports ---
from ui.dialogs.canvas_widgets import CanvasWidget, CardWidget
from ui.dialogs.visual_effects import GoldenGlowEffect, GreenCycleEffect, MixedGoldGreenEffect, SimulationProgressEffect



class DefineProductionFlowDialog(QDialog):
    """Diálogo para definir la secuencia de tareas, dependencias y trabajadores."""

    def __init__(self, tasks_data, workers, units, controller, schedule_config, parent=None, existing_flow=None):
        super().__init__(parent)
        self.schedule_config = schedule_config
        self.setWindowTitle("Definir Pila de Producción")
        self.setMinimumSize(1100, 700)

        self.tasks_data = tasks_data
        self.workers = sorted(workers)
        self.units = units
        self.controller = controller
        self.logger = logging.getLogger("EvolucionTiemposApp")

        self.task_data_by_product = self._prepare_task_data()
        self.production_flow = []
        self.editing_index = None
        self.flow_item_widgets = []

        # Widgets que se crean aquí para ser usados en ambos paneles
        self.worker_dependency_radio = QRadioButton("Depende de un trabajador")
        self.worker_dependency_menu = QComboBox()
        self.worker_dependency_menu.addItems(self.workers)

        # --- LÓGICA DE PANELES (SIMPLIFICADA) ---
        left_panel = self._create_add_and_edit_panel()
        right_panel = self._create_right_panel()

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        # --- CONEXIONES DE SEÑALES ---
        self.task_tree.currentItemChanged.connect(self._on_task_selected)
        self.add_update_button.clicked.connect(self._add_or_update_step)
        self.start_date_radio.toggled.connect(self._toggle_start_condition)
        self.dependency_radio.toggled.connect(self._toggle_start_condition)
        self.worker_dependency_radio.toggled.connect(self._toggle_start_condition)
        self.machine_menu.currentIndexChanged.connect(self._on_machine_selected)
        self.cancel_edit_button.clicked.connect(self._reset_form)
        self.save_flow_button.clicked.connect(self._on_save_flow)

        # --- LÓGICA DE CARGA INICIAL ---
        # Si se proporciona un flujo existente, el diálogo se poblará con él.
        if existing_flow:
            self._populate_from_flow(existing_flow)
        # Si no, se inicializa como un diálogo vacío.
        else:
            self._update_previous_task_menu()
            self._toggle_start_condition()
            self._update_flow_display()
            self._on_task_selected()

    def _populate_from_flow(self, flow_data):
        """Carga el diálogo con los datos de un flujo de producción existente."""
        self.logger.info(f"Poblando diálogo con {len(flow_data)} pasos existentes.")
        self.production_flow = flow_data

        # Actualizamos la visualización del panel derecho inmediatamente
        self._update_flow_display()
        # Actualizamos el menú de dependencias para que todos los pasos estén disponibles
        self._update_previous_task_menu()
        # Reseteamos el formulario izquierdo a su estado inicial
        self._reset_form()
        self.setWindowTitle("Editar Pila de Producción")

    def _create_add_and_edit_panel(self):
        panel = QFrame()
        layout = QVBoxLayout(panel)

        self.edit_info_label = QLabel("<b>Añadir Nuevo Paso a la Pila</b>")
        font = self.edit_info_label.font()
        font.setPointSize(12)
        self.edit_info_label.setFont(font)
        layout.addWidget(self.edit_info_label)

        # --- SECCIÓN 1: Selección de Tarea (sin cambios) ---
        layout.addWidget(QLabel("<b>1. Tarea Base</b>"))
        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderLabel("Productos y Tareas de la Fabricación")
        for product_code, product_info in self.task_data_by_product.items():
            product_item = QTreeWidgetItem(self.task_tree, [f"{product_info['descripcion']} ({product_code})"])
            product_font = product_item.font(0);
            product_font.setBold(True)
            product_item.setFont(0, product_font)
            product_item.setFlags(product_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            for task in product_info['tasks']:
                task_item = QTreeWidgetItem(product_item, [f"({task['department']}) {task['name']}"])
                task_item.setData(0, Qt.ItemDataRole.UserRole, task)
            product_item.setExpanded(True)
        layout.addWidget(self.task_tree, 1)

        # --- SECCIÓN 2: Condiciones ---
        layout.addWidget(QLabel("<b>2. Condición de Inicio</b>"))

        # Radio button: Fecha específica
        self.start_date_radio = QRadioButton("Iniciar en fecha específica")
        self.start_date_radio.setChecked(True)
        layout.addWidget(self.start_date_radio)
        self.start_date_entry = QDateEdit(QDate.currentDate())
        layout.addWidget(self.start_date_entry)

        # Radio button: Depende de tarea previa
        self.dependency_radio = QRadioButton("Depende de tarea previa")
        layout.addWidget(self.dependency_radio)

        # ComboBox para seleccionar la tarea predecesora
        dep_task_layout = QHBoxLayout()
        dep_task_layout.addWidget(QLabel("Tarea predecesora:"))
        self.previous_task_menu = QComboBox()
        dep_task_layout.addWidget(self.previous_task_menu)
        layout.addLayout(dep_task_layout)

        # ✅ NUEVO: Campo para unidades mínimas del predecesor
        min_pred_layout = QHBoxLayout()
        min_pred_label = QLabel("Esperar a que complete (unidades):")
        min_pred_label.setToolTip(
            "¿Cuántas unidades debe completar la tarea predecesora "
            "antes de que ESTA tarea pueda empezar?\n\n"
            "Ejemplo: Si pones 5, esta tarea empezará cuando el "
            "predecesor termine su unidad 5."
        )
        self.min_predecessor_units_entry = QLineEdit("1")
        self.min_predecessor_units_entry.setMaximumWidth(80)
        self.min_predecessor_units_entry.setPlaceholderText("1")
        min_pred_layout.addWidget(min_pred_label)
        min_pred_layout.addWidget(self.min_predecessor_units_entry)
        min_pred_layout.addStretch()
        layout.addLayout(min_pred_layout)

        # Campo para las unidades de ESTA tarea
        units_layout = QHBoxLayout()
        units_label = QLabel("Unidades a producir de ESTA tarea:")
        units_label.setToolTip(
            "¿Cuántas unidades de esta tarea se deben fabricar en total?\n\n"
            "Ejemplo: Si pones 36, se fabricarán 36 unidades de esta tarea."
        )
        self.trigger_units_entry = QLineEdit(str(self.units))
        self.trigger_units_entry.setMaximumWidth(80)
        units_layout.addWidget(units_label)
        units_layout.addWidget(self.trigger_units_entry)
        units_layout.addStretch()
        layout.addLayout(units_layout)

        # Radio button: Depende de trabajador
        self.worker_dependency_radio = QRadioButton("Depende de trabajador disponible")
        layout.addWidget(self.worker_dependency_radio)
        self.worker_dependency_menu = QComboBox()
        layout.addWidget(self.worker_dependency_menu)

        # Conectar señales para habilitar/deshabilitar campos
        self.start_date_radio.toggled.connect(self._toggle_start_condition)
        self.dependency_radio.toggled.connect(self._toggle_start_condition)
        self.worker_dependency_radio.toggled.connect(self._toggle_start_condition)

        # --- SECCIÓN 3: Recursos ---
        layout.addWidget(QLabel("<b>3. Recursos Asignados</b>"))
        self.resource_layout = QFormLayout()
        self.machine_menu = QComboBox()
        self.resource_layout.addRow("Máquina:", self.machine_menu)
        layout.addLayout(self.resource_layout)

        # Widgets para los Pasos de Preparación (RESTAURADOS)
        self.prep_steps_label = QLabel("Fases de Preparación para esta Tarea:")
        self.prep_steps_scroll = QScrollArea()
        self.prep_steps_scroll.setWidgetResizable(True)
        self.prep_steps_container = QWidget()
        self.prep_steps_layout = QVBoxLayout(self.prep_steps_container)
        self.prep_steps_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.prep_steps_scroll.setWidget(self.prep_steps_container)
        self.prep_steps_checkboxes = []
        layout.addWidget(self.prep_steps_label)
        layout.addWidget(self.prep_steps_scroll, 1)

        # Selector de trabajadores
        layout.addWidget(QLabel("Trabajadores:"))
        worker_scroll = QScrollArea()
        worker_scroll.setWidgetResizable(True)
        worker_widget = QWidget()
        worker_layout = QVBoxLayout(worker_widget)
        worker_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.worker_checkboxes = {}
        for worker in self.workers:
            cb = QCheckBox(worker)
            self.worker_checkboxes[worker] = cb
            worker_layout.addWidget(cb)
        worker_scroll.setWidget(worker_widget)
        layout.addWidget(worker_scroll)

        # --- SECCIÓN 4: Botones de Acción ---
        self.add_update_button = QPushButton("Añadir a la Pila ▼")
        self.cancel_edit_button = QPushButton("Cancelar Edición")
        self.cancel_edit_button.setVisible(False)  # Oculto por defecto

        action_button_layout = QHBoxLayout()
        action_button_layout.addWidget(self.cancel_edit_button)
        action_button_layout.addStretch()
        action_button_layout.addWidget(self.add_update_button)
        layout.addLayout(action_button_layout)

        return panel

    def _on_save_flow(self):
        """Gestiona el guardado de un flujo de producción sin calcular."""
        if not self.production_flow:
            QMessageBox.warning(self, "Flujo Vacío", "No hay pasos en el flujo para guardar.")
            return

        # Reutilizamos el diálogo de guardado para pedir nombre y descripción
        dialog = SavePilaDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nombre, descripcion = dialog.get_data()
            if not nombre:
                QMessageBox.warning(self, "Nombre Requerido",
                                    "El nombre de la pila es obligatorio para poder guardarla.")
                return

            # Llamamos a un nuevo método en el controlador para que se encargue de guardar
            self.controller.handle_save_flow_only(nombre, descripcion, self.production_flow)
            QMessageBox.information(self, "Éxito",
                                    f"El flujo de producción '{nombre}' ha sido guardado correctamente.\nPuedes cargarlo más tarde desde la pantalla principal de cálculo.")

    def _prepare_task_data(self):
        structured_data = {}
        for main_task in self.tasks_data:
            product_code = main_task['codigo']
            main_product_info = {
                "code": product_code,
                "desc": main_task.get('descripcion', 'Producto sin descripcion')
            }
            structured_data[product_code] = {"descripcion": main_task['descripcion'], "tasks": []}

            if main_task.get('tiene_subfabricaciones') and main_task.get('sub_partes'):
                for i, sub_task in enumerate(main_task.get('sub_partes', [])):
                    task_name = sub_task.get('descripcion', sub_task.get('name', 'Tarea sin nombre'))

                    duration = 0.0  # Inicializar con un valor por defecto seguro
                    # ✅ CAMBIO CRÍTICO: Buscar en TODAS las claves posibles
                    # 'duration' puede venir de pilas guardadas antiguas
                    for key in ['tiempo', 'tiempo_optimo', 'duration']:
                        if key in sub_task:
                            try:
                                # Comprobar que el valor no sea None ni un string vacío antes de convertir
                                val_str = str(sub_task[key]).strip()
                                if val_str:
                                    val = float(val_str.replace(",", "."))
                                    if val > 0:
                                        duration = val
                                        break  # Salir del bucle en cuanto encontremos un tiempo válido
                            except (ValueError, TypeError):
                                continue  # Si la conversión falla, probar con la siguiente clave

                    if duration <= 0:
                        self.logger.error(
                            f"❌ DIÁLOGO: Tarea '{task_name}' del producto {product_code} sin tiempo válido. "
                            f"Se usará 0.0. Datos de sub-tarea: {sub_task}"
                        )

                    task_id = f"{product_code}_{i}_{task_name.replace(' ', '_')}"
                    self.logger.info(f"🔧 DIÁLOGO construyendo tarea: {task_name}, duration={duration}")

                    structured_data[product_code]['tasks'].append({
                        'id': task_id,
                        'name': task_name,
                        'department': main_task.get('departamento', 'General'),
                        'duration': duration,
                        'tiempo': duration,  # Mantener ambas claves por compatibilidad
                        'original_product_code': product_code,
                        'requiere_maquina_tipo': sub_task.get('requiere_maquina_tipo'),
                        'required_skill_level': sub_task.get('tipo_trabajador', 1),
                        'tipo_trabajador': sub_task.get('tipo_trabajador', 1),
                        'original_product_info': main_product_info,
                        'deadline': main_task.get('deadline'),
                        'fabricacion_id': main_task.get('fabricacion_id')
                    })
        return structured_data

    def _is_task_auto_triggered(self, task_index):
        """
        Verifica si una tarea está configurada para iniciarse automáticamente
        desde otra tarea (es decir, otra tarea tiene a ésta como siguiente).

        Args:
            task_index (int): Índice de la tarea a verificar en self.canvas_tasks.

        Returns:
            tuple: (bool, int|None) - (está_auto_triggered, índice_tarea_predecesora_o_None)
        """
        # Asegurarse de que el índice es válido
        if task_index < 0 or task_index >= len(self.canvas_tasks):
            return (False, None)

        # Iterar sobre todas las tareas para ver si alguna apunta a la tarea 'task_index'
        for i, canvas_task in enumerate(self.canvas_tasks):
            # No puede ser disparada por sí misma
            if i == task_index:
                continue

            config = canvas_task.get('config', {})

            # Verificar si es la siguiente tarea en un ciclo
            next_cyclic = config.get('next_cyclic_task_index')
            if next_cyclic == task_index:
                # Sí, la tarea 'i' apunta a 'task_index' como su siguiente tarea cíclica
                self.logger.debug(f"Tarea {task_index} es auto-trigger (cíclico) desde tarea {i}")
                return (True, i)

            # Verificar si es una dependencia directa (aunque esto no debería desactivar controles)
            # Nota: La lógica original del informe decía que *cualquier* dependencia lo hacía,
            # pero típicamente solo un trigger automático (como un ciclo) debería desactivar controles.
            # Vamos a mantener la lógica del informe por ahora.
            # Si quieres cambiarlo para que solo los ciclos desactiven, comenta el siguiente bloque.
            # start_condition = config.get('start_condition', {})
            # if (start_condition.get('type') == 'dependency' and
            #     start_condition.get('value') == task_index):
            #     # Ojo: Esto significa que la tarea 'i' depende de la 'task_index',
            #     # no al revés como lo interpreté inicialmente.
            #     # La lógica correcta es buscar qué tarea *tiene* a 'task_index' como *hija*.
            #     pass # La dependencia no implica auto-trigger en este sentido

        # Revisión: Necesitamos chequear si 'task_index' *es* hija de alguna tarea 'i'.
        # La lógica de auto-trigger debería venir de la tarea *padre*.
        # Por ahora, solo los ciclos (`next_cyclic_task_index`) realmente *fuerzan*
        # el inicio automático. Una dependencia estándar (`start_condition['type'] == 'dependency'`)
        # solo indica *cuándo* puede empezar, pero no *fuerza* su inicio.
        # Mantendremos la implementación simple enfocada en los ciclos por ahora.

        # Nueva lógica para dependencia estándar: ¿Es 'task_index' el 'value' de la dependencia de otra tarea 'i'?
        current_task_config = self.canvas_tasks[task_index].get('config', {})
        current_start_condition = current_task_config.get('start_condition', {})
        if current_start_condition.get('type') == 'dependency':
            predecessor_index = current_start_condition.get('value')
            if predecessor_index is not None and 0 <= predecessor_index < len(self.canvas_tasks):
                # Esta tarea SÍ tiene una dependencia directa
                self.logger.debug(f"Tarea {task_index} tiene dependencia directa de tarea {predecessor_index}")
                # Según el informe FASE 4, esto debería considerarse auto-triggered
                return (True, predecessor_index)

        # Si no se encontró ninguna tarea que la dispare automáticamente
        return (False, None)

    def _create_right_panel(self):
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("<b>Pila de Producción (Secuencia de Tareas)</b>"))
        # Añadimos un layout horizontal para los botones de acción del flujo
        flow_actions_layout = QHBoxLayout()
        self.group_steps_button = QPushButton("🔗 Agrupar Tareas Seleccionadas")
        self.group_steps_button.clicked.connect(self._group_selected_steps)  # Conectamos la señal
        flow_actions_layout.addStretch()
        flow_actions_layout.addWidget(self.group_steps_button)
        layout.addLayout(flow_actions_layout)
        flow_scroll = QScrollArea();
        flow_scroll.setWidgetResizable(True)
        self.flow_display_widget = QWidget()
        self.flow_display_layout = QVBoxLayout(self.flow_display_widget)
        self.flow_display_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        flow_scroll.setWidget(self.flow_display_widget)
        layout.addWidget(flow_scroll)

        self.save_flow_button = QPushButton("💾 Guardar Flujo (sin calcular)")
        self.save_flow_button.setStyleSheet("background-color: #28a745; color: white; padding: 5px;")
        layout.addWidget(self.save_flow_button)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Confirmar y Calcular")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        return panel

    def _on_machine_selected(self):
        """Se activa al cambiar la máquina. Carga sus fases de preparación asociadas."""
        # Limpiar checkboxes anteriores
        while self.prep_steps_layout.count():
            child = self.prep_steps_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.prep_steps_checkboxes.clear()

        machine_id = self.machine_menu.currentData()
        if machine_id is None:
            self.prep_steps_scroll.setVisible(False)
            self.prep_steps_label.setVisible(False)
            return

        # Pedimos al controlador los grupos de esta máquina para obtener todos sus pasos
        groups_for_machine = self.controller.model.get_groups_for_machine(machine_id)
        all_steps_for_machine = []
        # Ahora usamos atributos DTO: id, nombre, descripcion
        for group in groups_for_machine:
            steps = self.controller.model.get_steps_for_group(group.id)
            all_steps_for_machine.extend(steps)

        if not all_steps_for_machine:
            self.prep_steps_layout.addWidget(QLabel("Esta máquina no tiene fases de preparación asignadas."))
            self.prep_steps_scroll.setVisible(True)
            self.prep_steps_label.setVisible(True)
            return

        # Crear nuevos checkboxes para todos los pasos disponibles en la máquina
        for step in all_steps_for_machine:
            # Ahora usamos atributos DTO: id, nombre, tiempo_fase, descripcion, es_diario
            cb = QCheckBox(f"{step.nombre} ({step.tiempo_fase} min)")
            cb.setProperty("step_id", step.id)  # Guardamos el ID en el widget
            self.prep_steps_layout.addWidget(cb)
            self.prep_steps_checkboxes.append(cb)

        # Lógica de automatización para seleccionar pasos por defecto
        default_group_id = self.machine_menu.property("default_group_id")
        if default_group_id:
            # Ahora usamos atributos DTO: id
            default_step_ids = {step.id for step in self.controller.model.get_steps_for_group(default_group_id)}
            for cb in self.prep_steps_checkboxes:
                if cb.property("step_id") in default_step_ids:
                    cb.setChecked(True)
                    cb.setEnabled(False)
                    cb.setStyleSheet("QCheckBox { color: #005A9C; font-weight: bold; }")

        self.prep_steps_scroll.setVisible(bool(self.prep_steps_checkboxes))
        self.prep_steps_label.setVisible(bool(self.prep_steps_checkboxes))


    def _on_task_selected(self):
        # Desconectar temporalmente para evitar llamadas recursivas o en bucle
        self.machine_menu.blockSignals(True)
        self.machine_menu.clear()

        selected_item = self.task_tree.currentItem()
        is_task = selected_item and selected_item.parent()

        # Obtenemos la fila del QFormLayout que contiene el menú de máquinas
        form_layout = self.resource_layout
        machine_row_index = -1
        for i in range(form_layout.rowCount()):
            if form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole).widget() == self.machine_menu:
                machine_row_index = i
                break

        if machine_row_index == -1:  # Cortafuegos por si no se encuentra
            self.machine_menu.blockSignals(False)
            return

        if not is_task:
            # Si no hay una tarea seleccionada, ocultamos la fila de la máquina
            form_layout.setRowVisible(machine_row_index, False)
            self.machine_menu.blockSignals(False)
            return

        # Si hay una tarea, mostramos la fila
        form_layout.setRowVisible(machine_row_index, True)
        task_info = selected_item.data(0, Qt.ItemDataRole.UserRole)
        tipo_maquina_requerido = task_info.get("requiere_maquina_tipo")
        product_code = task_info.get("original_product_code")

        default_group_id, default_machine_id = self.controller.model.get_prep_info_for_product(product_code)

        if tipo_maquina_requerido:
            self.machine_menu.setEnabled(True)
            available_machines = self.controller.model.get_machines_by_process_type(tipo_maquina_requerido)
            if available_machines:
                self.machine_menu.addItem("--- Seleccione una Máquina ---", userData=None)
                # Ahora usamos atributos DTO: id, nombre
                for machine in available_machines:
                    self.machine_menu.addItem(machine.nombre, userData=machine.id)
            else:
                self.machine_menu.addItem(f"¡No hay máquinas para '{tipo_maquina_requerido}'!", userData=None)
                self.machine_menu.setEnabled(False)

            if default_machine_id:
                index = self.machine_menu.findData(default_machine_id)
                if index != -1:
                    self.machine_menu.setCurrentIndex(index)
                    self.machine_menu.setProperty("default_group_id", default_group_id)
            else:
                self.machine_menu.setProperty("default_group_id", None)
        else:
            self.machine_menu.addItem("Esta tarea no requiere máquina", userData=None)
            self.machine_menu.setEnabled(False)

        # Reconectar y llamar manualmente al slot para cargar las fases de la máquina seleccionada
        self.machine_menu.blockSignals(False)
        # self._on_machine_selected() # Esta llamada puede que ya no sea necesaria aquí

    def _add_or_update_step(self):
        # 1. Obtener la información de la tarea base (CORREGIDO)
        # Se añade una lógica para diferenciar entre modo edición y modo añadir.
        task_info = None
        if self.editing_index is not None:
            # MODO EDICIÓN: La tarea no se puede cambiar. La obtenemos del paso que ya estamos editando.
            self.logger.debug(f"Modo edición para el paso índice {self.editing_index}.")
            task_info = self.production_flow[self.editing_index]['task']
        else:
            # MODO AÑADIR: La tarea se obtiene del árbol de selección de la izquierda.
            self.logger.debug("Modo añadir nuevo paso.")
            selected_item = self.task_tree.currentItem()
            if not selected_item or not selected_item.parent():
                QMessageBox.warning(self, "Selección Requerida",
                                    "Debe seleccionar una tarea específica de un producto para añadirla a la pila.")
                return
            task_info = selected_item.data(0, Qt.ItemDataRole.UserRole)

        # 2. Recoger el resto de datos del formulario (trabajadores, máquina, dependencias)
        selected_workers = [worker for worker, cb in self.worker_checkboxes.items() if cb.isChecked()]

        machine_id = self.machine_menu.currentData()
        if task_info.get("requiere_maquina_tipo") and machine_id is None:
            QMessageBox.warning(self, "Error", "Debe asignar una máquina disponible para esta tarea.")
            return

        # ✅ Inicializar variables por defecto
        start_date = None
        previous_task_index = None
        trigger_units = self.units
        min_pred_units = None
        depends_on_worker = None

        # ✅ CORRECCIÓN: Indentación correcta de los elif
        if self.start_date_radio.isChecked():
            start_date = self.start_date_entry.date().toPyDate()
        elif self.dependency_radio.isChecked():
            if self.previous_task_menu.count() == 0 or self.previous_task_menu.currentIndex() == -1:
                QMessageBox.warning(self, "Error", "Debe seleccionar una tarea previa válida como dependencia.")
                return
            previous_task_index = self.previous_task_menu.currentData()

            # Validar unidades de ESTA tarea
            try:
                trigger_units_val = int(self.trigger_units_entry.text())
                if not (0 < trigger_units_val <= self.units):
                    raise ValueError("Unidades fuera de rango")
                trigger_units = trigger_units_val
            except ValueError:
                QMessageBox.warning(self, "Error",
                                    f"Las unidades a producir deben ser un número entre 1 y {self.units}.")
                return

            # ✅ NUEVO: Validar unidades mínimas del predecesor
            try:
                min_pred_units = int(self.min_predecessor_units_entry.text())
                if min_pred_units < 1:
                    raise ValueError("Debe ser al menos 1")
            except ValueError:
                QMessageBox.warning(self, "Error",
                                    "Las unidades mínimas del predecesor deben ser un número positivo.")
                return
        elif self.worker_dependency_radio.isChecked():
            depends_on_worker = self.worker_dependency_menu.currentText()

        # 3. Construir el diccionario de datos del paso
        step_data = {
            "task": task_info,
            "workers": selected_workers,
            "start_date": start_date,
            "previous_task_index": previous_task_index,
            "trigger_units": trigger_units,
            "min_predecessor_units": min_pred_units,  # ✅ Ya no usa condicional, siempre incluye (None si no aplica)
            "machine_id": machine_id,
            "selected_prep_steps": [],
            "depends_on_worker": depends_on_worker
        }

        # 4. Decidir si actualizar o añadir
        if self.editing_index is not None:
            # MODO EDICIÓN: Sobrescribimos el paso existente
            self.production_flow[self.editing_index] = step_data
        else:
            # MODO AÑADIR: Añadimos un nuevo paso al final
            self.production_flow.append(step_data)

        # 5. Refrescar la UI y resetear el formulario al modo "Añadir"
        self._update_flow_display()
        self._reset_form()

    def _update_flow_display(self):
        # Limpiar la vista y la lista de widgets de control
        while self.flow_display_layout.count():
            child = self.flow_display_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.flow_item_widgets = []

        if not self.production_flow:
            self.flow_display_layout.addWidget(QLabel("Añada pasos desde el panel izquierdo..."))
            return

        for i, step in enumerate(self.production_flow):
            # Si el paso es un grupo secuencial
            # Si el paso es un grupo secuencial
            if isinstance(step, dict) and step.get('type') == 'sequential_group':
                group_frame = QFrame()
                group_frame.setFrameShape(QFrame.Shape.StyledPanel)
                group_frame.setStyleSheet("QFrame { border: 2px solid #3498db; border-radius: 5px; }")
                group_layout = QVBoxLayout(group_frame)

                title_layout = QHBoxLayout()

                # Obtener información del grupo
                workers_list = step.get('assigned_workers', [])
                workers_str = ", ".join(workers_list) if workers_list else "Sin asignar"

                metadata = step.get('group_metadata', {})
                task_count = metadata.get('task_count', len(step.get('tasks', [])))
                total_time = metadata.get('total_cycle_time', 0)

                # ========================================================================
                # ✨ NUEVA FUNCIONALIDAD: Mostrar configuración de ciclo dinámico
                # ========================================================================
                units_per_cycle = step.get('units_per_cycle', 1)
                total_cycles = step.get('total_cycles', self.units)

                # Crear el texto descriptivo con la nueva información
                cycle_info = f"{units_per_cycle} uds/ciclo → {total_cycles} ciclos totales"

                group_title = QLabel(
                    f"<b>Grupo Secuencial ({task_count} tareas)</b><br>"
                    f"<small>Trabajadores: {workers_str}</small><br>"
                    f"<small>⏱️ Tiempo/ciclo: {total_time:.1f} min | 🔄 Ciclos: {cycle_info}</small>"
                )
                # ========================================================================

                assign_worker_btn = QPushButton("Asignar Operarios")
                assign_worker_btn.clicked.connect(lambda checked, idx=i: self._assign_worker_to_group(idx))

                title_layout.addWidget(group_title)
                title_layout.addStretch()
                title_layout.addWidget(assign_worker_btn)
                group_layout.addLayout(title_layout)

                for task_in_group in step.get('tasks', []):
                    task_label = QLabel(f" • {task_in_group['task']['name']}")
                    group_layout.addWidget(task_label)

                self.flow_display_layout.addWidget(group_frame)
                self.flow_item_widgets.append({'type': 'group'})
            # Si es una tarea individual
            else:
                step_frame = QFrame()
                step_frame.setFrameShape(QFrame.Shape.StyledPanel)
                step_layout = QHBoxLayout(step_frame)

                checkbox = QCheckBox()
                step_layout.addWidget(checkbox)

                info_widget = QWidget()
                info_layout = QHBoxLayout(info_widget)

                info_text = QVBoxLayout()
                info_text.addWidget(QLabel(f"<b>PASO {i + 1}: {step['task']['name']}</b>"))
                if step.get('machine_id'):
                    all_machines = self.controller.model.get_all_machines(include_inactive=True)
                    # Ahora usamos atributos DTO: id, nombre
                    machine_name = next((m.nombre for m in all_machines if m.id == step['machine_id']), "Desconocida")
                    info_text.addWidget(QLabel(f"Máquina: {machine_name}"))

                # --- INICIO DE LA CORRECCIÓN ---
                # Comprueba si 'workers' es una lista de strings (formato antiguo)
                # o una lista de diccionarios (formato nuevo)
                workers_data = step.get('workers', [])
                if workers_data and isinstance(workers_data[0], dict):
                    # Formato nuevo: extraer el nombre de cada diccionario
                    worker_names = [w.get('name', 'N/A') for w in workers_data]
                    info_text.addWidget(QLabel(f"Trabajadores: {', '.join(worker_names)}"))
                else:
                    # Formato antiguo (o lista vacía): se puede usar join directamente
                    info_text.addWidget(QLabel(f"Trabajadores: {', '.join(workers_data)}"))
                # --- FIN DE LA CORRECCIÓN ---

                start_text = "Condición de inicio no definida"
                if step.get('start_date'):
                    start_text = f"Inicia el: {step['start_date'].strftime('%d/%m/%Y')}"
                elif step.get('previous_task_index') is not None:
                    prev_index = step['previous_task_index']
                    if 0 <= prev_index < len(self.production_flow):
                        parent_step = self.production_flow[prev_index]
                        if parent_step.get('type') == 'sequential_group':
                            parent_name = f"Grupo Secuencial"
                        else:
                            parent_name = parent_step['task']['name']
                        start_text = f"Depende de '{parent_name}' (Tras {step['trigger_units']} uds.)"
                    else:
                        start_text = "<b style='color:red;'>Dependencia Rota (re-asignar)</b>"
                elif step.get('depends_on_worker'):
                    start_text = f"Depende del trabajador: {step['depends_on_worker']}"
                info_text.addWidget(QLabel(start_text))

                info_layout.addLayout(info_text)
                info_layout.addStretch()

                btn_layout = QVBoxLayout()
                edit_btn = QPushButton("✎ Editar")
                delete_btn = QPushButton("🗑 Eliminar")
                edit_btn.clicked.connect(lambda checked, idx=i: self._edit_step(idx))
                delete_btn.clicked.connect(lambda checked, idx=i: self._delete_step(idx))
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(delete_btn)
                info_layout.addLayout(btn_layout)

                step_layout.addWidget(info_widget)
                self.flow_display_layout.addWidget(step_frame)
                self.flow_item_widgets.append({'checkbox': checkbox})

    def _group_selected_steps(self):
        """
        Crea un grupo secuencial a partir de las tareas seleccionadas y, de forma crucial,
        recalcula todos los índices de dependencia para mantener la integridad del flujo.
        MODIFICADO: Ahora captura units_per_cycle para cálculo cíclico dinámico.
        """
        selected_indices = []
        for i, widgets in enumerate(self.flow_item_widgets):
            if 'checkbox' in widgets and widgets['checkbox'].isChecked():
                selected_indices.append(i)

        if len(selected_indices) < 2:
            QMessageBox.warning(self, "Selección Insuficiente",
                                "Debe seleccionar al menos dos tareas para agrupar.")
            return

        if any(selected_indices[i] + 1 != selected_indices[i + 1] for i in range(len(selected_indices) - 1)):
            QMessageBox.warning(self, "Selección no Válida",
                                "Solo puede agrupar tareas que son consecutivas en el flujo.")
            return

        # 1. Usar el nuevo diálogo para seleccionar múltiples trabajadores
        dialog = MultiWorkerSelectionDialog(self.workers, parent=self)
        if not dialog.exec():
            self.logger.info("El usuario canceló la asignación de trabajadores al grupo.")
            return

        selected_workers = dialog.get_selected_workers()
        if not selected_workers:
            QMessageBox.warning(self, "Asignación Requerida", "Debe asignar al menos un trabajador al grupo.")
            return

        # ========================================================================
        # ✨ NUEVA FUNCIONALIDAD: Capturar el tamaño del ciclo dinámico
        # ========================================================================
        units_per_cycle, ok = QInputDialog.getInt(
            self,
            "Configurar Ciclo de Trabajo",
            f"¿Cuántas unidades desea procesar por ciclo?\n\n"
            f"Total de unidades a fabricar: {self.units}\n\n"
            f"Ejemplos:\n"
            f"  • 1 = Trabajo fino (cada unidad se calcula individualmente)\n"
            f"  • 20 = Trabajo estándar (procesa 20 unidades por iteración)\n"
            f"  • {self.units} = Procesar todo de una vez (máxima eficiencia)\n\n"
            f"Unidades por ciclo:",
            value=min(20, self.units),  # Valor por defecto: 20 o el total si es menor
            min=1,
            max=self.units
        )

        if not ok:
            self.logger.info("El usuario canceló la configuración del ciclo.")
            return

        # Calcular cuántos ciclos se generarán con esta configuración
        import math
        total_cycles = math.ceil(self.units / units_per_cycle)

        self.logger.info(
            f"Configuración de ciclo: {units_per_cycle} unidades/ciclo → "
            f"{total_cycles} ciclos totales para {self.units} unidades"
        )
        # ========================================================================

        self.logger.info(f"Agrupando tareas en los índices: {selected_indices}")

        # 2. Crear el nuevo objeto de grupo con información completa preservada
        tasks_to_group = [self.production_flow[i] for i in selected_indices]

        total_time = sum(t['task']['duration'] for t in tasks_to_group)
        total_units_time = sum(t['task'].get('tiempo_optimo', 0) for t in tasks_to_group)

        new_group = {
            "type": "sequential_group",
            "tasks": tasks_to_group,
            "assigned_workers": selected_workers,
            # ✨ NUEVO: Configuración de ciclo dinámico
            "units_per_cycle": units_per_cycle,
            "total_cycles": total_cycles,
            # ========================================
            "group_metadata": {
                "total_cycle_time": total_time,
                "total_optimal_time": total_units_time,
                "task_count": len(tasks_to_group),
                "departments": list(set(t['task'].get('department', '') for t in tasks_to_group))
            }
        }

        # 2b. Configurar dependencias internas del grupo (cadena secuencial)
        for idx in range(len(tasks_to_group)):
            if idx > 0:
                tasks_to_group[idx]['internal_dependency'] = idx - 1
            else:
                tasks_to_group[idx]['internal_dependency'] = None
            tasks_to_group[idx]['belongs_to_group'] = True
            tasks_to_group[idx]['group_position'] = idx

        # 3. Construir un mapa para traducir los índices antiguos a los nuevos
        old_to_new_index_map = {}
        group_insert_index = selected_indices[0]
        for old_index in range(len(self.production_flow)):
            if old_index < group_insert_index:
                old_to_new_index_map[old_index] = old_index
            elif old_index in selected_indices:
                old_to_new_index_map[old_index] = group_insert_index
            else:
                new_idx = old_index - (len(selected_indices) - 1)
                old_to_new_index_map[old_index] = new_idx

        # 4. Reconstruir la lista de la pila de producción
        new_production_flow = []
        new_production_flow.extend(self.production_flow[:group_insert_index])
        new_production_flow.append(new_group)
        new_production_flow.extend(
            step for i, step in enumerate(self.production_flow) if
            i not in selected_indices and i > group_insert_index
        )

        # 5. Actualizar las dependencias en la nueva lista usando el mapa
        for step in new_production_flow:
            if step.get('type') != 'sequential_group' and step.get('previous_task_index') is not None:
                old_dependency_index = step['previous_task_index']
                step['previous_task_index'] = old_to_new_index_map.get(old_dependency_index)

        # 6. Reemplazar la pila antigua por la nueva, ya corregida
        self.production_flow = new_production_flow

        # 7. Refrescar la vista y el formulario
        self._update_flow_display()
        self._reset_form()

    def _assign_worker_to_group(self, group_index):
        """Abre un diálogo para asignar uno o más trabajadores a un grupo."""
        group = self.production_flow[group_index]

        # --- INICIO DE LA MODIFICACIÓN ---
        # Usar el nuevo diálogo, preseleccionando los trabajadores ya asignados
        previously_selected = group.get('assigned_workers', [])
        dialog = MultiWorkerSelectionDialog(self.workers, previously_selected, self)

        if dialog.exec():
            selected_workers = dialog.get_selected_workers()
            if not selected_workers:
                QMessageBox.warning(self, "Asignación Requerida", "Debe asignar al menos un trabajador al grupo.")
                return

            # Actualizamos el diccionario del grupo con la nueva lista de trabajadores
            group['assigned_workers'] = selected_workers
            self.logger.info(f"Asignados los trabajadores {selected_workers} al grupo del índice {group_index}.")

            # Refrescamos toda la vista para que el cambio sea visible
            self._update_flow_display()
        # --- FIN DE LA MODIFICACIÓN ---

    def _reset_form(self):
        self.editing_index = None

        # Restaurar textos y visibilidad de botones
        self.edit_info_label.setText("<b>Añadir Nuevo Paso a la Pila</b>")
        self.add_update_button.setText("Añadir a la Pila ▼")
        self.cancel_edit_button.setVisible(False)
        self.task_tree.setEnabled(True)

        # Limpiar campos
        self.task_tree.clearSelection()
        self.start_date_radio.setChecked(True)
        self.trigger_units_entry.setText(str(self.units))
        for cb in self.worker_checkboxes.values():
            cb.setChecked(False)

        # Actualizar menús y estado de los radio buttons
        self._update_previous_task_menu()
        self._toggle_start_condition()
        self._on_task_selected()  # Esto resetea la máquina

        self.logger.debug("Formulario reseteado al modo 'Añadir Tarea'.")

    def _edit_step(self, index):
        self.editing_index = index
        step_data = self.production_flow[index]

        self.edit_info_label.setText(f"<b>Editando Paso {index + 1}: {step_data['task']['name']}</b>")
        self.add_update_button.setText("✓ Actualizar Paso")
        self.cancel_edit_button.setVisible(True)
        self.task_tree.setEnabled(False)  # Bloqueamos el árbol para no cambiar la tarea base

        # Rellenar formulario con los datos del paso
        # 1. Condiciones de inicio
        if step_data.get('start_date'):
            self.start_date_radio.setChecked(True)
            self.start_date_entry.setDate(step_data['start_date'])
        elif step_data.get('previous_task_index') is not None:
            self.dependency_radio.setChecked(True)
            idx = self.previous_task_menu.findData(step_data['previous_task_index'])
            if idx != -1:
                self.previous_task_menu.setCurrentIndex(idx)
            self.trigger_units_entry.setText(str(step_data.get('trigger_units', self.units)))
            # ✅ NUEVO: Cargar las unidades mínimas del predecesor
            self.min_predecessor_units_entry.setText(
                str(step_data.get('min_predecessor_units', 1))
            )
        elif step_data.get('depends_on_worker'):
            self.worker_dependency_radio.setChecked(True)
            self.worker_dependency_menu.setCurrentText(step_data['depends_on_worker'])
        self._toggle_start_condition()

        # 2. Máquina
        if step_data.get('machine_id'):
            idx = self.machine_menu.findData(step_data['machine_id'])
            if idx != -1:
                self.machine_menu.setCurrentIndex(idx)

        # 3. Trabajadores
        for worker, cb in self.worker_checkboxes.items():
            cb.setChecked(worker in step_data.get('workers', []))

    def _toggle_start_condition(self, checked=True):
        is_date_start = self.start_date_radio.isChecked()
        is_task_dependency = self.dependency_radio.isChecked()
        is_worker_dependency = self.worker_dependency_radio.isChecked()

        # Fecha específica
        self.start_date_entry.setEnabled(is_date_start)

        # Dependencia de tarea
        self.dependency_radio.setEnabled(len(self.production_flow) > 0)
        self.previous_task_menu.setEnabled(is_task_dependency)
        self.min_predecessor_units_entry.setEnabled(is_task_dependency)  # ✅ Solo se habilita con dependencia

        # ✅ CORRECCIÓN: trigger_units SIEMPRE está habilitado
        # Este campo siempre debe estar disponible porque representa las unidades totales de ESTA tarea
        self.trigger_units_entry.setEnabled(True)

        # Dependencia de trabajador
        self.worker_dependency_menu.setEnabled(is_worker_dependency)

        # Si no hay tareas previas, forzar fecha específica
        if not self.production_flow and (is_task_dependency or is_worker_dependency):
            self.start_date_radio.setChecked(True)

    def _update_previous_task_menu(self):
        self.previous_task_menu.clear()

        has_options = False
        for i, step in enumerate(self.production_flow):
            # No podemos depender de nosotros mismos si estamos editando
            if i == self.editing_index:
                continue

            # Comprueba si el 'step' es un grupo o una tarea individual
            if isinstance(step, dict) and step.get('type') == 'sequential_group':
                # Es un grupo, le damos un nombre genérico
                task_name = f"Paso {i + 1}: Grupo Secuencial"
            elif 'task' in step and 'name' in step['task']:
                # Es una tarea individual, usamos la lógica anterior
                task_name = f"Paso {i + 1}: {step['task']['name']}"
            else:
                # Si el formato es inesperado, lo saltamos para evitar un error
                self.logger.warning(f"Se encontró un paso con formato inesperado en el índice {i}. Omitiendo.")
                continue

            self.previous_task_menu.addItem(task_name, i)  # Guardamos el índice real
            has_options = True

        if not has_options:
            self.previous_task_menu.addItem("(No hay tareas previas)")
            self.dependency_radio.setEnabled(False)
        else:
            self.dependency_radio.setEnabled(True)

    def _delete_step(self, index):
        # Advertir si otros pasos dependen de este
        for i, step in enumerate(self.production_flow):
            if step.get('previous_task_index') == index:
                QMessageBox.critical(self, "Error de Dependencia",
                                     f"No se puede eliminar el paso {index + 1} porque el paso {i + 1} ('{step['task']['name']}') depende de él. Elimine primero la dependencia.")
                return

        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"¿Está seguro de que desea eliminar el Paso {index + 1}?")

        if reply == QMessageBox.StandardButton.Yes:
            # Eliminar el paso
            self.production_flow.pop(index)

            # CORRECCIÓN: Recalcular los índices de dependencia de los pasos posteriores
            for step in self.production_flow:
                if step.get('previous_task_index') is not None and step['previous_task_index'] > index:
                    step['previous_task_index'] -= 1

            # Actualizar la UI
            self._update_flow_display()
            self._reset_form()

    def get_production_flow(self):
        return self.production_flow


class EnhancedProductionFlowDialog(QDialog):
    # Señales para comunicación con la simulación
    simulation_processing_task = pyqtSignal(int)  # Emite índice de tarea siendo procesada
    simulation_finished = pyqtSignal()  # Emite cuando termina la simulación

    def __init__(self, tasks_data, workers, units, controller, schedule_config, parent=None, existing_flow=None):
        super().__init__(parent)

        self.setWindowTitle("Planificador de Flujo de Producción Visual")
        self.setWindowState(Qt.WindowState.WindowMaximized)

        # --- Inicialización de datos ---
        self.tasks_data = tasks_data
        self.workers = sorted(workers)
        self.units = units
        self.controller = controller
        self.schedule_config = schedule_config
        self.logger = logging.getLogger("EvolucionTiemposApp")

        self.production_flow = []
        self.canvas_tasks = []
        self.selected_canvas_task_index = None
        self.inspector_widgets = {}
        self._create_inspector_widgets()  # Crea los widgets pero no los añade al layout aún
        self.task_data_by_product = self._prepare_task_data()
        self.tasks_in_canvas = {}  # Para Fase 2 y 6

        # NUEVO: Diccionario para rastrear efectos de simulación (Fase 8.1)
        self.simulation_effects = {}

        # ✨ NUEVO: Label flotante para mensajes de simulación
        self.simulation_message_label = None

        # --- Layout Principal ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        content_layout = QHBoxLayout()
        library_panel = self._create_library_panel()
        canvas_panel = self._create_canvas_panel()

        # El inspector ya no se añade aquí permanentemente
        self.inspector_panel_widget = self._create_inspector_panel()  # Guardamos la referencia
        self.inspector_panel_widget.setParent(None)  # Inicialmente sin padre (oculto)
        self.inspector_is_visible = False  # Flag para rastrear visibilidad (Fase 7)

        content_layout.addWidget(library_panel, 1)  # Panel izquierdo
        content_layout.addWidget(canvas_panel, 3)  # Panel central (canvas)
        # El panel inspector (derecho) se añadirá dinámicamente

        main_layout.addLayout(content_layout, 1)  # Añade el layout horizontal al principal

        # --- Barra de Botones Inferior ---
        self.load_pila_button = QPushButton("📂 Cargar Pila")
        self.save_pila_button = QPushButton("💾 Guardar Pila")
        self.clear_button = QPushButton("🔄 Limpiar Canvas")
        self.manual_calc_button = QPushButton("📋 Planificación Manual")
        self.optimizer_calc_button = QPushButton("🚀 Optimizar por Fecha")

        # Estilos de botones (se mantienen igual)
        self.load_pila_button.setStyleSheet(
            "background-color: #5bc0de; color: white; padding: 8px; font-size: 14px;")
        self.save_pila_button.setStyleSheet(
            "background-color: #5cb85c; color: white; padding: 8px; font-size: 14px;")
        self.clear_button.setStyleSheet("background-color: #f0ad4e; color: white; padding: 8px; font-size: 14px;")
        self.manual_calc_button.setStyleSheet(
            "background-color: #337ab7; color: white; padding: 8px; font-size: 14px; font-weight: bold;")
        self.optimizer_calc_button.setStyleSheet(
            "background-color: #d9534f; color: white; padding: 8px; font-size: 14px; font-weight: bold;")

        button_bar_layout = QHBoxLayout()
        button_bar_layout.addWidget(self.load_pila_button)
        button_bar_layout.addWidget(self.save_pila_button)
        button_bar_layout.addWidget(self.clear_button)
        button_bar_layout.addStretch(1)
        button_bar_layout.addWidget(self.manual_calc_button)
        button_bar_layout.addWidget(self.optimizer_calc_button)
        main_layout.addLayout(button_bar_layout)  # Añade la barra de botones

        # Conectar señal del árbol de tareas (se mantiene igual)
        self.task_tree.itemClicked.connect(self._on_sidebar_task_clicked)

        # NUEVO: Conectar señales internas para efectos de simulación (Fase 8.1)
        # Los métodos _highlight_processing_task y _clear_all_simulation_effects se crearán después
        self.simulation_processing_task.connect(self._highlight_processing_task)
        self.simulation_finished.connect(self._clear_all_simulation_effects)

        # --- NUEVO (Fase 9): Botón flotante de preview ---
        self.preview_button = QPushButton("👁️ Previsualizar Orden de Ejecución", self)
        self.preview_button.setStyleSheet("""
                    QPushButton {
                        background-color: #17a2b8; /* Azul verdoso */
                        color: white;
                        padding: 12px 20px;
                        font-size: 14px;
                        font-weight: bold;
                        border-radius: 8px;
                        border: 2px solid #138496; /* Borde más oscuro */
                    }
                    QPushButton:hover {
                        background-color: #138496;
                    }
                    QPushButton:pressed {
                        background-color: #0f6674; /* Aún más oscuro al presionar */
                    }
                """)
        # Conectar a la función que crearemos después
        self.preview_button.clicked.connect(self._preview_execution_order)
        self.preview_button.setFixedSize(280, 50)  # Tamaño fijo

        # Posicionar inicialmente en esquina inferior derecha (usará _position_preview_button)
        self._position_preview_button()  # Llamada inicial

        # Conectar al evento de redimensionar para reposicionar (sobrescribiremos resizeEvent)
        # Guardamos la referencia al método original por si lo necesitamos
        self._original_resizeEvent = self.resizeEvent
        self.resizeEvent = self._on_dialog_resized  # Asignamos nuestro método
        # --- FIN NUEVO (Fase 9) ---

        # --- Lógica de carga inicial ---
        if existing_flow:
            self.production_flow = existing_flow
            self._load_flow_onto_canvas(existing_flow)

    def _show_inspector_panel(self):
        """Muestra el panel inspector flotante y lo añade al layout si no está."""
        # Solo actuar si no está visible ya
        if not self.inspector_is_visible:
            try:
                # Obtener el layout principal de contenido (QHBoxLayout)
                # Asumiendo que main_layout (QVBoxLayout) es el layout principal del diálogo
                # y content_layout (QHBoxLayout) está en el índice 0 de main_layout.
                main_layout = self.layout()
                if main_layout and main_layout.count() > 0:
                    content_item = main_layout.itemAt(0)
                    if content_item and isinstance(content_item.layout(), QHBoxLayout):
                        content_layout = content_item.layout()

                        # Añadir el widget del inspector al layout de contenido
                        # El '2' indica el factor de estiramiento relativo
                        content_layout.addWidget(self.inspector_panel_widget, 2)

                        # Actualizar el estado y hacer visible el widget
                        self.inspector_panel_widget.setVisible(True)
                        self.inspector_is_visible = True
                        self.logger.debug("Panel inspector añadido al layout y mostrado.")
                    else:
                        self.logger.error("No se pudo encontrar el QHBoxLayout 'content_layout'.")
                else:
                    self.logger.error("El layout principal del diálogo está vacío o no es accesible.")

            except Exception as e:
                self.logger.error(f"Error mostrando el panel inspector: {e}", exc_info=True)

    def _hide_inspector_panel(self):
        """Oculta el panel inspector flotante y lo quita del layout."""
        # Solo actuar si está visible
        if self.inspector_is_visible:
            try:
                # Obtener el layout principal de contenido
                main_layout = self.layout()
                if main_layout and main_layout.count() > 0:
                    content_item = main_layout.itemAt(0)
                    if content_item and isinstance(content_item.layout(), QHBoxLayout):
                        content_layout = content_item.layout()

                        # Quitar el widget del layout
                        content_layout.removeWidget(self.inspector_panel_widget)

                        # Ocultar widget y desvincularlo (setParent(None))
                        self.inspector_panel_widget.setVisible(False)
                        self.inspector_panel_widget.setParent(None)

                        # Limpiar selección actual
                        self.selected_canvas_task_index = None
                        # Podrías querer deseleccionar visualmente las tarjetas aquí también si es necesario
                        # self._on_card_selected(None) # Ojo: podría causar recursión si no se maneja bien

                        self.inspector_is_visible = False
                        self.logger.debug("Panel inspector quitado del layout y ocultado.")
                    else:
                        self.logger.error("No se pudo encontrar el QHBoxLayout 'content_layout' al ocultar.")
                else:
                    self.logger.error("El layout principal del diálogo está vacío o no es accesible al ocultar.")

            except Exception as e:
                self.logger.error(f"Error ocultando el panel inspector: {e}", exc_info=True)

    def _prepare_task_data(self):
        structured_data = {}
        for main_task in self.tasks_data:
            product_code = main_task['codigo']

            # --- 👇 INICIO DE LA MODIFICACIÓN 👇 ---
            # 1. Capturamos la información de contexto del producto/lote principal
            #    (el 'fabricacion_id' aquí es el identificador único del lote)
            context_data = {
                'fabricacion_id': main_task.get('fabricacion_id', 'N/A'),
                'original_product_code': main_task.get('codigo', 'N/A'),
                'original_product_info': {
                    'desc': main_task.get('descripcion', 'Sin descripción')
                },
                'deadline': main_task.get('deadline')
            }
            # --- 👆 FIN DE LA MODIFICACIÓN 👆 ---

            structured_data[product_code] = {"descripcion": main_task['descripcion'], "tasks": []}

            # Si es un producto simple (sin subfabricaciones), lo tratamos como una tarea única
            if not main_task.get('tiene_subfabricaciones'):
                task_name = main_task.get('descripcion', 'Tarea de producto simple')
                duration = 0.0
                try:
                    duration = float(str(main_task.get('tiempo_optimo', 0.0)).replace(",", "."))
                except (ValueError, TypeError):
                    self.logger.warning(f"Tiempo óptimo inválido para producto simple {product_code}")

                task_id = f"{product_code}_main_task"

                task_dict = {
                    'id': task_id,
                    'name': task_name,
                    'duration': duration,
                    'duration_per_unit': duration,
                    'department': main_task.get('departamento', 'General'),
                    'requiere_maquina_tipo': None,
                    'tipo_trabajador': main_task.get('tipo_trabajador', 1),
                }

                # --- 👇 INICIO DE LA MODIFICACIÓN 👇 ---
                # 2. Fusionamos los datos de contexto con los de la tarea
                task_dict.update(context_data)
                # --- 👆 FIN DE LA MODIFICACIÓN 👆 ---

                structured_data[product_code]['tasks'].append(task_dict)

            # Si tiene subfabricaciones, iteramos sobre ellas
            elif main_task.get('sub_partes'):
                for i, sub_task in enumerate(main_task.get('sub_partes', [])):
                    task_name = sub_task.get('descripcion', 'Tarea sin nombre')
                    duration = 0.0
                    for key in ['tiempo', 'duration']:
                        if key in sub_task:
                            try:
                                val_str = str(sub_task[key]).strip()
                                if val_str:
                                    duration = float(val_str.replace(",", "."))
                                    if duration > 0: break
                            except (ValueError, TypeError):
                                continue

                    task_id = f"{product_code}_{i}_{task_name.replace(' ', '_')}"

                    task_dict = {
                        'id': task_id,
                        'name': task_name,
                        'duration': duration,
                        'duration_per_unit': duration,
                        'department': main_task.get('departamento', 'General'),
                        'requiere_maquina_tipo': sub_task.get('requiere_maquina_tipo'),
                        'tipo_trabajador': sub_task.get('tipo_trabajador', 1),
                    }

                    # --- 👇 INICIO DE LA MODIFICACIÓN 👇 ---
                    # 2. Fusionamos los datos de contexto con los de la sub-tarea
                    task_dict.update(context_data)
                    # --- 👆 FIN DE LA MODIFICACIÓN 👆 ---

                    structured_data[product_code]['tasks'].append(task_dict)

        return structured_data

    # NUEVO: Placeholder para los métodos que conectamos (se implementarán después)
    def _highlight_processing_task(self, task_index):
        # Esta función aplicará el efecto naranja
        self.logger.debug(f"Placeholder: _highlight_processing_task llamada con índice {task_index}")
        pass

    def _clear_all_simulation_effects(self):
        # Esta función limpiará todos los efectos naranjas
        self.logger.debug("Placeholder: _clear_all_simulation_effects llamada.")
        pass

    def _create_library_panel(self):
        """Crea SÓLO el panel de contenido (QFrame) con la lista de tareas."""
        # NO creamos main_container, main_layout ni el botón aquí

        # Panel de contenido (el árbol de tareas)
        panel_content = QFrame()  # Usamos una variable local
        panel_content.setFrameShape(QFrame.Shape.StyledPanel)
        panel_content.setMinimumWidth(250)
        panel_content.setMaximumWidth(350)
        # Guardamos la referencia para poder ocultarlo/mostrarlo después
        self.library_panel_content = panel_content

        # Layout DENTRO del QFrame (panel_content)
        content_layout = QVBoxLayout(self.library_panel_content)
        # --- CORRECCIÓN: Eliminar línea duplicada ---
        content_layout.addWidget(QLabel("<b>📚 Biblioteca de Tareas</b>"))
        # content_layout.addWidget(QLabel("<b>📚 Biblioteca de Tareas</b>")) # <- Eliminar esta línea

        # Crear el árbol de tareas
        task_tree = QTreeWidget()
        self.task_tree = task_tree
        self.task_tree.setDragEnabled(True)
        task_tree.setHeaderLabel("Arrastra una tarea al panel central")

        # Diccionario para rastrear qué tareas están en el canvas
        self.tasks_in_canvas = {}

        # Poblar el árbol (sin cambios en esta parte)
        for product_code, product_info in self.task_data_by_product.items():
            product_item = QTreeWidgetItem(task_tree, [f"{product_info['descripcion']} ({product_code})"])
            product_item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))

            for task in product_info['tasks']:
                task_item_text = f"{task['name']} ({task['duration']:.2f} min)"
                task_item = QTreeWidgetItem(product_item, [task_item_text])
                task_item.setData(0, Qt.ItemDataRole.UserRole, task)
                try:
                    task_item.setIcon(0, QIcon("resources/icon.ico"))
                except NameError:
                    self.logger.warning("QIcon no disponible o icono no encontrado, omitiendo icono.")
                    pass

            product_item.setExpanded(True)

        content_layout.addWidget(task_tree)

        # --- CORRECCIÓN: Eliminar creación y conexión del botón de aquí ---
        # self.library_toggle_button = QPushButton("◀")
        # ... (Eliminar todo lo relacionado con library_toggle_button de esta función) ...
        # self.library_toggle_button.clicked.connect(self._toggle_library_panel)

        # Devolvemos SÓLO el panel de contenido (el QFrame)
        return self.library_panel_content

    def _toggle_library_panel(self):
        """Colapsa o expande el panel de biblioteca usando setVisible."""
        is_visible = self.library_panel_content.isVisible()

        if is_visible:
            # --- OCULTAR ---
            self.library_panel_content.setVisible(False)  # Más directo
            self.library_toggle_button.setText("▶")
            self.library_toggle_button.setToolTip("Mostrar Biblioteca")
        else:
            # --- MOSTRAR ---
            self.library_panel_content.setVisible(True)  # Más directo
            self.library_toggle_button.setText("◀")
            self.library_toggle_button.setToolTip("Ocultar Biblioteca")

        # Opcional: Forzar recalcular el layout padre (content_layout)
        # self.content_layout.activate() # Intenta sin esto primero

    def _update_task_tree_visual_states(self):
        """
        Actualiza el estado visual de todas las tareas en el árbol:
        - Amarillo tenue/Naranja: Tarea está en el canvas
        - Sin color especial: Tarea no está en el canvas
        - El color rojo de selección tiene prioridad visual sobre el amarillo.
        """
        if not hasattr(self, 'task_tree') or not self.task_tree:
            self.logger.warning("Intento de actualizar árbol de tareas, pero no existe.")
            return

        # --- CORRECCIÓN: Usar palette para colores de texto ---
        default_text_color = self.palette().color(QPalette.ColorRole.Text)
        canvas_marker_color = QColor("#f0ad4e")  # Naranja/Amarillo

        # Resetear todos los items primero
        iterator = QTreeWidgetItemIterator(self.task_tree)
        while iterator.value():
            item = iterator.value()
            if item.parent():  # Solo procesar items de tarea (tienen padre)
                # Color de fondo por defecto (transparente)
                item.setBackground(0, QBrush(Qt.GlobalColor.transparent))  # Más eficiente que QColor con alpha 0
                # Color de texto por defecto
                item.setForeground(0, default_text_color)
            iterator += 1

        # Marcar las tareas que están en el canvas
        for canvas_task in self.canvas_tasks:
            # Asegurarse de que 'data' existe
            task_data = canvas_task.get('data')
            if not task_data:
                continue

            original_task_id = task_data.get('original_task_id')
            if not original_task_id:
                continue

            # Buscar este ID en el árbol
            iterator = QTreeWidgetItemIterator(self.task_tree)
            while iterator.value():
                item = iterator.value()
                if not item.parent():  # Saltar items de producto (no tienen padre)
                    iterator += 1
                    continue

                item_data = item.data(0, Qt.ItemDataRole.UserRole)
                # --- CORRECCIÓN: Verificación más robusta de item_data ---
                if item_data and isinstance(item_data, dict) and item_data.get('id') == original_task_id:
                    # Marcar con el color Naranja/Amarillo en el NOMBRE (foreground)
                    item.setForeground(0, canvas_marker_color)
                    # Opcional: también el fondo muy tenue (como en el informe)
                    # item.setBackground(0, QBrush(QColor(255, 235, 59, 30))) # Amarillo muy transparente
                    break  # Tarea encontrada, no seguir buscando para este ID

                iterator += 1

        # Nota: No necesitamos manejar el color rojo aquí. El QTreeWidget lo aplica
        # automáticamente cuando se usa setCurrentItem(), y tiene prioridad visual.

    def _create_canvas_panel(self):
        """Crea el panel central donde se visualizará y construirá el flujo."""
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. Creamos el QScrollArea que contendrá nuestro canvas
        scroll_area = QScrollArea()
        # --- CAMBIO: False para control manual ---
        scroll_area.setWidgetResizable(False)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 2. Creamos una instancia de nuestro CanvasWidget
        self.canvas = CanvasWidget(self)
        # ✨ NUEVO: Crear el label de mensaje flotante (inicialmente oculto)
        self._create_simulation_message_label()

        # --- NUEVO: Guardar referencia al scroll_area ---
        self.canvas_scroll_area = scroll_area

        # --- CAMBIO: Tamaño inicial más razonable ---
        initial_width = 2000
        initial_height = 2000
        self.canvas.setMinimumSize(initial_width, initial_height)

        # 3. Asignamos el canvas como el widget DENTRO del QScrollArea
        scroll_area.setWidget(self.canvas)

        # 4. Añadimos el QScrollArea al layout principal
        layout.addWidget(scroll_area)

        return panel

    def _create_inspector_panel(self):
        """Crea el panel derecho flotante con los detalles de la tarea."""
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        # Establecer tamaño mínimo y máximo para controlar el ancho
        panel.setMinimumWidth(350)
        panel.setMaximumWidth(450)

        # NUEVO: Estilo para que se vea como flotante
        panel.setStyleSheet("""
            QFrame {
                background-color: palette(window);
                border: 2px solid #4a90e2; /* Azul claro */
                border-radius: 8px;
                /* Añadir sombra para efecto flotante (opcional, puede variar en estilo) */
                /* QGraphicsDropShadowEffect podría ser otra opción */
            }
        """)

        # Guardamos el layout principal del inspector
        self.inspector_layout = QVBoxLayout(panel)
        self.inspector_layout.setContentsMargins(5, 5, 5, 5)  # Márgenes internos reducidos

        # NUEVO: Botón de cierre en la esquina
        close_button = QPushButton("✖")
        close_button.setFixedSize(24, 24)  # Tamaño ajustado
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545; /* Rojo */
                color: white;
                border: none;
                border-radius: 12px; /* Redondo */
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333; /* Rojo más oscuro */
            }
        """)
        # Conectamos a la función que crearemos después
        close_button.clicked.connect(self._hide_inspector_panel)

        # Layout para el botón de cierre (esquina superior derecha)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_button)
        # Añadimos el layout del botón al layout principal del inspector
        self.inspector_layout.addLayout(close_layout)

        # Marcador de posición inicial (se mantiene igual)
        placeholder_label = QLabel(
            "PANEL INSPECTOR\n\nSelecciona una tarea en el canvas para configurar sus detalles y reglas de reasignación.")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setWordWrap(True)
        placeholder_label.setStyleSheet("color: #777; border: none;")  # Quitamos el borde al placeholder
        # Guardamos referencia al placeholder para poder ocultarlo/mostrarlo después
        self.inspector_widgets['placeholder'] = placeholder_label
        self.inspector_layout.addWidget(placeholder_label)

        # El resto de widgets se añadirán dinámicamente en _populate_inspector_panel

        return panel

    def _create_inspector_widgets(self):
        """Crea y conecta todos los widgets para el panel inspector."""
        self.inspector_widgets = {}

        # Título
        title = QLabel("Propiedades de Tarea")
        font = title.font()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        title.setWordWrap(True)
        self.inspector_widgets['title'] = title

        duration_label = QLabel()
        duration_label.setStyleSheet("font-style: italic; color: #888;")
        self.inspector_widgets['duration_label'] = duration_label

        # -- Grupo: Condición de Inicio --
        start_condition_group = QGroupBox("Condición de Inicio")  # Usar variable local clara
        start_layout = QVBoxLayout(start_condition_group)  # Crear layout DENTRO del grupo

        # Radio: Fecha específica
        self.inspector_widgets['start_date_radio'] = QRadioButton("Fecha y Hora Específica")
        start_layout.addWidget(self.inspector_widgets['start_date_radio'])

        # *** LÍNEA RESTAURADA Y CORREGIDA ***
        # Crear el QDateTimeEdit y guardarlo en el diccionario
        self.inspector_widgets['start_date_edit'] = QDateTimeEdit(datetime.now())
        self.inspector_widgets['start_date_edit'].setCalendarPopup(True)  # Opcional: añadir popup de calendario
        self.inspector_widgets['start_date_edit'].setDisplayFormat("dd/MM/yyyy HH:mm")  # Formato deseado
        start_layout.addWidget(self.inspector_widgets['start_date_edit'])  # Añadir al layout
        # *** FIN DE LA CORRECCIÓN ***

        # Radio: Dependencia
        self.inspector_widgets['dependency_radio'] = QRadioButton("Al finalizar otra tarea")
        start_layout.addWidget(self.inspector_widgets['dependency_radio'])

        # ComboBox de tarea predecesora
        dep_layout = QHBoxLayout()
        dep_layout.addWidget(QLabel("Tarea predecesora:"))
        self.inspector_widgets['dependency_combo'] = QComboBox()
        dep_layout.addWidget(self.inspector_widgets['dependency_combo'])
        start_layout.addLayout(dep_layout)

        # SpinBox para unidades mínimas del predecesor
        min_units_layout = QHBoxLayout()
        min_units_label = QLabel("Esperar a que complete:")
        min_units_label.setToolTip(
            "¿Cuántas unidades debe completar la tarea predecesora "
            "antes de que ESTA tarea pueda empezar?\n\n"
            "Ejemplo: Si pones 5, esta tarea empezará cuando el "
            "predecesor termine su unidad 5."
        )
        self.inspector_widgets['min_predecessor_units_spin'] = QSpinBox()
        self.inspector_widgets['min_predecessor_units_spin'].setRange(1, 99999)
        self.inspector_widgets['min_predecessor_units_spin'].setValue(1)
        self.inspector_widgets['min_predecessor_units_spin'].setSuffix(" unidades")
        self.inspector_widgets['min_predecessor_units_spin'].setMaximumWidth(150)
        min_units_layout.addWidget(min_units_label)
        min_units_layout.addWidget(self.inspector_widgets['min_predecessor_units_spin'])
        min_units_layout.addStretch()
        start_layout.addLayout(min_units_layout)

        # Guardar referencia al grupo completo
        self.inspector_widgets['start_condition_group'] = start_condition_group

        # Conectar señales del grupo de Condición de Inicio
        self.inspector_widgets['start_date_radio'].toggled.connect(self._update_task_config)
        self.inspector_widgets['start_date_radio'].toggled.connect(self._toggle_start_condition_widgets)
        self.inspector_widgets['start_date_edit'].dateTimeChanged.connect(self._update_task_config)
        self.inspector_widgets['dependency_radio'].toggled.connect(self._update_task_config)
        self.inspector_widgets['dependency_radio'].toggled.connect(self._toggle_start_condition_widgets)
        self.inspector_widgets['dependency_combo'].currentIndexChanged.connect(self._update_task_config)
        self.inspector_widgets['min_predecessor_units_spin'].valueChanged.connect(self._update_task_config)

        # -- Grupo: Marcador de Ciclo --
        cycle_marker_group = QGroupBox("Marcador de Ciclo")
        cycle_layout = QVBoxLayout(cycle_marker_group)

        self.inspector_widgets['cycle_start_checkbox'] = QCheckBox(
            "⭐ Marcar como Tarea de Inicio de Ciclo"
        )
        self.inspector_widgets['cycle_start_checkbox'].setToolTip(
            "Las tareas de inicio de ciclo son las primeras que se revisan\n"
            "al iniciar el cálculo. Pueden ser múltiples."
        )
        self.inspector_widgets['cycle_start_checkbox'].setStyleSheet("""
                QCheckBox {
                    font-weight: bold;
                    color: #f39c12; /* Color dorado/amarillo */
                }
            """)
        cycle_layout.addWidget(self.inspector_widgets['cycle_start_checkbox'])

        # Guardar referencia al grupo
        self.inspector_widgets['cycle_marker_group'] = cycle_marker_group

        # Conectar señal del nuevo checkbox
        self.inspector_widgets['cycle_start_checkbox'].stateChanged.connect(
            self._update_task_config
        )

        # -- Grupo: Objetivos de Producción --
        prod_goals_group = QGroupBox("Objetivos de Producción")  # Usar variable local clara
        prod_layout = QFormLayout(prod_goals_group)  # Crear layout DENTRO del grupo

        # Widget para Unidades Totales
        self.inspector_widgets['total_units_spin'] = QSpinBox()
        self.inspector_widgets['total_units_spin'].setRange(1, 99999)
        self.inspector_widgets['total_units_spin'].setValue(self.units)  # Valor inicial global
        prod_layout.addRow("Unidades Totales a Fabricar:", self.inspector_widgets['total_units_spin'])

        # Widget para Unidades por Ciclo
        self.inspector_widgets['units_per_cycle_spin'] = QSpinBox()
        self.inspector_widgets['units_per_cycle_spin'].setRange(1, 99999)  # Máximo se ajustará dinámicamente
        self.inspector_widgets['units_per_cycle_spin'].setValue(1)  # Valor por defecto
        prod_layout.addRow("Unidades por Ciclo:", self.inspector_widgets['units_per_cycle_spin'])

        # Widget para Siguiente Tarea Cíclica
        self.inspector_widgets['next_cyclic_combo'] = QComboBox()
        prod_layout.addRow("Siguiente Tarea Cíclica:", self.inspector_widgets['next_cyclic_combo'])

        # Conectar señales AQUI, después de crear los widgets
        self.inspector_widgets['total_units_spin'].valueChanged.connect(self._update_task_config)
        self.inspector_widgets['units_per_cycle_spin'].valueChanged.connect(self._update_task_config)
        self.inspector_widgets['next_cyclic_combo'].currentIndexChanged.connect(self._update_task_config)

        # Guardar referencia al grupo completo
        self.inspector_widgets['prod_goals_group'] = prod_goals_group

        # -- Grupo: Recursos --
        group = QGroupBox("Recursos Asignados")
        layout = QFormLayout()
        self.inspector_widgets['machine_combo'] = QComboBox()
        layout.addRow("Máquina:", self.inspector_widgets['machine_combo'])
        group.setLayout(layout)
        self.inspector_widgets['resources_group'] = group

        # Conectar señal del combo de máquina
        self.inspector_widgets['machine_combo'].currentIndexChanged.connect(self._update_task_config)

        # -- Grupo: Gestión de Trabajadores --
        group = QGroupBox("Gestión de Trabajadores")
        main_worker_layout = QVBoxLayout()
        lists_layout = QHBoxLayout()
        available_layout = QVBoxLayout()
        available_layout.addWidget(QLabel("Disponibles"))
        self.inspector_widgets['available_workers_list'] = QListWidget()
        available_layout.addWidget(self.inspector_widgets['available_workers_list'])
        assign_btns_layout = QVBoxLayout()
        assign_btns_layout.addStretch()
        self.inspector_widgets['assign_worker_button'] = QPushButton(">>")
        self.inspector_widgets['unassign_worker_button'] = QPushButton("<<")
        assign_btns_layout.addWidget(self.inspector_widgets['assign_worker_button'])
        assign_btns_layout.addWidget(self.inspector_widgets['unassign_worker_button'])
        assign_btns_layout.addStretch()
        assigned_layout = QVBoxLayout()
        assigned_layout.addWidget(QLabel("Asignados"))
        self.inspector_widgets['assigned_workers_list'] = QListWidget()
        assigned_layout.addWidget(self.inspector_widgets['assigned_workers_list'])
        lists_layout.addLayout(available_layout)
        lists_layout.addLayout(assign_btns_layout)
        lists_layout.addLayout(assigned_layout)
        main_worker_layout.addLayout(lists_layout)

        group.setLayout(main_worker_layout)  # Asignas el layout al GroupBox
        self.inspector_widgets['workers_group'] = group

        # -- Grupo: Botones de Configuración Avanzada --
        advanced_buttons_group = QGroupBox("Configuración Avanzada")
        advanced_layout = QHBoxLayout(advanced_buttons_group)  # Layout horizontal DENTRO del grupo

        # Botón de reasignación (ahora dentro del layout horizontal)
        self.inspector_widgets['reassignment_button'] = QPushButton(
            "🔧 Configurar Reasignación"
        )
        self.inspector_widgets['reassignment_button'].setToolTip(
            "Configura reglas para reasignar trabajadores automáticamente"
        )
        self.inspector_widgets['reassignment_button'].setStyleSheet("""
                    QPushButton {
                        background-color: #6c757d; /* Gris */
                        color: white;
                        padding: 8px;
                        font-size: 13px; /* Ajustado */
                        font-weight: bold;
                        border-radius: 5px;
                    }
                    QPushButton:hover { background-color: #5a6268; }
                    QPushButton:disabled { background-color: #d3d3d3; color: #888; }
                """)
        # La conexión de la señal se mantiene
        self.inspector_widgets['reassignment_button'].clicked.connect(self._handle_configure_reassignment)
        # Habilitar/deshabilitar se maneja en _populate_inspector_panel
        self.inspector_widgets['reassignment_button'].setEnabled(False)  # Empezar deshabilitado

        # >>> NUEVO: Botón de fin de ciclo <<<
        self.inspector_widgets['cycle_end_button'] = QPushButton(
            "🔄 Configurar Fin de Ciclo"
        )
        self.inspector_widgets['cycle_end_button'].setToolTip(
            "Define a qué tarea regresar al completar un ciclo"
        )
        self.inspector_widgets['cycle_end_button'].setStyleSheet("""
                    QPushButton {
                        background-color: #28a745; /* Verde */
                        color: white;
                        padding: 8px;
                        font-size: 13px; /* Ajustado */
                        font-weight: bold;
                        border-radius: 5px;
                    }
                    QPushButton:hover { background-color: #218838; }
                    QPushButton:disabled { background-color: #d3d3d3; color: #888; }
                """)
        # Conectar a la función que crearemos después
        self.inspector_widgets['cycle_end_button'].clicked.connect(self._open_cycle_end_dialog)

        # Añadir ambos botones al layout horizontal
        advanced_layout.addWidget(self.inspector_widgets['reassignment_button'])
        advanced_layout.addWidget(self.inspector_widgets['cycle_end_button'])

        # Guardar referencia al grupo
        self.inspector_widgets['advanced_buttons_group'] = advanced_buttons_group

        # Conectar señales del grupo de trabajadores
        self.inspector_widgets['assign_worker_button'].clicked.connect(self._handle_assign_worker)
        self.inspector_widgets['unassign_worker_button'].clicked.connect(self._handle_unassign_worker)
        self.inspector_widgets['reassignment_button'].clicked.connect(self._handle_configure_reassignment)
        self.inspector_widgets['assigned_workers_list'].itemSelectionChanged.connect(
            lambda: self.inspector_widgets['reassignment_button'].setEnabled(True)
        )

        # --- INICIO DE LA MODIFICACIÓN ---
        # 1. Crear el nuevo botón de eliminar
        delete_button = QPushButton("🗑️ Eliminar Tarea del Flujo")
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                border: 1px solid #d43f3a;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)
        self.inspector_widgets['delete_button'] = delete_button
        # --- FIN DE LA MODIFICACIÓN ---

        # Ocultar SOLO los grupos principales y widgets de nivel superior,
        # NO los widgets internos de los grupos
        widgets_to_hide = ['title', 'duration_label', 'start_condition_group',
                           'prod_goals_group', 'resources_group', 'workers_group',
                           'advanced_buttons_group',
                           'delete_button','cycle_marker_group', 'placeholder']

        for widget_name in widgets_to_hide:
            widget = self.inspector_widgets.get(widget_name)
            if widget:
                widget.setVisible(False)

        # 2. Conectar la señal del nuevo botón a la función que crearemos en el siguiente paso
        self.inspector_widgets['delete_button'].clicked.connect(self._handle_delete_selected_task)


    def _handle_delete_selected_task(self):
        """
        Elimina la tarea actualmente seleccionada del canvas y recalcula las dependencias.
        """
        if self.selected_canvas_task_index is None:
            return

        # Pedir confirmación al usuario
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            "¿Está seguro de que desea eliminar esta tarea del flujo de producción?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        index_to_delete = self.selected_canvas_task_index
        task_to_delete = self.canvas_tasks[index_to_delete]

        # Eliminar el widget visual de la tarjeta
        task_to_delete['widget'].deleteLater()

        # Eliminar los datos de la tarea de la lista principal
        self.canvas_tasks.pop(index_to_delete)
        self.logger.info(f"Tarea en el índice {index_to_delete} eliminada del flujo.")

        # --- LÓGICA CRÍTICA: Recalcular los índices de dependencia ---
        # Al eliminar un elemento, todos los índices de los elementos posteriores
        # se desplazan, y las dependencias que apuntaban a ellos deben actualizarse.
        for task in self.canvas_tasks:
            config = task.get('config', {})
            start_condition = config.get('start_condition', {})

            if start_condition.get('type') == 'dependency':
                parent_index = start_condition.get('value')
                if parent_index is None:
                    continue

                # Si una tarea dependía de la que hemos borrado, rompemos la dependencia
                if parent_index == index_to_delete:
                    start_condition['value'] = None
                    self.logger.warning(f"Dependencia rota para la tarea '{task['data']['name']}'. Por favor, reasígnela.")

                # Si una tarea dependía de otra posterior a la que hemos borrado,
                # tenemos que restar 1 a su índice de dependencia.
                elif parent_index > index_to_delete:
                    start_condition['value'] -= 1

        # Limpiar la selección y el panel inspector
        self.selected_canvas_task_index = None
        self._populate_inspector_panel(None)

        # Actualizar las flechas del canvas con las nuevas dependencias
        self._update_canvas_connections()

    def _load_flow_onto_canvas(self, flow_data):
        """
        Limpia el canvas y dibuja en él un flujo de producción existente,
        RESTAURANDO LA POSICIÓN y VALIDANDO TODA LA CONFIGURACIÓN de cada tarea.
        """
        # 1. Limpiar completamente el estado actual del diálogo
        self.logger.info(f"📂 Cargando flujo con {len(flow_data)} pasos")
        for child in self.canvas.findChildren(CardWidget):
            child.deleteLater()
        self.canvas_tasks = []
        self.selected_canvas_task_index = None
        self.canvas.set_connections([])
        self._populate_inspector_panel(None)

        # 2. Iterar sobre el flujo cargado y crear las tarjetas visuales
        import copy

        # ✨ NUEVO: Contadores para validación
        missing_configs_count = 0
        restored_configs_count = 0

        for i, step in enumerate(flow_data):
            task_data_original = step.get('task')
            if not task_data_original:
                self.logger.warning(
                    f"⚠️ Step {i}: Sin datos de tarea, omitido")
                continue

            # --- Lógica de posición (igual que la tuya) ---
            position_data = step.get('position')
            grid_size = 20
            if position_data and 'x' in position_data and 'y' in position_data:
                raw_x = position_data['x']
                raw_y = position_data['y']
                snapped_x = round(raw_x / grid_size) * grid_size
                snapped_y = round(raw_y / grid_size) * grid_size
                pos = QPoint(snapped_x, snapped_y)
            else:
                fallback_x = 50
                fallback_y = 50 + (i * 80)
                snapped_x = round(fallback_x / grid_size) * grid_size
                snapped_y = round(fallback_y / grid_size) * grid_size
                pos = QPoint(snapped_x, snapped_y)
                # ✨ NUEVO: Log si falta posición
                self.logger.warning(f"⚠️ Step {i}: Falta 'position', usando default {pos.x()},{pos.y()}")
                missing_configs_count += 1

            # ✨ CAMBIO: Añadir 'skip_confirmation=True' para evitar popups al cargar
            self._add_task_to_canvas(copy.deepcopy(task_data_original), pos, skip_confirmation=True)

            # --- INICIO CORRECCIÓN ---
            # Restaurar la regla de reasignación en la config interna
            if 'workers' in step and isinstance(step['workers'], list):
                # Obtenemos la referencia a la config recién añadida
                newly_added_config = self.canvas_tasks[-1]['config']

                # Asegurarnos de que la config interna tenga una lista de workers
                if 'workers' not in newly_added_config:
                    newly_added_config['workers'] = []

                # Limpiamos la lista interna por si acaso
                newly_added_config['workers'].clear()

                # Copiamos los datos de workers del flujo cargado a la config interna
                for worker_data_from_flow in step['workers']:
                    if isinstance(worker_data_from_flow, dict):
                        # Copiamos el diccionario completo (incluye name y reassignment_rule)
                        newly_added_config['workers'].append(worker_data_from_flow.copy())
                    elif isinstance(worker_data_from_flow, str):
                        # Convertimos formato antiguo a nuevo
                        newly_added_config['workers'].append({'name': worker_data_from_flow, 'reassignment_rule': None})

                self.logger.debug(f"Reglas restauradas para tarea {i}: {newly_added_config['workers']}")
            # --- FIN CORRECCIÓN ---

            # --- ✨ INICIO: RESTAURACIÓN ROBUSTA DE CONFIGURACIÓN ---
            if self.canvas_tasks:
                newly_added_index = len(self.canvas_tasks) - 1
                config = self.canvas_tasks[newly_added_index]['config']

                # Validar y restaurar cada campo crítico

                # 1. Units per cycle
                if 'units_per_cycle' in step:
                    if step['units_per_cycle'] is not None and step['units_per_cycle'] > 0:
                        config['units_per_cycle'] = step['units_per_cycle']
                        restored_configs_count += 1
                    else:
                        self.logger.warning(
                            f"⚠️ Step {i}: units_per_cycle inválido ({step['units_per_cycle']}), usando default=1")
                        config['units_per_cycle'] = 1
                        missing_configs_count += 1
                else:
                    self.logger.warning(f"⚠️ Step {i}: Falta units_per_cycle, usando default=1")
                    config['units_per_cycle'] = 1
                    missing_configs_count += 1

                # 2. Next cyclic task index
                if 'next_cyclic_task_index' in step:
                    config['next_cyclic_task_index'] = step.get('next_cyclic_task_index')
                    if step['next_cyclic_task_index'] is not None:
                        restored_configs_count += 1
                else:
                    config['next_cyclic_task_index'] = None

                # 3. Campos restantes (como los tenías, pero con .get() más seguros)
                config['total_units'] = step.get('trigger_units', self.units)
                config['min_predecessor_units'] = step.get('min_predecessor_units', 1)
                config['machine_id'] = step.get('machine_id')
                config['workers'] = step.get('workers', [])
                config['is_cycle_start'] = step.get('is_cycle_start', False)
                config['is_cycle_end'] = step.get('is_cycle_end', False)
                config['cycle_return_to_index'] = step.get('cycle_return_to_index')

                # 4. Condición de inicio (lógica robusta)
                if step.get('start_date'):
                    start_val = step['start_date']
                    start_dt = None
                    if isinstance(start_val, datetime):
                        start_dt = start_val
                    elif isinstance(start_val, date):
                        start_time_cfg = getattr(self.schedule_config, 'WORK_START_TIME', time(8, 0))
                        start_dt = datetime.combine(start_val, start_time_cfg)

                    if start_dt:
                        config['start_condition'] = {'type': 'date', 'value': start_dt}
                    else:
                        config['start_condition'] = {'type': 'date', 'value': datetime.now()}
                        missing_configs_count += 1

                elif 'previous_task_index' in step and step['previous_task_index'] is not None:
                    config['start_condition'] = {'type': 'dependency', 'value': step['previous_task_index']}
                else:
                    config['start_condition'] = {'type': 'date', 'value': datetime.now()}

                self.logger.debug(f"✅ Config restaurada para tarea '{task_data_original.get('name')}': "
                                    f"units_per_cycle={config['units_per_cycle']}, "
                                    f"next_cyclic={config['next_cyclic_task_index']}")

        # 3. Actualizar conexiones visuales y estado global
        self._update_canvas_connections()
        self._update_canvas_size()
        self._update_all_cycle_start_effects()

        # 4. ✨ NUEVO: Log de resumen y advertencia al usuario si faltan datos
        self.logger.info(f"✅ Flujo cargado:")
        self.logger.info(f"   • Tarjetas: {len(self.canvas_tasks)}")
        self.logger.info(f"   • Configs restauradas OK: {restored_configs_count}")
        self.logger.info(f"   • Configs con defaults: {missing_configs_count}")

        if missing_configs_count > 0:
            QMessageBox.warning(
                self,
                "Configuraciones Restauradas",
                f"Se restauró el flujo, pero {missing_configs_count} tareas tenían "
                f"configuraciones incompletas que se han completado con valores por defecto.\n\n"
                f"Esto es normal en pilas antiguas. Revisa las configuraciones y vuelve a guardar la pila.",
                QMessageBox.StandardButton.Ok
            )

        self.logger.info("Flujo cargado y dibujado correctamente en el canvas.")

    def _add_task_to_canvas(self, task_data, position, skip_confirmation=False):
        """Crea una 'tarjeta' y su estructura de datos de configuración en el canvas."""
        self.logger.info(
            f"--- _add_task_to_canvas starting for: {task_data.get('name', 'NO NAME')} ---")  # <<< AÑADIDO LOG

        original_task_id = task_data.get('id')  # ID de la tarea original de la biblioteca

        # Solo validar si el ID original existe y no se pide omitir la confirmación
        if original_task_id and not skip_confirmation:
            # Contar cuántas veces ya está esta tarea (basado en el ID original) en el canvas
            count = sum(
                1 for canvas_task in self.canvas_tasks
                if canvas_task.get('data', {}).get('original_task_id') == original_task_id
            )

            # Si ya existe al menos una vez, preguntar al usuario
            if count > 0:
                task_name = task_data.get('name', 'esta tarea')
                times_str = f"{count} vez" if count == 1 else f"{count} veces"

                msg_box = QMessageBox(self)  # Usar 'self' como parent
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowTitle("⚠️ Tarea Duplicada")
                msg_box.setText(f"<b>La tarea '{task_name}' ya está en el canvas.</b>")
                msg_box.setInformativeText(
                    f"Esta tarea ya ha sido añadida {times_str}.\n\n"
                    f"¿Deseas añadirla nuevamente?"
                )
                # Botones estándar: Sí y No
                msg_box.setStandardButtons(
                    QMessageBox.StandardButton.Yes |
                    QMessageBox.StandardButton.No
                )
                msg_box.setDefaultButton(QMessageBox.StandardButton.No)  # 'No' por defecto

                # Personalizar texto de los botones para mayor claridad
                yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
                yes_button.setText("Sí, añadir otra vez")
                no_button = msg_box.button(QMessageBox.StandardButton.No)
                no_button.setText("No, cancelar")

                # Mostrar el diálogo y esperar la respuesta
                result = msg_box.exec()

                # Si el usuario NO presiona 'Sí', salir de la función sin añadir
                if result != QMessageBox.StandardButton.Yes:
                    self.logger.info(
                        f"Usuario canceló la adición de tarea duplicada '{task_name}' (ID: {original_task_id})"
                    )
                    return  # Salir de la función _add_task_to_canvas

                # Si el usuario presiona 'Sí', continuar con la adición
                self.logger.info(
                    f"Usuario confirmó añadir tarea duplicada '{task_name}' (ID: {original_task_id})"
                )

        import uuid
        import copy  # <- Añade esta importación

        # --- CORRECCIÓN CRÍTICA: Usar deepcopy para aislar la configuración de cada tarjeta ---
        # Se crea una copia profunda tanto de los datos de la tarea como de la configuración por defecto.
        # Esto evita que todas las tarjetas compartan la misma referencia y se modifiquen a la vez.
        task_data_copy = copy.deepcopy(task_data)
        default_config = {
            'start_condition': {'type': 'date', 'value': datetime.now()},
            'total_units': self.units,  # Unidades totales para esta tarea
            'units_per_cycle': 1,  # Unidades procesadas antes de evaluar ciclo/reasignación
            'next_cyclic_task_index': None,  # Índice de la TAREA SIGUIENTE si esta NO es fin de ciclo
            'min_predecessor_units': 1,  # Unidades mínimas a esperar del predecesor
            'machine_id': None,  # ID de la máquina asignada
            'workers': [],  # Lista de trabajadores asignados [{'name': '...', 'rule': ...}]
            'is_cycle_start': False,  # Indica si es un punto de inicio para el motor
            # --- NUEVOS CAMPOS FASE 5.2 ---
            'is_cycle_end': False,  # Indica si esta tarea marca el final de un ciclo repetitivo
            'cycle_return_to_index': None,  # Índice de la tarea a la que regresar si is_cycle_end es True
            # --- FIN NUEVOS CAMPOS ---
        }

        # Defensa duración
        if 'duration' in task_data_copy and 'duration_per_unit' not in task_data_copy:
            task_data_copy['duration_per_unit'] = task_data_copy['duration']
        elif 'duration_per_unit' in task_data_copy and 'duration' not in task_data_copy:
            task_data_copy['duration'] = task_data_copy['duration_per_unit']
        self.logger.debug(f"  Duration used: {task_data_copy.get('duration', 'N/A')} min")  # <<< AÑADIDO LOG

        # ID Original
        if 'id' in task_data_copy:
            task_data_copy['original_task_id'] = task_data_copy['id']
        else:
            self.logger.warning("  Task data missing original 'id'")  # <<< AÑADIDO LOG

        # ID Único del Canvas
        task_data_copy['canvas_unique_id'] = str(uuid.uuid4())
        self.logger.info(f"  Assigned canvas_unique_id: {task_data_copy['canvas_unique_id']}")  # <<< AÑADIDO LOG

        card = CardWidget(task_data_copy, self.canvas)
        # Verificar conexión de señal
        try:
            card.clicked.connect(self._on_card_selected)
            self.logger.debug("  Signal card.clicked connected successfully.")  # <<< AÑADIDO LOG
        except Exception as e:
            self.logger.error(f"  ERROR connecting card.clicked signal: {e}")  # <<< AÑADIDO LOG

        card.moved.connect(self._on_card_moved)

        card_x = position.x() - card.width() // 2
        card_y = position.y() - card.height() // 2

        # ✨ NUEVO: Ajustar al grid antes de posicionar
        grid_size = 20
        snapped_x = round(card_x / grid_size) * grid_size
        snapped_y = round(card_y / grid_size) * grid_size

        card.move(snapped_x, snapped_y)
        card.show()

        canvas_task_object = {
            'data': task_data_copy,
            'widget': card,
            'config': copy.deepcopy(default_config)  # <- Usar la copia profunda de la configuración
        }

        self.canvas_tasks.append(canvas_task_object)
        self.logger.info(
            f"  Task added to self.canvas_tasks list (new length: {len(self.canvas_tasks)})")  # <<< AÑADIDO LOG
        # NUEVO: Actualizar marcas visuales en el árbol
        self._update_task_tree_visual_states()
        self._update_canvas_size()
        self.logger.info("--- _add_task_to_canvas finished ---")

    def _clear_canvas_and_reset(self):
        """
        Limpia completamente el canvas, eliminando todas las tareas y conexiones,
        y resetea el panel inspector a su estado inicial.
        """
        self.logger.info("Limpiando el canvas del editor visual.")

        # 1. Eliminar todos los widgets (tarjetas) del canvas
        for task in self.canvas_tasks:
            task['widget'].deleteLater()  # Método seguro para eliminar widgets en Qt

        # 2. Limpiar las listas de datos y el estado de selección
        self.canvas_tasks = []
        self.selected_canvas_task_index = None

        # 3. Limpiar las conexiones en el widget del canvas
        if hasattr(self, 'canvas'):
            self.canvas.set_connections([])  # Le pasamos una lista vacía

        # 4. Limpiar y mostrar el placeholder del panel inspector
        while self.inspector_layout.count():
            child = self.inspector_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)  # Oculta el widget actual del inspector

        placeholder_label = QLabel(
            "PANEL INSPECTOR\n\nEl flujo ha sido limpiado. "
            "Arrastra una tarea desde la biblioteca para empezar de nuevo."
        )
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setWordWrap(True)
        placeholder_label.setStyleSheet("color: #777;")
        self.inspector_layout.addWidget(placeholder_label)

    def _on_card_selected(self, task_data):
        """
        Se activa al hacer clic en una tarjeta. La resalta, puebla el inspector,
        resalta la tarea en la biblioteca y la cadena cíclica a la que pertenece.
        """
        self.logger.info("--- _on_card_selected triggered ---")
        # NUEVO: Mostrar el panel inspector antes de procesar la selección
        self._show_inspector_panel()

        if not task_data:
            self.logger.warning("  _on_card_selected received empty task_data.")
            return

        canvas_unique_id = task_data.get('canvas_unique_id')
        if not canvas_unique_id:
            self.logger.error("  ERROR: Card data is missing 'canvas_unique_id'!")
            return

        found_index = next(
            (i for i, task in enumerate(self.canvas_tasks) if task['data'].get('canvas_unique_id') == canvas_unique_id),
            -1)

        selected_task_object = None
        if found_index != -1:
            self.selected_canvas_task_index = found_index
            selected_task_object = self.canvas_tasks[self.selected_canvas_task_index]
            self.logger.info(f"  Índice de tarjeta encontrado y asignado: {self.selected_canvas_task_index}")
        else:
            self.logger.error(f"  🚨 ERROR: No se encontró la tarjeta con ID {canvas_unique_id} en la lista.")
            self.selected_canvas_task_index = None

        if selected_task_object:
            original_task_id = selected_task_object['data'].get('original_task_id')
            if original_task_id:
                iterator = QTreeWidgetItemIterator(self.task_tree)
                item_to_select = None
                while iterator.value():
                    item = iterator.value()
                    item_data = item.data(0, Qt.ItemDataRole.UserRole)
                    if item_data and isinstance(item_data, dict) and item_data.get('id') == original_task_id:
                        item_to_select = item
                        break
                    iterator += 1

                if item_to_select:
                    self.task_tree.setCurrentItem(item_to_select)
                    self.task_tree.scrollToItem(item_to_select, QAbstractItemView.ScrollHint.PositionAtCenter)

        palette = self.palette()
        base_color = palette.color(QPalette.ColorRole.Base).name()
        text_color = palette.color(QPalette.ColorRole.Text).name()
        hover_color = palette.color(QPalette.ColorRole.AlternateBase).name()

        parent_index = None
        children_indices = []

        # ============================================================================
        # ✨ NUEVA LÓGICA: Encontrar toda la cadena cíclica
        # ============================================================================
        cyclic_chain_indices = set()
        if selected_task_object and self.selected_canvas_task_index is not None:
            # Búsqueda hacia adelante en la cadena
            current_index = self.selected_canvas_task_index
            while current_index is not None:
                if current_index in cyclic_chain_indices: break  # Evitar bucles infinitos si hay un error
                cyclic_chain_indices.add(current_index)
                current_config = self.canvas_tasks[current_index].get('config', {})
                current_index = current_config.get('next_cyclic_task_index')

            # Búsqueda hacia atrás en la cadena
            current_index = self.selected_canvas_task_index
            while current_index is not None:
                # Encontrar qué tarea apunta a la actual
                previous_in_chain = next((i for i, task in enumerate(self.canvas_tasks)
                                          if task.get('config', {}).get('next_cyclic_task_index') == current_index),
                                         None)
                if previous_in_chain is not None:
                    if previous_in_chain in cyclic_chain_indices: break  # Evitar bucles infinitos
                    cyclic_chain_indices.add(previous_in_chain)
                    current_index = previous_in_chain
                else:
                    break  # No hay más predecesores en la cadena

        if selected_task_object and self.selected_canvas_task_index is not None:
            selected_config = selected_task_object.get('config', {})
            start_condition = selected_config.get('start_condition', {})
            if start_condition.get('type') == 'dependency':
                parent_index = start_condition.get('value')
            for i, task in enumerate(self.canvas_tasks):
                dep_config = task.get('config', {}).get('start_condition', {})
                if dep_config.get('type') == 'dependency' and dep_config.get(
                        'value') == self.selected_canvas_task_index:
                    children_indices.append(i)

        for i, task in enumerate(self.canvas_tasks):
            widget = task.get('widget')
            if not widget: continue

            is_selected = (self.selected_canvas_task_index is not None and i == self.selected_canvas_task_index)
            is_parent = (parent_index is not None and i == parent_index)
            is_child = (i in children_indices)
            is_in_cyclic_chain = i in cyclic_chain_indices

            # --- ✨ Lógica de color FASE 4.3 (Prioriza auto-trigger) ---
            # Primero, verifica si la tarea actual es auto-triggered
            is_auto_triggered, _ = self._is_task_auto_triggered(i)

            if is_selected:
                border_color = "#dc3545"  # Rojo (seleccionado) - Máxima prioridad
            elif is_auto_triggered:
                # Si es auto-triggered, usa verde, incluso si también es parte de un ciclo
                # o es padre/hijo de la tarea seleccionada (excepto si es la seleccionada).
                border_color = "#28a745"  # Verde (auto-triggered / ciclo)
            elif is_parent or is_child:
                border_color = "#9b59b6"  # Morado (dependencia con la seleccionada)
            # Nota: Ya no necesitamos un elif específico para is_in_cyclic_chain
            # porque is_auto_triggered ya cubre los ciclos que causan auto-trigger.
            # Si una tarea es parte de un ciclo pero NO es auto-triggered
            # (p.ej., la última del ciclo sin retorno), tendrá color normal o de dependencia.
            else:
                border_color = "#007bff"  # Azul (normal)

            # Determinar el ancho del borde (sin cambios aquí)
            border_width = "3px" if is_selected or is_auto_triggered or is_parent or is_child else "2px"

            try:
                widget.setStyleSheet(f"""
                    QLabel {{
                        background-color: {base_color}; color: {text_color};
                        border: {border_width} solid {border_color}; border-radius: 5px; padding: 5px;
                    }}
                    QLabel:hover {{ background-color: {hover_color}; }}
                """)
            except Exception as e:
                self.logger.error(f"Error aplicando estilo a tarjeta {i}: {e}")

        self.logger.info(f"  Llamando a _populate_inspector_panel con índice {self.selected_canvas_task_index}")
        self._populate_inspector_panel(selected_task_object)
        # NUEVO: Actualizar estados visuales del árbol (amarillo/normal)
        # El setCurrentItem() anterior ya se encarga del resaltado rojo.
        self._update_task_tree_visual_states()
        self.logger.info("--- _on_card_selected finalizado ---")

    def _on_sidebar_task_clicked(self, item, column):
        """
        Se activa al hacer clic en una tarea de la biblioteca lateral.
        Busca la primera instancia de esa tarea en el canvas y la selecciona,
        reutilizando la lógica de _on_card_selected para unificar el comportamiento.
        """
        # 1. Asegurarse de que el item clickeado es una tarea (tiene un padre en el árbol)
        if not item.parent():
            return

        # 2. Obtener los datos de la tarea original del item del árbol
        task_data_from_tree = item.data(0, Qt.ItemDataRole.UserRole)
        if not task_data_from_tree:
            return

        original_task_id = task_data_from_tree.get('id')
        if not original_task_id:
            return

        # 3. Buscar la primera tarjeta en el canvas que corresponda a esa tarea original
        found_card_data = None
        for canvas_task in self.canvas_tasks:
            # Comparamos con el 'original_task_id' que guardamos al crear la tarjeta
            if canvas_task['data'].get('original_task_id') == original_task_id:
                found_card_data = canvas_task['data']
                break  # Nos detenemos en la primera que encontramos

        # 4. Si encontramos una tarjeta, simplemente llamamos a la función _on_card_selected.
        #    Esta función ya se encarga de todo: resaltar la tarjeta, poblar el inspector,
        #    y volver a resaltar el item en el árbol, asegurando un comportamiento consistente.
        if found_card_data:
            self._on_card_selected(found_card_data)
        else:
            self.logger.debug(f"La tarea '{task_data_from_tree.get('name')}' no está actualmente en el canvas.")


    def _is_task_auto_triggered(self, task_index):
        """
        Verifica si una tarea está configurada para iniciarse automáticamente
        desde otra tarea (es decir, otra tarea tiene a ésta como siguiente).
        MODIFICADO: Ahora también considera las dependencias estándar como auto-trigger.

        Args:
            task_index (int): Índice de la tarea a verificar en self.canvas_tasks.

        Returns:
            tuple: (bool, int|None) - (está_auto_triggered, índice_tarea_predecesora_o_None)
        """
        # Asegurarse de que el índice es válido
        if not (0 <= task_index < len(self.canvas_tasks)):
            return (False, None)

        # Iterar sobre todas las tareas para ver si alguna apunta a la tarea 'task_index'
        for i, canvas_task in enumerate(self.canvas_tasks):
            # No puede ser disparada por sí misma
            if i == task_index:
                continue

            config = canvas_task.get('config', {})

            # 1. Verificar si es la siguiente tarea en un ciclo
            next_cyclic = config.get('next_cyclic_task_index')
            if next_cyclic == task_index:
                # Sí, la tarea 'i' apunta a 'task_index' como su siguiente tarea cíclica
                self.logger.debug(f"Tarea {task_index} es auto-trigger (cíclico) desde tarea {i}")
                return (True, i)

        # 2. Verificar si OTRA tarea 'i' tiene a 'task_index' como dependencia DIRECTA
        # Es decir, buscar si 'task_index' es el 'value' de la dependencia de alguna tarea 'i'.
        # (Esto NO causa auto-trigger por sí solo, pero el informe lo pedía así para marcarla en verde)
        # Nota: La lógica original en el informe era un poco confusa. Una dependencia estándar
        # normalmente no fuerza el inicio, solo lo permite. Pero seguimos el informe para el color.
        # Corrección: Verificamos si la tarea *actual* (task_index) tiene una dependencia.
        current_task_config = self.canvas_tasks[task_index].get('config', {})
        current_start_condition = current_task_config.get('start_condition', {})
        if current_start_condition.get('type') == 'dependency':
            predecessor_index = current_start_condition.get('value')
            if predecessor_index is not None and 0 <= predecessor_index < len(self.canvas_tasks):
                # Esta tarea SÍ tiene una dependencia directa
                self.logger.debug(f"Tarea {task_index} tiene dependencia directa de tarea {predecessor_index}")
                # Según el informe FASE 4, esto debería considerarse auto-triggered para la visualización
                return (True, predecessor_index)

        # Si no se encontró ninguna tarea que la dispare automáticamente
        return (False, None)

    def _populate_inspector_panel(self, canvas_task):
        """
        Limpia y rellena el panel inspector con la configuración de la tarea seleccionada.

        Este método es el puente entre el canvas visual y los controles de edición. Toma
        una tarea del canvas y muestra todas sus propiedades en widgets editables, bloqueando
        señales durante el proceso para evitar actualizaciones circulares infinitas.

        Args:
            canvas_task: Diccionario con estructura {'data': dict, 'widget': CardWidget, 'config': dict}
                         o None si no hay ninguna tarea seleccionada
        """
        self.logger.debug(f"--- Poblando inspector para: {canvas_task['data']['name'] if canvas_task else 'None'} ---")

        # =============================================================================
        # PASO 1: Limpiar el layout del inspector de forma robusta
        # =============================================================================
        items_to_remove = []
        for i in range(self.inspector_layout.count()):
            item = self.inspector_layout.itemAt(i)
            if item:
                items_to_remove.append(item)

        for item in items_to_remove:
            widget = item.widget()
            if widget:
                self.inspector_layout.removeWidget(widget)
                widget.setParent(None)
                widget.setVisible(False)
            else:
                # Manejar layouts y spacers anidados
                layout_item = item.layout()
                if layout_item:
                    while layout_item.count():
                        sub_item = layout_item.takeAt(0)
                        if sub_item.widget():
                            sub_item.widget().deleteLater()
                    self.inspector_layout.removeItem(layout_item)
                elif item.spacerItem():
                    self.inspector_layout.removeItem(item.spacerItem())

        self.logger.debug(f"Inspector limpiado. Items restantes: {self.inspector_layout.count()}")

        # =============================================================================
        # PASO 2: Mostrar placeholder si no hay tarea seleccionada
        # =============================================================================
        if canvas_task is None:
            if 'placeholder' not in self.inspector_widgets:
                placeholder_label = QLabel(
                    "PANEL INSPECTOR\n\n"
                    "Selecciona una tarea en el canvas\n"
                    "para configurar sus detalles."
                )
                placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder_label.setWordWrap(True)
                placeholder_label.setStyleSheet("color: #777; font-size: 12px;")
                self.inspector_widgets['placeholder'] = placeholder_label

            self.inspector_layout.addWidget(self.inspector_widgets['placeholder'])
            self.inspector_widgets['placeholder'].setVisible(True)
            self.logger.debug("Inspector poblado con placeholder")
            return  # Terminar aquí si no hay tarea seleccionada

        # Ocultar el placeholder si existe porque hay una tarea seleccionada
        if 'placeholder' in self.inspector_widgets:
            self.inspector_widgets['placeholder'].setVisible(False)

        # =============================================================================
        # PASO 3: Agregar los grupos de widgets al layout en orden lógico
        # =============================================================================
        widget_order = [
            'title',  # Título de la tarea
            'duration_label',  # Duración base por unidad
            'start_condition_group',  # Condición de inicio (fecha o dependencia)
            'cycle_marker_group',  # Marcador de inicio de ciclo
            'prod_goals_group',  # Objetivos de producción (unidades, ciclos)
            'resources_group',  # Recursos (máquinas)
            'workers_group',  # Gestión de trabajadores
            'advanced_buttons_group',  # Botones de configuración avanzada
        ]

        for widget_name in widget_order:
            widget = self.inspector_widgets.get(widget_name)
            if widget:
                if widget.parentWidget() is None:
                    self.inspector_layout.addWidget(widget)
                widget.setVisible(True)
            else:
                self.logger.warning(f"Widget '{widget_name}' no encontrado al repoblar inspector")

        # =============================================================================
        # PASO 4: Bloquear señales de todos los widgets antes de poblarlos
        # =============================================================================
        # Esta es una medida crítica para evitar bucles infinitos. Cuando cambiamos
        # el valor de un widget programáticamente, este normalmente emite señales que
        # disparan _update_task_config, lo que a su vez puede volver a llamar a este
        # método. Bloqueamos las señales temporalmente para romper ese ciclo.

        widgets_to_block = [
            'cycle_start_checkbox',
            'start_date_radio', 'start_date_edit',
            'dependency_radio', 'dependency_combo', 'min_predecessor_units_spin',
            'total_units_spin', 'units_per_cycle_spin', 'next_cyclic_combo',
            'machine_combo',
            'available_workers_list', 'assigned_workers_list'
        ]

        self.logger.debug("Bloqueando señales de widgets antes de poblar...")
        for widget_name in widgets_to_block:
            widget = self.inspector_widgets.get(widget_name)
            if widget and hasattr(widget, 'blockSignals'):
                widget.blockSignals(True)

        try:
            # =========================================================================
            # PASO 5: Extraer datos de la tarea seleccionada
            # =========================================================================
            task_data = canvas_task['data']
            task_config = canvas_task['config']
            current_canvas_id = task_data.get('canvas_unique_id')

            # =========================================================================
            # PASO 6: Poblar información básica (título y duración)
            # =========================================================================
            task_name = task_data.get('name', 'SIN NOMBRE')
            self.inspector_widgets['title'].setText(f"<b>Propiedades de:</b>\n{task_name}")

            duration = task_data.get('duration_per_unit', task_data.get('duration', 0.0))
            self.inspector_widgets['duration_label'].setText(
                f"<i>Duración base por unidad: {duration:.2f} min</i>"
            )

            # =========================================================================
            # PASO 7: Poblar checkbox de inicio de ciclo
            # =========================================================================
            is_cycle_start = task_config.get('is_cycle_start', False)
            if 'cycle_start_checkbox' in self.inspector_widgets:
                self.inspector_widgets['cycle_start_checkbox'].setChecked(is_cycle_start)

            # =========================================================================
            # PASO 8: Poblar condición de inicio (fecha o dependencia)
            # =========================================================================
            start_cond = task_config.get('start_condition', {'type': 'date', 'value': datetime.now()})
            is_date_start = start_cond.get('type') == 'date'
            is_dependency_start = start_cond.get('type') == 'dependency'

            # Establecer qué radio button está activo
            self.inspector_widgets['start_date_radio'].setChecked(is_date_start)
            self.inspector_widgets['dependency_radio'].setChecked(is_dependency_start)

            # Poblar el campo de fecha si aplica
            if is_date_start:
                start_value = start_cond.get('value', datetime.now())
                # Asegurar que sea datetime completo
                if isinstance(start_value, date) and not isinstance(start_value, datetime):
                    work_start_time = self.schedule_config.WORK_START_TIME if self.schedule_config else time(8, 0)
                    start_datetime = datetime.combine(start_value, work_start_time)
                elif isinstance(start_value, datetime):
                    start_datetime = start_value
                else:
                    start_datetime = datetime.now()

                self.inspector_widgets['start_date_edit'].setDateTime(start_datetime)

            # Poblar combo de dependencias
            dependency_combo = self.inspector_widgets['dependency_combo']
            dependency_combo.clear()
            dependency_combo.addItem("--- Seleccione Tarea Padre ---", None)

            # Agregar todas las tareas ANTERIORES como opciones de dependencia
            for i in range(len(self.canvas_tasks)):
                if i < self.selected_canvas_task_index:  # Solo tareas anteriores
                    other_task = self.canvas_tasks[i]
                    other_name = other_task.get('data', {}).get('name', 'Tarea desconocida')
                    dependency_combo.addItem(f"Paso {i + 1}: {other_name}", i)

            # Establecer la dependencia guardada si existe
            if is_dependency_start:
                dependency_index = start_cond.get('value')
                if dependency_index is not None:
                    combo_idx = dependency_combo.findData(dependency_index)
                    if combo_idx != -1:
                        dependency_combo.setCurrentIndex(combo_idx)
                    else:
                        self.logger.warning(f"Dependencia guardada (índice {dependency_index}) no encontrada")
                        dependency_combo.setCurrentIndex(0)
                else:
                    dependency_combo.setCurrentIndex(0)

            # Poblar unidades mínimas del predecesor
            min_pred_units = task_config.get('min_predecessor_units', 1)
            self.inspector_widgets['min_predecessor_units_spin'].setValue(min_pred_units)

            # Habilitar/deshabilitar widgets según el tipo de inicio
            self._toggle_start_condition_widgets()

            # =========================================================================
            # PASO 9: Verificar si la tarea es auto-triggered y mostrar advertencia
            # =========================================================================
            is_auto_triggered, predecessor_index = self._is_task_auto_triggered(self.selected_canvas_task_index)

            # Crear o reutilizar el label de advertencia
            if not hasattr(self, '_auto_trigger_warning_label'):
                self._auto_trigger_warning_label = QLabel()
                self._auto_trigger_warning_label.setWordWrap(True)
                self._auto_trigger_warning_label.setStyleSheet("""
                    QLabel {
                        background-color: #fff3cd;
                        color: #856404;
                        border: 1px solid #ffeeba;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 11px;
                    }
                """)
                # Insertar después del grupo de condición de inicio
                start_group_index = self.inspector_layout.indexOf(self.inspector_widgets['start_condition_group'])
                if start_group_index != -1:
                    self.inspector_layout.insertWidget(start_group_index + 1, self._auto_trigger_warning_label)

            if is_auto_triggered and predecessor_index is not None:
                # Deshabilitar controles de inicio
                start_date_radio = self.inspector_widgets.get('start_date_radio')
                dependency_radio = self.inspector_widgets.get('dependency_radio')
                if start_date_radio:
                    start_date_radio.setEnabled(False)
                if dependency_radio:
                    dependency_radio.setEnabled(False)

                # Mostrar advertencia explicativa
                if 0 <= predecessor_index < len(self.canvas_tasks):
                    pred_name = self.canvas_tasks[predecessor_index]['data'].get('name', 'Tarea desconocida')
                    self._auto_trigger_warning_label.setText(
                        f"⚠️ <b>Inicio Automático por Ciclo</b><br>"
                        f"Esta tarea se activa automáticamente cuando <b>{pred_name}</b> "
                        f"completa su ciclo. La configuración de inicio está deshabilitada."
                    )
                    self._auto_trigger_warning_label.show()
            else:
                # Habilitar controles normalmente
                start_date_radio = self.inspector_widgets.get('start_date_radio')
                dependency_radio = self.inspector_widgets.get('dependency_radio')
                if start_date_radio:
                    start_date_radio.setEnabled(True)
                if dependency_radio:
                    dependency_radio.setEnabled(True)

                self._auto_trigger_warning_label.hide()

            # =========================================================================
            # PASO 10: Poblar objetivos de producción
            # =========================================================================
            total_units = task_config.get('total_units', self.units)
            units_per_cycle = task_config.get('units_per_cycle', 1)

            self.inspector_widgets['total_units_spin'].setValue(total_units)
            # Ajustar el máximo del ciclo al total de unidades
            self.inspector_widgets['units_per_cycle_spin'].setMaximum(total_units)
            # Asegurar que el valor no exceda el máximo
            self.inspector_widgets['units_per_cycle_spin'].setValue(min(units_per_cycle, total_units))

            # =========================================================================
            # PASO 11: Poblar combo de siguiente tarea cíclica (SIN DUPLICADOS)
            # =========================================================================
            next_combo = self.inspector_widgets['next_cyclic_combo']
            next_combo.clear()
            next_combo.addItem("--- Ninguna ---", None)

            # Separar tareas en dos grupos: madre (inicio de ciclo) y normales
            tareas_madre = []
            tareas_normales = []

            for i, task_on_canvas in enumerate(self.canvas_tasks):
                other_task_data = task_on_canvas.get('data', {})
                other_task_config = task_on_canvas.get('config', {})

                # Saltar la tarea actual (no puede ser siguiente de sí misma)
                if other_task_data.get('canvas_unique_id') == current_canvas_id:
                    continue

                task_name = other_task_data.get('name', 'Tarea sin nombre')
                is_cycle_start_other = other_task_config.get('is_cycle_start', False)

                # Crear nombre descriptivo con indicador visual
                if is_cycle_start_other:
                    display_name = f"⭐ Paso {i + 1}: {task_name}"
                    tareas_madre.append((display_name, i))
                else:
                    display_name = f"Paso {i + 1}: {task_name}"
                    tareas_normales.append((display_name, i))

            # Agregar primero las tareas madre (son las más comunes como destino)
            if tareas_madre:
                for display_name, index in tareas_madre:
                    next_combo.addItem(display_name, index)

            # Luego agregar las tareas normales
            if tareas_normales:
                # Agregar separador visual si hay tareas madre arriba
                if tareas_madre:
                    next_combo.insertSeparator(next_combo.count())
                for display_name, index in tareas_normales:
                    next_combo.addItem(display_name, index)

            # Establecer el valor guardado en el combo
            saved_next_index = task_config.get('next_cyclic_task_index')
            if saved_next_index is not None:
                combo_idx = next_combo.findData(saved_next_index)
                if combo_idx != -1:
                    next_combo.setCurrentIndex(combo_idx)
                else:
                    self.logger.warning(f"Índice cíclico guardado ({saved_next_index}) no es válido")
                    task_config['next_cyclic_task_index'] = None
                    next_combo.setCurrentIndex(0)
            else:
                next_combo.setCurrentIndex(0)

            # =========================================================================
            # PASO 12: Poblar combo de máquinas
            # =========================================================================
            machine_combo = self.inspector_widgets['machine_combo']
            machine_combo.clear()

            tipo_maquina_req = task_data.get('requiere_maquina_tipo')
            machine_combo.setEnabled(bool(tipo_maquina_req))

            if tipo_maquina_req:
                try:
                    available_machines = self.controller.model.get_machines_by_process_type(tipo_maquina_req)
                    machine_combo.addItem("--- Seleccione Máquina ---", None)

                    # Ahora usamos atributos DTO: id, nombre
                    for machine in available_machines:
                        machine_combo.addItem(machine.nombre, machine.id)

                    saved_machine_id = task_config.get('machine_id')
                    if saved_machine_id:
                        machine_idx = machine_combo.findData(saved_machine_id)
                        if machine_idx != -1:
                            machine_combo.setCurrentIndex(machine_idx)
                        else:
                            self.logger.warning(f"Máquina guardada ({saved_machine_id}) no encontrada")
                            task_config['machine_id'] = None
                            machine_combo.setCurrentIndex(0)
                    else:
                        machine_combo.setCurrentIndex(0)
                except AttributeError as e:
                    self.logger.error(f"Error accediendo al modelo de máquinas: {e}")
                    machine_combo.addItem("Error cargando máquinas")
                    machine_combo.setEnabled(False)
            else:
                machine_combo.addItem("No requiere máquina")
                machine_combo.setEnabled(False)

            # =========================================================================
            # PASO 13: Poblar listas de trabajadores
            # =========================================================================
            assigned_workers_config = task_config.get('workers', [])
            self.inspector_widgets['available_workers_list'].clear()
            self.inspector_widgets['assigned_workers_list'].clear()
            self.inspector_widgets['reassignment_button'].setEnabled(False)

            # Crear set de nombres asignados para filtrar disponibles
            assigned_names = set(
                w.get('name') for w in assigned_workers_config
                if isinstance(w, dict) and w.get('name')
            )

            # Poblar lista de asignados con indicador de regla de reasignación
            for worker_config in assigned_workers_config:
                if isinstance(worker_config, dict):
                    worker_name = worker_config.get('name')
                    if not worker_name:
                        continue
                    # Agregar emoji si tiene regla de reasignación
                    display_name = worker_name + (" 🔧" if worker_config.get('reassignment_rule') else "")
                    self.inspector_widgets['assigned_workers_list'].addItem(display_name)
                elif isinstance(worker_config, str):
                    # Formato antiguo: solo string del nombre
                    self.inspector_widgets['assigned_workers_list'].addItem(worker_config)
                    assigned_names.add(worker_config)

            # Poblar lista de disponibles (todos menos los asignados)
            all_workers = self.workers if isinstance(self.workers, list) else []
            for worker_name in all_workers:
                if worker_name not in assigned_names:
                    self.inspector_widgets['available_workers_list'].addItem(worker_name)

        except KeyError as e:
            self.logger.error(f"Error de clave al poblar inspector: Falta '{e}'", exc_info=True)
        except Exception as e:
            self.logger.error(f"Error inesperado al poblar inspector: {e}", exc_info=True)
            # En caso de error grave, mostrar el placeholder
            if 'placeholder' in self.inspector_widgets:
                self.inspector_layout.addWidget(self.inspector_widgets['placeholder'])
                self.inspector_widgets['placeholder'].setVisible(True)
        finally:
            # =========================================================================
            # PASO 14: Desbloquear señales (SIEMPRE se ejecuta, incluso si hay error)
            # =========================================================================
            self.logger.debug("Desbloqueando señales después de poblar...")
            for widget_name in widgets_to_block:
                widget = self.inspector_widgets.get(widget_name)
                if widget and hasattr(widget, 'blockSignals'):
                    widget.blockSignals(False)

        self.logger.debug(f"--- Inspector poblado para índice {self.selected_canvas_task_index} ---")

    def _update_canvas_size(self):
        """
        Actualiza dinámicamente el tamaño del canvas para acomodar todas las tarjetas,
        permitiendo crecimiento en las cuatro direcciones con padding adecuado.
        """
        if not self.canvas_tasks:
            # Tamaño por defecto cuando no hay tarjetas
            self.canvas.setMinimumSize(2000, 2000)
            return

        # Encontrar los límites de las tarjetas en las 4 direcciones
        min_x = float('inf')
        min_y = float('inf')
        max_x = 0
        max_y = 0

        for task in self.canvas_tasks:
            card_widget = task['widget']
            left_edge = card_widget.x()
            top_edge = card_widget.y()
            right_edge = card_widget.x() + card_widget.width()
            bottom_edge = card_widget.y() + card_widget.height()

            if left_edge < min_x:
                min_x = left_edge
            if top_edge < min_y:
                min_y = top_edge
            if right_edge > max_x:
                max_x = right_edge
            if bottom_edge > max_y:
                max_y = bottom_edge

        # Padding en todos los lados
        padding = 300

        # Si hay tarjetas con coordenadas negativas, necesitamos ajustar
        # Calculamos el offset necesario
        offset_x = max(0, padding - min_x)
        offset_y = max(0, padding - min_y)

        # Si necesitamos offset, mover todas las tarjetas
        if offset_x > 0 or offset_y > 0:
            for task in self.canvas_tasks:
                card_widget = task['widget']
                # --- CORRECCIÓN: Usar QPoint para la nueva posición ---
                new_pos = QPoint(card_widget.x() + int(offset_x), card_widget.y() + int(offset_y))
                card_widget.move(new_pos)

            # Recalcular límites después del movimiento
            max_x += offset_x
            max_y += offset_y
            # --- NUEVO: Actualizar min_x y min_y también ---
            min_x += offset_x
            min_y += offset_y

        # Calcular el nuevo tamaño del canvas
        # Asegurarse de que sea al menos tan grande como el viewport
        # --- VERIFICACIÓN: Asegurarse de que self.canvas_scroll_area existe ---
        if not hasattr(self, 'canvas_scroll_area') or not self.canvas_scroll_area:
            self.logger.error("self.canvas_scroll_area no está definido en _update_canvas_size")
            # Fallback a un tamaño grande si no hay scroll area
            viewport_width = 2000
            viewport_height = 2000
        else:
            viewport_width = self.canvas_scroll_area.viewport().width()
            viewport_height = self.canvas_scroll_area.viewport().height()

        new_width = max(viewport_width, int(max_x + padding))
        new_height = max(viewport_height, int(max_y + padding))

        # Aplicar el nuevo tamaño
        # --- CAMBIO: Usar resize() además de setMinimumSize() ---
        self.canvas.setMinimumSize(new_width, new_height)
        self.canvas.resize(new_width, new_height)  # Asegura que el tamaño se aplique

        self.logger.debug(f"Canvas redimensionado a {new_width}x{new_height}")

    def _on_card_moved(self):
        """Se ejecuta cuando una tarjeta termina de moverse."""
        self._update_canvas_connections()
        self._update_canvas_size()

    def _update_canvas_connections(self):
        """
        Construye la lista de TODAS las conexiones (dependencias y ciclos)
        y le pide al canvas que se redibuje.
        """
        connections = []
        # Iteramos sobre todas las tareas que hemos añadido al canvas
        for i, task_info in enumerate(self.canvas_tasks):
            config = task_info.get('config', {})

            # --- 1. Buscar dependencias normales (previous_task_index) ---
            start_condition = config.get('start_condition', {})
            if start_condition.get('type') == 'dependency':
                parent_index = start_condition.get('value')
                if parent_index is not None and 0 <= parent_index < len(self.canvas_tasks):
                    start_widget = self.canvas_tasks[parent_index]['widget']
                    end_widget = task_info['widget']
                    # Añadimos un diccionario con el tipo de conexión
                    connections.append({
                        'start': start_widget,
                        'end': end_widget,
                        'type': 'dependency'  # Identificador para dependencias normales
                    })

            # --- 2. ✨ NUEVO: Buscar conexiones cíclicas (next_cyclic_task_index) ---
            cyclic_next_index = config.get('next_cyclic_task_index')
            if cyclic_next_index is not None and 0 <= cyclic_next_index < len(self.canvas_tasks):
                start_widget = task_info['widget']  # La tarea actual es el origen
                end_widget = self.canvas_tasks[cyclic_next_index]['widget']  # La tarea siguiente es el destino
                # Añadimos un diccionario con el tipo de conexión 'cyclic'
                connections.append({
                    'start': start_widget,
                    'end': end_widget,
                    'type': 'cyclic'  # Identificador para conexiones de ciclo
                })

        # Le pasamos la lista completa de conexiones al canvas para que las dibuje
        self.canvas.set_connections(connections)

        # ✨ NUEVO: Actualizar efectos visuales cuando cambien las conexiones
        self._update_all_cycle_effects()

    def _update_task_config(self):
        """Lee el estado del inspector y actualiza el diccionario 'config' de la tarea seleccionada."""
        # --- VERIFICACIÓN INICIAL ROBUSTA ---
        if self.selected_canvas_task_index is None or not (
                0 <= self.selected_canvas_task_index < len(self.canvas_tasks)):
            # self.logger.debug("_update_task_config called but no task selected or index invalid. Aborting.")
            return

        self.logger.info(f"--- 🔄 Updating config for task index {self.selected_canvas_task_index} ---")

        # --- Referencia directa a la configuración ---
        try:
            config = self.canvas_tasks[self.selected_canvas_task_index]['config']
        except IndexError:
            self.logger.error(
                f"  🚨 ERROR CRÍTICO AL ACCEDER: El índice {self.selected_canvas_task_index} es inválido para self.canvas_tasks (tamaño {len(self.canvas_tasks)}).")
            return  # Salir si el índice es incorrecto

        # <<< CORRECCIÓN: Definir widgets_to_block ANTES del try >>>
        widgets_to_block = [
            'start_date_radio', 'start_date_edit', 'dependency_radio',
            'dependency_combo', 'min_predecessor_units_spin',
            'total_units_spin', 'units_per_cycle_spin', 'next_cyclic_combo',
            'machine_combo'
        ]

        # --- Bloquear señales temporalmente ---
        for widget_name in widgets_to_block:
            widget = self.inspector_widgets.get(widget_name)
            if widget and hasattr(widget, 'blockSignals'):
                widget.blockSignals(True)

        try:
            # <<< INICIO BLOQUE DE DEPURACIÓN (Verificación de widgets) >>>
            import json  # Asegúrate de que json está importado al inicio del archivo si no lo está ya
            self.logger.debug(f"   Config ANTES: {json.dumps(config, default=str)}")
            missing_widget = False
            for w_name in widgets_to_block:  # Usar la lista ya definida
                if w_name not in self.inspector_widgets or self.inspector_widgets[w_name] is None:
                    self.logger.error(f"   🚨 ERROR CRÍTICO: Widget '{w_name}' no encontrado en self.inspector_widgets.")
                    missing_widget = True
            if missing_widget:
                # Salir si falta un widget esencial
                # (El bloque finally se ejecutará para desbloquear señales)
                return
            # <<< FIN BLOQUE DE DEPURACIÓN >>>

            # --- Lectura y Actualización de la Configuración ---

            # 1. Actualizar Condición de Inicio
            if self.inspector_widgets['start_date_radio'].isChecked():
                # Leer valor y asegurar que es datetime
                dt_value = self.inspector_widgets['start_date_edit'].dateTime().toPyDateTime()
                config['start_condition'] = {'type': 'date', 'value': dt_value}
                self.logger.debug(f"   Start condition set to date: {dt_value}")
            else:  # Dependency radio is checked
                dependency_index = self.inspector_widgets['dependency_combo'].currentData()
                config['start_condition'] = {'type': 'dependency', 'value': dependency_index}
                self.logger.debug(f"   Start condition set to dependency: index {dependency_index}")

            # 2. Actualizar Objetivos de Producción
            total_units = self.inspector_widgets['total_units_spin'].value()
            config['total_units'] = total_units
            self.logger.debug(f"   Total units set to: {total_units}")

            # Ajustar el máximo del spinbox de ciclo ANTES de leer su valor
            self.inspector_widgets['units_per_cycle_spin'].setMaximum(total_units)
            units_per_cycle = self.inspector_widgets['units_per_cycle_spin'].value()
            # Asegurar que no supere el total (doble verificación)
            if units_per_cycle > total_units:
                units_per_cycle = total_units
                self.inspector_widgets['units_per_cycle_spin'].setValue(
                    units_per_cycle)  # Corregir visualmente si es necesario
            config['units_per_cycle'] = units_per_cycle
            self.logger.debug(f"   Units per cycle set to: {units_per_cycle}")

            next_cyclic_index = self.inspector_widgets['next_cyclic_combo'].currentData()
            config['next_cyclic_task_index'] = next_cyclic_index
            self.logger.debug(f"   Next cyclic index set to: {next_cyclic_index}")

            # 3. Actualizar Unidades Mínimas del Predecesor
            min_pred_units = self.inspector_widgets['min_predecessor_units_spin'].value()
            config['min_predecessor_units'] = min_pred_units
            self.logger.debug(f"   Min predecessor units set to: {min_pred_units}")

            # 4. Actualizar Máquina
            machine_id = self.inspector_widgets['machine_combo'].currentData()
            config['machine_id'] = machine_id
            self.logger.debug(f"   Machine ID set to: {machine_id}")

            # 5. NUEVO: Guardar estado de inicio de ciclo
            # Asegurarnos de que el widget existe antes de leerlo
            if 'cycle_start_checkbox' in self.inspector_widgets:
                is_start = self.inspector_widgets['cycle_start_checkbox'].isChecked()
                config['is_cycle_start'] = is_start
                self.logger.debug(f"   Is cycle start set to: {is_start}")

                # Si se marca o desmarca, actualizar el efecto visual correspondiente
                if is_start:
                    self._apply_cycle_start_effect(self.selected_canvas_task_index)
                else:
                    self._remove_cycle_start_effect(self.selected_canvas_task_index)
            else:
                self.logger.warning("Widget 'cycle_start_checkbox' no encontrado al guardar config.")

            self.logger.debug(f"   Config DESPUÉS: {json.dumps(config, default=str)}")

            # <<< INICIO BLOQUE DE VERIFICACIÓN >>>
            total_units_after = self.inspector_widgets['total_units_spin'].value()
            units_per_cycle_after = self.inspector_widgets['units_per_cycle_spin'].value()
            next_cyclic_idx_after = self.inspector_widgets['next_cyclic_combo'].currentData()
            self.logger.debug(
                f"   Valores widgets DESPUÉS: total_u={total_units_after}, u_cycle={units_per_cycle_after}, next_idx={next_cyclic_idx_after}")
            mismatch = False
            if total_units_after != config['total_units']:
                self.logger.warning(
                    f"    ⚠️ Discrepancia en total_units! Widget={total_units_after}, Config={config['total_units']}")
                mismatch = True
            if units_per_cycle_after != config['units_per_cycle']:
                self.logger.warning(
                    f"    ⚠️ Discrepancia en units_per_cycle! Widget={units_per_cycle_after}, Config={config['units_per_cycle']}")
                mismatch = True
            if next_cyclic_idx_after != config['next_cyclic_task_index']:
                self.logger.warning(
                    f"    ⚠️ Discrepancia en next_cyclic_task_index! Widget={next_cyclic_idx_after}, Config={config['next_cyclic_task_index']}")
                mismatch = True
            if mismatch:
                self.logger.error(
                    "    🚨 ¡Valores en widgets no coinciden con 'config' guardada inmediatamente después!")
            # <<< FIN BLOQUE DE VERIFICACIÓN >>>

        except Exception as e:
            self.logger.error(f"  🚨 ERROR inesperado durante _update_task_config: {e}", exc_info=True)
            # Asegurarse de que las señales se desbloqueen incluso si hay un error
        finally:
            # --- Desbloquear señales ---
            # <<< CORRECCIÓN: Usar la lista definida fuera del try >>>
            for widget_name in widgets_to_block:
                widget = self.inspector_widgets.get(widget_name)
                if widget and hasattr(widget, 'blockSignals'):
                    # self.logger.debug(f"   Unblocking signals for {widget_name}") # Log opcional
                    widget.blockSignals(False)
            self.logger.debug("--- Señales desbloqueadas ---")

        # Actualizar las conexiones visuales en el canvas (fuera del finally)
        self._update_canvas_connections()
        self.logger.info(
            f"--- ✅ Configuración actualizada y conexiones redibujadas para índice {self.selected_canvas_task_index} ---")

    def _apply_cycle_start_effect(self, task_index):
        """Aplica el efecto visual de inicio de ciclo a una tarjeta."""
        if not (0 <= task_index < len(self.canvas_tasks)):
            self.logger.warning(f"Índice inválido {task_index} al aplicar efecto ciclo.")
            return

        canvas_task = self.canvas_tasks[task_index]
        card_widget = canvas_task.get('widget')
        if not card_widget:
            self.logger.warning(f"No se encontró widget para tarea índice {task_index}.")
            return

        # Verificar si ya tiene el efecto (usando un atributo en canvas_task)
        if canvas_task.get('golden_glow_effect_widget'):
            # Ya existe, forzar actualización de geometría y asegurar visibilidad
            effect_widget = canvas_task['golden_glow_effect_widget']
            effect_widget._update_geometry()
            effect_widget.show()
            effect_widget.raise_()
            self.logger.debug(f"Efecto de ciclo ya existe para índice {task_index}, actualizado.")
            return

        # Crear y aplicar el efecto
        effect_widget = GoldenGlowEffect(card_widget)
        # Guardar la referencia en el diccionario de la tarea, NO en el widget
        canvas_task['golden_glow_effect_widget'] = effect_widget
        self.logger.info(f"Efecto de inicio de ciclo aplicado a tarea en índice {task_index}")

        # CRÍTICO: Programar una actualización de geometría después de que el layout se estabilice
        # Esto asegura que el efecto se posicione correctamente incluso si el canvas
        # reorganiza las tarjetas después de crear el efecto
        QTimer.singleShot(100, effect_widget._update_geometry)
        QTimer.singleShot(200, effect_widget._update_geometry)
        QTimer.singleShot(500, effect_widget._update_geometry)

    def _remove_cycle_start_effect(self, task_index):
        """Elimina el efecto visual de inicio de ciclo de una tarjeta."""
        if not (0 <= task_index < len(self.canvas_tasks)):
            # No es un error si el índice es inválido aquí, simplemente no hacemos nada
            # self.logger.debug(f"Índice inválido {task_index} al quitar efecto ciclo.")
            return

        canvas_task = self.canvas_tasks[task_index]

        # Verificar si tiene el efecto guardado en su diccionario
        effect_widget = canvas_task.get('golden_glow_effect_widget')
        if effect_widget:
            effect_widget.stop_animation()  # Detener timer
            effect_widget.deleteLater()  # Eliminar el widget de forma segura
            # Eliminar la referencia del diccionario
            canvas_task['golden_glow_effect_widget'] = None
            self.logger.info(f"Efecto de inicio de ciclo eliminado de tarea en índice {task_index}")

    def _update_all_cycle_start_effects(self):
        """
        Actualiza los efectos visuales de todas las tareas según su config.
        CORREGIDO: Usa timers para asegurar que el canvas se estabilice antes de posicionar efectos.
        """
        self.logger.debug("Actualizando todos los efectos visuales de inicio de ciclo...")

        for i, canvas_task in enumerate(self.canvas_tasks):
            # Obtener el estado de la configuración de forma segura
            is_cycle_start = canvas_task.get('config', {}).get('is_cycle_start', False)

            if is_cycle_start:
                # Aplicar o actualizar el efecto
                self._apply_cycle_start_effect(i)
            else:
                # Remover el efecto si no debería estar
                self._remove_cycle_start_effect(i)

        # ✨ NUEVO: También actualizar efectos verdes y mixtos
        self._update_all_cycle_effects()

        # CRÍTICO: Programar actualizaciones de geometría escalonadas
        # Esto da tiempo al canvas para reorganizar las tarjetas antes de actualizar los efectos
        def update_all_geometries():
            """Función auxiliar para actualizar todas las geometrías de los efectos."""
            for canvas_task in self.canvas_tasks:
                effect_widget = canvas_task.get('golden_glow_effect_widget')
                if effect_widget:
                    effect_widget._update_geometry()
                    effect_widget.show()
                    effect_widget.raise_()
            self.logger.debug("Geometrías de efectos actualizadas")

        # Programar múltiples actualizaciones para capturar diferentes momentos del layout
        QTimer.singleShot(50, update_all_geometries)  # Primera actualización rápida
        QTimer.singleShot(150, update_all_geometries)  # Segunda actualización
        QTimer.singleShot(300, update_all_geometries)  # Tercera actualización
        QTimer.singleShot(500, update_all_geometries)  # Actualización final

    def _toggle_start_condition_widgets(self):
        """
        Actualiza inmediatamente el estado de habilitación de los widgets
        según qué radio button esté seleccionado.
        """
        if self.selected_canvas_task_index is None:
            return

        # Determinar qué radio está seleccionado
        is_date_selected = self.inspector_widgets['start_date_radio'].isChecked()
        is_dependency_selected = self.inspector_widgets['dependency_radio'].isChecked()

        # Activar/desactivar los widgets correspondientes
        self.inspector_widgets['start_date_edit'].setEnabled(is_date_selected)
        self.inspector_widgets['dependency_combo'].setEnabled(is_dependency_selected)
        self.inspector_widgets['min_predecessor_units_spin'].setEnabled(is_dependency_selected)  # ✅ NUEVO

        self.logger.debug(
            f"Widgets de condición de inicio actualizados: fecha={is_date_selected}, "
            f"dependencia={is_dependency_selected}"
        )

    def _handle_assign_worker(self):
        """Mueve un trabajador de la lista de disponibles a asignados."""
        if self.selected_canvas_task_index is None: return
        selected_item = self.inspector_widgets['available_workers_list'].currentItem()
        if not selected_item: return

        worker_name = selected_item.text()

        # Añadimos el trabajador a la configuración con una regla de reasignación nula por defecto
        self.canvas_tasks[self.selected_canvas_task_index]['config']['workers'].append({
            'name': worker_name,
            'reassignment_rule': None
        })

        # Repoblamos las listas para reflejar el cambio
        self._populate_inspector_panel(self.canvas_tasks[self.selected_canvas_task_index])

    def _handle_unassign_worker(self):
        """Mueve un trabajador de la lista de asignados a disponibles."""
        if self.selected_canvas_task_index is None: return
        selected_item = self.inspector_widgets['assigned_workers_list'].currentItem()
        if not selected_item: return

        worker_name_to_remove = selected_item.text()

        # Filtramos la lista de trabajadores para eliminar el seleccionado
        current_workers = self.canvas_tasks[self.selected_canvas_task_index]['config']['workers']
        self.canvas_tasks[self.selected_canvas_task_index]['config']['workers'] = [
            w for w in current_workers if w['name'] != worker_name_to_remove
        ]

        self._populate_inspector_panel(self.canvas_tasks[self.selected_canvas_task_index])

    def _open_cycle_end_dialog(self):
        """Abre el diálogo de configuración de fin de ciclo para la tarea seleccionada."""
        # Verificar que hay una tarea seleccionada
        if self.selected_canvas_task_index is None or not (
                0 <= self.selected_canvas_task_index < len(self.canvas_tasks)):
            self.logger.warning("Intento de configurar fin de ciclo sin tarea seleccionada.")
            # Podrías mostrar un mensaje al usuario aquí si lo deseas
            # QMessageBox.information(self, "Selección Requerida", "Seleccione una tarea en el canvas primero.")
            return

        self.logger.info(f"Abriendo diálogo de fin de ciclo para tarea índice {self.selected_canvas_task_index}")

        # Crear y mostrar el diálogo
        dialog = CycleEndConfigDialog(
            current_task_index=self.selected_canvas_task_index,
            all_canvas_tasks=self.canvas_tasks,
            parent=self  # El diálogo padre es el EnhancedProductionFlowDialog
        )

        # Si el usuario acepta los cambios en el diálogo
        if dialog.exec():
            # Obtener la configuración seleccionada por el usuario en el diálogo
            new_cycle_config = dialog.get_configuration()
            is_now_cycle_end = new_cycle_config['is_cycle_end']
            new_return_index = new_cycle_config['return_to_index']  # Puede ser None o un int

            # Actualizar la configuración ('config') de la tarea actualmente seleccionada
            try:
                current_task_config = self.canvas_tasks[self.selected_canvas_task_index]['config']

                # Guardar los nuevos valores
                current_task_config['is_cycle_end'] = is_now_cycle_end
                current_task_config['cycle_return_to_index'] = new_return_index

                # --- Lógica de Sincronización ---
                # Si se marcó como fin de ciclo Y se seleccionó una tarea de retorno VÁLIDA:
                if is_now_cycle_end and new_return_index is not None:
                    # Actualizamos 'next_cyclic_task_index' para que apunte a la tarea de retorno.
                    # Esto crea o actualiza la flecha verde de ciclo.
                    current_task_config['next_cyclic_task_index'] = new_return_index
                    self.logger.info(
                        f"Tarea {self.selected_canvas_task_index} configurada como fin de ciclo, "
                        f"regresando a tarea {new_return_index}"
                    )
                # Si se DESMARCÓ como fin de ciclo O se seleccionó "(No regresar...)":
                elif not is_now_cycle_end or new_return_index is None:
                    # Debemos comprobar si 'next_cyclic_task_index' estaba apuntando
                    # a la tarea que *antes* era la de retorno, para limpiarlo.
                    # Obtenemos el índice al que apuntaba *antes* de guardar (puede ser None).
                    previous_return_index = current_task_config.get(
                        'cycle_return_to_index')  # OJO: Aquí usamos el valor que *ya estaba* en config

                    # Si el 'next_cyclic_task_index' actual coincide con el índice de retorno *anterior*,
                    # significa que este enlace cíclico se creó por la configuración de "Fin de Ciclo".
                    # Ahora que ya no es fin de ciclo (o no regresa a ningún sitio), debemos eliminar ese enlace.
                    if current_task_config.get('next_cyclic_task_index') == previous_return_index:
                        current_task_config['next_cyclic_task_index'] = None
                        self.logger.info(
                            f"Tarea {self.selected_canvas_task_index} ya no es fin de ciclo "
                            f"o no regresa a ninguna tarea. Enlace cíclico eliminado (si existía por esta causa)."
                        )
                    # Si 'next_cyclic_task_index' apuntaba a otro sitio (configurado manualmente),
                    # no lo tocamos.

                # --- Fin Lógica de Sincronización ---

                # Actualizar las conexiones visuales (flechas) en el canvas
                self._update_canvas_connections()

                # Mensaje de confirmación para el usuario
                QMessageBox.information(
                    self,
                    "Configuración Guardada",
                    "La configuración de fin de ciclo ha sido guardada correctamente.",
                    QMessageBox.StandardButton.Ok
                )

            except IndexError:
                self.logger.error(
                    f"Error: Índice {self.selected_canvas_task_index} fuera de rango al guardar config de fin de ciclo.")
                QMessageBox.critical(self, "Error Interno", "No se pudo guardar la configuración. Índice inválido.")
            except Exception as e:
                self.logger.error(f"Error inesperado al guardar config de fin de ciclo: {e}", exc_info=True)
                QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error: {e}")
        else:
            self.logger.info("Usuario canceló la configuración de fin de ciclo.")

    def _handle_configure_reassignment(self):
        """Abre el diálogo de configuración de reglas para el trabajador seleccionado."""
        if self.selected_canvas_task_index is None: return

        selected_items = self.inspector_widgets['assigned_workers_list'].selectedItems()
        if not selected_items: return

        # El nombre puede tener el icono, lo limpiamos
        selected_worker_name = selected_items[0].text().replace(" 🔧", "").strip()

        # Buscamos la tarea y la configuración del trabajador actual
        current_canvas_task = self.canvas_tasks[self.selected_canvas_task_index]
        worker_config = next((w for w in current_canvas_task['config']['workers'] if w['name'] == selected_worker_name),
                             None)

        if worker_config is None: return  # Cortafuegos de seguridad

        # Abrimos el nuevo diálogo
        dialog = ReassignmentRuleDialog(
            worker_name=selected_worker_name,
            current_task=current_canvas_task['data'],
            all_canvas_tasks=self.canvas_tasks,
            current_rule=worker_config['reassignment_rule'],
            parent=self
        )

        if dialog.exec():
            # Si el usuario acepta, guardamos la nueva regla
            new_rule = dialog.get_rule()
            worker_config['reassignment_rule'] = new_rule
            self.logger.info(f"Regla de reasignación actualizada para '{selected_worker_name}': {new_rule}")

            # Repoblamos el inspector para que se vea el icono 🔧 si es necesario
            self._populate_inspector_panel(current_canvas_task)

    def get_production_flow(self):
        """
        Construye la lista final 'production_flow' a partir de los datos
        configurados para cada tarea en el canvas, incluyendo TODA la configuración
        y la posición de la tarjeta.
        VERSIÓN REFORZADA: Asegura la inclusión explícita de todos los campos.
        """
        final_flow = []
        # Crear un mapa de canvas_unique_id a índice actual para resolver dependencias
        id_to_index_map = {task['data'].get('canvas_unique_id'): i
                           for i, task in enumerate(self.canvas_tasks)
                           if task.get('data', {}).get('canvas_unique_id')}

        for i, canvas_task in enumerate(self.canvas_tasks):
            task_data_original = canvas_task.get('data', {})
            task_config = canvas_task.get('config', {})
            widget = canvas_task.get('widget')

            if not task_data_original or not widget:
                self.logger.warning(f"Saltando tarea inválida en el índice {i} durante get_production_flow.")
                continue

            # --- Extraer y procesar la configuración de inicio ---
            start_cond = task_config.get('start_condition', {})
            start_date_value = None
            previous_task_index = None  # Guardamos el índice relativo al canvas_tasks

            if start_cond.get('type') == 'date' and start_cond.get('value'):
                value = start_cond['value']
                if isinstance(value, datetime):
                    start_date_value = value
                elif isinstance(value, date):
                    start_time_config = getattr(self.schedule_config, 'WORK_START_TIME', time(8, 0))
                    start_date_value = datetime.combine(value, start_time_config)
            elif start_cond.get('type') == 'dependency':
                # Guardamos el índice del canvas, la conversión a ID único se hará en el repositorio
                previous_task_index = start_cond.get('value')

            # --- Construir el diccionario del paso ---
            step_dict = {
                # Datos base de la tarea (se necesita una copia limpia sin IDs de canvas)
                "task": {
                    key: val for key, val in task_data_original.items()
                    if key not in ['canvas_unique_id']  # Excluimos IDs temporales
                },
                "workers": task_config.get('workers', []),  # Incluye reglas de reasignación
                "machine_id": task_config.get('machine_id'),

                # --- Campos de configuración importantes ---
                "trigger_units": task_config.get('total_units', self.units),
                "min_predecessor_units": task_config.get('min_predecessor_units', 1),
                "units_per_cycle": task_config.get('units_per_cycle', 1),
                # Guardamos el índice relativo al canvas para la tarea cíclica
                "next_cyclic_task_index": task_config.get('next_cyclic_task_index'),
                # --- CRÍTICO: Campos de control de ciclo ---
                "is_cycle_start": task_config.get('is_cycle_start', False),
                "is_cycle_end": task_config.get('is_cycle_end', False),
                "cycle_return_to_index": task_config.get('cycle_return_to_index'),

                # --- Campos de inicio ---
                "start_date": start_date_value,  # datetime o None
                "previous_task_index": previous_task_index,  # Índice del canvas o None

                # --- Información de la UI ---
                "position": {"x": widget.x(), "y": widget.y()}
            }
            # Asegurar que las reglas de reasignación se incluyan en los workers
            workers_con_reglas = []
            # Obtenemos la lista de workers de la CONFIGURACIÓN INTERNA
            config_workers = task_config.get('workers', [])

            # Verificamos si config_workers tiene el formato esperado (lista de dicts)
            if config_workers and isinstance(config_workers[0], dict):
                # Copiamos la lista para no modificar la original
                workers_con_reglas = [w.copy() for w in config_workers]
            elif config_workers:  # Si es formato antiguo (lista de strings)
                # Lo convertimos al nuevo formato, añadiendo regla None
                workers_con_reglas = [{'name': w_name, 'reassignment_rule': None} for w_name in config_workers]

            # Sobrescribimos la clave 'workers' en step_dict con la versión que SÍ tiene las reglas
            step_dict['workers'] = workers_con_reglas
            final_flow.append(step_dict)

        self.logger.info(
            f"Flujo de producción final construido con {len(final_flow)} pasos (con config completa y posición)."
        )
        return final_flow

    def _position_preview_button(self):
        """Posiciona el botón flotante en la esquina inferior derecha."""
        if hasattr(self, 'preview_button'):  # Asegurarse de que el botón existe
            margin_x = 20
            margin_y = 20  # Margen desde la barra de botones inferior
            button_height = self.preview_button.height()
            button_width = self.preview_button.width()

            # Posición X: Ancho del diálogo - ancho del botón - margen
            x = self.width() - button_width - margin_x
            # Posición Y: Alto del diálogo - alto del botón - margen (y espacio para barra inferior)
            # Asumimos que la barra inferior tiene una altura aproximada, ajusta si es necesario
            bottom_bar_height_approx = 60
            y = self.height() - button_height - margin_y - bottom_bar_height_approx

            self.preview_button.move(x, y)
            # Asegurarse de que esté visible y encima de otros widgets
            self.preview_button.raise_()
            self.preview_button.show()

    def _on_dialog_resized(self, event):
        """Reposiciona el botón al redimensionar la ventana."""
        # Llamar al método original de resizeEvent si existe
        if hasattr(self, '_original_resizeEvent') and self._original_resizeEvent:
            self._original_resizeEvent(event)
        else:
            super().resizeEvent(event)  # Llamar al de la clase base si no había uno original
        # Reposicionar nuestro botón
        self._position_preview_button()

    def _preview_execution_order(self):
        """
        Muestra una previsualización del orden de ejecución de las tareas
        sin realizar cálculos reales, solo con efectos visuales.
        """
        if not self.canvas_tasks:
            QMessageBox.information(
                self, "Canvas Vacío",
                "No hay tareas en el canvas para previsualizar.",
                QMessageBox.StandardButton.Ok
            )
            return

        # Confirmar con el usuario
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("👁️ Previsualizar Orden")
        msg.setText("<b>¿Deseas previsualizar el orden de ejecución?</b>")
        msg.setInformativeText(
            "Esta función mostrará visualmente el orden en que el programa\n"
            "procesaría las tareas durante una simulación.\n\n"
            "No se realizarán cálculos reales, solo efectos visuales.\n"
            "Duración aproximada: unos segundos."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)

        if msg.exec() != QMessageBox.StandardButton.Yes:
            self.logger.info("Previsualización cancelada por el usuario.")
            return

        self.logger.info("Iniciando previsualización de orden de ejecución.")

        # Deshabilitar botones durante la preview para evitar interferencias
        self.preview_button.setEnabled(False)
        self.manual_calc_button.setEnabled(False)
        self.optimizer_calc_button.setEnabled(False)
        self.load_pila_button.setEnabled(False)
        self.save_pila_button.setEnabled(False)
        self.clear_button.setEnabled(False)

        # Calcular el orden teórico
        self.preview_order = self._calculate_preview_order()
        if not self.preview_order:
            self.logger.warning("No se pudo calcular el orden de previsualización.")
            self._end_preview()  # Terminar si no hay orden
            return

        self.logger.debug(f"Orden de preview calculado: {self.preview_order}")

        # Iniciar preview usando un QTimer para no bloquear la UI
        self.preview_index = 0
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self._show_next_preview_step)
        # Velocidad de la preview (más rápido que en el informe)
        self.preview_timer.start(500)  # Mostrar cada tarea por 500ms

    def _calculate_preview_order(self):
        """
        Calcula el orden de ejecución teórico basándose en:
        1. Tareas de inicio de ciclo o sin dependencias.
        2. Dependencias directas.
        3. Saltos cíclicos (se indican pero no se siguen recursivamente en preview).

        Returns:
            list: Lista de índices en el orden de ejecución teórico.
                    Puede incluir -1 para indicar un salto cíclico visual.
        """
        order = []
        visited = set()
        queue = []  # Usaremos una cola para un recorrido más ordenado (BFS-like)

        # Paso 1: Identificar tareas iniciales (inicio de ciclo o sin dependencias)
        initial_tasks = []
        has_cycle_starts = any(task.get('config', {}).get('is_cycle_start', False) for task in self.canvas_tasks)

        for i, task in enumerate(self.canvas_tasks):
            is_initial = False
            config = task.get('config', {})
            start_cond = config.get('start_condition', {})

            if has_cycle_starts:
                # Si hay marcadas como inicio de ciclo, esas son las iniciales
                if config.get('is_cycle_start', False):
                    is_initial = True
            else:
                # Si no hay marcadas, las iniciales son las que NO tienen dependencia
                if start_cond.get('type') != 'dependency' or start_cond.get('value') is None:
                    is_initial = True

            if is_initial:
                initial_tasks.append(i)

        # Añadir las tareas iniciales a la cola
        queue.extend(sorted(initial_tasks))  # Ordenar por índice inicial
        visited.update(initial_tasks)

        self.logger.debug(f"Tareas iniciales para preview: {queue}")

        # Paso 2: Procesar la cola hasta que esté vacía
        processed_in_order = []  # Lista para guardar el orden final
        while queue:
            current_idx = queue.pop(0)
            processed_in_order.append(current_idx)

            # Buscar tareas que dependen DIRECTAMENTE de 'current_idx'
            dependents = []
            for i, task in enumerate(self.canvas_tasks):
                if i not in visited:
                    config = task.get('config', {})
                    start_cond = config.get('start_condition', {})
                    if start_cond.get('type') == 'dependency' and start_cond.get('value') == current_idx:
                        dependents.append(i)

            # Añadir dependientes a la cola (ordenados por su índice original)
            dependents.sort()
            for dep_idx in dependents:
                if dep_idx not in visited:
                    queue.append(dep_idx)
                    visited.add(dep_idx)

            # Verificar salto cíclico desde 'current_idx'
            current_config = self.canvas_tasks[current_idx].get('config', {})
            cyclic_next = current_config.get('next_cyclic_task_index')
            if cyclic_next is not None and 0 <= cyclic_next < len(self.canvas_tasks):
                # Indicador visual de ciclo
                # Solo lo añadimos si la tarea destino aún no ha sido procesada en el orden
                # para evitar añadir indicadores redundantes si el ciclo ya se visitó
                if cyclic_next not in processed_in_order and cyclic_next not in queue:
                    processed_in_order.append(-1)  # Indicador visual
                    # Añadir el destino del ciclo a la cola si no está ya visitado
                    if cyclic_next not in visited:
                        queue.append(cyclic_next)
                        visited.add(cyclic_next)
                    self.logger.debug(f"   Salto cíclico detectado: {current_idx} -> {cyclic_next}")

        # Paso 3: Añadir tareas huérfanas (si las hubiera, por si acaso)
        # Esto puede ocurrir si hay dependencias rotas o tareas aisladas
        remaining_tasks = []
        for i in range(len(self.canvas_tasks)):
            if i not in visited:
                remaining_tasks.append(i)
        remaining_tasks.sort()
        processed_in_order.extend(remaining_tasks)

        return processed_in_order

    def _traverse_from_task(self, task_idx, order, visited):
        """
        Método RECURSIVO para recorrer las tareas desde un índice dado,
        siguiendo dependencias y ciclos para calcular el orden.
        (Este método se mantiene como estaba en tu informe)

        Args:
            task_idx: Índice de la tarea inicial.
            order: Lista donde se añadirán los índices en orden.
            visited: Set de índices ya visitados para evitar bucles infinitos.
        """
        # Si ya hemos visitado esta tarea en la recursión actual, salir
        if task_idx in visited:
            return

        # Marcar como visitada y añadir al orden
        visited.add(task_idx)
        order.append(task_idx)

        # Buscar tareas que dependen de ésta (hijas directas)
        children = []
        for i, task in enumerate(self.canvas_tasks):
            config = task.get('config', {})
            start_cond = config.get('start_condition', {})
            if (start_cond.get('type') == 'dependency' and
                    start_cond.get('value') == task_idx):
                children.append(i)

        # Recorrer recursivamente las hijas (ordenadas por índice para consistencia)
        for child_idx in sorted(children):
            self._traverse_from_task(child_idx, order, visited)

        # Verificar si esta tarea tiene un salto cíclico
        cyclic_next_idx = self.canvas_tasks[task_idx].get('config', {}).get('next_cyclic_task_index')

        # Si hay un salto cíclico Y la tarea destino aún no ha sido visitada
        # en esta rama de la recursión (para evitar bucles en la preview):
        if cyclic_next_idx is not None and 0 <= cyclic_next_idx < len(self.canvas_tasks):
            # Añadimos un indicador visual (-1) y luego el índice destino
            # Solo si el destino no está ya en el 'order' para evitar redundancia visual
            if cyclic_next_idx not in order:
                order.append(-1)  # Indicador de salto
                # Añadimos el destino al orden, pero NO llamamos recursivamente
                # para evitar bucles infinitos en la preview. Solo lo mostramos.
                order.append(cyclic_next_idx)
                # Lo marcamos como visitado para que otras ramas no lo añadan de nuevo
                visited.add(cyclic_next_idx)

    def _show_next_preview_step(self):
        """Muestra el siguiente paso de la previsualización resaltando la tarea."""
        # Verificar si hemos terminado la lista de orden
        if not hasattr(self, 'preview_order') or self.preview_index >= len(self.preview_order):
            self._end_preview()
            return

        # Limpiar cualquier efecto de resaltado anterior (naranja)
        self._clear_all_simulation_effects()

        # Obtener el índice de la tarea actual en el orden
        current_idx = self.preview_order[self.preview_index]

        # Si es el indicador de ciclo (-1)
        if current_idx == -1:
            self.logger.info("Preview: Indicador de salto cíclico")
            # Podríamos añadir un efecto visual breve aquí si quisiéramos,
            # como un parpadeo rápido de todas las tareas del ciclo, pero
            # por simplicidad, solo avanzamos al siguiente índice.
            pass  # Simplemente saltamos este indicador visual por ahora
        # Si es un índice de tarea válido
        elif 0 <= current_idx < len(self.canvas_tasks):
            try:
                # Usamos la función existente para aplicar el efecto naranja
                self._highlight_processing_task(current_idx)

                # Log para seguimiento
                task_name = self.canvas_tasks[current_idx]['data'].get('name', 'Tarea desconocida')
                step_number = self.preview_index + 1
                self.logger.info(f"Preview paso {step_number}: Tarea '{task_name}' (Índice {current_idx})")
            except IndexError:
                self.logger.error(f"Error en preview: Índice {current_idx} fuera de rango.")
                self._end_preview()  # Terminar si hay error
                return
            except Exception as e:
                self.logger.error(f"Error inesperado al resaltar en preview: {e}", exc_info=True)
                self._end_preview()  # Terminar si hay error
                return
        else:
            self.logger.warning(f"Índice inválido {current_idx} encontrado en preview_order.")

        # Avanzar al siguiente índice para la próxima llamada del timer
        self.preview_index += 1

    def _end_preview(self):
        """Finaliza la previsualización, detiene el timer y limpia los efectos."""
        # Detener el timer si está activo
        if hasattr(self, 'preview_timer') and self.preview_timer:
            self.preview_timer.stop()
            # Eliminar la referencia al timer para limpieza
            del self.preview_timer
            self.logger.info("Timer de previsualización detenido.")

        # Limpiar cualquier efecto de resaltado naranja que quede
        self._clear_all_simulation_effects()

        # Rehabilitar los botones principales
        self.preview_button.setEnabled(True)
        self.manual_calc_button.setEnabled(True)
        self.optimizer_calc_button.setEnabled(True)
        self.load_pila_button.setEnabled(True)
        self.save_pila_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.logger.info("Botones principales rehabilitados.")

        # Mostrar mensaje de finalización al usuario
        QMessageBox.information(
            self, "Preview Completado",
            "La previsualización del orden de ejecución ha finalizado.\n\n"
            "Este es el orden aproximado que seguirá el programa\n"
            "durante una simulación real.",
            QMessageBox.StandardButton.Ok
        )

        self.logger.info("✅ Previsualización de orden de ejecución completada.")
        # Limpiar variables de estado de la preview (opcional, buena práctica)
        if hasattr(self, 'preview_order'): del self.preview_order
        if hasattr(self, 'preview_index'): del self.preview_index


    def _create_simulation_message_label(self):
        """Crea el label flotante para mensajes de simulación."""
        self.simulation_message_label = QLabel(self.canvas)
        self.simulation_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.simulation_message_label.setWordWrap(True)
        self.simulation_message_label.setStyleSheet("""
            QLabel {
                background-color: rgba(44, 62, 80, 230);
                color: white;
                border: 2px solid #3498db;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.simulation_message_label.hide()  # Oculto por defecto


    def _show_simulation_message(self, message, is_processing=True):
        """Muestra el mensaje flotante en la parte superior del canvas."""
        if not self.simulation_message_label:
            return

        # Configurar el texto y color según el estado
        if is_processing:
            icon = "🔄"
            border_color = "#3498db"  # Azul
        else:
            icon = "✅"
            border_color = "#27ae60"  # Verde

        self.simulation_message_label.setText(f"{icon} {message}")
        self.simulation_message_label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(44, 62, 80, 230);
                color: white;
                border: 2px solid {border_color};
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }}
        """)

        # Ajustar tamaño y posición
        self.simulation_message_label.adjustSize()

        # Centrar horizontalmente en el canvas
        canvas_width = self.canvas.width()
        label_width = self.simulation_message_label.width()
        x_pos = (canvas_width - label_width) // 2
        y_pos = 20  # 20px desde el borde superior

        self.simulation_message_label.move(x_pos, y_pos)
        self.simulation_message_label.raise_()  # Asegurar que esté por encima
        self.simulation_message_label.show()

    def _hide_simulation_message(self):
        """Oculta el mensaje flotante."""
        if self.simulation_message_label:
            self.simulation_message_label.hide()


    def _highlight_processing_task(self, task_index):
        """
        Aplica el efecto de procesamiento (azulado) a la tarjeta especificada.
        Si ya había otra tarjeta con el efecto, lo remueve primero.
        """
        self.logger.info(f"Aplicando efecto de procesamiento a tarea índice: {task_index}")

        # Limpiar efectos anteriores
        self._clear_all_simulation_effects()

        # Verificar que el índice es válido
        if not (0 <= task_index < len(self.canvas_tasks)):
            self.logger.warning(f"Índice de tarea inválido para efecto: {task_index}")
            return

        canvas_task = self.canvas_tasks[task_index]
        card_widget = canvas_task.get('widget')

        if not card_widget:
            self.logger.warning(f"No se encontró widget para tarea índice: {task_index}")
            return

        # Crear y aplicar el efecto azulado
        try:
            effect_widget = SimulationProgressEffect(card_widget)
            self.simulation_effects[task_index] = effect_widget
            self.logger.debug(f"Efecto de procesamiento aplicado a tarea {task_index}")

            # --- ✨ INICIO DE LA MEJORA (Paso 3.1) ---
            # Mostrar mensaje de "procesando" con contador
            task_name = canvas_task.get('data', {}).get('name', 'Tarea')
            total_tasks = len(self.canvas_tasks)
            message = (f"Realizando simulación, espere por favor...\n"
                        f"Procesando: {task_name} ({task_index + 1}/{total_tasks})")

            self._show_simulation_message(message, is_processing=True)
            # --- FIN DE LA MEJORA ---

            # Forzar actualización visual
            QApplication.processEvents()

        except Exception as e:
            self.logger.error(f"Error al aplicar efecto de procesamiento: {e}", exc_info=True)

    def _clear_all_simulation_effects(self):
        """
        Elimina todos los efectos de simulación activos y muestra mensaje de completado.
        """
        self.logger.info("Limpiando todos los efectos de simulación")

        # Eliminar todos los efectos activos
        for task_index, effect_widget in list(self.simulation_effects.items()):
            try:
                effect_widget.stop_animation()
                effect_widget.deleteLater()
            except Exception as e:
                self.logger.error(f"Error al eliminar efecto de simulación: {e}")

        # Limpiar el diccionario
        self.simulation_effects.clear()

        # Mostrar mensaje de completado
        self._show_simulation_message("Simulación completada", is_processing=False)

        # Ocultar el mensaje después de 3 segundos
        QTimer.singleShot(3000, self._hide_simulation_message)

        self.logger.debug("Efectos de simulación limpiados")

    def _apply_green_cycle_effect(self, task_index):
        """Aplica el efecto verde de ciclo a una tarjeta intermedia."""
        if not (0 <= task_index < len(self.canvas_tasks)):
            return

        canvas_task = self.canvas_tasks[task_index]
        card_widget = canvas_task.get('widget')

        if not card_widget:
            return

        # Verificar si ya tiene el efecto
        if canvas_task.get('green_cycle_effect_widget'):
            effect_widget = canvas_task['green_cycle_effect_widget']
            effect_widget._update_geometry()
            effect_widget.show()
            effect_widget.raise_()
            return

        # Crear y aplicar el efecto
        effect_widget = GreenCycleEffect(card_widget)
        canvas_task['green_cycle_effect_widget'] = effect_widget
        self.logger.info(f"Efecto verde de ciclo aplicado a tarea en índice {task_index}")

        # Programar actualizaciones de geometría
        QTimer.singleShot(100, effect_widget._update_geometry)
        QTimer.singleShot(200, effect_widget._update_geometry)

    def _remove_green_cycle_effect(self, task_index):
        """Elimina el efecto verde de ciclo de una tarjeta."""
        if not (0 <= task_index < len(self.canvas_tasks)):
            return

        canvas_task = self.canvas_tasks[task_index]
        effect_widget = canvas_task.get('green_cycle_effect_widget')

        if effect_widget:
            effect_widget.stop_animation()
            effect_widget.deleteLater()
            canvas_task['green_cycle_effect_widget'] = None
            self.logger.info(f"Efecto verde de ciclo eliminado de tarea en índice {task_index}")

    def _apply_mixed_effect(self, task_index):
        """Aplica el efecto mixto dorado-verde a una tarjeta final de ciclo."""
        if not (0 <= task_index < len(self.canvas_tasks)):
            return

        canvas_task = self.canvas_tasks[task_index]
        card_widget = canvas_task.get('widget')

        if not card_widget:
            return

        # Verificar si ya tiene el efecto
        if canvas_task.get('mixed_effect_widget'):
            effect_widget = canvas_task['mixed_effect_widget']
            effect_widget._update_geometry()
            effect_widget.show()
            effect_widget.raise_()
            return

        # Crear y aplicar el efecto
        effect_widget = MixedGoldGreenEffect(card_widget)
        canvas_task['mixed_effect_widget'] = effect_widget
        self.logger.info(f"Efecto mixto dorado-verde aplicado a tarea en índice {task_index}")

        QTimer.singleShot(100, effect_widget._update_geometry)
        QTimer.singleShot(200, effect_widget._update_geometry)

    def _remove_mixed_effect(self, task_index):
        """Elimina el efecto mixto dorado-verde de una tarjeta."""
        if not (0 <= task_index < len(self.canvas_tasks)):
            return

        canvas_task = self.canvas_tasks[task_index]
        effect_widget = canvas_task.get('mixed_effect_widget')

        if effect_widget:
            effect_widget.stop_animation()
            effect_widget.deleteLater()
            canvas_task['mixed_effect_widget'] = None
            self.logger.info(f"Efecto mixto eliminado de tarea en índice {task_index}")

    def _update_all_cycle_effects(self):
        """
        Actualiza todos los efectos visuales de ciclo según la configuración actual.
        OPTIMIZADO: Solo aplica efectos a tareas madre y última tarea de cada cadena.
        """
        self.logger.debug("Actualizando efectos de ciclo (modo optimizado)...")

        # Primero, eliminar TODOS los efectos verdes y mixtos
        for i in range(len(self.canvas_tasks)):
            self._remove_green_cycle_effect(i)
            self._remove_mixed_effect(i)

        # Identificar las últimas tareas de cada cadena de ciclo
        last_tasks_in_chains = self._identify_last_tasks_in_cycles()

        # Aplicar efectos solo a las últimas tareas
        for task_index in last_tasks_in_chains:
            if not (0 <= task_index < len(self.canvas_tasks)):
                continue

            config = self.canvas_tasks[task_index].get('config', {})
            is_cycle_end = config.get('is_cycle_end', False)
            is_cycle_start = config.get('is_cycle_start', False)

            # No aplicar efecto si es tarea madre (ya tiene el dorado)
            if is_cycle_start:
                continue

            # Aplicar efecto según el tipo
            if is_cycle_end:
                # Última tarea Y marcada como fin de ciclo: efecto mixto
                self._apply_mixed_effect(task_index)
                self.logger.debug(f"Efecto mixto aplicado a tarea final {task_index}")
            else:
                # Última tarea pero NO fin de ciclo: efecto verde
                self._apply_green_cycle_effect(task_index)
                self.logger.debug(f"Efecto verde aplicado a última tarea {task_index}")

        self.logger.debug(f"Efectos optimizados actualizados. {len(last_tasks_in_chains)} tareas con efectos.")

    def _identify_last_tasks_in_cycles(self):
        """
        Identifica las últimas tareas de cada cadena de ciclo.
        Una tarea es "última" si tiene next_cyclic_task_index pero ninguna otra tarea
        tiene a esta como next_cyclic_task_index (es decir, nadie apunta a ella en el ciclo).
        """
        last_tasks = set()

        # Encontrar todas las tareas que tienen conexión cíclica saliente
        tasks_with_cyclic_out = set()
        for i, canvas_task in enumerate(self.canvas_tasks):
            config = canvas_task.get('config', {})
            if config.get('next_cyclic_task_index') is not None:
                tasks_with_cyclic_out.add(i)

        # Para cada tarea con conexión cíclica, verificar si es la última
        for task_idx in tasks_with_cyclic_out:
            is_last = True

            # Verificar si alguna otra tarea apunta a esta
            for other_idx, other_task in enumerate(self.canvas_tasks):
                if other_idx == task_idx:
                    continue

                other_config = other_task.get('config', {})
                if other_config.get('next_cyclic_task_index') == task_idx:
                    # Otra tarea apunta a esta, no es la última
                    is_last = False
                    break

            if is_last:
                last_tasks.add(task_idx)

        # También incluir tareas marcadas explícitamente como fin de ciclo
        for i, canvas_task in enumerate(self.canvas_tasks):
            config = canvas_task.get('config', {})
            if config.get('is_cycle_end', False):
                last_tasks.add(i)

        return last_tasks

    def _is_task_in_cycle_chain(self, task_index, cycle_chains):
        """Verifica si una tarea está en una cadena de ciclo."""
        return task_index in cycle_chains


class CycleEndConfigDialog(QDialog):
    """
    Diálogo para configurar el fin de ciclo de una tarea.
    Permite seleccionar a qué tarea de inicio de ciclo regresar.
    """
    def __init__(self, current_task_index, all_canvas_tasks, parent=None):
        super().__init__(parent)
        self.current_task_index = current_task_index
        self.all_canvas_tasks = all_canvas_tasks
        self.selected_return_index = None

        # --- Obtener configuración actual ---
        # Acceder de forma segura a la configuración
        current_config = {}
        if 0 <= self.current_task_index < len(self.all_canvas_tasks):
            current_config = self.all_canvas_tasks[self.current_task_index].get('config', {})
        self.current_return_index_from_config = current_config.get('cycle_return_to_index')
        self.is_currently_marked_as_end = current_config.get('is_cycle_end', False)
        # --- Fin obtener configuración ---

        self.setWindowTitle("Configurar Fin de Ciclo")
        self.setModal(True)
        self.setMinimumWidth(500)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Título
        title = QLabel("🔄 <b>Configuración de Fin de Ciclo</b>")
        title.setStyleSheet("font-size: 16px; color: #28a745;") # Verde
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Explicación
        explanation = QLabel(
            "Al completar un ciclo en esta tarea, el programa regresará\n"
            "a la tarea seleccionada para iniciar el siguiente ciclo.\n\n"
            "Seleccione la tarea a la que desea regresar:"
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(explanation)

        # Lista de tareas candidatas
        self.tasks_list = QListWidget()
        # NUEVO: Estilo personalizado para hacer la selección más obvia
        self.tasks_list.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #007bff;  /* Azul brillante */
                color: white;
                border: 2px solid #0056b3;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
            QListWidget::item {
                padding: 8px;
                margin: 2px;
            }
        """)
        self.tasks_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # Solo una selección

        # Opción para no regresar (quedar libre)
        no_return_item = QListWidgetItem("➡️ (No regresar a ninguna tarea específica)")
        no_return_item.setData(Qt.ItemDataRole.UserRole, None) # Guardamos None como índice
        no_return_item.setForeground(QBrush(QColor("#555"))) # Color grisáceo
        no_return_item.setFont(QFont("Segoe UI", 10, italic=True))
        self.tasks_list.addItem(no_return_item)

        # Poblar con tareas de inicio de ciclo y otras
        cycle_start_indices = set()
        for i, task in enumerate(self.all_canvas_tasks):
            if i == self.current_task_index:
                continue  # No puede regresar a sí misma

            is_cycle_start = task.get('config', {}).get('is_cycle_start', False)
            task_name = task.get('data', {}).get('name', 'Tarea Desconocida')

            if is_cycle_start:
                # Usar un formato más claro sin fondo que interfiera con la selección
                item = QListWidgetItem(f"⭐ {task_name} (Inicio de Ciclo)")
                item.setData(Qt.ItemDataRole.UserRole, i)

                # En lugar de fondo amarillo, usar un estilo de fuente destacado
                font = QFont("Segoe UI", 10)
                font.setBold(True)
                item.setFont(font)

                # Color dorado para el texto (no fondo)
                item.setForeground(QBrush(QColor("#F39C12")))  # Dorado

                # Agregar tooltip explicativo
                item.setToolTip(
                    "Esta es una tarea de Inicio de Ciclo.\n"
                    "Es el punto natural de retorno para ciclos repetitivos."
                )

                self.tasks_list.addItem(item)
                cycle_start_indices.add(i)

        # Añadir el resto de tareas (que no son de inicio ni la actual)
        for i, task in enumerate(self.all_canvas_tasks):
            if i == self.current_task_index or i in cycle_start_indices:
                continue

            task_name = task.get('data', {}).get('name', 'Tarea Desconocida')
            item = QListWidgetItem(f"📋 {task_name}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.tasks_list.addItem(item)

        layout.addWidget(self.tasks_list)

        # Información actual y selección automática
        current_name = "Ninguna"
        item_to_select = no_return_item # Por defecto, seleccionar "No regresar"

        if self.current_return_index_from_config is not None:
            if 0 <= self.current_return_index_from_config < len(self.all_canvas_tasks):
                current_name = self.all_canvas_tasks[self.current_return_index_from_config]['data'].get('name', 'Desconocida')
                # Buscar el item correspondiente en la lista para seleccionarlo
                for i in range(self.tasks_list.count()):
                    item = self.tasks_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == self.current_return_index_from_config:
                        item_to_select = item
                        break

        info_label = QLabel(
            f"✅ Actualmente configurado para regresar a: <b>{current_name}</b>"
        )
        info_label.setStyleSheet(
            "background-color: #d1ecf1; padding: 5px; " # Azul claro
            "border-radius: 3px; color: #0c5460;"
        )
        layout.addWidget(info_label)

        # Seleccionar el item después de añadir el label
        if item_to_select:
            self.tasks_list.setCurrentItem(item_to_select)

        # Checkbox para marcar como fin de ciclo
        self.mark_as_end_checkbox = QCheckBox(
            "🏁 Marcar esta tarea como Fin de Ciclo"
        )
        self.mark_as_end_checkbox.setStyleSheet("font-weight: bold; color: #28a745;") # Verde
        self.mark_as_end_checkbox.setChecked(self.is_currently_marked_as_end)
        layout.addWidget(self.mark_as_end_checkbox)

        # Botones
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_configuration(self):
        """
        Retorna la configuración seleccionada.

        Returns:
            dict: {'is_cycle_end': bool, 'return_to_index': int|None}
        """
        selected_items = self.tasks_list.selectedItems()
        return_index = None # Por defecto es None (no regresar)

        if selected_items:
            # Obtenemos el índice guardado (puede ser None para la opción "No regresar")
            return_index = selected_items[0].data(Qt.ItemDataRole.UserRole)

        return {
            'is_cycle_end': self.mark_as_end_checkbox.isChecked(),
            'return_to_index': return_index # Puede ser None o un índice entero
        }


class ReassignmentRuleDialog(QDialog):
    """Diálogo para definir la regla de reasignación de un trabajador para una tarea."""

    def __init__(self, worker_name, current_task, all_canvas_tasks, current_rule, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Regla para {worker_name} en {current_task['name']}")
        self.setMinimumWidth(500)

        self.all_canvas_tasks = all_canvas_tasks
        self.current_task_id = current_task['id']

        main_layout = QVBoxLayout(self)

        # --- Grupo 1: Condición de Liberación ---
        condition_group = QGroupBox("El trabajador se liberará de esta tarea...")
        cond_layout = QVBoxLayout(condition_group)

        self.rb_on_finish = QRadioButton("Al finalizar la producción total de la tarea.")
        self.rb_after_units = QRadioButton("Tras fabricar un número específico de unidades:")
        self.sb_units_value = QSpinBox()
        self.sb_units_value.setRange(1, 99999)

        cond_layout.addWidget(self.rb_on_finish)
        cond_layout.addWidget(self.rb_after_units)
        cond_layout.addWidget(self.sb_units_value)
        main_layout.addWidget(condition_group)

        # --- Grupo 2: Acción de Reasignación ---
        action_group = QGroupBox("Acción al liberarse")
        act_layout = QFormLayout(action_group)
        self.cb_target_task = QComboBox()
        act_layout.addRow("Reasignar a la tarea:", self.cb_target_task)
        main_layout.addWidget(action_group)

        # --- NUEVO: Grupo 3: Tipo de Reasignación ---
        tipo_grupo = QGroupBox("Tipo de Reasignación")
        tipo_layout = QVBoxLayout(tipo_grupo)  # Layout DENTRO del grupo

        self.tipo_compartir = QRadioButton("Compartir carga (comportamiento actual)")
        self.tipo_compartir.setToolTip(
            "El trabajador se une al grupo existente y comparten el tiempo restante de la unidad actual."
        )
        self.tipo_compartir.setChecked(True)  # Por defecto

        self.tipo_paralelo = QRadioButton("Trabajar en paralelo (NUEVO)")
        self.tipo_paralelo.setToolTip(
            "El trabajador inicia su propia línea de trabajo paralela en la misma tarea, trabajando en unidades diferentes."
        )

        tipo_layout.addWidget(self.tipo_compartir)
        tipo_layout.addWidget(self.tipo_paralelo)

        main_layout.addWidget(tipo_grupo)  # Añadir el grupo al layout principal

        # --- Botones ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._populate_fields(current_rule)

        # Conexiones de UI interna
        self.rb_on_finish.toggled.connect(lambda checked: self.sb_units_value.setEnabled(not checked))

    def _populate_fields(self, rule):
        # Poblar el ComboBox con las posibles tareas destino
        self.cb_target_task.addItem("--- Ninguna (queda libre) ---", None)
        for i, task in enumerate(self.all_canvas_tasks):
            if task['data']['id'] != self.current_task_id:
                self.cb_target_task.addItem(task['data']['name'], task['data']['id'])

        # Cargar la regla actual si existe
        if rule is None:
            self.rb_on_finish.setChecked(True)
            self.sb_units_value.setEnabled(False)
        else:
            if rule['condition_type'] == 'AFTER_UNITS':
                self.rb_after_units.setChecked(True)
                self.sb_units_value.setValue(rule['condition_value'])
                self.sb_units_value.setEnabled(True)
            else:  # ON_FINISH
                self.rb_on_finish.setChecked(True)
                self.sb_units_value.setEnabled(False)

            target_id = rule.get('target_task_id')
            if target_id:
                target_index = self.cb_target_task.findData(target_id)
                if target_index != -1:
                    self.cb_target_task.setCurrentIndex(target_index)

    # DENTRO de la clase ReassignmentRuleDialog en dialogs.py

    def get_rule(self):
        """
        Construye y devuelve el diccionario de la regla a partir del estado del formulario.
        CORREGIDO: Define y usa 'mode'.
        """
        # Determinar condición y valor (como antes)
        condition_type = None
        condition_value = None
        if self.rb_on_finish.isChecked():
            condition_type = 'ON_FINISH'
        elif self.rb_after_units.isChecked():
            condition_type = 'AFTER_UNITS'
            condition_value = self.sb_units_value.value()

        target_task_id = self.cb_target_task.currentData()

        # --- INICIO CORRECCIÓN ---
        # 1. Definir la variable 'mode' con un valor por defecto
        mode = 'compartir'  # O 'REPLACE' si usas esa constante en otro sitio

        # 2. Actualizar 'mode' si el botón de paralelo está marcado
        if self.tipo_paralelo.isChecked():
            mode = 'PARALLEL_JOIN'  # O 'PARALLEL_JOIN' si prefieres esa constante
        # --- FIN CORRECCIÓN ---

        # Construir regla solo si hay una condición o un destino
        if condition_type or target_task_id:
            return {
                "condition_type": condition_type,
                "condition_value": condition_value,
                "target_task_id": target_task_id,
                # 3. Usar la variable 'mode' definida arriba
                "mode": mode
            }
        else:
            # Si no hay condición ni destino, no hay regla
            return None


class DefinirCantidadesDialog(QDialog):
    """
    Diálogo para que el usuario defina la cantidad a producir para cada
    tarea o grupo de tareas en el flujo de producción.
    """

    def __init__(self, production_flow, parent=None):
        super().__init__(parent)
        self.production_flow = production_flow
        self.spin_boxes = []  # Para guardar referencia a los QSpinBox

        self.setWindowTitle("Definir Cantidades de Producción")
        self.setMinimumSize(600, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Introduce la cantidad a fabricar para cada ítem del plan:</b>"))

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Ítem del Plan", "Cantidad a Producir"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setRowCount(len(self.production_flow))

        for i, step in enumerate(self.production_flow):
            # Determinar el nombre del ítem (si es grupo o tarea individual)
            if step.get('type') == 'sequential_group':
                task_name = f"Grupo: {', '.join([t['task']['name'] for t in step.get('tasks', [])[:2]])}..."
            else:
                task_name = step.get('task', {}).get('name', 'Tarea Desconocida')

            name_item = QTableWidgetItem(task_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Hacer no editable

            spin_box = QSpinBox()
            spin_box.setRange(1, 99999)
            spin_box.setValue(1)

            self.table.setItem(i, 0, name_item)
            self.table.setCellWidget(i, 1, spin_box)
            self.spin_boxes.append(spin_box)

        layout.addWidget(self.table)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_cantidades(self):
        """
        Devuelve un diccionario que mapea el índice de cada paso del flujo
        con la cantidad de unidades especificada por el usuario.
        """
        cantidades = {}
        for i, spin_box in enumerate(self.spin_boxes):
            cantidades[i] = spin_box.value()
        return cantidades


