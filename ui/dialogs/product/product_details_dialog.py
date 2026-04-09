# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`product_details_dialog`): detalle de producto con pestañas de componentes e iteraciones.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Any

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget
from ui.widgets.product import ProductMaterialsWidget, ProductIterationsWidget

if TYPE_CHECKING:
    from controllers.product_controller_v2 import ProductController


class ProductDetailsDialog(QDialog):
    """
    Diálogo que utiliza sub-widgets para gestionar componentes e iteraciones.

    Recibe ``ProductController`` (no ``AppController``): materiales e iteraciones
    delegan en ese controlador y en la vista principal como padre para diálogos Qt.
    """

    def __init__(
        self,
        product_code: str,
        product_controller: "ProductController",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.product_code = product_code
        self.product_controller = product_controller
        self.logger = logging.getLogger("EvolucionTiemposApp.ProductDetailsDialog")

        try:
            details = self.product_controller.product_facade.get_product_details(self.product_code)
            prod_data = details.producto if details else None
            prod_desc = prod_data.descripcion if prod_data else ""
        except Exception:
            prod_desc = ""

        self.setWindowTitle(f"Detalles de Producto: {self.product_code} - {prod_desc}")
        self.setMinimumSize(1000, 750)

        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        view_parent = self.parentWidget()
        self.materials_tab = ProductMaterialsWidget(
            self.product_code,
            self.product_controller,
            view_parent,
        )
        self.tab_widget.addTab(self.materials_tab, "Componentes (Lista de Materiales)")

        self.iterations_tab = ProductIterationsWidget(
            self.product_code,
            self.product_controller,
            self,
        )
        self.tab_widget.addTab(self.iterations_tab, "Historial de Iteraciones")

    def load_all_data(self) -> None:
        """Carga los datos en ambos sub-widgets."""
        self.materials_tab.load_data()
        self.iterations_tab.load_data()
