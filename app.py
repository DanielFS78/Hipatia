# -*- coding: utf-8 -*-
"""
Nombre del Módulo: app.py
Descripcion: Punto de entrada principal para la aplicación Hipatia (Cálculo de Tiempos de Fabricación).
             Se encarga de la inicialización de QT, configuración de BD, logging y arranque de controladores.
             También crea e instala el ``QtLogHandler`` que alimenta la terminal interna de advertencias
             y errores visible en la pantalla de inicio.
"""
from __future__ import annotations
import configparser
import logging
import os
import sys
from typing import TYPE_CHECKING, Optional, Tuple, Any

if TYPE_CHECKING:
    from core.qt_log_handler import QtLogHandler

from concurrent_log_handler import ConcurrentRotatingFileHandler
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget

# Módulos locales
from database.database_manager import DatabaseManager
from core.app_model import AppModel
from controllers.app_controller import AppController
from core.services import calendar_helper
from core.schedule_config import ScheduleConfig
from ui.main_window import MainView
from core.utils.helpers import resource_path

# global dependencies para fallback y tests
cv2: Any = None

def _check_dependencies() -> None:
    """
    Verifica e importa dependencias opcionales dinámicamente.
    En particular, intenta cargar OpenCV (cv2) para funcionalidades de cámara.
    """
    global cv2
    try:
        import cv2 as cv_lib
        cv2 = cv_lib
    except (ImportError, AttributeError):
        cv2 = None

def _fix_qt_macos() -> None:
    """
    Aplica correcciones específicas para macOS.
    Resuelve problemas conocidos de Qt con espacios en rutas y configuración de plugins.
    """
    _check_dependencies()
    if sys.platform == "darwin":
        existing_qt_path = os.environ.get("QT_PLUGIN_PATH", "")
        if not (existing_qt_path and " " not in existing_qt_path and os.path.exists(existing_qt_path)):
            tmp_pyqt = "/tmp/pyqt6_venv"
            if os.path.exists(os.path.join(tmp_pyqt, "PyQt6", "Qt6", "plugins")):
                qt6_dir = os.path.join(tmp_pyqt, "PyQt6", "Qt6")
                os.environ["QT_PLUGIN_PATH"] = os.path.join(qt6_dir, "plugins")
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(qt6_dir, "plugins", "platforms")
                if tmp_pyqt not in sys.path:
                    sys.path.insert(0, tmp_pyqt)

def setup_logging() -> None:
    """
    Configura el sistema de registro (logging) en archivo y consola.

    Implementa rotación de archivos concurrente y salida por consola con
    diferentes niveles de detalle. El ``QtLogHandler`` NO se crea aquí:
    se instala en ``main()`` después de crear ``QApplication``, ya que
    ``QObject`` requiere que exista una instancia de ``QApplication``.
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "EvolucionTiempos.log")
    formatter = logging.Formatter('%(asctime)s [%(levelname)8s] %(name)s: %(message)s', datefmt='%H:%M:%S')

    file_handler = ConcurrentRotatingFileHandler(log_file, "a", maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    for h in root_logger.handlers: h.close()
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    def handle_exception(exc_type: type[BaseException], exc_value: BaseException, exc_traceback: Any) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.critical("Excepción no capturada:", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception
    logging.info("Sistema de logging iniciado correctamente.")

def main() -> None:
    """
    Punto de entrada principal que orquesta el arranque de la aplicación.

    Inicializa la base de datos, el modelo, la vista y el controlador principal,
    gestionando también el proceso de autenticación de usuario. Después del
    login conecta el ``QtLogHandler`` al ``HomeWidget`` para que la terminal
    interna de la pantalla de inicio reciba los mensajes de advertencia y error
    generados durante la sesión.

    El ``QtLogHandler`` se crea DESPUÉS de ``QApplication`` porque ``QObject``
    no puede instanciarse antes de que exista un event-loop de Qt. El buffer
    interno del handler almacena los warnings del arranque y los reproduce
    en cuanto el widget está listo.
    """
    _fix_qt_macos()
    setup_logging()

    app = QApplication(sys.argv)

    # Crear el handler Qt AHORA que QApplication ya existe
    qt_handler: "QtLogHandler | None" = None
    try:
        from core.qt_log_handler import QtLogHandler
        qt_handler = QtLogHandler()
        logging.getLogger().addHandler(qt_handler)
    except Exception as exc:
        logging.warning("QtLogHandler no disponible: %s", exc)
    
    config = configparser.ConfigParser()
    try:
        config_path = resource_path("config/config.ini")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuracion no encontrada en {config_path}")
        config.read(config_path)

        from database.config import DatabaseConfig
        saved_mode = config.get("Connection", "mode", fallback=None)
        
        if saved_mode == 'sqlite':
            DatabaseConfig.set_db_url(f"sqlite:///{os.path.abspath('data/montaje.db')}")
        elif not saved_mode:
            from ui.dialogs.connection_dialog import ConnectionDialog
            dialog = ConnectionDialog()
            if dialog.exec():
                mode, remember = dialog.get_selection()
                if mode == 'sqlite':
                    DatabaseConfig.set_db_url(f"sqlite:///{os.path.abspath('data/montaje.db')}")
                if remember:
                    if not config.has_section("Connection"): config.add_section("Connection")
                    config.set("Connection", "mode", mode)
                    with open(config_path, 'w') as configfile: config.write(configfile)
            else:
                sys.exit(0)

        db_manager = DatabaseManager()
        if not db_manager.engine:
            raise ConnectionError("Fallo de conexión a BD.")

        schedule_manager = ScheduleConfig(db_manager)
        calendar_helper.set_schedule_config(schedule_manager)

    except Exception as e:
        logging.critical(f"Error fatal en arranque: {e}", exc_info=True)
        QMessageBox.critical(None, "Error Crítico", f"Fallo al iniciar: {e}")
        sys.exit(1)

    model = AppModel(db_manager)
    view = MainView()
    controller = AppController(model, view, schedule_manager)
    
    controller.initialize_infra()
    view.set_controller(controller)
    view.init_ui()
    
    if controller.session_controller is None:
        logging.critical("SessionController no inicializado.")
        sys.exit(1)
        
    login_result = controller.session_controller.handle_login()
    if not login_result:
        sys.exit(0)

    user_data, authenticated = login_result
    
    if not authenticated or not user_data:
        QMessageBox.warning(None, "Acceso Denegado", "Credenciales inválidas.")
        sys.exit(1)

    # --- Pantalla de salud del sistema (post-login, pre-ventana principal) ---
    from PyQt6.QtWidgets import QDialog
    from ui.startup_screen import StartupScreen
    startup = StartupScreen(db_manager, run_tests=True)
    result = startup.exec()
    health_report = startup._report

    if result == QDialog.DialogCode.Rejected and health_report is None:
        # BD no disponible o usuario canceló sin informe — no arrancar
        sys.exit(0)

    role = getattr(user_data, 'role', '')
    if role == 'Trabajador':
        controller.session_controller.launch_worker_interface()
    else:
        controller.connect_all_signals()
        if isinstance(controller.view, QWidget):
            # Pasar el informe al HomeWidget si está disponible
            home = controller.view.pages.get("home")
            if home is not None and hasattr(home, "update_health_report") and health_report is not None:
                home.update_health_report(health_report)
            # Conectar el handler de log Qt a la terminal interna del HomeWidget
            if home is not None and hasattr(home, "connect_log_handler") and qt_handler is not None:
                home.connect_log_handler(qt_handler)
            controller.view.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()