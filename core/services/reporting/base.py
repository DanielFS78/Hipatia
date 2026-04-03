"""
========================================================================
BASE DE REPORTING — ESTRATEGIAS DE GENERACIÓN DE INFORMES
========================================================================
Define las interfaces base (IReporteEstrategia) y el contexto
(GeneradorDeInformes) para el patrón Strategy en la exportación de
reportes.

Desacopla la recolección de datos del formato de salida (Excel, PDF,
etc.) para que la UI no dependa de los detalles de las librerías de
ofimática.
========================================================================
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class IReporteEstrategia(ABC):
    @abstractmethod
    def generar_reporte(self, datos_informe: Dict[Any, Any], output_path: str) -> bool:
        pass

class GeneradorDeInformes:
    def __init__(self, estrategia: IReporteEstrategia):
        self._estrategia = estrategia

    def generar_y_guardar(self, datos_informe: Dict[Any, Any], output_path: str) -> bool:
        # Note: We'll keep the specialized logic for Excel if needed, 
        # but better to normalize the interface in the strategies themselves.
        # However, to maintain current behavior:
        from .excel_report_strategy import ReportePilaFabricacionExcelMejorado
        
        if isinstance(self._estrategia, ReportePilaFabricacionExcelMejorado):
            if self._estrategia.generar_reporte(datos_informe):
                return self._estrategia.guardar_reporte(output_path)
            return False
        else:
            return self._estrategia.generar_reporte(datos_informe, output_path)
