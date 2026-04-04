# -*- coding: utf-8 -*-
"""
Nombre del Módulo: pila_manager.py
Descripción: Gestor especializado en el ciclo de vida de las Pilas de fabricación.
             Maneja el cargado, guardado, eliminación y visualización de la bitácora.
"""
from typing import Any, List, Dict, Optional, Tuple, cast
import logging
from datetime import datetime
from PyQt6.QtWidgets import QDialog, QWidget

from controllers.pila.protocols import IPilaView, IPilaService
from ui.dialogs import LoadPilaDialog, SavePilaDialog, FabricacionBitacoraDialog
from core.services.time_calculator import CalculadorDeTiempos
from core.dtos import SimulationResultTaskDTO, CalculationStepDTO

class PilaManager:
    """
    Gestor de ciclo de vida de Pilas.
    Coordina la persistencia y recuperación de sesiones de planificación.
    """
    def __init__(
        self, 
        view: IPilaView, 
        pila_service: IPilaService,
        state: Any,
        schedule_manager: Any,
        app_ref: Any
    ) -> None:
        self._view = view
        self._pila_service = pila_service
        self._state = state
        self._schedule_manager = schedule_manager
        self._app = app_ref
        self.logger = logging.getLogger("EvolucionTiemposApp")

    def load_pila(self) -> None:
        """Muestra el diálogo de carga y procesa la pila seleccionada."""
        calc_page = self._view.pages.get("calculate")
        if not calc_page: return

        pilas_list = self._pila_service.get_all_pilas()
        if not pilas_list:
            self._view.show_message("Sin Datos", "No hay pilas guardadas.", "info")
            return

        dialog = LoadPilaDialog(pilas_list, cast(QWidget, self._view))
        if not dialog.exec():
            return
        selected_id = dialog.get_selected_id()
        if selected_id is None:
            return
        pila_id = int(selected_id)
        if dialog.delete_requested:
            self._handle_delete_pila(pila_id)
            return

        self.logger.info(f"Cargando datos para la Pila ID: {pila_id}")
        meta_data, pila_de_calculo, production_flow, results = self._pila_service.load_pila(pila_id)

        if not meta_data:
            self._view.show_message("Error de Carga", "No se pudieron cargar los datos de la pila.", "critical")
            return

        self._apply_loaded_pila_to_ui(meta_data, pila_de_calculo, production_flow, results, pila_id)

    def _handle_delete_pila(self, pila_id: int) -> None:
        """Maneja la eliminación de una pila tras confirmación."""
        if self._view.show_confirmation_dialog("Confirmar", "¿Seguro que desea eliminar esta pila?"):
            if self._pila_service.delete_pila(pila_id):
                self._view.show_message("Éxito", "La pila ha sido eliminada.", "info")
            else:
                self._view.show_message("Error", "No se pudo eliminar la pila.", "critical")

    def _apply_loaded_pila_to_ui(self, meta_data, pila_de_calculo, production_flow, results, pila_id) -> None:
        """Actualiza el estado de la aplicación y la UI con los datos cargados."""
        calc_page = self._view.pages.get("calculate")
        if not calc_page: return

        if self._app.simulation_controller:
            self._app.simulation_controller._on_clear_simulation()

        try:
            planning_item = CalculationStepDTO(
                identificador=meta_data.nombre,
                lote_codigo="(Pila Cargada)", 
                unidades=meta_data.unidades,
                deadline=None, 
                pila_de_calculo_directa=pila_de_calculo,
                lote_template_id=None
            )
            calc_page.planning_session = [planning_item]
            calc_page._update_plan_display()

            self._state.last_production_flow = production_flow
            self._state.last_pila_id_calculated = pila_id

            if results:
                self._state.last_simulation_results = self._reparse_dates(results)
                self._state.last_audit_log = []
                calc_page.display_simulation_results(self._state.last_simulation_results, [])

            calc_page.define_flow_button.setEnabled(True)
            calc_page.execute_manual_button.setEnabled(True)
            calc_page.execute_optimizer_button.setEnabled(True)

            self._view.show_message("Pila Cargada", f"Se ha cargado '{meta_data.nombre}'.", "info")
            
            if self._app.simulation_controller and production_flow is not None:
                self._app.simulation_controller._open_editor_with_loaded_flow(production_flow, meta_data.nombre, meta_data.unidades)

        except Exception as e:
            self.logger.critical(f"Error al procesar la pila cargada: {e}", exc_info=True)
            self._view.show_message("Error Crítico", f"Ocurrió un error al procesar la pila cargada: {e}", "critical")

    def save_pila(self) -> None:
        """Muestra el diálogo de guardado y persiste la pila actual."""
        calc_page = self._view.pages.get("calculate")
        if not calc_page: return
        
        if not self._state.last_production_flow:
            self._view.show_message("Acción no disponible", "Primero debe definir un flujo de producción para poder guardarlo.", "warning")
            return

        dialog = SavePilaDialog(cast(QWidget, self._view))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nombre, descripcion = dialog.get_data()
            if not nombre:
                self._view.show_message("Validación Fallida", "El nombre es obligatorio.", "critical")
                return

            pila_de_calculo_actual = calc_page.get_pila_for_calculation()
            producto_origen = self._state.selected_product_for_calc
            resultados_a_guardar = self._state.last_simulation_results or []

            pila_id = self._pila_service.save_pila(
                nombre, descripcion, pila_de_calculo_actual, self._state.last_production_flow,
                resultados_a_guardar, producto_origen, unidades=1
            )

            if pila_id and pila_id != "UNIQUE_CONSTRAINT":
                if resultados_a_guardar:
                    calc_page.last_pila_id = pila_id
                    calc_page.manage_bitacora_button.setEnabled(True)
                self._view.show_message("Éxito", f"Pila '{nombre}' guardada correctamente.", "info")

    def view_bitacora(self) -> None:
        """Abre el diálogo de bitácora para la pila actual."""
        calc_page = self._view.pages.get("calculate")
        if not calc_page: return
        
        pila_id = calc_page.last_pila_id
        if pila_id is None:
            self._view.show_message("Error", "No hay una pila cargada para ver la bitácora.", "warning")
            return
            
        pila_data, _, _, results = self._pila_service.load_pila(pila_id)
        if not pila_data:
            self._view.show_message("Error", "No se pudo cargar la pila.", "critical")
            return
            
        time_calculator = CalculadorDeTiempos(self._schedule_manager)
        results_dto: list[SimulationResultTaskDTO] = []
        for row in (results or []):
            if not isinstance(row, dict):
                continue
            inicio = row.get("Inicio")
            fin = row.get("Fin")
            tarea = row.get("Tarea")
            if not (isinstance(inicio, datetime) and isinstance(fin, datetime) and isinstance(tarea, str)):
                continue
            results_dto.append(SimulationResultTaskDTO(Inicio=inicio, Fin=fin, Tarea=tarea))

        dialog = FabricacionBitacoraDialog(
            pila_id,
            pila_data.nombre,
            results_dto,
            self._app,
            time_calculator,
            cast(QWidget, self._view),
            pila_service=self._pila_service,
        )
        dialog.exec()

    def _reparse_dates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convierte fechas ISO de resultados de simulación a objetos datetime."""
        for task in results:
            for key in ['Inicio', 'Fin']:
                if key in task and isinstance(task[key], str):
                    try:
                        task[key] = datetime.fromisoformat(task[key])
                    except (ValueError, TypeError):
                        self.logger.warning(f"No se pudo convertir fecha '{task[key]}' para tarea '{task.get('Tarea')}'.")
        return results
