# -*- coding: utf-8 -*-
"""
Nombre del Módulo: health_checker
Descripción: Verifica el estado de la base de datos y del sistema al arranque.
             Sin dependencia de UI — solo lógica pura.
"""
from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.paths import get_writable_app_root
from core.utils.helpers import resource_path

from .constants import CRITICAL_TABLES, TABLE_FRIENDLY, THRESHOLDS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses de resultado
# ---------------------------------------------------------------------------

@dataclass
class TableHealth:
    """Estado de una tabla de la base de datos."""
    table_name: str
    friendly_name: str
    description: str
    status: str          # "OK" | "EMPTY" | "ERROR"
    record_count: int
    error_message: str = ""


@dataclass
class SystemHealth:
    """Información de salud general del sistema."""
    disk_free_gb: float
    last_backup_date: str   # "Nunca" si no hay backups
    last_session_errors: int
    db_schema_version: str


@dataclass
class TestResults:
    """Resultados de la ejecución de tests unitarios."""
    total: int
    passed: int
    failed: int
    errors: int
    pass_rate: float
    coverage_pct: float
    duration_seconds: float
    failed_tests: list[str] = field(default_factory=list)


@dataclass
class HealthReport:
    """Informe completo de salud del sistema."""
    db_reachable: bool
    db_integrity_ok: bool
    tables: list[TableHealth]
    system: SystemHealth
    test_results: Optional[TestResults]
    overall_status: str      # "STABLE" | "WARNING" | "CRITICAL"
    generated_at: datetime = field(default_factory=datetime.now)
    error_message: str = ""


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------

class DatabaseHealthChecker:
    """Verifica el estado de la base de datos y del sistema."""

    def check(self, db_manager: object) -> HealthReport:
        """
        Ejecuta todas las verificaciones y devuelve un HealthReport.

        Args:
            db_manager: Instancia de DatabaseManager.

        Returns:
            HealthReport con el estado completo del sistema.
        """
        db_reachable = False
        db_integrity_ok = False
        tables: list[TableHealth] = []
        error_message = ""

        try:
            session = db_manager.get_session()  # type: ignore[attr-defined]
            db_reachable = True

            # Integridad
            try:
                result = session.execute(
                    __import__("sqlalchemy").text("PRAGMA integrity_check")
                ).fetchone()
                db_integrity_ok = result is not None and result[0] == "ok"
            except Exception as e:
                logger.warning(f"No se pudo verificar integridad: {e}")
                db_integrity_ok = False

            # Estado de cada tabla
            tables = self._check_tables(session)
            session.close()

        except Exception as e:
            error_message = str(e)
            logger.error(f"Error verificando BD: {e}")

        system = self._check_system()

        report = HealthReport(
            db_reachable=db_reachable,
            db_integrity_ok=db_integrity_ok,
            tables=tables,
            system=system,
            test_results=None,
            overall_status="CRITICAL",
            error_message=error_message,
        )
        report.overall_status = self._compute_status(report)
        return report

    def _check_tables(self, session: object) -> list[TableHealth]:
        """Verifica el estado de cada tabla conocida."""
        results = []
        for table_name, (friendly, description) in TABLE_FRIENDLY.items():
            try:
                from sqlalchemy import text
                count_result = session.execute(  # type: ignore[attr-defined]
                    text(f"SELECT COUNT(*) FROM {table_name}")
                ).fetchone()
                count = count_result[0] if count_result else 0
                status = "EMPTY" if count == 0 else "OK"
                results.append(TableHealth(
                    table_name=table_name,
                    friendly_name=friendly,
                    description=description,
                    status=status,
                    record_count=count,
                ))
            except Exception as e:
                # Si la tabla no existe, no es crítico — puede ser opcional
                error_msg = str(e)
                if "no such table" in error_msg.lower():
                    # Tabla opcional que no existe — no mostrar como error
                    continue
                results.append(TableHealth(
                    table_name=table_name,
                    friendly_name=friendly,
                    description=description,
                    status="ERROR",
                    record_count=0,
                    error_message=str(e),
                ))
        return results

    def _check_system(self) -> SystemHealth:
        """Recopila información de salud del sistema."""
        # Espacio en disco
        try:
            disk = shutil.disk_usage(str(get_writable_app_root()))
            disk_free_gb = disk.free / (1024 ** 3)
        except Exception:
            disk_free_gb = 0.0

        # Último backup — buscar en múltiples ubicaciones
        last_backup = "Nunca"
        wr = get_writable_app_root()
        backup_dirs = [
            str(wr / "database_backups"),
            str(wr / "data" / "backups"),
            str(wr / "backups"),
        ]
        
        all_backup_files = []
        for backup_dir in backup_dirs:
            if os.path.isdir(backup_dir):
                try:
                    files = [
                        os.path.join(backup_dir, f)
                        for f in os.listdir(backup_dir)
                        if f.endswith((".zip", ".db", ".tar.gz"))
                    ]
                    all_backup_files.extend(files)
                except Exception:
                    pass

        if all_backup_files:
            try:
                newest = max(all_backup_files, key=os.path.getmtime)
                mtime = datetime.fromtimestamp(os.path.getmtime(newest))
                delta = datetime.now() - mtime
                days = delta.days
                hours = delta.seconds // 3600
                
                if days == 0 and hours < 1:
                    last_backup = "Hace menos de 1 hora"
                elif days == 0:
                    last_backup = f"Hace {hours} horas"
                elif days == 1:
                    last_backup = "Ayer"
                else:
                    last_backup = f"Hace {days} días"
            except Exception:
                pass

        # Errores en el log de la última sesión
        last_errors = 0
        log_path = str(wr / "logs" / "EvolucionTiempos.log")
        if os.path.isfile(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    # Leer las últimas 500 líneas
                    lines = f.readlines()[-500:]
                last_errors = sum(1 for l in lines if " [CRITICAL]" in l or " [   ERROR]" in l)
            except Exception:
                pass

        # Versión del esquema (última migración Alembic)
        schema_version = "desconocida"
        versions_dir = Path(resource_path("migrations/versions"))
        if versions_dir.is_dir():
            try:
                version_files = sorted(
                    [f for f in os.listdir(str(versions_dir)) if f.endswith(".py") and not f.startswith("__")],
                    reverse=True,
                )
                if version_files:
                    schema_version = version_files[0][:12]
            except Exception:
                pass

        return SystemHealth(
            disk_free_gb=round(disk_free_gb, 1),
            last_backup_date=last_backup,
            last_session_errors=last_errors,
            db_schema_version=schema_version,
        )

    def _compute_status(self, report: HealthReport) -> str:
        """Calcula el estado general basado en el informe."""
        if not report.db_reachable:
            return "CRITICAL"
        
        if not report.db_integrity_ok:
            return "WARNING"

        # Verificar si hay tablas con ERROR (no solo vacías)
        error_tables = [t for t in report.tables if t.status == "ERROR"]
        if error_tables:
            return "CRITICAL"

        # Solo evaluar tests si realmente se ejecutaron
        if report.test_results and report.test_results.total > 0:
            tr = report.test_results
            if tr.pass_rate < THRESHOLDS["warning_pass_rate"]:
                return "CRITICAL"
            if tr.pass_rate < THRESHOLDS["stable_pass_rate"]:
                return "WARNING"
            # La cobertura del compliance_data.json no es relevante para el startup
            # Solo importa si los tests que se ejecutaron pasaron

        # Tablas críticas vacías → WARNING
        for t in report.tables:
            if t.table_name in CRITICAL_TABLES and t.status == "EMPTY":
                return "WARNING"

        return "STABLE"
