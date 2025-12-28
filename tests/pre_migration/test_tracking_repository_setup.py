import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from database.repositories.tracking_repository import TrackingRepository
from core.tracking_dtos import TrabajoLogDTO, PasoTrazabilidadDTO, IncidenciaLogDTO

@pytest.fixture
def db_session_factory():
    """Create a temporary in-memory database for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    yield Session
    # Properly dispose engine to prevent ResourceWarning
    engine.dispose()

@pytest.fixture
def tracking_repo(db_session_factory):
    """Initialize TrackingRepository with the test database."""
    return TrackingRepository(db_session_factory)

def test_repository_initialization(tracking_repo):
    """Test that the repository is initialized correctly."""
    assert tracking_repo is not None
    assert tracking_repo.session_factory is not None

def test_session_management(tracking_repo):
    """Test that the repository can create and close sessions."""
    session = tracking_repo.session_factory()
    assert session.is_active
    session.close()

def test_dto_imports():
    """Test that DTOs are importable and available."""
    assert TrabajoLogDTO is not None
    assert PasoTrazabilidadDTO is not None
    assert IncidenciaLogDTO is not None

def test_repository_has_expected_methods(tracking_repo):
    """Test that the repository has the expected methods."""
    methods = [
        'iniciar_trabajo',
        'finalizar_trabajo_log',
        'registrar_incidencia',
        'obtener_trabajo_por_qr',
        'get_paso_activo_por_trabajador',
        'obtener_trabajos_activos',
        'get_fabricaciones_por_trabajador'
    ]
    for method in methods:
        assert hasattr(tracking_repo, method), f"TrackingRepository missing method: {method}"
