# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`gestion_datos_widget`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from .base import *
from .products_widget import ProductsWidget
from .fabrications_widget import FabricationsWidget
from .machines_widget import MachinesWidget
from .workers_widget import WorkersWidget
from .lotes_widget import LotesWidget
from typing import Any

class GestionDatosWidget(QWidget):
    """
    Widget unificado que contiene pestañas para gestionar los datos
    principales de la aplicación.
    """
    
    # Attributes for strict mocks
    controller: Any = None
    tab_widget: QTabWidget | None = None
    productos_tab: QWidget | None = None
    fabricaciones_tab: QWidget | None = None
    maquinas_tab: QWidget | None = None
    trabajadores_tab: QWidget | None = None
    lotes_tab: QWidget | None = None

    def __init__(self, controller: Any = None) -> None:
        super().__init__()
        self.controller = controller
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(20, 20, 20, 20)
        title_label = QLabel("Gestión de Datos Centralizada")
        font = QFont(); font.setPointSize(24); font.setBold(True); title_label.setFont(font)
        main_layout.addWidget(title_label); main_layout.addSpacing(10)
        self.tab_widget = QTabWidget(); main_layout.addWidget(self.tab_widget)

        self.productos_tab = None; self.fabricaciones_tab = None
        self.maquinas_tab = None; self.trabajadores_tab = None; self.lotes_tab = None
        self._create_tabs()

    def _create_tabs(self) -> None:
        try:
            if self.controller:
                self.productos_tab = ProductsWidget(self.controller)
                self.fabricaciones_tab = FabricationsWidget(self.controller)
                self.maquinas_tab = MachinesWidget(self.controller)
                self.trabajadores_tab = WorkersWidget(self.controller)
                self.lotes_tab = LotesWidget(self.controller)
            else:
                self.productos_tab = QWidget(); self.fabricaciones_tab = QWidget()
                self.maquinas_tab = QWidget(); self.trabajadores_tab = QWidget(); self.lotes_tab = QWidget()
            if self.tab_widget is not None:
                if self.productos_tab is not None: self.tab_widget.addTab(self.productos_tab, "Productos")
                if self.fabricaciones_tab is not None: self.tab_widget.addTab(self.fabricaciones_tab, "Fabricaciones")
                if self.maquinas_tab is not None: self.tab_widget.addTab(self.maquinas_tab, "Máquinas")
                if self.trabajadores_tab is not None: self.tab_widget.addTab(self.trabajadores_tab, "Trabajadores")
                if self.lotes_tab is not None: self.tab_widget.addTab(self.lotes_tab, "Lotes")
        except Exception as e:
            logging.error(f"Error creando pestañas en GestionDatosWidget: {e}")

    def set_controller(self, controller: Any) -> None:
        self.controller = controller
        if self.productos_tab and not hasattr(self.productos_tab, 'search_entry'):
            if self.tab_widget is not None: self.tab_widget.clear()
            self._create_tabs()
        else:
            for w in [self.productos_tab, self.fabricaciones_tab, self.lotes_tab, self.maquinas_tab, self.trabajadores_tab]:
                if w and hasattr(w, 'set_controller'): w.set_controller(controller)
                elif w and hasattr(w, 'controller'): w.controller = controller
