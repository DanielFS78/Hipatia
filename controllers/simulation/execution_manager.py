# -*- coding: utf-8 -*-
"""
Nombre del Módulo: execution_manager.py (Simulation)
Descripción: Gestor encargado de la ejecución física de las simulaciones, 
             manejando hilos de trabajo, optimizadores y comunicación de resultados a la UI.
"""
from __future__ import annotations
import logging
from datetime import datetime, time
from typing import Any, List, Dict, Optional, Union, TYPE_CHECKING
from PyQt6.QtCore import QObject, QThread, QTimer
from PyQt6.QtWidgets import QApplication

from core.simulation.simulation_engine import SimulationWorker, Optimizer
from core.services.time_calculator import CalculadorDeTiempos
from ui.dialogs import GetOptimizationParametersDialog, EnhancedProductionFlowDialog
from .optimizer_worker import OptimizerWorker
from .execution_helpers import (
    build_scheduler,
    enable_result_actions,
    set_planning_units,
    start_optimizer_thread,
)

if TYPE_CHECKING:
    from .controller import SimulationController

class SimulationExecutionManager:
    """
    Gestor de ejecución de simulaciones.

    Encargado de configurar el motor de simulación (Scheduler), gestionar los 
    hilos de ejecución de cálculo manual y disparar el proceso de optimización.
    """

    def __init__(self, app: Any, db: Any, model: Any, view: Any, state: Any, schedule_manager: Any, controller_ref: SimulationController):
        """
        Inicializa el gestor de ejecución.

        Args:
            app: Referencia a la aplicación principal.
            db: Gestor de base de datos.
            model: Modelo de la aplicación.
            view: Referencia a la vista principal.
            state: Estado compartido.
            schedule_manager: Gestor de horarios.
            controller_ref: Referencia al controlador de simulación.
        """
        self.app = app
        self.db = db
        self.model = model
        self.view = view
        self.state = state
        self.schedule_manager = schedule_manager
        self.controller_ref = controller_ref
        self.logger = logging.getLogger("EvolucionTiemposApp")
        
        # Servicios ruteados
        self.worker_service = model.worker_service
        self.machine_service = model.machine_service
        self.pila_service = model.pila_service

    def _prepare_large_visual_simulation(self, flow_dialog: Any, task_count: int) -> None:
        """Minimiza efectos visuales en simulaciones grandes para reducir carga de UI."""
        if task_count <= 20:
            return
        if not hasattr(flow_dialog, "canvas_tasks"):
            return
        try:
            for canvas_task in flow_dialog.canvas_tasks:
                for key in ("golden_glow_effect_widget", "green_cycle_effect_widget", "mixed_effect_widget"):
                    effect = canvas_task.get(key)
                    if effect and hasattr(effect, "stop_animation"):
                        effect.stop_animation()
        except Exception as exc:
            self.logger.warning("No se pudo preparar optimización visual previa: %s", exc)

    def on_run_manual_plan_clicked(self) -> None:
        calc_page_widget = self.view.pages.get("calculate")
        if calc_page_widget is None: return
        calc_page = calc_page_widget

        if not self.state.last_production_flow:
            self.view.show_message("Flujo no Definido", "Debe pulsar 'Definir Flujo de Producción' antes de ejecutar un cálculo manual.", "warning")
            return

        try:
            production_flow = self.state.last_production_flow
            self.view.statusBar().showMessage("Construyendo plan de tareas...")
            calc_page.show_progress()
            QApplication.processEvents()

            scheduler = build_scheduler(
                production_flow=production_flow,
                worker_service=self.worker_service,
                machine_service=self.machine_service,
                schedule_manager=self.schedule_manager,
                time_calculator_cls=CalculadorDeTiempos,
            )

            self.start_simulation_thread(scheduler)

        except Exception as e:
            self.logger.critical(f"Error crítico en cálculo manual: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error inesperado: {e}", "critical")

    def on_execute_optimizer_simulation_clicked(self) -> None:
        calc_page_widget = self.view.pages.get("calculate")
        if calc_page_widget is None: 
            return
        calc_page = calc_page_widget

        if not calc_page.planning_session:
            self.view.show_message("Pila Vacía", "Añada al menos un Lote a la Pila antes de optimizar.", "warning")
            return

        dialog = GetOptimizationParametersDialog(self.view)
        if not dialog.exec(): return

        params = dialog.get_parameters()
        start_date = datetime.combine(params["start_date"], time(7, 0))
        end_date = params["end_date"]

        set_planning_units(calc_page.planning_session, params["units"])
        calc_page._update_plan_display()

        self.view.statusBar().showMessage("Iniciando optimización, por favor espere...")
        calc_page.show_progress()

        production_flow_to_use = self.state.last_production_flow

        try:
            optimizer = Optimizer(
                planning_session=calc_page.planning_session,
                db_manager=self.db,
                worker_service=self.worker_service,
                pila_service=self.pila_service,
                schedule_config=self.schedule_manager,
                production_flow_override=production_flow_to_use
            )

            start_optimizer_thread(
                optimizer=optimizer,
                start_date=start_date,
                end_date=end_date,
                units=params["units"],
                thread_cls=QThread,
                worker_cls=OptimizerWorker,
                on_finished=self._on_optimization_finished,
                controller_ref=self.controller_ref,
            )

        except Exception as e:
            self.logger.critical(f"Error al iniciar el optimizador: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"No se pudo iniciar la optimización: {e}", "critical")
            calc_page.hide_progress()

    def start_simulation_thread(self, scheduler: Any, visual_dialog_reference: Any | None = None) -> None:
        try:
            if self.controller_ref.execution_thread is not None and self.controller_ref.execution_thread.isRunning():
                self.view.show_message("Simulación en Curso", "Espere a que termine la simulación actual.", "warning")
                return
        except RuntimeError: 
            self.controller_ref.execution_thread = None

        calc_page_widget = self.view.pages.get("calculate")
        
        if calc_page_widget is not None: 
            calc_page_widget.show_progress()

        exec_thread = QThread()
        worker = SimulationWorker(scheduler)
        worker.moveToThread(exec_thread)

        self.controller_ref.execution_thread = exec_thread
        self.controller_ref.worker = worker

        exec_thread.started.connect(worker.run)
        worker.finished.connect(self._on_simulation_finished)
        if visual_dialog_reference is not None and hasattr(visual_dialog_reference, "simulation_finished"):
            worker.finished.connect(lambda *_: visual_dialog_reference.simulation_finished.emit())
        worker.finished.connect(worker.deleteLater)
        exec_thread.finished.connect(exec_thread.deleteLater)
        exec_thread.finished.connect(lambda: setattr(self.controller_ref, 'execution_thread', None))
        
        if calc_page_widget is not None:
             worker.progress_update.connect(lambda val, msg: calc_page_widget.set_progress_status(msg, val))

        exec_thread.start()

    def _on_simulation_finished(self, results: List[Dict[str, Any]], audit: List[str]) -> None:
        calc_page_widget = self.view.pages.get("calculate")
        if calc_page_widget is None: return
        calc_page = calc_page_widget

        if results:
            calc_page.set_progress_status("Procesando resultados...", 100)
            QApplication.processEvents()

            self.state.last_simulation_results = results
            self.state.last_audit_log = audit
            calc_page.display_simulation_results(results, audit)

            enable_result_actions(calc_page, include_go_home=True)

            if getattr(self.state, 'last_pila_id_calculated', None) is not None:
                calc_page.last_pila_id = self.state.last_pila_id_calculated

    def _on_optimization_finished(self, results: Optional[List[Dict[str, Any]]], audit: List[str], workers_needed: int) -> None:
        calc_page_widget = self.view.pages.get("calculate")
        if calc_page_widget is not None:
             calc_page_widget.hide_progress()
        
        calc_page = calc_page_widget

        if results:
            self.state.last_simulation_results = results
            self.state.last_audit_log = audit
            self.state.last_flexible_workers_needed = workers_needed
            
            if calc_page:
                calc_page.display_simulation_results(results, audit)
                enable_result_actions(calc_page)

            message = f"Optimización completada.\nSe necesitan **{workers_needed}** trabajadores flexibles adicionales para cumplir los plazos."
            if workers_needed == 0: message = "Optimización completada. Se cumplen los plazos con el personal actual."
            self.view.show_message("Resultado Optimización", message, "info")
        else:
            self.view.show_message("Optimización Fallida", "No se pudo encontrar una solución viable.", "warning")

    def handle_run_manual_from_visual_editor(self, flow_dialog: "EnhancedProductionFlowDialog") -> None:
        raw_production_flow = flow_dialog.get_production_flow()
        if not raw_production_flow: return

        try:
            self._prepare_large_visual_simulation(flow_dialog, len(raw_production_flow))
            self.view.statusBar().showMessage("Construyendo plan de tareas...")
            QApplication.processEvents()

            scheduler = build_scheduler(
                production_flow=raw_production_flow,
                worker_service=self.worker_service,
                machine_service=self.machine_service,
                schedule_manager=self.schedule_manager,
                time_calculator_cls=CalculadorDeTiempos,
                visual_dialog_reference=flow_dialog,
            )

            self.start_simulation_thread(scheduler, visual_dialog_reference=flow_dialog)
            self.logger.info("Simulación manual iniciada desde el editor visual.")

        except Exception as e:
            self.logger.critical(f"Error crítico en el flujo de planificación manual desde editor: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error inesperado al iniciar el cálculo manual: {e}", "critical")

    def handle_run_optimizer_from_visual_editor(self, flow_dialog: "EnhancedProductionFlowDialog") -> None:
        production_flow = flow_dialog.get_production_flow()
        if not production_flow: return

        calc_page_widget = self.view.pages.get("calculate")
        if calc_page_widget is None:
            self.view.show_message("Error", "No se encontró el widget de cálculo.", "critical")
            return
        calc_page = calc_page_widget

        if not calc_page.planning_session:
            self.view.show_message("Pila Vacía", "La pila de producción de la página principal está vacía.", "warning")
            return

        dialog = GetOptimizationParametersDialog(self.view)
        if not dialog.exec(): return

        params = dialog.get_parameters()
        start_date = datetime.combine(params["start_date"], time(7, 0))
        end_date = params["end_date"]
        units_to_produce = params['units']

        set_planning_units(calc_page.planning_session, units_to_produce)
        calc_page._update_plan_display()

        self.view.statusBar().showMessage("Iniciando optimización, por favor espere...")
        QApplication.processEvents()

        try:
            optimizer = Optimizer(
                planning_session=calc_page.planning_session,
                db_manager=self.db,
                worker_service=self.worker_service,
                pila_service=self.pila_service,
                schedule_config=self.schedule_manager,
                production_flow_override=production_flow,
                visual_dialog_reference=flow_dialog
            )

            start_optimizer_thread(
                optimizer=optimizer,
                start_date=start_date,
                end_date=end_date,
                units=units_to_produce,
                thread_cls=QThread,
                worker_cls=OptimizerWorker,
                on_finished=self._on_optimization_finished,
                controller_ref=self.controller_ref,
            )

        except Exception as e:
            self.logger.critical(f"Error crítico al iniciar el optimizador desde editor visual: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"No se pudo iniciar la optimización: {e}", "critical")
            calc_page.hide_progress()
