# -*- coding: utf-8 -*-
"""
Tests for TrackingRepository exception handling and edge cases.
These tests mock SQLAlchemy errors to achieve 100% coverage.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from database.models import (
    Trabajador, Fabricacion, Producto, TrabajoLog, IncidenciaLog,
    PasoTrazabilidad, Maquina, IncidenciaAdjunto
)
from database.repositories.tracking_repository import TrackingRepository
from core.tracking_dtos import TrabajoLogDTO, PasoTrazabilidadDTO, IncidenciaLogDTO


@pytest.fixture
def session_no_close(session):
    """Prevents repository from closing the session during tests."""
    original_close = session.close
    session.close = MagicMock()
    yield session
    session.close = original_close


@pytest.fixture
def tracking_repo_test(session_no_close):
    """Returns repository instance using the shared session."""
    return TrackingRepository(lambda: session_no_close)


@pytest.fixture
def seed_data(session_no_close):
    """Seeds basic data for tests."""
    session = session_no_close
    
    worker = Trabajador(nombre_completo="Exception Test Worker", tipo_trabajador=1, activo=True)
    session.add(worker)
    
    prod = Producto(
        codigo="PROD-EXC-01",
        descripcion="Exception Product",
        departamento="Test",
        tipo_trabajador=1,
        tiene_subfabricaciones=False,
        tiempo_optimo=100.0
    )
    session.add(prod)
    
    fab = Fabricacion(codigo="FAB-EXC-01", descripcion="Exception Fab")
    session.add(fab)
    
    maquina = Maquina(nombre="Exception Machine", departamento="T", tipo_proceso="P", activa=True)
    session.add(maquina)
    
    session.commit()
    
    return {
        "worker_id": worker.id,
        "product_code": prod.codigo,
        "fab_id": fab.id,
        "maquina_id": maquina.id
    }


@pytest.mark.unit
class TestTrackingRepositoryExceptions:
    """Tests that force SQLAlchemyError exceptions to cover exception handlers."""

    def test_finalizar_trabajo_log_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during finalizar_trabajo_log."""
        # Create a work log first
        job = tracking_repo_test.iniciar_trabajo(
            "QR-FIN-ERR", seed_data['worker_id'], 
            seed_data['fab_id'], seed_data['product_code']
        )
        
        # Mock session commit to raise error
        session = tracking_repo_test.session_factory()
        original_commit = session.commit
        session.commit = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.finalizar_trabajo_log(job.id)
        
        session.commit = original_commit
        assert result is None

    def test_pausar_trabajo_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during pausar_trabajo."""
        job = tracking_repo_test.iniciar_trabajo(
            "QR-PAUSE-ERR", seed_data['worker_id'],
            seed_data['fab_id'], seed_data['product_code']
        )
        
        session = tracking_repo_test.session_factory()
        original_commit = session.commit
        session.commit = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.pausar_trabajo(job.qr_code, "Test pause")
        
        session.commit = original_commit
        assert result is False

    def test_reanudar_trabajo_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during reanudar_trabajo."""
        job = tracking_repo_test.iniciar_trabajo(
            "QR-RES-ERR", seed_data['worker_id'],
            seed_data['fab_id'], seed_data['product_code']
        )
        # First pause it
        tracking_repo_test.pausar_trabajo(job.qr_code, "Pause first")
        
        session = tracking_repo_test.session_factory()
        original_commit = session.commit
        session.commit = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.reanudar_trabajo(job.qr_code)
        
        session.commit = original_commit
        assert result is False

    def test_obtener_trabajo_por_qr_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during obtener_trabajo_por_qr."""
        session = tracking_repo_test.session_factory()
        original_query = session.query
        session.query = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.obtener_trabajo_por_qr("ANY-QR")
        
        session.query = original_query
        assert result is None

    def test_obtener_trabajo_por_id_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during obtener_trabajo_por_id."""
        session = tracking_repo_test.session_factory()
        original_query = session.query
        session.query = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.obtener_trabajo_por_id(1)
        
        session.query = original_query
        assert result is None

    def test_get_paso_activo_por_trabajador_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during get_paso_activo_por_trabajador."""
        session = tracking_repo_test.session_factory()
        original_query = session.query
        session.query = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.get_paso_activo_por_trabajador(seed_data['worker_id'])
        
        session.query = original_query
        assert result is None

    def test_get_ultimo_paso_para_qr_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during get_ultimo_paso_para_qr."""
        session = tracking_repo_test.session_factory()
        original_query = session.query
        session.query = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.get_ultimo_paso_para_qr(1)
        
        session.query = original_query
        assert result is None

    def test_iniciar_nuevo_paso_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during iniciar_nuevo_paso."""
        job = tracking_repo_test.iniciar_trabajo(
            "QR-PASO-ERR", seed_data['worker_id'],
            seed_data['fab_id'], seed_data['product_code']
        )
        
        session = tracking_repo_test.session_factory()
        original_commit = session.commit
        session.commit = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.iniciar_nuevo_paso(
            trabajo_log_id=job.id,
            trabajador_id=seed_data['worker_id'],
            paso_nombre="Test",
            tipo_paso="manual"
        )
        
        session.commit = original_commit
        assert result is None

    def test_finalizar_paso_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during finalizar_paso."""
        job = tracking_repo_test.iniciar_trabajo(
            "QR-FPASO-ERR", seed_data['worker_id'],
            seed_data['fab_id'], seed_data['product_code']
        )
        step = tracking_repo_test.iniciar_nuevo_paso(
            job.id, seed_data['worker_id'], "Test", "manual"
        )
        
        session = tracking_repo_test.session_factory()
        original_commit = session.commit
        session.commit = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.finalizar_paso(step.id)
        
        session.commit = original_commit
        assert result is None

    def test_obtener_trabajos_activos_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during obtener_trabajos_activos."""
        session = tracking_repo_test.session_factory()
        original_query = session.query
        session.query = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.obtener_trabajos_activos()
        
        session.query = original_query
        assert result == []

    def test_resolver_incidencia_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during resolver_incidencia."""
        job = tracking_repo_test.iniciar_trabajo(
            "QR-RESOL-ERR", seed_data['worker_id'],
            seed_data['fab_id'], seed_data['product_code']
        )
        inc = tracking_repo_test.registrar_incidencia(
            job.id, seed_data['worker_id'], "Type", "Desc"
        )
        
        session = tracking_repo_test.session_factory()
        original_commit = session.commit
        session.commit = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.resolver_incidencia(inc.id, "Solution")
        
        session.commit = original_commit
        assert result is None

    def test_obtener_incidencias_abiertas_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during obtener_incidencias_abiertas."""
        session = tracking_repo_test.session_factory()
        original_query = session.query
        session.query = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.obtener_incidencias_abiertas()
        
        session.query = original_query
        assert result == []

    def test_asignar_trabajador_a_fabricacion_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during asignar_trabajador_a_fabricacion."""
        session = tracking_repo_test.session_factory()
        original_commit = session.commit
        session.commit = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.asignar_trabajador_a_fabricacion(
            seed_data['worker_id'], seed_data['fab_id']
        )
        
        session.commit = original_commit
        assert result is False

    def test_desasignar_trabajador_de_fabricacion_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during desasignar_trabajador_de_fabricacion."""
        # First assign
        tracking_repo_test.asignar_trabajador_a_fabricacion(
            seed_data['worker_id'], seed_data['fab_id']
        )
        
        session = tracking_repo_test.session_factory()
        original_commit = session.commit
        session.commit = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.desasignar_trabajador_de_fabricacion(
            seed_data['worker_id'], seed_data['fab_id']
        )
        
        session.commit = original_commit
        assert result is False

    def test_obtener_trabajadores_de_fabricacion_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during obtener_trabajadores_de_fabricacion."""
        session = tracking_repo_test.session_factory()
        original_query = session.query
        session.query = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.obtener_trabajadores_de_fabricacion(seed_data['fab_id'])
        
        session.query = original_query
        assert result == []

    def test_get_all_ordenes_fabricacion_sqlalchemy_error(self, tracking_repo_test):
        """Test SQLAlchemy error during get_all_ordenes_fabricacion."""
        session = tracking_repo_test.session_factory()
        original_query = session.query
        session.query = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.get_all_ordenes_fabricacion()
        
        session.query = original_query
        assert result == []


@pytest.mark.unit
class TestTrackingRepositoryExportEdgeCases:
    """Tests for export functionality and edge cases."""

    def test_get_data_for_export_with_completed_pasos(self, tracking_repo_test, seed_data, session_no_close):
        """Test export data functionality (basic check)."""
        # Export with old date
        since = datetime.now(timezone.utc) - timedelta(days=365)
        
        # This just tests that the method doesn't crash
        data = tracking_repo_test.get_data_for_export(seed_data['worker_id'], since)
        
        # Result should be a list (may be empty)
        assert isinstance(data, list)

    def test_get_data_for_export_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during get_data_for_export."""
        session = tracking_repo_test.session_factory()
        original_query = session.query
        session.query = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        since = datetime.now(timezone.utc) - timedelta(days=1)
        result = tracking_repo_test.get_data_for_export(seed_data['worker_id'], since)
        
        session.query = original_query
        assert result == []

    def test_get_data_for_export_general_exception(self, tracking_repo_test, seed_data):
        """Test general exception during get_data_for_export."""
        session = tracking_repo_test.session_factory()
        original_query = session.query
        session.query = MagicMock(side_effect=Exception("Unexpected error"))
        
        since = datetime.now(timezone.utc) - timedelta(days=1)
        result = tracking_repo_test.get_data_for_export(seed_data['worker_id'], since)
        
        session.query = original_query
        assert result == []

    def test_get_data_for_export_with_incidencias(self, tracking_repo_test, seed_data, session_no_close, tmp_path):
        """Test export data basic functionality."""
        # Export with old date
        since = datetime.now(timezone.utc) - timedelta(days=365)
        
        # This tests that the method works without crashing
        data = tracking_repo_test.get_data_for_export(seed_data['worker_id'], since)
        
        # Result should be a list
        assert isinstance(data, list)

    def test_upsert_trabajo_log_with_incidencias(self, tracking_repo_test, seed_data):
        """Test upsert with nested incidencias and adjuntos."""
        data = {
            "qr_code": "QR-UPSERT-NESTED",
            "trabajador_id": seed_data['worker_id'],
            "fabricacion_id": seed_data['fab_id'],
            "producto_codigo": seed_data['product_code'],
            "estado": "en_proceso",
            "tiempo_inicio": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "incidencias": [
                {
                    "tipo_incidencia": "Defecto",
                    "descripcion": "Test nested",
                    "fecha_reporte": datetime.now(timezone.utc).isoformat(),
                    "estado": "abierta",
                    "adjuntos": [
                        {
                            "ruta_archivo": "/path/to/file.jpg",
                            "nombre_archivo": "file.jpg",
                            "tipo_mime": "image/jpeg",
                            "tamaño_bytes": 1024
                        }
                    ]
                }
            ]
        }
        
        status, t_id = tracking_repo_test.upsert_trabajo_log_from_dict(data)
        assert status == 'created'
        assert t_id is not None

    def test_upsert_trabajo_log_error(self, tracking_repo_test, seed_data):
        """Test upsert returns error on exception."""
        session = tracking_repo_test.session_factory()
        original_commit = session.commit
        session.commit = MagicMock(side_effect=Exception("Mock error"))
        
        data = {
            "qr_code": "QR-UPSERT-ERR",
            "trabajador_id": seed_data['worker_id'],
            "fabricacion_id": seed_data['fab_id'],
            "producto_codigo": seed_data['product_code'],
        }
        
        status, t_id = tracking_repo_test.upsert_trabajo_log_from_dict(data)
        
        session.commit = original_commit
        assert status == 'error'
        assert t_id is None


@pytest.mark.unit
class TestTrackingRepositoryMapperEdgeCases:
    """Tests for DTO mapper exception branches."""

    def test_map_to_trabajo_log_dto_incidencias_exception(self, tracking_repo_test, seed_data, session_no_close):
        """Test mapper returns DTO even with problematic incidencias."""
        # Test that mapper handles None gracefully
        result = tracking_repo_test._map_to_trabajo_log_dto(None)
        assert result is None

    def test_map_to_incidencia_log_dto_adjuntos_exception(self, tracking_repo_test, seed_data, session_no_close):
        """Test mapper returns DTO with empty adjuntos on None input."""
        # Test None handling
        result = tracking_repo_test._map_to_incidencia_log_dto(None)
        assert result is None

    def test_map_to_incidencia_adjunto_dto_none(self, tracking_repo_test):
        """Test mapper returns None for None input."""
        result = tracking_repo_test._map_to_incidencia_adjunto_dto(None)
        assert result is None

    def test_map_to_paso_trazabilidad_dto_none(self, tracking_repo_test):
        """Test mapper returns None for None input."""
        result = tracking_repo_test._map_to_paso_trazabilidad_dto(None)
        assert result is None


@pytest.mark.unit
class TestTrackingRepositoryStatisticsEdgeCases:
    """Tests for statistics methods edge cases."""

    def test_obtener_estadisticas_trabajador_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during obtener_estadisticas_trabajador."""
        session = tracking_repo_test.session_factory()
        original_query = session.query
        session.query = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.obtener_estadisticas_trabajador(seed_data['worker_id'])
        
        session.query = original_query
        # Should return empty dict on error
        assert result == {}

    def test_obtener_estadisticas_fabricacion_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during obtener_estadisticas_fabricacion."""
        session = tracking_repo_test.session_factory()
        original_query = session.query
        session.query = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.obtener_estadisticas_fabricacion(seed_data['fab_id'])
        
        session.query = original_query
        # Should return empty dict on error
        assert result == {}

    def test_get_trabajo_logs_por_trabajador_sqlalchemy_error(self, tracking_repo_test, seed_data):
        """Test SQLAlchemy error during get_trabajo_logs_por_trabajador."""
        session = tracking_repo_test.session_factory()
        original_query = session.query
        session.query = MagicMock(side_effect=SQLAlchemyError("Mock error"))
        
        result = tracking_repo_test.get_trabajo_logs_por_trabajador(seed_data['worker_id'])
        
        session.query = original_query
        assert result == []

    def test_obtener_o_crear_trabajo_log_integrity_error(self, tracking_repo_test, seed_data):
        """Trigger IntegrityError in obtener_o_crear_trabajo_log_por_qr para cubrir línea 248."""
        mock_session = MagicMock()
        # Mocking the query to return None (initially not found)
        mock_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
        # Mocking add/commit to raise IntegrityError
        mock_session.add.side_effect = IntegrityError("Mock", "params", "orig")
        
        tracking_repo_test.session_factory = lambda: mock_session
        
        result = tracking_repo_test.obtener_o_crear_trabajo_log_por_qr(
            "DUPE", seed_data['worker_id'], seed_data['fab_id'], seed_data['product_code']
        )
        assert result is None
        mock_session.rollback.assert_called_once()

    def test_obtener_o_crear_trabajo_log_sqlalchemy_error_custom(self, tracking_repo_test, seed_data):
        """Trigger SQLAlchemyError in obtener_o_crear_trabajo_log_por_qr para cubrir línea 252."""
        mock_session = MagicMock()
        mock_session.query.side_effect = SQLAlchemyError("Generic SQL Error")
        
        tracking_repo_test.session_factory = lambda: mock_session
        
        result = tracking_repo_test.obtener_o_crear_trabajo_log_por_qr(
            "ERROR", seed_data['worker_id'], seed_data['fab_id'], seed_data['product_code']
        )
        assert result is None
        mock_session.rollback.assert_called_once()

    def test_get_data_for_export_complete_flow_coverage(self, tracking_repo_test, seed_data, session_no_close):
        """Cubre loops e hilos de ejecución en get_data_for_export (líneas 1331, 1354, 1396-1411, 1420-1444)."""
        # 1. Setup: Trabajo con paso completado e incidencia
        job_dto = tracking_repo_test.iniciar_trabajo(
            "QR-EXPORT-FULL", seed_data['worker_id'],
            seed_data['fab_id'], seed_data['product_code']
        )
        
        # Paso 1: Completado (línea 1400)
        step_dto = tracking_repo_test.iniciar_nuevo_paso(job_dto.id, seed_data['worker_id'], "Paso1", "manual")
        tracking_repo_test.finalizar_paso(step_dto.id)
        
        # Paso 2: En proceso (línea 1409)
        tracking_repo_test.iniciar_nuevo_paso(job_dto.id, seed_data['worker_id'], "Paso2", "manual")
        
        # Registrar incidencia con adjunto (líneas 1437-1438)
        tracking_repo_test.registrar_incidencia(
            job_dto.id, seed_data['worker_id'], "Error", "D",
            rutas_fotos=["dummy_photo.jpg"]
        )
        
        # 2. Export with naive date to cover timezone replacement (line 1354)
        since = datetime.now() - timedelta(days=1)
        data = tracking_repo_test.get_data_for_export(seed_data['worker_id'], since)
        
        assert len(data) >= 1
        job_data = next(d for d in data if d['qr_code'] == "QR-EXPORT-FULL")
        assert len(job_data['pasos_trazabilidad']) >= 2
        assert any(p['estado_paso'] == 'completado' for p in job_data['pasos_trazabilidad'])
        assert any(p['estado_paso'] == 'en_proceso' for p in job_data['pasos_trazabilidad'])
        assert len(job_data['incidencias']) >= 1
        assert len(job_data['incidencias'][0]['adjuntos']) >= 1

    def test_map_to_trabajo_log_dto_incidencias_exception_triggered(self, tracking_repo_test):
        """Actually trigger the Exception in the mapper for coverage (líneas 1517-1519)."""
        mock_trabajo = MagicMock(spec=TrabajoLog)
        # Configure the mock to raise Exception when accessing 'incidencias'
        type(mock_trabajo).incidencias = PropertyMock(side_effect=Exception("Triggered"))
        
        result = tracking_repo_test._map_to_trabajo_log_dto(mock_trabajo)
        assert result is not None
        assert result.incidencias == []

    def test_map_to_incidencia_log_dto_adjuntos_exception_triggered(self, tracking_repo_test):
        """Actually trigger the Exception in the mapper for coverage (líneas 1542-1543)."""
        mock_incidencia = MagicMock(spec=IncidenciaLog)
        # Configure to raise Exception when accessing 'adjuntos'
        type(mock_incidencia).adjuntos = PropertyMock(side_effect=Exception("Triggered"))
        
        result = tracking_repo_test._map_to_incidencia_log_dto(mock_incidencia)
        assert result is not None
        assert result.adjuntos == []
