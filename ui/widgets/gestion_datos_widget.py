# -*- coding: utf-8 -*-
from .base import *
from .products_widget import ProductsWidget
from .fabrications_widget import FabricationsWidget
from .machines_widget import MachinesWidget
from .workers_widget import WorkersWidget
from .lotes_widget import LotesWidget

class GestionDatosWidget(QWidget):
    """
    Widget unificado que contiene pestañas para gestionar los datos
    principales de la aplicación.
    """

    def __init__(self, controller=None):
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

    def _create_tabs(self):
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

            self.tab_widget.addTab(self.productos_tab, "Productos")
            self.tab_widget.addTab(self.fabricaciones_tab, "Fabricaciones")
            self.tab_widget.addTab(self.maquinas_tab, "Máquinas")
            self.tab_widget.addTab(self.trabajadores_tab, "Trabajadores")
            self.tab_widget.addTab(self.lotes_tab, "Lotes")
        except Exception as e:
            logging.error(f"Error creando pestañas en GestionDatosWidget: {e}")

    def set_controller(self, controller):
        self.controller = controller
        if self.productos_tab and not hasattr(self.productos_tab, 'search_entry'):
            self.tab_widget.clear(); self._create_tabs()
        else:
            for w in [self.productos_tab, self.fabricaciones_tab, self.lotes_tab, self.maquinas_tab, self.trabajadores_tab]:
                if w and hasattr(w, 'set_controller'): w.set_controller(controller)
                elif w and hasattr(w, 'controller'): w.controller = controller
