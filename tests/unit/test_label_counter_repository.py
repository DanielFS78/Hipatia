"""Tests de integración para `LabelCounterRepository` usando SQLite in-memory.

Regla de calidad Hipatia: los repositorios se validan contra una BD real en memoria,
evitando mocks de `Session` (falsos positivos / contratos irreales).
"""

import pytest

from core.dtos import LabelRangeDTO
from database.models import Fabricacion, FabricacionContador
from database.repositories.label_counter_repository import LabelCounterRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(session):
    return LabelCounterRepository(lambda: session)


@pytest.fixture
def fabricacion(session):
    fab = Fabricacion(codigo="FAB-LABEL-001", descripcion="Fabricación para labels")
    session.add(fab)
    session.commit()
    return fab


def test_get_next_unit_range_existing_counter(repo, session, fabricacion):
    session.add(FabricacionContador(fabricacion_id=fabricacion.id, ultimo_numero_unidad=50))
    session.commit()

    result = repo.get_next_unit_range(fabricacion.id, 10)

    assert isinstance(result, LabelRangeDTO)
    assert result.fabricacion_id == fabricacion.id
    assert result.start == 51
    assert result.end == 60
    assert result.count == 10

    contador = session.query(FabricacionContador).filter_by(fabricacion_id=fabricacion.id).first()
    assert contador is not None
    assert contador.ultimo_numero_unidad == 60


def test_get_next_unit_range_new_counter(repo, session, fabricacion):
    result = repo.get_next_unit_range(fabricacion.id, 5)

    assert isinstance(result, LabelRangeDTO)
    assert result.fabricacion_id == fabricacion.id
    assert result.start == 1
    assert result.end == 5
    assert result.count == 5

    contador = session.query(FabricacionContador).filter_by(fabricacion_id=fabricacion.id).first()
    assert contador is not None
    assert contador.ultimo_numero_unidad == 5


def test_get_next_unit_range_invalid_fabricacion_rolls_back_and_returns_none(repo, session):
    assert session.query(FabricacionContador).count() == 0

    result = repo.get_next_unit_range(999999, 10)
    assert result is None

    assert session.query(FabricacionContador).count() == 0


def test_close_does_not_raise(repo):
    repo.close()
    assert repo is not None
