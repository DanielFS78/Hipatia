# -*- coding: utf-8 -*-
"""
Nombre del Módulo: report_strategy
Descripción: Punto de entrada estable para estrategias de informe (Excel y PDF).

Reexporta ``IReporteEstrategia``, ``GeneradorDeInformes`` y las clases concretas del
subpaquete ``core.services.reporting`` para imports simples desde controladores.
"""

from core.services.reporting.base import IReporteEstrategia, GeneradorDeInformes
from core.services.reporting.excel_report_strategy import ReportePilaFabricacionExcelMejorado
from core.services.reporting.pdf_report_strategy import ReporteHistorialFabricacion, ReporteHistorialIteracion

__all__ = [
    "IReporteEstrategia",
    "GeneradorDeInformes",
    "ReportePilaFabricacionExcelMejorado",
    "ReporteHistorialFabricacion",
    "ReporteHistorialIteracion"
]