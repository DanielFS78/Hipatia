# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`__init__`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from .home_widget import HomeWidget
from .log_terminal_widget import LogTerminalWidget
from .timeline_widget import TimelineVisualizationWidget, TaskAnalysisPanel
from .historial_widget import HistorialWidget
from .settings_widget import SettingsWidget
from .dashboard_widget import DashboardWidget
from .workers_widget import WorkersWidget
from .machines_widget import MachinesWidget
from .prep_steps_widget import PrepStepsWidget
from .products_widget import ProductsWidget
from .fabrications_widget import FabricationsWidget
from .calculate_times_widget import CalculateTimesWidget
from .preprocesos_widget import PreprocesosWidget
from .lotes_widget import LotesWidget, DefinirLoteWidget
from .reportes_widget import ReportesWidget
from .gestion_datos_widget import GestionDatosWidget
from .help_widget import HelpWidget
from . import product
from . import production_flow
from . import reports

__all__: list[str] = [
    'HomeWidget',
    'LogTerminalWidget',
    'TimelineVisualizationWidget',
    'TaskAnalysisPanel',
    'HistorialWidget',
    'SettingsWidget',
    'DashboardWidget',
    'WorkersWidget',
    'MachinesWidget',
    'PrepStepsWidget',
    'ProductsWidget',
    'ProductsWidget',
    'FabricationsWidget',
    'CalculateTimesWidget',
    'PreprocesosWidget',
    'LotesWidget',
    'DefinirLoteWidget',
    'ReportesWidget',
    'GestionDatosWidget',
    'HelpWidget',
    'product',
    'production_flow',
    'reports'
]
