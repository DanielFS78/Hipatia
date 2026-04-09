# -*- coding: utf-8 -*-
"""Tests de infraestructura de reportes: ReportService frente a ReportsRepository."""
import pytest
from unittest.mock import MagicMock, PropertyMock
from datetime import datetime
from typing import Any

from core.app_model import AppModel

pytestmark = pytest.mark.unit
from database.database_manager import DatabaseManager
from core.reports_dtos import (
    ResultadoBusquedaDTO, OrdenFabricacionResumenDTO, PromedioTiempoDTO
)

class TestReportsInfrastructure:
    """
    Tests para verificar la infraestructura de datos del modulo de reportes.
    Verifica que ReportService delega correctamente en ReportsRepository.
    """

    @pytest.fixture
    def mock_db_manager(self):
        """Mock del DatabaseManager con todos los repositorios."""
        db = MagicMock(spec=DatabaseManager)
        
        # Mockear repositorios
        db.product_repo = MagicMock(spec=[])
        db.worker_repo = MagicMock(spec=[])
        db.machine_repo = MagicMock(spec=[])
        db.pila_repo = MagicMock(spec=[])
        db.preproceso_repo = MagicMock(spec=[])
        db.lote_repo = MagicMock(spec=[])
        db.iteration_repo = MagicMock(spec=[])
        db.tracking_repo = MagicMock(spec=[])
        db.reports_repo = MagicMock(
            spec=[
                "buscar_por_codigo",
                "obtener_ordenes_por_producto",
                "calcular_promedio_tiempo_unidad",
                "obtener_evolucion_temporal",
                "obtener_incidencias_por_producto",
                "obtener_tiempos_por_trabajador",
                "obtener_detalle_orden",
                "obtener_resumen_producto",
                "obtener_dashboard_producto",
            ]
        )
        db.material_repo = MagicMock(spec=[])
        
        return db

    @pytest.fixture
    def app_model(self, mock_db_manager):
        """Instancia de AppModel con mocks."""
        return AppModel(mock_db_manager)

    def test_search_reports_data_delegation(self, app_model, mock_db_manager):
        """Verifica que search_reports_data llama a reports_repo.buscar_por_codigo."""
        # Arrange
        query = "test"
        expected_result = [
            ResultadoBusquedaDTO("producto", "TEST-01", "Im?n Test", datetime.now(), 10)
        ]
        mock_db_manager.reports_repo.buscar_por_codigo.return_value = expected_result
        
        # Act
        result = app_model.report_service.search_reports_data(query)
        
        # Assert
        mock_db_manager.reports_repo.buscar_por_codigo.assert_called_once_with(query)
        assert result == expected_result
        assert result[0].codigo == "TEST-01"

    def test_get_orders_for_product_delegation(self, app_model, mock_db_manager):
        """Verifica delegaci?n de obtener_ordenes_por_producto."""
        # Arrange
        code = "PROD-123"
        expected = [
            OrdenFabricacionResumenDTO("OF-1", "PROD-123", "Desc", datetime.now())
        ]
        mock_db_manager.reports_repo.obtener_ordenes_por_producto.return_value = expected
        
        # Act
        result = app_model.report_service.get_orders_for_product(code)
        
        # Assert
        mock_db_manager.reports_repo.obtener_ordenes_por_producto.assert_called_once_with(code)
        assert result == expected

    def test_get_product_time_stats_delegation(self, app_model, mock_db_manager):
        """Verifica delegaci?n de calcular_promedio_tiempo_unidad."""
        # Arrange
        code = "PROD-ABC"
        expected = PromedioTiempoDTO(code, "Desc", 120.5, 5.0, 100, 140, 50)
        mock_db_manager.reports_repo.calcular_promedio_tiempo_unidad.return_value = expected
        
        # Act
        result = app_model.report_service.get_product_time_stats(code)
        
        # Assert
        mock_db_manager.reports_repo.calcular_promedio_tiempo_unidad.assert_called_once_with(code)
        assert result == expected
        assert result.promedio_segundos == 120.5

    def test_get_evolution_stats_delegation_defaults(self, app_model, mock_db_manager):
        """Verifica delegaci?n de obtener_evolucion_temporal con valor por defecto."""
        # Arrange
        code = "PROD-EVO"
        # Act
        app_model.report_service.get_evolution_stats(code)
        
        # Assert
        # Verificar que se llama con el valor por defecto (30) si no se especifica
        mock_db_manager.reports_repo.obtener_evolucion_temporal.assert_called_once_with(code, 30)

    def test_get_incidents_stats_delegation(self, app_model, mock_db_manager):
        """Verifica delegaci?n de obtener_incidencias_por_producto."""
        app_model.report_service.get_incidents_stats("P1")
        mock_db_manager.reports_repo.obtener_incidencias_por_producto.assert_called_once_with("P1")

    def test_get_worker_time_stats_delegation(self, app_model, mock_db_manager):
        """Verifica delegaci?n de obtener_tiempos_por_trabajador."""
        app_model.report_service.get_worker_time_stats("P1")
        mock_db_manager.reports_repo.obtener_tiempos_por_trabajador.assert_called_once_with("P1")

    def test_get_order_details_delegation(self, app_model, mock_db_manager):
        """Verifica delegaci?n de obtener_detalle_orden."""
        app_model.report_service.get_order_details("OF-999")
        mock_db_manager.reports_repo.obtener_detalle_orden.assert_called_once_with("OF-999")

    def test_get_product_summary_delegation(self, app_model, mock_db_manager):
        """Verifica delegaci?n de obtener_resumen_producto."""
        app_model.report_service.get_product_summary("P-SUM")
        mock_db_manager.reports_repo.obtener_resumen_producto.assert_called_once_with("P-SUM")

    def test_get_product_reports_dashboard_delegation(self, app_model, mock_db_manager):
        """Verifica delegaci?n del bundle agregado de dashboard de reportes."""
        expected: dict[str, Any] = {
            "summary": None,
            "orders": [],
            "time_stats": None,
            "worker_stats": [],
            "incidents": [],
            "evolution": [],
        }
        mock_db_manager.reports_repo.obtener_dashboard_producto.return_value = expected

        result = app_model.report_service.get_product_dashboard("PROD-DASH", evolution_days=15)

        mock_db_manager.reports_repo.obtener_dashboard_producto.assert_called_once_with("PROD-DASH", 15)
        assert result == expected
