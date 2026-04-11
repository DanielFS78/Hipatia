# -*- coding: utf-8 -*-
"""
Nombre del Módulo: app

Descripción: Punto de entrada principal para la aplicación Hipatia (cálculo de tiempos de fabricación).
             Inicializa Qt, configuración de BD, logging y arranque de controladores.

             Crea e instala ``QtLogHandler`` para la terminal visual de logs: tras el login se conecta
             a ``HomeWidget`` (rol Responsable u otros con vista principal) o a ``WorkerMainWindow``
             (rol Trabajador, pestaña Log), una sola vez por sesión.

             En ejecutable PyInstaller (Windows), ``_fix_qt_macos`` no aplica; BD, logs y configuración
             editable se resuelven con ``core.paths`` (directorio del ``.exe``).

             En ``main()``, antes de ``QApplication(sys.argv)``, se aplica
             ``QApplication.setHighDpiScaleFactorRoundingPolicy(PassThrough)`` cuando Qt6 lo permite,
             para alinear el escalado fraccional del SO (p. ej. 125 % / 150 % en Windows) con el motor Qt.
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
from core.paths import get_writable_app_root, resolve_user_config_ini

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
    log_root = get_writable_app_root() / "logs"
    log_root.mkdir(parents=True, exist_ok=True)
    log_file = os.path.join(str(log_root), "EvolucionTiempos.log")
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
    y el flujo de autenticación. Tras el login y la pantalla de salud del sistema:

    - Rol distinto de ``Trabajador``: conecta ``QtLogHandler`` al terminal de
      ``HomeWidget`` y muestra ``MainView``.
    - Rol ``Trabajador``: abre la interfaz de operario y conecta el mismo handler
      al ``LogTerminalWidget`` de la pestaña Log en ``WorkerMainWindow``.

    ``QtLogHandler`` se crea después de ``QApplication`` (requiere ``QObject``).
    El buffer interno guarda mensajes hasta la primera ``connect_to_widget`` y
    luego los reproduce en la terminal activa.
    """
    _fix_qt_macos()
    setup_logging()

    # Escalado fraccional del SO (p. ej. Windows 125 % / 150 %): alinear con Qt6 antes de crear la app.
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except (AttributeError, RuntimeError):
        pass

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
        config_path = resolve_user_config_ini(resource_path)
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuracion no encontrada en {config_path}")
        config.read(config_path)

        from database.config import DatabaseConfig
        saved_mode = config.get("Connection", "mode", fallback=None)

        def _default_sqlite_url() -> str:
            data_dir = get_writable_app_root() / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_file = data_dir / "montaje.db"
            return f"sqlite:///{db_file.resolve().as_posix()}"

        if saved_mode == 'sqlite':
            DatabaseConfig.set_db_url(_default_sqlite_url())
        elif not saved_mode:
            from ui.dialogs.connection_dialog import ConnectionDialog
            dialog = ConnectionDialog()
            if dialog.exec():
                mode, remember = dialog.get_selection()
                if mode == 'sqlite':
                    DatabaseConfig.set_db_url(_default_sqlite_url())
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
        worker_window = getattr(
            controller.session_controller, "worker_window", None
        )
        if (
            worker_window is not None
            and qt_handler is not None
            and hasattr(worker_window, "connect_log_handler")
        ):
            worker_window.connect_log_handler(qt_handler)
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