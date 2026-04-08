"""Tests unitarios para `core.health.health_checker`.

Objetivo:
- Cubrir todas las ramas del cálculo de estado (`_compute_status`).
- Cubrir la lectura de sistema (`_check_system`) con backups/logs/migraciones en filesystem real.
- Cubrir el chequeo de tablas (`_check_tables`) y el flujo principal (`check`) con mocks estrictos.
"""

from __future__ import annotations

import os
import time
from typing import Any
from unittest.mock import MagicMock

import pytest

import core.health.health_checker as health_checker_module

from core.health.health_checker import (
    DatabaseHealthChecker,
    HealthReport,
    SystemHealth,
    TableHealth,
    TestResults as HealthTestResults,
)


def _sync_fs_root(monkeypatch: Any, tmp_path: Any) -> None:
    """Alinea cwd (resource_path) y get_writable_app_root con tmp_path en tests de _check_system."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(health_checker_module, "get_writable_app_root", lambda: tmp_path)

pytestmark = pytest.mark.unit


def _mk_system() -> SystemHealth:
    return SystemHealth(
        disk_free_gb=1.0,
        last_backup_date="Nunca",
        last_session_errors=0,
        db_schema_version="desconocida",
    )


def _mk_report(*, db_reachable: bool, db_integrity_ok: bool, tables: list[TableHealth], test_results: HealthTestResults | None) -> HealthReport:
    return HealthReport(
        db_reachable=db_reachable,
        db_integrity_ok=db_integrity_ok,
        tables=tables,
        system=_mk_system(),
        test_results=test_results,
        overall_status="CRITICAL",
    )


def test_compute_status_db_unreachable_returns_critical() -> None:
    checker = DatabaseHealthChecker()
    report = _mk_report(db_reachable=False, db_integrity_ok=False, tables=[], test_results=None)
    assert checker._compute_status(report) == "CRITICAL"


def test_compute_status_integrity_not_ok_returns_warning() -> None:
    checker = DatabaseHealthChecker()
    tables = [TableHealth(table_name="trabajadores", friendly_name="x", description="d", status="OK", record_count=1)]
    report = _mk_report(db_reachable=True, db_integrity_ok=False, tables=tables, test_results=None)
    assert checker._compute_status(report) == "WARNING"


def test_compute_status_error_table_returns_critical() -> None:
    checker = DatabaseHealthChecker()
    tables = [
        TableHealth(table_name="productos", friendly_name="x", description="d", status="ERROR", record_count=0, error_message="boom"),
    ]
    report = _mk_report(db_reachable=True, db_integrity_ok=True, tables=tables, test_results=None)
    assert checker._compute_status(report) == "CRITICAL"


def test_compute_status_low_pass_rate_returns_critical() -> None:
    checker = DatabaseHealthChecker()
    tr = HealthTestResults(
        total=10,
        passed=5,
        failed=3,
        errors=2,
        pass_rate=0.5,
        coverage_pct=0.0,
        duration_seconds=0.1,
    )
    report = _mk_report(db_reachable=True, db_integrity_ok=True, tables=[], test_results=tr)
    assert checker._compute_status(report) == "CRITICAL"


def test_compute_status_mid_pass_rate_returns_warning() -> None:
    checker = DatabaseHealthChecker()
    tr = HealthTestResults(
        total=10,
        passed=9,
        failed=0,
        errors=1,
        pass_rate=0.9,
        coverage_pct=0.0,
        duration_seconds=0.1,
    )
    report = _mk_report(db_reachable=True, db_integrity_ok=True, tables=[], test_results=tr)
    assert checker._compute_status(report) == "WARNING"


def test_compute_status_critical_empty_tables_returns_warning() -> None:
    checker = DatabaseHealthChecker()
    tables = [
        TableHealth(table_name="trabajadores", friendly_name="x", description="d", status="EMPTY", record_count=0),
        TableHealth(table_name="productos", friendly_name="x", description="d", status="OK", record_count=10),
        TableHealth(table_name="maquinas", friendly_name="x", description="d", status="EMPTY", record_count=0),
    ]
    report = _mk_report(db_reachable=True, db_integrity_ok=True, tables=tables, test_results=None)
    assert checker._compute_status(report) == "WARNING"


def test_compute_status_stable_returns_stable() -> None:
    checker = DatabaseHealthChecker()
    tables = [
        TableHealth(table_name="trabajadores", friendly_name="x", description="d", status="OK", record_count=1),
        TableHealth(table_name="productos", friendly_name="x", description="d", status="OK", record_count=1),
        TableHealth(table_name="maquinas", friendly_name="x", description="d", status="OK", record_count=1),
    ]
    tr = HealthTestResults(
        total=5,
        passed=5,
        failed=0,
        errors=0,
        pass_rate=1.0,
        coverage_pct=100.0,
        duration_seconds=0.1,
    )
    report = _mk_report(db_reachable=True, db_integrity_ok=True, tables=tables, test_results=tr)
    assert checker._compute_status(report) == "STABLE"


def test_check_system_no_backups_no_logs_no_migrations(tmp_path: Any, monkeypatch: Any) -> None:
    checker = DatabaseHealthChecker()
    _sync_fs_root(monkeypatch, tmp_path)
    system = checker._check_system()
    assert system.last_backup_date == "Nunca"
    assert system.last_session_errors == 0
    assert system.db_schema_version == "desconocida"


def _setup_health_fs(tmp_path: Any, *, backup_mtime_seconds_ago: float | None, log_errors: int, schema_version_prefix: str | None) -> None:
    backup_dir_1 = tmp_path / "database_backups"
    backup_dir_2 = tmp_path / "data" / "backups"
    logs_dir = tmp_path / "logs"
    migrations_dir = tmp_path / "migrations" / "versions"

    if backup_mtime_seconds_ago is not None:
        backup_dir_1.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir_1 / "backup_test.zip"
        backup_file.write_bytes(b"data")
        mtime = time.time() - backup_mtime_seconds_ago
        os.utime(str(backup_file), (mtime, mtime))

        # Segundo directorio vacío para cubrir que existe la lista de backup_dirs pero sin añadir extra.
        backup_dir_2.mkdir(parents=True, exist_ok=True)

    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "EvolucionTiempos.log"
    if log_errors > 0:
        lines = []
        for i in range(log_errors):
            lines.append(f"2026-01-01 00:00:0{i} [CRITICAL] error line {i}\n")
        lines.append("2026-01-01 00:00:99 [INFO] ok\n")
        log_path.write_text("".join(lines), encoding="utf-8")
    else:
        # Asegurar que el fichero no exista
        if log_path.exists():
            log_path.unlink()

    if schema_version_prefix is not None:
        migrations_dir.mkdir(parents=True, exist_ok=True)
        # Solo necesitamos que exista al menos un fichero .py para cubrir la selección
        (migrations_dir / f"{schema_version_prefix}_upgrade.py").write_text("# x", encoding="utf-8")


def test_check_system_backup_date_less_than_1_hour(tmp_path: Any, monkeypatch: Any) -> None:
    checker = DatabaseHealthChecker()
    _sync_fs_root(monkeypatch, tmp_path)
    _setup_health_fs(tmp_path, backup_mtime_seconds_ago=1800, log_errors=2, schema_version_prefix="123456789012")
    system = checker._check_system()
    assert system.last_backup_date == "Hace menos de 1 hora"
    assert system.last_session_errors == 2
    assert system.db_schema_version == "123456789012"


def test_check_system_backup_date_hours(tmp_path: Any, monkeypatch: Any) -> None:
    checker = DatabaseHealthChecker()
    _sync_fs_root(monkeypatch, tmp_path)
    _setup_health_fs(tmp_path, backup_mtime_seconds_ago=3 * 3600, log_errors=1, schema_version_prefix="123456789012")
    system = checker._check_system()
    assert system.last_backup_date == "Hace 3 horas"
    assert system.last_session_errors == 1


def test_check_system_backup_date_yesterday(tmp_path: Any, monkeypatch: Any) -> None:
    checker = DatabaseHealthChecker()
    _sync_fs_root(monkeypatch, tmp_path)
    _setup_health_fs(tmp_path, backup_mtime_seconds_ago=25 * 3600, log_errors=0, schema_version_prefix="123456789012")
    system = checker._check_system()
    assert system.last_backup_date == "Ayer"
    assert system.last_session_errors == 0


def test_check_system_backup_date_days(tmp_path: Any, monkeypatch: Any) -> None:
    checker = DatabaseHealthChecker()
    _sync_fs_root(monkeypatch, tmp_path)
    _setup_health_fs(tmp_path, backup_mtime_seconds_ago=3 * 24 * 3600, log_errors=0, schema_version_prefix="123456789012")
    system = checker._check_system()
    assert system.last_backup_date == "Hace 3 días"
    assert system.db_schema_version == "123456789012"


def test_check_system_disk_usage_exception(tmp_path: Any, monkeypatch: Any) -> None:
    import core.health.health_checker as hc

    checker = DatabaseHealthChecker()
    _sync_fs_root(monkeypatch, tmp_path)
    monkeypatch.setattr(hc.shutil, "disk_usage", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("disk fail")))
    system = checker._check_system()
    assert system.disk_free_gb == 0.0


def test_check_system_backup_dir_listdir_exception(tmp_path: Any, monkeypatch: Any) -> None:
    """Cubre el `except` del listado de backups por directorio."""
    import core.health.health_checker as hc

    checker = DatabaseHealthChecker()
    _sync_fs_root(monkeypatch, tmp_path)

    # Aseguramos que `os.path.isdir(database_backups)` sea True
    (tmp_path / "database_backups").mkdir(parents=True, exist_ok=True)

    def _listdir(_path: str) -> list[str]:
        raise RuntimeError("listdir fail")

    monkeypatch.setattr(hc.os, "listdir", _listdir)

    system = checker._check_system()
    assert system.last_backup_date == "Nunca"


def test_check_system_backup_date_exception(tmp_path: Any, monkeypatch: Any) -> None:
    """Cubre el `except` de cálculo de `last_backup` (fromtimestamp/getmtime)."""
    import core.health.health_checker as hc

    checker = DatabaseHealthChecker()
    _sync_fs_root(monkeypatch, tmp_path)

    # Crear backup para que se ejecute el bloque `if all_backup_files: ...`
    _setup_health_fs(tmp_path, backup_mtime_seconds_ago=1800, log_errors=0, schema_version_prefix=None)

    def _getmtime(_path: str) -> float:
        raise RuntimeError("getmtime fail")

    monkeypatch.setattr(hc.os.path, "getmtime", _getmtime)

    system = checker._check_system()
    assert system.last_backup_date == "Nunca"


def test_check_system_log_read_exception(tmp_path: Any, monkeypatch: Any) -> None:
    """Cubre el `except` al leer el fichero de log."""
    import builtins
    import core.health.health_checker as hc

    checker = DatabaseHealthChecker()
    _sync_fs_root(monkeypatch, tmp_path)

    _setup_health_fs(tmp_path, backup_mtime_seconds_ago=None, log_errors=0, schema_version_prefix=None)
    # Forzar que el fichero exista para entrar en el try del log
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "EvolucionTiempos.log").write_text("x", encoding="utf-8")

    def _open_fail(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("open fail")

    monkeypatch.setattr(builtins, "open", _open_fail)

    system = checker._check_system()
    assert system.last_session_errors == 0


def test_check_system_schema_version_list_exception(tmp_path: Any, monkeypatch: Any) -> None:
    """Cubre el `except` al listar versiones Alembic."""
    import core.health.health_checker as hc

    checker = DatabaseHealthChecker()
    _sync_fs_root(monkeypatch, tmp_path)

    _setup_health_fs(tmp_path, backup_mtime_seconds_ago=None, log_errors=0, schema_version_prefix="123456789012")

    versions_dir = tmp_path / "migrations" / "versions"

    orig_listdir = hc.os.listdir

    def _listdir(path: str) -> list[str]:
        if path == str(versions_dir):
            raise RuntimeError("versions list fail")
        return orig_listdir(path)

    monkeypatch.setattr(hc.os, "listdir", _listdir)

    system = checker._check_system()
    assert system.db_schema_version == "desconocida"


def test_check_full_flow_tables_and_overall_status_critical(tmp_path: Any, monkeypatch: Any) -> None:
    checker = DatabaseHealthChecker()
    _sync_fs_root(monkeypatch, tmp_path)

    # Cobertura de sistema minimal
    _setup_health_fs(tmp_path, backup_mtime_seconds_ago=None, log_errors=0, schema_version_prefix=None)

    db_manager = MagicMock(spec=["get_session"])
    session = MagicMock(spec=["execute", "close"])

    def _execute_side_effect(query: Any, *args: Any, **kwargs: Any) -> Any:
        q = str(query)
        integrity_clause = "PRAGMA integrity_check" in q
        if integrity_clause:
            r = MagicMock(spec=["fetchone"])
            r.fetchone.return_value = ("ok",)
            return r

        # SELECT COUNT(*) FROM <table>
        # La cadena SQL contiene `FROM <table_name>`.

        if "FROM trabajadores" in q:
            r = MagicMock(spec=["fetchone"])
            r.fetchone.return_value = (1,)
            return r
        if "FROM productos" in q:
            r = MagicMock(spec=["fetchone"])
            r.fetchone.return_value = (0,)
            return r
        if "FROM maquinas" in q:
            r = MagicMock(spec=["fetchone"])
            r.fetchone.return_value = (1,)
            return r

        # Coger una tabla opcional con `no such table` para cubrir el continue
        if "FROM tracking_logs" in q:
            raise Exception("no such table tracking_logs")

        # Otra tabla con excepción genérica para cubrir status ERROR
        if "FROM audit_logs" in q:
            raise Exception("boom")

        r = MagicMock(spec=["fetchone"])
        r.fetchone.return_value = (1,)
        return r

    session.execute.side_effect = _execute_side_effect
    db_manager.get_session.return_value = session

    report = checker.check(db_manager)

    # `session.close()` se llama tras `_check_tables`
    assert session.close.call_count == 1
    assert report.db_reachable is True
    assert report.db_integrity_ok is True
    # audit_logs => ERROR => error_tables => CRITICAL
    assert report.overall_status == "CRITICAL"


def test_check_db_manager_get_session_raises_sets_error_message(tmp_path: Any, monkeypatch: Any) -> None:
    checker = DatabaseHealthChecker()
    _sync_fs_root(monkeypatch, tmp_path)
    _setup_health_fs(tmp_path, backup_mtime_seconds_ago=None, log_errors=0, schema_version_prefix=None)

    db_manager = MagicMock(spec=["get_session"])
    db_manager.get_session.side_effect = RuntimeError("db down")

    report = checker.check(db_manager)
    assert report.db_reachable is False
    assert report.error_message == "db down"
    assert report.overall_status == "CRITICAL"


def test_check_integrity_check_exception_sets_db_integrity_false_warning(tmp_path: Any, monkeypatch: Any) -> None:
    checker = DatabaseHealthChecker()
    _sync_fs_root(monkeypatch, tmp_path)
    _setup_health_fs(tmp_path, backup_mtime_seconds_ago=None, log_errors=0, schema_version_prefix=None)

    db_manager = MagicMock(spec=["get_session"])
    session = MagicMock(spec=["execute", "close"])

    def _execute_side_effect(query: Any, *_args: Any, **_kwargs: Any) -> Any:
        q = str(query)
        if "PRAGMA integrity_check" in q:
            raise RuntimeError("integrity fail")
        # Para el resto, devolvemos OK
        r = MagicMock(spec=["fetchone"])
        r.fetchone.return_value = (1,)
        return r

    session.execute.side_effect = _execute_side_effect
    db_manager.get_session.return_value = session

    report = checker.check(db_manager)
    assert report.db_reachable is True
    assert report.db_integrity_ok is False
    assert report.overall_status == "WARNING"

