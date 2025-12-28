
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from database.models import (
    Trabajador, Fabricacion, Producto, TrabajoLog, IncidenciaLog,
    PasoTrazabilidad, trabajador_fabricacion_link, fabricacion_productos, Maquina,
    IncidenciaAdjunto
)
from database.repositories.tracking_repository import TrackingRepository
from core.tracking_dtos import TrabajoLogDTO
from sqlalchemy import insert

@pytest.fixture
def session_no_close(session):
    original_close = session.close
    session.close = MagicMock()
    yield session
    session.close = original_close

@pytest.fixture
def tracking_repo_test(session_no_close):
    return TrackingRepository(lambda: session_no_close)

@pytest.fixture
def seed_stats_data(session_no_close):
    session = session_no_close
    
    # Worker
    w = Trabajador(nombre_completo="Stats Worker", tipo_trabajador=1, activo=True)
    session.add(w)
    session.commit()
    
    # Fab
    f = Fabricacion(codigo="FAB-STATS", descripcion="Stats Fab")
    session.add(f)
    session.commit()
    
    # Prod
    p = Producto(codigo="PROD-STATS", descripcion="Stats Prod", departamento="S", tipo_trabajador=1, tiene_subfabricaciones=False)
    session.add(p)
    session.commit()
    
    # Completed Jobs (3)
    for i in range(3):
        t = TrabajoLog(
            qr_code=f"QR-STAT-{i}",
            trabajador_id=w.id,
            fabricacion_id=f.id,
            producto_codigo=p.codigo,
            tiempo_inicio=datetime.now(timezone.utc) - timedelta(hours=2),
            tiempo_fin=datetime.now(timezone.utc) - timedelta(hours=1),
            duracion_segundos=3600,
            estado='completado',
            created_at=datetime.now(timezone.utc)
        )
        session.add(t)
    
    # In Progress Job (1)
    t_prog = TrabajoLog(
        qr_code="QR-STAT-PROG",
        trabajador_id=w.id,
        fabricacion_id=f.id,
        producto_codigo=p.codigo,
        tiempo_inicio=datetime.now(timezone.utc),
        estado='en_proceso',
        created_at=datetime.now(timezone.utc)
    )
    session.add(t_prog)
    session.commit()
    
    return w.id, f.id, p.codigo

class TestTrackingRepoStatsExport:
    
    def test_obtener_estadisticas_trabajador(self, tracking_repo_test, seed_stats_data):
        w_id, _, _ = seed_stats_data
        
        stats = tracking_repo_test.obtener_estadisticas_trabajador(w_id)
        
        assert stats['unidades_completadas'] == 3
        assert stats['tiempo_total_segundos'] == 3600 * 3
        assert stats['tiempo_promedio_segundos'] == 3600

    def test_obtener_estadisticas_trabajador_with_date_filters(self, tracking_repo_test, seed_stats_data):
        """Test statistics with fecha_inicio and fecha_fin filters."""
        w_id, _, _ = seed_stats_data
        
        # Use very old and very future dates to include all
        fecha_inicio = datetime.now(timezone.utc) - timedelta(days=365)
        fecha_fin = datetime.now(timezone.utc) + timedelta(days=1)
        
        stats = tracking_repo_test.obtener_estadisticas_trabajador(
            w_id, 
            fecha_inicio=fecha_inicio, 
            fecha_fin=fecha_fin
        )
        
        assert stats['unidades_completadas'] == 3
        assert 'tiempo_total_segundos' in stats

    def test_obtener_estadisticas_trabajador_empty(self, tracking_repo_test):
        """Test statistics when worker has no completed jobs."""
        # Use non-existent worker
        stats = tracking_repo_test.obtener_estadisticas_trabajador(99999)
        
        assert stats['unidades_completadas'] == 0
        assert stats['tiempo_total_segundos'] == 0
        assert stats['tiempo_promedio_segundos'] == 0
        
    def test_obtener_estadisticas_fabricacion(self, tracking_repo_test, seed_stats_data):
        _, f_id, _ = seed_stats_data
        
        stats = tracking_repo_test.obtener_estadisticas_fabricacion(f_id)
        
        assert stats['unidades_completadas'] == 3
        assert stats['unidades_en_proceso'] == 1
        # No assigned workers yet via link
        assert stats['trabajadores_asignados'] == 0

    def test_get_trabajo_logs_por_trabajador(self, tracking_repo_test, seed_stats_data):
        w_id, _, _ = seed_stats_data
        
        logs = tracking_repo_test.get_trabajo_logs_por_trabajador(w_id)
        assert len(logs) == 4 # 3 completed + 1 in progress
        assert isinstance(logs[0], TrabajoLogDTO)

    def test_upsert_trabajo_log_created(self, tracking_repo_test, seed_stats_data):
        w_id, f_id, p_code = seed_stats_data
        
        data = {
            "qr_code": "QR-UPSERT-NEW",
            "trabajador_id": w_id,
            "fabricacion_id": f_id,
            "producto_codigo": p_code,
            "estado": "en_proceso",
            "tiempo_inicio": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        status, t_id = tracking_repo_test.upsert_trabajo_log_from_dict(data)
        assert status == 'created'
        assert t_id is not None
        
        # Verify creation
        log = tracking_repo_test.obtener_trabajo_por_qr("QR-UPSERT-NEW")
        assert log is not None
        assert log.id == t_id

    def test_upsert_trabajo_log_updated(self, tracking_repo_test, seed_stats_data, session_no_close):
        """Test upsert updates existing trabajo with newer data."""
        w_id, f_id, p_code = seed_stats_data
        session = session_no_close
        
        # Create initial with old updated_at
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        t = TrabajoLog(
            qr_code="QR-UPSERT-UPD2",
            trabajador_id=w_id,
            fabricacion_id=f_id,
            producto_codigo=p_code,
            estado='en_proceso',
            updated_at=old_time,
            created_at=old_time
        )
        session.add(t)
        session.commit()
        original_id = t.id
        
        # Prepare update data (newer timestamp)
        new_time = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        data = {
            "qr_code": "QR-UPSERT-UPD2",
            "estado": "pausado",
            "updated_at": new_time,
            "incidencias": [],
        }
        
        status, t_id = tracking_repo_test.upsert_trabajo_log_from_dict(data)
        
        assert status == 'updated'
        assert t_id == original_id
        
        # Verify update
        log = tracking_repo_test.obtener_trabajo_por_qr("QR-UPSERT-UPD2")
        assert log.estado == "pausado"

    def test_upsert_trabajo_log_no_qr_code(self, tracking_repo_test):
        """Test upsert returns error when qr_code is missing."""
        data = {
            "estado": "en_proceso",
            "trabajador_id": 1,
        }
        
        status, t_id = tracking_repo_test.upsert_trabajo_log_from_dict(data)
        
        assert status == 'error'
        assert t_id is None


    def test_upsert_trabajo_skipped(self, tracking_repo_test, seed_stats_data, session_no_close):
        w_id, f_id, p_code = seed_stats_data
        session = session_no_close
        
        # Create initial with RECENT update time
        t = TrabajoLog(
            qr_code="QR-UPSERT-SKIP",
            trabajador_id=w_id,
            fabricacion_id=f_id,
            producto_codigo=p_code,
            updated_at=datetime.now(timezone.utc)
        )
        session.add(t)
        session.commit()
        
        # Incoming data is OLDER
        old_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        data = {
            "qr_code": "QR-UPSERT-SKIP",
            "estado": "pausado",
            "updated_at": old_time
        }
        
        status, t_id = tracking_repo_test.upsert_trabajo_log_from_dict(data)
        assert status == 'skipped'

    def test_get_data_for_export(self, tracking_repo_test, seed_stats_data):
        w_id, _, _ = seed_stats_data
        # Use a very old date to ensure inclusion
        since = datetime.now(timezone.utc) - timedelta(days=365)
        
        data = tracking_repo_test.get_data_for_export(w_id, since)
        
        # 3 completed + 1 in progress = 4
        assert len(data) >= 4, f"Expected 4+, got {len(data)}. Data: {data}"
        assert isinstance(data[0], dict)
        assert 'qr_code' in data[0]

    def test_obtener_trabajo_por_id(self, tracking_repo_test, seed_stats_data, session_no_close):
        w_id, f_id, p_code = seed_stats_data
        t = tracking_repo_test.iniciar_trabajo("QR-ID-TEST", w_id, f_id, p_code)
        
        dto = tracking_repo_test.obtener_trabajo_por_id(t.id)
        assert dto is not None
        assert dto.qr_code == "QR-ID-TEST"
        
        assert tracking_repo_test.obtener_trabajo_por_id(99999) is None

    def test_assignment_ops(self, tracking_repo_test, seed_stats_data, session_no_close):
        w_id, f_id, _ = seed_stats_data
        
        # Initial check
        workers = tracking_repo_test.obtener_trabajadores_de_fabricacion(f_id)
        assert len(workers) == 0
        
        # Assign
        tracking_repo_test.asignar_trabajador_a_fabricacion(w_id, f_id)
        workers_after = tracking_repo_test.obtener_trabajadores_de_fabricacion(f_id)
        assert len(workers_after) == 1
        
        # Desasign
        success = tracking_repo_test.desasignar_trabajador_de_fabricacion(w_id, f_id)
        assert success is True
        workers_final = tracking_repo_test.obtener_trabajadores_de_fabricacion(f_id)
        assert len(workers_final) == 0

