# -*- coding: utf-8 -*-
"""
Nombre del Módulo: controller.py (Simulation)
Descripción: Controlador principal para el módulo de simulación. Orquesta la ejecución 
             de hilos de cálculo, la optimización de recursos y la persistencia de flujos.
"""
from __future__ import annotations
import logging
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING
from PyQt6.QtCore import QObject

from core.simulation.simulation_engine import SimulationWorker
from core.services.flow_builder_service import FlowBuilderService
from .execution_manager import SimulationExecutionManager
from .editor_manager import SimulationEditorManager
from .optimizer_worker import OptimizerWorker

if TYPE_CHECKING:
    from controllers.app_controller import AppController
    from database.database_manager import DatabaseManager
    from core.schedule_config import ScheduleConfig
    from core.dtos import ProductionFlowStepDTO


class SimulationController(QObject):
    """
    Controlador de simulaciones y optimización.

    Encargado de coordinar el motor de simulación con la interfaz de usuario, 
    gestionando hilos de ejecución para evitar bloqueos y delegando tareas a los managers.
    """
    app: AppController
    db: DatabaseManager
    view: Any
    schedule_manager: ScheduleConfig
    logger: logging.Logger
    flow_builder: FlowBuilderService
    execution_thread: Optional[Any]
    worker: Optional[Union[OptimizerWorker, SimulationWorker]]
    state: Any # ApplicationState

    def __init__(
        self,
        app_controller: "AppController",
        worker_service: Any,
        machine_service: Any,
        pila_service: Any,
    ) -> None:
        """
        Inicializa el controlador de simulaciones.

        Args:
            app_controller: Referencia al controlador principal de la aplicación.
            worker_service: Servicio de trabajadores (inyectado).
            machine_service: Servicio de máquinas (inyectado).
            pila_service: Servicio de pilas (inyectado).
        """
        super().__init__()
        self.app = app_controller
        self.db: "DatabaseManager" = app_controller.db

        self.worker_service = worker_service
        self.machine_service = machine_service
        self.pila_service = pila_service

        self.view: Any = app_controller.view
        self.schedule_manager: "ScheduleConfig" = app_controller.schedule_manager
        self.logger = logging.getLogger("EvolucionTiemposApp")
        self.flow_builder = FlowBuilderService()

        self.execution_thread: Optional[Any] = None  # QThread
        self.worker: Optional[Union[OptimizerWorker, SimulationWorker]] = None
        
        from core.di_container import DIContainer
        from core.application_state import ApplicationState
        self.state = DIContainer.get_instance().resolve(ApplicationState)

        self.execution_manager = SimulationExecutionManager(
            self.app,
            self.db,
            self.worker_service,
            self.machine_service,
            self.pila_service,
            self.view,
            self.state,
            self.schedule_manager,
            self,
        )
        self.editor_manager = SimulationEditorManager(
            self.app,
            self.db,
            self.worker_service,
            self.pila_service,
            self.view,
            self.state,
            self.schedule_manager,
            self,
        )

    # Delegación de SimulationExecutionManager
    def _on_run_manual_plan_clicked(self) -> None:
        self.execution_manager.on_run_manual_plan_clicked()

    def _on_execute_optimizer_simulation_clicked(self) -> None:
        self.execution_manager.on_execute_optimizer_simulation_clicked()

    def _start_simulation_thread(self, scheduler: Any) -> None:
        self.execution_manager.start_simulation_thread(scheduler)

    def _on_simulation_finished(self, results: List[Dict[str, Any]], audit: List[str]) -> None:
        self.execution_manager._on_simulation_finished(results, audit)

    def _on_optimization_finished(
        self, results: Optional[List[Dict[str, Any]]], audit: List[str], workers_needed: int
    ) -> None:
        self.execution_manager._on_optimization_finished(results, audit, workers_needed)

    def _handle_run_manual_from_visual_editor(self, flow_dialog: Any) -> None:
        self.execution_manager.handle_run_manual_from_visual_editor(flow_dialog)

    def _handle_run_optimizer_from_visual_editor(self, flow_dialog: Any) -> None:
        self.execution_manager.handle_run_optimizer_from_visual_editor(flow_dialog)

    # Delegación de SimulationEditorManager
    def _on_define_flow_clicked(self) -> None:
        self.editor_manager.on_define_flow_clicked()

    def _open_editor_with_loaded_flow(
        self, production_flow: List[Dict[str, Any]], pila_nombre: str, units: int = 1
    ) -> None:
        self.editor_manager.open_editor_with_loaded_flow(production_flow, pila_nombre, units)

    def _on_clear_simulation(self) -> None:
        self.logger.info("Limpiando la vista de cálculo y reseteando el flujo de producción.")
        self.state.last_production_flow = None
        
        calc_page_widget = self.view.pages.get("calculate")
        if calc_page_widget is not None:
            calc_page_widget.clear_all()
            calc_page_widget.define_flow_button.setEnabled(False)

    def handle_save_flow_only(
        self,
        nombre: str,
        descripcion: str,
        production_flow: List[Dict[str, Any]] | List["ProductionFlowStepDTO"],
    ) -> Any:
        """Guarda solo el flujo de producción, reconstruyendo los datos necesarios."""
        self.logger.info(f"Guardando solo el flujo de producción para la pila '{nombre}'.")

        pila_de_calculo_reconstruida: Dict[str, Dict[Any, Any]] = {"preprocesos": {}, "productos": {}}
        for step in production_flow:
            if isinstance(step, dict):
                task_info = step.get("task", {})
                original_code = str(task_info.get("original_product_code", ""))
                task_name = str(task_info.get("name", "Desconocido"))
                original_desc = str(task_info.get("original_product_info", {}).get("desc", "Producto Desconocido"))
            else:
                task_info = step.task
                original_code = str(task_info.original_product_code)
                task_name = str(task_info.name)
                original_desc = str(task_info.original_product_info.get("desc", "Producto Desconocido"))

            if "PREP_" in original_code:
                prep_id = int(original_code.replace("PREP_", ""))
                pila_de_calculo_reconstruida["preprocesos"][prep_id] = {
                    "id": prep_id,
                    "nombre": task_name.replace("[PREPROCESO] ", ""),
                }
            else:
                pila_de_calculo_reconstruida["productos"][original_code] = {
                    "codigo": original_code,
                    "descripcion": original_desc,
                }

        simulation_results: List[Any] = []
        unidades: int = 1  
        producto_origen: Optional[str] = None  

        return self.pila_service.save_pila(
            nombre,
            descripcion,
            pila_de_calculo_reconstruida,
            production_flow,
            simulation_results,
            producto_origen,
            unidades=unidades
        )

    def _update_simulation_progress(self, value: int) -> None:
        """Actualiza el valor de la barra de progreso en la UI."""
        calc_page = self.view.pages.get("calculate")
        if calc_page is not None:
            calc_page.progress_bar.setValue(value)

    def _on_calc_product_result_selected(self, item: Any) -> None:
        pass

    def clear_simulation_state(self) -> None:
        """Limpia el estado de la simulación."""
        self.state.last_production_flow = None
        self.state.last_simulation_results = None
        self.state.last_audit_log = None
        self._on_clear_simulation()

