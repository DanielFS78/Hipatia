import pytest
import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Trabajador, Fabricacion, Producto, TrabajoLog, IncidenciaLog
from database.repositories.tracking_repository import TrackingRepository
from core.tracking_dtos import TrabajoLogDTO, PasoTrazabilidadDTO, IncidenciaLogDTO

@pytest.fixture
def db_session_factory():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    yield Session
    # Properly dispose engine to prevent ResourceWarning
    engine.dispose()

@pytest.fixture
def tracking_repo(db_session_factory):
    return TrackingRepository(db_session_factory)

@pytest.fixture
def seed_data(db_session_factory):
    session = db_session_factory()
    
    # Create Trabajador
    worker = Trabajador(nombre_completo='Juan Perez', tipo_trabajador=1, activo=True)
    session.add(worker)
    
    # Create Product
    product = Producto(
        codigo='PROD-001', 
        descripcion='Producto Test',
        departamento='Produccion',
        tipo_trabajador=1,
        tiene_subfabricaciones=False,
        tiempo_optimo=60.0
    )
    session.add(product)
    session.flush()

    # Create Fabricacion
    fab = Fabricacion(
        codigo='FAB-001', 
        descripcion='Fab Test', 
        # fecha_inicio is usually set through logic or defaults, model uses standard columns
    )
    session.add(fab)
    
    session.commit()
    
    data = {
        'worker_id': worker.id,
        'fabricacion_id': fab.id,
        'producto_codigo': product.codigo
    }
    session.close()
    return data

def test_iniciar_trabajo_creates_new_log(tracking_repo, seed_data):
    # Act
    log_dto = tracking_repo.iniciar_trabajo(
        qr_code="QR-TEST-001",
        trabajador_id=seed_data['worker_id'],
        fabricacion_id=seed_data['fabricacion_id'],
        producto_codigo=seed_data['producto_codigo']
    )
    
    # Assert
    assert log_dto is not None
    assert log_dto.qr_code == "QR-TEST-001"
    assert log_dto.trabajador_id == seed_data['worker_id']
    assert log_dto.estado == "en_proceso"
    assert isinstance(log_dto, TrabajoLogDTO)

def test_finalizar_trabajo_updates_log(tracking_repo, seed_data):
    # Arrange
    log_dto = tracking_repo.iniciar_trabajo(
        qr_code="QR-TEST-002",
        trabajador_id=seed_data['worker_id'],
        fabricacion_id=seed_data['fabricacion_id'],
        producto_codigo=seed_data['producto_codigo']
    )
    
    assert log_dto.tiempo_fin is None
    
    # Act
    updated_dto = tracking_repo.finalizar_trabajo_log(log_dto.id)
    
    # Assert
    assert updated_dto is not None
    assert updated_dto.tiempo_fin is not None
    assert updated_dto.estado == "completado"
    assert isinstance(updated_dto, TrabajoLogDTO)

def test_obtener_trabajo_por_qr_existing(tracking_repo, seed_data):
    # Arrange
    tracking_repo.iniciar_trabajo(
        qr_code="QR-TEST-003",
        trabajador_id=seed_data['worker_id'],
        fabricacion_id=seed_data['fabricacion_id'],
        producto_codigo=seed_data['producto_codigo']
    )
    
    # Act
    log_dto = tracking_repo.obtener_trabajo_por_qr("QR-TEST-003")
    
    # Assert
    assert log_dto is not None
    assert log_dto.qr_code == "QR-TEST-003"
    assert isinstance(log_dto, TrabajoLogDTO)

def test_obtener_trabajo_por_qr_non_existing(tracking_repo):
    # Act
    log_dto = tracking_repo.obtener_trabajo_por_qr("NON-EXISTENT-QR")
    
    # Assert
    assert log_dto is None

def test_registrar_incidencia(tracking_repo, seed_data):
    # Arrange
    log_dto = tracking_repo.iniciar_trabajo(
        qr_code="QR-TEST-004",
        trabajador_id=seed_data['worker_id'],
        fabricacion_id=seed_data['fabricacion_id'],
        producto_codigo=seed_data['producto_codigo']
    )
    
    # Act
    incidencia_dto = tracking_repo.registrar_incidencia(
        trabajo_log_id=log_dto.id,
        trabajador_id=seed_data['worker_id'],
        tipo_incidencia="defecto",
        descripcion="Test defect"
    )
    
    # Assert
    assert incidencia_dto is not None
    assert incidencia_dto.tipo_incidencia == "defecto"
    assert incidencia_dto.descripcion == "Test defect"
    assert isinstance(incidencia_dto, IncidenciaLogDTO)

def test_obtener_trabajos_activos(tracking_repo, seed_data):
    # Arrange
    tracking_repo.iniciar_trabajo(
        qr_code="QR-TEST-005",
        trabajador_id=seed_data['worker_id'],
        fabricacion_id=seed_data['fabricacion_id'],
        producto_codigo=seed_data['producto_codigo']
    )
    
    # Act
    activos = tracking_repo.obtener_trabajos_activos(seed_data['worker_id'])
    
    # Assert
    assert len(activos) >= 1
    assert any(job.qr_code == "QR-TEST-005" for job in activos)
    assert all(isinstance(job, TrabajoLogDTO) for job in activos)

def test_get_fabricaciones_por_trabajador_returns_dtos(tracking_repo, seed_data):
    # This test might return empty list if seed data didn't create link
    # But it should verify return TYPE is List[FabricacionAsignadaDTO] or DTO
    
    # Manually link worker to fabrication if needed?
    # tracking_repo.asignar_trabajador_a_fabricacion is likely needed, or manual link
    
    # Arrange - Manual link
    session = tracking_repo.session_factory()
    # Need to access link table directly or use model relationship
    # But link table `trabajador_fabricacion_link` is a Table object.
    # We can use execute insert.
    from sqlalchemy import insert
    from database.models import trabajador_fabricacion_link
    
    stmt = insert(trabajador_fabricacion_link).values(
        trabajador_id=seed_data['worker_id'], 
        fabricacion_id=seed_data['fabricacion_id'],
        estado='activo'
    )
    session.execute(stmt)
    session.commit()
    session.close()
    
    # Act
    fabs = tracking_repo.get_fabricaciones_por_trabajador(seed_data['worker_id'])
    
    # Assert
    # Import locally to assert
    from core.tracking_dtos import FabricacionAsignadaDTO
    
    assert len(fabs) >= 1
    assert any(f.id == seed_data['fabricacion_id'] for f in fabs)
    assert all(isinstance(f, FabricacionAsignadaDTO) for f in fabs)
