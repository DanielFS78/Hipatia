"""
Interfaz PyQt6 (`products_dialog`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit,
    QListWidget, QAbstractItemView, QListWidgetItem, QPushButton,
    QTableWidget, QHeaderView, QDialogButtonBox, QTableWidgetItem,
    QSpinBox, QWidget
)
from PyQt6.QtCore import Qt
from typing import List, Tuple, Dict, Any, Optional, TYPE_CHECKING
from core.dtos import FabricacionProductoDTO

if TYPE_CHECKING:
    # Assuming models structure
    pass

class ProductsSelectionDialog(QDialog):
    """
    Diálogo para asignar/editar productos de una fabricación existente.
    Permite añadir, quitar y modificar cantidades.
    """

    def __init__(self, fabricacion: Tuple[int, str, Optional[str]], all_products: List[Any], assigned_products_dtos: List[Any], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.fabricacion = fabricacion # (id, codigo, descripcion)
        self.all_products = all_products
        
        # Mapa de código -> (producto_data, cantidad)
        self.assigned_products: Dict[str, Tuple[Any, int]] = {}
        
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

    def setup_ui(self) -> None:
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
        header = self.assigned_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
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

    def load_initial_data(self) -> None:
        # Cargar disponibles
        self.available_list.clear()
        for product in self.all_products:
             item_text = f"{product.codigo} - {product.descripcion}"
             list_item = QListWidgetItem(item_text)
             list_item.setData(Qt.ItemDataRole.UserRole, product)
             self.available_list.addItem(list_item)
        
        self._filter_available_list()
        self._update_assigned_table()

    def _filter_available_list(self) -> None:
        filter_text = self.search_entry.text().lower()
        for i in range(self.available_list.count()):
            item = self.available_list.item(i)
            if not item: continue
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and data.codigo in self.assigned_products:
                item.setHidden(True)
            else:
                item.setHidden(filter_text not in item.text().lower())

    def _assign_product(self) -> None:
        selected_items = self.available_list.selectedItems()
        for item in selected_items:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and data.codigo not in self.assigned_products:
                self.assigned_products[data.codigo] = (data, 1) # Default qty 1
        
        self._update_assigned_table()
        self._filter_available_list()

    def _unassign_product(self) -> None:
        sel_model = self.assigned_table.selectionModel()
        if not sel_model: return
        selected_rows = sel_model.selectedRows()
        if not selected_rows: return
        
        # Recoger códigos a eliminar para evitar problemas con iteradores
        codigos_to_remove = []
        for index in selected_rows:
            item = self.assigned_table.item(index.row(), 0)
            if item:
                codigos_to_remove.append(item.text())
            
        for codigo in codigos_to_remove:
            if codigo in self.assigned_products:
                del self.assigned_products[codigo]

        self._update_assigned_table()
        self._filter_available_list()

    def _update_assigned_table(self) -> None:
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
            
    def _on_qty_changed(self, codigo: str, val: int) -> None:
        if codigo in self.assigned_products:
            data, _ = self.assigned_products[codigo]
            self.assigned_products[codigo] = (data, val)

    def get_products_data(self) -> List[FabricacionProductoDTO]:
        """
        Retorna la lista de productos configurada como DTOs.
        """
        return [
            FabricacionProductoDTO(producto_codigo=code, cantidad=qty) 
            for code, (data, qty) in self.assigned_products.items()
        ]
