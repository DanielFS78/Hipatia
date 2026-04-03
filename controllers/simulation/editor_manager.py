# -*- coding: utf-8 -*-
"""
Coordinación y señales del subsistema «editor_manager»: enlaza UI, servicios y persistencia para este ámbito de la aplicación Hipatia.
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any, TYPE_CHECKING
from PyQt6.QtWidgets import QApplication
from ui.dialogs import EnhancedProductionFlowDialog, LoadPilaDialog

if TYPE_CHECKING:
    from .controller import SimulationController

class SimulationEditorManager:
    """
    Gestor para la gestión del Editor Visual de Flujo de Producción.
    """

    def __init__(self, app: Any, db: Any, model: Any, view: Any, state: Any, schedule_manager: Any, controller_ref: SimulationController):
        self.app = app
        self.db = db
        self.model = model
        self.view = view
        self.state = state
        self.schedule_manager = schedule_manager
        self.controller_ref = controller_ref
        self.logger = logging.getLogger("EvolucionTiemposApp")
        
        # Servicios
        self.worker_service = model.worker_service
        self.pila_service = model.pila_service

    def on_define_flow_clicked(self) -> None:
        calc_page_widget = self.view.pages.get("calculate")
        if calc_page_widget is None:
             self.view.show_message("Error", "No se encontró el widget de cálculo.", "critical")
             return
        
        calc_page = calc_page_widget 
        
        if not calc_page.planning_session:
            self.view.show_message("Pila Vacía", "Añada al menos un Lote a la Pila antes de definir el flujo.", "warning")
            return

        try:
            tasks_data = self.pila_service.get_data_for_calculation_from_session(calc_page.planning_session)
            if not tasks_data:
                self.view.show_message("Error de Datos", "No se pudieron obtener los detalles de las tareas para la pila actual.", "critical")
                return

            workers_data = self.worker_service.get_all_workers(include_inactive=False)
            worker_names = [w.nombre_completo for w in workers_data]
            units_for_dialog = calc_page.planning_session[0].get("unidades", 1) if calc_page.planning_session else 1

            flow_dialog = EnhancedProductionFlowDialog(tasks_data, worker_names, units_for_dialog, self.app,
                                                       self.schedule_manager, parent=self.view,
                                                       existing_flow=self.state.last_production_flow)

            # (Eventos de botones manejados internamente por el propio diálogo)

            if not flow_dialog.exec(): return

            self.state.last_production_flow = flow_dialog.get_production_flow()

            if self.state.last_production_flow:
                self.view.show_message("Flujo Definido", "El flujo de producción ha sido definido. Ahora puede ejecutar un cálculo.", "info")
            else:
                self.logger.warning("No se definió ningún flujo de producción.")

        except Exception as e:
            self.logger.critical(f"Error crítico durante la definición del flujo: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error inesperado al definir el flujo: {e}", "critical")

    def open_editor_with_loaded_flow(self, production_flow: List[Dict[str, Any]], pila_nombre: str, units: int = 1) -> None:
        try:
            tasks_data = []
            seen_products = set()
            for step in production_flow:
                task_info = step.get('task', {})
                product_code = task_info.get('original_product_code', '')
                if product_code in seen_products: continue
                seen_products.add(product_code)
                original_info = task_info.get('original_product_info', {})
                task_data = {
                    'codigo': product_code,
                    'descripcion': task_info.get('name', original_info.get('desc', 'Tarea sin nombre')),
                    'tiene_subfabricaciones': False,
                    'tiempo_optimo': task_info.get('duration_per_unit', 0),
                    'departamento': task_info.get('department', 'General'),
                    'tipo_trabajador': task_info.get('required_skill_level', 1),
                    'requiere_maquina_tipo': task_info.get('requiere_maquina_tipo'),
                    'sub_partes': []
                }
                tasks_data.append(task_data)

            if not tasks_data:
                self.logger.warning("No se pudieron reconstruir tasks_data del flujo para el editor.")
                return

            workers_data = self.worker_service.get_all_workers(include_inactive=False)
            worker_names = [w.nombre_completo for w in workers_data]

            flow_dialog = EnhancedProductionFlowDialog(tasks_data, worker_names, units, self.app,
                                                       self.schedule_manager, parent=self.view,
                                                       existing_flow=production_flow)
            
            flow_dialog.setWindowTitle(f"Editor de Flujo - {pila_nombre}")

            # (Eventos de botones manejados internamente por el propio diálogo)

            if flow_dialog.exec():
                self.state.last_production_flow = flow_dialog.get_production_flow()

        except Exception as e:
            self.logger.error(f"Error abriendo editor con flujo cargado: {e}", exc_info=True)
