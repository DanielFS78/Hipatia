# -*- coding: utf-8 -*-
"""
Nombre del Módulo: navigation_controller.py
Descripción: Gestiona la navegación entre las diferentes páginas de la aplicación, 
             controlando la carga de datos específicos y el flujo de transiciones.
"""
from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING, List, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from core.interfaces.controller_interface import IController
from core.utils.ui_scaler import UIScaler

from controllers.ui_class_loader import ui_class

if TYPE_CHECKING:
    from core.services.product_service import ProductService
    from controllers.app_controller import AppController
    from core.interfaces.view_interface import IView


class NavigationController(IController):
    """
    Controlador dedicado a la gestión de navegación.
    
    Responsable de orquestar el cambio de vista entre los diferentes widgets funcionales, 
    asegurando que los datos necesarios se refresquen al entrar en cada sección.
    """
    
    # Signals
    page_changed = pyqtSignal(str)  # nombre de la página
    navigation_blocked = pyqtSignal(str)  # razón del bloqueo
    
    def __init__(self, app: AppController, view: IView, product_service: ProductService, logger: logging.Logger) -> None:
        """
        Inicializa el controlador de navegación.

        Args:
            app: Referencia al controlador principal de la aplicación.
            view: Interfaz de la vista para gestionar el cambio de páginas.
            product_service: Servicio de productos para carga de datos durante la navegación.
            logger: Instancia para el registro de eventos de navegación.
        """
        super().__init__()
        self.app: AppController = app
        self.view: IView = view
        self.product_service: ProductService = product_service
        self.logger: logging.Logger = logger
        
    def initialize(self) -> None:
        """
        Inicializa el controlador y establece las conexiones iniciales.
        """
        self.connect_signals()
        self.logger.debug("NavigationController inicializado.")

    def cleanup(self) -> None:
        """Limpieza de recursos del controlador."""
        try:
            self.disconnect()
        except Exception:
            pass # Si no hay señales conectadas explícitamente, ignorar
        self.logger.debug("NavigationController limpiado.")

    def connect_signals(self) -> None:
        """Conecta las señales de los botones de navegación."""
        # Las señales de navegación se conectan desde la vista o app_controller
        pass
        
    def on_nav_button_clicked(self, name: str) -> None:
        """
        Maneja el clic en botones de navegación.
        
        Args:
            name: Nombre de la página destino
        """
        self.logger.info(f"Botón de navegación '{name}' presionado. Cambiando de página.")
        try:
            self._perform_navigation(name)
        except Exception as e:
            self.handle_error(e, f"Navegación a {name}")
        
    def navigate_to(self, page_name: str) -> bool:
        """
        Navega a una página específica.
        
        Args:
            page_name: Nombre de la página
            
        Returns:
            True si la navegación fue exitosa
        """
        try:
            self._perform_navigation(page_name)
            return True
        except Exception as e:
            self.handle_error(e, f"Navegando a {page_name}")
            return False

    def _perform_navigation(self, name: str) -> None:
        """
        Lógica interna de navegación. Lanza excepciones en caso de error.
        
        Args:
            name: Nombre de la página
        """
        self.view.switch_page(name)
        
        # --- Aplicar escalado si es una página densa e iterando sobre la principal ---
        # Definimos 'calculate' (Simulación) y 'gestion_datos' como páginas que requieren alto espacio.
        DENSE_PAGES = {"calculate", "gestion_datos", "definir_lote", "historial", "preprocesos", "reportes"}
        if name in DENSE_PAGES:
            try:
                # Obtenemos el widget principal (MainView hereda de QMainWindow / QWidget)
                main_widget = self.view
                if hasattr(main_widget, 'stacked_widget'):
                    current_height = UIScaler.get_current_screen_height(main_widget)
                    # Si la altura es menor que el estándar (1080p), aplicamos el reajuste
                    if current_height < UIScaler.BASE_HEIGHT:
                        factor = UIScaler.calculate_scale_factor(current_height)
                        qss = UIScaler.generate_dynamic_qss(factor)
                        
                        # Inyectar el CSS de forma local para forzar recalculo en la subvista o global en la app
                        from typing import cast
                        from PyQt6.QtWidgets import QApplication
                        app = cast(QApplication | None, QApplication.instance())
                        if app is not None and app.styleSheet() != qss:
                            self.logger.info(f"Aplicando auto-escala {factor} preventivamente por pantalla '{name}'. Height: {current_height}")
                            app.setStyleSheet(qss)
                            
                        # Si pudiéramos llamar a 'recalcular' de la vista, lo haríamos,
                        # pero por ahora el cambio de styleSheet a nivel QApplication forzará el update() general.
            except Exception as e:
                self.logger.error(f"Error aplicando Auto-Ajuste en NavigationController: {e}")

        # Cargar datos específicos según la página
        if name == "settings":
            if self.app.hardware_controller:
                self.app.hardware_controller.load_hardware_settings()
            self.app.load_schedule_settings()
        elif name == "dashboard":
            if self.app.ui_controller:
                self.app.ui_controller.update_dashboard_view()
        elif name == "calculate":
            calc_page = self.view.pages.get("calculate")
            # Usamos getattr/hasattr de forma segura con tipado
            if calc_page and hasattr(calc_page, "planning_session"):
                setattr(calc_page, "planning_session", [])
                
                # Usar QTimer para diferir la actualización de la UI
                CalculateTimesWidget = ui_class("ui.widgets.calculate_times_widget", "CalculateTimesWidget")
                if isinstance(calc_page, CalculateTimesWidget):
                    QTimer.singleShot(0, lambda: self.safe_update_calculate_page(calc_page))
        elif name == "historial":
            if self.app.historial_controller:
                self.app.historial_controller.update_view()
        elif name == "definir_lote":
            DefinirLoteWidget = ui_class("ui.widgets.lotes_widget", "DefinirLoteWidget")
            lote_page = self.view.pages.get("definir_lote")
            if isinstance(lote_page, DefinirLoteWidget):
                lote_page.clear_form()
                pila = getattr(self.app, "pila_controller", None)
                if pila is not None:
                    ps = getattr(lote_page, "product_search", None)
                    fs = getattr(lote_page, "fab_search", None)
                    if ps is not None and hasattr(ps, "text"):
                        pila._on_lote_def_product_search_changed(ps.text())
                    if fs is not None and hasattr(fs, "text"):
                        pila._on_lote_def_fab_search_changed(fs.text())
        elif name == "preprocesos":
            if self.app.preproceso_controller:
                self.app.preproceso_controller.load_preprocesos_data()
        elif name == "gestion_datos":
            if self.app.ui_controller:
                self.app.ui_controller.update_workers_view()
                self.app.ui_controller.update_machines_view()
            if self.app.lote_controller:
                self.app.lote_controller.update_lotes_view()
            
            GestionDatosWidget = ui_class("ui.widgets.gestion_datos_widget", "GestionDatosWidget")
            gestion_datos = self.view.pages.get("gestion_datos")
            if isinstance(gestion_datos, GestionDatosWidget):
                prod_tab = gestion_datos.productos_tab
                from PyQt6.QtWidgets import QLineEdit
                if prod_tab and hasattr(prod_tab, 'search_entry') and isinstance(prod_tab.search_entry, QLineEdit):
                    prod_tab.search_entry.textChanged.emit("")
                
                fab_tab = gestion_datos.fabricaciones_tab
                if fab_tab and self.app.fabricacion_controller:
                    self.app.fabricacion_controller.refresh_fabricaciones_list()
                
        self.page_changed.emit(name)
        
    def safe_update_calculate_page(self, calc_page: Any) -> None:
        """
        Actualiza la página de cálculo de forma segura, con manejo de errores.
        Este método se llama diferido para dar tiempo a Qt a estabilizar los widgets.
        
        Args:
            calc_page: Widget de la página de cálculo
        """
        try:
            if self.app.calculation_controller:
                self.app.calculation_controller.update_calculate_page_lists(calc_page)
        except Exception as e:
            self.handle_error(e, "Actualización diferida cálculo")
        
    def on_go_home_and_reset_calc(self) -> None:
        """Limpia la simulación y vuelve a la pantalla de inicio."""
        try:
            if self.app.simulation_controller:
                self.app.simulation_controller.clear_simulation_state()
            self.navigate_to("home")
        except Exception as e:
            self.handle_error(e, "Resetear cálculo y volver a home")
        
    def update_page_permissions(self, role: str) -> None:
        """
        Actualiza los permisos de acceso a páginas según el rol del usuario.
        
        Args:
            role: Rol del usuario actual
        """
        # Esta funcionalidad se puede implementar más adelante
        pass

