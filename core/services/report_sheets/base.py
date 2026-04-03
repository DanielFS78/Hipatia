# core/services/report_sheets/base.py

"""
Lógica o utilidades del núcleo (`base`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

import logging
from abc import ABC, abstractmethod
from openpyxl import Workbook

class ExcelSheetStrategy(ABC):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def create_sheet(self, wb: Workbook, **kwargs) -> None:
        """
        Creates a sheet in the workbook with specific logic.
        """
        pass
