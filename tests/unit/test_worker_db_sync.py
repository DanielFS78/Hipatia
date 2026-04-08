# -*- coding: utf-8 -*-
"""Tests unitarios para WorkerDbSync: fabricaciones asignadas, trabajos activos, pasos, incidencias."""
import pytest
from unittest.mock import MagicMock
from features.worker_db_sync import WorkerDbSync

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_repo():
    return MagicMock(spec=['get_fabricaciones_por_trabajador', 'obtener_trabajos_activos', 'get_paso_activo_por_trabajador', 'obtener_o_crear_trabajo_log_por_qr', 'finalizar_paso', 'registrar_incidencia'])

@pytest.fixture
def db_sync(mock_repo):
    return WorkerDbSync(mock_repo)

def test_get_assigned_fabricaciones(db_sync, mock_repo):
    mock_fab = MagicMock(spec=['id', 'codigo', 'descripcion', 'productos', 'fecha_asignacion', 'estado'])
    mock_fab.id = 1
    mock_fab.codigo = "FAB1"
    mock_fab.descripcion = "Desc"
    mock_fab.productos = [{"codigo": "P1", "descripcion": "Pd", "cantidad": 10}]
    mock_fab.fecha_asignacion = "2023-01-01"
    mock_fab.estado = "pendiente"

    mock_repo.get_fabricaciones_por_trabajador.return_value = [mock_fab]
    result = db_sync.get_assigned_fabricaciones(123)

    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].producto_codigo == "P1"
    assert mock_repo.get_fabricaciones_por_trabajador.call_count == 1
    mock_repo.get_fabricaciones_por_trabajador.assert_called_once_with(123)

def test_get_active_trabajos(db_sync, mock_repo):
    mock_repo.obtener_trabajos_activos.return_value = ["job1"]
    result = db_sync.get_active_trabajos(123)
    assert result == ["job1"]
    assert mock_repo.obtener_trabajos_activos.call_count == 1
    mock_repo.obtener_trabajos_activos.assert_called_once_with(123)

def test_get_paso_activo(db_sync, mock_repo):
    mock_repo.get_paso_activo_por_trabajador.return_value = "step1"
    result = db_sync.get_paso_activo(123)
    assert result == "step1"
    assert mock_repo.get_paso_activo_por_trabajador.call_count == 1
    mock_repo.get_paso_activo_por_trabajador.assert_called_once_with(123)

def test_iniciar_o_recuperar_trabajo(db_sync, mock_repo):
    mock_repo.obtener_o_crear_trabajo_log_por_qr.return_value = "job"
    result = db_sync.iniciar_o_recuperar_trabajo("QR", 123, 1, "PROD")
    assert result == "job"
    assert mock_repo.obtener_o_crear_trabajo_log_por_qr.call_count == 1
    mock_repo.obtener_o_crear_trabajo_log_por_qr.assert_called_once_with(
        qr_code="QR",
        trabajador_id=123,
        fabricacion_id=1,
        producto_codigo="PROD",
        orden_fabricacion=None,
    )

def test_finalizar_paso(db_sync, mock_repo):
    mock_repo.finalizar_paso.return_value = True
    assert db_sync.finalizar_paso(1) is True
    assert mock_repo.finalizar_paso.call_count == 1
    mock_repo.finalizar_paso.assert_called_once_with(1)

def test_registrar_incidencia(db_sync, mock_repo):
    mock_repo.registrar_incidencia.return_value = "inc1"
    result = db_sync.registrar_incidencia(1, 123, "Type", "Desc", [])
    assert result == "inc1"
    assert mock_repo.registrar_incidencia.call_count == 1
    mock_repo.registrar_incidencia.assert_called_once_with(
        trabajo_log_id=1, trabajador_id=123, tipo_incidencia="Type", descripcion="Desc", rutas_fotos=[]
    )
