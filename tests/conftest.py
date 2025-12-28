# tests/conftest.py
"""
Configuración Central Mejorada para Pytest
==========================================
- Define fixtures compartidas
- Registra plugins de auditoría
- Configura métricas de cobertura
- Prepara datos de prueba comunes
"""

# --- AÑADE ESTE BLOQUE AL PRINCIPIO DE tests/conftest.py ---
import sys
import os
import warnings
from unittest.mock import MagicMock

# Global Mocks for missing environmental dependencies
sys.modules["cv2"] = MagicMock()
sys.modules["PyQt6.QtCharts"] = MagicMock()
sys.modules["pyzbar"] = MagicMock()
sys.modules["pyzbar.pyzbar"] = MagicMock()

# Suprimir DeprecationWarning de sqlite3 date adapter (Python 3.12+)
# Registrar adaptador para datetime.date (Fix DeprecationWarning Python 3.12+)
import sqlite3
from datetime import date

def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date_iso)

# 1. Obtiene la ruta a la carpeta 'tests' (donde está este conftest.py)
tests_dir = os.path.dirname(__file__)

# 2. Obtiene la ruta a la carpeta raíz del proyecto (la que está UN NIVEL ARRIBA)
project_root = os.path.abspath(os.path.join(tests_dir, '..'))

# 3. Añade la carpeta raíz al path de Python para que pueda encontrar 'app.py'
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- FIN DEL BLOQUE ---
import pytest
import tempfile
import shutil
from datetime import datetime, date, time
from pathlib import Path

import shutil
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication

# ------------------------------------------------------------------------------
# ❌ IMPORTACIONES PROBLEMÁTICAS ELIMINADAS DE AQUÍ
# ------------------------------------------------------------------------------
# Se han movido:
# from app import AppModel, AppController, MainView
# from ui.worker.worker_main_window import WorkerMainWindow
# from features.worker_controller import WorkerController
# ------------------------------------------------------------------------------

from core.label_manager import LabelManager
from core.qr_generator import QrGenerator
from database.repositories.label_counter_repository import LabelCounterRepository

# Importaciones de SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Importaciones de la aplicación
from database.models import Base
from database.database_manager import DatabaseManager
from database.repositories import (
    ProductRepository, WorkerRepository, MachineRepository,
    PilaRepository, PreprocesoRepository, LoteRepository,
    MaterialRepository, TrackingRepository, IterationRepository, ConfigurationRepository
)
# NOTA: Importar repositorios y modelos está BIEN. No dependen de cv2.

from tests.reporting.audit_report_generator import PytestAuditPlugin
from schedule_config import ScheduleConfig
import calendar_helper


# ==============================================================================
# CONFIGURACIÓN DE PYTEST
# ==============================================================================

def pytest_configure(config):
    """
    Hook de configuración ejecutado al iniciar pytest.
    Registra plugins personalizados y configura el entorno.
    """
    # Registrar plugin de auditoría ISO 9001 (DESACTIVADO por petición del usuario)
    # audit_plugin = PytestAuditPlugin()
    # config.pluginmanager.register(audit_plugin, "iso_audit_plugin")

    # Configurar marcadores personalizados
    config.addinivalue_line(
        "markers", "unit: Tests unitarios rápidos"
    )
    config.addinivalue_line(
        "markers", "integration: Tests de integración"
    )
    config.addinivalue_line(
        "markers", "e2e: Tests end-to-end completos"
    )
    config.addinivalue_line(
        "markers", "slow: Tests que tardan más de 5 segundos"
    )


# ==============================================================================
# FIXTURES DE DIRECTORIO Y ARCHIVOS TEMPORALES
# ==============================================================================

@pytest.fixture(scope="session")
def test_reports_dir():
    """
    Crea directorio para almacenar todos los reportes de tests.
    Se limpia al finalizar la sesión completa de tests.
    """
    reports_dir = Path("test_reports")
    reports_dir.mkdir(exist_ok=True)

    # Crear subdirectorios
    (reports_dir / "coverage").mkdir(exist_ok=True)
    (reports_dir / "audit").mkdir(exist_ok=True)
    (reports_dir / "performance").mkdir(exist_ok=True)

    yield reports_dir

    # Limpieza opcional (comentar si se desea conservar)
    # shutil.rmtree(reports_dir, ignore_errors=True)


@pytest.fixture
def temp_report_dir():
    """
    Crea directorio temporal para informes individuales de cada test.
    Se limpia automáticamente al finalizar el test.
    """
    temp_dir = tempfile.mkdtemp(prefix="test_report_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_db_file():
    """Crea un archivo de base de datos temporal para tests de persistencia."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


# ==============================================================================
# FIXTURES DE BASE DE DATOS
# ==============================================================================

@pytest.fixture(scope="function")
def session() -> Session:
    """
    Crea una base de datos SQLite en memoria limpia para cada test.
    Garantiza aislamiento total entre tests.
    """
    engine = create_engine("sqlite:///:memory:")
    
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
    db_session = SessionLocal()

    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def in_memory_db_manager(session):
    """
    Proporciona un DatabaseManager conectado a BD en memoria.
    Incluye configuración inicial básica.
    """
    connection = session.connection().connection
    db_manager = DatabaseManager(existing_connection=connection)

    # Crear tabla de configuración
    db_manager.cursor.execute(
        "CREATE TABLE IF NOT EXISTS configuracion "
        "(clave TEXT PRIMARY KEY, valor TEXT NOT NULL)"
    )
    db_manager.conn.commit()

    # Configuración predeterminada de horarios
    db_manager.config_repo.set_setting('breaks', '[{"start": "12:00", "end": "13:00"}]')

    yield db_manager

    # Teardown explícito para evitar ResourceWarning
    if db_manager.engine:
        db_manager.engine.dispose()


@pytest.fixture(scope="function")
def repos(session: Session):
    """
    Proporciona diccionario con todos los repositorios inicializados.
    Facilita acceso rápido a cualquier repositorio en los tests.
    """
    return {
        "product": ProductRepository(lambda: session),
        "worker": WorkerRepository(lambda: session),
        "machine": MachineRepository(lambda: session),
        "pila": PilaRepository(lambda: session),
        "preproceso": PreprocesoRepository(lambda: session),
        "lote": LoteRepository(lambda: session),
        "material": MaterialRepository(lambda: session),
        "tracking": TrackingRepository(lambda: session),
        "iteration": IterationRepository(lambda: session),
        "configuration": ConfigurationRepository(lambda: session)
    }


# ==============================================================================
# FIXTURES DE CONFIGURACIÓN Y UTILIDADES
# ==============================================================================

@pytest.fixture
def schedule_config(in_memory_db_manager):
    """
    Proporciona un ScheduleConfig configurado con horarios estándar.
    Configura también el helper global de calendario.
    """
    config = ScheduleConfig(in_memory_db_manager)
    calendar_helper.set_schedule_config(config)
    return config


@pytest.fixture
def sample_workers(repos):
    """Crea trabajadores de prueba con diferentes niveles de habilidad."""
    worker_repo = repos["worker"]

    workers = [
        ("Operario Junior A", 1),
        ("Operario Junior B", 1),
        ("Técnico Intermedio A", 2),
        ("Técnico Intermedio B", 2),
        ("Especialista Senior", 3),
    ]

    for nombre, nivel in workers:
        worker_repo.add_worker(nombre, "", tipo_trabajador=nivel)

    return worker_repo.get_all_workers()


@pytest.fixture
def sample_machines(repos):
    """Crea máquinas de prueba para diferentes procesos."""
    machine_repo = repos["machine"]

    machines = [
        ("CNC-100", "Mecánica", "Torno"),
        ("CNC-200", "Mecánica", "Fresadora"),
        ("Robot-Soldador", "Montaje", "Soldadura"),
        ("Mesa-Ensamblaje-1", "Montaje", "Ensamblaje"),
    ]

    for nombre, depto, tipo in machines:
        machine_repo.add_machine(nombre, depto, tipo)

    return machine_repo.get_all_machines()


@pytest.fixture
def sample_products(repos):
    """Crea productos de prueba con diferentes configuraciones."""
    product_repo = repos["product"]

    products = [
        {
            "codigo": "PROD-SIMPLE-01",
            "descripcion": "Producto Simple de Prueba",
            "departamento": "Mecánica",
            "tipo_trabajador": 1,
            "tiene_subfabricaciones": False,
            "tiempo_optimo": 30
        },
        {
            "codigo": "PROD-COMPLEJO-01",
            "descripcion": "Producto Complejo con Subfabricaciones",
            "departamento": "Montaje",
            "tipo_trabajador": 2,
            "tiene_subfabricaciones": True,
            "tiempo_optimo": 120
        }
    ]

    for prod_data in products:
        product_repo.add_product(prod_data)

    return product_repo.get_all_products()


# ==============================================================================
# FIXTURES DE DATOS DE SIMULACIÓN
# ==============================================================================

@pytest.fixture
def sample_simulation_data():
    """
    Proporciona conjunto de datos realistas de simulación
    para tests de generación de informes.
    """
    from datetime import timedelta
    from simulation_engine import CalculationDecision, DecisionStatus

    start_time = datetime(2025, 10, 27, 8, 0)

    return {
        "meta_data": {
            "type": "Pila",
            "code": "TEST-PILA-001",
            "description": "Pila de Prueba para Tests",
            "id": 999
        },
        "planificacion": [
            {
                'Tarea': 'Preparación Material',
                'Inicio': start_time,
                'Fin': start_time + timedelta(minutes=60),
                'Duracion (min)': 60,
                'Trabajador Asignado': ['Operario A'],
                'Departamento': 'Mecánica',
                'product_code': 'P1',
                'product_desc': 'Producto 1',
                'fabricacion_id': 'TEST-PILA-001',
                'Index': 0,
                'Parent Index': None
            },
            {
                'Tarea': 'Mecanizado',
                'Inicio': start_time + timedelta(minutes=60),
                'Fin': start_time + timedelta(minutes=180),
                'Duracion (min)': 120,
                'Trabajador Asignado': ['Operario B'],
                'Departamento': 'Mecánica',
                'product_code': 'P1',
                'product_desc': 'Producto 1',
                'fabricacion_id': 'TEST-PILA-001',
                'Index': 1,
                'Parent Index': 0
            }
        ],
        "audit": [
            CalculationDecision(
                start_time,
                "Preparación Material",
                "INICIO_TAREA",
                "Iniciando tarea",
                "Iniciando preparación de material",
                "P1",
                "Producto 1"
            )
        ],
        "production_flow": [{"task": {"name": "Preparación Material"}}],
        "flexible_workers_needed": 0
    }


@pytest.fixture
def sample_pytest_audit_data():
    """
    Proporciona datos simulados de auditoría pytest
    para tests del sistema de informes.
    """
    return {
        "validation_results": [
            {"test_name": "test_database_connection", "status": "PASS"},
            {"test_name": "test_product_crud", "status": "PASS"},
            {"test_name": "test_simulation_engine", "status": "PASS"},
            {"test_name": "test_report_generation", "status": "PASS"},
        ],
        "coverage": {
            "percent_covered": 92.5,
            "lines_covered": 1850,
            "lines_total": 2000
        },
        "test_duration": 45.3,
        "timestamp": datetime.now().isoformat()
    }


# ==============================================================================
# FIXTURES DE PYTEST-QT (si se usan tests de UI)
# ==============================================================================
# La fixture qtbot es proporcionada automáticamente por pytest-qt
# No es necesario definirla manualmente amenos que no se use el plugin.
# Si pytest-qt está instalado, esta definición manual causaba conflictos/errores
# al pasar 'app' en lugar de 'request' al constructor de QtBot.

# HOOKS DE PYTEST PARA METRICAS
# ==============================================================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook para capturar resultados de cada test.
    Permite recopilar métricas y estadísticas.
    """
    outcome = yield
    rep = outcome.get_result()

    # Añadir información de timing
    if rep.when == "call":
        setattr(item, f"rep_{rep.when}", rep)

        # Marcar tests lentos automáticamente
        if hasattr(rep, 'duration') and rep.duration > 5:
            item.add_marker(pytest.mark.slow)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Hook para mostrar resumen personalizado al final de los tests.
    """
    stats = terminalreporter.stats
    passed = len(stats.get('passed', []))
    failed = len(stats.get('failed', []))
    skipped = len(stats.get('skipped', []))
    error = len(stats.get('error', []))

    print(f"\n{'=' * 70}")
    print(f"RESUMEN DE EJECUCIÓN DE TESTS")
    print(f"{'=' * 70}")
    print(f"✓ Tests Exitosos: {passed}")
    print(f"✗ Tests Fallidos: {failed}")
    if skipped:
        print(f"⚠ Tests Saltados: {skipped}")
    if error:
        print(f"🔥 Errores: {error}")
    print(f"Total: {passed + failed + skipped + error}")
    print(f"{'=' * 70}\n")


# ==============================================================================
# FIXTURES DE SIMULACIÓN DE APLICACIÓN (MOCKS)
# ==============================================================================

@pytest.fixture(scope="session")
def app_instance():
    """Crea una instancia de QApplication (necesaria para widgets)"""
    app = QApplication.instance() or QApplication(sys.argv)
    return app


@pytest.fixture
def label_counter_repo(tmp_path):
    """Crea un repo de contadores de etiquetas en un archivo temporal."""
    test_db_path = tmp_path / "test_etiquetas.db"
    repo = LabelCounterRepository(db_path=str(test_db_path))
    yield repo
    repo.close()


@pytest.fixture
def app_model(in_memory_db_manager):
    """Crea una instancia del AppModel usando la base de datos de test."""
    # --- ✅ IMPORTACIÓN MOVILIDA AQUÍ ---
    from app import AppModel
    return AppModel(in_memory_db_manager)


@pytest.fixture
def mock_main_view(app_instance):
    """Crea un Mock (simulacro) de la MainView (GUI)."""
    # --- ✅ IMPORTACIÓN MOVILIDA AQUÍ ---
    from ui.main_window import MainView
    mock_view = MagicMock(spec=MainView)
    mock_view.show_message = MagicMock()
    return mock_view


@pytest.fixture
def app_controller(app_model, mock_main_view, schedule_config):
    """Crea el controlador principal de Administrador."""
    # --- ✅ IMPORTACIÓN MOVILIDA AQUÍ ---
    from app import AppController
    # Nota: app_controller no usa el scanner ni el label_manager directamente
    # en el flujo de test, así que podemos pasarlos como None.
    controller = AppController(app_model, mock_main_view, schedule_config)
    controller.qr_scanner = MagicMock()
    controller.label_manager = MagicMock()
    return controller


@pytest.fixture
def mock_worker_view(app_instance):
    """Crea un Mock (simulacro) de la WorkerMainWindow (GUI)."""
    # --- ✅ IMPORTACIÓN MOVILIDA AQUÍ ---
    from ui.worker.worker_main_window import WorkerMainWindow
    mock_view = MagicMock(spec=WorkerMainWindow)
    mock_view.show_message = MagicMock()
    mock_view.update_tasks_list = MagicMock()
    mock_view.update_task_state = MagicMock()
    return mock_view


@pytest.fixture
def mock_qr_scanner():
    """Crea un Mock (simulacro) del QRScanner."""
    mock_scanner = MagicMock()
    mock_scanner.scan_once = MagicMock()
    mock_scanner.parse_qr_data = MagicMock(side_effect=lambda x: {"qr": x})
    return mock_scanner


@pytest.fixture
def mock_label_manager():
    """Crea un Mock (simulacro) del LabelManager."""
    mock_lm = MagicMock(spec=LabelManager)
    mock_lm.count_qr_placeholders = MagicMock(return_value=10)
    mock_lm.generate_labels = MagicMock(return_value="/fake/path/labels.docx")
    mock_lm.print_document = MagicMock(return_value=True)
    return mock_lm


@pytest.fixture
def worker_controller(
        in_memory_db_manager,
        mock_worker_view,
        mock_qr_scanner,
        mock_label_manager,
        label_counter_repo
):
    """Crea el controlador de Trabajador con todos sus mocks."""
    # --- ✅ IMPORTACIÓN MOVILIDA AQUÍ ---
    from features.worker_controller import WorkerController

    test_user_data = {
        'id': 1,
        'nombre': 'Test Worker',
        'role': 'Trabajador'
    }

    # Añadimos manually el trabajador a la BD de test
    in_memory_db_manager.worker_repo.add_worker(
        nombre_completo=test_user_data['nombre'],
        notas="Test user",
        tipo_trabajador=1,
        worker_id=test_user_data['id']  # Forzamos el ID
    )

    controller = WorkerController(
        current_user=test_user_data,
        db_manager=in_memory_db_manager,
        main_window=mock_worker_view,
        qr_scanner=mock_qr_scanner,
        tracking_repo=in_memory_db_manager.tracking_repo,
        label_manager=mock_label_manager,
        qr_generator=QrGenerator(),  # Usamos el real, es seguro
        label_counter_repo=label_counter_repo
    )
    controller.initialize()
    return controller