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

from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QDate, QTimer, QTime, QPoint, QRectF, QSize
from PyQt6.QtGui import (
    QFont, QPixmap, QPainter, QColor, QBrush, QTextCharFormat, QIcon, QPen, QPalette,
    QPolygonF
)


# --- Split Dialogs Imports ---


class ProductDetailsDialog(QDialog):
    """
    Diálogo rediseñado con pestañas para gestionar Componentes e Iteraciones de un producto.
    """
    def __init__(self, product_code, controller, parent=None):
        super().__init__(parent)
        self.product_code = product_code
        self.controller = controller
        self.view = parent # La vista principal (MainView)
        self.logger = logging.getLogger("EvolucionTiemposApp")

        prod_data, _, _ = self.controller.model.get_product_details(self.product_code)
        prod_desc = prod_data.descripcion if prod_data else ""
        self.setWindowTitle(f"Detalles de Producto: {self.product_code} - {prod_desc}")
        self.setMinimumSize(950, 700)

        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Crear Pestañas
        self._create_components_tab()
        self._create_iterations_tab()

        self.load_all_data()

    def load_all_data(self):
        """Carga los datos para ambas pestañas."""
        self.load_components()
        self.load_iterations()

    # --- PESTAÑA DE COMPONENTES ---
    def _create_components_tab(self):
        components_widget = QWidget()
        layout = QVBoxLayout(components_widget)
        self.tab_widget.addTab(components_widget, "Componentes (Lista de Materiales)")

        layout.addWidget(QLabel("<b>Componentes asociados a este producto:</b>"))
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(2)
        self.materials_table.setHorizontalHeaderLabels(["Código", "Descripción"])
        self.materials_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.materials_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.materials_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.materials_table)

        buttons_layout = QHBoxLayout()
        add_button = QPushButton("Añadir Componente")
        edit_button = QPushButton("Editar Componente")
        delete_button = QPushButton("Eliminar Componente")
        import_button = QPushButton("Importar desde Excel")
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(import_button)
        layout.addLayout(buttons_layout)

        add_button.clicked.connect(self._on_add_material)
        edit_button.clicked.connect(self._on_edit_material)
        delete_button.clicked.connect(self._on_delete_material)
        import_button.clicked.connect(self._on_import_materials_clicked)

    def load_components(self):
        """Carga la lista de materiales del producto en la tabla."""
        self.materials_table.setRowCount(0)
        materials = self.controller.model.get_materials_for_product(self.product_code)
        for mat in materials:
            row_pos = self.materials_table.rowCount()
            self.materials_table.insertRow(row_pos)
            item_code = QTableWidgetItem(mat.codigo_componente)
            item_code.setData(Qt.ItemDataRole.UserRole, mat.id) # Guardamos el ID del material
            self.materials_table.setItem(row_pos, 0, item_code)
            self.materials_table.setItem(row_pos, 1, QTableWidgetItem(mat.descripcion_componente))

    def _on_add_material(self):
        codigo, ok1 = QInputDialog.getText(self, "Añadir Componente", "Código del Componente:")
        if not (ok1 and codigo.strip()): return
        descripcion, ok2 = QInputDialog.getText(self, "Añadir Componente", "Descripción:")
        if not (ok2 and descripcion.strip()): return

        if self.controller.handle_add_material_to_product(self.product_code, codigo, descripcion):
            self.load_components()

    def _on_edit_material(self):
        selected_items = self.materials_table.selectedItems()
        if not selected_items:
            self.view.show_message("Atención", "Debe seleccionar un componente para editar.", "warning")
            return
        row = selected_items[0].row()
        material_id = self.materials_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        current_codigo = self.materials_table.item(row, 0).text()
        current_desc = self.materials_table.item(row, 1).text()

        nuevo_codigo, ok1 = QInputDialog.getText(self, "Editar Componente", "Código:", text=current_codigo)
        if not (ok1 and nuevo_codigo.strip()): return
        nueva_desc, ok2 = QInputDialog.getText(self, "Editar Componente", "Descripción:", text=current_desc)
        if not (ok2 and nueva_desc.strip()): return

        if self.controller.handle_update_material(material_id, nuevo_codigo, nueva_desc):
            self.load_components()

    def _on_delete_material(self):
        selected_items = self.materials_table.selectedItems()
        if not selected_items:
            self.view.show_message("Atención", "Debe seleccionar un componente para eliminar.", "warning")
            return
        row = selected_items[0].row()
        material_id = self.materials_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        codigo = self.materials_table.item(row, 0).text()

        if self.view.show_confirmation_dialog("Confirmar", f"¿Seguro que desea eliminar el componente '{codigo}' de este producto?"):
            if self.controller.handle_unlink_material_from_product(self.product_code, material_id):
                self.load_components()

    def _on_import_materials_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo Excel", "", "Archivos de Excel (*.xlsx *.xls)")
        if not file_path:
            return
        if self.controller.handle_import_materials_to_product(self.product_code, file_path):
            self.load_components()

    # --- PESTAÑA DE ITERACIONES ---
    def _create_iterations_tab(self):
        iterations_widget = QWidget()
        layout = QHBoxLayout(iterations_widget)
        self.tab_widget.addTab(iterations_widget, "Historial de Iteraciones")

        # Panel Izquierdo (Detalles)
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.details_layout = QVBoxLayout(left_panel)
        layout.addWidget(left_panel, 1)

        # Panel Derecho (Historial)
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("<b>Historial de Cambios</b>"))
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["Fecha", "Responsable", "Descripción"])
        self.history_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.history_tree.setColumnWidth(0, 150)
        right_layout.addWidget(self.history_tree)

        history_buttons_layout = QHBoxLayout()
        add_iteration_button = QPushButton("Añadir Nueva Iteración")
        edit_iteration_button = QPushButton("Editar Iteración")
        delete_iteration_button = QPushButton("Eliminar Iteración")
        self.edit_iteration_button = edit_iteration_button
        self.delete_iteration_button = delete_iteration_button
        history_buttons_layout.addWidget(add_iteration_button)
        history_buttons_layout.addWidget(edit_iteration_button)
        history_buttons_layout.addWidget(delete_iteration_button)
        right_layout.addLayout(history_buttons_layout)
        layout.addWidget(right_panel, 2)

        self._create_details_panel_widgets()
        self._clear_details_panel()

        self.history_tree.itemClicked.connect(self._on_iteration_selected)
        add_iteration_button.clicked.connect(self._on_add_new_iteration_clicked)
        edit_iteration_button.clicked.connect(self._on_edit_iteration_clicked)
        delete_iteration_button.clicked.connect(self._on_delete_iteration_clicked)

    def _create_details_panel_widgets(self):
        self.details_title = QLabel("Detalles de la Iteración")
        font = self.details_title.font();
        font.setPointSize(16);
        font.setBold(True)
        self.details_title.setFont(font)
        self.details_layout.addWidget(self.details_title)

        self.details_form_layout = QFormLayout()
        self.responsable_label = QLabel()
        self.tipo_fallo_label = QLabel()  # ✅ NUEVO
        self.descripcion_text = QTextEdit()
        self.descripcion_text.setReadOnly(True)
        self.details_form_layout.addRow("<b>Responsable:</b>", self.responsable_label)
        self.details_form_layout.addRow("<b>Categoría:</b>", self.tipo_fallo_label)  # ✅ NUEVO
        self.details_form_layout.addRow("<b>Descripción:</b>", self.descripcion_text)
        self.details_layout.addLayout(self.details_form_layout)

        # Panel de adjuntos (Galería)
        adjuntos_layout = QVBoxLayout()
        adjuntos_layout.addWidget(QLabel("<b>Imágenes Adjuntas:</b>"))

        # Galería de imágenes (QListWidget en modo Icono)
        self.image_gallery = QListWidget()
        self.image_gallery.setViewMode(QListWidget.ViewMode.IconMode)
        self.image_gallery.setIconSize(QSize(120, 120))
        self.image_gallery.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.image_gallery.setSpacing(10)
        self.image_gallery.setMinimumHeight(200)
        self.image_gallery.itemDoubleClicked.connect(self._on_gallery_item_double_clicked)
        adjuntos_layout.addWidget(self.image_gallery)

        # Botones de gestión de imágenes
        botones_imagenes_layout = QHBoxLayout()
        self.add_image_button = QPushButton("➕ Añadir Imagen")
        self.add_image_button.clicked.connect(self._on_add_image_clicked)
        self.delete_image_button = QPushButton("🗑️ Eliminar Imagen")
        self.delete_image_button.clicked.connect(self._on_delete_image_clicked)
        
        botones_imagenes_layout.addWidget(self.add_image_button)
        botones_imagenes_layout.addWidget(self.delete_image_button)
        adjuntos_layout.addLayout(botones_imagenes_layout)

        # Botón para el plano
        self.view_plano_button = QPushButton("📄 Ver Plano Adjunto")
        self.view_plano_button.clicked.connect(self._on_view_plano_clicked)
        adjuntos_layout.addWidget(self.view_plano_button)

        self.details_layout.addLayout(adjuntos_layout)
        self.details_layout.addStretch()

    def _clear_details_panel(self):
        # (Este método es idéntico al de la clase original)
        for i in range(self.details_layout.count()):
            item = self.details_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setVisible(False)
        if hasattr(self, 'placeholder'):
            self.placeholder.deleteLater()
        self.placeholder = QLabel("Seleccione una iteración del historial para ver sus detalles,\no añada una nueva.")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setWordWrap(True)
        self.details_layout.addWidget(self.placeholder)
        self.current_selected_iteration_id = None
        self.edit_iteration_button.setEnabled(False)
        self.delete_iteration_button.setEnabled(False)

    def _show_details_panel(self):
        # (Este método es idéntico al de la clase original)
        if hasattr(self, 'placeholder'):
            self.placeholder.setVisible(False)
        for i in range(self.details_layout.count()):
            item = self.details_layout.itemAt(i)
            widget = item.widget()
            if widget and widget != self.placeholder:
                widget.setVisible(True)

    def load_iterations(self):
        # (Este método es casi idéntico, solo cambia el nombre de la función)
        self.history_tree.clear()
        iterations = self.controller.model.get_product_iterations(self.product_code)
        for iteration in iterations:
            fecha_obj = iteration.fecha_creacion
            if isinstance(fecha_obj, str):
               fecha_obj = datetime.strptime(fecha_obj, '%Y-%m-%d %H:%M:%S')

            fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
            item_text = [fecha_str, iteration.nombre_responsable, iteration.descripcion]
            tree_item = QTreeWidgetItem(self.history_tree, item_text)
            tree_item.setData(0, Qt.ItemDataRole.UserRole, iteration)
        self._clear_details_panel()

    def _on_iteration_selected(self, item):
        iteration_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not iteration_data:
            return

        self._show_details_panel()
        self.edit_iteration_button.setEnabled(True)
        self.delete_iteration_button.setEnabled(True)

        self.current_selected_iteration_id = iteration_data.id
        self.responsable_label.setText(iteration_data.nombre_responsable)
        self.descripcion_text.setPlainText(iteration_data.descripcion)
        self.tipo_fallo_label.setText(getattr(iteration_data, 'tipo_fallo', 'No especificado'))

        # Cargar galería de imágenes
        self.image_gallery.clear()
        
        # 1. Cargar imagen principal "legacy" si existe
        legacy_image = getattr(iteration_data, 'ruta_imagen', None)
        if legacy_image and os.path.exists(legacy_image):
            self._add_image_to_gallery(legacy_image, "Imagen Principal (Legacy)", is_legacy=True)

        # 2. Cargar imágenes adicionales desde la nueva tabla
        additional_images = self.controller.model.db.iteration_repo.get_images(iteration_data.id)
        for img_data in additional_images:
            path = img_data['image_path']
            # Evitar duplicados si la legacy es la misma que alguna nueva (migración implícita)
            if path != legacy_image and os.path.exists(path):
                self._add_image_to_gallery(path, img_data.get('description', ''), image_id=img_data['id'])
        
        self.view_plano_button.setEnabled(bool(getattr(iteration_data, 'ruta_plano', None)))

    def _add_image_to_gallery(self, path, tooltip, image_id=None, is_legacy=False):
        """Helper para añadir un item a la galería."""
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            icon = QIcon(pixmap)
            item = QListWidgetItem(icon, "")
            item.setToolTip(tooltip or "Sin descripción")
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setData(Qt.ItemDataRole.UserRole + 1, image_id) # ID de base de datos
            item.setData(Qt.ItemDataRole.UserRole + 2, is_legacy)
            self.image_gallery.addItem(item)

    def _on_gallery_item_double_clicked(self, item):
        """Abre la imagen en tamaño completo."""
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.controller.handle_view_file(path)

    def _on_view_plano_clicked(self):
        if self.current_selected_iteration_id is None:
            return

        iterations = self.controller.model.get_product_iterations(self.product_code)
        selected_iteration = next((it for it in iterations if it.id == self.current_selected_iteration_id), None)

        if selected_iteration and getattr(selected_iteration, 'ruta_plano', None):
            self.controller.handle_view_file(selected_iteration.ruta_plano)
        else:
            self.view.show_message("Información", "No hay ningún plano adjunto para esta iteración.", "info")

    def _on_add_new_iteration_clicked(self):
        """
        Abre un diálogo para crear una nueva iteración.
        """
        dialog = AddIterationDialog(self.product_code, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["responsable"] or not data["descripcion"]:
                self.view.show_message("Campos Vacíos", "El responsable y la descripción son obligatorios.", "warning")
                return

            if self.controller.handle_add_product_iteration(self.product_code, data):
                self.load_iterations()

    def _on_edit_iteration_clicked(self):
        if self.current_selected_iteration_id is None:
           self.view.show_message("Atención", "Debe seleccionar una iteración para editar.", "warning")
           return
        current_responsable = self.responsable_label.text()
        current_descripcion = self.descripcion_text.toPlainText()
        nuevo_responsable, ok1 = QInputDialog.getText(self, "Editar Iteración", "Responsable:", text=current_responsable)
        if not (ok1 and nuevo_responsable.strip()): return
        nueva_descripcion, ok2 = QInputDialog.getMultiLineText(self, "Editar Iteración", "Descripción:", text=current_descripcion)
        if not (ok2 and nueva_descripcion.strip()): return
        if self.controller.handle_update_product_iteration(self.current_selected_iteration_id, nuevo_responsable, nueva_descripcion):
            self.load_iterations()

    def _on_delete_iteration_clicked(self):
        if self.current_selected_iteration_id is None:
            self.view.show_message("Atención", "Debe seleccionar una iteración para eliminar.", "warning")
            return
        if self.view.show_confirmation_dialog("Confirmar", "¿Seguro que desea eliminar esta iteración?"):
            if self.controller.handle_delete_product_iteration(self.current_selected_iteration_id):
                self.load_iterations()

    def _on_add_image_clicked(self):
        if self.current_selected_iteration_id is None:
           self.view.show_message("Atención", "Debe seleccionar una iteración.", "warning")
           return
        
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Seleccionar Imágenes", "", "Archivos de Imagen (*.png *.jpg *.jpeg)")
        if not file_paths: return

        count = 0
        for path in file_paths:
            success, msg = self.controller.handle_add_iteration_image(self.current_selected_iteration_id, path)
            if success: count += 1
        
        if count > 0:
           self.load_iterations() # Recargar datos
           self._reselect_current_iteration()
           self.view.show_message("Éxito", f"{count} imágenes añadidas correctamente.", "info")
        else:
           self.view.show_message("Error", "No se pudieron añadir las imágenes.", "warning")

    def _on_delete_image_clicked(self):
        selected_items = self.image_gallery.selectedItems()
        if not selected_items:
            self.view.show_message("Atención", "Seleccione una imagen para eliminar.", "warning")
            return

        item = selected_items[0]
        image_id = item.data(Qt.ItemDataRole.UserRole + 1)
        is_legacy = item.data(Qt.ItemDataRole.UserRole + 2)

        if is_legacy:
            self.view.show_message("Aviso", "La imagen principal (legacy) no se puede eliminar desde aquí por ahora. Reemplácela subiendo una nueva imagen principal si es necesario.", "info")
            return

        if self.view.show_confirmation_dialog("Confirmar", "¿Eliminar esta imagen de la galería?"):
            if self.controller.handle_delete_iteration_image(image_id):
                 self.load_iterations()
                 self._reselect_current_iteration()
                 self.view.show_message("Éxito", "Imagen eliminada.", "info")
            else:
                 self.view.show_message("Error", "No se pudo eliminar la imagen.", "critical")

    def _reselect_current_iteration(self):
        """Helper para mantener la selección tras recargar."""
        iterator = QTreeWidgetItemIterator(self.history_tree)
        while iterator.value():
            item = iterator.value()
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data.id == self.current_selected_iteration_id:
                self.history_tree.setCurrentItem(item)
                self._on_iteration_selected(item)
                break
            iterator += 1

    def _on_attach_image_clicked(self):
         # DEPRECATED: Redirecciona a nueva función
         self._on_add_image_clicked()


class AddIterationDialog(QDialog):
    """Diálogo para añadir una nueva iteración con todos los campos requeridos."""

    def __init__(self, product_code, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Nueva Iteración")
        self.setMinimumWidth(500)
        self.product_code = product_code
        self.attached_plano_path = None

        self.layout = QFormLayout(self)
        self.responsable_edit = QLineEdit()
        self.tipo_fallo_combo = QComboBox()
        self.tipo_fallo_combo.addItems([
            "No especificado",
            "Fallo de Proveedor",
            "Fallo de Producción",
            "Mejora de Diseño",
            "Observación de Cliente"
        ])
        self.description_edit = QTextEdit()

        plano_layout = QHBoxLayout()
        self.plano_label = QLabel("Ningún plano adjunto.")
        attach_plano_button = QPushButton("Adjuntar Plano...")
        attach_plano_button.clicked.connect(self._attach_plano)
        plano_layout.addWidget(self.plano_label)
        plano_layout.addWidget(attach_plano_button)

        self.layout.addRow("<b>Responsable:</b>", self.responsable_edit)
        self.layout.addRow("<b>Categoría:</b>", self.tipo_fallo_combo)
        self.layout.addRow("<b>Descripción del Cambio:</b>", self.description_edit)
        self.layout.addRow("<b>Plano (Opcional):</b>", plano_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def _attach_plano(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Plano", "",
                                                   "Archivos PDF (*.pdf);;Todos los archivos (*.*)")
        if file_path:
            self.attached_plano_path = file_path
            self.plano_label.setText(os.path.basename(file_path))

    def get_data(self):
        return {
            "responsable": self.responsable_edit.text().strip(),
            "descripcion": self.description_edit.toPlainText().strip(),
            "tipo_fallo": self.tipo_fallo_combo.currentText(),
            "ruta_plano_origen": self.attached_plano_path
        }


class SubfabricacionesDialog(QDialog):
    """
    Diálogo para gestionar (CRUD) la lista de sub-fabricaciones de un producto.
    """

    def __init__(self, subfabricaciones_actuales, available_machines, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionar Sub-fabricaciones")
        self.setMinimumSize(600, 500)

        self.subfabricaciones = list(subfabricaciones_actuales)
        self._selected_row = -1

        main_layout = QVBoxLayout(self)

        # --- Tabla para mostrar la lista ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Descripción", "Tiempo (min)", "Tipo Trabajador", "Máquina Asignada"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_item_selected)
        main_layout.addWidget(self.table)

        # --- Formulario para añadir/editar ---
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_frame)
        self.desc_entry = QLineEdit()
        self.tiempo_entry = QLineEdit()
        self.trabajador_menu = QComboBox()
        self.trabajador_menu.addItems(["Tipo 1", "Tipo 2", "Tipo 3"])
        self.tipo_proceso_menu = QComboBox()
        self.tipo_proceso_menu.addItem("(Ninguna)", userData=None)
        for machine in available_machines:
            # Ahora machine es un MachineDTO, usamos acceso por atributos
            self.tipo_proceso_menu.addItem(machine.nombre, userData=machine.id)

        form_layout.addRow("Descripción:", self.desc_entry)
        form_layout.addRow("Tiempo (min):", self.tiempo_entry)
        form_layout.addRow("Tipo de Trabajador:", self.trabajador_menu)
        form_layout.addRow("Máquina Requerida:", self.tipo_proceso_menu)

        self.add_update_button = QPushButton("Añadir Sub-fabricación")
        self.add_update_button.clicked.connect(self._add_or_update)
        form_layout.addRow(self.add_update_button)
        main_layout.addWidget(form_frame)

        action_layout = QHBoxLayout()
        self.delete_button = QPushButton("Eliminar Seleccionado")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._delete_selected)
        action_layout.addStretch()
        action_layout.addWidget(self.delete_button)
        main_layout.addLayout(action_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._refresh_table()

    def _refresh_table(self):
        self.table.setRowCount(0)
        for sub in self.subfabricaciones:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            self.table.setItem(row_pos, 0, QTableWidgetItem(sub['descripcion']))
            self.table.setItem(row_pos, 1, QTableWidgetItem(str(sub['tiempo'])))
            self.table.setItem(row_pos, 2, QTableWidgetItem(f"Tipo {sub['tipo_trabajador']}"))

            # CORRECCIÓN: Busca el nombre de la máquina usando el maquina_id guardado.
            machine_name = ""
            machine_id = sub.get('maquina_id')
            if machine_id:
                # Busca en el ComboBox el item cuyo 'userData' (el ID) coincida.
                index = self.tipo_proceso_menu.findData(machine_id)
                if index != -1:
                    machine_name = self.tipo_proceso_menu.itemText(index)
            self.table.setItem(row_pos, 3, QTableWidgetItem(machine_name))

    def _on_item_selected(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            self._selected_row = -1
            self.delete_button.setEnabled(False)
            self.add_update_button.setText("Añadir Sub-fabricación")
            self._clear_form()
            return

        self._selected_row = self.table.row(selected_items[0])
        sub = self.subfabricaciones[self._selected_row]

        self.desc_entry.setText(sub['descripcion'])
        self.tiempo_entry.setText(str(sub['tiempo']))
        self.trabajador_menu.setCurrentIndex(sub['tipo_trabajador'] - 1)

        assigned_machine_id = sub.get('maquina_id')
        if assigned_machine_id:
            index = self.tipo_proceso_menu.findData(assigned_machine_id)
            if index != -1:
                self.tipo_proceso_menu.setCurrentIndex(index)
            else:
                # Si no se encuentra la máquina (p.ej. fue eliminada), se selecciona "(Ninguna)"
                self.tipo_proceso_menu.setCurrentIndex(0)
        else:
            self.tipo_proceso_menu.setCurrentIndex(0)

        self.delete_button.setEnabled(True)
        self.add_update_button.setText("Actualizar Sub-fabricación")

    def _add_or_update(self):
        desc = self.desc_entry.text().strip()
        tiempo_str = self.tiempo_entry.text().strip().replace(",", ".")

        if not desc or not tiempo_str:
            QMessageBox.warning(self, "Campos Vacíos", "La descripción y el tiempo son obligatorios.")
            return

        try:
            tiempo = float(tiempo_str)
            if tiempo <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Dato Inválido", "El tiempo debe ser un número positivo.")
            return

        tipo_trabajador = self.trabajador_menu.currentIndex() + 1
        machine_id = self.tipo_proceso_menu.currentData()
        new_data = {
            "descripcion": desc,
            "tiempo": tiempo,
            "tipo_trabajador": tipo_trabajador,
            "maquina_id": machine_id
        }

        if self._selected_row != -1:
            self.subfabricaciones[self._selected_row] = new_data
        else:
            self.subfabricaciones.append(new_data)

        self._clear_form()
        self._refresh_table()

    def _delete_selected(self):
        if self._selected_row != -1:
            self.subfabricaciones.pop(self._selected_row)
            self._clear_form()
            self._refresh_table()

    def _clear_form(self):
        self.desc_entry.clear()
        self.tiempo_entry.clear()
        self.trabajador_menu.setCurrentIndex(0)
        self.tipo_proceso_menu.setCurrentIndex(0)
        self.table.clearSelection()
        self._selected_row = -1
        self.delete_button.setEnabled(False)
        self.add_update_button.setText("Añadir Sub-fabricación")

    def get_updated_subfabricaciones(self):
        return self.subfabricaciones

    def accept(self):
        """
        Sobrescribe el método accept para avisar si hay datos en el formulario sin guardar.
        """
        if self.desc_entry.text().strip() or self.tiempo_entry.text().strip():
            reply = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "Hay datos en el formulario de edición que no se han añadido/actualizado en la lista.\n"
                "¿Deseas descartarlos y cerrar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        super().accept()


class ProcesosMecanicosDialog(QDialog):
    """
    Diálogo para gestionar los procesos mecánicos de un producto.
    Similar a SubfabricacionesDialog pero sin máquinas.
    """

    def __init__(self, current_procesos, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionar Procesos Mecánicos")
        self.setModal(True)
        self.resize(800, 600)

        self.procesos_data = current_procesos.copy() if current_procesos else []
        self.setup_ui()
        self.populate_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Procesos Mecánicos del Producto")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Tabla de procesos
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Nombre", "Descripción", "Tiempo (min)", "Tipo Trabajador", "Acciones"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table)

        # Botón añadir
        add_button = QPushButton("➕ Añadir Proceso Mecánico")
        add_button.clicked.connect(self.add_proceso)
        layout.addWidget(add_button)

        # Botones de diálogo
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def populate_table(self):
        self.table.setRowCount(len(self.procesos_data))
        for row, proceso in enumerate(self.procesos_data):
            # Nombre
            self.table.setItem(row, 0, QTableWidgetItem(proceso.get("nombre", "")))
            # Descripción
            self.table.setItem(row, 1, QTableWidgetItem(proceso.get("descripcion", "")))
            # Tiempo
            self.table.setItem(row, 2, QTableWidgetItem(str(proceso.get("tiempo", 0))))
            # Tipo trabajador
            self.table.setItem(row, 3, QTableWidgetItem(str(proceso.get("tipo_trabajador", 1))))

            # Botón eliminar
            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_proceso(r))
            self.table.setCellWidget(row, 4, delete_btn)

    def add_proceso(self):
        dialog = AddProcesoMecanicoDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_proceso = dialog.get_proceso_data()
            self.procesos_data.append(new_proceso)
            self.populate_table()

    def delete_proceso(self, row):
        if 0 <= row < len(self.procesos_data):
            del self.procesos_data[row]
            self.populate_table()

    def get_updated_procesos_mecanicos(self):
        # Actualizar datos desde la tabla antes de retornar
        updated_procesos = []
        for row in range(self.table.rowCount()):
            nombre_item = self.table.item(row, 0)
            desc_item = self.table.item(row, 1)
            tiempo_item = self.table.item(row, 2)
            trabajador_item = self.table.item(row, 3)

            if nombre_item and desc_item and tiempo_item and trabajador_item:
                try:
                    proceso = {
                        "nombre": nombre_item.text().strip(),
                        "descripcion": desc_item.text().strip(),
                        "tiempo": float(tiempo_item.text().replace(",", ".")),
                        "tipo_trabajador": int(trabajador_item.text())
                    }
                    if proceso["nombre"]:  # Solo añadir si tiene nombre
                        updated_procesos.append(proceso)
                except (ValueError, TypeError):
                    continue

        return updated_procesos


class AddProcesoMecanicoDialog(QDialog):
    """Diálogo para añadir un nuevo proceso mecánico."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Proceso Mecánico")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.nombre_entry = QLineEdit()
        self.descripcion_entry = QTextEdit()
        self.descripcion_entry.setMaximumHeight(80)
        self.tiempo_entry = QLineEdit()
        self.tipo_trabajador_combo = QComboBox()
        self.tipo_trabajador_combo.addItems(["1 - Oficial", "2 - Ayudante", "3 - Especialista"])

        layout.addRow("Nombre del Proceso:", self.nombre_entry)
        layout.addRow("Descripción:", self.descripcion_entry)
        layout.addRow("Tiempo (minutos):", self.tiempo_entry)
        layout.addRow("Tipo de Trabajador:", self.tipo_trabajador_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_proceso_data(self):
        return {
            "nombre": self.nombre_entry.text().strip(),
            "descripcion": self.descripcion_entry.toPlainText().strip(),
            "tiempo": float(self.tiempo_entry.text().replace(",", ".")) if self.tiempo_entry.text() else 0.0,
            "tipo_trabajador": self.tipo_trabajador_combo.currentIndex() + 1
        }


