# -*- coding: utf-8 -*-
"""Acceso unificado a ítems de planning_session y set_planning_units."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from controllers.simulation.execution_helpers import set_planning_units
from core.dtos import CalculationProductDTO, CalculationStepDTO, CalculationSubPartDTO
from core.planning_session_access import (
    deadline_to_date,
    planning_identificador,
    planning_lote_codigo,
    planning_unidades,
)

pytestmark = [pytest.mark.unit]


def test_planning_unidades_dict_and_dtos() -> None:
    assert planning_unidades({"unidades": 5}) == 5
    assert planning_unidades({}) == 1
    step = CalculationStepDTO(
        lote_template_id=1,
        lote_codigo="L",
        identificador="L",
        unidades=7,
        deadline=None,
    )
    assert planning_unidades(step) == 7
    sub = CalculationSubPartDTO("s", 1.0, 1, None)
    prod = CalculationProductDTO(
        codigo="P",
        descripcion="",
        departamento="D",
        tipo_trabajador=1,
        donde="",
        tiene_subfabricaciones=False,
        tiempo_optimo=1.0,
        sub_partes=[sub],
        units_for_this_instance=4,
    )
    assert planning_unidades(prod) == 4


def test_planning_identificador_and_lote_codigo() -> None:
    step = CalculationStepDTO(
        lote_template_id=1,
        lote_codigo="LC",
        identificador="ID1",
        unidades=1,
        deadline=None,
    )
    assert planning_identificador(step) == "ID1"
    assert planning_lote_codigo(step) == "LC"


def test_deadline_to_date() -> None:
    d = datetime(2025, 6, 15, 12, 0, 0)
    assert deadline_to_date(d) == date(2025, 6, 15)
    assert deadline_to_date(date(2025, 1, 2)) == date(2025, 1, 2)
    assert deadline_to_date(None) is None


def test_set_planning_units_step_dto_replaces_in_list() -> None:
    step = CalculationStepDTO(
        lote_template_id=1,
        lote_codigo="L",
        identificador="L",
        unidades=1,
        deadline=None,
    )
    session: list = [step]
    set_planning_units(session, 9)
    assert len(session) == 1
    assert isinstance(session[0], CalculationStepDTO)
    assert session[0].unidades == 9
