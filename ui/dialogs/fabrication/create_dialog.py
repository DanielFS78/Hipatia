# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.fabrication.create_dialog
Descripción: Diálogo o presentador de fabricación: órdenes, preprocesos, productos y persistencia de pilas.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit,
    QTabWidget, QWidget, QDialogButtonBox, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QPushButton,
    QTableWidget, QHeaderView, QAbstractItemView, QTableWidgetItem,
    QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt
from typing import List, Dict, Any, Tuple, Optional

from core.dtos import FabricacionDTO
from ui.dialogs.fabrication.create_presenter import CreateFabricacionPresenter

class CreateFabricacionDialog(QDialog):
    """
    Diálogo para crear fabricaciones: preprocesos, productos con cantidades y validación del código.

    La recogida de datos y la validación se delegan en ``CreateFabricacionPresenter``; al aceptar,
    el resultado se expresa como ``FabricacionDTO``.
    """

    def __init__(self, all_preprocesos: List[Any], all_products: Optional[List[Any]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.presenter = CreateFabricacionPresenter(all_preprocesos, all_products)

        self.setup_ui()
        self.load_initial_data()

    # API legacy (alias de la pestaña de preprocesos; sin capa intermedia)
    @property
    def search_entry(self) -> QLineEdit:
        return self.prep_search_entry

    @property
    def available_list(self) -> QListWidget:
        return self.prep_available_list

    @property
    def assigned_list(self) -> QListWidget:
        return self.prep_assigned_list

    @property
    def add_button(self) -> QPushButton:
        return self.prep_add_button

    @property
    def remove_button(self) -> QPushButton:
        return self.prep_remove_button

    def filter_available_list(self) -> None:
        self._filter_prep_available_list()

    def assign_preproceso(self) -> None:
        self._assign_preproceso()

    def unassign_preproceso(self) -> None:
        self._unassign_preproceso()

    def update_available_list(self) -> None:
        self._filter_prep_available_list()

    def update_assigned_list(self) -> None:
        self._update_prep_assigned_list()

    def setup_ui(self) -> None:
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

    def _setup_preprocesos_tab(self, tab_widget: QWidget) -> None:
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

    def _setup_productos_tab(self, tab_widget: QWidget) -> None:
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
        header = self.prod_assigned_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.prod_assigned_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        right_panel.addWidget(self.prod_assigned_table)

        assignment_layout.addLayout(left_panel, 2)
        assignment_layout.addLayout(buttons_panel)
        assignment_layout.addLayout(right_panel, 2)

        # Conexiones
        self.prod_add_button.clicked.connect(self._assign_product)
        self.prod_remove_button.clicked.connect(self._unassign_product)

    def load_initial_data(self) -> None:
        """Carga los datos iniciales en las listas."""
        self._filter_prep_available_list()
        self._filter_prod_available_list()

    # --- Métodos para PREPROCESOS ---
    def _filter_prep_available_list(self) -> None:
        filter_text = self.prep_search_entry.text()
        filtered = self.presenter.get_filtered_preprocesos(filter_text)
        
        self.prep_available_list.clear()
        for preproceso in filtered:
            item_text = getattr(preproceso, 'nombre', '')
            desc = getattr(preproceso, 'descripcion', '')
            if desc:
                item_text += f" - {desc}"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, preproceso)
            self.prep_available_list.addItem(list_item)

    def _assign_preproceso(self) -> None:
        selected_items = self.prep_available_list.selectedItems()
        preps_to_assign = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        self.presenter.assign_preprocesos(preps_to_assign)
        
        self._update_prep_assigned_list()
        self._filter_prep_available_list()

    def _unassign_preproceso(self) -> None:
        selected_items = self.prep_assigned_list.selectedItems()
        preps_to_unassign = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        self.presenter.unassign_preprocesos(preps_to_unassign)
        
        self._update_prep_assigned_list()
        self._filter_prep_available_list()

    def _update_prep_assigned_list(self) -> None:
        self.prep_assigned_list.clear()
        assigned = self.presenter.get_assigned_preprocesos()
        for preproceso in assigned:
            list_item = QListWidgetItem(getattr(preproceso, 'nombre', ''))
            list_item.setData(Qt.ItemDataRole.UserRole, preproceso)
            self.prep_assigned_list.addItem(list_item)

    # --- Métodos para PRODUCTOS ---
    def _filter_prod_available_list(self) -> None:
        filter_text = self.prod_search_entry.text()
        filtered = self.presenter.get_filtered_products(filter_text)
        
        self.prod_available_list.clear()
        for product in filtered:
            item_text = f"{getattr(product, 'codigo', '')} - {getattr(product, 'descripcion', '')}"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, product)
            self.prod_available_list.addItem(list_item)

    def _assign_product(self) -> None:
        selected_items = self.prod_available_list.selectedItems()
        products_to_assign = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        self.presenter.assign_products(products_to_assign)
        
        self._update_prod_assigned_table()
        self._filter_prod_available_list()

    def _unassign_product(self) -> None:
        sel_model = self.prod_assigned_table.selectionModel()
        if not sel_model: return
        selected_rows = sel_model.selectedRows()
        codes_to_remove = []
        for index in selected_rows:
            item = self.prod_assigned_table.item(index.row(), 0)
            if item:
                codes_to_remove.append(item.text())
            
        self.presenter.unassign_products_by_code(codes_to_remove)
        
        self._update_prod_assigned_table()
        self._filter_prod_available_list()

    def _update_prod_assigned_table(self) -> None:
        self.prod_assigned_table.setRowCount(0)
        assigned = self.presenter.get_assigned_products()
        for data, cantidad in assigned:
            row = self.prod_assigned_table.rowCount()
            codigo = getattr(data, 'codigo', '')
            self.prod_assigned_table.insertRow(row)
            self.prod_assigned_table.setItem(row, 0, QTableWidgetItem(codigo))
            self.prod_assigned_table.setItem(row, 1, QTableWidgetItem(getattr(data, 'descripcion', '')))
            
            # Spinbox para cantidad
            qty_spin = QSpinBox()
            qty_spin.setRange(1, 9999)
            qty_spin.setValue(cantidad)
            qty_spin.valueChanged.connect(lambda val, c=codigo: self._on_qty_changed(c, val))
            self.prod_assigned_table.setCellWidget(row, 2, qty_spin)

    def _on_qty_changed(self, codigo: str, new_value: int) -> None:
        self.presenter.update_product_qty(codigo, new_value)

    # --- Validación y Datos ---
    def validate_and_accept(self) -> None:
        codigo = self.codigo_entry.text()
        valid, error_msg = self.presenter.validate(codigo)
        if not valid:
            QMessageBox.warning(self, "Error de Validación", error_msg)
            return

        self.accept()

    def get_fabricacion_data(self) -> FabricacionDTO:
        """
        Consolida y retorna el estado actual del formulario como un objeto DTO.
        
        Este método delega en el Presenter la creación de los DTOs de productos
        y la cabecera de fabricación, garantizando que los datos estén tipados
        y normalizados para su envío al servicio de dominio.
        """
        return self.presenter.get_fabricacion_data(
            self.codigo_entry.text(),
            self.descripcion_entry.text()
        )
