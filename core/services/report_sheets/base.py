# -*- coding: utf-8 -*-
"""
Nombre del Módulo: report_sheets.base
Descripción: Clase base abstracta para cada hoja Excel del informe de pila de fabricación.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from openpyxl import Workbook

class ExcelSheetStrategy(ABC):
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def create_sheet(self, wb: Workbook, **_kwargs: Any) -> None:
        """Añade una hoja al libro ``wb`` según el análisis recibido en ``kwargs``."""
        ...
