# -*- coding: utf-8 -*-
"""
Nombre del Módulo: main_nav_panel
Descripcion: Widget lateral de navegación para la ventana principal.
             Gestiona los botones de acceso a las diferentes secciones y el menú de planificación.
"""
import logging
from typing import Dict, Optional, Any

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QPushButton, QLabel, QMenu, QScrollArea
)

class MainNavPanel(QFrame):
    """
    Panel lateral de navegación con botones categorizados y menú de operaciones.
    """
    
    # Señal emitida cuando el usuario solicita cambiar de página
    page_requested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Inicializa el panel de navegación y sus estilos."""
        super().__init__(parent)
        self.buttons: Dict[str, QPushButton] = {}
        self.setFixedWidth(250)
        self._setup_style()
        self._init_ui()

    def _setup_style(self) -> None:
        """Establece la apariencia visual del panel lateral."""
        self.setStyleSheet("""
            QFrame { background-color: #2c3e50; color: white; border: none; }
            QPushButton {
                background-color: #34495e; color: white; border: none;
                text-align: left; padding: 15px 20px; margin: 2px;
                border-radius: 5px; font-size: 14px;
            }
            QPushButton:hover { background-color: #3498db; }
            QPushButton:checked { background-color: #e74c3c; }
            QPushButton[navActive="true"] { background-color: #e74c3c; }
            QPushButton[navActive="true"]:hover { background-color: #c0392b; }
            QLabel {
                color: #bdc3c7; font-weight: bold; font-size: 12px;
                padding: 10px 20px 5px; border: none;
            }
        """)

    def _init_ui(self) -> None:
        """Crea los botones y categorías del panel, dentro de un área con scroll."""
        # Layout raíz del frame (sin márgenes) contiene solo el QScrollArea
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Widget interior con el contenido real de navegación
        inner_widget = QWidget()
        inner_widget.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(inner_widget)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(2)

        # SECCIÓN: Principal
        layout.addWidget(self._create_category_label("Principal"))
        self.btn_home = self._create_nav_button("Inicio", "home")
        self.btn_dashboard = self._create_nav_button("Dashboard", "dashboard")
        layout.addWidget(self.btn_home)
        layout.addWidget(self.btn_dashboard)

        # SECCIÓN: Operaciones
        layout.addWidget(self._create_category_label("Operaciones"))
        
        # Planificación: sin setMenu (evita layout interno del subcontrol de menú que desalinea el texto).
        # Mismo aspecto que el resto de botones; el menú se abre con exec bajo el botón.
        self.btn_planificacion = QPushButton("Planificación")
        self.btn_planificacion.setCheckable(False)
        self.btn_planificacion.setProperty("navActive", False)

        self._planificacion_menu = QMenu(self)
        action_definir_lote = self._planificacion_menu.addAction("Definir Plantilla de Lote")
        action_planificar = self._planificacion_menu.addAction("Planificar Producción (Crear Pila)")

        if action_definir_lote:
            action_definir_lote.triggered.connect(lambda: self.page_requested.emit("definir_lote"))
        if action_planificar:
            action_planificar.triggered.connect(lambda: self.page_requested.emit("calculate"))

        self.btn_planificacion.clicked.connect(self._show_planificacion_menu)
        layout.addWidget(self.btn_planificacion)

        self.btn_preprocesos = self._create_nav_button("Preprocesos", "preprocesos")
        layout.addWidget(self.btn_preprocesos)

        # SECCIÓN: Gestión
        layout.addWidget(self._create_category_label("Gestión"))
        self.btn_gestion = self._create_nav_button("Gestión de Datos", "gestion_datos")
        layout.addWidget(self.btn_gestion)

        # SECCIÓN: Análisis
        layout.addWidget(self._create_category_label("Análisis"))
        self.btn_reportes = self._create_nav_button("Reportes", "reportes")
        self.btn_historial = self._create_nav_button("Historial", "historial")
        layout.addWidget(self.btn_reportes)
        layout.addWidget(self.btn_historial)

        # SECCIÓN: Sistema
        layout.addWidget(self._create_category_label("Sistema"))
        self.btn_settings = self._create_nav_button("Configuración", "settings")
        self.btn_help = self._create_nav_button("Ayuda", "help")
        layout.addWidget(self.btn_settings)
        layout.addWidget(self.btn_help)

        layout.addStretch()

        # Área de scroll: permite acceder a todos los botones en pantallas pequeñas
        scroll = QScrollArea()
        scroll.setWidget(inner_widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { background-color: transparent; border: none; }
            QScrollBar:vertical {
                background: #2c3e50; width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #3d566e; border-radius: 3px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        root_layout.addWidget(scroll)

        # Registro de botones para fácil acceso y actualización de estado
        self.buttons = {
            "home": self.btn_home,
            "dashboard": self.btn_dashboard,
            "preprocesos": self.btn_preprocesos,
            "gestion_datos": self.btn_gestion,
            "reportes": self.btn_reportes,
            "historial": self.btn_historial,
            "settings": self.btn_settings,
            "help": self.btn_help
        }

    def _create_category_label(self, text: str) -> QLabel:
        """Crea una etiqueta de categoría estilizada."""
        label = QLabel(text.upper())
        label.setStyleSheet("color: #95a5a6; font-size: 11px; margin-top: 15px;")
        return label

    def _create_nav_button(self, text: str, page_name: str) -> QPushButton:
        """Crea un botón de navegación que emite una señal al ser pulsado."""
        button = QPushButton(text)
        button.setCheckable(True)
        button.clicked.connect(lambda: self.page_requested.emit(page_name))
        return button

    def _show_planificacion_menu(self) -> None:
        """Abre el menú de planificación bajo el botón (sin acoplar menú al QPushButton)."""
        btn = self.btn_planificacion
        origin = btn.mapToGlobal(btn.rect().bottomLeft())
        self._planificacion_menu.exec(origin)

    @property
    def planificacion_menu(self) -> QMenu:
        """Menú contextual de planificación (tests y depuración)."""
        return self._planificacion_menu

    def update_active_button(self, active_page: str) -> None:
        """
        Actualiza visualmente qué botón aparece marcado como activo.
        
        Args:
            active_page: nombre interno de la página activa.
        """
        for page_name, button in self.buttons.items():
            button.setChecked(page_name == active_page)

        # Planificación no usa setCheckable (menú suelto): estado activo vía propiedad QSS
        is_planificacion = active_page in ["calculate", "definir_lote"]
        self.btn_planificacion.setProperty("navActive", is_planificacion)
        self.btn_planificacion.style().unpolish(self.btn_planificacion)
        self.btn_planificacion.style().polish(self.btn_planificacion)
