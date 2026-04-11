"""
Nombre del Módulo: core.facades.reporting_facade

Descripción: Expone ``ReportingFacade`` como API estable de aplicación sobre servicios ya inyectados; no contiene reglas de persistencia directa. Integración típica con: ``__future__``.
"""

from __future__ import annotations

from typing import Any


class ReportingFacade:
    """Agrupa operaciones de ReportService."""

    def __init__(self, report_service: Any) -> None:
        self._report_service = report_service

    def __getattr__(self, name: str) -> Any:
        return getattr(self._report_service, name)
