# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`product_details_dialog`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Any

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget
from ui.widgets.product import ProductMaterialsWidget, ProductIterationsWidget

if TYPE_CHECKING:
    from controllers.app_controller import AppController

class ProductDetailsDialog(QDialog):
    """
    Diálogo rediseñado que utiliza sub-widgets para gestionar Componentes e Iteraciones.
    """
    def __init__(self, product_code: str, controller: Any, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.product_code = product_code
        self.controller = controller
        self.logger = logging.getLogger("EvolucionTiemposApp.ProductDetailsDialog")

        # Obtener descripción para el título
        try:
            details = self.controller.product_facade.get_product_details(self.product_code)
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

        # 1. Pestaña de Componentes
        self.materials_tab = ProductMaterialsWidget(
            self.product_code, 
            self.controller, 
            self.parentWidget() # MainView
        )
        self.tab_widget.addTab(self.materials_tab, "Componentes (Lista de Materiales)")

        # 2. Pestaña de Iteraciones
        self.iterations_tab = ProductIterationsWidget(
            self.product_code, 
            self.controller, 
            self.parentWidget() # MainView
        )
        self.tab_widget.addTab(self.iterations_tab, "Historial de Iteraciones")

    def load_all_data(self) -> None:
        """Carga los datos en ambos sub-widgets."""
        self.materials_tab.load_data()
        self.iterations_tab.load_data()



