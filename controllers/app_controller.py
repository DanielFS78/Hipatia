# -*- coding: utf-8 -*-
"""
Nombre del Módulo: app_controller.py
Descripción: Orquestador central de la aplicación. Gestiona el ciclo de vida de los 
             sub-controladores y coordina la comunicación entre el modelo global y la vista principal.
"""
from __future__ import annotations
import logging
import sys
import os
from typing import Optional, TYPE_CHECKING, Any, List, Dict, Callable
from PyQt6.QtCore import QThreadPool

from core.interfaces.controller_interface import IController
from core.interfaces.view_interface import IView
from core.app_model import AppModel
from core.schedule_config import ScheduleConfig
# Alias de importación por compatibilidad
from core.utils.helpers import resource_path

if TYPE_CHECKING:
    from core.dtos import FileOperationResultDTO, ProductionFlowStepDTO
    from controllers.startup_controller import StartupController
    from controllers.ui_signals_controller import UISignalsController
    from controllers.session_controller import SessionController
    # Sub-controllers (loaded dynamically/via DI)
    from controllers.navigation_controller import NavigationController
    from controllers.ui_controller import UIController
    from controllers.product_controller_v2 import ProductController
    from controllers.worker.controller import WorkerController
    from controllers.pila_controller import PilaController
    from controllers.simulation.controller import SimulationController
    from controllers.report_controller import ReportController
    from controllers.hardware_controller import HardwareController
    from controllers.machine_controller import MachineController
    from controllers.calculation_controller import CalculationController
    from controllers.historial.controller import HistorialController
    from controllers.schedule_controller import ScheduleController
    from controllers.file_controller import FileController
    from controllers.preproceso_controller import PreprocesoController
    from controllers.fabricacion_controller import FabricacionController
    from controllers.lote_controller import LoteController
    from controllers.backup_controller import BackupController
    from core.di_container import DIContainer
    from core.application_state import ApplicationState
    from core.qr_generator import QrGenerator
    from core.label_manager import LabelManager
    from core.security.security_service import SecurityService
    from core.quote_service import QuoteService
class AppController(IController):
    """
    Controlador Principal de la Aplicación.

    Actúa como el 'Hub' central de la lógica de negocio, encargándose de la 
    inicialización de la infraestructura, la inyección de dependencias a través 
    del contenedor DI y la delegación de tareas a controladores especializados.
    """
    model: AppModel
    db: Any
    view: IView
    schedule_manager: ScheduleConfig
    logger: logging.Logger
    container: Any # DIContainer
    startup_controller: Any # StartupController
    ui_signals_controller: Any # UISignalsController
    session_controller: Optional[SessionController]
    navigation_controller: Optional[NavigationController]
    ui_controller: Optional[UIController]
    product_controller: Optional[ProductController]
    worker_controller: Optional[WorkerController]
    pila_controller: Optional[PilaController]
    simulation_controller: Optional[SimulationController]
    report_controller: Optional[ReportController]
    hardware_controller: Optional[HardwareController]
    machine_controller: Optional[MachineController]
    calculation_controller: Optional[CalculationController]
    historial_controller: Optional[HistorialController]
    schedule_controller: Optional[ScheduleController]
    file_controller: Optional[FileController]
    preproceso_controller: Optional[PreprocesoController]
    fabricacion_controller: Optional[FabricacionController]
    lote_controller: Optional[LoteController]
    backup_controller: Optional[BackupController]
    qr_generator: Optional[QrGenerator]
    label_manager: Optional[LabelManager]
    backup_service: Optional[Any]
    audit_logger: Optional[Any]
    maintenance_service: Optional[Any]
    quote_service: Optional[Any]
    thread_pool: Optional[Any]
    security_service: Optional[SecurityService]
    tracking_repo: Any
    label_counter_repo: Any
    state: Optional[ApplicationState]

    def __init__(self, model: AppModel, view: IView, schedule_manager: ScheduleConfig):
        """
        Inicializa el orquestador principal y sus dependencias base.

        Args:
            model: Instancia del modelo de aplicación (AppModel).
            view: Instancia de la vista principal (MainView).
            schedule_manager: Gestor de configuración de horarios.
        """
        super().__init__()
        self.model = model
        self.db = model.db
        self.view = view
        self.schedule_manager = schedule_manager
        self.logger = logging.getLogger("EvolucionTiemposApp")
        
        # --- Dependencias ---
        from core.di_container import DIContainer
        from controllers.startup_controller import StartupController
        from controllers.ui_signals_controller import UISignalsController
        
        self.container = DIContainer.get_instance()
        
        # Controladores de infraestructura
        self.startup_controller = StartupController(self)
        self.ui_signals_controller = UISignalsController(self)
        self.session_controller: Optional['SessionController'] = None
        
        # Placeholder para sub-controladores (serán poblados por StartupController)
        self.navigation_controller: Optional['NavigationController'] = None
        self.ui_controller: Optional['UIController'] = None
        self.product_controller: Optional['ProductController'] = None
        self.worker_controller: Optional['WorkerController'] = None
        self.pila_controller: Optional['PilaController'] = None
        self.simulation_controller: Optional['SimulationController'] = None
        self.report_controller: Optional['ReportController'] = None
        self.hardware_controller: Optional['HardwareController'] = None
        self.machine_controller: Optional['MachineController'] = None
        self.calculation_controller: Optional['CalculationController'] = None
        self.historial_controller: Optional['HistorialController'] = None
        self.schedule_controller: Optional['ScheduleController'] = None
        
        # New controllers
        self.file_controller: Optional['FileController'] = None
        self.preproceso_controller: Optional['PreprocesoController'] = None
        self.fabricacion_controller: Optional['FabricacionController'] = None
        self.lote_controller: Optional['LoteController'] = None
        self.backup_controller: Optional['BackupController'] = None
        


        # Servicios (Referencia rápida)
        self.qr_generator: Optional['QrGenerator'] = None
        self.label_manager: Optional['LabelManager'] = None
        self.backup_service: Optional[Any] = None
        self.audit_logger: Optional[Any] = None
        self.maintenance_service: Optional[Any] = None
        self.quote_service: Optional[Any] = None
        self.thread_pool: Optional[Any] = None
        self.security_service: Optional['SecurityService'] = None
        self.tracking_repo: Any = None
        self.label_counter_repo: Any = None
        
        # Estado Global extraído a ApplicationState (seteado por StartupController)
        self.state: Optional['ApplicationState'] = None

        self.logger.info("Inicializando AppController...")
        # NOTA: No llamamos a initialize() automáticamente para permitir 
        # que el lanzador (app.py) controle el orden exacto.

    def initialize_infra(self) -> None:
        """
        Inicializa la infraestructura básica y los sub-controladores.
        Este método prepara los servicios y estados antes de que se conecten las señales de la UI.
        """
        try:
            self.startup_controller.initialize_app()
            self.logger.info("✅ Infraestructura de AppController inicializada.")
        except Exception as e:
            self.handle_error(e, "Inicialización de Infraestructura")
            raise e

    def connect_all_signals(self) -> None:
        """
        Establece todas las conexiones de señales y slots entre controladores y la UI.
        Debe llamarse una vez que todos los componentes visuales han sido inicializados.
        """
        try:
            self.ui_signals_controller.connect_all_signals()
            self.logger.info("✅ Todas las señales de la aplicación conectadas.")
        except Exception as e:
            self.handle_error(e, "Conexión de Señales")

    def initialize(self) -> None:
        """
        Realiza una inicialización completa de la aplicación (infraestructura + señales).
        Método de conveniencia para arranques estándar.
        """
        self.initialize_infra()
        self.connect_all_signals()
        self.logger.info("✅ AppController (Orquestador) inicializado completamente.")

    def cleanup(self) -> None:
        """Limpieza de recursos al cerrar la aplicación."""
        self.logger.info("Limpiando AppController...")
        
        # Delegar limpieza a sub-controladores si es necesario
        if self.navigation_controller: self.navigation_controller.cleanup()
        if self.report_controller: self.report_controller.cleanup()
        # ... otros
        
        self.logger.info("AppController finalizado.")

    # --- Propiedades de Conveniencia ---

    @property
    def current_user(self) -> Optional[Any]:
        """
        Obtiene el usuario autenticado actualmente a través del controlador de sesión.
        
        Returns:
            Instancia del usuario actual o None si no hay sesión activa.
        """
        return self.session_controller.current_user if self.session_controller else None

    @current_user.setter
    def current_user(self, user: Optional[Any]) -> None:
        """Permite sincronizar el usuario actual con SessionController."""
        if self.session_controller is not None:
            self.session_controller.current_user = user

    def on_data_changed(self) -> None:
        """
        Notifica a los componentes interesados que los datos globales han cambiado.
        Coordina la actualización de la UI y el refresco de tablas de búsqueda.
        """
        # Hub central para notificar cambios de datos
        # Podríamos mover esto a UIController o un EventBus
        self.logger.info("Notificando cambio de datos global.")
        if self.ui_controller:
            self.ui_controller.on_data_changed()
            
        # Refrescar listas específicas si es necesario
        gestion_datos = self.view.get_page("gestion_datos")
        if gestion_datos and hasattr(gestion_datos, "productos_tab"):
             prod_tab = gestion_datos.productos_tab
             if hasattr(prod_tab, "clear_all"): prod_tab.clear_all()
             if hasattr(prod_tab, "update_search_results"):
                 if self.product_controller is not None:
                     all_products = self.product_controller.product_service.search_products("")
                 else:
                     all_products = self.model.product_service.search_products("")
                 prod_tab.update_search_results(all_products)

    # --- Compatibilidad y delegación (API estable absorbida en esta clase) ---

    def handle_save_flow_only(
        self,
        nombre: str,
        descripcion: str,
        production_flow: List[Dict[str, Any]] | List["ProductionFlowStepDTO"],
    ) -> Any:
        if self.simulation_controller is None:
            raise RuntimeError("simulation_controller no inicializado")
        return self.simulation_controller.handle_save_flow_only(nombre, descripcion, production_flow)

    def search_fabricaciones(self, text: str) -> list[Any]:
        if self.fabricacion_controller is not None:
            return self.fabricacion_controller.search_fabricaciones(text)
        if self.product_controller is not None:
            return self.product_controller.search_fabricaciones(text)
        return []

    def show_fabricacion_preprocesos(self, fabricacion_id: int) -> None:
        if self.fabricacion_controller is not None:
            self.fabricacion_controller.show_fabricacion_preprocesos(fabricacion_id)
            return
        if self.product_controller is not None:
            self.product_controller.show_fabricacion_preprocesos(fabricacion_id)
            return
        raise RuntimeError("No hay controlador de fabricación inicializado")

    def logout_user(self) -> None:
        if self.session_controller:
            self.session_controller.logout()

    def handle_login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        if self.session_controller:
            return bool(self.session_controller.handle_login())
        return False

    def _on_export_gantt_to_pdf_clicked(self) -> None:
        if self.report_controller:
            calc_page = self.view.pages.get("calculate")
            self.report_controller.on_export_gantt_to_pdf_clicked(calc_page)

    def load_schedule_settings(self) -> None:
        if self.schedule_controller:
            self.schedule_controller.load_schedule_settings()

    def config_get_setting(self, key: str, default: str = "") -> str:
        """
        Compatibilidad para widgets que reciben AppController durante arranque
        y esperan la API de configuración del ScheduleController.
        """
        if self.schedule_controller is not None:
            return self.schedule_controller.config_get_setting(key, default)
        return self.model.config_get_setting(key, default)

    def config_set_setting(self, key: str, value: str) -> bool:
        """Compatibilidad para escritura de configuración en arranque temprano."""
        if self.schedule_controller is not None:
            return self.schedule_controller.config_set_setting(key, value)
        return self.model.config_set_setting(key, value)

    def on_nav_button_clicked(self, name: str) -> None:
        if self.navigation_controller:
            self.navigation_controller.on_nav_button_clicked(name)

    def handle_attach_file(
        self,
        target_dir: str,
        name_prefix: str | int,
        source_path: str,
        category: str = "general",
    ) -> "FileOperationResultDTO":
        """Delega la adjunción de archivos al FileController."""
        from core.dtos import FileOperationResultDTO

        if self.file_controller:
            try:
                owner_id = int(name_prefix)
            except (ValueError, TypeError):
                owner_id = 0
            return self.file_controller.handle_attach_file(target_dir, owner_id, source_path, category)
        return FileOperationResultDTO(success=False, path_or_error="FileController no inicializado")

