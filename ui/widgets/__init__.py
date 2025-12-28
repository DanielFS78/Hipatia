# -*- coding: utf-8 -*-
from .home_widget import HomeWidget
from .timeline_widget import TimelineVisualizationWidget, TaskAnalysisPanel
from .historial_widget import HistorialWidget
from .settings_widget import SettingsWidget
from .dashboard_widget import DashboardWidget
from .workers_widget import WorkersWidget
from .machines_widget import MachinesWidget
from .prep_steps_widget import PrepStepsWidget
from .products_widget import ProductsWidget, AddProductWidget
from .fabrications_widget import FabricationsWidget
from .calculate_times_widget import CalculateTimesWidget
from .preprocesos_widget import PreprocesosWidget
from .lotes_widget import LotesWidget, DefinirLoteWidget
from .reportes_widget import ReportesWidget
from .gestion_datos_widget import GestionDatosWidget
from .help_widget import HelpWidget

__all__ = [
    'HomeWidget',
    'TimelineVisualizationWidget',
    'TaskAnalysisPanel',
    'HistorialWidget',
    'SettingsWidget',
    'DashboardWidget',
    'WorkersWidget',
    'MachinesWidget',
    'PrepStepsWidget',
    'ProductsWidget',
    'AddProductWidget',
    'FabricationsWidget',
    'CalculateTimesWidget',
    'PreprocesosWidget',
    'LotesWidget',
    'DefinirLoteWidget',
    'ReportesWidget',
    'GestionDatosWidget',
    'HelpWidget'
]
