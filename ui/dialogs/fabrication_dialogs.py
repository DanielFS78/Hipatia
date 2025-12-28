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


class CreateFabricacionDialog(QDialog):
    """
    Diálogo para crear una fabricación asignándole preprocesos Y productos.
    """

    def __init__(self, all_preprocesos, all_products=None, parent=None):
        super().__init__(parent)
        # Guardamos copias locales
        self.all_preprocesos = sorted(all_preprocesos, key=lambda x: x.id, reverse=True)
        self.all_products = all_products if all_products else []
        self.assigned_preprocesos = {}  # {id: data}
        self.assigned_products = {}  # {codigo: (data, cantidad)}

        self.setup_ui()
        self.load_initial_data()

    def setup_ui(self):
        self.setWindowTitle("Crear Nueva Fabricación")
        self.setModal(True)
        self.resize(900, 650)

        main_layout = QVBoxLayout(self)

        # --- Información de la Fabricación ---
        fab_info_group = QGroupBox("Datos de la Fabricación")
        form_layout = QFormLayout(fab_info_group)
        self.codigo_entry = QLineEdit()
        self.codigo_entry.setPlaceholderText("Código único para la fabricación (ej: PED-CLIENTE-01)")
        self.descripcion_entry = QLineEdit()
        self.descripcion_entry.setPlaceholderText("Descripción opcional")
        form_layout.addRow("<b>Código:</b>", self.codigo_entry)
        form_layout.addRow("<b>Descripción:</b>", self.descripcion_entry)
        main_layout.addWidget(fab_info_group)

        # --- Pestañas para Preprocesos y Productos ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # === PESTAÑA 1: PREPROCESOS ===
        preprocesos_tab = QWidget()
        self._setup_preprocesos_tab(preprocesos_tab)
        self.tabs.addTab(preprocesos_tab, "📋 Preprocesos")

        # === PESTAÑA 2: PRODUCTOS ===
        productos_tab = QWidget()
        self._setup_productos_tab(productos_tab)
        self.tabs.addTab(productos_tab, "📦 Productos")

        # --- Botones del Diálogo ---
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _setup_preprocesos_tab(self, tab_widget):
        """Configura la pestaña de Preprocesos."""
        assignment_layout = QHBoxLayout(tab_widget)

        # Panel Izquierdo: Preprocesos Disponibles
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("<b>Preprocesos Disponibles</b>"))
        self.prep_search_entry = QLineEdit()
        self.prep_search_entry.setPlaceholderText("Buscar por nombre o descripción...")
        self.prep_search_entry.textChanged.connect(self._filter_prep_available_list)
        left_panel.addWidget(self.prep_search_entry)
        self.prep_available_list = QListWidget()
        self.prep_available_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        left_panel.addWidget(self.prep_available_list)

        # Panel Central: Botones de Acción
        buttons_panel = QVBoxLayout()
        buttons_panel.addStretch()
        self.prep_add_button = QPushButton(">>")
        self.prep_add_button.setToolTip("Añadir preproceso seleccionado")
        self.prep_remove_button = QPushButton("<<")
        self.prep_remove_button.setToolTip("Quitar preproceso de la fabricación")
        buttons_panel.addWidget(self.prep_add_button)
        buttons_panel.addWidget(self.prep_remove_button)
        buttons_panel.addStretch()

        # Panel Derecho: Preprocesos Asignados
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("<b>Preprocesos en esta Fabricación</b>"))
        self.prep_assigned_list = QListWidget()
        right_panel.addWidget(self.prep_assigned_list)

        assignment_layout.addLayout(left_panel, 2)
        assignment_layout.addLayout(buttons_panel)
        assignment_layout.addLayout(right_panel, 2)

        # Conexiones
        self.prep_add_button.clicked.connect(self._assign_preproceso)
        self.prep_remove_button.clicked.connect(self._unassign_preproceso)

    def _setup_productos_tab(self, tab_widget):
        """Configura la pestaña de Productos."""
        assignment_layout = QHBoxLayout(tab_widget)

        # Panel Izquierdo: Productos Disponibles
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("<b>Productos Disponibles</b>"))
        self.prod_search_entry = QLineEdit()
        self.prod_search_entry.setPlaceholderText("Buscar por código o descripción...")
        self.prod_search_entry.textChanged.connect(self._filter_prod_available_list)
        left_panel.addWidget(self.prod_search_entry)
        self.prod_available_list = QListWidget()
        self.prod_available_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        left_panel.addWidget(self.prod_available_list)

        # Panel Central: Botones de Acción
        buttons_panel = QVBoxLayout()
        buttons_panel.addStretch()
        self.prod_add_button = QPushButton(">>")
        self.prod_add_button.setToolTip("Añadir producto seleccionado")
        self.prod_remove_button = QPushButton("<<")
        self.prod_remove_button.setToolTip("Quitar producto de la fabricación")
        buttons_panel.addWidget(self.prod_add_button)
        buttons_panel.addWidget(self.prod_remove_button)
        buttons_panel.addStretch()

        # Panel Derecho: Productos Asignados (con cantidad)
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("<b>Productos en esta Fabricación</b>"))
        self.prod_assigned_table = QTableWidget()
        self.prod_assigned_table.setColumnCount(3)
        self.prod_assigned_table.setHorizontalHeaderLabels(["Código", "Descripción", "Cantidad"])
        self.prod_assigned_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.prod_assigned_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        right_panel.addWidget(self.prod_assigned_table)

        assignment_layout.addLayout(left_panel, 2)
        assignment_layout.addLayout(buttons_panel)
        assignment_layout.addLayout(right_panel, 2)

        # Conexiones
        self.prod_add_button.clicked.connect(self._assign_product)
        self.prod_remove_button.clicked.connect(self._unassign_product)

    def load_initial_data(self):
        """Carga los datos iniciales en las listas."""
        # Cargar preprocesos
        self.prep_available_list.clear()
        for preproceso in self.all_preprocesos:
            item_text = f"{preproceso.nombre}"
            if preproceso.descripcion:
                item_text += f" - {preproceso.descripcion}"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, preproceso)
            self.prep_available_list.addItem(list_item)

        # Cargar productos
        self.prod_available_list.clear()
        for product in self.all_products:
            item_text = f"{product.codigo} - {product.descripcion}"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, product)
            self.prod_available_list.addItem(list_item)

    # --- Métodos para PREPROCESOS ---
    def _filter_prep_available_list(self):
        filter_text = self.prep_search_entry.text().lower()
        for i in range(self.prep_available_list.count()):
            item = self.prep_available_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and data.id in self.assigned_preprocesos:
                item.setHidden(True)
            else:
                item.setHidden(filter_text not in item.text().lower())

    def _assign_preproceso(self):
        selected_items = self.prep_available_list.selectedItems()
        for item in selected_items:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and data.id not in self.assigned_preprocesos:
                self.assigned_preprocesos[data.id] = data
        self._update_prep_assigned_list()
        self._filter_prep_available_list()

    def _unassign_preproceso(self):
        selected_items = self.prep_assigned_list.selectedItems()
        for item in selected_items:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and data.id in self.assigned_preprocesos:
                del self.assigned_preprocesos[data.id]
        self._update_prep_assigned_list()
        self._filter_prep_available_list()

    def _update_prep_assigned_list(self):
        self.prep_assigned_list.clear()
        sorted_assigned = sorted(self.assigned_preprocesos.values(), key=lambda x: x.nombre)
        for preproceso in sorted_assigned:
            list_item = QListWidgetItem(preproceso.nombre)
            list_item.setData(Qt.ItemDataRole.UserRole, preproceso)
            self.prep_assigned_list.addItem(list_item)

    # --- Métodos para PRODUCTOS ---
    def _filter_prod_available_list(self):
        filter_text = self.prod_search_entry.text().lower()
        for i in range(self.prod_available_list.count()):
            item = self.prod_available_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and data.codigo in self.assigned_products:
                item.setHidden(True)
            else:
                item.setHidden(filter_text not in item.text().lower())

    def _assign_product(self):
        selected_items = self.prod_available_list.selectedItems()
        for item in selected_items:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and data.codigo not in self.assigned_products:
                self.assigned_products[data.codigo] = (data, 1)  # Cantidad inicial = 1
        self._update_prod_assigned_table()
        self._filter_prod_available_list()

    def _unassign_product(self):
        selected_rows = self.prod_assigned_table.selectionModel().selectedRows()
        for index in selected_rows:
            codigo = self.prod_assigned_table.item(index.row(), 0).text()
            if codigo in self.assigned_products:
                del self.assigned_products[codigo]
        self._update_prod_assigned_table()
        self._filter_prod_available_list()

    def _update_prod_assigned_table(self):
        self.prod_assigned_table.setRowCount(0)
        for codigo, (data, cantidad) in sorted(self.assigned_products.items()):
            row = self.prod_assigned_table.rowCount()
            self.prod_assigned_table.insertRow(row)
            self.prod_assigned_table.setItem(row, 0, QTableWidgetItem(codigo))
            self.prod_assigned_table.setItem(row, 1, QTableWidgetItem(data.descripcion))
            
            # Spinbox para cantidad
            qty_spin = QSpinBox()
            qty_spin.setRange(1, 9999)
            qty_spin.setValue(cantidad)
            qty_spin.valueChanged.connect(lambda val, c=codigo: self._on_qty_changed(c, val))
            self.prod_assigned_table.setCellWidget(row, 2, qty_spin)

    def _on_qty_changed(self, codigo, new_value):
        if codigo in self.assigned_products:
            data, _ = self.assigned_products[codigo]
            self.assigned_products[codigo] = (data, new_value)

    # --- Validación y Datos ---
    def validate_and_accept(self):
        codigo = self.codigo_entry.text().strip()
        if not codigo:
            QMessageBox.warning(self, "Campo Obligatorio", "El código de la fabricación es obligatorio.")
            return

        if not self.assigned_preprocesos and not self.assigned_products:
            QMessageBox.warning(self, "Selección Requerida", 
                              "Debe asignar al menos un preproceso O un producto a la fabricación.")
            return

        self.accept()

    def get_fabricacion_data(self):
        """Retorna los datos de la fabricación incluyendo preprocesos y productos."""
        products_list = [(codigo, qty) for codigo, (data, qty) in self.assigned_products.items()]
        return {
            "codigo": self.codigo_entry.text().strip(),
            "descripcion": self.descripcion_entry.text().strip(),
            "preprocesos_ids": list(self.assigned_preprocesos.keys()),
            "productos": products_list  # Lista de (codigo, cantidad)
        }

    # --- Compatibilidad con versión anterior (sin productos) ---
    @property
    def search_entry(self):
        return self.prep_search_entry

    @property
    def available_list(self):
        return self.prep_available_list

    @property
    def assigned_list(self):
        return self.prep_assigned_list

    @property
    def add_button(self):
        return self.prep_add_button

    @property
    def remove_button(self):
        return self.prep_remove_button

    def filter_available_list(self):
        self._filter_prep_available_list()

    def assign_preproceso(self):
        self._assign_preproceso()

    def unassign_preproceso(self):
        self._unassign_preproceso()

    def update_available_list(self):
        self._filter_prep_available_list()

    def update_assigned_list(self):
        self._update_prep_assigned_list()


class PreprocesosSelectionDialog(QDialog):
    """
    Diálogo para seleccionar qué preprocesos asignar a una fabricación.
    """

    def __init__(self, fabricacion, all_preprocesos, assigned_ids, parent=None):
        super().__init__(parent)
        self.fabricacion = fabricacion
        self.all_preprocesos = all_preprocesos
        self.assigned_ids = set(assigned_ids)
        self.checkboxes = {}

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(f"Asignar Preprocesos - {self.fabricacion[1]}")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        # Información de la fabricación
        info_label = QLabel(f"<b>Fabricación:</b> {self.fabricacion[1]} - {self.fabricacion[2] or 'Sin descripción'}")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addWidget(QLabel("Seleccione los preprocesos que se aplicarán a esta fabricación:"))

        # Área de scroll para los preprocesos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        if not self.all_preprocesos:
            scroll_layout.addWidget(QLabel("No hay preprocesos disponibles. Cree preprocesos primero."))
        else:
            for preproceso in self.all_preprocesos:
                checkbox = QCheckBox()

                # Crear texto descriptivo
                componentes_text = ", ".join([comp.descripcion for comp in preproceso.componentes])
                texto = f"<b>{preproceso.nombre}</b>"
                if preproceso.descripcion:
                    texto += f"<br><i>{preproceso.descripcion}</i>"
                if componentes_text:
                    texto += f"<br>Componentes: {componentes_text}"

                checkbox.setText("")
                checkbox.setChecked(preproceso.id in self.assigned_ids)

                # Layout horizontal para checkbox y texto
                h_layout = QHBoxLayout()
                h_layout.addWidget(checkbox)

                label = QLabel(texto)
                label.setWordWrap(True)
                label.setStyleSheet("margin-left: 10px; padding: 5px;")
                h_layout.addWidget(label)

                # Widget contenedor
                container = QWidget()
                container.setLayout(h_layout)
                scroll_layout.addWidget(container)

                self.checkboxes[preproceso.id] = checkbox

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # Botones
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_preprocesos(self):
        """Retorna lista de IDs de preprocesos seleccionados."""
        return [
            preproceso_id for preproceso_id, checkbox in self.checkboxes.items()
            if checkbox.isChecked()
        ]


class PreprocesosForCalculationDialog(QDialog):
    """
    Diálogo para mostrar y seleccionar preprocesos disponibles
    para añadir al cálculo de tiempos de una fabricación.
    """

    def __init__(self, fabricacion_id, available_preprocesos, parent=None):
        super().__init__(parent)
        self.fabricacion_id = fabricacion_id
        self.available_preprocesos = available_preprocesos
        self.selected_preprocesos = []

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Preprocesos Disponibles")
        self.setModal(True)
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        # Instrucciones
        instructions = QLabel(
            "<b>Seleccione los preprocesos que desea añadir al cálculo de tiempos:</b><br>"
            "Los preprocesos seleccionados se añadirán como pasos adicionales en la planificación."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Lista de preprocesos disponibles
        self.preprocesos_list = QListWidget()
        self.preprocesos_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        if not self.available_preprocesos:
            item = QListWidgetItem("No hay preprocesos asignados a esta fabricación.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # No seleccionable
            self.preprocesos_list.addItem(item)
        else:
            for preproceso in self.available_preprocesos:
                # Crear descripción detallada
                tiempo_estimado = len(preproceso.get('componentes', [])) * 5  # 5 min por componente
                componentes_text = ", ".join([comp[1] for comp in preproceso.get('componentes', [])])

                text = f"{preproceso['nombre']} (~{tiempo_estimado} min)"
                if preproceso['descripcion']:
                    text += f"\n{preproceso['descripcion']}"
                if componentes_text:
                    text += f"\nComponentes: {componentes_text}"

                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, preproceso)
                self.preprocesos_list.addItem(item)

        layout.addWidget(self.preprocesos_list)

        # Información adicional
        info_label = QLabel(
            "<i>Nota: Los preprocesos añadidos aparecerán como tareas separadas "
            "que requerirán asignación de trabajadores en el siguiente paso.</i>"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666666; font-size: 10pt;")
        layout.addWidget(info_label)

        # Botones
        button_layout = QHBoxLayout()

        select_all_button = QPushButton("Seleccionar Todos")
        select_all_button.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_button)

        clear_selection_button = QPushButton("Limpiar Selección")
        clear_selection_button.clicked.connect(self.clear_selection)
        button_layout.addWidget(clear_selection_button)

        button_layout.addStretch()

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)

    def select_all(self):
        """Selecciona todos los preprocesos."""
        for i in range(self.preprocesos_list.count()):
            item = self.preprocesos_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsSelectable:
                item.setSelected(True)

    def clear_selection(self):
        """Limpia la selección."""
        self.preprocesos_list.clearSelection()

    def get_selected_preprocesos(self):
        """
        Retorna lista de preprocesos seleccionados.

        Returns:
            list: Lista de diccionarios con datos de preprocesos
        """
        selected = []
        for item in self.preprocesos_list.selectedItems():
            preproceso_data = item.data(Qt.ItemDataRole.UserRole)
            if preproceso_data:
                selected.append(preproceso_data)

        return selected

# ==============================================================================
# DIÁLOGO MEJORADO PARA ASIGNAR PREPROCESOS EN EL MENÚ DE PREPROCESOS
# ==============================================================================


class AssignPreprocesosDialog(QDialog):
    """
    Diálogo para asignar preprocesos a fabricaciones desde el menú de Preprocesos.
    """

    def __init__(self, parent_controller, parent=None):
        super().__init__(parent)
        self.controller = parent_controller
        self.setup_ui()
        self.load_fabricaciones()

    def setup_ui(self):
        self.setWindowTitle("Asignar Preprocesos a Fabricaciones")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # Instrucciones
        instructions = QLabel(
            "<b>Gestión de Preprocesos por Fabricación</b><br>"
            "Seleccione una fabricación para ver y modificar sus preprocesos asignados."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Layout horizontal principal
        main_layout = QHBoxLayout()

        # Panel izquierdo - Lista de fabricaciones
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("<b>Fabricaciones disponibles:</b>"))

        self.fabricaciones_list = QListWidget()
        self.fabricaciones_list.itemSelectionChanged.connect(self.on_fabricacion_selected)
        left_panel.addWidget(self.fabricaciones_list)

        # Panel derecho - Preprocesos de la fabricación seleccionada
        right_panel = QVBoxLayout()

        self.fabricacion_info = QLabel("Seleccione una fabricación para ver sus preprocesos")
        self.fabricacion_info.setWordWrap(True)
        self.fabricacion_info.setStyleSheet("font-weight: bold; color: #0066CC;")
        right_panel.addWidget(self.fabricacion_info)

        # Botón para modificar preprocesos
        self.modify_button = QPushButton("Modificar Preprocesos")
        self.modify_button.clicked.connect(self.modify_selected_fabricacion)
        self.modify_button.setEnabled(False)
        right_panel.addWidget(self.modify_button)

        # Lista de preprocesos actuales
        right_panel.addWidget(QLabel("Preprocesos actuales:"))
        self.current_preprocesos_list = QListWidget()
        right_panel.addWidget(self.current_preprocesos_list)

        # Añadir paneles al layout principal
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(300)

        right_widget = QWidget()
        right_widget.setLayout(right_panel)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
        layout.addLayout(main_layout)

        # Botón cerrar
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def load_fabricaciones(self):
        """Carga todas las fabricaciones disponibles."""
        try:
            fabricaciones = self.controller.search_fabricaciones("")
            self.fabricaciones_list.clear()

            if not fabricaciones:
                item = QListWidgetItem("No hay fabricaciones disponibles")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.fabricaciones_list.addItem(item)
            else:
                for fab in fabricaciones:
                    text = f"{fab.codigo}"
                    if fab.descripcion:
                        text += f" - {fab.descripcion}"

                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, fab.id)
                    self.fabricaciones_list.addItem(item)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando fabricaciones: {e}")

    def on_fabricacion_selected(self):
        """Maneja la selección de una fabricación."""
        current_item = self.fabricaciones_list.currentItem()
        if not current_item or not current_item.data(Qt.ItemDataRole.UserRole):
            self.modify_button.setEnabled(False)
            self.fabricacion_info.setText("Seleccione una fabricación para ver sus preprocesos")
            self.current_preprocesos_list.clear()
            return

        fabricacion_id = current_item.data(Qt.ItemDataRole.UserRole)
        fabricacion_text = current_item.text()

        self.fabricacion_info.setText(f"Fabricación seleccionada: {fabricacion_text}")
        self.modify_button.setEnabled(True)

        # Cargar preprocesos actuales
        self.load_current_preprocesos(fabricacion_id)

    def load_current_preprocesos(self, fabricacion_id):
        """Carga los preprocesos actuales de la fabricación."""
        try:
            preprocesos = self.controller.model.db.get_preprocesos_by_fabricacion(fabricacion_id)
            self.current_preprocesos_list.clear()

            if not preprocesos:
                item = QListWidgetItem("Sin preprocesos asignados")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.current_preprocesos_list.addItem(item)
            else:
                for prep_id, nombre, descripcion in preprocesos:
                    text = nombre
                    if descripcion:
                        text += f" - {descripcion}"

                    item = QListWidgetItem(text)
                    self.current_preprocesos_list.addItem(item)

        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"Error cargando preprocesos de la fabricación: {e}")

    def modify_selected_fabricacion(self):
        """Abre el diálogo para modificar preprocesos de la fabricación seleccionada."""
        current_item = self.fabricaciones_list.currentItem()
        if not current_item:
            return

        fabricacion_id = current_item.data(Qt.ItemDataRole.UserRole)

        # Usar el método existente del controlador
        self.controller.show_fabricacion_preprocesos(fabricacion_id)

        # Recargar los preprocesos después de la modificación
        self.load_current_preprocesos(fabricacion_id)


class FabricacionBitacoraDialog(QDialog):
    """
    Diálogo para gestionar el diario de bitácora de una pila de fabricación
    con un calendario interactivo.
    """

    def __init__(self, pila_id, pila_nombre, simulation_results, controller, time_calculator: CalculadorDeTiempos, parent=None):
        super().__init__(parent)
        self.time_calculator = time_calculator  # Guardamos la instancia del calculador
        self.setWindowTitle(f"Diario de Bitácora para Pila: {pila_nombre}")
        self.setMinimumSize(1200, 800)
        self.pila_id = pila_id
        self.simulation_results = simulation_results
        self.controller = controller
        self.logger = logging.getLogger("EvolucionTiemposApp")

        self.pila_start_date = self.simulation_results[0]['Inicio'].date() if self.simulation_results else date.today()
        self.selected_date = date.today()
        self.bitacora_entries = {}

        # --- Layout Principal (Horizontal) ---
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # --- Panel Izquierdo (Calendario e Historial) ---
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self._on_calendar_date_selected)
        left_layout.addWidget(self.calendar)

        left_layout.addWidget(QLabel("<b>Historial de Entradas Guardadas</b>"))
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["Fecha", "Plan", "Realizado"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        left_layout.addWidget(self.history_table)

        # --- Panel Derecho (Detalle del Día y Acciones) ---
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        self.day_detail_label = QLabel("Detalles del Día")
        font = self.day_detail_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.day_detail_label.setFont(font)
        right_layout.addWidget(self.day_detail_label)

        form_layout = QFormLayout()
        self.plan_entry = QTextEdit()
        self.plan_entry.setReadOnly(True)
        self.real_entry = QTextEdit()
        self.real_entry.setPlaceholderText("Describe el trabajo que se ha realizado...")
        self.notes_entry = QTextEdit()
        self.notes_entry.setPlaceholderText("Añade notas, incidencias, etc...")
        form_layout.addRow("<b>Plan Previsto:</b>", self.plan_entry)
        form_layout.addRow("<b>Trabajo Realizado:</b>", self.real_entry)
        form_layout.addRow("<b>Notas:</b>", self.notes_entry)
        right_layout.addLayout(form_layout)

        self.save_entry_button = QPushButton("Guardar Entrada del Día")
        self.save_entry_button.clicked.connect(self._add_diario_entry)
        right_layout.addWidget(self.save_entry_button)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        self._load_and_process_data()


    def _load_and_process_data(self):
        """Carga los datos iniciales, formatea el calendario y selecciona el día actual."""

            # 1. Cargar entradas existentes desde la BD
        _, entries = self.controller.model.get_diario_bitacora(self.pila_id)
        self.bitacora_entries = {}
        for entry_data in entries:
            entry_date_source = entry_data[0]

            if isinstance(entry_date_source, str):
                entry_date = datetime.strptime(entry_date_source, '%Y-%m-%d').date()
            else:
                entry_date = entry_date_source

            self.bitacora_entries[entry_date] = {
                "plan": entry_data[2],
                "realizado": entry_data[3],
                "notas": entry_data[4]
            }

            # 2. Resaltar días de trabajo en el calendario
        self._highlight_work_days()
        self._update_history_table()

            # 3. Seleccionar el primer día de trabajo pendiente
        first_pending_date = self.pila_start_date
        while first_pending_date in self.bitacora_entries:
            if first_pending_date > date.today() + timedelta(days=365):
                break
            first_pending_date = self.time_calculator.find_next_workday(first_pending_date)

        self.calendar.setSelectedDate(first_pending_date)
        self._on_calendar_date_selected()

    def _highlight_work_days(self):
        """Resalta en el calendario los días con trabajo planificado."""
        workday_format = QTextCharFormat()
        workday_format.setBackground(QColor("#E0F0FF"))

        completed_day_format = QTextCharFormat()
        completed_day_format.setBackground(QColor("#D5F5E3"))

        planned_dates = {task['Inicio'].date() for task in self.simulation_results}

        for p_date in planned_dates:
            if p_date in self.bitacora_entries:
                self.calendar.setDateTextFormat(p_date, completed_day_format)
            else:
                self.calendar.setDateTextFormat(p_date, workday_format)

    def _on_calendar_date_selected(self):
        """Actualiza la vista de detalles cuando se selecciona una fecha."""
        from datetime import date
        self.selected_date = self.calendar.selectedDate().toPyDate()
        self.day_detail_label.setText(f"Detalles para el {self.selected_date.strftime('%A, %d de %B de %Y')}")

        planned_work = self._get_planned_work_for_day(self.selected_date)
        self.plan_entry.setPlainText(planned_work)

        if self.selected_date in self.bitacora_entries:
            entry = self.bitacora_entries[self.selected_date]
            self.real_entry.setPlainText(entry['realizado'])
            self.notes_entry.setPlainText(entry['notas'])
            self.save_entry_button.setText("Actualizar Entrada del Día")
            self.real_entry.setReadOnly(False)
            self.notes_entry.setReadOnly(False)
        else:
            self.real_entry.clear()
            self.notes_entry.clear()
            self.save_entry_button.setText("Guardar Entrada del Día")
            if self.selected_date <= date.today():
                self.real_entry.setReadOnly(False)
                self.notes_entry.setReadOnly(False)
                self.save_entry_button.setEnabled(True)
            else:
                self.real_entry.setReadOnly(True)
                self.notes_entry.setReadOnly(True)
                self.save_entry_button.setEnabled(False)

    def _update_history_table(self):
        """Rellena la tabla del historial con las entradas guardadas."""
        self.history_table.setRowCount(0)
        sorted_dates = sorted(self.bitacora_entries.keys())
        self.history_table.setRowCount(len(sorted_dates))
        for i, entry_date in enumerate(sorted_dates):
            entry = self.bitacora_entries[entry_date]
            self.history_table.setItem(i, 0, QTableWidgetItem(entry_date.strftime('%d/%m/%Y')))
            self.history_table.setItem(i, 1, QTableWidgetItem(entry['plan']))
            self.history_table.setItem(i, 2, QTableWidgetItem(entry['realizado']))

    def _get_planned_work_for_day(self, target_date):
        """Genera un resumen del trabajo planificado para una fecha específica."""
        if not self.simulation_results:
            return "No hay resultados de simulación."

        planned_tasks = []
        for task in self.simulation_results:
            if task['Inicio'].date() == target_date:
                start_time = task['Inicio'].strftime('%H:%M')
                end_time = task['Fin'].strftime('%H:%M')
                planned_tasks.append(f"- De {start_time} a {end_time}: {task['Tarea']}")

        if not planned_tasks:
            return "No hay trabajo planificado para esta fecha."

        return "\n".join(sorted(planned_tasks))


    def _add_diario_entry(self):
        """Guarda o actualiza la entrada para la fecha seleccionada."""
        plan = self.plan_entry.toPlainText().strip()
        realizado = self.real_entry.toPlainText().strip()
        notas = self.notes_entry.toPlainText().strip()

        if not realizado:
            self.controller.view.show_message("Campo Requerido",
                                                  "El campo 'Trabajo Realizado' no puede estar vacío.", "warning")
            return

        day_number = (self.selected_date - self.pila_start_date).days + 1

            # --- LÍNEA CORREGIDA ---
            # Pasamos el objeto de fecha directamente, sin convertirlo a texto
        success = self.controller.model.add_diario_entry(self.pila_id, self.selected_date, day_number, plan,
                                                            realizado, notas)
            # --- FIN LÍNEA CORREGIDA ---

        if success:
            self.controller.view.show_message("Éxito", "La entrada del día se ha guardado correctamente.", "info")
            self._load_and_process_data()
        else:
            self.controller.view.show_message("Error", "No se pudo guardar la entrada en la base de datos.",
                                                  "critical")


class GetLoteInstanceParametersDialog(QDialog):
    """
    Diálogo para solicitar los parámetros de una instancia de Lote al añadirla a la Pila.
    """

    def __init__(self, lote_codigo, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Parámetros para Lote: {lote_codigo}")
        self.setModal(True)

        layout = QFormLayout(self)
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        # --- Widgets del formulario ---
        self.identificador_entry = QLineEdit()
        self.identificador_entry.setPlaceholderText("Ej: Pedido Cliente A, Lote de Stock...")

        self.units_spinbox = QSpinBox()
        self.units_spinbox.setRange(1, 99999)
        self.units_spinbox.setValue(1)

        self.deadline_edit = QDateEdit(QDate.currentDate().addDays(14))  # Por defecto, 2 semanas
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setMinimumDate(QDate.currentDate())

        layout.addRow("<b>Identificador Único:</b>", self.identificador_entry)
        layout.addRow("<i>(Para diferenciar este lote dentro del plan)</i>", QLabel())

        layout.addRow("<b>Unidades a Fabricar:</b>", self.units_spinbox)
        layout.addRow("<b>Fecha Límite de Entrega:</b>", self.deadline_edit)

        # --- Botones de Aceptar/Cancelar ---
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def get_data(self):
        """Devuelve un diccionario con los parámetros introducidos por el usuario."""
        return {
            "identificador": self.identificador_entry.text().strip(),
            "unidades": self.units_spinbox.value(),
            "deadline": self.deadline_edit.date().toPyDate()
        }


class GetOptimizationParametersDialog(QDialog):
    """
    Diálogo para solicitar fecha de inicio, fecha de fin y unidades para la optimización.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Parámetros de Optimización")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QFormLayout(self)
        self.start_date_edit = QDateEdit(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        self.end_date_edit = QDateEdit(QDate.currentDate().addDays(30))
        self.end_date_edit.setCalendarPopup(True)
        self.units_spinbox = QSpinBox()
        self.units_spinbox.setRange(1, 99999)
        self.units_spinbox.setValue(1)

        layout.addRow("<b>Unidades a Fabricar:</b>", self.units_spinbox)
        layout.addRow("<b>Fecha de Inicio Deseada:</b>", self.start_date_edit)
        layout.addRow("<b>Fecha Límite de Entrega:</b>", self.end_date_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Optimizar Plan")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_parameters(self):
        return {
            "start_date": self.start_date_edit.date().toPyDate(),
            "end_date": self.end_date_edit.date().toPyDate(),
            "units": self.units_spinbox.value()
        }


class GetUnitsDialog(QDialog):
    """Diálogo simple para solicitar el número de unidades a producir."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Unidades a Producir")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("¿Cuántas unidades deseas producir?"))

        self.units_spinbox = QSpinBox()
        self.units_spinbox.setMinimum(1)
        self.units_spinbox.setMaximum(100000)
        self.units_spinbox.setValue(1)
        layout.addWidget(self.units_spinbox)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_units(self):
        return self.units_spinbox.value()


class SavePilaDialog(QDialog):
    """Diálogo para pedir nombre y descripción al guardar una pila."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Guardar Pila de Producción")
        self.layout = QFormLayout(self)

        self.nombre_edit = QLineEdit()
        self.descripcion_edit = QTextEdit()
        self.descripcion_edit.setFixedHeight(70)

        self.layout.addRow("Nombre de la Pila:", self.nombre_edit)
        self.layout.addRow("Descripción (Opcional):", self.descripcion_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addRow(self.buttons)

    def get_data(self):
        return self.nombre_edit.text().strip(), self.descripcion_edit.toPlainText().strip()


class LoadPilaDialog(QDialog):
    """Diálogo para mostrar y seleccionar pilas guardadas."""
    def __init__(self, pilas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cargar Pila de Producción")
        self.setMinimumSize(500, 400)
        self.layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        for pila in pilas:
            # Support both DTOs and legacy tuples if necessary, or assume DTOs
            if hasattr(pila, 'nombre'):
                p_id = pila.id
                nombre = pila.nombre
                desc = pila.descripcion
            else:
                p_id, nombre, desc = pila
            
            item = QListWidgetItem(f"{nombre}\n  └ {desc or 'Sin descripción'}")
            item.setData(Qt.ItemDataRole.UserRole, p_id) # Guardamos el ID
            self.list_widget.addItem(item)

        self.layout.addWidget(QLabel("Seleccione una pila para cargar o eliminar:"))
        self.layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        self.load_button = QPushButton("Cargar")
        self.delete_button = QPushButton("Eliminar")
        self.cancel_button = QPushButton("Cancelar")

        self.load_button.clicked.connect(self.accept)
        self.delete_button.clicked.connect(self._request_delete)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(button_layout)

        self.selected_id = None
        self.delete_requested = False

    def _request_delete(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione una pila para eliminar.")
            return

        self.selected_id = current_item.data(Qt.ItemDataRole.UserRole)
        self.delete_requested = True
        self.accept()

    def get_selected_id(self):
        # ✅ CORRECCIÓN: Devolver el ID guardado si se solicitó eliminar
        if self.delete_requested:
            return self.selected_id  # ✅ Devuelve el ID guardado en _request_delete

        # Si no es eliminación, obtener el ID del item seleccionado
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None


class ProductsSelectionDialog(QDialog):
    """
    Diálogo para asignar/editar productos de una fabricación existente.
    Permite añadir, quitar y modificar cantidades.
    """

    def __init__(self, fabricacion, all_products, assigned_products_dtos, parent=None):
        super().__init__(parent)
        self.fabricacion = fabricacion # (id, codigo, descripcion)
        self.all_products = all_products
        
        # Mapa de código -> (producto_data, cantidad)
        self.assigned_products = {}
        
        # Indexar all_products por código para acceso rápido
        self.products_map = {p.codigo: p for p in all_products}
        
        # Cargar asignados
        for dto in assigned_products_dtos:
            if dto.producto_codigo in self.products_map:
                self.assigned_products[dto.producto_codigo] = (self.products_map[dto.producto_codigo], dto.cantidad)
            else:
                # Caso raro: producto asignado pero no encontrado en all_products
                pass

        self.setup_ui()
        self.load_initial_data()

    def setup_ui(self):
        self.setWindowTitle(f"Gestionar Productos - {self.fabricacion[1]}")
        self.setModal(True)
        self.resize(850, 600)

        main_layout = QVBoxLayout(self)

        # Información
        info_label = QLabel(f"<b>Fabricación:</b> {self.fabricacion[1]} - {self.fabricacion[2] or 'Sin descripción'}")
        info_layout = QHBoxLayout()
        info_layout.addWidget(info_label)
        main_layout.addLayout(info_layout)
        
        assignment_layout = QHBoxLayout()
        main_layout.addLayout(assignment_layout, 1)

        # === Panel Izquierdo: Productos Disponibles ===
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("<b>Productos Disponibles</b>"))
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Buscar por código o descripción...")
        self.search_entry.textChanged.connect(self._filter_available_list)
        left_panel.addWidget(self.search_entry)
        
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        left_panel.addWidget(self.available_list)

        # === Panel Central: Botones ===
        buttons_panel = QVBoxLayout()
        buttons_panel.addStretch()
        self.add_button = QPushButton(">>")
        self.add_button.setToolTip("Añadir productos seleccionados")
        self.add_button.clicked.connect(self._assign_product)
        
        self.remove_button = QPushButton("<<")
        self.remove_button.setToolTip("Quitar productos seleccionados")
        self.remove_button.clicked.connect(self._unassign_product)
        
        buttons_panel.addWidget(self.add_button)
        buttons_panel.addWidget(self.remove_button)
        buttons_panel.addStretch()

        # === Panel Derecho: Productos Asignados ===
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("<b>Productos en esta Fabricación</b>"))
        
        self.assigned_table = QTableWidget()
        self.assigned_table.setColumnCount(3)
        self.assigned_table.setHorizontalHeaderLabels(["Código", "Descripción", "Cantidad"])
        self.assigned_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.assigned_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        right_panel.addWidget(self.assigned_table)

        assignment_layout.addLayout(left_panel, 2)
        assignment_layout.addLayout(buttons_panel)
        assignment_layout.addLayout(right_panel, 2)

        # === Botones Inferiores ===
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def load_initial_data(self):
        # Cargar disponibles
        self.available_list.clear()
        for product in self.all_products:
             item_text = f"{product.codigo} - {product.descripcion}"
             list_item = QListWidgetItem(item_text)
             list_item.setData(Qt.ItemDataRole.UserRole, product)
             self.available_list.addItem(list_item)
        
        self._filter_available_list()
        self._update_assigned_table()

    def _filter_available_list(self):
        filter_text = self.search_entry.text().lower()
        for i in range(self.available_list.count()):
            item = self.available_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and data.codigo in self.assigned_products:
                item.setHidden(True)
            else:
                item.setHidden(filter_text not in item.text().lower())

    def _assign_product(self):
        selected_items = self.available_list.selectedItems()
        for item in selected_items:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and data.codigo not in self.assigned_products:
                self.assigned_products[data.codigo] = (data, 1) # Default qty 1
        
        self._update_assigned_table()
        self._filter_available_list()

    def _unassign_product(self):
        selected_rows = self.assigned_table.selectionModel().selectedRows()
        if not selected_rows: return

        # Recoger códigos a eliminar para evitar problemas con iteradores
        codigos_to_remove = []
        for index in selected_rows:
            codigo = self.assigned_table.item(index.row(), 0).text()
            codigos_to_remove.append(codigo)
            
        for codigo in codigos_to_remove:
            if codigo in self.assigned_products:
                del self.assigned_products[codigo]

        self._update_assigned_table()
        self._filter_available_list()

    def _update_assigned_table(self):
        self.assigned_table.setRowCount(0)
        # Ordenar por código
        for codigo, (data, cantidad) in sorted(self.assigned_products.items()):
            row = self.assigned_table.rowCount()
            self.assigned_table.insertRow(row)
            
            # Codigo (no editable)
            item_code = QTableWidgetItem(codigo)
            item_code.setFlags(item_code.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.assigned_table.setItem(row, 0, item_code)
            
            # Descripcion (no editable)
            item_desc = QTableWidgetItem(data.descripcion)
            item_desc.setFlags(item_desc.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.assigned_table.setItem(row, 1, item_desc)
            
            # Cantidad (SpinBox)
            qty_spin = QSpinBox()
            qty_spin.setRange(1, 999999)
            qty_spin.setValue(cantidad)
            qty_spin.valueChanged.connect(lambda val, c=codigo: self._on_qty_changed(c, val))
            self.assigned_table.setCellWidget(row, 2, qty_spin)
            
    def _on_qty_changed(self, codigo, val):
        if codigo in self.assigned_products:
            data, _ = self.assigned_products[codigo]
            self.assigned_products[codigo] = (data, val)

    def get_products_data(self):
        """
        Retorna la lista de productos configurada.
        Returns:
            list: Lista de tuplas (producto_codigo, cantidad)
        """
        return [(code, qty) for code, (data, qty) in self.assigned_products.items()]
