# -*- coding: utf-8 -*-
import logging
from datetime import datetime, time
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QThread, QTimer
from PyQt6.QtWidgets import QDialog, QMessageBox, QListWidgetItem, QApplication

# Core Engines
from simulation_engine import Optimizer, SimulationWorker
from simulation_adapter import AdaptadorScheduler
from time_calculator import CalculadorDeTiempos
import constants

# UI
from ui.dialogs import (
    GetOptimizationParametersDialog, 
    LoadPilaDialog, 
    SavePilaDialog, 
    FabricacionBitacoraDialog,
    EnhancedProductionFlowDialog
)
from ui.widgets import (
    CalculateTimesWidget, 
    DefinirLoteWidget, 
    GestionDatosWidget, 
    LotesWidget
)


class OptimizerWorker(QObject):
    """Worker para ejecutar el Optimizer en un hilo separado."""
    finished = pyqtSignal(object, object, int)  # results, audit, workers_needed

    def __init__(self, optimizer, start_date, end_date, units):
        super().__init__()
        self.optimizer = optimizer
        self.start_date = start_date
        self.end_date = end_date
        self.units = units
        self.logger = logging.getLogger("EvolucionTiemposApp")

    def run(self):
        """Ejecuta el bucle de optimización usando el NUEVO AdaptadorScheduler."""
        self.logger.info("Iniciando ciclo de optimización con el motor de eventos unificado.")
        flexible_workers_needed = 0
        final_results = None

        prioritized_tasks_template = self.optimizer._prepare_and_prioritize_tasks()

        while True:
            self.logger.info(f"--- INICIANDO CICLO CON {flexible_workers_needed} TRABAJADOR(ES) FLEXIBLE(S) ---")

            real_workers_data = self.optimizer.model.worker_repo.get_all_workers(include_inactive=False)
            real_workers = [(data.nombre_completo, data.tipo_trabajador) for data in real_workers_data]
            flexible_workers = [(f"Trabajador Flexible {i + 1}", 3) for i in range(flexible_workers_needed)]
            all_workers_for_sim = real_workers + flexible_workers

            sorted_workers = sorted(all_workers_for_sim, key=lambda w: w[1], reverse=True)

            production_flow = []
            for task_info in prioritized_tasks_template:
                start_date_for_task = None
                if task_info.get('previous_task_index') is None:
                    start_date_for_task = self.start_date

                required_skill = task_info.get('required_skill_level', 1)
                assigned_worker = None

                for worker_name, worker_skill in sorted_workers:
                    if worker_skill >= required_skill:
                        assigned_worker = worker_name
                        break

                workers_list = []
                if assigned_worker:
                    workers_list = [{'name': assigned_worker}]
                else:
                    self.logger.warning(
                        f"No se encontró trabajador con habilidad >= {required_skill} "
                        f"para '{task_info.get('name', 'Tarea')}'"
                    )

                step = {
                    "task": task_info,
                    "workers": workers_list,
                    "machine_id": task_info.get('machine_id'),
                    "trigger_units": self.units,
                    "start_date": start_date_for_task,
                    "previous_task_index": task_info.get('previous_task_index')
                }
                production_flow.append(step)

            all_machines_data = self.optimizer.model.machine_repo.get_all_machines()
            machines_dict = {m.id: m.nombre for m in all_machines_data}
            time_calculator = CalculadorDeTiempos(self.optimizer.schedule_config)

            dialog_ref = getattr(self.optimizer, 'visual_dialog_reference', None)

            scheduler = AdaptadorScheduler(
                production_flow=production_flow,
                all_workers_with_skills=all_workers_for_sim,
                available_machines=machines_dict,
                schedule_config=self.optimizer.schedule_config,
                time_calculator=time_calculator,
                start_date=self.start_date,
                visual_dialog_reference=dialog_ref
            )

            results, audit = scheduler.run_simulation()
            self.optimizer.audit_log.extend(audit)

            all_deadlines_met = self.optimizer._verify_deadlines(results)

            if all_deadlines_met:
                self.logger.info(f"ÉXITO: Plazos cumplidos con {flexible_workers_needed} trabajadores flexibles.")
                final_results = results
                break
            else:
                flexible_workers_needed += 1
                if flexible_workers_needed > 20:
                    self.logger.critical("Límite de 20 trabajadores flexibles alcanzado. Planificación inviable.")
                    final_results = results
                    break

        self.finished.emit(final_results, self.optimizer.audit_log, flexible_workers_needed)


class PilaController(QObject):
    """
    Controlador para la gestión de Pilas, Lotes y Cálculos de Tiempos (Simulaciones).
    Delegado del AppController principal.
    """
    
    def __init__(self, app_controller):
        super().__init__()
        self.app = app_controller
        self.db = app_controller.db
        self.model = app_controller.model
        self.view = app_controller.view
        self.schedule_manager = app_controller.schedule_manager
        self.logger = logging.getLogger("EvolucionTiemposApp")

        self.thread = None
        self.worker = None
        self.OptimizerWorker = OptimizerWorker # Reference for consistency if needed

    # =================================================================================
    # GESTIÓN DE LOTES (DEFINIR LOTE Y GESTIÓN)
    # =================================================================================

    def _on_calc_lote_search_changed(self, text):
        calc_page = self.view.pages["calculate"]
        results = self.model.lote_repo.search_lotes(text)
        calc_page.lote_search_results.clear()
        for lote in results:
            item = QListWidgetItem(f"{lote.codigo} - {lote.descripcion or 'Sin descripción'}")
            item.setData(Qt.ItemDataRole.UserRole, (lote.id, lote.codigo))
            calc_page.lote_search_results.addItem(item)

    def _on_add_lote_to_pila_clicked(self):
        calc_page = self.view.pages.get("calculate")
        if not isinstance(calc_page, CalculateTimesWidget):
            return

        selected = calc_page.lote_search_results.currentItem()
        if not selected:
            self.view.show_message("Selección Requerida", "Por favor, seleccione una plantilla de lote de la lista para añadir.", "warning")
            return

        lote_id, lote_codigo = selected.data(Qt.ItemDataRole.UserRole)
        self.logger.info(f"Añadiendo plantilla de lote '{lote_codigo}' (ID: {lote_id}) a la pila.")

        lote_instance_data = {
            "lote_template_id": lote_id,
            "lote_codigo": lote_codigo,
            "identificador": lote_codigo,
            "unidades": 1,
            "deadline": None
        }

        calc_page.planning_session.append(lote_instance_data)
        calc_page.define_flow_button.setEnabled(True)
        calc_page._update_plan_display()

    def _on_remove_lote_from_pila_clicked(self):
        """
        Quita el elemento seleccionado de la lista 'planning_session' del widget y actualiza la vista.
        """
        calc_page = self.view.pages.get("calculate")
        if not isinstance(calc_page, CalculateTimesWidget):
            return

        selected_rows = calc_page.pila_content_table.selectionModel().selectedRows()
        if not selected_rows:
            self.view.show_message("Selección Requerida", "Seleccione un elemento de la pila para quitar.", "warning")
            return

        rows_to_delete = sorted([r.row() for r in selected_rows], reverse=True)

        for row in rows_to_delete:
            if 0 <= row < len(calc_page.planning_session):
                del calc_page.planning_session[row]
            else:
                self.logger.error(f"Intento de borrar fila {row} fuera de rango.")

        calc_page._update_plan_display()
        
        # Deshabilitar botón flow si la pila se queda vacía
        if not calc_page.planning_session:
            calc_page.define_flow_button.setEnabled(False)

    # --- Definir Lote (Template) ---

    def _on_lote_def_product_search_changed(self, text):
        lote_page = self.view.pages["definir_lote"]
        if len(text) < constants.VALIDATION['MIN_SEARCH_LENGTH']:
            lote_page.product_results.clear()
            return
        results = self.model.product_repo.search_products(text)
        lote_page.product_results.clear()
        for codigo, descripcion in results:
            item = QListWidgetItem(f"{codigo} | {descripcion}")
            item.setData(Qt.ItemDataRole.UserRole, (codigo, descripcion))
            lote_page.product_results.addItem(item)

    def _on_lote_def_fab_search_changed(self, text):
        lote_page = self.view.pages["definir_lote"]
        if len(text) < constants.VALIDATION['MIN_SEARCH_LENGTH']:
            lote_page.fab_results.clear()
            return
        results = self.model.preproceso_repo.search_fabricaciones(text)
        lote_page.fab_results.clear()
        for fab in results:
            item = QListWidgetItem(fab.codigo)
            item.setData(Qt.ItemDataRole.UserRole, (fab.id, fab.codigo))
            lote_page.fab_results.addItem(item)

    def _on_add_product_to_lote_template(self):
        lote_page = self.view.pages["definir_lote"]
        selected = lote_page.product_results.currentItem()
        if not selected: return
        prod_data = selected.data(Qt.ItemDataRole.UserRole)
        lote_page.lote_content["products"].add(prod_data)
        lote_page.update_content_list()
        lote_page.product_search.clear()

    def _on_add_fab_to_lote_template(self):
        lote_page = self.view.pages["definir_lote"]
        selected = lote_page.fab_results.currentItem()
        if not selected: return
        fab_data = selected.data(Qt.ItemDataRole.UserRole)
        lote_page.lote_content["fabrications"].add(fab_data)
        lote_page.update_content_list()
        lote_page.fab_search.clear()

    def _on_remove_item_from_lote_template(self):
        lote_page = self.view.pages["definir_lote"]
        selected = lote_page.lote_content_list.currentItem()
        if not selected: return
        item_type, item_data = selected.data(Qt.ItemDataRole.UserRole)
        if item_type == "product":
            item_to_remove = next((p for p in lote_page.lote_content["products"] if p[0] == item_data), None)
            if item_to_remove: lote_page.lote_content["products"].remove(item_to_remove)
        elif item_type == "fabrication":
            item_to_remove = next((f for f in lote_page.lote_content["fabrications"] if f[0] == item_data), None)
            if item_to_remove: lote_page.lote_content["fabrications"].remove(item_to_remove)
        lote_page.update_content_list()

    def _on_save_lote_template_clicked(self):
        lote_page = self.view.pages.get("definir_lote")
        if not isinstance(lote_page, DefinirLoteWidget): return
        data = lote_page.get_data()

        if not data["codigo"]:
            self.view.show_message("Campo Requerido", "El código del lote es obligatorio.", "warning")
            return
        if not data["product_codes"] and not data["fabricacion_ids"]:
            self.view.show_message("Contenido Vacío", "La plantilla de lote debe contener al menos un producto o fabricación.", "warning")
            return

        lote_id = self.model.lote_repo.create_lote(data)
        if lote_id:
            self.view.show_message("Éxito", f"Plantilla de Lote '{data['codigo']}' guardada correctamente.", "info")
            lote_page.clear_form()
        else:
            self.view.show_message("Error al Guardar", "No se pudo guardar la plantilla. Es posible que el código ya exista.", "critical")

    # --- Gestión Lotes (Tab) ---

    def _connect_lotes_management_signals(self):
        gestion_page = self.view.pages.get("gestion_datos")
        if not isinstance(gestion_page, GestionDatosWidget): return
        lotes_tab = gestion_page.lotes_tab
        if isinstance(lotes_tab, LotesWidget):
            lotes_tab.search_entry.textChanged.connect(self.update_lotes_view)
            lotes_tab.results_list.itemClicked.connect(self._on_lote_management_result_selected)
            lotes_tab.save_lote_signal.connect(self._on_update_lote_template_clicked)
            lotes_tab.delete_lote_signal.connect(self._on_delete_lote_template_clicked)
            self.logger.debug("Señales de 'Gestión Lotes' conectadas.")

    def update_lotes_view(self):
        gestion_page = self.view.pages.get("gestion_datos")
        if not gestion_page: return
        lotes_tab = gestion_page.lotes_tab
        search_query = lotes_tab.search_entry.text()
        lotes = self.model.lote_repo.search_lotes(search_query)

        lotes_tab.results_list.clear()
        for lote in lotes:
            item = QListWidgetItem(f"{lote.codigo} - {lote.descripcion or 'Sin descripción'}")
            item.setData(Qt.ItemDataRole.UserRole, lote.id)
            lotes_tab.results_list.addItem(item)
        
        if not search_query: lotes_tab.clear_edit_area()

    def _on_lote_management_result_selected(self, item):
        lote_id = item.data(Qt.ItemDataRole.UserRole)
        lote_data = self.model.lote_repo.get_lote_details(lote_id)
        if lote_data:
            gestion_page = self.view.pages.get("gestion_datos")
            gestion_page.lotes_tab.display_lote_details(lote_data)
        else:
            self.view.show_message("Error", "No se pudieron cargar los detalles del lote.", "critical")

    def _on_update_lote_template_clicked(self, lote_id):
        gestion_page = self.view.pages.get("gestion_datos")
        lotes_tab = gestion_page.lotes_tab
        data = lotes_tab.get_form_data()
        
        if not data["codigo"]:
            self.view.show_message("Error", "El código no puede estar vacío.", "warning")
            return

        full_details = self.model.lote_repo.get_lote_details(lote_id)
        data['product_codes'] = [p[0] for p in full_details['productos']]
        data['fabricacion_ids'] = [f[0] for f in full_details['fabricaciones']]

        if self.model.lote_repo.update_lote(lote_id, data):
            self.view.show_message("Éxito", "Plantilla de Lote actualizada.", "info")
            self.update_lotes_view()
        else:
            self.view.show_message("Error", "No se pudo actualizar la plantilla.", "critical")

    def _on_delete_lote_template_clicked(self, lote_id):
        if self.view.show_confirmation_dialog("Confirmar", "¿Seguro que desea eliminar esta plantilla de lote?"):
            if self.model.lote_repo.delete_lote(lote_id):
                self.view.show_message("Éxito", "Plantilla de Lote eliminada.", "info")
                self.update_lotes_view()
            else:
                self.view.show_message("Error", "No se pudo eliminar la plantilla.", "critical")


    def _connect_lotes_management_signals(self):
        """Conecta las señales de la pestaña de gestión de Lotes."""
        gestion_page = self.view.pages.get("gestion_datos")
        if not isinstance(gestion_page, GestionDatosWidget):
            return

        lotes_tab = gestion_page.lotes_tab
        if isinstance(lotes_tab, LotesWidget):
            lotes_tab.search_entry.textChanged.connect(self.update_lotes_view)
            lotes_tab.results_list.itemClicked.connect(self._on_lote_management_result_selected)
            lotes_tab.save_lote_signal.connect(self._on_update_lote_template_clicked)
            lotes_tab.delete_lote_signal.connect(self._on_delete_lote_template_clicked)
            self.logger.debug("Señales de 'Gestión Lotes' conectadas.")

    # =================================================================================
    # GESTIÓN DE PILAS (LOAD/SAVE/BITACORA)
    # =================================================================================

    def _reparse_simulation_results_dates(self, results):
        if not results: return []
        for task in results:
            for key in ['Inicio', 'Fin']:
                if key in task and isinstance(task[key], str):
                    try:
                        task[key] = datetime.fromisoformat(task[key])
                    except (ValueError, TypeError):
                        self.logger.warning(f"No se pudo convertir fecha '{task[key]}' para tarea '{task.get('Tarea')}'.")
                        task[key] = None
        return results

    def _on_load_pila_clicked(self):
        calc_page = self.view.pages.get("calculate")
        if not calc_page: return

        pilas_list = self.model.pila_repo.get_all_pilas()
        if not pilas_list:
            self.view.show_message("Sin Datos", "No hay pilas guardadas.", "info")
            return

        dialog = LoadPilaDialog(pilas_list, self.view)
        if not dialog.exec() or dialog.get_selected_id() is None: return

        if dialog.delete_requested:
            pila_id_to_delete = dialog.get_selected_id()
            if self.view.show_confirmation_dialog("Confirmar", "¿Seguro que desea eliminar esta pila?"):
                if self.model.delete_pila(pila_id_to_delete):
                    self.view.show_message("Éxito", "La pila ha sido eliminada.", "info")
                else:
                    self.view.show_message("Error", "No se pudo eliminar la pila.", "critical")
            return

        pila_id = dialog.get_selected_id()
        self.logger.info(f"Cargando datos para la Pila ID: {pila_id}")
        meta_data, pila_de_calculo, production_flow, results = self.model.pila_repo.load_pila(pila_id)

        if not meta_data:
            self.view.show_message("Error de Carga", "No se pudieron cargar los datos de la pila.", "critical")
            return

        self._on_clear_simulation()

        try:
            planning_item = {
                "identificador": meta_data.get("nombre", f"Pila_{pila_id}"),
                "lote_codigo": "(Pila Cargada)", "unidades": meta_data.get("unidades", 1),
                "deadline": None, "pila_de_calculo_directa": pila_de_calculo,
                "lote_template_id": None
            }
            calc_page.planning_session = [planning_item]
            calc_page._update_plan_display()

            self.app.last_production_flow = production_flow
            self.app.last_pila_id_calculated = pila_id

            if results:
                self.app.last_simulation_results = self._reparse_simulation_results_dates(results)
                self.app.last_audit_log = []
                calc_page.display_simulation_results(self.app.last_simulation_results, [])

            calc_page.define_flow_button.setEnabled(True)
            calc_page.execute_manual_button.setEnabled(True)
            calc_page.execute_optimizer_button.setEnabled(True)

            self.view.show_message("Pila Cargada", f"Se ha cargado '{meta_data.get('nombre')}'.", "info")
            
            units_from_pila = meta_data.get("unidades", 1)
            self._open_editor_with_loaded_flow(production_flow, meta_data.get('nombre'), units_from_pila)

        except Exception as e:
            self.logger.critical(f"Error al procesar la pila cargada: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error al procesar la pila cargada: {e}", "critical")
            self._on_clear_simulation()

    def _on_save_pila_clicked(self):
        calc_page = self.view.pages["calculate"]
        if not self.app.last_production_flow:
            self.view.show_message("Acción no disponible", "Primero debe definir un flujo de producción para poder guardarlo.", "warning")
            return

        dialog = SavePilaDialog(self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nombre, descripcion = dialog.get_data()
            if not nombre:
                self.view.show_message("Validación Fallida", "El nombre es obligatorio.", "critical")
                return

            pila_de_calculo_actual = calc_page.get_pila_for_calculation()
            producto_origen = self.app._selected_product_for_calc
            unidades = 1
            resultados_a_guardar = self.app.last_simulation_results if self.app.last_simulation_results is not None else []

            pila_id = self.model.save_pila(
                nombre, descripcion, pila_de_calculo_actual, self.app.last_production_flow,
                resultados_a_guardar, producto_origen, unidades=unidades
            )

            if pila_id and pila_id != "UNIQUE_CONSTRAINT":
                if resultados_a_guardar:
                    calc_page.last_pila_id = pila_id
                    calc_page.manage_bitacora_button.setEnabled(True)
                self.view.show_message("Éxito", f"Pila '{nombre}' guardada correctamente.", "info")

    def _on_ver_bitacora_pila_clicked(self):
        calc_page = self.view.pages["calculate"]
        pila_id = calc_page.last_pila_id
        if pila_id is None:
            self.view.show_message("Error", "No hay una pila cargada para ver la bitácora.", "warning")
            return
        pila_data, _, simulation_results = self.model.pila_repo.load_pila(pila_id)
        if not pila_data:
            self.view.show_message("Error", "No se pudo cargar la pila.", "critical")
            return
        time_calculator = CalculadorDeTiempos(self.schedule_manager)
        dialog = FabricacionBitacoraDialog(pila_id, pila_data['nombre'], simulation_results, self.app, time_calculator, self.view)
        dialog.exec()

    def get_preprocesos_for_fabricacion(self, fabricacion_id: int) -> list:
        try:
            fab_dto = self.model.preproceso_repo.get_fabricacion_by_id(fabricacion_id)
            if not fab_dto or not fab_dto.preprocesos: return []
            return [{"id": p.id, "nombre": p.nombre, "descripcion": p.descripcion} for p in fab_dto.preprocesos]
        except Exception as e:
            self.logger.error(f"Error al obtener los preprocesos vía repositorio: {e}")
            return []

    # =================================================================================
    # CÁLCULO Y SIMULACIÓN
    # =================================================================================

    def _on_define_flow_clicked(self):
        calc_page = self.view.pages.get("calculate")
        if not calc_page or not calc_page.planning_session:
            self.view.show_message("Pila Vacía", "Añada al menos un Lote a la Pila antes de definir el flujo.", "warning")
            return

        try:
            tasks_data = self.model.get_data_for_calculation_from_session(calc_page.planning_session)
            if not tasks_data:
                self.view.show_message("Error de Datos", "No se pudieron obtener los detalles de las tareas para la pila actual.", "critical")
                return

            workers_data = self.model.get_all_workers(include_inactive=False)
            worker_names = [w.nombre_completo for w in workers_data]
            units_for_dialog = calc_page.planning_session[0].get("unidades", 1) if calc_page.planning_session else 1

            flow_dialog = EnhancedProductionFlowDialog(tasks_data, worker_names, units_for_dialog, self.app,
                                                       self.schedule_manager, parent=self.view,
                                                       existing_flow=self.app.last_production_flow)

            flow_dialog.load_pila_button.clicked.connect(lambda: self._handle_load_pila_into_visual_editor(flow_dialog))
            flow_dialog.save_pila_button.clicked.connect(lambda: self._handle_save_pila_from_visual_editor(flow_dialog))
            flow_dialog.clear_button.clicked.connect(lambda: self._handle_clear_visual_editor(flow_dialog))
            flow_dialog.manual_calc_button.clicked.connect(lambda: self._handle_run_manual_from_visual_editor(flow_dialog))
            flow_dialog.optimizer_calc_button.clicked.connect(lambda: self._handle_run_optimizer_from_visual_editor(flow_dialog))

            if not flow_dialog.exec(): return

            self.app.last_production_flow = flow_dialog.get_production_flow()

            if self.app.last_production_flow:
                self.view.show_message("Flujo Definido", "El flujo de producción ha sido definido. Ahora puede ejecutar un cálculo.", "info")
            else:
                self.logger.warning("No se definió ningún flujo de producción.")

        except Exception as e:
            self.logger.critical(f"Error crítico durante la definición del flujo: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error inesperado al definir el flujo: {e}", "critical")

    def _open_editor_with_loaded_flow(self, production_flow, pila_nombre, units=1):
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

            workers_data = self.model.get_all_workers(include_inactive=False)
            worker_names = [w.nombre_completo for w in workers_data]

            flow_dialog = EnhancedProductionFlowDialog(tasks_data, worker_names, units, self.app,
                                                       self.schedule_manager, parent=self.view,
                                                       existing_flow=production_flow)
            
            flow_dialog.setWindowTitle(f"Editor de Flujo - {pila_nombre}")

            # Conectamos las mismas señales
            flow_dialog.load_pila_button.clicked.connect(lambda: self._handle_load_pila_into_visual_editor(flow_dialog))
            flow_dialog.save_pila_button.clicked.connect(lambda: self._handle_save_pila_from_visual_editor(flow_dialog))
            flow_dialog.clear_button.clicked.connect(lambda: self._handle_clear_visual_editor(flow_dialog))
            flow_dialog.manual_calc_button.clicked.connect(lambda: self._handle_run_manual_from_visual_editor(flow_dialog))
            flow_dialog.optimizer_calc_button.clicked.connect(lambda: self._handle_run_optimizer_from_visual_editor(flow_dialog))

            if flow_dialog.exec():
                self.app.last_production_flow = flow_dialog.get_production_flow()

        except Exception as e:
            self.logger.error(f"Error abriendo editor con flujo cargado: {e}", exc_info=True)

    def _on_clear_simulation(self):
        self.logger.info("Limpiando la vista de cálculo y reseteando el flujo de producción.")
        self.app.last_production_flow = None
        calc_page = self.view.pages.get("calculate")
        if isinstance(calc_page, CalculateTimesWidget):
            calc_page.clear_all()
            calc_page.define_flow_button.setEnabled(False)

    def _on_run_manual_plan_clicked(self):
        calc_page = self.view.pages.get("calculate")
        if not isinstance(calc_page, CalculateTimesWidget): return

        if not self.app.last_production_flow:
            self.view.show_message("Flujo no Definido", "Debe pulsar 'Definir Flujo de Producción' antes de ejecutar un cálculo manual.", "warning")
            return

        try:
            production_flow = self.app.last_production_flow
            self.view.statusBar().showMessage("Construyendo plan de tareas...")
            calc_page.show_progress()
            QApplication.processEvents()

            workers_data = self.model.get_all_workers(include_inactive=False)
            worker_names_and_skills = [(w.nombre_completo, w.tipo_trabajador) for w in workers_data]
            all_machines_data = self.model.get_all_machines(include_inactive=False)
            machines_dict = {m.id: m.nombre for m in all_machines_data}
            time_calculator = CalculadorDeTiempos(self.schedule_manager)

            scheduler = AdaptadorScheduler(
                production_flow=production_flow,
                all_workers_with_skills=worker_names_and_skills,
                available_machines=machines_dict,
                schedule_config=self.schedule_manager,
                time_calculator=time_calculator,
                start_date=datetime.now()
            )

            self._start_simulation_thread(scheduler)

        except Exception as e:
            self.logger.critical(f"Error crítico en cálculo manual: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error inesperado: {e}", "critical")

    def _on_execute_optimizer_simulation_clicked(self):
        calc_page = self.view.pages.get("calculate")
        if not calc_page or not calc_page.planning_session:
            self.view.show_message("Pila Vacía", "Añada al menos un Lote a la Pila antes de optimizar.", "warning")
            return

        dialog = GetOptimizationParametersDialog(self.view)
        if not dialog.exec(): return

        params = dialog.get_parameters()
        start_date = datetime.combine(params["start_date"], time(7, 0))
        end_date = params["end_date"]

        for item in calc_page.planning_session: item['unidades'] = params['units']
        calc_page._update_plan_display()

        self.view.statusBar().showMessage("Iniciando optimización, por favor espere...")
        calc_page.show_progress()

        production_flow_to_use = self.app.last_production_flow

        try:
            optimizer = Optimizer(
                calc_page.planning_session,
                self.model,
                self.schedule_manager,
                production_flow_override=production_flow_to_use
            )

            self.thread = QThread()
            self.worker = OptimizerWorker(optimizer, start_date, end_date, params['units'])
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self._on_optimization_finished)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()

        except Exception as e:
            self.logger.critical(f"Error al iniciar el optimizador: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"No se pudo iniciar la optimización: {e}", "critical")
            calc_page.hide_progress()

    def _start_simulation_thread(self, scheduler):
        try:
            if self.thread is not None and self.thread.isRunning():
                self.view.show_message("Simulación en Curso", "Espere a que termine la simulación actual.", "warning")
                return
        except RuntimeError: self.thread = None

        calc_page = self.view.pages.get("calculate")
        if isinstance(calc_page, CalculateTimesWidget): calc_page.show_progress()

        self.thread = QThread()
        self.worker = SimulationWorker(scheduler)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_simulation_finished)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: setattr(self, 'thread', None))
        self.worker.progress_update.connect(lambda val, msg: calc_page.set_progress_status(msg, val) if calc_page else None)

        self.thread.start()

    def _on_simulation_finished(self, results, audit):
        calc_page = self.view.pages.get("calculate")
        if not isinstance(calc_page, CalculateTimesWidget): return

        if results:
            calc_page.set_progress_status("Procesando resultados...", 100)
            QApplication.processEvents()

            self.app.last_simulation_results = results
            self.app.last_audit_log = audit
            calc_page.display_simulation_results(results, audit)

            calc_page.save_pila_button.setEnabled(True)
            calc_page.export_button.setEnabled(True)
            calc_page.export_pdf_button.setEnabled(True)
            calc_page.export_log_button.setEnabled(True)
            calc_page.clear_button.setEnabled(True)
            calc_page.go_home_button.setEnabled(True)

            if hasattr(self.app, 'last_pila_id_calculated'):
                calc_page.last_pila_id = self.app.last_pila_id_calculated

    def _on_optimization_finished(self, results, audit, workers_needed):
        calc_page = self.view.pages.get("calculate")
        calc_page.hide_progress()

        if results:
            self.app.last_simulation_results = results
            self.app.last_audit_log = audit
            self.app.last_flexible_workers_needed = workers_needed
            calc_page.display_simulation_results(results, audit)
            calc_page.save_pila_button.setEnabled(True)
            calc_page.export_button.setEnabled(True)
            calc_page.export_pdf_button.setEnabled(True)
            calc_page.export_log_button.setEnabled(True)
            calc_page.clear_button.setEnabled(True)

            message = f"Optimización completada.\nSe necesitan **{workers_needed}** trabajadores flexibles adicionales para cumplir los plazos."
            if workers_needed == 0: message = "Optimización completada. Se cumplen los plazos con el personal actual."
            self.view.show_message("Resultado Optimización", message, "info")
        else:
            self.view.show_message("Optimización Fallida", "No se pudo encontrar una solución viable.", "warning")

    # --- Handlers from Visual Editor ---

    def _handle_run_manual_from_visual_editor(self, flow_dialog):
        raw_production_flow = flow_dialog.get_production_flow()
        if not raw_production_flow: return

        try:
            self.view.statusBar().showMessage("Construyendo plan de tareas...")
            QApplication.processEvents()

            processed_production_flow = raw_production_flow
            all_workers = self.model.get_all_workers(include_inactive=False)
            sorted_workers = sorted(all_workers, key=lambda w: w.tipo_trabajador, reverse=True)

            for step in processed_production_flow:
                workers_in_step = step.get('workers')
                if not workers_in_step:
                    task_data = step.get('task', {})
                    required_skill = task_data.get('required_skill_level', 1)
                    assigned_worker = None
                    for worker in sorted_workers:
                        if worker.tipo_trabajador >= required_skill:
                            assigned_worker = worker
                            break
                    if assigned_worker:
                        step['workers'] = [{'name': assigned_worker.nombre_completo}]
                    else:
                        step['workers'] = []

            workers_data = self.model.get_all_workers(include_inactive=False)
            worker_names_and_skills = [(w.nombre_completo, w.tipo_trabajador) for w in workers_data]
            all_machines_data = self.model.get_all_machines(include_inactive=False)
            machines_dict = {m.id: m.nombre for m in all_machines_data}
            time_calculator = CalculadorDeTiempos(self.schedule_manager)

            scheduler = AdaptadorScheduler(
                production_flow=processed_production_flow,
                all_workers_with_skills=worker_names_and_skills,
                available_machines=machines_dict,
                schedule_config=self.schedule_manager,
                time_calculator=time_calculator,
                start_date=datetime.now(),
                visual_dialog_reference=flow_dialog
            )

            self._start_simulation_thread(scheduler)
            self.logger.info("Simulación manual iniciada desde el editor visual.")

        except Exception as e:
            self.logger.critical(f"Error crítico en el flujo de planificación manual desde editor: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error inesperado al iniciar el cálculo manual: {e}", "critical")

    def _handle_run_optimizer_from_visual_editor(self, flow_dialog):
        production_flow = flow_dialog.get_production_flow()
        if not production_flow: return

        calc_page = self.view.pages.get("calculate")
        if not calc_page or not calc_page.planning_session:
            self.view.show_message("Pila Vacía", "La pila de producción de la página principal está vacía.", "warning")
            return

        dialog = GetOptimizationParametersDialog(self.view)
        if not dialog.exec(): return

        params = dialog.get_parameters()
        start_date = datetime.combine(params["start_date"], time(7, 0))
        end_date = params["end_date"]
        units_to_produce = params['units']

        for item in calc_page.planning_session: item['unidades'] = units_to_produce
        calc_page._update_plan_display()

        self.view.statusBar().showMessage("Iniciando optimización, por favor espere...")
        QApplication.processEvents()

        try:
            optimizer = Optimizer(
                planning_session=calc_page.planning_session,
                model=self.model,
                schedule_config=self.schedule_manager,
                production_flow_override=production_flow,
                visual_dialog_reference=flow_dialog
            )

            self.thread = QThread()
            self.worker = OptimizerWorker(optimizer, start_date, end_date, units_to_produce)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self._on_optimization_finished)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()

        except Exception as e:
            self.logger.critical(f"Error crítico al iniciar el optimizador desde editor visual: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"No se pudo iniciar la optimización: {e}", "critical")
            calc_page.hide_progress()

    def _handle_load_pila_into_visual_editor(self, flow_dialog):
        """Handler placeholder as it might require breaking the flow or recursion, keeping it simple mainly relies on dialog features."""
        # Typically this dialog handles it internally or calls back to controller to load.
        # But here we are inside the controller, so we can just reuse the load pila logic and update the dialog?
        # The original code called self._on_load_pila_clicked() BUT that opens a prompt and loads into Main UI.
        # Probably we want to load ONLY into the dialog? 
        # The existing dialog has a load button which likely emits a signal or we connected a lambda.
        # In _on_define_flow_clicked: flow_dialog.load_pila_button.clicked.connect(lambda: self._handle_load_pila_into_visual_editor(flow_dialog))
        
        # We'll implement a simplified version that loads and sets the flow on the dialog
        pilas_list = self.model.pila_repo.get_all_pilas()
        if not pilas_list: return
        dialog = LoadPilaDialog(pilas_list, self.view)
        if not dialog.exec() or dialog.get_selected_id() is None: return
        
        pila_id = dialog.get_selected_id()
        _, _, production_flow, _ = self.model.pila_repo.load_pila(pila_id)
        if production_flow:
            flow_dialog.set_production_flow(production_flow)


    def _handle_save_pila_from_visual_editor(self, flow_dialog):
        # Similar logic to _on_save_pila_clicked but taking flow from dialog
        production_flow = flow_dialog.get_production_flow()
        if not production_flow: return
        
        # Update app state so standard save dialog uses this flow
        self.app.last_production_flow = production_flow
        
        # Trigger standard save
        self._on_save_pila_clicked()

    def _handle_clear_visual_editor(self, flow_dialog):
        flow_dialog.clear_flow()
