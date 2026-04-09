# -*- coding: utf-8 -*-
"""
Regresión de la política cohorte dominio vs UI en scripts/test_quality_analyzer.py.

Cubre classify_test_tier (rutas y nombres) y resolve_analyzer_status (strict_domain exige 100).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / "scripts" / "test_quality_analyzer.py"

_spec = importlib.util.spec_from_file_location("test_quality_analyzer_script", _SCRIPT)
assert _spec and _spec.loader
_tqa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tqa)

classify_test_tier = _tqa.classify_test_tier
resolve_analyzer_status = _tqa.resolve_analyzer_status


@pytest.mark.unit
class TestClassifyTestTier:
    def test_infra_returns_infra(self) -> None:
        p = _ROOT / "tests" / "conftest.py"
        assert classify_test_tier(p, True) == "infra"

    def test_tests_db_is_strict_domain(self) -> None:
        p = _ROOT / "tests" / "db" / "test_product_repository_db.py"
        assert classify_test_tier(p, False) == "strict_domain"

    def test_service_filename_strict_domain(self) -> None:
        p = _ROOT / "tests" / "unit" / "test_machine_service.py"
        assert classify_test_tier(p, False) == "strict_domain"

    def test_repository_filename_strict_domain(self) -> None:
        p = _ROOT / "tests" / "unit" / "test_tracking_repository_full.py"
        assert classify_test_tier(p, False) == "strict_domain"

    def test_widget_file_is_ui_qt(self) -> None:
        p = _ROOT / "tests" / "unit" / "test_home_widget.py"
        assert classify_test_tier(p, False) == "ui_qt"


@pytest.mark.unit
class TestResolveAnalyzerStatus:
    def test_strict_domain_score_100_actualizado(self) -> None:
        ceiling = {"ceiling_score": 100, "at_ceiling": True, "actionable_penalties": {}}
        st, detail, dom = resolve_analyzer_status(
            test_tier="strict_domain", score=100, ceiling_data=ceiling
        )
        assert st == "Actualizado"
        assert "100/100" in detail
        assert dom == "Listo dominio"

    def test_strict_domain_at_ceiling_but_score_70_en_progreso(self) -> None:
        ceiling = {"ceiling_score": 100, "at_ceiling": True, "actionable_penalties": {}}
        st, detail, dom = resolve_analyzer_status(
            test_tier="strict_domain", score=70, ceiling_data=ceiling
        )
        assert st == "En Progreso"
        assert "100" in detail
        assert dom == "Pendiente dominio"

    def test_ui_at_ceiling_low_ceiling_actualizado(self) -> None:
        ceiling = {"ceiling_score": 70, "at_ceiling": True, "actionable_penalties": {}}
        st, detail, dom = resolve_analyzer_status(
            test_tier="ui_qt", score=70, ceiling_data=ceiling
        )
        assert st == "Actualizado"
        assert dom is None

    def test_ui_effective_85_actualizado(self) -> None:
        ceiling = {"ceiling_score": 85, "at_ceiling": False, "actionable_penalties": {"x": -1}}
        st, _, dom = resolve_analyzer_status(
            test_tier="ui_qt", score=70, ceiling_data=ceiling
        )
        assert st == "Actualizado"
        assert dom is None

    def test_strict_domain_score_40_legacy(self) -> None:
        ceiling = {"ceiling_score": 45, "at_ceiling": True, "actionable_penalties": {}}
        st, _, dom = resolve_analyzer_status(
            test_tier="strict_domain", score=40, ceiling_data=ceiling
        )
        assert st == "Legacy / Pendiente"
        assert dom == "Pendiente dominio"
