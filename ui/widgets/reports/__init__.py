# -*- coding: utf-8 -*-
"""
Módulo de widgets para el sistema de Reportes de Producción (Fase 5).
"""

from .smart_search import SmartSearchWidget
from .order_list import OrderListWidget
from .charts_container import ReportsChartsWidget

__all__ = [
    'SmartSearchWidget',
    'OrderListWidget',
    'ReportsChartsWidget'
]
