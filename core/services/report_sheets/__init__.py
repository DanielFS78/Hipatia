# -*- coding: utf-8 -*-
"""
Nombre del Módulo: report_sheets
Descripción: Hojas Excel reutilizables del informe de pila (resumen, cronograma, gráficas, etc.).

Cada módulo define una subclase de ``ExcelSheetStrategy`` que añade una pestaña al libro.
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
    "ExcelSheetStrategy",
    "ResumenEjecutivoSheet",
    "AnalisisTrabajadoresSheet",
    "CronogramaSheet",
    "CuellosBotollaSheet",
    "AuditSheet",
    "GraficasSheet",
    "TrabajoParaleloSheet",
]
