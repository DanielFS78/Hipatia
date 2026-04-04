# -*- coding: utf-8 -*-
"""
Nombre del Módulo: startup_controller.py
Descripción: Orquestador del arranque de la aplicación. Se encarga de instanciar 
             servicios, repositorios y todos los controladores del sistema.
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, Callable, cast
from PyQt6.QtCore import QObject, QThreadPool

if TYPE_CHECKING:
    from controllers.app_controller import AppController
    from core.app_model import AppModel
    from core.schedule_config import ScheduleConfig
    from database.database_manager import DatabaseManager
    from ui.main_view import MainView

from core.di_container import DIContainer, ServiceLifecycle

# Domain services & facades (singletons viven en AppModel; se exponen en DI)
from core.services.product_service import ProductService
from core.services.pila_service import PilaService
from core.services.worker_service import WorkerService
from core.services.machine_service import MachineService
from core.services.preparation_service import PreparationService
from core.services.fabricacion_service import FabricacionService
from core.services.report_service import ReportService
from core.services.tracking_assignment_service import TrackingAssignmentService
from core.facades import ProductFacade, PlanningFacade
from core.services.system_integration_service import SystemIntegrationService
from core.application_state import ApplicationState

# Services
from core.qr_generator import QrGenerator
from core.label_manager import LabelManager
from core.security.security_service import SecurityService
from core.security.access_control import set_security_service
from core.quote_service import QuoteService
from database.repositories import LabelCounterRepository
from core.interfaces.view_interface import IView

# Controllers
from controllers.backup_controller import BackupController
from controllers.report_controller import ReportController
from controllers.hardware_controller import HardwareController
from controllers.machine_controller import MachineController
from controllers.calculation_controller import CalculationController
from controllers.product_controller_v2 import ProductController
from controllers.worker.controller import WorkerController
from controllers.pila.controller import PilaController
from controllers.simulation.controller import SimulationController
from controllers.historial.controller import HistorialController
from controllers.schedule_controller import ScheduleController
from controllers.session_controller import SessionController

# New controllers (Refactor Fase 2)
from controllers.file_controller import FileController
from controllers.preproceso_controller import PreprocesoController
from controllers.fabricacion_controller import FabricacionController
from controllers.lote_controller import LoteController
from controllers.ui_controller import UIController
from controllers.navigation_controller import NavigationController
from controllers.ui_signals_controller import UISignalsController
from controllers.pila.protocols import IPilaView


class StartupController:
    """
    Controlador responsable de la inicialización de la aplicación.
    Maneja la configuración de servicios, repositorios y sub-controladores.
    """

    def __init__(self, app_controller: 'AppController'):
        """
        Inicializa el controlador de arranque.
        
        Args:
            app_controller: Instancia del controlador principal de la aplicación.
        """
        self.app: 'AppController' = app_controller
        self.model: 'AppModel' = app_controller.model
        self.view: IView = app_controller.view
        self.schedule_manager: 'ScheduleConfig' = app_controller.schedule_manager
        self.logger: logging.Logger = logging.getLogger("EvolucionTiemposApp.Startup")
        self.container: DIContainer = DIContainer.get_instance()
        self.scheduler_timer: Optional[Any] = None

    def initialize_app(self) -> None:
        """Orquesta todo el proceso de arranque."""
        self.logger.info("Iniciando secuencia de arranque...")
        
        # 1. Servicios Core (DB, Config, Security)
        self._init_services()
        
        # 2. Estado inicial
        self._init_state()
        
        # 3. Sub-controladores
        self._init_controllers()
        
        # 4. Delegaciones de compatibilidad eliminadas
        
        # 5. Inicializar Scheduler
        self._init_scheduler()
        
        self.logger.info("Secuencia de arranque completada.")

    def _init_services(self) -> None:
        """Inicializa y registra los servicios y repositorios core."""
        self.logger.info("Inicializando servicios...")
        
        # Registrar servicios CORE en el contenedor (Singletons por naturaleza)
        self.container.register('AppModel', self.model, lifecycle=ServiceLifecycle.SINGLETON) 
        self.container.register(type(self.model), self.model, lifecycle=ServiceLifecycle.SINGLETON)
        self.container.register(type(self.model.db), self.model.db, lifecycle=ServiceLifecycle.SINGLETON)
        self.container.register(type(self.schedule_manager), self.schedule_manager, lifecycle=ServiceLifecycle.SINGLETON)

        # Dominio (misma instancia que AppModel; resolución por tipo sin pasar por la fachada)
        m = self.model
        self.container.register(ProductService, m.product_service, lifecycle=ServiceLifecycle.SINGLETON)
        self.container.register(PilaService, m.pila_service, lifecycle=ServiceLifecycle.SINGLETON)
        self.container.register(WorkerService, m.worker_service, lifecycle=ServiceLifecycle.SINGLETON)
        self.container.register(MachineService, m.machine_service, lifecycle=ServiceLifecycle.SINGLETON)
        self.container.register(PreparationService, m.preparation_service, lifecycle=ServiceLifecycle.SINGLETON)
        self.container.register(FabricacionService, m.fabricacion_service, lifecycle=ServiceLifecycle.SINGLETON)
        self.container.register(ReportService, m.report_service, lifecycle=ServiceLifecycle.SINGLETON)
        self.container.register(TrackingAssignmentService, m.tracking_assignment_service, lifecycle=ServiceLifecycle.SINGLETON)
        self.container.register(ProductFacade, m.product_facade, lifecycle=ServiceLifecycle.SINGLETON)
        self.container.register(PlanningFacade, m.planning_facade, lifecycle=ServiceLifecycle.SINGLETON)
        self.container.register(SystemIntegrationService, m.system_integration, lifecycle=ServiceLifecycle.SINGLETON)
        
        # 1. QrGenerator
        self.app.qr_generator = QrGenerator()
        self.container.register(QrGenerator, self.app.qr_generator, lifecycle=ServiceLifecycle.SINGLETON)

        # 2. LabelManager
        self.app.label_manager = LabelManager(
            templates_dir="templates",
            qr_generator=self.app.qr_generator
        )
        self.container.register(LabelManager, self.app.label_manager, lifecycle=ServiceLifecycle.SINGLETON)

        # 3. SecurityService
        self.app.security_service = SecurityService()
        set_security_service(self.app.security_service) 
        self.container.register(SecurityService, self.app.security_service, lifecycle=ServiceLifecycle.SINGLETON)

        self.app.tracking_repo = self.model.db.tracking_repo
        
        if self.model.db.SessionLocal:
             session_factory = cast(Callable[[], Any], self.model.db.SessionLocal)
             self.app.label_counter_repo = LabelCounterRepository(session_factory)
        else:
             self.logger.critical("DB SessionLocal es None durante el arranque")
             raise RuntimeError("Base de datos no inicializada")

        # 5. Servicios adicionales
        self.app.quote_service = QuoteService()
        self.container.register(QuoteService, self.app.quote_service, lifecycle=ServiceLifecycle.SINGLETON)
        
        self.app.thread_pool = QThreadPool()
        
        self.container.register(type(self.app), self.app, lifecycle=ServiceLifecycle.SINGLETON)
        
        # 6. Maintenance & Backup Services
        from core.services.rate_limiter import RateLimiter
        from core.services.audit_logger import AuditLogger
        from core.services.maintenance_service import MaintenanceService
        from core.services.backup_service import BackupService
        
        # Iniciar BackupService
        self.app.backup_service = BackupService(data_dir="data")
        self.container.register(BackupService, self.app.backup_service, lifecycle=ServiceLifecycle.SINGLETON)

        if self.model.db.SessionLocal:
             session_factory = cast(Callable[[], Any], self.model.db.SessionLocal)
             rate_limiter = RateLimiter(session_factory)
             audit_logger = AuditLogger(session_factory)
             self.app.audit_logger = audit_logger  
             
             self.app.maintenance_service = MaintenanceService(rate_limiter, audit_logger, self.app.backup_service)
             self.container.register(MaintenanceService, self.app.maintenance_service, lifecycle=ServiceLifecycle.SINGLETON)
             
             self.app.maintenance_service.run_background_maintenance()
        
        self.logger.info("Servicios inicializados correctamente.")

    def _init_scheduler(self) -> None:
        """Inicializa el planificador de tareas automático."""
        from PyQt6.QtCore import QTimer
        
        self.logger.info("Iniciando planificador de tareas (Scheduler)...")
        self.scheduler_timer = QTimer(self.app)  # Parented to app controller (QObject)
        if self.scheduler_timer:
            self.scheduler_timer.timeout.connect(self._check_scheduled_tasks)
            self.scheduler_timer.start(60000)  # Verificar cada minuto
        self.logger.info("Scheduler iniciado. Verificación cada 60s.")

    def _check_scheduled_tasks(self) -> None:
        """Verifica si hay tareas programadas para ejecutar en este momento."""
        from PyQt6.QtCore import QTime
        
        # Hora programada para el backup (desde configuración en DB; sin pasar por AppModel)
        raw_backup = self.model.db.config_repo.get_setting("backup_time", "02:00")
        backup_time_str = str(raw_backup) if raw_backup is not None else "02:00"
        SCHEDULED_BACKUP_TIME = QTime.fromString(backup_time_str, "HH:mm")
        
        current_time = QTime.currentTime()
        
        # Verificar si es el minuto exacto de la hora programada
        # Margen de 1 minuto para asegurar que se ejecute solo una vez
        if (SCHEDULED_BACKUP_TIME.isValid() and 
            current_time.hour() == SCHEDULED_BACKUP_TIME.hour() and 
            current_time.minute() == SCHEDULED_BACKUP_TIME.minute()):
            
            self.logger.info(f"Hora programada ({SCHEDULED_BACKUP_TIME.toString()}) alcanzada via Scheduler.")
            
            if hasattr(self.app, 'maintenance_service') and self.app.maintenance_service:
                self.logger.info("Disparando mantenimiento programado...")
                self.app.maintenance_service.run_background_maintenance()
            else:
                self.logger.warning("MaintenanceService no disponible para ejecución programada.")

    def _init_state(self) -> None:
        """Inicializa el estado global de la aplicación (ApplicationState)."""
        from core.application_state import ApplicationState
        app_state = ApplicationState()
        self.container.register(ApplicationState, app_state)
        self.app.state = app_state

    def _init_controllers(self) -> None:
        """
        Inicializa todos los controladores de la aplicación usando el contenedor.
        Utiliza fábricas (lambdas) para permitir la instanciación diferida y ciclos de vida.
        """
        self.logger.info("Inicializando controladores...")
        
        # Registro de factorías
        # Por defecto los controladores son SINGLETON para esta sesión de la app
        self.container.register(BackupController, factory=lambda: BackupController(self.model.db, self.view, self.logger, self.app.backup_service, self.app.audit_logger))
        # ReportController with direct services
        self.container.register(ReportController, factory=lambda: ReportController(
            db=self.model.db, view=self.view,
            worker_service=self.container.resolve(WorkerService),
            product_service=self.container.resolve(ProductService),
            pila_service=self.container.resolve(PilaService),
            schedule_manager=self.schedule_manager,
            logger=self.logger
        ))
        self.container.register(HardwareController, factory=lambda: HardwareController(self.model.db, self.view, self.logger))
        self.container.register(MachineController, factory=lambda: MachineController(
            self.container.resolve(MachineService), self.view, self.logger
        ))
        
        # Controllers that depend on AppController
        self.container.register(CalculationController, factory=lambda: CalculationController(
            self.app, self.container.resolve(PilaService)
        ))
        self.container.register(ProductController, factory=lambda: ProductController(
            app_shell=self.app,
            db=self.model.db,
            product_model=self.model,
            view=self.view,
            product_facade=self.container.resolve(ProductFacade),
            fabricacion_service=self.container.resolve(FabricacionService),
            planning_facade=self.container.resolve(PlanningFacade),
            material_service=self.container.resolve(ProductService),
            machine_service=self.container.resolve(MachineService),
            state=self.container.resolve(ApplicationState),
        ))
        self.container.register(WorkerController, factory=lambda: WorkerController(
            app_controller=self.app,
            view=self.view,
            worker_service=self.container.resolve(WorkerService),
            product_service=self.container.resolve(ProductService),
            fabricacion_service=self.container.resolve(FabricacionService),
            workers_changed_signal=self.model.workers_changed_signal,
        ))
        self.container.register(PilaController, factory=lambda: PilaController(
            app_controller=self.app,
            view=cast(IPilaView, self.view),
            system_integration=self.container.resolve(SystemIntegrationService),
            product_service=self.container.resolve(ProductService),
            fabricacion_service=self.container.resolve(FabricacionService),
            pila_service=self.container.resolve(PilaService),
            state=self.app.state,
            schedule_manager=self.schedule_manager,
        ))
        self.container.register(SimulationController, factory=lambda: SimulationController(
            self.app,
            self.container.resolve(WorkerService),
            self.container.resolve(MachineService),
            self.container.resolve(PilaService),
        ))
        self.container.register(HistorialController, factory=lambda: HistorialController(
            self.model.db,
            self.container.resolve(PilaService),
            self.container.resolve(WorkerService),
            cast('MainView', self.view),
            self.logger,
        ))
        
        self.container.register(ScheduleController, factory=lambda: ScheduleController(
            self.model.db, self.view, self.schedule_manager, self.logger
        ))
        self.container.register(SessionController, factory=lambda: SessionController(
            self.app, self.app.db, self.container.resolve(WorkerService)
        ))
        
        # Resolve instances and attach to AppController
        self.app.backup_controller = self.container.resolve(BackupController)
        self.app.report_controller = self.container.resolve(ReportController)
        self.app.hardware_controller = self.container.resolve(HardwareController)
        self.app.machine_controller = self.container.resolve(MachineController)
        self.app.calculation_controller = self.container.resolve(CalculationController)

        self.app.product_controller = self.container.resolve(ProductController)
        self.app.worker_controller = self.container.resolve(WorkerController)
        self.app.pila_controller = self.container.resolve(PilaController)
        self.app.simulation_controller = self.container.resolve(SimulationController)
        self.app.schedule_controller = self.container.resolve(ScheduleController)
        self.app.historial_controller = self.container.resolve(HistorialController)
        self.app.session_controller = self.container.resolve(SessionController)
        
        # NEW CONTROLLERS (Refactor Fase 2)
        # Register them in DI setup
        self.container.register(FileController, factory=lambda: FileController(
            self.model.db, self.view, self.app.logger
        ))
        self.container.register(PreprocesoController, factory=lambda: PreprocesoController(
            db_manager=self.model.db,
            view=self.view,
            fabricacion_service=self.container.resolve(FabricacionService),
            logger=self.logger
        ))
        self.container.register(FabricacionController, factory=lambda: FabricacionController(
            self.model.db, self.view, self.app.product_controller, self.app.logger
        ))
        self.container.register(LoteController, factory=lambda: LoteController(
            self.model.db, self.view, self.app.pila_controller, self.app.logger
        ))
        self.container.register(UIController, factory=lambda: UIController(
            self.view,
            self.container.resolve(MachineService),
            self.container.resolve(WorkerService),
            self.container.resolve(ReportService),
            self.container.resolve(ProductService),
            self.app.worker_controller,
            self.app.machine_controller,
            cast('QuoteService', self.app.quote_service),
            cast('QThreadPool', self.app.thread_pool),
            self.app.logger
        ))
        self.container.register(NavigationController, factory=lambda: NavigationController(
            self.app, self.view, self.container.resolve(ProductService), self.app.logger
        ))
        self.container.register(UISignalsController, factory=lambda: UISignalsController(self.app))

        # Resolve instances and attach to AppController
        self.app.file_controller = self.container.resolve(FileController)
        self.app.preproceso_controller = self.container.resolve(PreprocesoController)
        self.app.fabricacion_controller = self.container.resolve(FabricacionController)
        self.app.lote_controller = self.container.resolve(LoteController)
        self.app.ui_controller = self.container.resolve(UIController)
        self.app.navigation_controller = self.container.resolve(NavigationController)
        self.app.ui_signals_controller = self.container.resolve(UISignalsController)
        
        self.logger.info("Controladores inicializados correctamente.")


