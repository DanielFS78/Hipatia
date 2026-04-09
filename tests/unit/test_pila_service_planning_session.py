# -*- coding: utf-8 -*-
"""Sesión de planificación: PilaService acepta CalculationStepDTO (no solo dict)."""

from __future__ import annotations

from unittest.mock import MagicMock, create_autospec, patch

import pytest

from core.dtos import (
    CalculationProductDTO,
    CalculationStepDTO,
    CalculationSubPartDTO,
    LoteDTO,
    ProductDTO,
)
from core.services.pila_service import PilaService
from database.database_manager import DatabaseManager
from database.repositories.lote_repository import LoteRepository

pytestmark = [pytest.mark.unit]


def _minimal_product_dto() -> CalculationProductDTO:
    return CalculationProductDTO(
        codigo="P1",
        descripcion="Prod",
        departamento="D",
        tipo_trabajador=1,
        donde="",
        tiene_subfabricaciones=False,
        tiempo_optimo=1.0,
        sub_partes=[
            CalculationSubPartDTO(
                descripcion="s",
                tiempo=1.0,
                tipo_trabajador=1,
                requiere_maquina_tipo=None,
            )
        ],
    )


def _db_with_lote(lote: LoteDTO) -> MagicMock:
    """DatabaseManager define ``lote_repo`` en ``__init__``; no aparece en autospec de clase."""
    lote_repo = create_autospec(LoteRepository, instance=True)
    lote_repo.get_lote_details.return_value = lote
    db = MagicMock(spec=DatabaseManager)
    db.lote_repo = lote_repo
    return db


def test_get_data_for_calculation_from_session_accepts_calculation_step_dto() -> None:
    lote_details = LoteDTO(
        id=42,
        codigo="L42",
        descripcion="",
        productos=[ProductDTO(codigo="P1", descripcion="D")],
        fabricaciones=[],
    )
    db = _db_with_lote(lote_details)

    svc = PilaService(db)
    out_dto = _minimal_product_dto()

    step = CalculationStepDTO(
        lote_template_id=42,
        lote_codigo="L-X",
        identificador="L-X",
        unidades=3,
        deadline=None,
    )
    with patch.object(svc, "get_data_for_calculation", return_value=[out_dto]) as mock_calc:
        result = svc.get_data_for_calculation_from_session([step])

    db.lote_repo.get_lote_details.assert_called_once_with(42)
    mock_calc.assert_called_once_with("P1")
    assert len(result) == 1
    assert result[0].units_for_this_instance == 3
    assert result[0].fabricacion_id == "L-X"


def test_get_data_for_calculation_from_session_mixed_product_and_step() -> None:
    lote_details = LoteDTO(
        id=1,
        codigo="L1",
        descripcion="",
        productos=[],
        fabricaciones=[],
    )
    db = _db_with_lote(lote_details)

    svc = PilaService(db)
    direct = _minimal_product_dto()
    step = CalculationStepDTO(
        lote_template_id=1,
        lote_codigo="L",
        identificador="L",
        unidades=1,
        deadline=None,
    )
    result = svc.get_data_for_calculation_from_session([direct, step])
    assert direct in result
    assert len(result) == 1
