"""Tests para cubrir líneas faltantes en TrackingRepository."""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from database.repositories.tracking_repository import TrackingRepository
from database.models import Fabricacion, Trabajador, TrabajoLog, PasoTrazabilidad, Producto
from core.tracking_dtos import FabricacionAsignadaDTO

@pytest.mark.unit
class TestTrackingRepositoryCoverageFix:
    """Tests específicos para cubrir líneas faltantes en TrackingRepository."""

    @pytest.fixture(autouse=True)
    def prevent_session_close(self, session):
        """Evita que el repositorio cierre la sesión de test."""
        # No "mock_session": mantener sesión real de fixture; solo evitar cierre.
        session.close = lambda: None




    def test_completar_trabajo_naive_datetime(self, repos, session):
        """
        Cubre líneas 309-312: Manejo de datetime naive en completar_trabajo.
        """
        repo = repos["tracking"]
        
        # Setup dependencias
        worker = Trabajador(nombre_completo="Worker Naive", activo=True)
        prod = Producto(codigo="PROD-NAIVE", descripcion="P", departamento="D", tipo_trabajador=1, tiene_subfabricaciones=False)
        fab = Fabricacion(codigo="FAB-NAIVE", descripcion="F")
        session.add_all([worker, prod, fab])
        session.commit()

        # Crear trabajo con fecha naive
        trabajo = TrabajoLog(
            trabajador_id=worker.id,
            qr_code="TEST-NAIVE",
            tiempo_inicio=datetime(2025, 1, 1, 10, 0, 0), # Naive
            estado="en_proceso",
            fabricacion_id=fab.id,       # FK Required
            producto_codigo=prod.codigo  # FK Required
        )
        session.add(trabajo)
        session.commit()
        
        # Ejecutar
        result = repo.finalizar_trabajo_log(trabajo.id)
        
        assert result is not None
        assert result.estado == "completado"
        assert result.tiempo_fin is not None
        
    def test_completar_paso_naive_datetime(self, repos, session):
        """
        Cubre líneas 630-633: Manejo de datetime naive en completar_paso_trazabilidad.
        """
        repo = repos["tracking"]
        
        # Setup dependencias
        worker = Trabajador(nombre_completo="Worker Paso Naive", activo=True)
        prod = Producto(codigo="PROD-PASO-NAIVE", descripcion="P", departamento="D", tipo_trabajador=1, tiene_subfabricaciones=False)
        fab = Fabricacion(codigo="FAB-PASO-NAIVE", descripcion="F")
        session.add_all([worker, prod, fab])
        session.commit()

        trabajo = TrabajoLog(
            trabajador_id=worker.id,
            qr_code="TEST-PASO-NAIVE",
            tiempo_inicio=datetime.now(timezone.utc),
            estado="en_proceso",
            fabricacion_id=fab.id,
            producto_codigo=prod.codigo
        )
        session.add(trabajo)
        session.commit()

        paso = PasoTrazabilidad(
            trabajo_log_id=trabajo.id,
            paso_nombre="Test Paso",
            tipo_paso="test",
            estado_paso="en_proceso",
            tiempo_inicio_paso=datetime(2025, 1, 1, 10, 0, 0) # Naive
        )
        session.add(paso)
        session.commit()
        
        result = repo.finalizar_paso(paso.id)
        
        assert result is not None
        session.refresh(paso)
        assert paso.estado_paso == "completado"

    def test_export_completed_step(self, repos, session):
        """
        Cubre líneas 1403-1405: Exportación de paso completado con tiempo_fin.
        """
        repo = repos["tracking"]
        
        # Setup
        trabajador = Trabajador(nombre_completo="Export Tester", activo=True)
        prod = Producto(codigo="PROD-EXPORT", descripcion="P", departamento="D", tipo_trabajador=1, tiene_subfabricaciones=False)
        fab = Fabricacion(codigo="FAB-EXPORT", descripcion="F")
        session.add_all([trabajador, prod, fab])
        session.flush()
        
        trabajo = TrabajoLog(
            trabajador_id=trabajador.id,
            qr_code="EXPORT-TEST",
            tiempo_inicio=datetime.now(timezone.utc),
            estado="en_proceso",
            created_at=datetime.now(timezone.utc),
            fabricacion_id=fab.id,
            producto_codigo=prod.codigo
        )
        session.add(trabajo)
        session.flush()
        
        paso = PasoTrazabilidad(
            trabajo_log_id=trabajo.id,
            paso_nombre="Paso Completed",
            tipo_paso="test",
            estado_paso="completado",
            tiempo_inicio_paso=datetime.now(timezone.utc),
            tiempo_fin_paso=datetime.now(timezone.utc),
            duracion_paso_segundos=10
        )
        session.add(paso)
        session.commit()
        
        # Execute
        data = repo.get_data_for_export(trabajador.id, datetime(2000, 1, 1))
        
        # Assert
        assert len(data) == 1
        pasos = data[0]['pasos_trazabilidad']
        assert len(pasos) == 1
        assert pasos[0]['tiempo_fin_paso'] is not None
