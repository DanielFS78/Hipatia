# -*- coding: utf-8 -*-
"""Tests para WorkerService."""
import pytest
from unittest.mock import MagicMock, patch, ANY
from core.services.worker_service import WorkerService
from core.dtos import WorkerDTO, ProductDetailsDTO
from database.database_manager import DatabaseManager

@pytest.mark.unit
class TestWorkerService:
    """
    Tests unitarios para WorkerService.
    Sigue el estándar de strict_testing.
    """

    @pytest.fixture
    def mock_db(self):
        db = MagicMock(spec=DatabaseManager)
        db.worker_repo = MagicMock(
            spec=[
                "get_all_workers",
                "add_worker",
                "get_worker_details",
            ]
        )
        db.tracking_repo = MagicMock(spec=[])
        db.preproceso_repo = MagicMock(
            spec=[
                "create_fabricacion_with_preprocesos",
                "search_fabricaciones",
                "add_product_to_fabricacion",
            ]
        )
        db.product_repo = MagicMock(spec=["get_product_details"])
        db.pila_repo = MagicMock(spec=["get_all_pilas_with_dates", "load_pila"])
        return db

    @pytest.fixture
    def service(self, mock_db):
        return WorkerService(mock_db)

    def test_get_all_workers(self, service, mock_db):
        """Prueba que obtiene todos los trabajadores delegando al repo."""
        mock_workers = [WorkerDTO(id=1, nombre_completo="Juan Perez", activo=True, notas="", tipo_trabajador=1)]
        mock_db.worker_repo.get_all_workers.return_value = mock_workers
        
        result = service.get_all_workers(include_inactive=True)
        
        assert result == mock_workers
        mock_db.worker_repo.get_all_workers.assert_called_once_with(True)

    def test_add_worker_success(self, service, mock_db):
        """Prueba la adición exitosa de un trabajador y la emisión de señal."""
        mock_db.worker_repo.add_worker.return_value = True
        
        # Conectar señal a un mock para verificar emisión
        signal_mock = MagicMock(spec=[])
        service.workers_changed_signal.connect(signal_mock)
        
        result = service.add_worker("Test Worker", "Notas")
        
        assert result is True
        assert signal_mock.call_count == 1
        signal_mock.assert_called_once_with()
        assert mock_db.worker_repo.add_worker.call_count == 1
        mock_db.worker_repo.add_worker.assert_called_once_with(
            nombre_completo="Test Worker",
            notas="Notas",
            tipo_trabajador=ANY,
            activo=True,
            username=None,
            password_hash=None,
            role=None,
        )

    def test_assign_task_to_worker_success(self, service, mock_db):
        """Prueba la asignación de tarea (lógica compleja extraída)."""
        # Configurar mocks para los 4 pasos de assign_task_to_worker
        mock_worker = MagicMock(spec=["nombre_completo"])
        mock_worker.nombre_completo = "Juan Perez"
        mock_db.worker_repo.get_worker_details.return_value = mock_worker
        
        mock_prod = MagicMock(spec=["descripcion"])
        mock_prod.descripcion = "Producto Test"
        mock_db.product_repo.get_product_details.return_value = ProductDetailsDTO(producto=mock_prod, subfabricaciones=[], procesos_mecanicos=[])
        
        mock_db.preproceso_repo.create_fabricacion_with_preprocesos.return_value = True
        
        # Mock para recuperar el ID (search_fabricaciones)
        fab_mock = MagicMock(spec=["codigo", "id"])
        fab_mock.codigo = "TASK-JUAN-PROD1-TIMESTAMP" # Simplificado
        fab_mock.id = 100
        mock_db.preproceso_repo.search_fabricaciones.return_value = [fab_mock]
        
        mock_db.preproceso_repo.add_product_to_fabricacion.return_value = True
        mock_tas = MagicMock(spec=["asignar_trabajador_a_fabricacion"])
        mock_tas.asignar_trabajador_a_fabricacion.return_value = True
        service._tracking_assignment_service = mock_tas

        with patch("core.services.worker_service.datetime") as mock_date:
            mock_date.now.return_value.strftime.return_value = "TIMESTAMP"
            success, msg = service.assign_task_to_worker(1, "PROD1", 10)
            
        assert success is True
        assert "asignada a Juan Perez" in msg
        mock_tas.asignar_trabajador_a_fabricacion.assert_called_once_with(1, 100)

    def test_get_worker_load_stats(self, service, mock_db):
        """Prueba el cálculo de estadísticas de carga de trabajo."""
        pila_mock = MagicMock(spec=["id"])
        pila_mock.id = 1
        mock_db.pila_repo.get_all_pilas_with_dates.return_value = [pila_mock]
        
        # Resultados de simulación mockeados
        sim_results = [
            {"Duracion (min)": 60, "Lista Trabajadores": ["Juan"]},
            {"Duracion (min)": 30, "Trabajador Asignado": "Maria"}
        ]
        mock_db.pila_repo.load_pila.return_value = (None, None, None, sim_results)
        
        stats = service.get_worker_load_stats()
        
        assert stats["Juan"] == 60
        assert stats["Maria"] == 30
