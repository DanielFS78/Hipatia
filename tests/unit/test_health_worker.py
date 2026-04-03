"""Tests unitarios para `core.health.health_worker.HealthCheckWorker`.

Se cubren:
- Rama `run_tests=False` (solo `db_checked` + `all_done`).
- Rama `run_tests=True` (progreso + `test_finished` + `all_done`).
- Rama de excepción (emite `error_occurred`).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from core.health.health_checker import HealthReport, SystemHealth, TableHealth
from core.health.health_checker import TestResults as HealthTestResults
from core.health.health_worker import HealthCheckWorker

pytestmark = pytest.mark.unit


def _mk_report_for_worker() -> HealthReport:
    system = SystemHealth(disk_free_gb=1.0, last_backup_date="Nunca", last_session_errors=0, db_schema_version="x")
    tables = [
        TableHealth(table_name="trabajadores", friendly_name="T", description="d", status="OK", record_count=1),
        TableHealth(table_name="productos", friendly_name="P", description="d", status="OK", record_count=1),
        TableHealth(table_name="maquinas", friendly_name="M", description="d", status="OK", record_count=1),
    ]
    return HealthReport(
        db_reachable=True,
        db_integrity_ok=True,
        tables=tables,
        system=system,
        test_results=None,
        overall_status="STABLE",
    )


def test_health_worker_run_without_tests_emits_db_checked_and_all_done(qapp: Any, monkeypatch: Any) -> None:
    import core.health.health_worker as hw_mod

    def _fake_check(self: Any, _db_manager: Any) -> HealthReport:
        return _mk_report_for_worker()

    monkeypatch.setattr(hw_mod.DatabaseHealthChecker, "check", _fake_check)

    db_manager = MagicMock(spec_set=[])
    worker = HealthCheckWorker(db_manager=db_manager, run_tests=False)

    db_checked: list[HealthReport] = []
    all_done: list[HealthReport] = []

    worker.db_checked.connect(lambda report: db_checked.append(report))
    worker.all_done.connect(lambda report: all_done.append(report))

    worker.run()

    assert len(db_checked) == 1
    assert len(all_done) == 1
    assert all_done[0].overall_status == "STABLE"


def test_health_worker_run_with_tests_emits_progress_and_finishes(qapp: Any, monkeypatch: Any) -> None:
    import core.health.health_worker as hw_mod
    import core.health.test_runner as tr_mod

    def _fake_check(self: Any, _db_manager: Any) -> HealthReport:
        return _mk_report_for_worker()

    monkeypatch.setattr(hw_mod.DatabaseHealthChecker, "check", _fake_check)

    class _DummyRunner:
        def run(self: Any, *, progress_callback: Any, finished_callback: Any) -> None:
            progress_callback("t1", 1, 1)
            tr = HealthTestResults(
                total=1,
                passed=1,
                failed=0,
                errors=0,
                pass_rate=1.0,
                coverage_pct=10.0,
                duration_seconds=0.1,
            )
            finished_callback(tr)

    monkeypatch.setattr(tr_mod, "TestRunner", _DummyRunner)

    db_manager = MagicMock(spec_set=[])
    worker = HealthCheckWorker(db_manager=db_manager, run_tests=True)

    progress: list[tuple[str, int, int]] = []
    test_finished: list[HealthTestResults] = []
    all_done: list[HealthReport] = []

    worker.test_progress.connect(lambda name, cur, tot: progress.append((name, cur, tot)))
    worker.test_finished.connect(lambda res: test_finished.append(res))
    worker.all_done.connect(lambda report: all_done.append(report))

    worker.run()

    assert progress != []
    assert len(test_finished) == 1
    assert len(all_done) == 1
    assert all_done[0].test_results is not None
    assert all_done[0].test_results.total == 1


def test_health_worker_run_when_checker_raises_emits_error(qapp: Any, monkeypatch: Any) -> None:
    import core.health.health_worker as hw_mod

    def _fake_check(self: Any, _db_manager: Any) -> HealthReport:
        raise RuntimeError("boom")

    monkeypatch.setattr(hw_mod.DatabaseHealthChecker, "check", _fake_check)

    db_manager = MagicMock(spec_set=[])
    worker = HealthCheckWorker(db_manager=db_manager, run_tests=False)

    errors: list[str] = []
    worker.error_occurred.connect(lambda msg: errors.append(msg))

    worker.run()

    assert errors == ["boom"]

