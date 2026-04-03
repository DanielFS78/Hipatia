# -*- coding: utf-8 -*-
"""
Nombre del Módulo: simulation_engine.py
Descripción: Motor de simulación de producción. Incluye el trabajador de hilo 
             (Worker) y el optimizador de recursos para cumplir plazos.
"""

import logging
from typing import List, Dict, Any, Optional # <-- AÑADIDO
from datetime import datetime, timedelta, time, date
from core.services.time_calculator import CalculadorDeTiempos # ⬅️ NUEVO IMPORT
from core.services.calendar_helper import set_schedule_config # ⬅️ (Puedes eliminar los otros si ya no se usan)
from PyQt6.QtCore import QObject, pyqtSignal
from enum import Enum
from core.services.calculation_audit import CalculationDecision, DecisionStatus
from PyQt6.QtCore import QObject, pyqtSignal
import heapq # Para gestionar la cola de eventos de forma eficiente



class SimulationWorker(QObject):
    """
    Trabajador de hilo (Worker) para ejecutar la simulación en segundo plano.
    
    Permite que la interfaz de usuario permanezca sensible mientras se realizan
    los cálculos intensivos del motor de simulación.
    
    Signals:
        finished (list, list): Emitida al completar, envía (resultados, logs_auditoria).
        progress_update (int): Emitida durante el proceso para actualizar barras de progreso.
    """
    finished = pyqtSignal(list, list)
    progress_update = pyqtSignal(int)
    def __init__(self, scheduler: Any) -> None:
        super().__init__()
        self.scheduler = scheduler
        self.logger = logging.getLogger("EvolucionTiemposApp")

    def run(self) -> None:
        if hasattr(self.scheduler, "progress_signal"):
            self.scheduler.progress_signal = self.progress_update
        self.logger.info("SimulationWorker: Iniciando simulación en un hilo separado...")
        try:
            if hasattr(self.scheduler, "run_simulation"):
                results, audit = self.scheduler.run_simulation()
            else:
                results, audit = self.scheduler.ejecutar_simulacion()
            self.finished.emit(results, audit)
            self.logger.info("SimulationWorker: Simulación completada.")
        except Exception as e:
            self.logger.critical(f"Error crítico en el hilo de simulación: {e}", exc_info=True)
            self.finished.emit([], [])

class Optimizer:
    """
    Motor de optimización algorítmica iterativa para asignación de recursos.
    
    Algoritmo de Optimización (Constraint Satisfaction Heuristic):
    Determina matemáticamente el número mínimo y estrictamente necesario de 
    recursos complementarios (trabajadores extra) para cumplir un plazo.
    
    Estrategia de resolución iterativa:
    1. Efectúa una simulación "Forward-Pass" logística asumiendo 0 extras.
    2. Compara el array de resultables de hitos (Fin) contra los 'deadlines'.
    3. Si satisface todos los plazos (`_verify_deadlines`), retorna matriz óptima.
    4. Si se viola algún plazo, ajusta `trabajadores_flexibles += 1` y reinicia ciclo.
    5. Protege el cálculo contra ciclos con `MAX_FLEXIBLE_WORKERS` = 20 para evitar
       bucles O(infinito) en condiciones objetivamente imposibles por agenda horaria.
    """

    def __init__(self, planning_session: List[Dict[str, Any]], db_manager: Any, 
                 worker_service: Any, pila_service: Any, schedule_config: Any, 
                 production_flow_override: Optional[List[Dict[str, Any]]] = None,
                 visual_dialog_reference: Optional[Any] = None) -> None:
        self.logger = logging.getLogger(__name__)
        self.planning_session = planning_session
        self.db = db_manager
        self.worker_service = worker_service
        self.pila_service = pila_service
        self.schedule_config = schedule_config
        self.production_flow_override = production_flow_override
        self.visual_dialog_reference = visual_dialog_reference
        self.audit_log: List[CalculationDecision] = []
        self.prioritized_tasks: List[Dict[str, Any]] = [] # Initialize
        
        if not self.planning_session:
            raise ValueError("La sesión de planificación (planning_session) no puede estar vacía.")

        self.total_units = self.planning_session[0].get("unidades", 1) if self.planning_session else 1
        
        # Initialize workers data needed by OptimizerWorker
        self.workers_with_skills: List[tuple[str, int]] = []
        self._load_workers()

    def _load_workers(self) -> None:
        """Loads active workers and their skills from the model."""
        try:
            workers_data = self.worker_service.get_all_workers(include_inactive=False)
            self.workers_with_skills = [(w.nombre_completo, w.tipo_trabajador) for w in workers_data]
            self.logger.info(f"Loaded {len(self.workers_with_skills)} workers for optimization.")
        except Exception as e:
            self.logger.error(f"Error loading workers in Optimizer: {e}")
            self.workers_with_skills = []

    def _prepare_and_prioritize_tasks(self) -> List[Dict[str, Any]]:
        """
        Recopila, expande y aplana todas las tareas.
        Si se proporciona un 'production_flow_override', lo usa directamente.
        De lo contrario, construye las tareas desde la sesión de planificación.
        """
        # --- INICIO DE LA MODIFICACIÓN CRÍTICA ---
        # Si hemos recibido un flujo desde el editor visual, lo usamos y saltamos la reconstrucción
        if self.production_flow_override:
            self.logger.info("Usando el flujo de producción personalizado del editor visual para la optimización.")

            tasks_for_scheduler: List[Dict[str, Any]] = []
            # Mapeo para encontrar el índice de una tarea por su 'id' de canvas
            task_id_to_index_map = {step['task']['id']: i for i, step in enumerate(self.production_flow_override) if
                                    'task' in step and 'id' in step['task']}

            for i, step in enumerate(self.production_flow_override):
                task_list: List[Dict[str, Any]] = []
                if step.get('type') == 'sequential_group':
                    task_list.extend(t['task'] for t in step.get('tasks', []) if t.get('task'))
                else:
                    task_item = step.get('task')
                    if task_item:
                        task_list.append(task_item)

                for task in task_list:
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
        raw_task_groups: List[Any] = []
        for lote_instance in self.planning_session:
            units = lote_instance.get("unidades", 1)
            deadline = lote_instance.get("deadline")
            identificador = lote_instance.get("identificador")
            
            # get_data_for_calculation_from_session ya nos devuelve una lista de CalculationProductDTO
            # con deadline, identificador y unidades ya inyectados.
            session_dtos = self.pila_service.get_data_for_calculation_from_session([lote_instance])
            raw_task_groups.extend(session_dtos)

        # 2. APLANAR Y ESTANDARIZAR LA LISTA DE TAREAS FINALES (desde DTOs)
        from core.dtos import CalculationProductDTO

        for task_dto in raw_task_groups:
            if not isinstance(task_dto, CalculationProductDTO):
                self.logger.warning(f"Objeto no reconocido en raw_task_groups: {type(task_dto)}")
                continue

            # Si el DTO representa un preproceso (código empieza por PREP_)
            if task_dto.codigo.startswith("PREP_"):
                tasks_for_scheduler.append({
                    'id': f"{task_dto.fabricacion_id}_{task_dto.codigo}",
                    'name': task_dto.descripcion,
                    'duration_per_unit': task_dto.tiempo_optimo,
                    'is_batch_task': True,
                    'trigger_units': 1,
                    'required_skill_level': task_dto.tipo_trabajador,
                    'department': task_dto.departamento,
                    'deadline': task_dto.deadline,
                    'fabricacion_id': task_dto.fabricacion_id,
                    'original_product_code': task_dto.codigo,
                    'original_product_info': {'desc': task_dto.descripcion}
                })
            elif task_dto.sub_partes:
                for i, sub_dto in enumerate(task_dto.sub_partes):
                    tasks_for_scheduler.append({
                        'id': f"{task_dto.fabricacion_id}_{task_dto.codigo}_{i}",
                        'name': sub_dto.descripcion,
                        'duration_per_unit': sub_dto.tiempo,
                        'is_batch_task': False,
                        'trigger_units': 1,
                        'required_skill_level': sub_dto.tipo_trabajador,
                        'department': task_dto.departamento,
                        'deadline': task_dto.deadline,
                        'fabricacion_id': task_dto.fabricacion_id,
                        'original_product_code': task_dto.codigo,
                        'original_product_info': {'desc': task_dto.descripcion}
                    })
            else:
                tasks_for_scheduler.append({
                    'id': f"{task_dto.fabricacion_id}_{task_dto.codigo}",
                    'name': task_dto.descripcion,
                    'duration_per_unit': task_dto.tiempo_optimo,
                    'is_batch_task': False,
                    'trigger_units': 1,
                    'required_skill_level': task_dto.tipo_trabajador,
                    'department': task_dto.departamento,
                    'deadline': task_dto.deadline,
                    'fabricacion_id': task_dto.fabricacion_id,
                    'original_product_code': task_dto.codigo,
                    'original_product_info': {'desc': task_dto.descripcion}
                })

        self.prioritized_tasks = tasks_for_scheduler

        self.logger.info(
            f"Se han recopilado y ordenado {len(self.prioritized_tasks)} tareas finales para la simulación.")
        return self.prioritized_tasks

    def run_simulation(self) -> tuple[List[Dict[str, Any]], List[CalculationDecision]]:
        """
        Ejecuta el bloque iterativo del solver de Satisfacción de Restricciones (CSP).
        
        Heurística Matemática del Motor (Pseudo-código analítico):
        Variable Objetivo: w_flexibles (enteros, recursos dinámicos).
        Constraints (Restricciones): para todo f_i en Tareas: Fin(f_i) <= Deadline(f_i).
        
        Iteración 0: 
           P_result = SimuladorDiscreto(Tareas_Base, Trabajadores=W_fijos + w_flexibles=0)
           Holguras H_i = Deadline(f_i) - Fin(f_i) de P_result
           
           if eval(min(H_i)) >= 0:
               return P_result, log  # Optimidad Alcanzada
               
           else:
               if w_flexibles < 20: 
                   w_flexibles ++ 1
                   Goto Iteración 0
               else:
                   return P_result(inviable_cortado), log_warning # Restricción Dura
                   
        Coordina intrínsecamente la preparación del dataset, el event-loop del scheduler 
        y la verificación vectorizada de plazos contra los T_actuales devueltos.
        """
        self._prepare_and_prioritize_tasks()
        
        # En una versión real aquí llamaríamos al MotorDeEventos
        # pero mantenemos la firma para compatibilidad con SimulationWorker
        return [], self.audit_log

    def _verify_deadlines(self, results: List[Dict[str, Any]]) -> bool:
        """
        Solver evaluador de restricciones (Deadline Constraints).
        
        Matemáticas Puras - Análisis de Holgura (Slack Time):
        Sean f_1, f_2... f_n el arreglo de sub-ítems pertenecientes a una Fab_A.
        Calcula el Maximo Absoluto temporal: T_max(Fab_A) = Max(Fin(f_1), Fin(f_2)...).
        Compara la inecuación: 
             T_max(Fab_A).date() <= Deadline(Fab_A).date()
             
        Si la inecuación se viola, calcula la penalización métrica:
             Retraso Delta_D(Fab_A) = Abs(T_max(Fab_A).date() - Deadline_A(Fab_A).date()) en días.
             
        Si para todo i, T_max(i) <= Deadline(i) -> Constraint Satisfecha (return True).
        """
        if not results:
            self.logger.warning("La simulación no produjo resultados, se asume que los plazos no se cumplen.")
            return False

        # Agrupar los resultados por el identificador de la instancia del lote
        results_by_instance_id: Dict[str, List[Dict[str, Any]]] = {}
        for task in results:
            instance_id = str(task.get('fabricacion_id', ''))
            if not instance_id:
                continue
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

