# -*- coding: utf-8 -*-
import logging
import sys
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QHBoxLayout, QFrame, QVBoxLayout,
    QLabel, QPushButton, QMenu, QMessageBox, QApplication
)

# Imports from local modules
from ui.widgets import (
    HomeWidget, DashboardWidget, DefinirLoteWidget, CalculateTimesWidget,
    PreprocesosWidget, AddProductWidget, GestionDatosWidget, ReportesWidget,
    HistorialWidget, SettingsWidget, HelpWidget
)

# We might need resource_path if used in init_ui for icons
def resource_path(relative_path):
    """
    Obtiene la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller.
    """
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # En desarrollo, usar el directorio actual
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainView(QMainWindow):
    """Vista principal de la aplicación (la ventana)."""

    def __init__(self, parent=None):
        """Inicializa la ventana principal y sus componentes de UI."""
        super().__init__(parent)
        self.setWindowTitle("Evolucion Tiempos App")
        self.setGeometry(100, 100, 1600, 900)
        self.controller = None
        self.pages = {}
        self.buttons = {}
        self.current_page_name = "home"

    def init_ui(self):
        """Inicializa todos los componentes de la interfaz."""

        # 1. PRIMERO configurar la ventana principal
        self.setWindowTitle("Calculadora de Tiempos de Fabricación - v1.4.1")
        self.setGeometry(100, 100, 1400, 800)
        self.setWindowIcon(QIcon("resources/icon.ico"))
        
        # NOTE: If resource_path is needed for correct icon loading in packaged app:
        # self.setWindowIcon(QIcon(resource_path("resources/icon.ico")))

        # 2. CREAR stacked_widget ANTES de los widgets (CRÍTICO)
        self.stacked_widget = QStackedWidget()

        # 3. Crear widgets de página con el controller ya disponible
        widget_classes = {
            "home": HomeWidget,
            "dashboard": DashboardWidget,
            "definir_lote": DefinirLoteWidget,
            "calculate": CalculateTimesWidget,
            "preprocesos": PreprocesosWidget,
            "add_product": AddProductWidget,
            "gestion_datos": GestionDatosWidget,
            "reportes": ReportesWidget,
            "historial": HistorialWidget,
            "settings": SettingsWidget,
            "help": HelpWidget
        }

        self.pages = {}
        for name, WidgetClass in widget_classes.items():
            try:
                if name in ["home", "help"]:
                    # Widgets que no necesitan controller
                    instance = WidgetClass()
                else:
                    # Widgets que necesitan controller
                    instance = WidgetClass(
                        self.controller if hasattr(self, 'controller') else None
                    )

                # CRÍTICO: Establecer parent DESPUÉS de crear la instancia
                # Esto previene que Qt elimine los widgets prematuramente
                instance.setParent(self.stacked_widget)

                self.pages[name] = instance
                setattr(self, f"{name}_widget", instance)

                # Añadir inmediatamente al stacked_widget
                self.stacked_widget.addWidget(instance)

            except Exception as e:
                logging.error(f"Error creando widget {name}: {e}", exc_info=True)
                # Crear widget vacío como fallback
                fallback = QWidget()
                fallback.setParent(self.stacked_widget)
                self.pages[name] = fallback
                setattr(self, f"{name}_widget", fallback)
                self.stacked_widget.addWidget(fallback)

        logging.info("Widgets de página de MainView inicializados correctamente.")

        # 4. Construir el resto de la interfaz
        self._create_main_layout()
        self.statusBar().showMessage("Listo")
        logging.info("Vista principal (QMainWindow) inicializada con sus componentes.")
        self.switch_page("home")

    def set_controller(self, controller):
        """Asigna el controlador a esta vista y a sus widgets hijos."""
        self.controller = controller

        # Asignar el controller a todos los widgets que lo necesiten
        for name, widget in self.pages.items():
            if hasattr(widget, 'set_controller'):
                widget.set_controller(controller)
            elif hasattr(widget, 'controller'):
                widget.controller = controller

            # Para GestionDatosWidget, también asignar a sus sub-widgets (pestañas)
            if name == "gestion_datos":
                try:
                    for tab_widget in [widget.productos_tab, widget.fabricaciones_tab, widget.maquinas_tab,
                                       widget.trabajadores_tab]:
                        if tab_widget:
                            # Algunos widgets usan 'set_controller', otros asignación directa
                            if hasattr(tab_widget, 'set_controller'):
                                tab_widget.set_controller(controller)
                            elif hasattr(tab_widget, 'controller'):
                                tab_widget.controller = controller
                except AttributeError as e:
                    logging.warning(f"Error asignando controller a sub-widgets de gestion_datos: {e}")

        logging.info("Controller asignado correctamente a MainView y todos sus widgets.")

    def _create_main_layout(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        nav_frame = self._create_nav_panel()
        main_layout.addWidget(nav_frame)

        main_layout.addWidget(self.stacked_widget, 1)

    def _create_nav_panel(self):
        """Crea el panel de navegación lateral con el nuevo menú de Planificación."""
        nav_frame = QFrame()
        nav_frame.setFixedWidth(250)
        nav_frame.setStyleSheet("""
            QFrame { background-color: #2c3e50; color: white; }
            QPushButton {
                background-color: #34495e; color: white; border: none;
                text-align: left; padding: 15px 20px; margin: 2px;
                border-radius: 5px; font-size: 14px;
            }
            QPushButton:hover { background-color: #3498db; }
            QPushButton:checked { background-color: #e74c3c; }
            QPushButton::menu-indicator { image: none; } /* Oculta la flecha del menú */
            QLabel {
                color: #bdc3c7; font-weight: bold; font-size: 12px;
                padding: 10px 20px 5px; border: none;
            }
        """)

        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(2)

        def create_category_label(text):
            label = QLabel(text.upper())
            label.setStyleSheet("color: #95a5a6; font-size: 11px; margin-top: 15px;")
            return label

        def create_nav_button(text, page_name):
            button = QPushButton(text)
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, name=page_name: self._on_nav_button_clicked(name))
            return button

        # Sección Principal
        nav_layout.addWidget(create_category_label("Principal"))
        home_btn = create_nav_button("Inicio", "home")
        dashboard_btn = create_nav_button("Dashboard", "dashboard")
        nav_layout.addWidget(home_btn)
        nav_layout.addWidget(dashboard_btn)


        nav_layout.addWidget(create_category_label("Operaciones"))

        # Botón principal que abrirá el menú
        planificacion_btn = QPushButton("Planificación")
        planificacion_btn.setCheckable(True)
        # Estilo explícito para asegurar alineación correcta del texto
        planificacion_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 15px 20px;
                padding-right: 20px;
            }
        """)

        # Creamos el menú desplegable
        planificacion_menu = QMenu(self)
        action_definir_lote = planificacion_menu.addAction("Definir Plantilla de Lote")
        action_planificar = planificacion_menu.addAction("Planificar Producción (Crear Pila)")

        # Conectamos las acciones del menú
        action_definir_lote.triggered.connect(lambda: self._on_nav_button_clicked("definir_lote"))
        action_planificar.triggered.connect(lambda: self._on_nav_button_clicked("calculate"))

        planificacion_btn.setMenu(planificacion_menu)
        nav_layout.addWidget(planificacion_btn)

        preprocesos_btn = create_nav_button("Preprocesos", "preprocesos")
        nav_layout.addWidget(preprocesos_btn)

        # --- RESTO DE SECCIONES (SIN CAMBIOS) ---
        nav_layout.addWidget(create_category_label("Gestión"))
        add_prod_btn = create_nav_button("Añadir Producto", "add_product")
        gestion_btn = create_nav_button("Gestión de Datos", "gestion_datos")
        nav_layout.addWidget(add_prod_btn)
        nav_layout.addWidget(gestion_btn)

        nav_layout.addWidget(create_category_label("Análisis"))
        reports_btn = create_nav_button("Reportes", "reportes")
        history_btn = create_nav_button("Historial", "historial")
        nav_layout.addWidget(reports_btn)
        nav_layout.addWidget(history_btn)

        nav_layout.addWidget(create_category_label("Sistema"))
        settings_btn = create_nav_button("Configuración", "settings")
        help_btn = create_nav_button("Ayuda", "help")
        nav_layout.addWidget(settings_btn)
        nav_layout.addWidget(help_btn)

        nav_layout.addStretch()

        self.buttons = {
            "home": home_btn, "dashboard": dashboard_btn,
            "planificacion_main": planificacion_btn,
            "preprocesos": preprocesos_btn, "add_product": add_prod_btn,
            "gestion_datos": gestion_btn, "reportes": reports_btn,
            "historial": history_btn, "settings": settings_btn, "help": help_btn
        }
        return nav_frame

    def _on_nav_button_clicked(self, page_name):
        """Maneja el clic en botones de navegación desde la vista."""
        if hasattr(self, 'controller') and self.controller:
            self.controller._on_nav_button_clicked(page_name)
        else:
            self.switch_page(page_name)

    def switch_page(self, page_name):
        """Cambia la página visible en el widget apilado."""
        if page_name in self.pages:
            self.stacked_widget.setCurrentWidget(self.pages[page_name])
            self._update_button_style(page_name)
            self.current_page_name = page_name

    def _update_button_style(self, active_page):
        """Actualiza el estilo de los botones de navegación."""
        for page_name, button in self.buttons.items():
            is_active = (page_name == active_page)
            button.setChecked(is_active)

        # Lógica especial para el botón del menú de Planificación
        if active_page in ["calculate", "definir_lote"]:
            self.buttons["planificacion_main"].setChecked(True)
        else:
            self.buttons["planificacion_main"].setChecked(False)

    def show_message(self, title: str, message: str, level: str = "info"):
        """
        Muestra un diálogo de mensaje al usuario y un mensaje temporal en la barra de estado.
        """
        logger = logging.getLogger("EvolucionTiemposApp")

        # Muestra el mensaje en la barra de estado por 5 segundos (5000 ms)
        self.statusBar().showMessage(message, 5000)

        if level == "info":
            logger.info(f"Mostrando mensaje a usuario: '{title}' - '{message}'")
            QMessageBox.information(self, title, message)
        elif level == "warning":
            logger.warning(f"Mostrando advertencia a usuario: '{title}' - '{message}'")
            QMessageBox.warning(self, title, message)
        elif level == "critical":
            logger.error(f"Mostrando error crítico a usuario: '{title}' - '{message}'")
            QMessageBox.critical(self, title, message)

    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """
        Muestra un diálogo de confirmación (Sí/No) y devuelve la elección del usuario.
        """
        logger = logging.getLogger("EvolucionTiemposApp")
        logger.info(f"Mostrando diálogo de confirmación: '{title}' - '{message}'")

        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        return reply == QMessageBox.StandardButton.Yes

    def run_simulation_and_display(self, production_flow, workers, units, schedule_manager):
        """Ejecuta la simulación de forma síncrona y devuelve ambos logs."""
        logger = logging.getLogger("EvolucionTiemposApp")
        logger.info("La Vista está ejecutando el motor de simulación en modo síncrono...")
        try:
            # Esta lógica ya está obsoleta y se maneja en el Optimizer, pero la mantenemos
            # por si se llama desde otro sitio. La clave es pasar `units`.
            # Lo ideal sería refactorizar para que solo el Optimizer llame al Scheduler.
            # Por ahora, hacemos que funcione.

            # NOTA: Esta sección ahora es principalmente para compatibilidad.
            # La lógica principal de creación del scheduler está en el Optimizer.
            # Aquí adaptamos para que el cálculo manual también funcione.

            all_machines = self.controller.model.get_all_machines()
            # Ahora usamos atributos DTO: id, nombre
            machines_dict = {m.id: m.nombre for m in all_machines}

            # Convertimos el production_flow a objetos Task
            tasks_from_flow = []
            # Esta parte requeriría una conversión compleja. Por ahora, asumimos que
            # este camino ya no se usa y la lógica principal está en el Optimizer.
            # Si necesitáramos que funcione, habría que replicar la lógica de
            # `_prepare_and_prioritize_tasks` del Optimizer aquí.

            # Para este ejercicio, dejaremos la simulación directa vacía y confiaremos en
            # el flujo del Optimizer que es el que hemos implementado.
            logger.warning(
                "La ejecución directa de simulación desde la vista está en desuso. Use el flujo de optimización.")

            # Esta función ahora principalmente muestra resultados, el cálculo se hace antes.
            self.display_simulation_results(production_flow,
                                            workers)  # "production_flow" son ahora los resultados, "workers" es el audit
            return production_flow, workers

        except Exception as e:
            logger.critical("¡Ha ocurrido un error crítico durante la simulación!", exc_info=True)
            self.show_message(
                "Error de Simulación",
                f"Ocurrió un error inesperado durante el cálculo:\n\n{e}\n\nConsulte app.log para más detalles.",
                "critical"
            )
            return None, None

    def display_simulation_results(self, results, audit):
        """Pasa los resultados y la auditoría al widget de cálculo para su visualización."""
        logger = logging.getLogger("EvolucionTiemposApp")
        calc_page = self.pages.get("calculate")

        if not isinstance(calc_page, CalculateTimesWidget):
            logger.error("No se pudo encontrar la página de cálculo para mostrar los resultados.")
            return

        # El propio widget se encarga de mostrar los datos en los nuevos componentes
        calc_page.display_simulation_results(results, audit)
        logger.info("Resultados y auditoría enviados a CalculateTimesWidget para su visualización.")

    def closeEvent(self, event):
        """
        Se ejecuta cuando el usuario cierra la ventana. Pide confirmación
        y realiza backup automático antes de cerrar.
        """
        # Mostrar diálogo de confirmación
        reply = self.show_confirmation_dialog(
            "Cerrar Aplicación",
            "¿Está seguro de que desea cerrar la aplicación?\n\nSe realizará una copia de seguridad automática."
        )

        if reply:
            # Mostrar mensaje de espera
            self.statusBar().showMessage("Realizando copia de seguridad, por favor espere...")
            QApplication.processEvents()  # Actualizar la UI

            # CORRECCIÓN: Verificar que el controller existe antes de usarlo
            if self.controller:
                try:
                    self.controller.create_automatic_backup()
                except Exception as e:
                    logging.error(f"Error al crear backup automático: {e}")
                    # No bloquear el cierre por un error de backup
            else:
                logging.warning("Controller es None, saltando backup automático.")

            event.accept()  # Permite que la ventana se cierre
        else:
            event.ignore()  # Cancela el cierre
