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
import logging

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


class PrepStepsDialog(QDialog):
    """Diálogo para gestionar los pasos individuales de un grupo de preparación."""

    def __init__(self, group_id, group_name, controller, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Pasos para el Grupo: {group_name}")
        self.setMinimumSize(700, 550)
        self.group_id = group_id
        self.controller = controller
        self.current_step_id = None

        main_layout = QVBoxLayout(self)

        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(4)
        self.steps_table.setHorizontalHeaderLabels(["Nombre del Paso", "Tiempo (min)", "Es Diario", "Descripción"])
        self.steps_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.steps_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.steps_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.steps_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.steps_table.itemSelectionChanged.connect(self._on_step_selected)
        main_layout.addWidget(self.steps_table)

        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_frame)
        self.step_name_edit = QLineEdit()
        self.step_time_edit = QLineEdit()
        self.step_desc_edit = QTextEdit()
        self.step_desc_edit.setFixedHeight(60)
        self.is_daily_check = QCheckBox("Este paso se repite cada día de trabajo")

        form_layout.addRow("Nombre del Paso:", self.step_name_edit)
        form_layout.addRow("Tiempo (minutos):", self.step_time_edit)
        form_layout.addRow(self.is_daily_check)
        form_layout.addRow("Descripción:", self.step_desc_edit)
        main_layout.addWidget(form_frame)

        button_layout = QHBoxLayout()
        self.add_update_button = QPushButton("Añadir Nuevo Paso")
        self.delete_button = QPushButton("Eliminar Paso Seleccionado")
        self.clear_button = QPushButton("Limpiar Formulario")
        button_layout.addWidget(self.add_update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)

        self.add_update_button.clicked.connect(self._add_or_update_step)
        self.delete_button.clicked.connect(self._delete_step)
        self.clear_button.clicked.connect(self._clear_form)

        self._load_steps()
        self._clear_form()

    def _load_steps(self):
        """Carga los pasos del grupo y los muestra en la tabla."""
        self.steps_table.setRowCount(0)
        steps = self.controller.model.get_steps_for_group(self.group_id)
        self.steps_table.blockSignals(True)
        for step_data in steps:
            step_id, name, time, description, is_daily = step_data[:5]
            row_position = self.steps_table.rowCount()
            self.steps_table.insertRow(row_position)
            item_name = QTableWidgetItem(name)
            item_name.setData(Qt.ItemDataRole.UserRole, step_id)
            item_time = QTableWidgetItem(str(time))
            item_daily = QTableWidgetItem("Sí" if is_daily else "No")
            item_desc = QTableWidgetItem(description)
            item_time.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_daily.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.steps_table.setItem(row_position, 0, item_name)
            self.steps_table.setItem(row_position, 1, item_time)
            self.steps_table.setItem(row_position, 2, item_daily)
            self.steps_table.setItem(row_position, 3, item_desc)
        self.steps_table.blockSignals(False)

    def _on_step_selected(self):
        """Carga los datos de un paso seleccionado en el formulario."""
        selected_items = self.steps_table.selectedItems()
        if not selected_items:
            return
        selected_row = self.steps_table.row(selected_items[0])
        self.current_step_id = self.steps_table.item(selected_row, 0).data(Qt.ItemDataRole.UserRole)
        name = self.steps_table.item(selected_row, 0).text()
        time = self.steps_table.item(selected_row, 1).text()
        is_daily_text = self.steps_table.item(selected_row, 2).text()
        description = self.steps_table.item(selected_row, 3).text()
        self.step_name_edit.setText(name)
        self.step_time_edit.setText(time)
        self.is_daily_check.setChecked(is_daily_text == "Sí")
        self.step_desc_edit.setPlainText(description)
        self.add_update_button.setText("Actualizar Paso Seleccionado")
        self.delete_button.setEnabled(True)

    def _clear_form(self):
        """Limpia el formulario para añadir un nuevo paso."""
        self.steps_table.clearSelection()
        self.step_name_edit.clear()
        self.step_time_edit.clear()
        self.step_desc_edit.clear()
        self.is_daily_check.setChecked(False)
        self.step_name_edit.setFocus()
        self.current_step_id = None
        self.add_update_button.setText("Añadir Nuevo Paso")
        self.delete_button.setEnabled(False)

    def _add_or_update_step(self):
        # --- INICIO DE LA CORRECCIÓN: Lógica para obtener la tarea base ---
        task_info = None
        if self.editing_index is not None:
            # MODO EDICIÓN: Obtenemos la tarea del paso que ya estamos editando.
            self.logger.debug(f"Modo edición para el paso índice {self.editing_index}.")
            task_info = self.production_flow[self.editing_index]['task']
        else:
            # MODO AÑADIR: Obtenemos la tarea del árbol de selección.
            self.logger.debug("Modo añadir nuevo paso.")
            selected_item = self.task_tree.currentItem()
            if not selected_item or not selected_item.parent():
                QMessageBox.warning(self, "Selección Requerida",
                                    "Debe seleccionar una tarea específica de un producto para añadirla a la pila.")
                return
            task_info = selected_item.data(0, Qt.ItemDataRole.UserRole)
        # --- FIN DE LA CORRECCIÓN ---

        # El resto de la función sigue la lógica original de recolección de datos
        selected_workers = [worker for worker, cb in self.worker_checkboxes.items() if cb.isChecked()]
        machine_id = self.machine_menu.currentData()

        # Validación de máquina (si es requerida)
        if task_info.get("requiere_maquina_tipo") and machine_id is None:
            QMessageBox.warning(self, "Máquina Requerida", "Debe asignar una máquina disponible para esta tarea.")
            return

        start_date, previous_task_index, trigger_units, depends_on_worker = None, None, self.units, None
        if self.start_date_radio.isChecked():
            start_date = self.start_date_entry.date().toPyDate()
        elif self.dependency_radio.isChecked():
            if self.previous_task_menu.count() == 0 or self.previous_task_menu.currentIndex() == -1:
                QMessageBox.warning(self, "Dependencia Requerida",
                                    "Debe seleccionar una tarea previa válida como dependencia.")
                return
            previous_task_index = self.previous_task_menu.currentData()
            try:
                trigger_units_val = int(self.trigger_units_entry.text())
                if not (0 < trigger_units_val <= self.units): raise ValueError
                trigger_units = trigger_units_val
            except ValueError:
                QMessageBox.warning(self, "Dato Inválido", f"Las unidades deben ser un número entre 1 y {self.units}.")
                return
        elif self.worker_dependency_radio.isChecked():
            depends_on_worker = self.worker_dependency_menu.currentText()

        step_data = {
            "task": task_info, "workers": selected_workers, "start_date": start_date,
            "previous_task_index": previous_task_index, "trigger_units": trigger_units,
            "machine_id": machine_id,
            "depends_on_worker": depends_on_worker
        }

        if self.editing_index is not None:
            self.production_flow[self.editing_index] = step_data
        else:
            self.production_flow.append(step_data)

        self._update_flow_display()
        self._reset_form()

    def _delete_step(self):
        """Elimina el paso seleccionado."""
        if self.current_step_id is None:
            self.controller.view.show_message("Selección Requerida", "Por favor, seleccione un paso para eliminar.", "warning")
            return
        step_name = self.step_name_edit.text()
        if self.controller.view.show_confirmation_dialog("Confirmar Eliminación", f"¿Está seguro de que desea eliminar el paso '{step_name}'?"):
            if self.controller.model.delete_prep_step(self.current_step_id):
                self.controller.view.show_message("Éxito", "El paso se ha eliminado.", "info")
                self._load_steps()
                self._clear_form()
            else:
                self.controller.view.show_message("Error", "No se pudo eliminar el paso.", "critical")


class PrepGroupsDialog(QDialog):
    """Diálogo para gestionar los Grupos de Preparación de una máquina."""

    def __init__(self, machine_id, machine_name, controller, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Grupos de Preparación para: {machine_name}")
        self.setMinimumSize(800, 500)
        self.machine_id = machine_id
        self.controller = controller
        self.products = self.controller.model.search_products("")
        self.current_group_id = None

        main_layout = QHBoxLayout(self)

        # --- Panel izquierdo ---
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("<b>Grupos de esta Máquina</b>"))
        self.groups_list = QListWidget()
        self.groups_list.itemSelectionChanged.connect(self._on_group_selected)
        left_layout.addWidget(self.groups_list)
        group_buttons = QHBoxLayout()
        add_group_btn = QPushButton("Añadir Grupo")
        delete_group_btn = QPushButton("Eliminar Grupo")
        manage_steps_btn = QPushButton("Gestionar Pasos del Grupo")
        group_buttons.addWidget(add_group_btn)
        group_buttons.addWidget(delete_group_btn)
        left_layout.addLayout(group_buttons)
        left_layout.addWidget(manage_steps_btn)

        # --- Panel derecho (Formulario) ---
        right_panel = QFrame()
        self.form_layout = QFormLayout(right_panel)
        self.group_name_edit = QLineEdit()
        self.group_desc_edit = QTextEdit()

        # ComboBox editable y con autocompletado
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        self.product_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.product_combo.addItem("Ninguno", None)

        product_list_for_completer = []
        for product in self.products:
            display_text = f"{product.codigo} - {product.descripcion}"
            self.product_combo.addItem(display_text, product.codigo)
            product_list_for_completer.append(display_text)

        completer = QCompleter(product_list_for_completer, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.product_combo.setCompleter(completer)

        self.save_group_btn = QPushButton("Guardar Cambios")

        self.form_layout.addRow("Nombre del Grupo:", self.group_name_edit)
        self.form_layout.addRow("Producto Asociado (Opcional):", self.product_combo)
        self.form_layout.addRow("Descripción:", self.group_desc_edit)
        self.form_layout.addWidget(self.save_group_btn)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        # Conexiones
        add_group_btn.clicked.connect(self._add_group)
        delete_group_btn.clicked.connect(self._delete_group)
        self.save_group_btn.clicked.connect(self._save_group)
        manage_steps_btn.clicked.connect(self._manage_steps)

        self._load_groups()
        self._toggle_form(False)

    def _toggle_form(self, enabled):
        for i in range(self.form_layout.rowCount()):
            widget = self.form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
            if widget:
                widget.setEnabled(enabled)

    def _load_groups(self):
        self.groups_list.clear()
        groups = self.controller.model.get_groups_for_machine(self.machine_id)
        for group in groups:
            # group es un DTO
            item = QListWidgetItem(group.nombre)
            item.setData(Qt.ItemDataRole.UserRole, (group.id, group.nombre, group.descripcion))
            self.groups_list.addItem(item)
        self._toggle_form(False)
        self.group_name_edit.clear()
        self.group_desc_edit.clear()
        self.product_combo.setCurrentIndex(0)

    def _on_group_selected(self):
        selected_items = self.groups_list.selectedItems()
        if not selected_items:
            self._toggle_form(False)
            return

        self._toggle_form(True)
        group_id, name, desc = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.current_group_id = group_id
        self.group_name_edit.setText(name)
        self.group_desc_edit.setPlainText(desc)

        group_details = self.controller.model.get_group_details(group_id)
        if group_details:
            # DTO access
            product_code = group_details.producto_codigo
            if product_code:
                index = self.product_combo.findData(product_code)
                if index != -1:
                    self.product_combo.setCurrentIndex(index)
                else:
                    self.product_combo.setCurrentIndex(0)
            else:
                self.product_combo.setCurrentIndex(0)

    def _add_group(self):
        self.groups_list.clearSelection()
        self.current_group_id = None
        self.group_name_edit.clear()
        self.group_desc_edit.clear()
        self.product_combo.setCurrentIndex(0)
        self._toggle_form(True)
        self.group_name_edit.setFocus()

    def _save_group(self):
        name = self.group_name_edit.text().strip()
        desc = self.group_desc_edit.toPlainText().strip()
        product_code = self.product_combo.currentData()

        if not name:
            self.controller.view.show_message("Error", "El nombre del grupo es obligatorio.", "warning")
            return

        if self.current_group_id:
            self.controller.model.update_prep_group(self.current_group_id, name, desc, product_code)
        else:
            self.controller.model.add_prep_group(self.machine_id, name, desc, product_code)

        self._load_groups()

    def _delete_group(self):
        selected_items = self.groups_list.selectedItems()
        if not selected_items:
            self.controller.view.show_message("Selección Requerida", "Por favor, seleccione un grupo para eliminar.", "warning")
            return

        group_id, group_name, _ = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if self.controller.view.show_confirmation_dialog("Confirmar Eliminación", f"¿Está seguro de que desea eliminar el grupo '{group_name}'?"):
            self.controller.model.delete_prep_group(group_id)
            self._load_groups()

    def _manage_steps(self):
        selected_items = self.groups_list.selectedItems()
        if not selected_items:
            self.controller.view.show_message("Selección Requerida", "Por favor, seleccione un grupo para gestionar sus pasos.", "warning")
            return

        group_id, group_name, _ = selected_items[0].data(Qt.ItemDataRole.UserRole)
        dialog = PrepStepsDialog(group_id, group_name, self.controller, self)
        dialog.exec()


class PreprocesoDialog(QDialog):
    """
    Diálogo para crear o editar un Preproceso, permitiendo la asignación
    de materiales (componentes).
    """
    def __init__(self, preproceso_existente: dict = None, all_materials: list = None, controller=None, parent=None):
        super().__init__(parent)
        logging.info(f"PreprocesoDialog.__init__ called. Controller arg: {controller}")
        self.preproceso_data = preproceso_existente
        self.all_materials = all_materials if all_materials else []
        self.controller = controller  # REQUIRED for managing components
        self.assigned_material_ids = set()

        if self.preproceso_data:
            # Handle DTO or dict
            if hasattr(self.preproceso_data, 'componentes'):
                self.assigned_material_ids = {comp.id for comp in self.preproceso_data.componentes}
            elif 'componentes' in self.preproceso_data:
                self.assigned_material_ids = {comp[0] for comp in self.preproceso_data['componentes']}

        title = "Editar Preproceso" if self.preproceso_data else "Crear Nuevo Preproceso"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Pestañas para organizar la información ---
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # --- Pestaña 1: Datos Básicos ---
        basic_data_widget = QWidget()
        form_layout = QFormLayout(basic_data_widget)
        self.nombre_entry = QLineEdit()
        self.tiempo_entry = QLineEdit()
        self.descripcion_entry = QTextEdit()
        self.descripcion_entry.setMaximumHeight(80)
        form_layout.addRow("<b>Nombre:</b>", self.nombre_entry)
        form_layout.addRow("<b>Tiempo (minutos):</b>", self.tiempo_entry)
        form_layout.addRow("<b>Descripción:</b>", self.descripcion_entry)
        tab_widget.addTab(basic_data_widget, "📝 Datos Básicos")

        # --- Pestaña 2: Asignación de Componentes ---
        components_widget = QWidget()
        components_layout = QVBoxLayout(components_widget)
        components_layout.addWidget(QLabel("Seleccione los materiales que componen este preproceso:"))
        
        # Lista de materiales
        self.materials_list = QListWidget()
        self.materials_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        components_layout.addWidget(self.materials_list)

        # Botones de gestión de componentes (NUEVO)
        btns_layout = QHBoxLayout()
        add_btn = QPushButton("Añadir Componente")
        edit_btn = QPushButton("Editar Componente")
        del_btn = QPushButton("Eliminar Componente")
        btns_layout.addWidget(add_btn)
        btns_layout.addWidget(edit_btn)
        btns_layout.addWidget(del_btn)
        components_layout.addLayout(btns_layout)

        add_btn.clicked.connect(self._on_add_material)
        edit_btn.clicked.connect(self._on_edit_material)
        del_btn.clicked.connect(self._on_delete_material)

        tab_widget.addTab(components_widget, "🔩 Componentes")

        # Poblar datos si estamos editando
        if self.preproceso_data:
            if hasattr(self.preproceso_data, 'nombre'):
                # DTO Access
                self.nombre_entry.setText(self.preproceso_data.nombre)
                self.tiempo_entry.setText(str(getattr(self.preproceso_data, 'tiempo', 0.0)))
                self.descripcion_entry.setPlainText(self.preproceso_data.descripcion or '')
            else:
                # Dict Access
                self.nombre_entry.setText(self.preproceso_data.get('nombre', ''))
                self.tiempo_entry.setText(str(self.preproceso_data.get('tiempo', 0.0)))
                self.descripcion_entry.setPlainText(self.preproceso_data.get('descripcion', ''))

        self._populate_materials_list()
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _populate_materials_list(self):
        """Rellena la lista con los materiales actuales."""
        self.materials_list.clear()
        for material in self.all_materials:
            # Soporte para DTOs (nuevo) y tuplas (legacy)
            if hasattr(material, 'id') and hasattr(material, 'descripcion_componente'):
                mat_id = material.id
                mat_desc = material.descripcion_componente
                mat_code = material.codigo_componente if hasattr(material, 'codigo_componente') else "N/A"
            else:
                mat_id, mat_desc = material
                mat_code = "?"
            
            item = QListWidgetItem(f"{mat_code} - {mat_desc}")
            item.setData(Qt.ItemDataRole.UserRole, mat_id)
            item.setData(Qt.ItemDataRole.UserRole + 1, mat_code) # Guardar codigo
            item.setData(Qt.ItemDataRole.UserRole + 2, mat_desc) # Guardar desc

            self.materials_list.addItem(item)
            if mat_id in self.assigned_material_ids:
                item.setSelected(True)

    def _refresh_data(self):
        """Recarga los materiales desde el modelo y actualiza la lista."""
        if not self.controller: return
        self.all_materials = self.controller.model.get_all_materials_for_selection()
        
        # Guardamos la selección actual para restaurarla (si es que aún existen los items)
        # Nota: assigned_material_ids ya rastrea lo que queremos que esté seleccionado.
        # Pero si el usuario seleccionó cosas nuevas en la UI antes de añadir un nuevo item,
        # deberíamos actualizar assigned_material_ids primero.
        self._update_assigned_ids_from_selection()
        
        self._populate_materials_list()

    def _update_assigned_ids_from_selection(self):
        """Sincroniza el set interno con lo que está seleccionado en la UI."""
        current_selection = set()
        for item in self.materials_list.selectedItems():
            current_selection.add(item.data(Qt.ItemDataRole.UserRole))
        # Actualizamos assigned_material_ids con la selección actual en UI
        # (Mejor comportamiento: Mantener lo seleccionado visiblemente)
        self.assigned_material_ids = current_selection

    def _on_add_material(self):
        logging.info(f"_on_add_material clicked. Controller: {self.controller}")
        if not self.controller: return
        codigo, ok1 = QInputDialog.getText(self, "Añadir Componente", "Código:")
        if not (ok1 and codigo.strip()): return
        desc, ok2 = QInputDialog.getText(self, "Añadir Componente", "Descripción:")
        if not (ok2 and desc.strip()): return

        if self.controller.handle_create_material(codigo, desc):
            self._refresh_data()

    def _on_edit_material(self):
        logging.info(f"_on_edit_material clicked. Controller: {self.controller}")
        if not self.controller: return
        selected_items = self.materials_list.selectedItems()
        # Nota: QListWidget en MultiSelection permite seleccionar varios.
        # Para editar, pedimos que seleccione solo uno (o tomamos el primero).
        if len(selected_items) != 1:
            QMessageBox.warning(self, "Selección Única", "Seleccione un único componente para editar.")
            return

        item = selected_items[0]
        mat_id = item.data(Qt.ItemDataRole.UserRole)
        old_code = item.data(Qt.ItemDataRole.UserRole + 1)
        old_desc = item.data(Qt.ItemDataRole.UserRole + 2)

        new_code, ok1 = QInputDialog.getText(self, "Editar Componente", "Código:", text=old_code)
        if not (ok1 and new_code.strip()): return
        new_desc, ok2 = QInputDialog.getText(self, "Editar Componente", "Descripción:", text=old_desc)
        if not (ok2 and new_desc.strip()): return

        if self.controller.handle_update_material(mat_id, new_code, new_desc):
            self._refresh_data()

    def _on_delete_material(self):
        logging.info(f"_on_delete_material clicked. Controller: {self.controller}")
        if not self.controller: return
        selected_items = self.materials_list.selectedItems()
        if not selected_items:
             QMessageBox.warning(self, "Selección", "Seleccione componente(s) para eliminar.")
             return
        
        if QMessageBox.question(self, "Confirmar Eliminación", 
                                "¿Está seguro de eliminar los componentes seleccionados DEL SISTEMA COMPLETO?\n"
                                "Esto afectará a todos los productos y preprocesos que los usen.",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return

        for item in selected_items:
            mat_id = item.data(Qt.ItemDataRole.UserRole)
            self.controller.handle_delete_material(mat_id)
            # Removemos del set assigned para que no intente re-seleccionarlo
            if mat_id in self.assigned_material_ids:
                self.assigned_material_ids.remove(mat_id)
        
        self._refresh_data()

    def get_data(self) -> dict | None:
        nombre = self.nombre_entry.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Campo Requerido", "El nombre del preproceso es obligatorio.")
            return None
        try:
            tiempo = float(self.tiempo_entry.text().strip().replace(",", "."))
            if tiempo < 0: raise ValueError
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Dato Inválido", "El tiempo debe ser un número positivo (o cero).")
            return None

        # Sincronizamos selección final
        self._update_assigned_ids_from_selection()
        
        return {
            "nombre": nombre,
            "descripcion": self.descripcion_entry.toPlainText().strip(),
            "tiempo": tiempo,
            "componentes_ids": list(self.assigned_material_ids)
        }


