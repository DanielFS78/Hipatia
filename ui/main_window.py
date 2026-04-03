# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`main_window`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

import logging
import sys
import os
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QHBoxLayout, QFrame, QVBoxLayout,
    QLabel, QPushButton, QMenu, QMessageBox, QApplication
)

from ui.widgets import (
    HomeWidget, DashboardWidget, DefinirLoteWidget, CalculateTimesWidget,
    PreprocesosWidget, GestionDatosWidget, ReportesWidget,
    HistorialWidget, SettingsWidget, HelpWidget
)
from ui.widgets.main_nav_panel import MainNavPanel
from ui.widgets.main_header import MainHeader

from core.interfaces.view_interface import IView
from core.utils.helpers import resource_path

class MainView(QMainWindow, IView):
    """Vista principal de la aplicación (la ventana)."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Inicializa la ventana principal y sus componentes de UI."""
        super().__init__(parent)
        self.setWindowTitle("Evolucion Tiempos App")
        self.setGeometry(100, 100, 1600, 900)
        self.controller: Optional[Any] = None
        self._pages: Dict[str, Any] = {}
        self.current_page_name = "home"

    def init_ui(self) -> None:
        """Inicializa todos los componentes de la interfaz."""
        self.setWindowTitle("Calculadora de Tiempos de Fabricación - v1.4.1")
        self.setGeometry(100, 100, 1400, 800)
        self.setWindowIcon(QIcon("resources/icon.ico"))
        
        self.stacked_widget = QStackedWidget()

        # 1. Crear widgets de página
        self._init_pages()

        # 2. Construir layout principal usando componentes extraídos
        self._create_main_layout()
        
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage("Listo")
        
        self.switch_page("home")

    def _init_pages(self) -> None:
        """Instancia y registra todas las páginas de la aplicación."""
        widget_classes = {
            "home": HomeWidget,
            "dashboard": DashboardWidget,
            "definir_lote": DefinirLoteWidget,
            "calculate": CalculateTimesWidget,
            "preprocesos": PreprocesosWidget,
            "gestion_datos": GestionDatosWidget,
            "reportes": ReportesWidget,
            "historial": HistorialWidget,
            "settings": SettingsWidget,
            "help": HelpWidget
        }

        for name, WidgetClass in widget_classes.items():
            try:
                if name in ["home", "help"]:
                    instance = WidgetClass()
                else:
                    instance = WidgetClass(self.controller if hasattr(self, 'controller') else None)

                instance.setParent(self.stacked_widget)
                self._pages[name] = instance
                setattr(self, f"{name}_widget", instance)
                self.stacked_widget.addWidget(instance)
                logging.info(f"Widget '{name}' inicializado correctamente.")

            except Exception as e:
                logging.error(f"Error creando widget {name}: {e}", exc_info=True)
                fallback = QWidget()
                fallback.setParent(self.stacked_widget)
                self._pages[name] = fallback
                self.stacked_widget.addWidget(fallback)

    def set_controller(self, controller: Any) -> None:
        """Asigna el controlador a esta vista y a sus widgets hijos."""
        self.controller = controller
        for name, widget in self._pages.items():
            try:
                if hasattr(widget, "set_controller"):
                    widget.set_controller(controller)
                elif hasattr(widget, "controller"):
                    widget.controller = controller

                if name == "gestion_datos":
                    self._assign_controller_to_gestion_tabs(widget, controller)
            except Exception as e:
                logging.warning(f"Error set_controller para widget '{name}': {e}")

    def _assign_controller_to_gestion_tabs(self, widget: Any, controller: Any) -> None:
        """Asigna el controlador a las pestañas internas de Gestión de Datos."""
        try:
            tabs = ["productos_tab", "fabricaciones_tab", "maquinas_tab", "trabajadores_tab"]
            for tab_name in tabs:
                tab = getattr(widget, tab_name, None)
                if tab:
                    if hasattr(tab, 'set_controller'):
                        tab.set_controller(controller)
                    elif hasattr(tab, 'controller'):
                        tab.controller = controller
        except Exception as e:
            logging.warning(f"Error asignando controller a sub-widgets de gestion_datos: {e}")

    def _create_main_layout(self) -> None:
        """Configura el layout principal con NavPanel, Header y StackedWidget."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Panel de Navegación
        self.nav_panel = MainNavPanel(self)
        self.nav_panel.page_requested.connect(self._on_nav_requested)
        main_layout.addWidget(self.nav_panel)
        
        # Panel Derecho (Header + Contenido)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        self.header = MainHeader(self)
        self.header.auto_adjust_requested.connect(self._forzar_auto_ajuste)
        
        right_layout.addWidget(self.header)
        right_layout.addWidget(self.stacked_widget, 1)

        main_layout.addWidget(right_panel, 1)

    def _on_nav_requested(self, page_name: str) -> None:
        """Interceder en la solicitud de cambio de página."""
        if hasattr(self, 'controller') and self.controller:
            self.controller.on_nav_button_clicked(page_name)
        else:
            self.switch_page(page_name)

    def switch_page(self, page_name: str) -> None:
        """Cambia la página visible en el widget apilado."""
        if page_name in self._pages:
            self.stacked_widget.setCurrentWidget(self._pages[page_name])
            self.nav_panel.update_active_button(page_name)
            self.current_page_name = page_name

    def get_page(self, name: str) -> Any:
        """Obtiene una página específica por nombre."""
        return self._pages.get(name)

    def get_products_tab(self) -> Any:
        """Retorna el widget de gestión de productos."""
        gestion = self.get_page("gestion_datos")
        return getattr(gestion, "productos_tab", None) if gestion else None

    def get_fabrications_tab(self) -> Any:
        """Retorna el widget de gestión de fabricaciones."""
        gestion = self.get_page("gestion_datos")
        return getattr(gestion, "fabricaciones_tab", None) if gestion else None

    @property
    def pages(self) -> Dict[str, Any]:
        """Interfaz de compatibilidad para el reporte de páginas."""
        return self._pages

    @property
    def buttons(self) -> Dict[str, QPushButton]:
        """Compatibilidad legacy: expone los botones del panel de navegación."""
        nav_panel = getattr(self, "nav_panel", None)
        if nav_panel is None:
            return {}
        return getattr(nav_panel, "buttons", {})

    def _forzar_auto_ajuste(self) -> None:
        """Fuerza un recalculo dinámico del factor de escala y repinta."""
        from core.utils.ui_scaler import UIScaler
        current_height = UIScaler.get_current_screen_height(self)
        factor = UIScaler.calculate_scale_factor(current_height)
        qss = UIScaler.generate_dynamic_qss(factor)
        
        from typing import cast
        app = cast(QApplication | None, QApplication.instance())
        if app is not None:
            app.setStyleSheet(qss)
            
        for page in self._pages.values():
            if hasattr(page, 'updateGeometry'):
                page.updateGeometry()
            if hasattr(page, 'adjustSize'):
                page.adjustSize()

        # Bajo pytest/CI evitamos processEvents() para no disparar timeouts en suites largas.
        if not os.getenv("PYTEST_CURRENT_TEST"):
            QApplication.processEvents()
        self.update()
        self.show_message("Auto-Ajuste", f"Interfaz escalada al {int(factor*100)}% correctamente.", "info")

    def show_message(self, title: str, message: str, level: str = "info") -> None:
        """Muestra un diálogo de mensaje al usuario."""
        logger = logging.getLogger("EvolucionTiemposApp")
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage(message, 5000)

        # En tests, abrir QMessageBox real puede bloquear (modal) si no está mockeado.
        # Respetamos el test que hace monkeypatch de QMessageBox.* verificando el call.
        is_test_run = os.getenv("PYTEST_CURRENT_TEST") is not None
        if level == "info":
            logger.info(f"Mensaje INFO: {message}")
            if is_test_run and not hasattr(QMessageBox.information, "assert_called"):
                return
            QMessageBox.information(self, title, message)
        elif level == "warning":
            logger.warning(f"Mensaje WARN: {message}")
            if is_test_run and not hasattr(QMessageBox.warning, "assert_called"):
                return
            QMessageBox.warning(self, title, message)
        elif level == "critical":
            logger.error(f"Mensaje CRIT: {message}")
            if is_test_run and not hasattr(QMessageBox.critical, "assert_called"):
                return
            QMessageBox.critical(self, title, message)

    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """Muestra un diálogo de confirmación (Sí/No)."""
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def run_simulation_and_display(self, results: Any, audit: Any, units: int, schedule: Any) -> tuple[Any, Any]:
        """Legacy helper para mostrar resultados de simulación."""
        self.display_simulation_results(results, audit)
        return results, audit

    def display_simulation_results(self, results: Any, audit: Any) -> None:
        """Envía resultados al widget de cálculo."""
        calc_page = self.get_page("calculate")
        if calc_page is not None and hasattr(calc_page, "display_simulation_results"):
            calc_page.display_simulation_results(results, audit)

    def closeEvent(self, event: Any) -> None:
        """Maneja el cierre de la aplicación con backup automático."""
        # Bajo pytest/CI, `qtbot` puede cerrar el widget al terminar cada test.
        # Si no hay mocking del diálogo, evitamos QMesageBox modal para no bloquear.
        is_test_run = os.getenv("PYTEST_CURRENT_TEST") is not None
        if is_test_run and not hasattr(self.show_confirmation_dialog, "assert_called"):
            event.accept()
            return

        if self.show_confirmation_dialog("Cerrar Aplicación", "¿Desea cerrar y realizar backup?"):
            if self.controller:
                try:
                    self.controller.backup_controller.create_automatic_backup()
                except Exception as e:
                    logging.error(f"Error backup: {e}")
            event.accept()
        else:
            event.ignore()

