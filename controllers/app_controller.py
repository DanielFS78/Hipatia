# -*- coding: utf-8 -*-
# =================================================================================
# IMPORTS
# =================================================================================

# ------------------- LIBRERÍAS ESTÁNDAR -------------------
import configparser
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import sys
import math
from dataclasses import asdict

# --- FIX PARA macOS: EVITAR BUG DE QT CON ESPACIOS EN PATH ---
# Qt6 tiene un bug donde no puede cargar plugins si la ruta contiene espacios.
# 
# PRIORIDAD DE SOLUCIONES:
# 1. Si QT_PLUGIN_PATH ya está configurado (por run_app.sh), no hacer nada
# 2. Si no, intentar usar la ruta sin espacios en /tmp/pyqt6_venv
# 3. Como último recurso, fallar con mensaje explicativo
#
# IMPORTANTE: Este fix debe ejecutarse ANTES de cualquier import de PyQt6.
if sys.platform == "darwin":
    # Verificar si las variables ya están configuradas correctamente (por run_app.sh)
    existing_qt_path = os.environ.get("QT_PLUGIN_PATH", "")
    if existing_qt_path and " " not in existing_qt_path and os.path.exists(existing_qt_path):
        # Ya está configurado correctamente, no hacer nada
        pass
    else:
        # Intentar configurar usando la copia en /tmp
        tmp_pyqt = "/tmp/pyqt6_venv"
        if os.path.exists(os.path.join(tmp_pyqt, "PyQt6", "Qt6", "plugins")):
            qt6_dir = os.path.join(tmp_pyqt, "PyQt6", "Qt6")
            os.environ["QT_PLUGIN_PATH"] = os.path.join(qt6_dir, "plugins")
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(qt6_dir, "plugins", "platforms")
            
            # Añadir /tmp/pyqt6_venv al path de Python para que encuentre PyQt6
            if tmp_pyqt not in sys.path:
                sys.path.insert(0, tmp_pyqt)
        # Si no existe la copia en /tmp, Qt probablemente fallará y el usuario verá el mensaje de error
# --- FIN DEL FIX ---
from datetime import date, datetime, timedelta, time
from simulation_adapter import AdaptadorScheduler
from core.camera_manager import CameraManager, CameraInfo
try:
    import cv2
except (ImportError, AttributeError):
    cv2 = None
# ------------------- LIBRERÃAS DE TERCEROS -------------------
import requests
from time_calculator import CalculadorDeTiempos
# PyQt6 - Core y GUI
from PyQt6.QtCore import QDate, QObject, QProcess, Qt, QTime, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QTextCharFormat

# Imports para las nuevas funcionalidades de trazabilidad
from core.qr_scanner import QrScanner, scan_qr_simple
from core.camera_manager import CameraManager, CameraInfo
from core.qr_generator import QrGenerator
from core.label_manager import LabelManager

# PyQt6 - Widgets
from PyQt6.QtWidgets import (
    QApplication, QButtonGroup, QCalendarWidget, QCheckBox, QComboBox,
    QCompleter, QDateEdit, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QInputDialog,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPushButton, QRadioButton, QSpinBox, QScrollArea, QSizePolicy, QSpacerItem,
    QStackedWidget, QTableWidget, QTableWidgetItem, QTextEdit, QTimeEdit,
    QVBoxLayout, QWidget, QMenu
)

# PyQt6 - Charts
from PyQt6.QtCharts import (
    QBarSeries, QBarSet, QChart, QChartView, QDateTimeAxis, QLineSeries,
    QPieSeries, QValueAxis
)

# ------------------- MÃ“DULOS DE LA APLICACIÃ“N LOCAL -------------------

# Lógica de la base de datos y repositorios
from database.database_manager import DatabaseManager
from core.app_model import AppModel
from database.repositories import (
    MachineRepository, PilaRepository, PreprocesoRepository, ProductRepository,
    MachineRepository, PilaRepository, PreprocesoRepository, ProductRepository,
    WorkerRepository, LabelCounterRepository, LoteRepository, TrackingRepository
)

# --- SUB-CONTROLLERS ---
from controllers.product_controller_v2 import ProductController
from controllers.worker_controller import WorkerController
from controllers.pila_controller import PilaController

# Lógica de negocio y utilidades
import calendar_helper
import constants
import utils
from importer import MaterialImporterFactory
from report_strategy import (
    GeneradorDeInformes, ReporteHistorialFabricacion,
    ReporteHistorialIteracion, ReportePilaFabricacionExcelMejorado,
)
from schedule_config import ScheduleConfig
from simulation_engine import SimulationWorker, Optimizer
from visualization_generator import VisualizationGenerator

# Componentes de la Interfaz de Usuario (UI)
from ui.dialogs import (
    AddBreakDialog, AddIterationDialog, ChangePasswordDialog,
    DefineProductionFlowDialog, FabricacionBitacoraDialog,
    LoadPilaDialog, PrepGroupsDialog, PrepStepsDialog,
    ProcesosMecanicosDialog, ProductDetailsDialog, SavePilaDialog,
    SeleccionarHojasExcelDialog, SubfabricacionesDialog,
    PreprocesoDialog, EnhancedProductionFlowDialog,
    PreprocesosSelectionDialog, CreateFabricacionDialog, GetOptimizationParametersDialog,
    PreprocesosForCalculationDialog, AssignPreprocesosDialog,
    GetUnitsDialog, DefinirCantidadesDialog
)
from ui.widgets import (
    AddProductWidget,
    CalculateTimesWidget,
    DashboardWidget,
    DefinirLoteWidget,
    GestionDatosWidget,
    LotesWidget,
    MachinesWidget,
    HelpWidget,
    HistorialWidget,
    HomeWidget,
    PreprocesosWidget,
    ReportesWidget,
    SettingsWidget,
    PrepStepsWidget,
    WorkersWidget
)
from core.quote_service import QuoteService  # NUEVO: Importar servicio de frases
from PyQt6.QtCore import QRunnable, QThreadPool  # NUEVO: Para carga asíncrona de datos de wiki

# =================================================================================
# FUNCIONES AUXILIARES
# =================================================================================


def resource_path(relative_path):
    import sys, os
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

class AppController(QObject):
    """Controlador principal que orquesta la aplicación."""

    # OptimizerWorker class moved to pila_controller.py

    def __init__(self, model: AppModel, view, schedule_manager: ScheduleConfig):
        super().__init__()
        self.model = model
        self.db = model.db
        self.view = view
        self.schedule_manager = schedule_manager
        self.logger = logging.getLogger("EvolucionTiemposApp")
        self.logger.info("Inicializando AppController...")

        # --- INICIO DE CAMBIOS ---
        # 1. Crear UNA SOLA instancia de CameraManager
        self.camera_manager = CameraManager(
            max_cameras=10,
            detection_timeout=2.0,
            validation_frames=3
        )
        self.logger.info("CameraManager global inicializado")

        # 2. Crear UNA SOLA instancia de QrGenerator
        self.qr_generator = QrGenerator()
        self.logger.info("QrGenerator global inicializado")

        # 3. Inicializar LabelManager con el generador
        self.label_manager = LabelManager(
            templates_dir="templates",
            qr_generator=self.qr_generator
        )
        self.logger.info("LabelManager inicializado")

        # 4. QrScanner se inicializa como None.
        #    Se creará en _initialize_qr_scanner() DESPUÉS de la detección.
        self.qr_scanner = None
        # --- FIN DE CAMBIOS ---

        # Acceso directo al tracking_repository
        self.tracking_repo = self.model.db.tracking_repo

        # 5. Inicializar el repositorio de contadores de etiquetas usando el SessionLocal de la BD principal
        self.label_counter_repo = LabelCounterRepository(self.model.db.SessionLocal)
        self.logger.info("Repositorio de contadores (etiquetas) inicializado.")

        # Estado y caché del controlador
        self.active_dialogs = {}
        self._edit_search_type = "Productos"
        self.last_production_flow = None
        self.last_simulation_results = None
        self.last_audit_log = None
        self.last_units_calculated = 1
        self.last_flexible_workers_needed = 0
        self.current_lote_content = []
        self.selected_report_item = None
        self._selected_product_for_calc = None
        self._selected_product_for_calc_desc = ""
        self.historial_data = []
        self.current_user = None

        # Servicio de Frases y ThreadPool
        self.quote_service = QuoteService()
        self.thread_pool = QThreadPool()

        # Hilos para tareas en segundo plano
        self.thread = None
        self.worker = None

        # --- SUB-CONTROLLERS INITIALIZATION ---
        self.product_controller = ProductController(self)
        self.worker_controller = WorkerController(self)
        self.pila_controller = PilaController(self)
        
        # Alias for backward compatibility if needed, or redirect
        self.OptimizerWorker = self.pila_controller.OptimizerWorker

        # Backward-compatible delegation methods for fabrications
        self.show_create_fabricacion_dialog = self.product_controller.show_create_fabricacion_dialog
        self._on_fabrication_result_selected = self.product_controller._on_fabrication_result_selected
        self._on_update_fabricacion = self.product_controller._on_update_fabricacion
        self._on_delete_fabricacion = self.product_controller._on_delete_fabricacion
        self.get_preprocesos_for_fabricacion = self.pila_controller.get_preprocesos_for_fabricacion
        self.get_preprocesos_by_fabricacion = self.product_controller.get_preprocesos_by_fabricacion
        self.search_fabricaciones = self.product_controller.search_fabricaciones
        self.show_fabricacion_preprocesos = self.product_controller.show_fabricacion_preprocesos
        self._refresh_fabricaciones_list = self.product_controller._refresh_fabricaciones_list
        
        # Backward-compatible delegation for pila methods
        self._start_simulation_thread = self.pila_controller._start_simulation_thread
        self._on_add_lote_to_pila_clicked = self.pila_controller._on_add_lote_to_pila_clicked
        self._on_calc_lote_search_changed = self.pila_controller._on_calc_lote_search_changed
        self._on_clear_simulation = self.pila_controller._on_clear_simulation
        
        # Backward-compatible delegation for worker methods
        self.update_workers_view = self.worker_controller.update_workers_view
        self.update_lotes_view = self.pila_controller.update_lotes_view
        # self.update_machines_view removed (implemented as real method)
        
        # Backward-compatible delegation for product methods
        # Backward-compatible delegation for product methods
        self._on_product_search_changed = self.product_controller._on_product_search_changed
        self._on_edit_fabricacion_preprocesos_clicked = self.product_controller.show_fabricacion_preprocesos

        self.logger.info("Sub-controladores (Product, Worker, Pila) inicializados.")

        # Textos de ayuda contextual
        self.help_texts = {
            "home": "Esta es la pantalla de bienvenida. Desde aquí puedes navegar a todas las secciones de la aplicación usando el menú de la izquierda.",
            "dashboard": """El Dashboard ofrece una vista gráfica y rápida del estado general de la producción. Aquí encontrarás:
    - <b>Uso de Máquinas:</b> Un gráfico de barras que muestra el tiempo total (en minutos) que cada máquina ha sido requerida según las subfabricaciones definidas.
    - <b>Carga de Trabajo:</b> Muestra el tiempo total de trabajo asignado a cada operario.
    - <b>Componentes Problemáticos:</b> Un gráfico circular que identifica los materiales o componentes que se registran con más frecuencia en iteraciones de producto marcadas como problemáticas.
    - <b>Actividad Mensual:</b> Un gráfico de líneas que compara el número de nuevas iteraciones de producto frente a nuevas fabricaciones creadas en el último año.""",
            "reportes": """En esta sección puedes generar informes detallados en formato PDF o Excel.
    1.  <b>Buscar Elemento:</b> Usa el cuadro de búsqueda para encontrar el elemento sobre el que quieres informar. Puedes buscar:
    - Un <b>Producto</b> (para ver su historial de cambios).
    - Una <b>Fabricación</b> (para ver la planificación de una de sus pilas guardadas).
    - Una <b>Pila</b> guardada directamente por su nombre.
    2.  <b>Seleccionar Resultado:</b> Haz clic en un elemento de la lista de resultados.
    3.  <b>Generar Informe:</b> A la derecha aparecerán los botones con los tipos de informes disponibles para ese elemento.
    Haz clic en el que necesites y sigue las instrucciones para guardarlo.""",
            "historial": """Aquí puedes consultar el historial de toda la actividad de la aplicación.
    - <b>Modo de Vista:</b> Elige entre 'Ver Iteraciones' (para consultar el historial de cambios y versiones de los productos) o 'Ver Fabricaciones' (para ver el historial de todas las 'Pilas' de producción que has guardado).
    - <b>Búsqueda y Filtros:</b> Utiliza la búsqueda y los filtros para encontrar rápidamente lo que necesitas.
    - <b>Calendario Interactivo:</b> Las fechas en el calendario se colorearán según los resultados de tu búsqueda.
    Haz clic en una fecha para filtrar la lista y ver solo la actividad de ese día.""",
            "gestion_datos": """Este es el panel central para administrar los datos maestros de la aplicación. Utiliza las pestañas para navegar entre las diferentes secciones:
    - <b>Productos y Fabricaciones:</b> Gestiona tus productos finales y los 'kits' (fabricaciones) que los agrupan.
    - <b>Máquinas:</b> Añade o edita las máquinas disponibles en tu planta.
    - <b>Trabajadores:</b> Gestiona la lista de operarios.
    El funcionamiento general es similar en todas las pestañas: la lista de la izquierda muestra los elementos existentes, y al seleccionar uno, sus detalles aparecen a la derecha para que puedas editarlos.""",
            "add_product": """Utiliza este formulario para añadir un nuevo producto a la base de datos.
    - <b>Código y Descripción:</b> Identificadores únicos y descriptivos para el producto. Son campos obligatorios.
    - <b>Departamento:</b> El área principal responsable del producto.
    - <b>Dónde se encuentra/ubica:</b> Notas sobre su localización física o en el almacén.
    - <b>Â¿Tiene subfabricaciones?:</b> Esta es la opción más importante.
    - Si <b>NO</b> está marcada: El producto se considera una tarea única.
    Deberás introducir su 'Tiempo Ã“ptimo' de fabricación en minutos.
    - Si <b>SÃ</b> está marcada: El producto se compone de múltiples pasos. El campo 'Tiempo Ã“ptimo' desaparecerá.
    En su lugar, debes pulsar el botón <b>'Añadir/Editar Subfabricaciones'</b>.
    Al pulsar este botón, se abrirá un diálogo donde podrás definir cada una de las tareas (subfabricaciones) que componen el producto, asignando a cada una su propio tiempo, tipo de trabajador y máquina requerida.
    <b>Implicación en el cálculo:</b> El tiempo total del producto será la suma de los tiempos de todas sus subfabricaciones.""",
            "create_fabrication": """Una 'Fabricación' no es un producto físico, sino un 'kit' o una orden de producción que agrupa uno o más productos en ciertas cantidades.
    1.  <b>Código y Descripción de Fabricación:</b> Dale un nombre o código único a esta orden (ej: 'PEDIDO_CLIENTE_A').
    2.  <b>Añadir Producto:</b> En la sección inferior, busca un producto existente por su código o descripción.
    3.  <b>Seleccionar y Añadir:</b> Cuando aparezca en la lista de resultados, haz clic sobre él.
    Luego, ajusta la 'Cantidad' y pulsa el botón <b>'Añadir Producto'</b>.
    El producto se añadirá a la tabla de 'Contenido de la Fabricación'.
    4.  <b>Repetir y Guardar:</b> Repite el proceso para todos los productos que forman parte de esta orden y finalmente pulsa <b>'Guardar Fabricación'</b>.""",
            "settings": """Aquí puedes configurar los parámetros globales de la aplicación.
    - <b>Configuración del Horario Laboral:</b> Define la hora de inicio y fin de la jornada laboral, así como los periodos de descanso (ej: almuerzo).
    Estos tiempos se usarán para que los cálculos de planificación sean realistas.
    - <b>Gestión de Días Festivos y Cierres:</b> Selecciona fechas en el calendario y márcalas como no laborables.
    El motor de cálculo saltará estos días automáticamente.
    - <b>Copias de Seguridad:</b> Permite exportar toda la base de datos a un archivo .zip para guardarla de forma segura, o importar un archivo .zip para restaurar los datos (Â¡cuidado, esto sobreescribe los datos actuales!)."""
        }

    def handle_login(self):
        """
        Muestra el diálogo de login y gestiona la autenticación.

        Returns:
            tuple: (user_data, authenticated) donde:
                - user_data: Diccionario con datos del usuario o None
                - authenticated: True si login exitoso, False si falló
            None: Si el usuario canceló el login
        """
        from ui.dialogs import LoginDialog

        dialog = LoginDialog(self.view if hasattr(self, 'view') else None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username, password = dialog.get_credentials()
            user_data = self.model.worker_repo.authenticate_user(username, password)

            if user_data:
                self.current_user = user_data
                self.logger.info(f"Login exitoso para el usuario '{username}' con rol '{user_data['role']}'.")
                
                # Cargar frase célebre
                self._load_quote_for_home()
                
                return (user_data, True)
            else:
                self.logger.warning("Intento de login fallido: credenciales incorrectas")
                return (None, False)

    def _load_quote_for_home(self):
        """Carga una frase aleatoria en el HomeWidget y lanza hilo para detalles."""
        try:
            home_page = self.view.pages.get("home")
            if not isinstance(home_page, HomeWidget):
                return

            # 1. Obtener frase local (rápido)
            quote_data = self.quote_service.get_random_quote()
            if not quote_data:
                return

            author = quote_data.get('author', 'Anónimo')
            quote = quote_data.get('quote', '')
            
            # Mostrar inmediatamente
            home_page.set_quote(quote, author)

            # 2. Lanza tarea en background para info extra (Wiki)
            worker = AuthorInfoLoader(self.quote_service, author)
            # Usamos una lambda segura para actualizar la UI
            worker.signals.finished.connect(lambda info: home_page.set_quote(quote, author, info))
            self.thread_pool.start(worker)
            
        except Exception as e:
            self.logger.error(f"Error cargando frase célebre: {e}")
        else:
            self.logger.info("El usuario canceló el inicio de sesión.")
            return None

    def _launch_worker_interface(self):
        """
        Lanza la interfaz simplificada para trabajadores.

        Crea una ventana específica para el rol de trabajador con funcionalidades
        limitadas: ver fabricaciones asignadas, escanear QR y registrar incidencias.
        """
        try:
            # Importar módulos necesarios para la interfaz de trabajador
            # NOTA: Estos archivos los crearemos en el siguiente paso
            from ui.worker.worker_main_window import WorkerMainWindow
            from features.worker_controller import WorkerController

            self.logger.info("Iniciando interfaz de trabajador...")

            # Crear ventana principal de trabajador
            self.worker_window = WorkerMainWindow(self.current_user)

            # ------------------------------------------------------------------
            # INICIO DE CORRECCIÓN: Restaurar la inicialización de cámara
            # ------------------------------------------------------------------
            # self._initialize_qr_scanner() # <-- LÃ NEA ORIGINAL ELIMINADA
            # self.qr_scanner = None
            # self.logger.info("Inicialización de cámara al inicio OMITIDA. Se configurará desde el menú.")

            # RESTAURAMOS LA INICIALIZACIÓN AUTOMÁTICA
            self.logger.info("Inicializando QrScanner automáticamente al inicio...")
            self._initialize_qr_scanner()  # <-- LÍNEA RESTAURADA
            if not self.qr_scanner:
                self.logger.error("Fallo al inicializar el QrScanner automáticamente.")
                # No bloqueamos la app, pero los botones de escaneo no funcionarán
                # El usuario podrá intentarlo manualmente desde el menú "Configurar Cámara"

            # ------------------------------------------------------------------
            # FIN DE CORRECCIÓN
            # ------------------------------------------------------------------

            # Crear controlador específico para trabajadores
            self.worker_controller = WorkerController(
                current_user=self.current_user,
                db_manager=self.model.db,
                main_window=self.worker_window,
                qr_scanner=self.qr_scanner,  # <-- Ahora se pasa el scanner inicializado (o None si falló)
                tracking_repo=self.tracking_repo,
                label_manager=self.label_manager,
                qr_generator=self.qr_generator,
                label_counter_repo=self.label_counter_repo
            )

            # Inicializar el controlador
            self.worker_controller.initialize()

            # Mostrar la ventana
            self.worker_window.show()

            self.logger.info(f"Interfaz de trabajador iniciada para: {self.current_user.get('nombre', 'Usuario')}")

        except ImportError as e:
            self.logger.error(f"Error importando módulos de trabajador: {e}")
            self.logger.warning("Los módulos de trabajador aún no están creados. Mostrando interfaz básica.")

            # Fallback: mostrar mensaje y cerrar
            QMessageBox.information(
                None,
                "Funcionalidad en Desarrollo",
                "La interfaz de trabajador está en desarrollo.\n\n"
                f"Bienvenido/a: {self.current_user.get('nombre', 'Usuario')}\n"
                "Próximamente podrás acceder a tus fabricaciones asignadas."
            )
            sys.exit(0)

        except Exception as e:
            self.logger.critical(f"Error crítico lanzando interfaz de trabajador: {e}", exc_info=True)
            QMessageBox.critical(
                None,
                "Error",
                f"No se pudo iniciar la interfaz de trabajador.\n\nError: {e}"
            )
            sys.exit(1)

    def _update_ui_for_role(self):
        """Habilita o deshabilita elementos de la UI según el rol del usuario."""
        if not self.current_user:
            return

        role = self.current_user.get('role')
        is_responsable = (role == 'Responsable')

        self.view.buttons['dashboard'].setEnabled(is_responsable)
        self.view.buttons['reportes'].setEnabled(is_responsable)
        self.view.buttons['historial'].setEnabled(is_responsable)
        self.view.buttons['gestion_datos'].setEnabled(is_responsable)
        self.view.buttons['add_product'].setEnabled(is_responsable)
        self.view.buttons['settings'].setEnabled(is_responsable)

        if not is_responsable:
            self.view.switch_page("home")
            self.view.show_message("Acceso Limitado",
                                   "Como trabajador, tu acceso es limitado. Futuras funcionalidades estarán disponibles aquí.",
                                   "info")

    def connect_signals(self):
        self.logger.debug("Iniciando conexión de señales...")
        self._connect_navigation_signals()
        self._connect_add_product_signals()
        self._connect_reportes_signals()
        self._connect_calculate_signals()
        self._connect_historial_signals()
        self._connect_workers_signals()
        self._connect_machines_signals()
        self._connect_products_signals()
        self._connect_fabrications_signals()

        # âœ… CORRECCIÃ“N: Conectar señales de preprocesos de forma segura
        try:
            self._connect_preprocesos_signals()
        except Exception as e:
            self.logger.error(f"Error conectando señales de preprocesos: {e}")
        self._connect_definir_lote_signals()
        self._connect_lotes_management_signals()
        self.model.product_deleted_signal.connect(self._on_data_changed)
        self.logger.info("âœ… Todas las señales de la aplicación han sido conectadas exitosamente.")

        # Señales de configuración de hardware
        settings_page = self.view.pages.get("settings")
        if isinstance(settings_page, SettingsWidget):
            settings_page.detect_cameras_signal.connect(self._on_detect_cameras)
            settings_page.save_hardware_signal.connect(self._on_save_hardware_settings)

            # AÃ‘ADIR ESTA LÃNEA (si el botón existe en SettingsWidget):
            if hasattr(settings_page, 'test_camera_signal'):
                settings_page.test_camera_signal.connect(self._on_test_camera)

    def _connect_preprocesos_signals(self):
        """Conecta las señales del widget de preprocesos."""
        self.logger.debug("Conectando señales de Preprocesos...")
        try:
            # Obtener el widget desde el diccionario de páginas de la vista
            preprocesos_widget = self.view.pages.get("preprocesos")

            if isinstance(preprocesos_widget, PreprocesosWidget):
                # Asegurarnos de que el widget conoce al controlador
                preprocesos_widget.set_controller(self)

                # --- INICIO DE LA CORRECCIÃ“N ---
                # Conectar las señales de los botones a los métodos del controlador
                preprocesos_widget.add_button.clicked.connect(self.show_add_preproceso_dialog)
                preprocesos_widget.edit_button.clicked.connect(preprocesos_widget._on_edit_clicked)
                preprocesos_widget.delete_button.clicked.connect(preprocesos_widget._on_delete_clicked)
                # --- FIN DE LA CORRECCIÃ“N ---

                self.logger.debug("Señales de Preprocesos conectadas exitosamente.")

                # Cargar los datos iniciales al arrancar
                self._load_preprocesos_data()
            else:
                self.logger.warning("Widget de preprocesos no encontrado o no es del tipo correcto.")

        except Exception as e:
            self.logger.error(f"Error crítico al conectar las señales de preprocesos: {e}", exc_info=True)

    def _update_simulation_progress(self, value):
        """Actualiza el valor de la barra de progreso en la UI."""
        calc_page = self.view.pages.get("calculate")
        if isinstance(calc_page, CalculateTimesWidget):
            calc_page.progress_bar.setValue(value)

    def handle_save_flow_only(self, nombre, descripcion, production_flow):
        """Guarda solo el flujo de producción, reconstruyendo los datos necesarios."""
        self.logger.info(f"Guardando solo el flujo de producción para la pila '{nombre}'.")

        # 1. Reconstruir la 'pila_de_calculo' a partir del 'production_flow'
        pila_de_calculo_reconstruida = {"preprocesos": {}, "productos": {}}
        for step in production_flow:
            task_info = step.get('task', {})
            original_code = task_info.get('original_product_code', '')

            if "PREP_" in original_code:
                # Es un preproceso
                prep_id = int(original_code.replace("PREP_", ""))
                # Nota: No tenemos toda la info del preproceso aquí, pero sí lo esencial.
                pila_de_calculo_reconstruida['preprocesos'][prep_id] = {
                    'id': prep_id,
                    'nombre': task_info.get('name', 'Preproceso Desconocido').replace("[PREPROCESO] ", "")
                }
            else:
                # Es un producto
                original_info = task_info.get('original_product_info', {})
                pila_de_calculo_reconstruida['productos'][original_code] = {
                    "codigo": original_code,
                    "descripcion": original_info.get('desc', 'Producto Desconocido')
                }

        # 2. No hay resultados de simulación ni unidades definidas en este modo.
        simulation_results = []
        unidades = 1  # Se guarda con 1 unidad por defecto
        producto_origen = None  # No se conoce el origen en este contexto

        # 3. Llamar al método del modelo con los datos correctamente estructurados
        self.model.save_pila(
            nombre,
            descripcion,
            pila_de_calculo_reconstruida,
            production_flow,
            simulation_results,
            producto_origen,
            unidades=unidades
        )

    def _load_preprocesos_data(self):
        """Carga o recarga los datos de preprocesos y los muestra en la tabla."""
        self.logger.info("Cargando datos de preprocesos...")
        try:
            # âœ… CORRECCIÃ“N: Usar el widget correcto desde self.view.pages
            preprocesos_widget = self.view.pages.get("preprocesos")

            if not preprocesos_widget:
                self.logger.warning("Widget de preprocesos no encontrado en las páginas.")
                return

            # Obtener los datos de preprocesos del modelo
            preprocesos_data = self.model.get_all_preprocesos_with_components()

            # Cargar en el widget
            preprocesos_widget.load_preprocesos_data(preprocesos_data)

        except Exception as e:
            self.logger.error(f"Error cargando datos de preprocesos: {e}")
            # Cargar lista vacía en caso de error
            preprocesos_widget = self.view.pages.get("preprocesos")
            if preprocesos_widget:
                preprocesos_widget.load_preprocesos_data([])

    def get_all_preprocesos_with_components(self):
        """
        Obtiene todos los preprocesos ya formateados desde el repositorio.
        """
        try:
            # El repositorio ahora hace todo el trabajo y devuelve la lista final.
            return self.model.preproceso_repo.get_all_preprocesos()
        except Exception as e:
            self.logger.error(f"Error obteniendo preprocesos: {e}", exc_info=True)
            return []

    def _on_add_new_iteration_clicked(self):
        """Abre el nuevo diálogo para crear una iteración completa."""
        dialog = AddIterationDialog(self.product_code, self.view)
        if dialog.exec():
            data = dialog.get_data()
            if not data["responsable"] or not data["descripcion"]:
                self.view.show_message("Campos Vacíos", "El responsable y la descripción son obligatorios.",
                                       "warning")
                return

            # Creamos la iteración primero para obtener un ID.
            # Si hay un plano, se guardará temporalmente como NULL.
            iteracion_id = self.model.add_product_iteration(
                self.product_code, data["responsable"], data["descripcion"],
                data["tipo_fallo"], [], ruta_plano=None
            )
            if not iteracion_id:
                self.view.show_message("Error", "No se pudo crear la base de la iteración.", "critical")
                return

            # Si se adjuntó un plano, ahora lo copiamos y actualizamos la BD
            if data["ruta_plano_origen"]:
                success, final_plano_path = self.handle_attach_file(
                    "iteration", iteracion_id, data["ruta_plano_origen"], "plano"
                )
                if success:
                    self.model.db.update_iteration_file_path(iteracion_id, 'ruta_plano', final_plano_path)

            self.load_iterations()  # Recargamos para ver el nuevo item

    def handle_attach_file(self, owner_type: str, owner_id: int, source_file_path: str, file_type: str):
        """Gestiona la copia de un archivo a una carpeta de datos y devuelve la ruta relativa."""
        self.logger.info(f"Adjuntando archivo '{source_file_path}' a {owner_type} ID {owner_id}.")
        try:
            # data/imagenes/iteration_1.jpg | data/planos/iteration_1.pdf
            target_dir = os.path.join("data", f"{file_type}s")
            os.makedirs(target_dir, exist_ok=True)

            _, file_extension = os.path.splitext(source_file_path)
            new_filename = f"{owner_type}_{owner_id}{file_extension}"
            destination_path = os.path.join(target_dir, new_filename)

            # Aseguramos que el subdirectorio final exista (por si owner_type contenía rutas)
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)

            shutil.copy(source_file_path, destination_path)

            relative_path = os.path.join("data", f"{file_type}s", new_filename).replace("\\", "/")
            self.logger.info(f"Archivo guardado en '{destination_path}'. Ruta relativa: '{relative_path}'")
            return True, relative_path
        except Exception as e:
            self.logger.error(f"Error al adjuntar archivo: {e}", exc_info=True)
            return False, str(e)

    def handle_view_file(self, relative_path: str):
        """Abre un archivo usando el visor por defecto del sistema."""
        if not relative_path or not os.path.exists(relative_path):
            self.view.show_message("Error", "El archivo no se encuentra o la ruta es inválida.", "warning")
            return
        try:
            from PyQt6.QtGui import QDesktopServices
            from PyQt6.QtCore import QUrl

            file_url = QUrl.fromLocalFile(os.path.abspath(relative_path))
            QDesktopServices.openUrl(file_url)
        except Exception as e:
            self.logger.error(f"No se pudo abrir el archivo '{relative_path}': {e}")
            self.view.show_message("Error", f"No se pudo abrir el archivo:\n{e}", "critical")

    def _connect_navigation_signals(self):
        """Conecta las señales de los botones de navegación."""
        try:
            for name, button in self.view.buttons.items():
                if name == "context_help":
                    button.clicked.connect(self._on_context_help_clicked)
                else:
                    # âœ… USAR lambda con captura correcta de variable
                    button.clicked.connect(lambda checked=False, n=name: self._on_nav_button_clicked(n))

            # Conectar señales específicas de configuración
            settings_page = self.view.pages.get("settings")
            if isinstance(settings_page, SettingsWidget):
                settings_page.add_holiday_button.clicked.connect(self._on_add_holiday)
                settings_page.remove_holiday_button.clicked.connect(self._on_remove_holiday)
                settings_page.import_signal.connect(self._on_import_databases)
                settings_page.export_signal.connect(self._on_export_databases)
                settings_page.save_schedule_signal.connect(self._on_save_schedule_settings)
                settings_page.add_break_signal.connect(self._on_add_break_clicked)
                settings_page.sync_signal.connect(self._on_sync_databases_clicked)
                # settings_page.change_own_password_signal.connect(self._on_change_own_password_clicked)
                # --- BEGIN: Add connections for break editing/removal ---
                settings_page.edit_break_signal.connect(self._on_edit_break_clicked)
                settings_page.remove_break_signal.connect(self._on_remove_break_clicked)

                settings_page.detect_cameras_signal.connect(self._on_detect_cameras)
                settings_page.save_hardware_signal.connect(self._on_save_hardware_settings)

                settings_page.import_tasks_signal.connect(self._on_import_task_data)

            self.logger.debug("Señales de los botones de navegación y configuración conectadas.")
        except Exception as e:
            self.logger.error(f"Error conectando señales de navegación: {e}")

    def _on_import_task_data(self):
        """
        Importa un archivo JSON de datos de tareas (trabajos, incidencias)
        y lo fusiona con la base de datos central.
        """
        self.logger.info("Iniciando importaciónn de datos de tareas...")

        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Seleccionar Archivo JSON de Tareas",
            "",
            "Archivos JSON (*.json)"
        )

        if not file_path:
            self.logger.info("Importación de tareas cancelada.")
            return

        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data_to_import = json.load(f)

            if not isinstance(data_to_import, list):
                raise ValueError("El archivo JSON no contiene una lista de trabajos.")

            if not self.view.show_confirmation_dialog(
                    "Confirmar Importación",
                    f"Se encontraron {len(data_to_import)} registros de trabajo en el archivo.\n"
                    "Â¿Desea fusionar estos datos con la base de datos central?\n\n"
                    "(Los registros existentes se omitirán o actualizarán)."
            ):
                return

            # Procesar la importación
            stats = {'created': 0, 'updated': 0, 'skipped': 0, 'error': 0}

            for trabajo_data in data_to_import:
                # Alrededor de la línea 1960 en app.py
                status, _ = self.model.db.tracking_repo.upsert_trabajo_log_from_dict(trabajo_data)

                # Debemos actualizar el contador de estadísticas
                if status in stats:
                    stats[status] += 1

            self.logger.info(f"Importación de tareas completada: {stats}")
            self.view.show_message(
                "Importación Completa",
                f"Importación de datos de tareas finalizada:\n\n"
                f"Nuevos: {stats['created']}\n"
                f"Actualizados: {stats['updated']}\n"
                f"Omitidos: {stats['skipped']}\n"
                f"Errores: {stats['error']}",
                "info"
            )

        except json.JSONDecodeError:
            self.logger.error(f"Error: El archivo {file_path} no es un JSON válido.")
            self.view.show_message("Error de Archivo", "El archivo seleccionado no es un JSON válido.", "critical")
        except Exception as e:
            self.logger.error(f"Error crítico durante la importación de tareas: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error inesperado: {e}", "critical")

    def _on_add_holiday(self):
        """Añade el día seleccionado en el calendario como festivo."""
        settings_page = self.view.pages["settings"]
        selected_date = settings_page.calendar.selectedDate().toPyDate()

        holidays_json = self.model.db.config_repo.get_setting('holidays', '[]')
        holidays_list = json.loads(holidays_json)

        # Evitar duplicados
        if selected_date.isoformat() not in holidays_list:
            holidays_list.append(selected_date.isoformat())
            self.model.db.config_repo.set_setting('holidays', json.dumps(holidays_list))
            self.schedule_manager.reload_config(self.model.db)
            self._load_schedule_settings()  # Recargar para refrescar la UI
            self.view.show_message("Éxito", f"Día {selected_date.strftime('%d/%m/%Y')} añadido como festivo.",
                                   "info")

    def _on_remove_holiday(self):
        """Elimina el día seleccionado de la lista de festivos."""
        settings_page = self.view.pages["settings"]
        selected_date = settings_page.calendar.selectedDate().toPyDate()

        holidays_json = self.model.db.config_repo.get_setting('holidays', '[]')
        holidays_list = json.loads(holidays_json)

        if selected_date.isoformat() in holidays_list:
            holidays_list.remove(selected_date.isoformat())
            self.model.db.config_repo.set_setting('holidays', json.dumps(holidays_list))
            self.schedule_manager.reload_config(self.model.db)
            self._load_schedule_settings()  # Recargar para refrescar la UI
            self.view.show_message("Éxito", f"Día {selected_date.strftime('%d/%m/%Y')} eliminado de festivos.",
                                   "info")

    def _initialize_qr_scanner(self):
        """
        Lee la configuración de cámara guardada e inicializa el escáner QR.
        VERSIÃ“N DEFINITIVA: Encuentra, valida Y ABRE la cámara aquí.
        Luego, inyecta el objeto de cámara abierto en QrScanner.
        """
        camera_object = None
        try:
            # 1. Liberar el scanner anterior si existe
            if self.qr_scanner:
                self.logger.info("Liberando instancia de QrScanner anterior...")
                self.qr_scanner.release_camera()
                self.qr_scanner = None

            # 2. Leer el índice de cámara guardado
            try:
                saved_index = int(self.model.db.config_repo.get_setting('camera_index', '-1'))
            except (ValueError, TypeError):
                saved_index = -1
            
            self.logger.info(f"Buscando cámara. Configuración guardada: {saved_index}")

            final_camera_index = -1
            camera_to_use = None
            camera_object = None  # Aquí guardaremos la cámara abierta

            # --- INICIO DE CAMBIOS ---

            # 3. Validar o encontrar la mejor cámara
            if saved_index >= 0:
                # Si hay un índice guardado, validarlo (Validación "pesada")
                self.logger.info(f"Validando cámara guardada (índice {saved_index})...")
                camera_to_use = self.camera_manager.get_camera_info(saved_index)
                if camera_to_use and camera_to_use.is_working:
                    self.logger.info("âœ“ Cámara guardada es válida.")
                    final_camera_index = camera_to_use.index
                else:
                    self.logger.warning(f"Cámara guardada ({saved_index}) no es válida. Buscando la mejor...")
                    saved_index = -1  # Forzar búsqueda

            if saved_index < 0:
                # Si no hay índice guardado o el guardado falla, buscar la mejor
                camera_to_use = self.camera_manager.get_best_camera()  # Detección "pesada"
                if camera_to_use:
                    final_camera_index = camera_to_use.index
                    self.logger.info(f"âœ“ Mejor cámara encontrada: {final_camera_index} ({camera_to_use.name})")
                    self.model.db.config_repo.set_setting('camera_index', str(final_camera_index))
                else:
                    self.logger.warning("No se encontró ninguna cámara funcional. Intentando fallback a índice 0.")
                    final_camera_index = 0  # Último recurso

            # 4. ABRIR LA CÁMARA AQUÃ (La única llamada a VideoCapture)
            if final_camera_index >= 0:
                self.logger.info(f"Intentando abrir hardware de cámara {final_camera_index}...")
                camera_object = cv2.VideoCapture(final_camera_index)

                if not camera_object or not camera_object.isOpened():
                    self.logger.error(
                        f"Â¡Fallo crítico! No se pudo abrir la cámara {final_camera_index} después de validarla.")
                    camera_object = None
                else:
                    self.logger.info(f"âœ“ Hardware de cámara {final_camera_index} abierto y listo.")
                    # Configurar resolución aquí
                    camera_object.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    camera_object.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    camera_object.set(cv2.CAP_PROP_FPS, 30)

            if not camera_object:
                raise Exception(f"No se pudo crear un objeto VideoCapture válido para el índice {final_camera_index}")

            # 5. Crear QrScanner INYECTANDO el objeto de cámara YA ABIERTO
            self.logger.info(f"Creando instancia de QrScanner y pasando el objeto de cámara...")
            self.qr_scanner = QrScanner(
                camera_manager=self.camera_manager,
                camera_index=final_camera_index,
                camera_object=camera_object  # <-- Pasamos la cámara abierta
            )

            if not self.qr_scanner.is_camera_ready:
                raise Exception(f"QrScanner reportó que la cámara {final_camera_index} no está lista.")

            self.logger.info(f"âœ“ QrScanner inicializado y listo con cámara {final_camera_index}")

            # --- FIN DE CAMBIOS ---

            if hasattr(self, 'worker_controller') and self.worker_controller:
                self.worker_controller.qr_scanner = self.qr_scanner

        except Exception as e:
            self.logger.critical(f"Error crítico inicializando QrScanner: {e}", exc_info=True)
            if camera_object:  # Si el objeto se creó pero QrScanner falló
                camera_object.release()
            self.qr_scanner = None

            if hasattr(self, 'view') and self.view:
                self.view.show_message(
                    "Error de Cámara",
                    "No se pudo inicializar una cámara funcional.\n\n"
                    "Las funciones de escaneo QR no estarán disponibles.\n"
                    f"Error: {e}",
                    "critical"
                )

    def _on_detect_cameras(self):
        """
        Detecta cámaras usando el CameraManager robusto.
        """
        self.logger.info("Iniciando detección robusta de cámaras...")

        settings_page = self.view.pages.get("settings")
        if not isinstance(settings_page, SettingsWidget):
            return

        # Limpiar y mostrar "detectando..."
        settings_page.camera_combo.clear()
        settings_page.camera_combo.addItem("ðŸ” Detectando cámaras...", -2)
        settings_page.camera_combo.setEnabled(False)
        QApplication.processEvents()

        try:
            # Usar CameraManager para detectar
            cameras = self.camera_manager.detect_cameras(force_refresh=True)

            settings_page.camera_combo.clear()

            if not cameras:
                settings_page.camera_combo.addItem("âŒ No se detectaron cámaras", -1)
                self.logger.warning("No se detectaron cámaras")
                QMessageBox.warning(
                    settings_page,
                    "Sin Cámaras",
                    "No se detectaron cámaras.\n\nVerifica que esté conectada."
                )
            else:
                # Añadir cámaras con información detallada
                for camera in cameras:
                    text = f"ðŸ“¹ Cámara {camera.index}: {camera.name} ({camera.width}x{camera.height})"
                    settings_page.camera_combo.addItem(text, camera.index)

                settings_page.camera_combo.setEnabled(True)
                self.logger.info(f"âœ“ {len(cameras)} cámara(s) detectada(s)")

                camera_list = "\n".join([f"â€¢ {c.name}" for c in cameras])
                QMessageBox.information(
                    settings_page,
                    "Cámaras Detectadas",
                    f"Se detectaron {len(cameras)} cámara(s):\n\n{camera_list}"
                )

        except Exception as e:
            self.logger.error(f"Error: {e}", exc_info=True)
            settings_page.camera_combo.clear()
            settings_page.camera_combo.addItem("âš ï¸ Error", -1)
            QMessageBox.critical(settings_page, "Error", f"Error detectando cámaras:\n\n{e}")

    def _load_hardware_settings(self):
        """Carga la configuración de hardware guardada en la UI."""
        settings_page = self.view.pages.get("settings")
        if not isinstance(settings_page, SettingsWidget):
            return

        # Llama a detectar cámaras para poblar el combo
        self._on_detect_cameras()

        # Selecciona la cámara guardada
        saved_index = int(self.model.db.config_repo.get_setting('camera_index', '0'))
        combo_index = settings_page.camera_combo.findData(saved_index)
        if combo_index != -1:
            settings_page.camera_combo.setCurrentIndex(combo_index)

    def _on_save_hardware_settings(self):
        """
        Guarda la configuración de hardware con validación robusta.
        Versión mejorada que valida la cámara antes de guardar.
        """
        settings_page = self.view.pages.get("settings")
        if not isinstance(settings_page, SettingsWidget):
            return

        selected_index = settings_page.camera_combo.currentData()

        # Validar que hay una selección válida
        if selected_index is None or selected_index < 0:
            self.view.show_message(
                "Error",
                "No hay una cámara válida seleccionada.",
                "warning"
            )
            return

        try:
            # Validar que la cámara funciona ANTES de guardar
            self.logger.info(f"Validando cámara {selected_index} antes de guardar...")

            is_valid, error_msg = self.camera_manager.validate_camera(selected_index)

            if not is_valid:
                self.logger.error(
                    f"La cámara seleccionada ({selected_index}) no es válida: {error_msg}"
                )

                QMessageBox.warning(
                    settings_page,
                    "Cámara No Válida",
                    f"La cámara seleccionada no funciona correctamente:\n\n{error_msg}\n\n"
                    "Por favor selecciona otra cámara o ejecuta la detección nuevamente."
                )
                return

            # Guardar la configuración
            self.model.db.config_repo.set_setting('camera_index', str(selected_index))
            camera_info = self.camera_manager.get_camera_info(selected_index)
            if camera_info:
                camera_type = "EXTERNA" if camera_info.is_external else "INTEGRADA"
                self.logger.info(
                    f"âœ“ Configuración guardada: Cámara {selected_index} - "
                    f"{camera_info.name} [{camera_type}]"
                )
            else:
                self.logger.info(f"âœ“ Configuración guardada: cámara {selected_index}")

            # Reinicializar el escáner con la nueva cámara
            old_scanner = self.qr_scanner
            self._initialize_qr_scanner()

            # Liberar el scanner anterior si existe
            if old_scanner and hasattr(old_scanner, 'release_camera'):
                try:
                    old_scanner.release_camera()
                except:
                    pass

            # Obtener info de la cámara para el mensaje
            camera_info = self.camera_manager.get_camera_info(selected_index)
            if camera_info:
                camera_type = "Externa (USB)" if camera_info.is_external else "Integrada"
                camera_desc = (
                    f"ðŸ“¹ {camera_info.name}\n"
                    f"ðŸ“Œ Tipo: {camera_type}\n"
                    f"ðŸ“ Resolución: {camera_info.width}x{camera_info.height}\n"
                    f"ðŸŽ¬ FPS: {camera_info.fps:.1f}"
                )
            else:
                camera_desc = f"Cámara {selected_index}"

            self.view.show_message(
                "Configuración Guardada",
                f"âœ“ Configuración de cámara guardada correctamente.\n\n"
                f"{camera_desc}\n\n"
                "El escáner QR se ha reiniciado con la nueva cámara.",
                "info"
            )

        except Exception as e:
            self.logger.error(f"Error guardando configuración de cámara: {e}", exc_info=True)

            QMessageBox.critical(
                settings_page,
                "Error",
                f"No se pudo guardar la configuración de cámara:\n\n{str(e)}\n\n"
                "Por favor intenta nuevamente."
            )

    def _on_test_camera(self):
        """
        Prueba la cámara seleccionada mostrando un preview temporal.
        Nuevo método para validar cámaras visualmente.
        """
        settings_page = self.view.pages.get("settings")
        if not isinstance(settings_page, SettingsWidget):
            return

        selected_index = settings_page.camera_combo.currentData()

        if selected_index is None or selected_index < 0:
            self.view.show_message(
                "Error",
                "Por favor selecciona una cámara primero.",
                "warning"
            )
            return

        # Obtener información de la cámara
        camera_info = self.camera_manager.get_camera_info(selected_index)
        if camera_info:
            camera_type = "Externa (USB)" if camera_info.is_external else "Integrada"
            camera_details = (
                f"ðŸ“¹ {camera_info.name}\n"
                f"ðŸ“Œ Tipo: {camera_type}\n"
                f"ðŸ“ Resolución: {camera_info.width}x{camera_info.height}\n"
                f"ðŸŽ¬ FPS: {camera_info.fps:.1f}"
            )
        else:
            camera_details = f"Cámara {selected_index}"

        # Confirmar con el usuario
        reply = QMessageBox.question(
            settings_page,
            "Probar Cámara",
            f"Â¿Deseas probar esta cámara?\n\n"
            f"{camera_details}\n\n"
            "Se mostrará una ventana de preview durante 5 segundos.\n"
            "Presiona ESC para cerrar antes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.logger.info(f"Iniciando preview de cámara {selected_index}")

            # Mostrar preview
            success = self.camera_manager.test_camera_with_preview(
                index=selected_index,
                duration=5.0
            )

            if success:
                # Obtener info actualizada
                camera_info = self.camera_manager.get_camera_info(selected_index)
                if camera_info:
                    camera_type = "Externa (USB)" if camera_info.is_external else "Integrada"
                    message = (
                        f"âœ“ La cámara funciona correctamente.\n\n"
                        f"ðŸ“¹ {camera_info.name}\n"
                        f"ðŸ“Œ Tipo: {camera_type}\n"
                        f"ðŸ“ Resolución: {camera_info.width}x{camera_info.height}\n\n"
                        "Puedes guardar esta configuración."
                    )
                else:
                    message = f"âœ“ La Cámara {selected_index} funciona correctamente.\n\nPuedes guardar esta configuración."

                QMessageBox.information(
                    settings_page,
                    "Test Exitoso",
                    message
                )
            else:
                camera_info = self.camera_manager.get_camera_info(selected_index)
                if camera_info and camera_info.error_message:
                    error_details = f"\n\nError: {camera_info.error_message}"
                else:
                    error_details = ""

                QMessageBox.warning(
                    settings_page,
                    "Test Fallido",
                    f"âœ— No se pudo obtener video de la Cámara {selected_index}.{error_details}\n\n"
                    "Posibles causas:\n"
                    "â€¢ La cámara está siendo usada por otra aplicación\n"
                    "â€¢ No tienes permisos para acceder a la cámara\n"
                    "â€¢ La cámara está desconectada o dañada\n\n"
                    "Por favor selecciona otra cámara."
                )

        except Exception as e:
            self.logger.error(f"Error probando cámara: {e}", exc_info=True)

            QMessageBox.critical(
                settings_page,
                "Error",
                f"Ocurrió un error al probar la cámara:\n\n{str(e)}"
            )

    # DELETED: Password management moved to WorkerController.


    def _connect_products_signals(self):
        self.product_controller._connect_products_signals()

    def _connect_fabrications_signals(self):
        """Conecta las señales del widget de gestión de Fabricaciones."""
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if isinstance(gestion_datos_page, GestionDatosWidget):
            fabrications_page = gestion_datos_page.fabricaciones_tab
            fabrications_page.search_entry.textChanged.connect(self.product_controller._on_fabrication_search_changed)
            fabrications_page.results_list.itemClicked.connect(self.product_controller._on_fabrication_result_selected) # Wait, is this right? Check ProductController
            fabrications_page.create_fabricacion_signal.connect(self.product_controller.show_create_fabricacion_dialog)
            fabrications_page.save_fabricacion_signal.connect(self.product_controller._on_update_fabricacion) # Check existence
            fabrications_page.delete_fabricacion_signal.connect(self.product_controller._on_delete_fabricacion) # Check existence
            fabrications_page.edit_preprocesos_signal.connect(self.product_controller.show_fabricacion_preprocesos)
            fabrications_page.edit_products_signal.connect(self.product_controller.show_fabricacion_products)
        self.logger.debug("Señales de 'Gestión Fabricaciones' conectadas.")

    def _connect_add_product_signals(self):
        add_prod_page = self.view.pages.get("add_product")
        if isinstance(add_prod_page, AddProductWidget):
            add_prod_page.save_button.clicked.connect(self.product_controller._on_save_product_clicked)
            add_prod_page.manage_subs_signal.connect(self.product_controller._on_manage_subs_for_new_product)
            add_prod_page.manage_procesos_signal.connect(self.product_controller._on_manage_procesos_for_new_product)
        self.logger.debug("Señales de 'Añadir Producto' conectadas.")

    def _connect_calculate_signals(self):
        """
        Conecta las señales del widget de cálculo.
        Si la UI no está inicializada, programa la conexión para después.
        """
        calc_page = self.view.pages.get("calculate")
        if not isinstance(calc_page, CalculateTimesWidget):
            self.logger.error("calc_page no es una instancia de CalculateTimesWidget")
            return

        # âœ… VERIFICAR si la UI está inicializada
        if not hasattr(calc_page, '_ui_setup_complete'):
            # La UI aún no se ha creado, conectar las señales después del primer showEvent
            self.logger.debug(
                "UI de CalculateTimesWidget no inicializada aún. Las señales se conectarán cuando se muestre el widget.")

            # Guardar una referencia al controlador para conectar después
            calc_page._pending_signal_connection = True
            return

        # âœ… VERIFICACIÃ“N ROBUSTA: Comprobar que los widgets existen y no han sido eliminados
        required_widgets = [
            'lote_search_entry', 'add_lote_button', 'remove_item_button',
            'define_flow_button',  # <-- AÃ‘ADIDO EL NUEVO BOTÃ“N
            'save_pila_button', 'load_pila_button', 'manage_bitacora_button',
            'export_button', 'export_pdf_button', 'export_log_button',
            'clear_button', 'go_home_button'
        ]

        for widget_name in required_widgets:
            if not hasattr(calc_page, widget_name):
                self.logger.error(f"Widget '{widget_name}' no existe en CalculateTimesWidget")
                return

            widget = getattr(calc_page, widget_name)
            if widget is None:
                self.logger.error(f"Widget '{widget_name}' es None")
                return

            # Verificar que el objeto C++ subyacente no ha sido eliminado
            try:
                widget.objectName()  # Esto fallará si el objeto C++ fue eliminado
            except RuntimeError:
                self.logger.error(f"Widget '{widget_name}' ha sido eliminado por Qt")
                return

        # Si llegamos aquí, todos los widgets son válidos
        try:
            calc_page.lote_search_entry.textChanged.connect(self.pila_controller._on_calc_lote_search_changed)
            calc_page.add_lote_button.clicked.connect(self.pila_controller._on_add_lote_to_pila_clicked)
            calc_page.remove_item_button.clicked.connect(self.pila_controller._on_remove_lote_from_pila_clicked)
            
            # Conectamos el nuevo botón a su futuro manejador
            calc_page.define_flow_button.clicked.connect(self.pila_controller._on_define_flow_clicked)
            # Botones de planificación manual/optimizador eliminados según solicitud

            calc_page.save_pila_button.clicked.connect(self.pila_controller._on_save_pila_clicked)
            calc_page.load_pila_button.clicked.connect(self.pila_controller._on_load_pila_clicked)
            calc_page.manage_bitacora_button.clicked.connect(self.pila_controller._on_ver_bitacora_pila_clicked)
            calc_page.export_button.clicked.connect(self._on_export_to_excel_clicked) # Export might still be in AppController
            calc_page.export_pdf_button.clicked.connect(self._on_export_gantt_to_pdf_clicked)
            calc_page.export_log_button.clicked.connect(self._on_export_audit_log)
            calc_page.clear_button.clicked.connect(self.pila_controller._on_clear_simulation)
            calc_page.go_home_button.clicked.connect(self._on_go_home_and_reset_calc)
            self.model.pilas_changed_signal.connect(lambda title, msg: self.view.show_message(title, msg, "info"))

            # Marcar que las señales ya están conectadas
            calc_page._signals_connected = True
            self.logger.debug("✅ Señales de 'Calcular Tiempos' conectadas correctamente.")
        except RuntimeError as e:
            self.logger.error(f"Error de runtime conectando señales: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Error inesperado: {e}", exc_info=True)

    def _update_lote_content_table(self):
        """Refresca la tabla de contenido del lote en la UI."""
        calc_page = self.view.pages.get("calculate")
        if not isinstance(calc_page, CalculateTimesWidget):
            return

        calc_page.lote_content_table.setRowCount(0)  # Limpiar tabla
        for row, item in enumerate(self.current_lote_content):
            calc_page.lote_content_table.insertRow(row)

            # Columna 0: Código
            item_code = QTableWidgetItem(item.get("codigo"))
            item_code.setData(Qt.ItemDataRole.UserRole, item)  # Guardamos todo el dict en el item
            calc_page.lote_content_table.setItem(row, 0, item_code)

            # Columna 1: Descripción
            calc_page.lote_content_table.setItem(row, 1, QTableWidgetItem(item.get("descripcion")))

            # Columna 2: Cantidad (editable)
            qty_spinbox = QSpinBox()
            qty_spinbox.setRange(1, 99999)
            qty_spinbox.setValue(item.get("cantidad", 1))
            # Conectamos una señal para actualizar el dato si el usuario cambia la cantidad
            qty_spinbox.valueChanged.connect(
                lambda value, r=row: self.current_lote_content[r].update({"cantidad": value}))
            calc_page.lote_content_table.setCellWidget(row, 2, qty_spinbox)

            # Columna 3: Origen
            calc_page.lote_content_table.setItem(row, 3, QTableWidgetItem(item.get("origen")))









    def _clear_canvas_and_reset(self):
        """
        Limpia completamente el canvas, eliminando todas las tareas y conexiones,
        y resetea el panel inspector a su estado inicial.
        """
        self.logger.info("Limpiando el canvas del editor visual.")

        # 1. Eliminar todos los widgets (tarjetas) del canvas
        for task in self.canvas_tasks:
            task['widget'].deleteLater()  # Método seguro para eliminar widgets en Qt

        # 2. Limpiar las listas de datos y el estado de selección
        self.canvas_tasks = []
        self.selected_canvas_task_index = None

        # 3. Limpiar las conexiones en el widget del canvas
        if hasattr(self, 'canvas'):
            self.canvas.set_connections([])  # Le pasamos una lista vacía

        # 4. Limpiar y mostrar el placeholder del panel inspector
        while self.inspector_layout.count():
            child = self.inspector_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)  # Oculta el widget actual del inspector

        placeholder_label = QLabel(
            "PANEL INSPECTOR\n\nEl flujo ha sido limpiado. "
            "Arrastra una tarea desde la biblioteca para empezar de nuevo."
        )
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setWordWrap(True)
        placeholder_label.setStyleSheet("color: #777;")
        self.inspector_layout.addWidget(placeholder_label)

    def _handle_clear_visual_editor(self, flow_dialog):
        """
        Gestiona la limpieza completa del editor visual y resetea el estado en el controlador.
        """
        # 1. Resetear el estado guardado en el controlador
        self.logger.info("Borrando el estado de la simulación y el flujo de producción.")
        self.last_production_flow = None
        self.last_simulation_results = None
        self.last_audit_log = None
        self.last_units_calculated = 1

        # 2. Llamar al método del diálogo para que se limpie visualmente
        if flow_dialog:
            flow_dialog._clear_canvas_and_reset()

        self.view.show_message("Lienzo Limpio", "Puedes empezar a construir un nuevo flujo de producción.", "info")

    def _on_go_home_and_reset_calc(self):
        """Limpia la simulación y vuelve a la pantalla de inicio."""
        self.logger.info("El usuario solicitó volver al inicio desde la pantalla de cálculo.")

        # 1. Reutilizamos la lógica de limpieza existente para refrescar la sección
        self._on_clear_simulation()

        # 2. Reutilizamos la lógica de navegación para cambiar a la página de inicio
        self._on_nav_button_clicked("home")

    def _on_export_audit_log(self):
        """Exporta el contenido del log de auditoría a un archivo de texto."""
        self.logger.info("Exportando log de auditoría...")
        calc_page = self.view.pages.get("calculate")
        if not isinstance(calc_page, CalculateTimesWidget) or not calc_page.last_audit:
            self.view.show_message("Sin Datos", "No hay un log de auditoría para exportar.", "warning")
            return

        log_content_html = calc_page.audit_log_display.toHtml()

        # Guardar como HTML para preservar el formato
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Guardar Log de Auditoría",
            "Log_Auditoria.html",
            "Archivos HTML (*.html);;Todos los archivos (*.*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(log_content_html)
            self.view.show_message("Éxito", f"Log de auditoría guardado en:\n{file_path}", "info")
        except Exception as e:
            self.logger.error(f"Error al guardar el log de auditoría: {e}", exc_info=True)
            self.view.show_message("Error", f"No se pudo guardar el archivo: {e}", "critical")

    def _map_task_keys(self, original_task, units):
        """
        Mapea y normaliza una tarea al formato estándar del scheduler.
        Esta versión es robusta y previene errores por datos faltantes.
        """
        # 1. Búsqueda segura del tiempo de la tarea
        # -------------------------------------------
        ## Se define una lista de posibles nombres para la clave de tiempo.
        ## Esto hace la función compatible con diferentes partes del código
        ## que puedan usar 'tiempo', 'duration', etc.
        time_keys_priority = ['duration', 'duration_per_unit', 'tiempo', 'tiempo_optimo']
        time_value = 0.0

        ## Se itera sobre las claves prioritarias. En cuanto se encuentra un
        ## valor de tiempo válido y positivo, se detiene la búsqueda.
        for key in time_keys_priority:
            if key in original_task and original_task[key] is not None:
                try:
                    # Se asegura de que el valor sea un string y reemplaza comas por puntos
                    # para una conversión a float segura.
                    val = str(original_task[key]).replace(",", ".")
                    parsed_time = float(val)

                    # Se asegura de que el tiempo sea positivo. Tiempos de cero o negativos
                    # romperían la lógica de la simulación.
                    if parsed_time > 0:
                        time_value = parsed_time
                        break  # Detiene el bucle al encontrar un tiempo válido.
                except (ValueError, TypeError):
                    # Si el valor no es un número (ej. texto vacío),
                    # simplemente continúa al siguiente intento sin fallar.
                    continue

        ## Si después de todos los intentos el tiempo sigue siendo cero, se registra una
        ## advertencia detallada. Este log es tu mejor herramienta para encontrar
        ## qué tarea específica está llegando sin datos de tiempo.
        if time_value <= 0:
            self.logger.warning(
                f"âš ï¸ La tarea '{original_task.get('name', original_task.get('descripcion'))}' "
                f"tiene un tiempo por unidad de 0 o inválido. Datos recibidos: {original_task}"
            )

        # 2. Construcción del diccionario de la tarea normalizada
        # --------------------------------------------------------
        ## Se usan operadores 'or' para crear "fallbacks" o valores por defecto.
        ## Si una clave no existe, en lugar de fallar, usa el siguiente valor.
        ## Esto previene errores de tipo 'NoneType' en el motor de simulación.
        mapped_task = {
            'id': original_task.get('id') or f"task_{id(original_task)}",
            'name': (
                    original_task.get('name') or
                    original_task.get('descripcion') or
                    'Tarea sin nombre'
            ),

            ## CRÃTICO: Se asigna el time_value (que podría ser 0.0 si no se encontró)
            ## a AMBOS campos de duración para máxima compatibilidad con el resto del sistema.
            'duration': time_value,
            'duration_per_unit': time_value,

            'trigger_units': units,
            'is_unit_task': True,

            'department': (
                    original_task.get('department') or
                    original_task.get('departamento') or
                    'General'
            ),
            'required_skill_level': (
                    original_task.get('required_skill_level') or
                    original_task.get('tipo_trabajador') or
                    1
            ),
            'original_product_code': (
                    original_task.get('codigo') or
                    original_task.get('original_product_code') or
                    'N/A'
            ),
            'fabricacion_id': original_task.get('fabricacion_id') or 'N/A',
            'deadline': original_task.get('deadline'),
            'original_product_info': original_task.get('original_product_info') or {
                'desc': original_task.get('descripcion') or 'Sin descripción'
            },
            'requiere_maquina_tipo': original_task.get('requiere_maquina_tipo'),
        }

        return mapped_task

    def _handle_save_pila_from_visual_editor(self, flow_dialog):
        """
        Gestiona el guardado de una pila directamente desde el editor visual,
        reconstruyendo los datos necesarios a partir del flujo.
        """
        self.logger.info("Iniciando guardado de pila desde el editor visual.")

        # 1. Obtener el flujo de producción actual del diálogo
        production_flow = flow_dialog.get_production_flow()
        if not production_flow:
            self.view.show_message("Flujo Vacío", "No hay pasos en el flujo de producción para guardar.", "warning")
            return

        # 2. Pedir al usuario un nombre y descripción para la pila
        dialog = SavePilaDialog(self.view)
        if not dialog.exec():
            self.logger.info("El usuario canceló el guardado de la pila.")
            return

        nombre, descripcion = dialog.get_data()
        if not nombre:
            self.view.show_message("Nombre Requerido", "El nombre de la pila es obligatorio.", "warning")
            return

        # 3. Reconstruir la 'pila_de_calculo' a partir del flujo visual
        # Esto es crucial para saber qué productos y fabricaciones componen la pila
        pila_de_calculo_reconstruida = {"productos": {}, "fabricaciones": {}}
        for step in production_flow:
            task_info = step.get('task', {})
            original_code = task_info.get('original_product_code', '')
            if not original_code:
                continue

            # Asumimos que si no es un preproceso, es un producto
            if "PREP_" not in original_code:
                pila_de_calculo_reconstruida['productos'][original_code] = {
                    "codigo": original_code,
                    "descripcion": task_info.get('original_product_info', {}).get('desc', 'Producto Desconocido')
                }
            # (En el futuro se podría añadir lógica para fabricaciones si fuera necesario)

        # 4. Llamar al método del modelo para guardar los datos.
        #    Como es un guardado de "plantilla", los resultados de simulación van vacíos.
        self.model.save_pila(
            nombre=nombre,
            descripcion=descripcion,
            pila_de_calculo=pila_de_calculo_reconstruida,
            production_flow=production_flow,
            simulation_results=[],  # No hay simulación al guardar solo el flujo
            producto_origen_codigo=None
            # La unidad se guardará con el valor por defecto en el método del modelo
        )

    def _handle_load_pila_into_visual_editor(self, flow_dialog):
        """
        Gestiona la carga de una pila guardada y la dibuja en el editor visual existente.
        """
        pilas_list = self.model.pila_repo.get_all_pilas()
        if not pilas_list:
            self.view.show_message("Sin Datos", "No hay pilas guardadas para cargar.", "info")
            return

        # 1. Mostrar el diálogo para seleccionar qué pila cargar
        dialog = LoadPilaDialog(pilas_list, self.view)
        if not dialog.exec() or dialog.get_selected_id() is None:
            return

        # 2. Manejar la solicitud de eliminación (si aplica)
        if dialog.delete_requested:
            pila_id_to_delete = dialog.get_selected_id()
            if self.view.show_confirmation_dialog("Confirmar", "Â¿Seguro que desea eliminar esta pila?"):
                self.model.delete_pila(pila_id_to_delete)
            return

        # 3. Cargar los datos de la pila desde la base de datos
        pila_id = dialog.get_selected_id()
        self.logger.info(f"Cargando datos de la Pila ID: {pila_id} para el editor visual.")
        meta_data, _, production_flow, _ = self.model.pila_repo.load_pila(pila_id)

        if not meta_data or not production_flow:
            self.view.show_message("Error de Carga",
                                   "La pila seleccionada no contiene un flujo de producción válido.",
                                   "critical")
            return

        # 4. Llamar al método del diálogo visual para que se "pinte" a sí mismo con el flujo
        try:
            flow_dialog._load_flow_onto_canvas(production_flow)
            self.view.show_message("Pila Cargada",
                                   f"Se ha cargado el flujo de '{meta_data.get('nombre')}'. Ahora puedes editarlo y recalcularlo.",
                                   "info")
        except Exception as e:
            self.logger.critical(f"Error al intentar dibujar el flujo cargado en el canvas: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error al visualizar la pila cargada: {e}",
                                   "critical")

    def _on_define_flow_clicked(self):
        """
        Abre el diálogo visual para definir/editar el flujo de producción
        y conecta todos sus botones de acción al controlador.
        """
        self.logger.info("Iniciando el proceso de definición de flujo de producción.")
        calc_page = self.view.pages.get("calculate")
        if not calc_page or not calc_page.planning_session:
            self.view.show_message("Pila Vacía", "Añada al menos un Lote a la Pila antes de definir el flujo.",
                                   "warning")
            return

        try:
            tasks_data = self.model.get_data_for_calculation_from_session(calc_page.planning_session)
            if not tasks_data:
                self.view.show_message("Error de Datos",
                                       "No se pudieron obtener los detalles de las tareas para la pila actual.",
                                       "critical")
                return

            workers_data = self.model.get_all_workers(include_inactive=False)
            worker_names = [w.nombre_completo for w in workers_data]
            units_for_dialog = calc_page.planning_session[0].get("unidades", 1) if calc_page.planning_session else 1

            flow_dialog = EnhancedProductionFlowDialog(tasks_data, worker_names, units_for_dialog, self,
                                                       self.schedule_manager, parent=self.view,
                                                       existing_flow=self.last_production_flow)

            # Conectar todos los botones del diálogo a sus funciones manejadoras
            flow_dialog.load_pila_button.clicked.connect(
                lambda: self._handle_load_pila_into_visual_editor(flow_dialog)
            )
            flow_dialog.save_pila_button.clicked.connect(
                lambda: self._handle_save_pila_from_visual_editor(flow_dialog)
            )
            flow_dialog.clear_button.clicked.connect(
                lambda: self._handle_clear_visual_editor(flow_dialog)
            )
            flow_dialog.manual_calc_button.clicked.connect(
                lambda: self._handle_run_manual_from_visual_editor(flow_dialog)
            )
            flow_dialog.optimizer_calc_button.clicked.connect(
                lambda: self._handle_run_optimizer_from_visual_editor(flow_dialog)
            )

            if not flow_dialog.exec():
                self.logger.info("El usuario canceló la definición del flujo.")
                return

            production_flow = flow_dialog.get_production_flow()
            self.last_production_flow = production_flow

            if self.last_production_flow:
                self.logger.info(f"Flujo de producción definido con {len(self.last_production_flow)} pasos.")
                self.view.show_message("Flujo Definido",
                                       "El flujo de producción ha sido definido. Ahora puede ejecutar un cálculo desde esta misma ventana.",
                                       "info")
            else:
                self.logger.warning("No se definió ningún flujo de producción.")

        except Exception as e:
            self.logger.critical(f"Error crítico durante la definición del flujo: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error inesperado al definir el flujo: {e}",
                                   "critical")

    def _on_run_manual_plan_clicked(self):
        """
        Ejecuta una simulación manual utilizando el flujo de producción
        previamente definido por el usuario (desde el editor visual).
        Versión CORREGIDA: Ya no pide unidades/fechas globales.
        """
        self.logger.info("ðŸ”µ Iniciando flujo de planificación manual con flujo visual.")
        calc_page = self.view.pages.get("calculate")
        if not isinstance(calc_page, CalculateTimesWidget):
            self.logger.error("Widget CalculateTimesWidget no encontrado.")
            return  # Salir si no se encuentra la página

        # --- VERIFICACIÃ“N CLAVE ---
        # Ahora es REQUISITO que el flujo haya sido definido previamente.
        if not self.last_production_flow:
            self.view.show_message(
                "Flujo no Definido",
                "Debe pulsar 'Definir Flujo de Producción' y configurar la secuencia de tareas "
                "antes de ejecutar un cálculo manual.",
                "warning"
            )
            return

        self.logger.info(
            f"ðŸ”µ Usando 'last_production_flow' con {len(self.last_production_flow)} pasos."
        )

        try:
            # El flujo ya está listo en self.last_production_flow,
            # incluyendo las unidades correctas por tarea/entrega.
            production_flow = self.last_production_flow

            # Iniciar feedback visual al usuario
            self.view.statusBar().showMessage("Construyendo plan de tareas...")
            calc_page.show_progress()  # Muestra la barra de progreso
            QApplication.processEvents()  # Asegura que la UI se actualice

            # Obtener datos de trabajadores y máquinas (sin cambios)
            workers_data = self.model.get_all_workers(include_inactive=False)
            # Asegúrate de obtener habilidad (índice 4)
            # DTO refactor: user attributes instead of index
            worker_names_and_skills = [(w.nombre_completo, w.tipo_trabajador) for w in workers_data]
            all_machines_data = self.model.get_all_machines(include_inactive=False)
            # Ahora usamos atributos DTO: id, nombre
            machines_dict = {m.id: m.nombre for m in all_machines_data}

            # 1. Crear la instancia del calculador de tiempos (sin cambios)
            time_calculator = CalculadorDeTiempos(self.schedule_manager)

            # 2. Crear el AdaptadorScheduler pasando el flujo directamente (sin cambios)
            # El adaptador ya sabe cómo interpretar las 'trigger_units' de cada paso.
            scheduler = AdaptadorScheduler(
                production_flow=production_flow,
                all_workers_with_skills=worker_names_and_skills,
                available_machines=machines_dict,
                schedule_config=self.schedule_manager,
                time_calculator=time_calculator,
                # Usar la fecha/hora actual como inicio por defecto para el cálculo manual
                start_date=datetime.now()
            )
            self.logger.info("ðŸ”µ AdaptadorScheduler creado correctamente para cálculo manual.")

            # 3. Iniciar la simulación en un hilo (sin cambios)
            self._start_simulation_thread(scheduler)
            self.logger.info("ðŸ”µ Hilo de simulación iniciado.")

        except Exception as e:
            self.logger.critical(f"Error crítico en el flujo de planificación manual: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error inesperado al iniciar el cálculo: {e}",
                                   "critical")
            # Asegurarse de ocultar el progreso en caso de error
            calc_page.hide_progress()

    def _on_clear_simulation(self):
        """Limpia la vista de cálculo, resetea el flujo de producción y el estado de los botones."""
        self.logger.info("Limpiando la vista de cálculo y reseteando el flujo de producción.")

        # 1. Resetear el estado del flujo de producción guardado en el controlador
        self.last_production_flow = None

        calc_page = self.view.pages.get("calculate")
        if isinstance(calc_page, CalculateTimesWidget):
            # 2. Llamar al método del widget para que limpie toda su UI y estado interno
            calc_page.clear_all()

            # 3. Asegurarse de que todos los botones de acción queden deshabilitados
            calc_page.define_flow_button.setEnabled(False)
            calc_page.execute_manual_button.setEnabled(False)
            calc_page.execute_optimizer_button.setEnabled(False)

        self.view.show_message("Listo", "Puede definir un nuevo Plan de Producción.", "info")

    def _on_optimize_by_deadline_clicked(self):
        """
        Inicia el flujo de optimización para encontrar el número de trabajadores
        necesarios para cumplir un plazo.
        """
        self.logger.info("Iniciando flujo de optimización por fecha límite.")
        calc_page = self.view.pages.get("calculate")
        if not calc_page or not calc_page.planning_session:
            self.view.show_message("Pila Vacía", "Añada al menos un Lote a la Pila antes de optimizar.", "warning")
            return

        # 1. Pedir al usuario la fecha de inicio y fin
        dialog = GetOptimizationParametersDialog(self.view)
        if not dialog.exec():
            return

        params = dialog.get_parameters()
        start_date = datetime.combine(params["start_date"], time(7, 0))  # Empezar al inicio del día
        end_date = params["end_date"]

        # Actualizar las unidades en la sesión de planificación desde el diálogo
        for item in calc_page.planning_session:
            item['unidades'] = params['units']
        calc_page._update_plan_display()

        self.view.statusBar().showMessage("Iniciando optimización, por favor espere...")
        calc_page.show_progress()

        # âœ… CORRECCIÃ“N: Verificar si hay un production_flow cargado
        production_flow_to_use = self.last_production_flow if self.last_production_flow else None

        if production_flow_to_use:
            self.logger.info(f"ðŸ”„ Usando production_flow cargado con {len(production_flow_to_use)} pasos")
        else:
            self.logger.info("âš ï¸ No hay production_flow cargado, se reconstruirá desde la base de datos")

        # 2. Crear y ejecutar el Optimizer en un hilo
        try:
            # âœ… CORRECCIÃ“N CRÃTICA: Pasar el production_flow como cuarto parámetro
            optimizer = Optimizer(
                calc_page.planning_session,
                self.model,
                self.schedule_manager,
                production_flow_override=production_flow_to_use  # â† LÃNEA AÃ‘ADIDA
            )

            self.thread = QThread()
            self.worker = self.OptimizerWorker(optimizer, start_date, end_date)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self._on_optimization_finished)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()
        except Exception as e:
            self.logger.critical(f"Error al iniciar el optimizador: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"No se pudo iniciar la optimización: {e}", "critical")
            calc_page.hide_progress()

    def _handle_run_manual_from_visual_editor(self, flow_dialog):
        """
        Ejecuta una simulación manual utilizando el flujo de producción
        directamente desde el editor visual.
        CORREGIDO: Asigna trabajadores automáticamente si no están definidos.
        """
        self.logger.info("Iniciando flujo de planificación manual desde el editor visual.")

        raw_production_flow = flow_dialog.get_production_flow()
        if not raw_production_flow:
            self.view.show_message("Flujo no Definido", "No hay un flujo para calcular.", "warning")
            return

        try:
            self.view.statusBar().showMessage("Construyendo plan de tareas...")
            # --- CORRECCIÃ“N: Usar QApplication desde PyQt6.QtWidgets ---
            from PyQt6.QtWidgets import \
                QApplication  # Asegúrate que QApplication esté importado arriba si no lo está
            QApplication.processEvents()

            processed_production_flow = raw_production_flow

            # Obtener trabajadores ordenados por habilidad (descendente)
            all_workers = self.model.get_all_workers(include_inactive=False)
            # Ordenar por habilidad (tipo_trabajador), de mayor a menor
            sorted_workers = sorted(all_workers, key=lambda w: w.tipo_trabajador, reverse=True)

            # âœ… CORRECCIÃ“N: Asignar trabajadores a TODAS las tareas sin trabajador asignado
            for step in processed_production_flow:
                # Verificar si 'workers' está vacío, no existe, o es una lista vacía
                workers_in_step = step.get('workers')  # Obtener lista o None
                if not workers_in_step:  # Cubre None y lista vacía []
                    # Asegurarse de que 'task' existe y tiene 'required_skill_level'
                    task_data = step.get('task', {})
                    required_skill = task_data.get('required_skill_level', 1)  # Default a 1 si no existe

                    # Buscar el primer trabajador con habilidad suficiente
                    assigned_worker = None
                    for worker in sorted_workers:
                        # worker es un WorkerDTO con atributos: id, nombre_completo, activo, notas, tipo_trabajador
                        if worker.tipo_trabajador >= required_skill:
                            assigned_worker = worker
                            break  # Encontramos uno, salimos del bucle

                    if assigned_worker:
                        worker_name = assigned_worker.nombre_completo
                        # âœ… Asignar en el formato correcto: lista de diccionarios
                        step['workers'] = [{'name': worker_name}]
                        self.logger.info(
                            f"Asignación automática: Trabajador '{worker_name}' â†’ '{task_data.get('name', 'Tarea desconocida')}'"
                        )
                    else:
                        # âš ï¸ Advertencia: No hay trabajador cualificado disponible
                        self.logger.error(
                            f"âŒ No se encontró trabajador con habilidad >= {required_skill} "
                            f"para la tarea '{task_data.get('name', 'Tarea desconocida')}'. Esta tarea NO podrá ejecutarse."
                        )
                        # âœ… Asignar lista vacía explícitamente para evitar errores posteriores
                        step['workers'] = []

            # Preparar datos para el scheduler (sin cambios)
            workers_data = self.model.get_all_workers(include_inactive=False)
            # Asegurarse de obtener habilidad (índice 4)
            worker_names_and_skills = [(w.nombre_completo, w.tipo_trabajador) for w in workers_data]
            all_machines_data = self.model.get_all_machines(include_inactive=False)
            # Ahora usamos atributos DTO: id, nombre
            machines_dict = {m.id: m.nombre for m in all_machines_data}

            # Crear el calculador de tiempos (sin cambios)
            from time_calculator import CalculadorDeTiempos  # Asegúrate que esté importado
            time_calculator = CalculadorDeTiempos(self.schedule_manager)

            # Crear el adaptador del scheduler
            from simulation_adapter import AdaptadorScheduler  # Asegúrate que esté importado
            scheduler = AdaptadorScheduler(
                production_flow=processed_production_flow,
                all_workers_with_skills=worker_names_and_skills,
                available_machines=machines_dict,
                schedule_config=self.schedule_manager,
                time_calculator=time_calculator,
                start_date=datetime.now(),
                # NUEVO: Pasar referencia al diálogo para visualización (Fase 8.5)
                visual_dialog_reference=flow_dialog
            )
            self.logger.info("AdaptadorScheduler creado con referencia al diálogo visual.")  # Log añadido

            # Iniciar la simulación en un hilo separado (sin cambios)
            self._start_simulation_thread(scheduler)
            self.logger.info("Simulación manual iniciada desde el editor visual.")  # Log añadido

        except Exception as e:
            self.logger.critical(f"Error crítico en el flujo de planificación manual desde editor: {e}",
                                 exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error inesperado al iniciar el cálculo manual: {e}",
                                   "critical")

    def _handle_run_optimizer_from_visual_editor(self, flow_dialog):
        """
        Inicia el flujo de optimización usando el flujo del editor visual
        y la pila de cálculo de la página principal.
        """
        self.logger.info("Iniciando flujo de optimización desde el editor visual.")

        # 1. Obtener el flujo de producción del diálogo
        production_flow = flow_dialog.get_production_flow()
        if not production_flow:
            self.view.show_message("Flujo no Definido", "No hay un flujo de producción en el editor para optimizar.",
                                   "warning")
            return

        # 2. Obtener la pila de cálculo (los productos a fabricar) de la página principal
        calc_page = self.view.pages.get("calculate")
        if not calc_page or not calc_page.planning_session:
            self.view.show_message("Pila Vacía",
                                   "La pila de producción de la página principal está vacía. Añada lotes para poder optimizar.",
                                   "warning")
            return

        # 3. Pedir parámetros de optimización (sin cambios)
        dialog = GetOptimizationParametersDialog(self.view)
        if not dialog.exec():
            self.logger.info("Optimización cancelada por el usuario.")  # Log añadido
            return

        params = dialog.get_parameters()
        start_date = datetime.combine(params["start_date"], time(7, 0))  # Hora de inicio por defecto
        end_date = params["end_date"]
        units_to_produce = params['units']  # Guardar unidades

        # Actualizar unidades en la sesión de planificación (sin cambios)
        for item in calc_page.planning_session:
            item['unidades'] = units_to_produce
        calc_page._update_plan_display()  # Actualizar UI

        # Mostrar feedback al usuario (sin cambios)
        self.view.statusBar().showMessage("Iniciando optimización, por favor espere...")
        # --- CORRECCIÃ“N: Usar QApplication desde PyQt6.QtWidgets ---
        from PyQt6.QtWidgets import QApplication  # Asegúrate que QApplication esté importado
        QApplication.processEvents()

        try:
            # 4. Crear instancia del Optimizer
            # Â¡IMPORTANTE! Pasamos el `production_flow` del editor visual al Optimizer
            # y también la referencia al diálogo visual.
            optimizer = Optimizer(
                planning_session=calc_page.planning_session,
                model=self.model,
                schedule_config=self.schedule_manager,
                production_flow_override=production_flow,
                # NUEVO: Pasar referencia al diálogo para visualización (Fase 8.5)
                visual_dialog_reference=flow_dialog
            )
            self.logger.info("Instancia de Optimizer creada con flujo y referencia al diálogo.")  # Log añadido

            # 5. Configurar e iniciar el hilo del worker (sin cambios)
            self.thread = QThread()
            # Pasar las unidades correctas al worker
            self.worker = self.OptimizerWorker(optimizer, start_date, end_date, units_to_produce)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self._on_optimization_finished)
            # --- CORRECCIÃ“N: Conectar deleteLater a finished ---
            # Asegura que los objetos se limpien después de que el hilo termine
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.quit)  # Asegurar que el hilo se detenga
            self.thread.finished.connect(self.thread.deleteLater)  # Limpiar el hilo

            self.thread.start()
            self.logger.info("Hilo de optimización iniciado.")  # Log añadido

        except Exception as e:
            self.logger.critical(f"Error crítico al iniciar el optimizador desde editor visual: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"No se pudo iniciar la optimización: {e}", "critical")
            # Asegurarse de ocultar el progreso si falla al inicio
            if calc_page:
                calc_page.hide_progress()

    def _on_optimization_finished(self, results, audit, workers_needed):
        """
        Se ejecuta cuando el OptimizerWorker ha terminado su cálculo.
        """
        self.logger.info(
            f"Controlador: Hilo de optimización finalizado. Se necesitan {workers_needed} trabajadores flexibles.")
        calc_page = self.view.pages.get("calculate")
        calc_page.hide_progress()

        if results:
            # Guardar los resultados para poder generar informes
            self.last_simulation_results = results
            self.last_audit_log = audit
            self.last_flexible_workers_needed = workers_needed

            # Mostrar los resultados en la UI
            self.view.display_simulation_results(results, audit)

            # Informar al usuario del resultado
            self.view.show_message(
                "Optimización Completa",
                f"Para cumplir con los plazos, se necesitan **{workers_needed}** trabajador(es) flexible(s) adicionales.",
                "info"
            )
        else:
            self.view.show_message("Optimización Fallida",
                                   "No se pudo encontrar una planificación viable, incluso con trabajadores adicionales. Revise los plazos o la estructura de tareas.",
                                   "critical")

        # Limpieza del hilo
        if self.thread:
            self.thread.quit()
            self.thread.wait()

    def _save_chunk_results(self, chunk_index, results, audit):
        """Guarda los resultados de un lote en un archivo JSON temporal."""
        import json
        # ===== INICIO DE LA MODIFICACIÃ“N =====
        # Añadimos Enum a los imports necesarios para el serializador
        from enum import Enum
        from calculation_audit import DecisionStatus
        # =====================================

        # Convertir objetos datetime y Enum a strings para que sean serializables
        def default_serializer(o):
            if isinstance(o, (datetime, date)):
                return o.isoformat()
            # ===== LÃNEA AÃ‘ADIDA PARA CORREGIR EL TypeError =====
            if isinstance(o, Enum):
                return o.value
            # ====================================================
            raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

        temp_dir = "temp_chunks"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, f"chunk_{chunk_index}.json")

        data_to_save = {
            "results": results,
            "audit": [vars(a) for a in audit]  # Convertir dataclasses a dicts
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, default=default_serializer)

        self.logger.info(f"Lote {chunk_index} guardado en {file_path}")
        return file_path

    def _consolidate_chunk_results(self, temp_files):
        """Lee todos los archivos de lotes temporales y los une en un resultado final."""
        import json
        from calculation_audit import CalculationDecision, DecisionStatus

        all_results = []
        all_audit_dicts = []

        # Convertir strings de vuelta a objetos datetime
        def datetime_parser(json_dict):
            for key, value in json_dict.items():
                if isinstance(value, str):
                    try:
                        # Intentar convertir strings que parezcan fechas
                        json_dict[key] = datetime.fromisoformat(value)
                    except (ValueError, TypeError):
                        pass
            return json_dict

        for file_path in temp_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f, object_hook=datetime_parser)
                all_results.extend(data.get("results", []))
                all_audit_dicts.extend(data.get("audit", []))

        # Reconstruir los objetos CalculationDecision desde los diccionarios
        final_audit = []
        for audit_dict in all_audit_dicts:
            # Convertir el string de status de vuelta a un objeto Enum
            status_str = audit_dict.get('status')
            if status_str in DecisionStatus._value2member_map_:
                audit_dict['status'] = DecisionStatus(status_str)
            else:
                audit_dict['status'] = DecisionStatus.NEUTRAL

            final_audit.append(CalculationDecision(**audit_dict))

        self.logger.info(f"Consolidados {len(all_results)} resultados y {len(final_audit)} eventos de auditoría.")
        return all_results, final_audit






    def _connect_historial_signals(self):
        historial_page = self.view.pages.get("historial")
        if isinstance(historial_page, HistorialWidget):
            historial_page.mode_changed_signal.connect(self.update_historial_view)
            historial_page.item_selected_signal.connect(self._on_historial_item_selected)
            historial_page.search_text_changed_signal.connect(self._populate_historial_list)
            historial_page.filter_changed_signal.connect(self._populate_historial_list)
            historial_page.calendar_date_selected_signal.connect(self._on_historial_calendar_clicked)
            historial_page.print_report_signal.connect(self._on_print_historial_report_clicked)
        self.logger.debug("Señales de 'Historial' conectadas.")

    def _connect_definir_lote_signals(self):
        """Conecta las señales del widget para definir plantillas de Lote."""
        lote_page = self.view.pages.get("definir_lote")
        if not isinstance(lote_page, DefinirLoteWidget):
            return

        # Conectar buscadores
        lote_page.product_search.textChanged.connect(self.pila_controller._on_lote_def_product_search_changed)
        lote_page.fab_search.textChanged.connect(self.pila_controller._on_lote_def_fab_search_changed)

        # Conectar botones de añadir/quitar
        lote_page.add_product_button.clicked.connect(self.pila_controller._on_add_product_to_lote_template)
        lote_page.add_fab_button.clicked.connect(self.pila_controller._on_add_fab_to_lote_template)
        lote_page.remove_item_button.clicked.connect(self.pila_controller._on_remove_item_from_lote_template)
        lote_page.new_button.clicked.connect(lote_page.clear_form)
        lote_page.save_button.clicked.connect(self.pila_controller._on_save_lote_template_clicked)

        # La señal del botón de guardado la conectaremos más adelante
        self.logger.debug("Señales de 'Definir Lote' conectadas.")

    # DELETED: Lote definition logic moved to PilaController.


    def _connect_lotes_management_signals(self):
        self.pila_controller._connect_lotes_management_signals()

    # DELETED: Lote management logic moved to PilaController.


    def _on_manage_procesos_for_new_product(self, current_procesos):
        add_product_page = self.view.pages["add_product"]

        dialog = ProcesosMecanicosDialog(current_procesos, self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_procesos = dialog.get_updated_procesos_mecanicos()
            add_product_page.procesos_mecanicos_temp = updated_procesos



    def _on_report_result_selected(self, item):
        result_data = item.data(Qt.ItemDataRole.UserRole)
        self.selected_report_item = result_data
        reportes_page = self.view.pages.get("reportes")

        # Limpiar botones existentes
        for i in reversed(range(reportes_page.reports_buttons_layout.count())):
            reportes_page.reports_buttons_layout.itemAt(i).widget().setParent(None)

        if result_data['type'] == 'Producto':
            codigo = result_data['code']
            btn = QPushButton(f"ðŸ“Š Historial de Iteraciones (PDF) para {codigo}")
            reportes_page.reports_buttons_layout.addWidget(btn)
            btn.clicked.connect(lambda: self._on_generar_informe_clicked('historial_iteraciones'))

        elif result_data['type'] == 'Pila':
            pila_id = result_data['id']
            btn1 = QPushButton(f"ðŸ­ Informe de Pila (Excel) para {result_data['code']}")
            btn2 = QPushButton(f"ðŸ“‹ Historial de Pila (PDF) para {result_data['code']}")
            reportes_page.reports_buttons_layout.addWidget(btn1)
            reportes_page.reports_buttons_layout.addWidget(btn2)
            btn1.clicked.connect(lambda: self._on_generar_informe_clicked('pila_fabricacion_excel', pila_id))
            btn2.clicked.connect(lambda: self._on_generar_informe_clicked('historial_pila_pdf', pila_id))

    def _connect_reportes_signals(self):
        reportes_page = self.view.pages.get("reportes")
        if isinstance(reportes_page, ReportesWidget):
            reportes_page.search_entry.textChanged.connect(self._on_report_search_changed)
            reportes_page.results_list.itemClicked.connect(self._on_report_result_selected)
        self.logger.debug("Señales de 'Generación de Informes' conectadas.")

    def _connect_workers_signals(self):
        self.worker_controller._connect_workers_signals()



    def _connect_machines_signals(self):
        machines_page = self.view.pages.get("gestion_datos").maquinas_tab
        machines_page.delete_signal.connect(self._on_delete_machine_clicked)
        if isinstance(machines_page, MachinesWidget):
            machines_page.machines_list.itemClicked.connect(self._on_machine_selected_in_list)
            machines_page.add_button.clicked.connect(machines_page.show_add_new_form)
            machines_page.save_signal.connect(self._on_save_machine_clicked)
            machines_page.manage_groups_signal.connect(self._on_manage_prep_groups_clicked)
            machines_page.add_maintenance_signal.connect(self._on_add_maintenance_clicked)
            self.model.machines_changed_signal.connect(self.update_machines_view)
        self.logger.debug("Señales de 'Gestión Máquinas' conectadas.")

    def _on_calc_product_result_selected(self, item):
        calc_page = self.view.pages["calculate"]
        codigo = item.data(Qt.ItemDataRole.UserRole)
        texto_completo = item.text()
        self._selected_product_for_calc = codigo
        self._selected_product_for_calc_desc = texto_completo
        calc_page.set_selected_product(texto_completo)

    def _on_context_help_clicked(self):
        current_page = self.view.current_page_name
        help_text = self.help_texts.get(current_page, "No hay ayuda disponible para esta sección.")
        title_map = {
            'home': 'Inicio', 'dashboard': 'Dashboard', 'calculate': 'Calcular Tiempos',
            'reportes': 'Generación de Informes', 'historial': 'Historial',
            'gestion_datos': 'Gestión de Datos', 'add_product': 'Añadir Productos',
            'settings': 'Configuración', 'help': 'Guía de Usuario'
        }
        display_title = title_map.get(current_page, current_page.replace("_", " ").capitalize())
        self.view.show_message(f"Ayuda: {display_title}", help_text, "info")

    def _on_save_product_clicked(self):
        add_product_page = self.view.pages["add_product"]
        data = add_product_page.get_data()

        # Llamamos al modelo para que valide y guarde los datos
        result = self.model.add_product(data, data.get("sub_partes"))

        # Interpretamos el resultado y mostramos el mensaje adecuado
        if result == "SUCCESS":
            self.view.show_message("Éxito", f"Producto '{data['codigo']}' guardado.", "info")
            add_product_page.clear_form()

        elif result == "INVALID_TIME":
            # Este es el nuevo mensaje de error específico que querías
            self.view.show_message(
                "Error de Validación",
                "Para productos sin subfabricaciones, el campo 'Tiempo Ã“ptimo' es obligatorio y debe ser un número mayor que cero.",
                "critical"
            )

        elif result == "MISSING_FIELDS":
            self.view.show_message("Error de Validación", "El código y la descripción son campos obligatorios.",
                                   "critical")

        elif result == "DB_ERROR":
            self.view.show_message("Error al Guardar",
                                   "No se pudo guardar el producto.\nEs posible que el código ya exista en la base de datos.",
                                   "critical")

        else:
            # Mensaje por si ocurre otro error inesperado
            self.view.show_message("Error Desconocido", "Ocurrió un error inesperado al guardar el producto.",
                                   "critical")

    def _on_delete_machine_clicked(self, machine_id):
        """Maneja la eliminación de una máquina."""
        if self.view.show_confirmation_dialog("Confirmar Eliminación",
                                              "Â¿Está seguro de que desea eliminar esta máquina?"):
            if self.model.delete_machine(machine_id):
                self.view.show_message("Éxito", "Máquina eliminada.", "info")
            else:
                self.view.show_message("Error", "No se pudo eliminar la máquina.", "critical")

    def _on_manage_subs_for_new_product(self, current_subs):
        add_product_page = self.view.pages["add_product"]
        available_machines = self.model.get_all_machines(include_inactive=False)
        dialog = SubfabricacionesDialog(current_subs, available_machines, self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_subs = dialog.get_updated_subfabricaciones()
            add_product_page.subfabricaciones_temp = updated_subs

    def update_historial_view(self):
        self.logger.info("Actualizando la vista de Historial.")
        page = self.view.pages.get("historial")
        if not isinstance(page, HistorialWidget):
            return
        page.clear_view()
        mode = page.current_mode
        if mode == "iteraciones":
            self.historial_data = self.model.get_all_iterations_with_dates()
            # DTO usage: access attributes dot notation
            responsables = ["Todos los Responsables"] + sorted(list(
                set(row.nombre_responsable for row in self.historial_data if row.nombre_responsable)))
            page.filter_combo.blockSignals(True)
            page.filter_combo.clear()
            page.filter_combo.addItems(responsables)
            page.filter_combo.blockSignals(False)
        else:
            self.historial_data = self.model.get_all_pilas_with_dates()
            page.filter_combo.blockSignals(True)
            page.filter_combo.clear()
            page.filter_combo.addItem("Todas las Pilas")
            page.filter_combo.blockSignals(False)
        self._populate_historial_list()
        self._update_historial_calendar_highlights()
        self._update_historial_activity_chart()

    def _populate_historial_list(self):
        page = self.view.pages.get("historial")
        if not isinstance(page, HistorialWidget) or not hasattr(self, 'historial_data'):
            return
        search_text = page.search_entry.text().lower()
        filter_text = page.filter_combo.currentText()
        mode = page.current_mode
        page.results_list.clear()
        
        for item_data in self.historial_data:
            list_item = None
            if mode == "iteraciones":
                # item_data is ProductIterationDTO
                prod_code = item_data.producto_codigo
                # Ensure we handle potential None values gracefully, though DTO defaults should help
                prod_desc = item_data.producto_descripcion if hasattr(item_data, 'producto_descripcion') else ""
                # Fallback if DTO doesn't have it (it should based on repository)
                if not prod_desc and hasattr(item_data, 'descripcion'):
                     # Careful: item_data.descripcion is iteration description
                     pass 
                
                # The repository sets producto_descripcion in get_all_iterations_with_dates
                
                responsable = item_data.nombre_responsable
                creation_date = item_data.fecha_creacion # datetime object
                
                search_content = f"{prod_code} {prod_desc}".lower()
                if (filter_text != "Todos los Responsables" and responsable != filter_text):
                    continue
                if (search_text and search_text not in search_content):
                    continue
                
                date_str = creation_date.strftime('%d/%m/%Y') if isinstance(creation_date, (datetime, date)) else str(creation_date)
                
                display_text = f"📜 {prod_code} - {prod_desc}\n    └ {date_str} por {responsable}"
                list_item = QListWidgetItem(display_text)
                list_item.setData(Qt.ItemDataRole.UserRole, item_data)
            elif mode == "fabricaciones":
                # Existing logic for fabricaciones (assuming it's not IterationDTO)
                fab_name = item_data.nombre
                fab_desc = item_data.descripcion
                search_content = f"{fab_name} {fab_desc}".lower()
                if search_text and search_text not in search_content:
                    continue
                start_date = item_data.start_date
                end_date = item_data.end_date
                start_str = start_date.strftime('%d/%m/%Y') if isinstance(start_date, date) else 'N/A'
                end_str = end_date.strftime('%d/%m/%Y') if isinstance(end_date, date) else 'N/A'
                display_text = f"📋 {fab_name}\n    └── {start_str} a {end_str}"
                list_item = QListWidgetItem(display_text)
                list_item.setData(Qt.ItemDataRole.UserRole, item_data)
            
            if list_item:
                page.results_list.addItem(list_item)

    def _update_historial_calendar_highlights(self):
        page = self.view.pages.get("historial")
        if not isinstance(page, HistorialWidget):
            return
        page.clear_calendar_format()
        mode = page.current_mode
        dates_to_highlight = set()
        
        for i in range(page.results_list.count()):
            item = page.results_list.item(i)
            item_data = item.data(Qt.ItemDataRole.UserRole)
            if mode == "iteraciones":
                # item_data is ProductIterationDTO
                creation_date = item_data.fecha_creacion
                if isinstance(creation_date, datetime):
                    dates_to_highlight.add(QDate(creation_date.date()))
                elif isinstance(creation_date, date):
                    dates_to_highlight.add(QDate(creation_date))
            else:
                start_date = item_data.start_date
                end_date = item_data.end_date
                if start_date and end_date:
                    current_date = start_date
                    while current_date <= end_date:
                        dates_to_highlight.add(QDate(current_date))
                        current_date += timedelta(days=1)
        
        color = "#3498db" if mode == 'iteraciones' else "#2ecc71"
        page.highlight_calendar_dates(list(dates_to_highlight), color)

    def _on_historial_item_selected(self, item):
        page = self.view.pages.get("historial")
        if not isinstance(page, HistorialWidget): return
        item_data = item.data(Qt.ItemDataRole.UserRole)
        mode = page.current_mode
        page.details_stack.setCurrentIndex(1)
        self._update_historial_calendar_highlights()
        selected_dates = []
        
        if mode == "iteraciones":
            # item_data is ProductIterationDTO
            prod_code = item_data.producto_codigo
            page.details_title_label.setText(f"Producto: {prod_code}")
            
            creation_date = item_data.fecha_creacion
            if isinstance(creation_date, datetime):
                selected_dates.append(QDate(creation_date.date()))
            
            # Fetch full history now returns List[ProductIterationDTO]
            full_history = self.model.get_product_iterations(prod_code)
            
            details_text = "HISTORIAL DE CAMBIOS DEL PRODUCTO:\n\n"
            for it in full_history:
                # it is ProductIterationDTO
                fecha_obj = it.fecha_creacion
                if isinstance(fecha_obj, str):
                    try:
                        fecha_obj = datetime.strptime(fecha_obj, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass
                
                fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M') if isinstance(fecha_obj, (datetime, date)) else str(fecha_obj)
                
                details_text += f"--- {fecha_str} por {it.nombre_responsable} ---\n"
                details_text += f"{it.descripcion}\n\n"
                
                if it.materiales:
                     details_text += "Materiales Afectados:\n"
                     for mat in it.materiales:
                         # mat is ProductIterationMaterialDTO
                         details_text += f"  - {mat.codigo}: {mat.descripcion}\n"
                     details_text += "\n"

            page.details_text.setText(details_text)
        else:
            page.details_title_label.setText(f"Fabricación: {item_data.get('nombre', 'N/A') if isinstance(item_data, dict) else getattr(item_data, 'nombre', 'N/A')}")
            
            # Fallback for fabricaciones (assuming dict or object)
            start_date = item_data.get('start_date') if isinstance(item_data, dict) else getattr(item_data, 'start_date', None)
            end_date = item_data.get('end_date') if isinstance(item_data, dict) else getattr(item_data, 'end_date', None)
            item_id = item_data.get('id') if isinstance(item_data, dict) else getattr(item_data, 'id', None)

            if start_date and end_date:
                current_date = start_date
                while current_date <= end_date:
                    selected_dates.append(QDate(current_date))
                    current_date += timedelta(days=1)
            
            bitacora_id, entradas = self.model.get_diario_bitacora(item_id)
            details_text = f"BITÁCORA DE FABRICACIÓN:\n\n"
            if entradas:
                for fecha, dia, plan, real, notas in entradas:
                    fecha_str = fecha.strftime('%d/%m/%Y') if isinstance(fecha, date) else fecha
                    details_text += f"--- Día {dia} ({fecha_str}) ---\n"
                    details_text += f"PLAN: {plan}\n"
                    details_text += f"REALIZADO: {real}\n"
                    if notas:
                        details_text += f"NOTAS: {notas}\n"
                    details_text += "\n"
            else:
                details_text += "Aún no hay entradas en la bitácora para esta fabricación."
            page.details_text.setText(details_text)
        page.highlight_calendar_dates(selected_dates, "#e74c3c")

    def _on_historial_calendar_clicked(self, q_date):
        page = self.view.pages.get("historial")
        if not isinstance(page, HistorialWidget): return
        py_date = q_date.toPyDate()
        mode = page.current_mode
        for i in range(page.results_list.count()):
            item = page.results_list.item(i)
            item_data = item.data(Qt.ItemDataRole.UserRole)
            is_visible = False
            if mode == "iteraciones":
                creation_date_str = item_data.get('fecha_creacion')
                if creation_date_str:
                    try:
                        if datetime.strptime(creation_date_str, '%Y-%m-%d %H:%M:%S').date() == py_date:
                            is_visible = True
                    except (ValueError, TypeError):
                        pass
            else:
                start_date = item_data.get('start_date')
                end_date = item_data.get('end_date')
                if start_date and end_date and start_date <= py_date <= end_date:
                    is_visible = True
            item.setHidden(not is_visible)

    def _on_print_historial_report_clicked(self):
        self.logger.info("El usuario ha solicitado imprimir un informe de historial.")
        page = self.view.pages.get("historial")
        if not isinstance(page, HistorialWidget): return
        selected_items = page.results_list.selectedItems()
        if not selected_items:
            self.view.show_message("Selección Requerida", "Debe seleccionar un elemento de la lista para imprimir.",
                                   "warning")
            return
        item_data = selected_items[0].data(Qt.ItemDataRole.UserRole)
        mode = page.current_mode
        success = False
        file_path = ""
        if mode == "iteraciones":
            prod_code = item_data.get('producto_codigo', 'unknown')
            prod_desc = item_data.get('descripcion', '')
            full_history = self.model.get_product_iterations(prod_code)
            file_path, _ = QFileDialog.getSaveFileName(self.view, "Guardar Informe", f"Historial_{prod_code}.pdf",
                                                       "Archivos PDF (*.pdf)")
            if not file_path: return
            datos_informe = {"product_code": prod_code, "product_desc": prod_desc, "history": full_history}
            generador = GeneradorDeInformes(ReporteHistorialIteracion())
            success = generador.generar_y_guardar(datos_informe, file_path)
        elif mode == "fabricaciones":
            pila_id = item_data.get('id')
            meta_data, _, _, planificacion = self.model.load_pila(pila_id)
            _, entradas_bitacora = self.model.get_diario_bitacora(pila_id)
            file_path, _ = QFileDialog.getSaveFileName(self.view, "Guardar Informe",
                                                       f"Informe_{meta_data.get('nombre', 'pila')}.pdf",
                                                       "Archivos PDF (*.pdf)")
            if not file_path: return
            datos_completos = {"meta_data": meta_data, "entradas_bitacora": entradas_bitacora,
                               "planificacion": planificacion}
            generador = GeneradorDeInformes(ReporteHistorialFabricacion())
            success = generador.generar_y_guardar(datos_completos, file_path)
        if success:
            self.view.show_message("Éxito", f"El informe se ha guardado en:\n{file_path}", "info")
        elif file_path:
            self.view.show_message("Error", "No se pudo generar el informe PDF.", "critical")

    def _update_historial_activity_chart(self):
        page = self.view.pages.get("historial")
        if not isinstance(page, HistorialWidget) or not hasattr(self, 'historial_data'):
            return
        from collections import defaultdict
        counts, now, mode = defaultdict(int), datetime.now(), page.current_mode
        for item_data in self.historial_data:
            item_date = None
            if mode == "iteraciones":
                item_date_str = item_data.get('fecha_creacion')
                if item_date_str:
                    try:
                        item_date = datetime.strptime(item_date_str, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        continue
            else:
                start_date_obj = item_data.get('start_date')
                if isinstance(start_date_obj, date):
                    item_date = datetime.combine(start_date_obj, datetime.min.time())
            if item_date and (now - item_date).days <= 365:
                timestamp = datetime(item_date.year, item_date.month, 1).timestamp() * 1000
                counts[timestamp] += 1
        series = QLineSeries()
        max_val = 0
        if counts:
            max_val = max(counts.values())
        for ts, count in sorted(counts.items()):
            series.append(ts, count)
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(f"Actividad de {mode.capitalize()} (Últimos 12 Meses)")
        chart.legend().hide()
        axis_x = QDateTimeAxis()
        axis_x.setFormat("MMM yyyy")
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%i")
        axis_y.setRange(0, max_val + 1)
        axis_y.setTickCount(max_val + 2 if max_val < 10 else 10)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        page.activity_chart_view.setChart(chart)






    # En app.py, clase AppController
    # Sustituye esta función completa










    def _on_export_to_excel_clicked(self):
        """
        Exporta los resultados de la simulación a un archivo Excel con ordenación y datos de producto corregidos.
        """
        calc_page = self.view.pages.get("calculate")
        if not self.last_simulation_results:
            self.view.show_message("Sin Datos", "No hay resultados de simulación para exportar.", "warning")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.view, "Guardar Informe Excel",
            f"Informe_Detallado_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            "Archivos Excel (*.xlsx)"
        )
        if not file_path:
            return

        self.logger.info("Invocando estrategia de informe Excel con lógica de ordenación mejorada...")
        self.view.statusBar().showMessage("Generando informe Excel, por favor espere...")
        QApplication.processEvents()

        try:
            # âœ… CORRECCIÃ“N REFINADA: Ordenar por Inicio Y LUEGO por Secuencia Evento
            # Primero, añadimos el índice original para usarlo como desempate
            results_with_index = []
            for index, result in enumerate(self.last_simulation_results):
                result['_original_sequence'] = index  # Guardamos el orden original
                results_with_index.append(result)

            # Ahora ordenamos: Primario por 'Inicio', Secundario por '_original_sequence'
            resultados_ordenados = sorted(
                results_with_index,
                key=lambda x: (
                    x.get('Inicio', datetime.max),  # Clave primaria: Timestamp de inicio
                    x.get('_original_sequence', 0)  # Clave secundaria: Orden original
                )
            )

            # Ya no necesitamos la clave temporal '_original_sequence' en el informe final
            # (aunque no molesta si se queda)
            # for r in resultados_ordenados:
            #     if '_original_sequence' in r: del r['_original_sequence']

            # Usar esta lista perfectamente ordenada para generar el informe
            datos_informe = {
                "data": resultados_ordenados,
                "audit_log": self.last_audit_log,
                "production_flow": self.last_production_flow,
                "fab_info": calc_page.pila_content_table.item(0,
                                                              1).text() if calc_page.pila_content_table.rowCount() > 0 else "N/A",
                "unidades": self.last_units_calculated
                # Asegúrate que esta variable refleje las unidades correctas si aplica
            }

            estrategia = ReportePilaFabricacionExcelMejorado(self.schedule_manager)  # Puede necesitar schedule_manager
            generador = GeneradorDeInformes(estrategia)

            if generador.generar_y_guardar(datos_informe, file_path):
                self.view.show_message("Éxito", f"Informe Excel detallado guardado correctamente en:\n{file_path}",
                                       "info")
            else:
                self.view.show_message("Error", "No se pudo generar o guardar el informe Excel. Revise los logs.",
                                       "critical")

        except Exception as e:
            self.logger.critical(f"Error inesperado durante la exportación a Excel: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error al generar el Excel: {e}", "critical")
        finally:
            self.view.statusBar().clearMessage()

    def _on_export_gantt_to_pdf_clicked(self):
        if not self.last_simulation_results or not self.last_audit_log:
            self.view.show_message("Sin Datos", "Debe ejecutar una simulación completa primero.", "warning")
            return

        file_path, _ = QFileDialog.getSaveFileName(self.view, "Guardar Informe PDF",
                                                   f"Informe_Planificacion_{datetime.now().strftime('%Y%m%d')}.pdf",
                                                   "Archivos PDF (*.pdf)")
        if not file_path:
            return

        calc_page = self.view.pages.get("calculate")
        meta_data_code = calc_page.pila_content_table.item(0,
                                                           1).text() if calc_page.pila_content_table.rowCount() > 0 else "Plan"

        datos_informe = {
            "meta_data": {"code": meta_data_code},
            "planificacion": self.last_simulation_results,
            "audit": self.last_audit_log,
            "flexible_workers_needed": getattr(self, 'last_flexible_workers_needed', 0),
            "production_flow": getattr(self, 'last_production_flow', [])
        }

        # Pasamos el gestor de horarios (schedule_manager) al crear la estrategia
        estrategia = ReporteHistorialFabricacion(self.model, self.schedule_manager)

        generador = GeneradorDeInformes(estrategia)

        if generador.generar_y_guardar(datos_informe, file_path):
            self.view.show_message("Éxito", f"Informe PDF guardado en:\n{file_path}", "info")
        else:
            self.view.show_message("Error", "No se pudo generar el informe PDF.", "critical")

    def _on_import_databases(self):
        """Importa copia de seguridad y reinicia la aplicación para cargar los datos."""
        file_path, _ = QFileDialog.getOpenFileName(self.view, "Seleccionar Copia de Seguridad", "",
                                                   "Archivos ZIP (*.zip)")
        if not file_path:
            return

        if self.view.show_confirmation_dialog("Confirmar",
                                              "<b>Â¡ADVERTENCIA!</b> Esto sobrescribirá los datos actuales. Â¿Continuar?"):
            self.view.statusBar().showMessage("Importando datos, por favor espere...")
            QApplication.processEvents()

            # Cerramos la conexión de la base de datos principal
            self.model.db.close()

            try:
                import zipfile
                # La ruta base donde se encuentran las bases de datos
                extract_path = os.path.dirname(self.model.db.db_path)

                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Extraemos todos los contenidos del ZIP en la carpeta de la BBDD
                    zip_ref.extractall(extract_path)
                    self.logger.info(f"Archivos del ZIP extraídos en: {extract_path}")

                # --- Lógica de Reconexión Simplificada ---
                # Simplemente reinicializamos el modelo.
                # Esto reconstruirá el DatabaseManager y todos los repositorios con los nuevos archivos.
                self.model.__init__(DatabaseManager(db_path=self.model.db.db_path))

                self.view.show_message("Éxito", "Datos importados correctamente. Los cambios ya están disponibles.")
                self.logger.info("Importación de bases de datos completada exitosamente")

                # Actualizar todas las vistas para mostrar los nuevos datos
                self._on_data_changed()
                self.update_workers_view()
                self.update_machines_view()
                # Y cualquier otra vista que necesite refrescarse
                if self.view.current_page_name == "calculate":
                    self._on_nav_button_clicked("calculate")


            except Exception as e:
                self.logger.error(f"Error durante la importación: {e}", exc_info=True)
                self.view.show_message("Error", f"No se pudo importar: {e}", "critical")

                # Intentamos reconectar a la base de datos original por seguridad
                try:
                    self.model.__init__(DatabaseManager(db_path=self.model.db.db_path))
                except Exception as recon_e:
                    self.logger.critical(
                        f"No se pudo reconectar a la base de datos tras el fallo de importación: {recon_e}")

    def _on_export_databases(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        file_path, _ = QFileDialog.getSaveFileName(self.view, "Guardar Copia de Seguridad", f"backup_{timestamp}.zip",
                                                   "Archivos ZIP (*.zip)")
        if not file_path:
            return
        try:
            import zipfile
            db_files = [
                resource_path(self.model.db.db_path)
            ]
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in db_files:
                    if os.path.exists(file):
                        zipf.write(file, os.path.basename(file))
                    else:
                        self.logger.warning(f"No se encontró el archivo de base de datos '{file}' para exportar.")
            self.view.show_message("Éxito", f"Copia de seguridad guardada en:\n{file_path}", "info")
        except Exception as e:
            self.view.show_message("Error", f"No se pudo crear la copia: {e}", "critical")

    def _on_sync_databases_clicked(self):
        self.logger.info("Iniciando proceso de sincronización de bases de datos.")
        foreign_db_path, _ = QFileDialog.getOpenFileName(self.view, "Seleccionar Base de Datos a Sincronizar", "",
                                                         "Archivos de Base de Datos (*.db)")
        if not foreign_db_path:
            return
        differences = self.model.db.compare_with_db(foreign_db_path)
        if not any(differences.values()):
            self.view.show_message("Sincronización", "No se encontraron diferencias entre las bases de datos.", "info")
            return
        from ui.dialogs import SyncDialog
        dialog = SyncDialog(differences, self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_changes = dialog.get_selected_changes()
            if not selected_changes:
                self.view.show_message("Sincronización", "No se seleccionó ningún cambio para importar.", "warning")
                return
            count = self.model.db.apply_sync_changes(selected_changes)
            self.view.show_message("Sincronización Completa", f"Se han importado/actualizado {count} registros.",
                                   "info")
            self._on_data_changed()
            self.update_machines_view()
            self.update_workers_view()

    def _create_backup_directory_structure(self):
        """Crea la estructura de carpetas para backups organizados por fecha y hora."""
        try:
            from datetime import datetime
            import os

            # Obtener directorio base donde está el ejecutable
            base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            backup_main_dir = os.path.join(base_dir, "Backup")

            # Crear carpeta principal Backup si no existe
            os.makedirs(backup_main_dir, exist_ok=True)

            # Crear subcarpetas principales
            db_backup_dir = os.path.join(backup_main_dir, "Base de datos")
            log_backup_dir = os.path.join(backup_main_dir, "Registro de errores")
            os.makedirs(db_backup_dir, exist_ok=True)
            os.makedirs(log_backup_dir, exist_ok=True)

            # Obtener fecha y hora actual
            now = datetime.now()
            date_folder = now.strftime("%Y-%m-%d")
            time_folder = now.strftime("%H-%M")

            # Crear carpetas de fecha y hora para base de datos
            db_date_dir = os.path.join(db_backup_dir, date_folder)
            db_final_dir = os.path.join(db_date_dir, time_folder)
            os.makedirs(db_final_dir, exist_ok=True)

            # Crear carpetas de fecha y hora para logs
            log_date_dir = os.path.join(log_backup_dir, date_folder)
            log_final_dir = os.path.join(log_date_dir, time_folder)
            os.makedirs(log_final_dir, exist_ok=True)

            self.logger.info(f"Estructura de backup creada: DB={db_final_dir}, LOG={log_final_dir}")
            return db_final_dir, log_final_dir

        except Exception as e:
            self.logger.error(f"Error al crear estructura de directorios de backup: {e}")
            return None, None

    def create_automatic_backup(self):
        """
        Realiza copia de seguridad automática con estructura organizada por fecha/hora
        e incluye backup del log de errores.
        """
        self.logger.info("Iniciando proceso de copia de seguridad automática mejorada...")

        try:
            db_backup_dir, log_backup_dir = self._create_backup_directory_structure()
            if not db_backup_dir or not log_backup_dir:
                self.logger.error("No se pudo crear la estructura de directorios de backup")
                return False

            # 1. Backup de la base de datos principal
            db_backup_success = False
            main_db_path = self.model.db.db_path
            if os.path.exists(main_db_path):
                destination_path = os.path.join(db_backup_dir, os.path.basename(main_db_path))
                shutil.copy2(main_db_path, destination_path)
                self.logger.info(f"BD principal copiada a: {destination_path}")
                db_backup_success = True
            else:
                self.logger.warning(f"Archivo de BD principal no encontrado: {main_db_path}")

            # 2. Backup del log de errores (sin cambios)
            log_backup_success = self._backup_and_clean_log(log_backup_dir)

            if db_backup_success and log_backup_success:
                self.logger.info("Copia de seguridad automática completada con éxito.")
                return True
            else:
                self.logger.warning("Copia de seguridad completada con algunos errores.")
                return False

        except Exception as e:
            self.logger.critical(f"FALLO CRÃTICO en la copia de seguridad automática: {e}", exc_info=True)
            return False

    def _backup_and_clean_log(self, log_backup_dir):
        """Realiza backup del log de errores y lo limpia."""
        try:
            log_file_path = os.path.join("logs", "EvolucionTiempos.log")

            if os.path.exists(log_file_path):
                # Copiar el log al directorio de backup
                log_backup_path = os.path.join(log_backup_dir, "EvolucionTiempos.log")
                shutil.copy2(log_file_path, log_backup_path)
                self.logger.info(f"Log copiado a: {log_backup_path}")

                # Limpiar el archivo de log original
                with open(log_file_path, 'w', encoding='utf-8') as f:
                    f.write("")  # Vaciar el archivo

                self.logger.info("Archivo de log limpiado después del backup.")
                return True
            else:
                self.logger.warning(f"Archivo de log no encontrado: {log_file_path}")
                return False

        except Exception as e:
            self.logger.error(f"Error en backup/limpieza del log: {e}")
            return False

    def _on_add_break_clicked(self):
        dialog = AddBreakDialog(self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_break = dialog.get_times()
            breaks_json = self.model.db.config_repo.get_setting('breaks', '[]')
            breaks_list = json.loads(breaks_json)
            breaks_list.append(new_break)
            self.model.db.config_repo.set_setting('breaks', json.dumps(breaks_list))
            self.schedule_manager.reload_config()
            self._load_schedule_settings()

    def _on_remove_break_clicked(self):
        """Elimina el descanso seleccionado de la lista y guarda los cambios."""
        settings_page = self.view.pages.get("settings")
        if not isinstance(settings_page, SettingsWidget):
            return

        selected_items = settings_page.breaks_list.selectedItems()
        if not selected_items:
            self.view.show_message("Selección Requerida", "Seleccione un descanso de la lista para eliminar.",
                                   "warning")
            return

        selected_item = selected_items[0]
        break_text = selected_item.text()

        if self.view.show_confirmation_dialog("Confirmar Eliminación",
                                              f"Â¿Está seguro de que desea eliminar el descanso '{break_text}'?"):
            row = settings_page.breaks_list.row(selected_item)
            settings_page.breaks_list.takeItem(row)  # Elimina el item de la lista visual
            self.logger.info(f"Descanso '{break_text}' eliminado de la UI.")
            self._on_save_schedule_settings()  # Guarda la lista actualizada en la BD
            # No es necesario llamar a _load_schedule_settings aquí porque _on_save ya recarga
            # y la UI ya está actualizada.
            # Mostramos un mensaje diferente a _on_save_schedule_settings
            self.view.show_message("Éxito", "Descanso eliminado correctamente.", "info")
            settings_page._update_break_buttons_state()  # Actualiza estado de botones

    def _on_edit_break_clicked(self):
        """Edita el descanso seleccionado usando AddBreakDialog."""
        settings_page = self.view.pages.get("settings")
        if not isinstance(settings_page, SettingsWidget):
            return

        selected_items = settings_page.breaks_list.selectedItems()
        if not selected_items:
            self.view.show_message("Selección Requerida", "Seleccione un descanso de la lista para editar.", "warning")
            return

        selected_item = selected_items[0]
        original_text = selected_item.text()
        try:
            current_start_str, current_end_str = original_text.split(' - ')
            current_start_time = QTime.fromString(current_start_str.strip(), "HH:mm")
            current_end_time = QTime.fromString(current_end_str.strip(), "HH:mm")
        except (ValueError, IndexError):
            self.logger.error(f"Error al parsear el texto del descanso: '{original_text}'")
            self.view.show_message("Error", "No se pudo leer la hora del descanso seleccionado.", "critical")
            return

        dialog = AddBreakDialog(self.view)
        # Pre-rellenar el diálogo con las horas actuales
        dialog.start_time_edit.setTime(current_start_time)
        dialog.end_time_edit.setTime(current_end_time)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_times = dialog.get_times()
            new_start = new_times['start']
            new_end = new_times['end']
            new_text = f"{new_start} - {new_end}"

            # Actualizar el texto del item seleccionado en la lista visual
            selected_item.setText(new_text)
            self.logger.info(f"Descanso editado en la UI: '{original_text}' -> '{new_text}'")

            # Guardar la lista completa actualizada en la BD
            self._on_save_schedule_settings()
            # Mostramos un mensaje diferente a _on_save_schedule_settings
            self.view.show_message("Éxito", "Descanso actualizado correctamente.", "info")
            settings_page._update_break_buttons_state()  # Actualiza estado botones

    def _on_save_schedule_settings(self):
        """Guarda la configuración completa del horario laboral."""
        import json

        settings_page = self.view.pages["settings"]

        # 1. Guardar horas de entrada y salida
        start_time = settings_page.work_start_time.time().toString('HH:mm')
        end_time = settings_page.work_end_time.time().toString('HH:mm')

        self.model.db.config_repo.set_setting('work_start_time', start_time)
        self.model.db.config_repo.set_setting('work_end_time', end_time)

        # 2. Guardar descansos (NUEVO)
        breaks = []
        for i in range(settings_page.breaks_list.count()):
            item_text = settings_page.breaks_list.item(i).text()
            if ' - ' in item_text:
                start, end = item_text.split(' - ')
                breaks.append({"start": start.strip(), "end": end.strip()})

        self.model.db.config_repo.set_setting('breaks', json.dumps(breaks))

        # 3. Recargar configuración
        self.schedule_manager.reload_config(self.model.db)

        self.logger.info(f"âœ… Horario completo guardado: {start_time} - {end_time}, {len(breaks)} descansos")
        self.view.show_message("Éxito", "Horario completo guardado y aplicado.", "info")

    def _on_add_break(self):
        """Abre un diálogo para añadir un descanso."""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QTimeEdit
        from PyQt6.QtCore import QTime

        dialog = QDialog(self.view)
        dialog.setWindowTitle("Añadir Descanso")
        layout = QFormLayout(dialog)

        start_time = QTimeEdit()
        start_time.setDisplayFormat("HH:mm")
        start_time.setTime(QTime(12, 0))  # Default 12:00
        end_time = QTimeEdit()
        end_time.setDisplayFormat("HH:mm")
        end_time.setTime(QTime(13, 0))  # Default 13:00

        layout.addRow("Hora de Inicio:", start_time)
        layout.addRow("Hora de Fin:", end_time)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            start = start_time.time().toString('HH:mm')
            end = end_time.time().toString('HH:mm')

            settings_page = self.view.pages["settings"]
            settings_page.breaks_list.addItem(f"{start} - {end}")
            self.logger.info(f"Descanso añadido: {start} - {end}")

    def _load_schedule_settings(self):
        """Carga la configuración del horario en la UI."""
        from PyQt6.QtCore import QTime
        import json

        settings_page = self.view.pages["settings"]

        # Cargar horas
        start_time_str = self.model.db.config_repo.get_setting('work_start_time', '08:00')
        end_time_str = self.model.db.config_repo.get_setting('work_end_time', '15:15')

        settings_page.work_start_time.setTime(QTime.fromString(start_time_str, 'HH:mm'))
        settings_page.work_end_time.setTime(QTime.fromString(end_time_str, 'HH:mm'))

        # Cargar descansos
        breaks_json = self.model.db.config_repo.get_setting('breaks', '[{"start": "12:00", "end": "13:00"}]')
        try:
            breaks = json.loads(breaks_json)
            settings_page.breaks_list.clear()
            for brk in breaks:
                settings_page.breaks_list.addItem(f"{brk['start']} - {brk['end']}")
        except json.JSONDecodeError:
            self.logger.warning("Error cargando descansos, usando valor por defecto")
            settings_page.breaks_list.addItem("12:00 - 13:00")

    def _on_manage_prep_groups_clicked(self, machine_id, machine_name):
        dialog = PrepGroupsDialog(machine_id, machine_name, self, self.view)
        dialog.exec()

    def handle_image_attachment(self, iteration_id, source_file_path):
        self.logger.info(f"Adjuntando imagen '{source_file_path}' a la iteración ID {iteration_id}.")
        if not iteration_id or not source_file_path:
            return False, "Datos de entrada inválidos."
        try:
            images_dir = resource_path("data/images")
            os.makedirs(images_dir, exist_ok=True)
            _, file_extension = os.path.splitext(source_file_path)
            new_filename = f"iteration_{iteration_id}{file_extension}"
            destination_path = os.path.join(images_dir, new_filename)
            shutil.copy(source_file_path, destination_path)
            relative_path = os.path.join("data", "images", new_filename)
            if self.model.update_iteration_image_path(iteration_id, relative_path):
                self.logger.info(f"Imagen guardada en '{destination_path}' y ruta actualizada en la BD.")
                return True, "Imagen guardada con éxito."
            else:
                return False, "La imagen fue copiada, pero no se pudo actualizar la base de datos."
        except Exception as e:
            self.logger.error(f"Error al adjuntar la imagen: {e}", exc_info=True)
            return False, str(e)



    # DELETED: Worker management logic moved to WorkerController.




    def update_dashboard_view(self):
        self.logger.info("Actualizando la vista del Dashboard...")
        dashboard_page = self.view.pages.get("dashboard")
        if isinstance(dashboard_page, DashboardWidget):
            machine_stats = self.model.get_machine_usage_stats()
            worker_stats = self.model.get_worker_load_stats()
            component_stats = self.model.get_problematic_components_stats()
            dashboard_page.update_machine_usage(machine_stats)
            dashboard_page.update_worker_load(worker_stats)
            dashboard_page.update_problematic_components(component_stats)

    # DELETED: Worker update logic moved to WorkerController.




    def _on_save_machine_clicked(self):
        gestion_datos_page = self.view.pages["gestion_datos"]
        machines_page = gestion_datos_page.maquinas_tab
        machine_id = machines_page.current_machine_id
        data = machines_page.get_form_data()

        if not data or not data["nombre"]:
            self.view.show_message("Error", "El nombre es obligatorio.", "warning")
            return

        if machine_id is None:  # Es una máquina nueva
            result = self.model.add_machine(data["nombre"], data["departamento"], data["tipo_proceso"])
            if result is True:
                self.view.show_message("Éxito", "Máquina añadida.", "info")
                self.update_machines_view()
            elif result == "UNIQUE_CONSTRAINT":
                self.view.show_message("Error", "Ya existe una máquina con ese nombre.", "warning")
            else:
                self.view.show_message("Error", "No se pudo añadir la máquina.", "critical")
        else:  # Es una actualización
            if self.model.update_machine(machine_id, data["nombre"], data["departamento"], data["tipo_proceso"],
                                         data["activa"]):
                self.view.show_message("Éxito", "Máquina actualizada.", "info")
                self.update_machines_view()
            else:
                self.view.show_message("Error", "No se pudo actualizar la máquina.", "critical")

    def _on_add_maintenance_clicked(self, machine_id):
        if machine_id is None:
            self.view.show_message("Atención", "Debe haber una máquina seleccionada para añadir un registro.",
                                   "warning")
            return
        notes, ok = QInputDialog.getText(self.view, "Añadir Registro de Mantenimiento", "Notas del Mantenimiento:")
        if ok and notes.strip():
            if self.model.add_machine_maintenance(machine_id, date.today(), notes.strip()):
                self.view.show_message("Éxito", "Registro de mantenimiento añadido.", "info")
                gestion_datos_page = self.view.pages.get("gestion_datos")
                if isinstance(gestion_datos_page, GestionDatosWidget):
                    machines_page = gestion_datos_page.maquinas_tab
                    history_data = self.model.get_machine_history(machine_id)
                    machines_page.populate_history_tables(history_data.get('maintenance_history', []))
            else:
                self.view.show_message("Error", "No se pudo añadir el registro.", "critical")

    def update_machines_view(self):
        """Actualiza la vista de máquinas con TODAS las máquinas."""
        self.logger.info("Actualizando la vista de máquinas...")
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if isinstance(gestion_datos_page, GestionDatosWidget):
            machines_page = gestion_datos_page.maquinas_tab
            # âœ… CAMBIO: Usar get_all_machines en lugar de get_latest_machines
            machines_data = self.model.get_all_machines()
            machines_page.populate_list(machines_data)

    # DELETED: Worker selection moved to WorkerController.


    def _on_machine_selected_in_list(self, item):
        machine_id = item.data(Qt.ItemDataRole.UserRole)
        all_machines = self.model.get_all_machines(include_inactive=True)
        # Ahora usamos atributo DTO .id en lugar de índice [0]
        machine_data = next((m for m in all_machines if m.id == machine_id), None)
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if not isinstance(gestion_datos_page, GestionDatosWidget):
            return
        machines_page = gestion_datos_page.maquinas_tab
        if machine_data:
            machines_page.show_machine_details(machine_data)
            history_data = self.model.get_machine_history(machine_id)
            machines_page.populate_history_tables(history_data.get('maintenance_history', []))

    def _on_report_search_changed(self, text):
        reportes_page = self.view.pages.get("reportes")
        if not isinstance(reportes_page, ReportesWidget) or len(text) < 2:
            if reportes_page: reportes_page.results_list.clear()
            return

        # Solo buscar productos y pilas
        search_results = self.model.search_products(text)
        # Convertir formato de productos para consistencia
        formatted_results = []
        for product in search_results:
            formatted_results.append({'type': 'Producto', 'code': product.codigo, 'description': product.descripcion})

        pilas_results = self.model.pila_repo.search_pilas(text)
        for pila in pilas_results:
            formatted_results.append({'type': 'Pila', 'code': pila.nombre, 'description': pila.descripcion, 'id': pila.id})

        reportes_page.results_list.clear()
        for result in formatted_results:
            item_text = f"[{result['type']}] {result['code']} - {result['description']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, result)
            reportes_page.results_list.addItem(item)

    def _on_generar_informe_clicked(self, tipo_informe, item_id=None):
        """Genera el informe seleccionado por el usuario desde la página de Reportes."""
        if not self.selected_report_item:
            self.view.show_message("Error", "No hay un elemento seleccionado.", "warning")
            return

        # --- Caso de uso para el nuevo PDF de Pila de Fabricación ---
        if tipo_informe == 'historial_pila_pdf':
            # Cargamos los últimos resultados de la simulación que están en memoria
            if not self.last_simulation_results:
                self.view.show_message("Error", "No hay datos de una simulación reciente para generar el informe.",
                                       "warning")
                return

            datos_informe = {
                "meta_data": self.selected_report_item,
                "planificacion": self.last_simulation_results,
                "audit": self.last_audit_log,
                "flexible_workers_needed": self.last_flexible_workers_needed,
                "production_flow": self.last_production_flow  # <-- AÃ‘ADE ESTA LÃNEA
            }

            file_path, _ = QFileDialog.getSaveFileName(self.view, "Guardar Informe PDF",
                                                       f"Informe_Optimizacion_{self.selected_report_item['code']}.pdf",
                                                       "Archivos PDF (*.pdf)")
            if not file_path: return

            # Preparamos los datos para el informe, incluyendo el resultado de la optimización
            datos_informe = {
                "meta_data": self.selected_report_item,
                "planificacion": self.last_simulation_results,
                "audit": self.last_audit_log,
                "flexible_workers_needed": self.last_flexible_workers_needed  # <-- DATO CLAVE
            }
            generador = GeneradorDeInformes(ReporteHistorialFabricacion(self.model))
            if generador.generar_y_guardar(datos_informe, file_path):
                self.view.show_message("Éxito", "Informe PDF guardado.", "info")
            else:
                self.view.show_message("Error", "No se pudo generar el informe PDF.", "critical")

        # --- Otros casos de uso (se mantienen como estaban) ---
        elif tipo_informe == 'pila_fabricacion_excel':
            # Esta lógica ya se maneja en el botón de la página de cálculo principal
            # Se podría unificar aquí si se desea.
            pass
        elif tipo_informe == 'historial_iteraciones':
            prod_code = self.selected_report_item.get('code')
            history = self.model.get_product_iterations(prod_code)
            file_path, _ = QFileDialog.getSaveFileName(self.view, "Guardar Informe", f"Historial_{prod_code}.pdf",
                                                       "Archivos PDF (*.pdf)")
            if not file_path: return

            datos_informe = {"product_code": prod_code, "product_desc": self.selected_report_item.get('description'),
                             "history": history}
            generador = GeneradorDeInformes(ReporteHistorialIteracion())
            if generador.generar_y_guardar(datos_informe, file_path):
                self.view.show_message("Éxito", "Informe PDF guardado.", "info")
            else:
                self.view.show_message("Error", "No se pudo generar el informe PDF.", "critical")

    def _on_data_changed(self):
        self.logger.info("El modelo ha cambiado, refrescando la vista de edición de productos.")
        products_page = self.view.pages["gestion_datos"].productos_tab
        products_page.clear_all()
        # Cargar productos por defecto
        all_products = self.model.search_products("")
        products_page.update_search_results(all_products)

    def search_fabricaciones(self, query: str):
        """Busca fabricaciones usando el repositorio de preprocesos."""
        try:
            # Usa el repositorio en lugar de la conexión directa a la BD
            return self.model.preproceso_repo.search_fabricaciones(query)
        except Exception as e:
            self.logger.error(f"Error buscando fabricaciones a través del repositorio: {e}")
            return []

    def show_fabricacion_preprocesos(self, fabricacion_id: int):
        """
        Muestra un diálogo para seleccionar preprocesos para una fabricación.
        CORREGIDO: Ahora utiliza el repositorio para la actualización, garantizando
        la consistencia de la sesión de SQLAlchemy.
        """
        try:
            # Obtener información de la fabricación (usamos el método legacy que ya funciona)
            fabricacion_tuple = self.model.db.get_fabricacion_by_id(fabricacion_id)
            if not fabricacion_tuple:
                self.view.show_message("Error", "Fabricación no encontrada.", "critical")
                return

            # Convertimos la tupla a un formato de diccionario más manejable para el diálogo
            fabricacion_dict = (fabricacion_tuple['id'], fabricacion_tuple['codigo'], fabricacion_tuple['descripcion'])

            # Obtener todos los preprocesos disponibles
            all_preprocesos = self.model.get_all_preprocesos_with_components()

            # Obtener preprocesos ya asignados a esta fabricación
            assigned_preprocesos_tuples = self.model.db.get_preprocesos_by_fabricacion(fabricacion_id)
            assigned_ids = [p[0] for p in assigned_preprocesos_tuples]

            # Crear y mostrar diálogo
            dialog = PreprocesosSelectionDialog(
                fabricacion_dict, all_preprocesos, assigned_ids, self.view
            )

            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_ids = dialog.get_selected_preprocesos()

                # --- LÃNEA CLAVE DE LA CORRECCIÃ“N ---
                # Usamos el nuevo método del repositorio en lugar del método legacy.
                # Esto mantiene la sesión de SQLAlchemy sincronizada.
                if self.model.preproceso_repo.update_fabricacion_preprocesos(fabricacion_id, selected_ids):
                    self.view.show_message("Éxito",
                                           f"Preprocesos actualizados para la fabricación '{fabricacion_dict[1]}'.",
                                           "info")
                    # Opcional: Refrescar la vista si es necesario
                    gestion_datos_page = self.view.pages.get("gestion_datos")
                    if gestion_datos_page:
                        gestion_datos_page.fabricaciones_tab._on_fabrication_result_selected(
                            gestion_datos_page.fabricaciones_tab.results_list.currentItem())

                else:
                    self.view.show_message("Error",
                                           "No se pudieron actualizar los preprocesos.", "critical")

        except Exception as e:
            self.logger.error(f"Error mostrando preprocesos de fabricación: {e}", exc_info=True)
            self.view.show_message("Error", f"Error inesperado: {e}", "critical")

    def _refresh_fabricaciones_list(self):
        """Refresca la lista de fabricaciones en gestión de datos."""
        try:
            # Si estamos en la pestaña de productos y fabricaciones, actualizar
            if hasattr(self.view, 'pages') and 'gestion_datos' in self.view.pages:
                gestion_widget = self.view.pages['gestion_datos']
                if hasattr(gestion_widget, 'productos_fabricaciones_tab'):
                    # Aquí se podría añadir lógica para refrescar la lista de fabricaciones
                    # si tuvieras una pestaña de fabricaciones en el futuro
                    pass
        except Exception as e:
            self.logger.error(f"Error refrescando lista de fabricaciones: {e}")

    def get_fabricacion_products_for_calculation(self, fabricacion_id: int):
        """
        Obtiene todos los productos de una fabricación preparados para cálculo.

        Returns:
            list: Lista de productos con cantidades para el cálculo
        """
        try:
            # Obtener productos de la fabricación
            fabricacion_products = self.model.db.preproceso_repo.get_products_for_fabricacion(fabricacion_id)

            calculation_data = []
            for fp_dto in fabricacion_products:
                # Obtener datos detallados del producto
                product_data = self.model.get_data_for_calculation(fp_dto.producto_codigo)
                if product_data:
                    # Ajustar cantidad
                    product_info = product_data[0].copy()
                    product_info['cantidad_en_kit'] = fp_dto.cantidad
                    calculation_data.append(product_info)

            return calculation_data

        except Exception as e:
            self.logger.error(f"Error obteniendo productos de fabricación para cálculo: {e}")
            return []




    # ==============================================================================
    # SUSTITUYE las funciones show_add_preproceso_dialog y show_edit_preproceso_dialog
    # en la clase AppController de main.py
    # ==============================================================================
    def show_add_preproceso_dialog(self):
        """Muestra el diálogo para crear un nuevo preproceso, pasándole los materiales."""
        self.logger.info("Mostrando diálogo para añadir preproceso.")
        try:
            all_materials = self.model.get_all_materials_for_selection()
            dialog = PreprocesoDialog(all_materials=all_materials, controller=self.product_controller, parent=self.view)
            if dialog.exec():
                data = dialog.get_data()
                if data and self.model.create_preproceso(data):
                    self.view.show_message("Éxito", f"Preproceso '{data['nombre']}' creado.", "info")
                    self._load_preprocesos_data()
                elif data:
                    self.view.show_message("Error", "No se pudo crear el preproceso. El nombre podría ya existir.",
                                           "critical")
        except Exception as e:
            self.logger.error(f"Error mostrando diálogo de crear preproceso: {e}", exc_info=True)

    def show_edit_preproceso_dialog(self, preproceso_data):
        """Muestra el diálogo para editar un preproceso, pasándole los materiales."""
        self.logger.info(f"Mostrando diálogo para editar preproceso ID: {preproceso_data.id}")
        try:
            all_materials = self.model.get_all_materials_for_selection()
            dialog = PreprocesoDialog(preproceso_existente=preproceso_data, all_materials=all_materials, controller=self.product_controller, parent=self.view)
            if dialog.exec():
                new_data = dialog.get_data()
                if new_data and self.model.update_preproceso(preproceso_data.id, new_data):
                    self.view.show_message("Éxito", f"Preproceso '{new_data['nombre']}' actualizado.", "info")
                    self._load_preprocesos_data()
                elif new_data:
                    self.view.show_message("Error", "No se pudo actualizar el preproceso.", "critical")
        except Exception as e:
            self.logger.error(f"Error mostrando diálogo de editar preproceso: {e}", exc_info=True)

    def delete_preproceso(self, preproceso_id: int, preproceso_nombre: str):
        """
        Solicita confirmación y elimina un preproceso.

        Args:
            preproceso_id (int): ID del preproceso a eliminar.
            preproceso_nombre (str): Nombre del preproceso, para mostrar en el diálogo.
        """
        self.logger.info(f"Iniciando proceso de eliminación para preproceso ID: {preproceso_id}")

        reply = QMessageBox.question(
            self.view,
            'Confirmar Eliminación',
            f"Â¿Estás seguro de que quieres eliminar el preproceso '{preproceso_nombre}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.model.delete_preproceso(preproceso_id):
                QMessageBox.information(self.view, "Éxito", f"El preproceso '{preproceso_nombre}' ha sido eliminado.")
                self._load_preprocesos_data()  # Recargar la tabla
            else:
                QMessageBox.critical(self.view, "Error de Eliminación", "No se pudo eliminar el preproceso.")

    def _on_nav_button_clicked(self, name: str):
        """Maneja el clic en botones de navegación."""
        self.logger.info(f"Botón de navegación '{name}' presionado. Cambiando de página.")
        self.view.switch_page(name)

        # Cargar datos específicos según la página
        if name == "settings":
            self._load_schedule_settings()
        elif name == "dashboard":
            self.update_dashboard_view()
        elif name == "calculate":
            calc_page = self.view.pages.get("calculate")
            if isinstance(calc_page, CalculateTimesWidget):
                try:
                    # Limpiar la sesión anterior al entrar
                    calc_page.planning_session = []

                    # âœ… SOLUCIÃ“N: Usar QTimer para diferir la actualización de la UI.
                    # Esto asegura que el widget esté completamente construido y visible
                    # antes de que intentemos llenarlo de datos.
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, lambda: self._safe_update_calculate_page(calc_page))

                except Exception as e:
                    self.logger.error(f"Error preparando la página de cálculo: {e}", exc_info=True)
                    self.view.show_message("Error", f"No se pudo cargar la página de cálculo: {e}", "critical")
        elif name == "historial":
            self.update_historial_view()
        elif name == "definir_lote":
            lote_page = self.view.pages.get("definir_lote")
            if lote_page:
                lote_page.clear_form()
        elif name == "preprocesos":
            self._load_preprocesos_data()
        elif name == "gestion_datos":
            self.update_workers_view()
            self.update_machines_view()
            self.update_lotes_view()
            if self.view.pages["gestion_datos"].productos_tab:
                self.view.pages["gestion_datos"].productos_tab.search_entry.textChanged.emit("")
            if self.view.pages["gestion_datos"].fabricaciones_tab:
                # self.view.pages["gestion_datos"].fabricaciones_tab.search_entry.textChanged.emit("")
                self._refresh_fabricaciones_list()
        elif name == "add_product":
            add_product_page = self.view.pages["add_product"]
            latest_products = self.model.get_latest_products()
            add_product_page.update_existing_products_list(latest_products)

    def update_machines_view(self):
        """Actualiza la lista de máquinas en la vista."""
        gestion_page = self.view.pages.get("gestion_datos")
        if isinstance(gestion_page, GestionDatosWidget) and gestion_page.maquinas_tab:
            machines = self.model.get_all_machines(include_inactive=True)
            if hasattr(gestion_page.maquinas_tab, 'populate_list'):
                gestion_page.maquinas_tab.populate_list(machines)

    def _safe_update_calculate_page(self, calc_page):
        """
        Actualiza la página de cálculo de forma segura, con manejo de errores.
        Este método se llama diferido para dar tiempo a Qt a estabilizar los widgets.
        """
        try:
            calc_page._update_plan_display()
            self._on_calc_lote_search_changed("")  # "" busca todos
        except RuntimeError as e:
            self.logger.error(f"RuntimeError diferido en calculate: {e}", exc_info=True)
        except AttributeError as e:
            self.logger.error(f"AttributeError diferido en calculate: {e}", exc_info=True)

    def delete_preproceso(self, preproceso_id: int, preproceso_nombre: str):
        """
        Solicita confirmación y elimina un preproceso.

        Args:
            preproceso_id (int): ID del preproceso a eliminar.
            preproceso_nombre (str): Nombre del preproceso, para mostrar en el diálogo.
        """
        self.logger.info(f"Iniciando proceso de eliminación para preproceso ID: {preproceso_id}")

        # Usar el método de confirmación existente de la vista
        reply = self.view.show_confirmation_dialog(
            'Confirmar Eliminación',
            f"Â¿Estás seguro de que quieres eliminar el preproceso '{preproceso_nombre}'?\n\n"
            "Esta acción no se puede deshacer."
        )

        if reply:
            try:
                if self.model.delete_preproceso(preproceso_id):
                    self.view.show_message("Éxito", f"El preproceso '{preproceso_nombre}' ha sido eliminado.", "info")
                    self._load_preprocesos_data()  # Recargar la tabla
                else:
                    self.view.show_message("Error de Eliminación", "No se pudo eliminar el preproceso.", "critical")
            except Exception as e:
                self.logger.error(f"Error eliminando preproceso: {e}")
                self.view.show_message("Error", f"Error al eliminar el preproceso: {e}", "critical")

    def get_preprocesos_by_fabricacion(self, fabricacion_id: int):
        """
        Obtiene los preprocesos asignados a una fabricación.

        Args:
            fabricacion_id: ID de la fabricación

        Returns:
            Lista de diccionarios con información de preprocesos
        """
        try:
            if not hasattr(self, 'preproceso_repo'):
                from database.repositories import PreprocesoRepository
                self.preproceso_repo = PreprocesoRepository(self.model.db.SessionLocal)

            preprocesos = self.preproceso_repo.get_preprocesos_by_fabricacion(fabricacion_id)

            # Convertir a formato esperado
            result = []
            for preproceso in preprocesos:
                result.append({
                    'id': preproceso.id,
                    'nombre': preproceso.nombre,
                    'descripcion': preproceso.descripcion or '',
                    'componentes': [(comp.id, comp.descripcion_componente) for comp in preproceso.componentes]
                })

            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo preprocesos de fabricación: {e}")
            return []

    def add_preprocesos_to_current_pila(self, preprocesos: list) -> int:
        """
        Añade preprocesos a la pila de cálculo actual.

        Args:
            preprocesos: Lista de diccionarios con información de preprocesos

        Returns:
            int: Número de preprocesos añadidos exitosamente
        """
        try:
            calc_widget = self.view.pages.get("calculate")
            if not calc_widget or not hasattr(calc_widget, 'add_preprocesos_to_pila'):
                self.logger.warning("Widget de cálculo no disponible o no soporta preprocesos")
                return 0

            added_count = 0
            for preproceso in preprocesos:
                # Convertir preproceso a formato de paso de pila
                step_data = self._convert_preproceso_to_pila_step(preproceso)
                if step_data and calc_widget.add_step_to_pila(step_data):
                    added_count += 1

            self.logger.info(f"Añadidos {added_count} preprocesos a la pila actual")
            return added_count

        except Exception as e:
            self.logger.error(f"Error añadiendo preprocesos a pila: {e}")
            return 0

    def _convert_preproceso_to_pila_step(self, preproceso: dict) -> dict:
        """
        Convierte un preproceso al formato de paso de pila.

        Args:
            preproceso: Diccionario con información del preproceso

        Returns:
            dict: Datos del paso en formato de pila o None si falla
        """
        try:
            # Calcular tiempo total basado en componentes
            tiempo_total = 0
            for comp_id, comp_desc in preproceso.get('componentes', []):
                # Por ahora usamos un tiempo base, pero esto podría calcularse
                # basándose en propiedades de los materiales
                tiempo_total += 5  # 5 minutos por componente (configurable)

            # Crear descripción detallada
            componentes_text = ", ".join([comp[1] for comp in preproceso.get('componentes', [])])
            descripcion = f"PREPROCESO: {preproceso['nombre']}"
            if componentes_text:
                descripcion += f" (Componentes: {componentes_text})"

            return {
                'tipo': 'preproceso',
                'descripcion': descripcion,
                'tiempo': max(tiempo_total, 10),  # Mínimo 10 minutos
                'tipo_trabajador': 1,  # Por defecto: Oficial
                'es_preproceso': True,
                'preproceso_id': preproceso['id'],
                'preproceso_nombre': preproceso['nombre']
            }

        except Exception as e:
            self.logger.error(f"Error convirtiendo preproceso a paso de pila: {e}")
            return None


# ==============================================================================
# CLASES DE UTILIDAD PARA HILOS
# ==============================================================================

class WorkerSignals(QObject):
    """Señales para el worker de carga de info de autor."""
    finished = pyqtSignal(object)

class AuthorInfoLoader(QRunnable):
    """
    Worker para cargar información de Wikipedia en segundo plano sin bloquear la UI.
    """
    def __init__(self, service: QuoteService, author_name: str):
        super().__init__()
        self.service = service
        self.author_name = author_name
        self.signals = WorkerSignals()

    def run(self):
        try:
            # Esta llamada puede tardar unos segundos
            info = self.service.get_author_info(self.author_name)
            self.signals.finished.emit(info)
        except Exception:
            self.signals.finished.emit(None)



