# -*- coding: utf-8 -*-
"""Tests unitarios para generación de texto del informe de arranque."""
import os
import tempfile
from dataclasses import dataclass
from typing import Any, Optional, cast
from unittest.mock import patch

import pytest

from ui.startup_screen_report import generate_startup_report_text


pytestmark = pytest.mark.unit


@dataclass(frozen=True)
class _SystemInfo:
    disk_free_gb: float
    last_backup_date: str
    last_session_errors: int
    db_schema_version: str


@dataclass(frozen=True)
class _TestResults:
    total: int
    passed: int
    failed: int
    errors: int
    pass_rate: float
    coverage_pct: float
    duration_seconds: float
    failed_tests: list[str]


@dataclass(frozen=True)
class _TableReport:
    friendly_name: str
    table_name: str
    status: str
    record_count: int
    error_message: str = ""


@dataclass(frozen=True)
class _HealthReportLike:
    overall_status: str
    db_reachable: bool
    db_integrity_ok: bool
    error_message: str
    tables: list[_TableReport]
    system: _SystemInfo
    test_results: Optional[_TestResults] = None


def test_generate_startup_report_text_none():
    """Si report es None retorna mensaje por defecto."""
    assert generate_startup_report_text(None) == "Sin datos disponibles"


def test_generate_startup_report_text_empty_report():
    """Reporte mínimo sin test_results y con tablas vacías."""
    report = _HealthReportLike(
        overall_status="STABLE",
        db_reachable=True,
        db_integrity_ok=True,
        error_message="",
        tables=[],
        system=_SystemInfo(
            disk_free_gb=10.5,
            last_backup_date="Nunca",
            last_session_errors=0,
            db_schema_version="1.0",
        ),
        test_results=None,
    )

    text = generate_startup_report_text(cast(Any, report), log_path="/nonexistent/log.txt")

    assert "INFORME DE VERIFICACIÓN DEL SISTEMA HIPATIA" in text
    assert "Estado General: STABLE" in text
    assert "Conexión: OK" in text
    assert "Integridad: OK" in text
    assert "Espacio libre en disco: 10.5 GB" in text
    assert "Archivo de log no encontrado" in text
    assert "FIN DEL INFORME" in text


def test_generate_startup_report_text_with_test_results():
    """Incluye sección de tests cuando test_results está presente."""
    report = _HealthReportLike(
        overall_status="WARNING",
        db_reachable=True,
        db_integrity_ok=True,
        error_message="",
        tables=[],
        system=_SystemInfo(
            disk_free_gb=0,
            last_backup_date="",
            last_session_errors=0,
            db_schema_version="",
        ),
        test_results=_TestResults(
            total=100,
            passed=95,
            failed=3,
            errors=2,
            pass_rate=0.95,
            coverage_pct=85.0,
            duration_seconds=12.5,
            failed_tests=["test_a", "test_b"],
        ),
    )

    text = generate_startup_report_text(cast(Any, report), log_path="/nonexistent/log.txt")

    assert "VERIFICACIÓN DE ESTRUCTURA INTERNA" in text
    assert "Total de verificaciones: 100" in text
    assert "Exitosas: 95" in text
    assert "Tests fallidos:" in text
    assert "  - test_a" in text
    assert "  - test_b" in text


def test_generate_startup_report_text_with_many_failed_tests():
    """Trunca la lista de tests fallidos a 10 y añade '... y N más'."""
    report = _HealthReportLike(
        overall_status="CRITICAL",
        db_reachable=True,
        db_integrity_ok=True,
        error_message="",
        tables=[],
        system=_SystemInfo(
            disk_free_gb=0,
            last_backup_date="",
            last_session_errors=0,
            db_schema_version="",
        ),
        test_results=_TestResults(
            total=50,
            passed=40,
            failed=10,
            errors=0,
            pass_rate=0.8,
            coverage_pct=70.0,
            duration_seconds=5.0,
            failed_tests=[f"test_{i}" for i in range(15)],
        ),
    )

    text = generate_startup_report_text(cast(Any, report), log_path="/nonexistent/log.txt")

    assert "  ... y 5 más" in text


def test_generate_startup_report_text_with_tables_and_error_message():
    """Incluye tablas y error_message cuando existen."""
    report = _HealthReportLike(
        overall_status="CRITICAL",
        db_reachable=False,
        db_integrity_ok=False,
        error_message="Connection refused",
        tables=[
            _TableReport(
                friendly_name="Productos",
                table_name="productos",
                status="OK",
                record_count=42,
                error_message="",
            ),
            _TableReport(
                friendly_name="Auditoría",
                table_name="audit_logs",
                status="ERROR",
                record_count=0,
                error_message="Timeout al conectar",
            ),
        ],
        system=_SystemInfo(
            disk_free_gb=0,
            last_backup_date="",
            last_session_errors=0,
            db_schema_version="",
        ),
        test_results=None,
    )

    text = generate_startup_report_text(cast(Any, report), log_path="/nonexistent/log.txt")

    assert "Conexión: ERROR" in text
    assert "Error: Connection refused" in text
    assert "Productos (productos): OK - 42 registros" in text
    assert "Auditoría (audit_logs): ERROR - 0 registros" in text
    assert "    Error: Timeout al conectar" in text


def test_generate_startup_report_text_reads_log_file():
    """Si log_path existe, incluye las últimas líneas del archivo."""
    report = _HealthReportLike(
        overall_status="STABLE",
        db_reachable=True,
        db_integrity_ok=True,
        error_message="",
        tables=[],
        system=_SystemInfo(
            disk_free_gb=0,
            last_backup_date="",
            last_session_errors=0,
            db_schema_version="",
        ),
        test_results=None,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8") as f:
        try:
            f.write("line1\nline2\nline3\n")
            f.flush()
            log_path = f.name
            text = generate_startup_report_text(cast(Any, report), log_path=log_path)
            assert "LOGS RECIENTES" in text
            assert "line1" in text
            assert "line2" in text
            assert "line3" in text
        finally:
            os.unlink(log_path)


def test_generate_startup_report_text_log_read_error():
    """Si el archivo de log no puede leerse, se añade mensaje de error."""
    report = _HealthReportLike(
        overall_status="STABLE",
        db_reachable=True,
        db_integrity_ok=True,
        error_message="",
        tables=[],
        system=_SystemInfo(
            disk_free_gb=0,
            last_backup_date="",
            last_session_errors=0,
            db_schema_version="",
        ),
        test_results=None,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8") as f:
        f.write("x")
        f.flush()
        log_path = f.name
    try:
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            text = generate_startup_report_text(cast(Any, report), log_path=log_path)
        assert "LOGS RECIENTES" in text
        assert "No se pudieron leer los logs" in text
    finally:
        os.unlink(log_path)
