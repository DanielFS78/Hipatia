import pytest
from datetime import datetime, timedelta
from database.models import Fabricacion, TrabajoLog, Producto, Trabajador
from core.reports_dtos import ResultadoBusquedaDTO

class TestReportsIntegration:
    
    @pytest.fixture
    def setup_integration_data(self, session, worker_controller):
        """Crea datos reales en la DB para el test de integración."""
        # Usuario/Trabajador
        worker = Trabajador(nombre_completo="Admin User", role="Admin", tipo_trabajador=1)
        session.add(worker)
        session.commit()
        
        # Producto
        prod = Producto(
            codigo="INT-001", 
            descripcion="Integration Product", 
            tiempo_optimo=30.0,
            departamento="Test",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        )
        session.add(prod)
        
        # Orden link
        fab = Fabricacion(codigo="OF-INT-1", descripcion="Integration Order")
        session.add(fab)
        session.commit()
        
        # Log
        log = TrabajoLog(
            fabricacion_id=fab.id,
            orden_fabricacion="OF-INT-1",
            producto_codigo="INT-001",
            qr_code="QR-INT-1",
            trabajador_id=worker.id,
            tiempo_inicio=datetime.now() - timedelta(hours=2),
            duracion_segundos=3600,
            estado="completado"
        )
        session.add(log)
        session.commit()
        
        return {"worker": worker, "prod": prod, "fab": fab}

    def test_full_search_flow(self, app_model, setup_integration_data):
        """
        Prueba el flujo completo desde AppModel -> Repository -> DB
        Verifica que buscar devuelve resultados reales.
        """
        # La búsqueda debe encontrar el producto INT-001
        results = app_model.reports_buscar_por_codigo("INT-001")
        
        assert len(results) > 0
        assert any(r.codigo == "INT-001" for r in results)
        assert isinstance(results[0], ResultadoBusquedaDTO)

    def test_charts_data_flow(self, app_model, setup_integration_data):
        """
        Prueba el flujo de datos para gráficas.
        """
        # Calcular promedio
        avg_dto = app_model.reports_calcular_promedio_tiempo("INT-001")
        assert avg_dto is not None
        assert avg_dto.producto_codigo == "INT-001"
        assert avg_dto.total_unidades >= 1
        
        # Evolución
        evol = app_model.reports_obtener_evolucion_temporal("INT-001")
        assert len(evol) > 0
