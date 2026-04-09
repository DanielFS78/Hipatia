# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`materials_widget`): lista de materiales de un producto.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Any, cast

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QInputDialog,
    QFileDialog,
)
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from controllers.product_controller_v2 import ProductController


class ProductMaterialsWidget(QWidget):
    """
    Gestión de la lista de materiales (componentes) de un producto.

    Usa ``ProductController`` para servicios y comandos; ``view`` es la ventana principal
    para ``show_message`` / ``show_confirmation_dialog`` (protocolo IView).
    """

    def __init__(
        self,
        product_code: str,
        product_controller: "ProductController",
        view: Any,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.product_code = product_code
        self.product_controller = product_controller
        self.view = view
        self.logger = logging.getLogger("EvolucionTiemposApp.ProductMaterials")

        self._setup_ui()
        self.load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Componentes asociados a este producto:</b>"))

        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(2)
        self.materials_table.setHorizontalHeaderLabels(["Código", "Descripción"])
        header = self.materials_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
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

    def load_data(self) -> None:
        """Carga la lista de materiales del producto en la tabla."""
        self.materials_table.setRowCount(0)
        try:
            materials = self.product_controller.material_service.get_materials_for_product(
                self.product_code
            )
            for mat in materials:
                row_pos = self.materials_table.rowCount()
                self.materials_table.insertRow(row_pos)
                item_code = QTableWidgetItem(mat.codigo_componente)
                item_code.setData(Qt.ItemDataRole.UserRole, mat.id)
                self.materials_table.setItem(row_pos, 0, item_code)
                self.materials_table.setItem(row_pos, 1, QTableWidgetItem(mat.descripcion_componente))
        except Exception as e:
            self.logger.error(f"Error cargando materiales para {self.product_code}: {e}")

    def _on_add_material(self) -> None:
        codigo, ok1 = QInputDialog.getText(self, "Añadir Componente", "Código del Componente:")
        if not (ok1 and codigo.strip()):
            return
        descripcion, ok2 = QInputDialog.getText(self, "Añadir Componente", "Descripción:")
        if not (ok2 and descripcion.strip()):
            return

        if self.product_controller.handle_add_material_to_product(
            self.product_code, codigo, descripcion
        ):
            self.load_data()

    def _on_edit_material(self) -> None:
        selected_items = self.materials_table.selectedItems()
        if not selected_items:
            self.view.show_message("Atención", "Debe seleccionar un componente para editar.", "warning")
            return
        row = selected_items[0].row()
        item_cod = self.materials_table.item(row, 0)
        item_desc = self.materials_table.item(row, 1)
        if not item_cod or not item_desc:
            return

        material_id = item_cod.data(Qt.ItemDataRole.UserRole)
        current_codigo = item_cod.text()
        current_desc = item_desc.text()

        nuevo_codigo, ok1 = QInputDialog.getText(
            self, "Editar Componente", "Código:", text=current_codigo
        )
        if not (ok1 and nuevo_codigo.strip()):
            return
        nueva_desc, ok2 = QInputDialog.getText(
            self, "Editar Componente", "Descripción:", text=current_desc
        )
        if not (ok2 and nueva_desc.strip()):
            return

        if self.product_controller.handle_update_material(material_id, nuevo_codigo, nueva_desc):
            self.load_data()

    def _on_delete_material(self) -> None:
        selected_items = self.materials_table.selectedItems()
        if not selected_items:
            self.view.show_message("Atención", "Debe seleccionar un componente para eliminar.", "warning")
            return
        row = selected_items[0].row()
        item_cod = self.materials_table.item(row, 0)
        if not item_cod:
            return
        material_id = item_cod.data(Qt.ItemDataRole.UserRole)
        codigo = item_cod.text()

        if self.view.show_confirmation_dialog(
            "Confirmar",
            f"¿Seguro que desea eliminar el componente '{codigo}' de este producto?",
        ):
            if self.product_controller.handle_unlink_material_from_product(
                self.product_code, material_id
            ):
                self.load_data()

    def _on_import_materials_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Archivo Excel", "", "Archivos de Excel (*.xlsx *.xls)"
        )
        if not file_path:
            return
        if self.product_controller.handle_import_materials_to_product(self.product_code, file_path):
            self.load_data()
