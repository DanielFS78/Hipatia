# -*- coding: utf-8 -*-
"""
Nombre del Módulo: gestion_datos_widget

Descripción: Pestañas unificadas para productos, fabricaciones, máquinas, trabajadores y lotes.
             Cada pestaña resuelve su controlador vía DI.
"""

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

    Las pestañas resuelven controladores de dominio vía DI; no reciben ``AppController``
    desde esta vista ni se mantiene referencia al hub.
    """

    tab_widget: QTabWidget | None = None
    productos_tab: QWidget | None = None
    fabricaciones_tab: QWidget | None = None
    maquinas_tab: QWidget | None = None
    trabajadores_tab: QWidget | None = None
    lotes_tab: QWidget | None = None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        title_label = QLabel("Gestión de Datos Centralizada")
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        main_layout.addWidget(title_label)
        main_layout.addSpacing(10)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.productos_tab = None
        self.fabricaciones_tab = None
        self.maquinas_tab = None
        self.trabajadores_tab = None
        self.lotes_tab = None
        self._create_tabs()

    def _create_tabs(self) -> None:
        try:
            self.productos_tab = ProductsWidget()
            self.fabricaciones_tab = FabricationsWidget()
            self.maquinas_tab = MachinesWidget()
            self.trabajadores_tab = WorkersWidget()
            self.lotes_tab = LotesWidget()
            if self.tab_widget is not None:
                if self.productos_tab is not None:
                    self.tab_widget.addTab(self.productos_tab, "Productos")
                if self.fabricaciones_tab is not None:
                    self.tab_widget.addTab(self.fabricaciones_tab, "Fabricaciones")
                if self.maquinas_tab is not None:
                    self.tab_widget.addTab(self.maquinas_tab, "Máquinas")
                if self.trabajadores_tab is not None:
                    self.tab_widget.addTab(self.trabajadores_tab, "Trabajadores")
                if self.lotes_tab is not None:
                    self.tab_widget.addTab(self.lotes_tab, "Lotes")
        except Exception as e:
            logging.error(f"Error creando pestañas en GestionDatosWidget: {e}")
