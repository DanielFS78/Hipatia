# -*- coding: utf-8 -*-
"""
Nombre del Paquete: controllers
Descripción: Centraliza y exporta todos los controladores del sistema Hipatia.
             Sigue el patrón MVC, donde los controladores actúan como mediadores entre 
             los modelos de datos y las vistas de la interfaz de usuario.
"""

from controllers.app_controller import AppController
from controllers.backup_controller import BackupController
from controllers.calculation_controller import CalculationController
from controllers.hardware_controller import HardwareController
from controllers.historial.controller import HistorialController
from controllers.machine_controller import MachineController
from controllers.pila.controller import PilaController
from controllers.product_controller_v2 import ProductController as ProductControllerV2
from controllers.report_controller import ReportController
from controllers.schedule_controller import ScheduleController
from controllers.session_controller import SessionController
from controllers.simulation.controller import SimulationController
from controllers.startup_controller import StartupController
from controllers.worker.controller import WorkerController

# Nuevos controllers (Refactorización Fase 1)
from controllers.lote_controller import LoteController
from controllers.file_controller import FileController
from controllers.preproceso_controller import PreprocesoController
from controllers.fabricacion_controller import FabricacionController
from controllers.ui_controller import UIController
from controllers.navigation_controller import NavigationController

__all__ = [
    'AppController',
    'BackupController',
    'CalculationController',
    'HardwareController',
    'HistorialController',
    'MachineController',
    'PilaController',
    'ProductControllerV2',
    'ReportController',
    'ScheduleController',
    'SessionController',
    'SimulationController',
    'StartupController',
    'WorkerController',
    # Nuevos controllers
    'LoteController',
    'FileController',
    'PreprocesoController',
    'FabricacionController',
    'UIController',
    'NavigationController',
]
