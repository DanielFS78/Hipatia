"""Tests unitarios para `core.health.test_runner.TestRunner`.

Se cubren:
- Parseo de líneas individuales (PASSED/FAILED/ERROR).
- Parseo de resumen cuando no hay líneas de tests.
- Ruta cuando no se encuentra resumen (total queda en 0).
- Manejo de excepciones de subprocess.
- Manejo de excepciones en `_read_coverage`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator
from unittest.mock import MagicMock, create_autospec

import pytest

from core.health.health_checker import TestResults as HealthTestResults
from core.health.test_runner import TestRunner

pytestmark = pytest.mark.unit


class _DummyStdout:
    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    def __iter__(self) -> Iterator[str]:
        return iter(self._lines)


class _DummyProc:
    def __init__(self, lines: list[str], *, returncode: int = 0) -> None:
        self.stdout = _DummyStdout(lines)
        self.returncode = returncode
        self._wait_called = False

    def wait(self) -> None:
        self._wait_called = True


def test_run_parses_individual_test_lines_and_emits_progress(tmp_path: Path, monkeypatch: Any) -> None:
    # Entrar en el parser de PASSED/FAILED/ERROR y en el parseo de `name` con/ sin `::`.
    import core.health.test_runner as tr_mod

    lines = [
        "tests/unit/test_a.py::TestX::test_1 PASSED\n",
        "tests/unit/test_b.py PASSED\n",
        "tests/unit/test_a.py::TestX::test_2 FAILED\n",
        "tests/unit/test_a.py::TestX::test_3 ERROR\n",
    ]

    def _dummy_popen(*_args: Any, **_kwargs: Any) -> _DummyProc:
        return _DummyProc(lines, returncode=0)

    monkeypatch.setattr(tr_mod.subprocess, "Popen", _dummy_popen)

    progress_callback = create_autospec(lambda _name, _cur, _tot: None)
    finished_callback = create_autospec(lambda _results: None)

    runner = TestRunner()
    runner.run(progress_callback=progress_callback, finished_callback=finished_callback)

    assert progress_callback.call_count == 4
    assert finished_callback.call_count == 1

    (results,) = finished_callback.call_args.args
    assert isinstance(results, HealthTestResults)
    assert results.total == 4
    assert results.passed == 2
    assert results.failed == 1
    assert results.errors == 1
    assert results.failed_tests != []


def test_run_parses_summary_when_no_individual_lines(tmp_path: Path, monkeypatch: Any) -> None:
    import core.health.test_runner as tr_mod

    lines = [
        "some log line\n",
        "5 passed, 1 failed in 0.3s\n",
    ]

    def _dummy_popen(*_args: Any, **_kwargs: Any) -> _DummyProc:
        return _DummyProc(lines, returncode=0)

    monkeypatch.setattr(tr_mod.subprocess, "Popen", _dummy_popen)

    progress_callback = create_autospec(lambda _name, _cur, _tot: None)
    finished_callback = create_autospec(lambda _results: None)

    runner = TestRunner()
    runner.run(progress_callback=progress_callback, finished_callback=finished_callback)

    # No hubo líneas PASSED/FAILED/ERROR individuales
    assert progress_callback.call_count == 0
    assert finished_callback.call_count == 1

    (results,) = finished_callback.call_args.args
    assert results.total == 6
    assert results.passed == 5
    assert results.failed == 1
    assert results.errors == 0


def test_run_when_total_stays_zero_without_summary(tmp_path: Path, monkeypatch: Any) -> None:
    import core.health.test_runner as tr_mod

    lines = [
        "some log line 1\n",
        "some log line 2\n",
    ]

    def _dummy_popen(*_args: Any, **_kwargs: Any) -> _DummyProc:
        return _DummyProc(lines, returncode=0)

    monkeypatch.setattr(tr_mod.subprocess, "Popen", _dummy_popen)

    progress_callback = create_autospec(lambda _name, _cur, _tot: None)
    finished_callback = create_autospec(lambda _results: None)

    runner = TestRunner()
    runner.run(progress_callback=progress_callback, finished_callback=finished_callback)

    assert progress_callback.call_count == 0
    assert finished_callback.call_count == 1

    (results,) = finished_callback.call_args.args
    assert results.total == 0
    assert results.pass_rate == 0.0


def test_run_handles_subprocess_exception(tmp_path: Path, monkeypatch: Any) -> None:
    import core.health.test_runner as tr_mod

    def _dummy_popen(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("popen fail")

    monkeypatch.setattr(tr_mod.subprocess, "Popen", _dummy_popen)

    progress_callback = create_autospec(lambda _name, _cur, _tot: None)
    finished_callback = create_autospec(lambda _results: None)

    runner = TestRunner()
    runner.run(progress_callback=progress_callback, finished_callback=finished_callback)

    assert progress_callback.call_count == 0
    assert finished_callback.call_count == 1

    (results,) = finished_callback.call_args.args
    assert results.total == results.passed + results.failed + results.errors
    assert results.errors >= 1


def test_read_coverage_exception_returns_zero(monkeypatch: Any) -> None:
    runner = TestRunner()

    # Forzar que el fichero exista, pero que `read_text` falle para ejecutar el except.
    orig_exists = Path.exists
    orig_read_text = Path.read_text

    def _exists(self: Path) -> bool:
        if str(self).endswith("test_reports/compliance_data.json"):
            return True
        return orig_exists(self)

    def _read_text(self: Path, *args: Any, **kwargs: Any) -> str:
        if str(self).endswith("test_reports/compliance_data.json"):
            raise RuntimeError("read fail")
        return orig_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "exists", _exists)
    monkeypatch.setattr(Path, "read_text", _read_text)

    root = Path(__file__).resolve().parent.parent.parent
    cov = runner._read_coverage(root)
    assert cov == 0.0

