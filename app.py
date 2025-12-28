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
from openpyxl import Workbook
from datetime import date, datetime, timedelta, time
from concurrent_log_handler import ConcurrentRotatingFileHandler
from calculation_audit import CalculationDecision, DecisionStatus
from simulation_adapter import AdaptadorScheduler
from core.camera_manager import CameraManager, CameraInfo
try:
    import cv2
except (ImportError, AttributeError):
    cv2 = None
# ------------------- LIBRERÃ AS DE TERCEROS -------------------
import pandas as pd
import requests
from PIL import Image

# PyQt6 - Core y GUI
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap

# Imports para las nuevas funcionalidades de trazabilidad
# (Some might be unused if MainView was the only user, but let's be careful. Camera/QR might be used elsewhere?)
# core/camera_manager is used in app.py's global scope just below imports? No.
# core/qr_scanner?
# Let's keep them if unsure, or check usage.
from core.qr_scanner import QrScanner
from core.camera_manager import CameraManager
from core.qr_generator import QrGenerator
from core.label_manager import LabelManager

# PyQt6 - Widgets
from PyQt6.QtWidgets import (
    QApplication, QMessageBox
)

# ------------------- MÃ“DULOS DE LA APLICACIÃ“N LOCAL -------------------

# Lógica de la base de datos y repositorios
from database.database_manager import DatabaseManager
from core.app_model import AppModel
from controllers.app_controller import AppController

# Lógica de negocio y utilidades
import calendar_helper
from schedule_config import ScheduleConfig

# UI Imports
from ui.main_window import MainView

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


# =================================================================================
# FUNCIONES AUXILIARES
# =================================================================================

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


def setup_logging():
    """
    Configura un sistema de logging robusto con rotación de archivos.
    """
    # Crear directorio de logs si no existe
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "EvolucionTiempos.log")

    # Configurar formato de logging
    formatter = logging.Formatter(
        '%(asctime)s [ %(levelname)8s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )

    # Handler para archivo con rotación
    file_handler = ConcurrentRotatingFileHandler(
        log_file,
        "a",  # El modo "a" (append) es explícito y recomendado para este manejador
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Configurar logger raíz
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Limpiar handlers anteriores si existen
    logger.handlers.clear()

    # Añadir nuevos handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Configurar manejo de excepciones no capturadas
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.critical(
            "Excepción no capturada:",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception

    logging.info("=" * 70)
    logging.info("Sistema de logging configurado correctamente")
    logging.info(f"Archivo de log: {os.path.abspath(log_file)}")
    logging.info("=" * 70)


# =================================================================================



if __name__ == "__main__":
    setup_logging()
    app = QApplication(sys.argv)

    db_manager = None
    schedule_manager = None

    # Se inicializa 'config' antes del bloque 'try' para evitar errores de referencia
    config = configparser.ConfigParser()

    try:
        # RUTA CORREGIDA
        config_path = resource_path("config/config.ini")
        if not os.path.exists(config_path):
            raise FileNotFoundError("El archivo de configuración 'config.ini' no se encuentra.")
        config.read(config_path)

        # Inicializar gestor de la base de datos principal
        db_filename = "montaje.db"
        db_path = os.path.join(os.path.dirname(__file__), db_filename)
        db_manager = DatabaseManager(db_path=db_path)
        if not db_manager.conn:
            raise ConnectionError("No se pudo establecer conexión con la base de datos principal.")

        # Crear la instancia de configuración y asignarla al módulo calendar_helper
        schedule_manager = ScheduleConfig(db_manager)
        calendar_helper.set_schedule_config(schedule_manager)
        logging.info("Configuración de horario cargada y asignada al gestor de calendario.")

    except Exception as e:
        # Manejo de errores centralizado para cualquier fallo durante el arranque
        logging.critical(f"FALLO CRÃ TICO DURANTE LA INICIALIZACIÃ“N: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "Error Crítico",
            f"No se pudo iniciar la aplicación. Revise el archivo 'app.log' para más detalles.\n\nError: {e}"
        )
        sys.exit(1)


    # Doble comprobación para asegurar que todos los gestores se inicializaron
    if not all([db_manager, schedule_manager]):
        QMessageBox.critical(None, "Error Crítico", "Fallo al inicializar componentes clave de la aplicación.")
        sys.exit(1)

    logging.info("Creando instancias de Modelo, Vista y Controlador.")

    # --- FLUJO DE INICIALIZACIÃ“N CON AUTENTICACIÃ“N ---
    model = AppModel(db_manager)
    view = MainView()
    controller = AppController(model, view, schedule_manager)

    # Asignar controller a la vista (necesario para algunos diálogos)
    view.controller = controller

    # Inicializar la UI de la vista (pero NO mostrarla aún)
    view.init_ui()
    view.set_controller(controller)

    logging.info("Iniciando proceso de autenticación...")

    # Mostrar diálogo de login ANTES de mostrar cualquier ventana
    login_result = controller.handle_login()

    if not login_result:
        # Usuario canceló el login
        logging.info("Login cancelado por el usuario. Cerrando aplicación.")
        sys.exit(0)

    # Desempaquetar resultado del login
    user_data, authenticated = login_result

    if not authenticated or not user_data:
        # Autenticación fallida
        logging.warning("Autenticación fallida.")
        QMessageBox.warning(
            None,
            "Acceso Denegado",
            "Usuario o contraseña incorrectos."
        )
        sys.exit(1)

    # Autenticación exitosa - determinar qué interfaz mostrar
    logging.info(
        f"Usuario autenticado: {user_data.get('nombre', 'Usuario')} - Rol: {user_data.get('role', 'Desconocido')}")

    role = user_data.get('role', '')

    if role == 'Trabajador':
        # Lanzar interfaz simplificada para trabajadores
        logging.info("Lanzando interfaz de trabajador...")
        controller._launch_worker_interface()
        # NO conectamos señales ni mostramos la vista principal


    else:

        # Lanzar interfaz completa para Admin/Responsable

        logging.info("Lanzando interfaz de administrador...")

        controller.view.show()

        # Conectar señales DESPUÉS de mostrar la ventana

        controller.connect_signals()

    # Iniciar el bucle de eventos
    logging.info("Bucle de eventos de Qt iniciado.")
    sys.exit(app.exec())