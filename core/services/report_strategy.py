"""
Fachada de compatibilidad para estrategias de informes: reexporta interfaces y
implementaciones desde core.services.reporting (Excel/PDF) sin acoplar
importadores al subpaquete interno.
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