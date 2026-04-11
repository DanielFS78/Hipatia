# -*- coding: utf-8 -*-
"""
Nombre del Módulo: reporting.base
Descripción: Contrato común (``IReporteEstrategia``) y contexto ``GeneradorDeInformes`` para exportar informes.

Desacopla la recogida de datos del formato de salida (Excel, PDF, etc.) para que la UI no
dependa de librerías de ofimática concretas.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class IReporteEstrategia(ABC):
    @abstractmethod
    def generar_reporte(self, datos_informe: Dict[Any, Any], output_path: str) -> bool:
        """Genera el informe y lo deja en ``output_path`` (o delega en submétodos según la estrategia)."""
        ...


class GeneradorDeInformes:
    def __init__(self, estrategia: IReporteEstrategia):
        self._estrategia = estrategia

    def generar_y_guardar(self, datos_informe: Dict[Any, Any], output_path: str) -> bool:
        from .excel_report_strategy import ReportePilaFabricacionExcelMejorado

        if isinstance(self._estrategia, ReportePilaFabricacionExcelMejorado):
            if self._estrategia.generar_reporte(datos_informe):
                return self._estrategia.guardar_reporte(output_path)
            return False
        return self._estrategia.generar_reporte(datos_informe, output_path)
