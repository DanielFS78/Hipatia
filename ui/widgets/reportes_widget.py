# -*- coding: utf-8 -*-
from .base import *

class ReportesWidget(QWidget):
    """Widget para el nuevo módulo de Generación de Informes."""

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(450)

        search_box = QFrame()
        search_box_layout = QVBoxLayout(search_box)
        search_box.setFrameShape(QFrame.Shape.StyledPanel)
        search_box_layout.addWidget(QLabel("<b>Buscar Producto o Fabricación</b>"))
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Introduzca código o descripción...")
        search_box_layout.addWidget(self.search_entry)
        left_layout.addWidget(search_box)

        results_box = QFrame()
        results_box_layout = QVBoxLayout(results_box)
        results_box.setFrameShape(QFrame.Shape.StyledPanel)
        results_box_layout.addWidget(QLabel("<b>Resultados de la Búsqueda</b>"))
        self.results_list = QListWidget()
        results_box_layout.addWidget(self.results_list)
        left_layout.addWidget(results_box, 1)

        right_panel = QFrame(); right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.right_layout = QVBoxLayout(right_panel)
        self.placeholder_label = QLabel("Seleccione un elemento para ver los informes disponibles.")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.placeholder_label.setWordWrap(True)
        self.right_layout.addWidget(self.placeholder_label)

        self.reports_buttons_container = QWidget()
        self.reports_buttons_layout = QVBoxLayout(self.reports_buttons_container)
        self.reports_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.right_layout.addWidget(self.reports_buttons_container)
        self.reports_buttons_container.setVisible(False)
        self.right_layout.addStretch()

        main_layout.addWidget(left_panel); main_layout.addWidget(right_panel, 1)
