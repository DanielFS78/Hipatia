# =================================================================================
# simulation_engine.py
# VERSIÓN CON TIMESTAMPS CRONOLÓGICOS EN EL LOG DE AUDITORÍA
# =================================================================================

import logging
from datetime import datetime, timedelta, time, date
from time_calculator import CalculadorDeTiempos # ⬅️ NUEVO IMPORT
from calendar_helper import set_schedule_config # ⬅️ (Puedes eliminar los otros si ya no se usan)
from PyQt6.QtCore import QObject, pyqtSignal
from enum import Enum
from calculation_audit import CalculationDecision, DecisionStatus
from PyQt6.QtCore import QObject, pyqtSignal
import heapq # Para gestionar la cola de eventos de forma eficiente
class DecisionStatus(Enum):
    NEUTRAL = "NEUTRAL"
    POSITIVE = "POSITIVE"
    WARNING = "WARNING"


class SimulationWorker(QObject):
    finished = pyqtSignal(list, list)
    progress_update = pyqtSignal(int)
    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler
        self.logger = logging.getLogger("EvolucionTiemposApp")

    def run(self):
        self.scheduler.progress_signal = self.progress_update
        self.logger.info("SimulationWorker: Iniciando simulación en un hilo separado...")
        try:
            results, audit = self.scheduler.run_simulation()
            self.finished.emit(results, audit)
            self.logger.info("SimulationWorker: Simulación completada.")
        except Exception as e:
            self.logger.critical(f"Error crítico en el hilo de simulación: {e}", exc_info=True)
            self.finished.emit([], [])

class Optimizer:
    """
    Motor de optimización que determina el número mínimo de trabajadores
    flexibles necesarios para cumplir con los plazos de entrega.
    """

    def __init__(self, planning_session, model, schedule_config, production_flow_override=None,
                 visual_dialog_reference=None):
        self.logger = logging.getLogger(__name__)
        self.planning_session = planning_session
        self.model = model
        self.schedule_config = schedule_config
        self.production_flow_override = production_flow_override
        self.visual_dialog_reference = visual_dialog_reference
        self.audit_log = []
        if not self.planning_session:
            raise ValueError("La sesión de planificación (planning_session) no puede estar vacía.")

        self.total_units = self.planning_session[0].get("unidades", 1) if self.planning_session else 1

    def _prepare_and_prioritize_tasks(self):
        """
        Recopila, expande y aplana todas las tareas.
        Si se proporciona un 'production_flow_override', lo usa directamente.
        De lo contrario, construye las tareas desde la sesión de planificación.
        """
        # --- INICIO DE LA MODIFICACIÓN CRÍTICA ---
        # Si hemos recibido un flujo desde el editor visual, lo usamos y saltamos la reconstrucción
        if self.production_flow_override:
            self.logger.info("Usando el flujo de producción personalizado del editor visual para la optimización.")

            tasks_for_scheduler = []
            # Mapeo para encontrar el índice de una tarea por su 'id' de canvas
            task_id_to_index_map = {step['task']['id']: i for i, step in enumerate(self.production_flow_override) if
                                    'task' in step and 'id' in step['task']}

            for i, step in enumerate(self.production_flow_override):
                task_list = []
                if step.get('type') == 'sequential_group':
                    task_list.extend(t['task'] for t in step.get('tasks', []))
                else:
                    task_list.append(step.get('task'))

                for task in task_list:
                    if not task: continue

                    # CORRECCIÓN CLAVE: Copiamos la dependencia del 'step' a la 'task'
                    task['previous_task_index'] = step.get('previous_task_index')
                    tasks_for_scheduler.append(task)
            # La priorización por deadline sigue siendo importante
            # REEMPLAZA CON ESTA LÍNEA
            self.prioritized_tasks = tasks_for_scheduler
            self.logger.info(f"Se han priorizado {len(self.prioritized_tasks)} tareas del flujo personalizado.")
            return self.prioritized_tasks
        # --- FIN DE LA MODIFICACIÓN CRÍTICA ---

        # Si no hay override, se ejecuta la lógica original para construir el flujo desde la BD
        self.logger.info("Recopilando y priorizando tareas desde la Pila de Producción (base de datos)...")
        tasks_for_scheduler = []

        # 1. RECOPILAR TODOS LOS GRUPOS DE TAREAS (PRODUCTOS Y PREPROCESOS)
        raw_task_groups = []
        for lote_instance in self.planning_session:
            units = lote_instance.get("unidades", 1)
            deadline = lote_instance.get("deadline")
            identificador = lote_instance.get("identificador")
            pila_de_calculo = lote_instance.get("pila_de_calculo_directa")

            productos_a_procesar = []
            fabricaciones_a_procesar = []

            if pila_de_calculo:
                self.logger.info(f"Procesando tareas desde Pila guardada: {identificador}")
                productos_a_procesar.extend(pila_de_calculo.get("productos", {}).keys())
                fabricaciones_a_procesar.extend(
                    [int(fab_id) for fab_id in pila_de_calculo.get("fabricaciones", {})])
            elif lote_instance.get("lote_template_id"):
                lote_id = lote_instance["lote_template_id"]
                self.logger.info(f"Procesando tareas desde Plantilla de Lote ID: {lote_id}")
                lote_details = self.model.lote_repo.get_lote_details(lote_id)
                if lote_details:
                    productos_a_procesar.extend([p[0] for p in lote_details.get("productos", [])])
                    fabricaciones_a_procesar.extend([f[0] for f in lote_details.get("fabricaciones", [])])

            for prod_code in productos_a_procesar:
                product_data = self.model.get_data_for_calculation(prod_code)
                for task_group in product_data:
                    task_group.update(
                        {'units_for_this_instance': units, 'deadline': deadline, 'fabricacion_id': identificador})
                    raw_task_groups.append(task_group)

            for fab_id in fabricaciones_a_procesar:
                fab_products = self.model.preproceso_repo.get_products_for_fabricacion(fab_id)
                for prod_dto in fab_products:
                    prod_code = prod_dto.producto_codigo
                    product_data = self.model.get_data_for_calculation(prod_code)
                    for task_group in product_data:
                        task_group.update(
                            {'units_for_this_instance': units, 'deadline': deadline,
                             'fabricacion_id': identificador})
                        raw_task_groups.append(task_group)

                fab_details = self.model.preproceso_repo.get_fabricacion_by_id(fab_id)
                if fab_details and fab_details.get('preprocesos'):
                    for prep_id, prep_nombre, prep_desc, prep_tiempo in fab_details['preprocesos']:
                        raw_task_groups.append({
                            'is_preproceso': True,
                            'descripcion': f"[PREPROCESO] {prep_nombre}",
                            'tiempo': prep_tiempo,
                            'units_for_this_instance': units,
                            'deadline': deadline,
                            'fabricacion_id': identificador,
                            'departamento': 'Preparación',
                            'original_product_code': f"PREP_{prep_id}",
                            'original_product_info': {'desc': prep_desc}
                        })

        # 2. APLANAR Y ESTANDARIZAR LA LISTA DE TAREAS FINALES
        for task_group in raw_task_groups:
            def get_duration_per_unit(data, default_key='tiempo'):
                val = data.get('tiempo', data.get(default_key, '0.0'))
                try:
                    return float(str(val).replace(",", "."))
                except (ValueError, TypeError):
                    return 0.0

            if task_group.get('is_preproceso'):
                duration_per_unit = get_duration_per_unit(task_group)
                tasks_for_scheduler.append({
                    'id': f"{task_group['fabricacion_id']}_{task_group['original_product_code']}",
                    'name': task_group.get('descripcion', 'Preproceso sin nombre'),
                    'duration_per_unit': duration_per_unit,
                    'is_batch_task': True,
                    'trigger_units': 1,
                    'required_skill_level': 1,
                    'department': task_group.get('departamento'),
                    'deadline': task_group['deadline'],
                    'fabricacion_id': task_group['fabricacion_id'],
                    'original_product_code': task_group.get('original_product_code'),
                    'original_product_info': task_group.get('original_product_info')
                })
            elif task_group.get('sub_partes'):
                for i, sub_task in enumerate(task_group['sub_partes']):
                    duration_per_unit = get_duration_per_unit(sub_task)
                    tasks_for_scheduler.append({
                        'id': f"{task_group['fabricacion_id']}_{task_group.get('codigo', 'prod')}_{i}",
                        'name': sub_task.get('descripcion', 'Sub-tarea sin nombre'),
                        'duration_per_unit': duration_per_unit,
                        'is_batch_task': False,
                        'trigger_units': 1,
                        'required_skill_level': sub_task.get('tipo_trabajador', 1),
                        'department': task_group.get('departamento'),
                        'deadline': task_group['deadline'],
                        'fabricacion_id': task_group['fabricacion_id'],
                        'original_product_code': task_group.get('codigo'),
                        'original_product_info': {'desc': task_group.get('descripcion')}
                    })
            else:
                duration_per_unit = get_duration_per_unit(task_group, 'tiempo_optimo')
                tasks_for_scheduler.append({
                    'id': f"{task_group['fabricacion_id']}_{task_group.get('codigo', 'prod')}",
                    'name': task_group.get('descripcion', 'Producto sin nombre'),
                    'duration_per_unit': duration_per_unit,
                    'is_batch_task': False,
                    'trigger_units': 1,
                    'required_skill_level': task_group.get('tipo_trabajador', 1),
                    'department': task_group.get('departamento'),
                    'deadline': task_group['deadline'],
                    'fabricacion_id': task_group['fabricacion_id'],
                    'original_product_code': task_group.get('codigo'),
                    'original_product_info': {'desc': task_group.get('descripcion')}
                })

        self.prioritized_tasks = tasks_for_scheduler

        self.logger.info(
            f"Se han recopilado y ordenado {len(self.prioritized_tasks)} tareas finales para la simulación.")
        return self.prioritized_tasks

    def _verify_deadlines(self, results):
        """
        Verifica si todas las fabricaciones en los resultados cumplen sus plazos
        y registra un evento de auditoría si no es así.
        CORREGIDO: Maneja la estructura de datos de la sesión de planificación.
        """
        if not results:
            self.logger.warning("La simulación no produjo resultados, se asume que los plazos no se cumplen.")
            return False

        # Agrupar los resultados por el identificador de la instancia del lote
        results_by_instance_id = {}
        for task in results:
            instance_id = task.get('fabricacion_id')
            if instance_id not in results_by_instance_id:
                results_by_instance_id[instance_id] = []
            results_by_instance_id[instance_id].append(task)

        all_deadlines_met = True
        # Iterar sobre las instancias de lote definidas en la sesión de planificación
        for lote_instance in self.planning_session:
            instance_id = lote_instance["identificador"]
            deadline = lote_instance["deadline"]

            # Si hay resultados para esta instancia, encontrar la fecha de finalización más tardía
            if instance_id in results_by_instance_id:
                fab_end_time = max(task['Fin'] for task in results_by_instance_id[instance_id])

                if fab_end_time.date() > deadline:
                    all_deadlines_met = False
                    delay = (fab_end_time.date() - deadline).days
                    self.logger.warning(f"INCUMPLIMIENTO: Instancia '{instance_id}' finaliza con {delay} días de retraso.")

                    reason = f"El plazo final ({deadline.strftime('%d/%m/%Y')}) no se cumple. La producción finaliza el {fab_end_time.date().strftime('%d/%m/%Y')}."
                    self.audit_log.append(CalculationDecision(
                        timestamp=fab_end_time,
                        task_name=f"LOTE '{instance_id}'",
                        decision_type="PLAZO_INCUMPLIDO",
                        reason=reason, user_friendly_reason=f"Plazo incumplido por {delay} día(s).",
                        product_code=lote_instance.get('lote_codigo', 'N/A'),
                        product_desc=f"Identificador: {instance_id}",
                        details={"retraso_dias": delay}, status=DecisionStatus.WARNING, icon="🔴"
                    ))

        return all_deadlines_met

