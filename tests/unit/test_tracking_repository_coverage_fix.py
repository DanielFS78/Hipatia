
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
        session.close = MagicMock()

    def test_get_fabricaciones_asignadas_duplicates(self, repos, session):
        """
        Cubre líneas 111-122: Lógica de agrupación de fabricaciones asignadas.
        """
        repo = repos["tracking"]
        
        # 1. Crear datos de prueba complejos
        worker = Trabajador(nombre_completo="Worker Duplicates", activo=True)
        session.add(worker)
        session.commit()
        
        fab = Fabricacion(codigo="FAB-DUP", descripcion="Duplicate Test")
        session.add(fab)
        session.commit()
        
        # Asignar trabajador a fabricación
        worker.fabricaciones_asignadas.append(fab)
        session.commit()
        
        # Crear Productos
        p1 = Producto(codigo="PROD-1", descripcion="P1", departamento="D", tipo_trabajador=1, tiene_subfabricaciones=False)
        p2 = Producto(codigo="PROD-2", descripcion="P2", departamento="D", tipo_trabajador=1, tiene_subfabricaciones=False)
        session.add_all([p1, p2])
        session.commit()
        
        # Añadir productos a la fabricación
        preproceso_repo = repos["preproceso"]
        preproceso_repo.add_product_to_fabricacion(fab.id, "PROD-1", 10)
        preproceso_repo.add_product_to_fabricacion(fab.id, "PROD-2", 5)
        
        # 2. Ejecutar método bajo prueba con el nombre correcto
        results = repo.get_fabricaciones_por_trabajador(worker.id)
        
        # 3. Assertions
        assert len(results) == 1
        dto = results[0]
        assert isinstance(dto, FabricacionAsignadaDTO)
        assert dto.codigo == "FAB-DUP"
        assert len(dto.productos) == 2
        
        prod_codes = {p['codigo'] for p in dto.productos}
        assert "PROD-1" in prod_codes
        assert "PROD-2" in prod_codes


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
