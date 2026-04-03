# core/services/report_sheets/__init__.py

"""
Lógica o utilidades del núcleo (`__init__`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

from .base import ExcelSheetStrategy
from .resumen import ResumenEjecutivoSheet
from .trabajadores import AnalisisTrabajadoresSheet
from .cronograma import CronogramaSheet
from .cuellos_botella import CuellosBotollaSheet
from .audit import AuditSheet
from .graficas import GraficasSheet
from .trabajo_paralelo import TrabajoParaleloSheet

__all__ = [
    'ExcelSheetStrategy',
    'ResumenEjecutivoSheet',
    'AnalisisTrabajadoresSheet',
    'CronogramaSheet',
    'CuellosBotellaSheet',
    'AuditSheet',
    'GraficasSheet',
    'TrabajoParaleloSheet'
]
