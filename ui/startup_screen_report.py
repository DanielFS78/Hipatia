# -*- coding: utf-8 -*-
"""
Generación de texto del informe de verificación del sistema (StartupScreen).
Lógica pura sin Qt; testeable con HealthReport mock o real.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.health.health_checker import HealthReport


def generate_startup_report_text(
    report: Optional[HealthReport],
    log_path: Optional[str] = None,
) -> str:
    """
    Genera el texto completo del informe para exportación.

    Args:
        report: Informe de salud. Si es None, devuelve "Sin datos disponibles".
        log_path: Ruta al archivo de log. Si None, usa os.path.join(os.getcwd(), "logs", "EvolucionTiempos.log").

    Returns:
        Texto formateado del informe.
    """
    if not report:
        return "Sin datos disponibles"

    lines = []
    lines.append("=" * 80)
    lines.append("INFORME DE VERIFICACIÓN DEL SISTEMA HIPATIA")
    lines.append("=" * 80)
    lines.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    lines.append(f"Estado General: {report.overall_status}")
    lines.append("")

    if report.test_results:
        tr = report.test_results
        lines.append("-" * 80)
        lines.append("VERIFICACIÓN DE ESTRUCTURA INTERNA")
        lines.append("-" * 80)
        lines.append(f"Total de verificaciones: {tr.total}")
        lines.append(f"Exitosas: {tr.passed}")
        lines.append(f"Fallidas: {tr.failed}")
        lines.append(f"Errores: {tr.errors}")
        lines.append(f"Tasa de éxito: {tr.pass_rate * 100:.1f}%")
        lines.append(f"Calidad del código: {tr.coverage_pct:.1f}/100")
        lines.append(f"Duración: {tr.duration_seconds:.1f} segundos")
        if tr.failed_tests:
            lines.append("\nTests fallidos:")
            for test in tr.failed_tests[:10]:
                lines.append(f"  - {test}")
            if len(tr.failed_tests) > 10:
                lines.append(f"  ... y {len(tr.failed_tests) - 10} más")
        lines.append("")

    lines.append("-" * 80)
    lines.append("VERIFICACIÓN DE BASES DE DATOS")
    lines.append("-" * 80)
    lines.append(f"Conexión: {'OK' if report.db_reachable else 'ERROR'}")
    lines.append(f"Integridad: {'OK' if report.db_integrity_ok else 'ERROR'}")
    if report.error_message:
        lines.append(f"Error: {report.error_message}")
    lines.append("\nTablas:")
    for t in report.tables:
        lines.append(f"  {t.friendly_name} ({t.table_name}): {t.status} - {t.record_count} registros")
        if t.error_message:
            lines.append(f"    Error: {t.error_message}")
    lines.append("")

    lines.append("-" * 80)
    lines.append("INFORMACIÓN DEL SISTEMA")
    lines.append("-" * 80)
    lines.append(f"Espacio libre en disco: {report.system.disk_free_gb} GB")
    lines.append(f"Último backup: {report.system.last_backup_date}")
    lines.append(f"Errores en sesión anterior: {report.system.last_session_errors}")
    lines.append(f"Versión del esquema: {report.system.db_schema_version}")
    lines.append("")

    lines.append("-" * 80)
    lines.append("LOGS RECIENTES (ÚLTIMAS 50 LÍNEAS)")
    lines.append("-" * 80)
    path = log_path or os.path.join(os.getcwd(), "logs", "EvolucionTiempos.log")
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                log_lines = f.readlines()[-50:]
            lines.extend(line.rstrip() for line in log_lines)
        except Exception as e:
            lines.append(f"No se pudieron leer los logs: {e}")
    else:
        lines.append("Archivo de log no encontrado")

    lines.append("")
    lines.append("=" * 80)
    lines.append("FIN DEL INFORME")
    lines.append("=" * 80)
    return "\n".join(lines)
