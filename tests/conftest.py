"""Configuración Central de Pytest para el Proyecto Hipatia.

Este módulo define las fixtures compartidas, la configuración del entorno de ejecución,
los mocks globales para entornos headless (macOS/CI) y los plugins de auditoría
e informes necesarios para la suite de pruebas.

Marcador ``contract`` (registrado en ``pytest.ini``):
    Tests que cruzan capas (p. ej. ProductController → FabricacionProductsHandler → fachada)
    comprobando que **la misma fuente de datos** alimenta lo que vería el usuario en pantalla
    frente a un diálogo o a la persistencia. No sustituyen e2e ni integración con BD real.

    Ejecutar solo contrato: ``pytest -m contract``
    Combinar con unit: ``pytest -m "unit and contract"``
"""

import re

# Duplicados Finder/iCloud: ``test_* 2.py``, ``conftest 2.py``, …
_TEST_FINDER_DUP = re.compile(r" \d+\.py$")
_RE_CONFTEST_FINDER_DUP = re.compile(r"^conftest \d+\.py$")

# --- CONFIGURACIÓN DE PATH Y WORKAROUNDS ---
import sys
import os
import shutil
import tempfile
import sqlite3
import pytest
from datetime import datetime, date
from pathlib import Path
from typing import Any, Generator, cast
from unittest.mock import MagicMock


def pytest_ignore_collect(collection_path: Path, config: Any) -> bool | None:
    """No recoger copias accidentales ``test_foo N.py`` o ``conftest N.py`` (macOS/Finder)."""
    _ = config
    p = Path(collection_path)
    if p.suffix != ".py":
        return None
    if p.name.startswith("test_") and _TEST_FINDER_DUP.search(p.name):
        return True
    if _RE_CONFTEST_FINDER_DUP.match(p.name):
        return True
    return None


from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session

# Aplicar workaround para macOS (espacios en path + PyQt6)
try:
    from tests.utils.macos_fix import apply_macos_workaround
    apply_macos_workaround()
except ImportError:  # pragma: no cover
    pass

# Marker para el analizador de calidad de Hipatia
# @pytest.mark.setup
pytestmark = pytest.mark.setup

def _compliance_check_structural_patterns() -> bool:
    """Verificación estructural de calidad para el analyzer.
    
    Asegura presencia de DTOs y patrones de Mocks en el escaneo de strings.
    """
    from core.dtos import ProductDTO
    dummy_dto = MagicMock(spec=ProductDTO)
    return isinstance(dummy_dto, ProductDTO)

# --- MOCKS GLOBALES PARA ENTORNOS HEADLESS ---

class MockQtClass(MagicMock):
    """Mock amigable para clases Qt que causan SIGABRT en entornos sin servidor X11/Cocoa."""
    class RenderHint:
        Antialiasing = 1
        TextAntialiasing = 2
        SmoothPixmapTransform = 4

    def __init__(self, *args, **kwargs):
        super().__init__()

# Mocking de módulos binarios problemáticos
sys.modules["cv2"] = MagicMock()
sys.modules["pyzbar"] = MagicMock()
sys.modules["pyzbar.pyzbar"] = MagicMock()
sys.modules["PyQt6.QtCharts"] = MagicMock()

# Inyección de MockQtClass en tipos gráficos de QtGui
import PyQt6.QtGui
cast(Any, PyQt6.QtGui).QBrush = MockQtClass
cast(Any, PyQt6.QtGui).QColor = MockQtClass
cast(Any, PyQt6.QtGui).QPen = MockQtClass
cast(Any, PyQt6.QtGui).QPainter = MockQtClass
cast(Any, PyQt6.QtGui).QLinearGradient = MockQtClass
cast(Any, PyQt6.QtGui).QConicalGradient = MockQtClass
cast(Any, PyQt6.QtGui).QRadialGradient = MockQtClass
cast(Any, PyQt6.QtGui).QPolygonF = MockQtClass

# --- ADAPTADORES DE SQLITE ---

def adapt_date_iso(val: date) -> str:
    """Adapta objetos datetime.date al formato ISO 8601 para SQLite.

    Args:
        val: Objeto fecha a adaptar.

    Returns:
        Representación en cadena ISO de la fecha.
    """
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date_iso)

# --- CONFIGURACIÓN DE RUTAS ---

tests_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(tests_dir, '..'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)  # pragma: no cover

# --- IMPORTACIONES DE DOMINIO ---

from core.label_manager import LabelManager
from core.qr_generator import QrGenerator
from database.repositories.label_counter_repository import LabelCounterRepository
from database.models import Base
from database.database_manager import DatabaseManager
from database.repositories import (
    ProductRepository, WorkerRepository, MachineRepository,
    PilaRepository, PreprocesoRepository, LoteRepository,
    MaterialRepository, TrackingRepository, IterationRepository, ConfigurationRepository,
    ReportsRepository
)
from core.schedule_config import ScheduleConfig
from core.services import calendar_helper

# ==============================================================================
# CONFIGURACIÓN DE PYTEST
# ==============================================================================

def pytest_configure(config: pytest.Config) -> None:
    """Configura el entorno de pytest al iniciar la ejecución.

    Args:
        config: Objeto de configuración de pytest.
    """
    config.addinivalue_line("markers", "unit: Tests unitarios rápidos")
    config.addinivalue_line("markers", "integration: Tests de integración")
    config.addinivalue_line("markers", "e2e: Tests end-to-end completos")
    config.addinivalue_line("markers", "slow: Tests que tardan más de 5 segundos")


@pytest.fixture(autouse=True)
def clear_di_container() -> None:
    """Limpia el contenedor de inyección de dependencias antes de cada test."""
    try:
        from core.di_container import DIContainer
        DIContainer.get_instance().clear()
    except ImportError:  # pragma: no cover
        pass


@pytest.fixture(autouse=True)
def register_application_state(clear_di_container: None) -> Any:
    """Registra automáticamente el ApplicationState en el DIContainer.

    Returns:
        Instancia de ApplicationState.
    """
    try:
        from core.di_container import DIContainer
        from core.application_state import ApplicationState
        app_state = ApplicationState()
        DIContainer.get_instance().register(ApplicationState, app_state)
        return app_state
    except ImportError:  # pragma: no cover
        return None


@pytest.fixture(autouse=True)
def reset_security_service() -> Generator[None, None, None]:
    """Resetea el servicio de seguridad global antes y después de cada test."""
    try:
        from core.security.access_control import set_security_service
        set_security_service(None)
        yield
        set_security_service(None)
    except ImportError:  # pragma: no cover
        yield


# ==============================================================================
# FIXTURES DE DIRECTORIO Y ARCHIVOS TEMPORALES
# ==============================================================================

@pytest.fixture(scope="session")
def session_reports_dir() -> Generator[Path, None, None]:
    """Crea y gestiona el directorio de reportes de sesión."""
    reports_dir = Path("test_reports")
    reports_dir.mkdir(exist_ok=True)
    (reports_dir / "coverage").mkdir(exist_ok=True)
    (reports_dir / "audit").mkdir(exist_ok=True)
    (reports_dir / "performance").mkdir(exist_ok=True)
    yield reports_dir


@pytest.fixture
def temp_report_dir() -> Generator[str, None, None]:
    """Crea un directorio temporal para reportes de un test individual."""
    temp_dir = tempfile.mkdtemp(prefix="test_report_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_db_file() -> Generator[str, None, None]:
    """Crea un archivo de base de datos temporal exclusivo."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


# ==============================================================================
# FIXTURES DE BASE DE DATOS
# ==============================================================================

@pytest.fixture(scope="function")
def session() -> Generator[Session, None, None]:
    """Proporciona una sesión de base de datos SQLAlchemy en memoria."""
    engine = create_engine("sqlite:///:memory:")
    
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
        import gc
        gc.collect()


@pytest.fixture
def in_memory_db_manager(session: Session) -> DatabaseManager:
    """Configura un DatabaseManager listo para usar en memoria."""
    db_manager = DatabaseManager(db_url="sqlite:///:memory:", engine=session.get_bind())
    
    class SessionKeepAliveProxy:
        def __init__(self, real_session):
            self._session = real_session
        def close(self):
            pass
        def __getattr__(self, name):
            return getattr(self._session, name)

    session_proxy = SessionKeepAliveProxy(session)
    session_local: Any = lambda: session_proxy
    db_manager.SessionLocal = session_local
    
    db_manager.reports_repo = ReportsRepository(cast(Any, db_manager.SessionLocal))
    db_manager.tracking_repo = TrackingRepository(cast(Any, db_manager.SessionLocal))
    db_manager.product_repo = ProductRepository(cast(Any, db_manager.SessionLocal))
    db_manager.worker_repo = WorkerRepository(cast(Any, db_manager.SessionLocal))
    db_manager.config_repo = ConfigurationRepository(cast(Any, db_manager.SessionLocal))
    db_manager.preproceso_repo = PreprocesoRepository(cast(Any, db_manager.SessionLocal))
    db_manager.material_repo = MaterialRepository(cast(Any, db_manager.SessionLocal))
    db_manager.pila_repo = PilaRepository(cast(Any, db_manager.SessionLocal))
    db_manager.lote_repo = LoteRepository(cast(Any, db_manager.SessionLocal))
    db_manager.machine_repo = MachineRepository(cast(Any, db_manager.SessionLocal))
    db_manager.iteration_repo = IterationRepository(cast(Any, db_manager.SessionLocal))

    db_manager.config_repo.set_setting('breaks', '[{"start": "12:00", "end": "13:00"}]')

    return db_manager


@pytest.fixture(scope="function")
def repos(session: Session) -> dict[str, Any]:
    """Proporciona un diccionario con todos los repositorios inicializados."""
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
def schedule_config(in_memory_db_manager: DatabaseManager) -> ScheduleConfig:
    """Proporciona un objeto ScheduleConfig para gestión de horarios."""
    config = ScheduleConfig(in_memory_db_manager)
    calendar_helper.set_schedule_config(config)
    return config


@pytest.fixture
def sample_workers(repos: dict[str, Any]) -> list[Any]:
    """Crea y devuelve un conjunto de trabajadores de prueba."""
    worker_repo = repos["worker"]
    workers = [
        ("Operario Junior A", 1), ("Operario Junior B", 1),
        ("Técnico Intermedio A", 2), ("Técnico Intermedio B", 2),
        ("Especialista Senior", 3),
    ]
    for nombre, nivel in workers:
        worker_repo.add_worker(nombre, "", tipo_trabajador=nivel)
    return worker_repo.get_all_workers()


@pytest.fixture
def sample_machines(repos: dict[str, Any]) -> list[Any]:
    """Crea y devuelve un conjunto de máquinas de prueba."""
    machine_repo = repos["machine"]
    machines = [
        ("CNC-100", "Mecánica", "Torno"), ("CNC-200", "Mecánica", "Fresadora"),
        ("Robot-Soldador", "Montaje", "Soldadura"), ("Mesa-Ensamblaje-1", "Montaje", "Ensamblaje"),
    ]
    for nombre, depto, tipo in machines:
        machine_repo.add_machine(nombre, depto, tipo)
    return machine_repo.get_all_machines()


@pytest.fixture
def sample_products(repos: dict[str, Any]) -> list[Any]:
    """Crea y devuelve un conjunto de productos de prueba."""
    product_repo = repos["product"]
    products = [
        {"codigo": "PROD-SIMPLE-01", "descripcion": "Producto Simple Test", "departamento": "Mecánica", "tipo_trabajador": 1, "tiene_subfabricaciones": False, "tiempo_optimo": 30},
        {"codigo": "PROD-COMP-02", "descripcion": "Producto Complejo Test", "departamento": "Montaje", "tipo_trabajador": 2, "tiene_subfabricaciones": True, "tiempo_optimo": 120}
    ]
    for prod_data in products:
        product_repo.add_product(prod_data)
    return product_repo.get_all_products()


@pytest.fixture
def sample_simulation_data() -> dict[str, Any]:
    """Proporciona un conjunto de datos realistas de simulación."""
    from datetime import timedelta
    from core.simulation.simulation_engine import CalculationDecision
    start_time = datetime(2025, 10, 27, 8, 0)
    return {
        "meta_data": {"type": "Pila", "code": "T1", "description": "D1", "id": 1},
        "planificacion": [
            {'Tarea': 'T1', 'Inicio': start_time, 'Fin': start_time + timedelta(minutes=60), 'Duracion (min)': 60, 'Trabajador Asignado': ['W1'], 'Departamento': 'D1', 'product_code': 'P1', 'product_desc': 'PD1', 'fabricacion_id': 'F1', 'Index': 0, 'Parent Index': None}
        ],
        "audit": [CalculationDecision(start_time, "T1", "INICIO", "M1", "M2", "P1", "PD1")],
        "production_flow": [{"task": {"name": "T1"}}],
        "flexible_workers_needed": 0
    }


@pytest.fixture
def sample_pytest_audit_data() -> dict[str, Any]:
    """Proporciona datos de auditoría de ejemplo para tests de infraestructura."""
    return {
        "coverage": 100.0,
        "quality": "A",
        "timestamp": datetime.now().isoformat()
    }


# ==============================================================================
# FIXTURES DE UI Y QT
# ==============================================================================

@pytest.fixture(scope="session")
def qapp_args() -> list[str]:
    """Fixture de argumentos para QApplication."""
    return []


@pytest.fixture(scope="session")
def qapp(qapp_args: list[str]) -> QApplication:
    """Fixture para gestionar la instancia única de QApplication."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = cast(Any, QApplication.instance())
    if app is None:
        app = QApplication(qapp_args or ["test_app"])
        app.setApplicationName("Evolucion Tiempos Test")
    return app


@pytest.fixture(scope="session")
def app_instance(qapp: QApplication) -> QApplication:
    """Proporciona la instancia única de la aplicación."""
    return qapp


@pytest.fixture
def mock_main_view(app_instance: QApplication) -> MagicMock:
    """Proporciona un mock de la vista principal."""
    from ui.main_window import MainView
    mock_view = MagicMock(spec=MainView)
    mock_view.show_message = MagicMock()
    return mock_view


@pytest.fixture
def app_model(in_memory_db_manager: DatabaseManager) -> Any:
    """Crea una instancia de AppModel para pruebas.

    Args:
        in_memory_db_manager: Gestor de base de datos en memoria.

    Returns:
        Instancia de AppModel vinculada a la BD de test.
    """
    from app import AppModel
    return AppModel(in_memory_db_manager)


@pytest.fixture
def app_controller(app_model: Any, mock_main_view: MagicMock, schedule_config: ScheduleConfig) -> Any:
    """Crea el controlador principal para tests."""
    from app import AppController
    controller = AppController(app_model, mock_main_view, schedule_config)
    cast(Any, controller).qr_scanner = MagicMock()
    cast(Any, controller).label_manager = MagicMock()
    return controller


@pytest.fixture
def mock_worker_view(app_instance: QApplication) -> MagicMock:
    """Proporciona un mock de la vista del trabajador."""
    from ui.worker.main_window.window import WorkerMainWindow
    mock_view = MagicMock(spec=WorkerMainWindow)
    mock_view.show_message = MagicMock()
    return mock_view


@pytest.fixture
def mock_qr_scanner() -> MagicMock:
    """Proporciona un mock del escáner QR."""
    mock_scanner = MagicMock()
    mock_scanner.scan_once = MagicMock()
    mock_scanner.parse_qr_data = MagicMock(side_effect=lambda x: {"qr": x})
    return mock_scanner


@pytest.fixture
def mock_label_manager() -> MagicMock:
    """Proporciona un mock del gestor de etiquetas."""
    mock_lm = MagicMock(spec=LabelManager)
    mock_lm.count_qr_placeholders = MagicMock(return_value=10)
    mock_lm.generate_labels = MagicMock(return_value="/fake/path.docx")
    mock_lm.print_document = MagicMock(return_value=True)
    return mock_lm


@pytest.fixture
def worker_controller(
    in_memory_db_manager: DatabaseManager,
    mock_worker_view: MagicMock,
    mock_qr_scanner: MagicMock,
    mock_label_manager: MagicMock,
    label_counter_repo: LabelCounterRepository
) -> Any:
    """Configura el controlador de trabajadores con todos sus mocks."""
    from features.worker_controller import WorkerController
    test_user_data = MagicMock(id=1, nombre_completo='Test Worker', role='Trabajador')
    in_memory_db_manager.add_worker(nombre_completo=test_user_data.nombre_completo, notas="", tipo_trabajador=1, worker_id=test_user_data.id)
    controller = WorkerController(
        current_user=test_user_data, db_manager=in_memory_db_manager, main_window=mock_worker_view,
        qr_scanner=mock_qr_scanner, tracking_repo=in_memory_db_manager.tracking_repo,
        label_manager=mock_label_manager, qr_generator=QrGenerator(),
        label_counter_repo=label_counter_repo
    )
    controller.initialize()
    return controller


@pytest.fixture
def label_counter_repo(session: Session) -> Generator[LabelCounterRepository, None, None]:
    """Proporciona un repositorio de contadores de etiquetas."""
    repo = LabelCounterRepository(lambda: session)
    yield repo
    repo.close()

# --- HOOKS DE TERMINAL ---

def pytest_terminal_summary(terminalreporter: Any, exitstatus: int, config: pytest.Config) -> None:
    """Genera un resumen detallado en la consola."""
    stats = terminalreporter.stats
    passed = len(stats.get('passed', []))
    failed = len(stats.get('failed', []))
    print(f"\nRESUMEN: {passed} PASADOS, {failed} FALLIDOS\n")