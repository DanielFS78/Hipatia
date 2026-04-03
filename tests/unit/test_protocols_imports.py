"""Tests de import y existencia para Protocols de interoperabilidad.

Estos módulos no tienen lógica ejecutable (son contratos de tipado), pero al
estar en `coverage.json` con `0%` significa que no se importan en la suite.
Este test fuerza su carga para que la cobertura sea alcanzable.
"""

from __future__ import annotations

import pytest

from controllers.historial.protocols import HistorialControllerProtocol
from controllers.simulation.protocols import SimulationControllerProtocol
from database.repositories.protocols import (
    PilaRepositoryProtocol,
    RepositoryProtocol,
    TrackingRepositoryProtocol,
)

pytestmark = pytest.mark.unit


def test_protocol_classes_exist() -> None:
    assert RepositoryProtocol is not None
    assert SimulationControllerProtocol is not None
    assert HistorialControllerProtocol is not None
    assert PilaRepositoryProtocol is not None
    assert TrackingRepositoryProtocol is not None

