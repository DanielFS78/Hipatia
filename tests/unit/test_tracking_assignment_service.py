# -*- coding: utf-8 -*-
"""
Tests unitarios para TrackingAssignmentService.
Verifica la delegación correcta al repositorio de tracking.
"""
import pytest
from unittest.mock import ANY, create_autospec
from core.services.tracking_assignment_service import TrackingAssignmentService
from database.database_manager import DatabaseManager
from database.repositories.tracking_repository import TrackingRepository

@pytest.fixture
def mock_db_manager():
    """Mock estricto del DatabaseManager usando create_autospec."""
    manager = create_autospec(DatabaseManager, instance=True)
    manager.tracking_repo = create_autospec(TrackingRepository, instance=True)
    return manager

@pytest.fixture
def tracking_assignment_service(mock_db_manager):
    return TrackingAssignmentService(mock_db_manager)

@pytest.mark.unit
def test_init(tracking_assignment_service, mock_db_manager):
    """Verifica que el servicio se inicializa y guarda su db_manager."""
    assert tracking_assignment_service._db is mock_db_manager

@pytest.mark.unit
def test_get_fabricaciones_por_trabajador(tracking_assignment_service, mock_db_manager):
    """Prueba que el método delega en tracking_repo.get_fabricaciones_por_trabajador."""
    mock_db_manager.tracking_repo.get_fabricaciones_por_trabajador.return_value = ["FAB-1"]
    result = tracking_assignment_service.get_fabricaciones_por_trabajador(1)
    
    assert result == ["FAB-1"]
    mock_db_manager.tracking_repo.get_fabricaciones_por_trabajador.assert_called_once_with(1)
    
@pytest.mark.unit
def test_get_fabricaciones_por_trabajador_empty(tracking_assignment_service, mock_db_manager):
    """Prueba comportamiento cuando el repositorio devuelve lista vacía."""
    mock_db_manager.tracking_repo.get_fabricaciones_por_trabajador.return_value = []
    result = tracking_assignment_service.get_fabricaciones_por_trabajador(99)
    assert result == []

@pytest.mark.unit
def test_actualizar_estado_asignacion_true(tracking_assignment_service, mock_db_manager):
    """Test actualizando estado con exito."""
    mock_db_manager.tracking_repo.safe_execute.return_value = True
    assert tracking_assignment_service.actualizar_estado_asignacion(1, 1, "completado") is True

@pytest.mark.unit
def test_actualizar_estado_asignacion_false(tracking_assignment_service, mock_db_manager):
    """Test actualizando estado sin exito."""
    mock_db_manager.tracking_repo.safe_execute.return_value = None
    assert tracking_assignment_service.actualizar_estado_asignacion(1, 1, "nada") is False

@pytest.mark.unit
def test_asignar_trabajador_a_fabricacion(tracking_assignment_service, mock_db_manager):
    """Verifica asignación exitosa de trabajador a fabricación."""
    mock_db_manager.tracking_repo.safe_execute.return_value = True
    assert tracking_assignment_service.asignar_trabajador_a_fabricacion(1, 1) is True

@pytest.mark.unit
def test_desasignar_trabajador_de_fabricacion(tracking_assignment_service, mock_db_manager):
    """Verifica desasignación exitosa de trabajador de fabricación."""
    mock_db_manager.tracking_repo.safe_execute.return_value = True
    assert tracking_assignment_service.desasignar_trabajador_de_fabricacion(1, 1) is True
