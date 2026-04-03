# -*- coding: utf-8 -*-
"""Tests unitarios para WorkerValidationService.

Cubre validate_qr_data (válido/inválido), validate_product_match, is_step_duplicated.
Decisión de mocking: QR scanner con spec parse_qr_data; objetos trabajo/paso con spec.
"""
import pytest
from unittest.mock import MagicMock
from features.worker_validation_service import WorkerValidationService

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_qr_scanner():
    return MagicMock(spec=['parse_qr_data'])

@pytest.fixture
def validation_service(mock_qr_scanner):
    return WorkerValidationService(mock_qr_scanner)

def test_validate_qr_data_valid(validation_service, mock_qr_scanner):
    mock_qr_scanner.parse_qr_data.return_value = {"producto_codigo": "PROD1"}
    is_valid, data, error = validation_service.validate_qr_data("VALID_QR")
    assert mock_qr_scanner.parse_qr_data.call_count == 1
    assert is_valid is True
    assert data == {"producto_codigo": "PROD1"}
    assert error == ""

def test_validate_qr_data_invalid(validation_service, mock_qr_scanner):
    mock_qr_scanner.parse_qr_data.return_value = None
    is_valid, data, error = validation_service.validate_qr_data("INVALID_QR")
    assert is_valid is False
    assert data is None
    assert "formato" in error.lower()

def test_validate_product_match_success(validation_service):
    is_match, error = validation_service.validate_product_match("PROD1", "PROD1")
    assert is_match is True
    assert error == ""

def test_validate_product_match_fail(validation_service):
    is_match, error = validation_service.validate_product_match("PROD1", "PROD2")
    assert is_match is False
    assert "no coincide" in error.lower()

def test_is_step_duplicated_true(validation_service):
    mock_trabajo = MagicMock(spec=['pasos_trazabilidad'])
    mock_paso = MagicMock(spec=['paso_nombre', 'estado_paso'])
    mock_paso.paso_nombre = "Operario"
    mock_paso.estado_paso = "completado"
    mock_trabajo.pasos_trazabilidad = [mock_paso]
    assert validation_service.is_step_duplicated(mock_trabajo, "Operario") is True

def test_is_step_duplicated_false(validation_service):
    mock_trabajo = MagicMock(spec=['pasos_trazabilidad'])
    mock_paso = MagicMock(spec=['paso_nombre'])
    mock_paso.paso_nombre = "Operario"
    mock_trabajo.pasos_trazabilidad = [mock_paso]
    assert validation_service.is_step_duplicated(mock_trabajo, "Control de Calidad") is False
