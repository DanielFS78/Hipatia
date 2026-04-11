# core/simulation/engine/motor.py
"""
Nombre del Módulo: core.simulation.engine.motor

Descripción: Define protocolos o tipos principales: ``MotorDeEventos``. Orquestador principal del motor de simulación basado en eventos. Integración típica con: ``__future__``, ``heapq``, ``time``, ``os``, ``tempfile``, ``datetime``.
"""
from __future__ import annotations
import logging
import heapq
import time
import os
import tempfile
from datetime import datetime
from threading import Lock
from typing import List, Dict, Any, Optional, Sequence, cast

from .base import SimulationState
from .core_runner import CoreSimulationRunner
from .dependency_handler import DependencyHandler
from .results_compiler import ResultsCompiler

from core.services.calculation_audit import CalculationDecision

from ..resource_manager import GestorDeRecursos
from core.services.temporal_storage import RegistroTemporal
from ..timeline_task import LineaTemporalTarea
from ..simulation_events import EventoInicioUnidad

class MotorDeEventos:
    """
    Orquestador principal del motor de simulación basado en eventos.
    
    Esta clase es el "corazón" del sistema de cálculo de tiempos. Utiliza un 
    bucle de eventos (Event Loop) con una cola de prioridad (heapq) para 
    avanzar el tiempo virtual y procesar hitos de producción.
    
    Responsabilidades:
        - Gestionar el tiempo virtual de la simulación.
        - Coordinar el Gestor de Recursos (trabajadores y máquinas).
        - Manejar dependencias entre tareas (DependencyHandler).
        - Compilar resultados y auditorías (ResultsCompiler).
        - Ejecutar la lógica de eventos (CoreSimulationRunner).
    """
    def __init__(self, production_flow: List[Dict[str, Any]], all_workers_data: List[tuple[str, int]],
                 all_machines_data: Dict[str, Any], schedule_config: Any, start_date: datetime,
                 time_calculator: Any, checkpoint_path: str | None = None,
                 visual_dialog_reference: Optional[Any] = None) -> None:

        self.logger = logging.getLogger(__name__)
        self.lock = Lock()
        self.visual_dialog_reference = visual_dialog_reference
        self.calculador_tiempos = time_calculator

        # 1. Estado
        self.state = SimulationState(
            tiempo_actual=start_date,
            production_flow=production_flow
        )

        # 2. Componentes de Soporte
        self.gestor_recursos = GestorDeRecursos(self.calculador_tiempos)
        temp_db_path = os.path.join(
            tempfile.gettempdir(),
            f"temp_simulation_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.db"
        )
        self.registro_temporal = RegistroTemporal(db_path=temp_db_path)

        # 3. Módulos Especializados
        self.runner = CoreSimulationRunner(self.state, self.lock)
        self.dependency_handler = DependencyHandler(self.state, self.logger)
        self.results_compiler = ResultsCompiler(self.state, self.calculador_tiempos, self.logger)

        if checkpoint_path and os.path.exists(checkpoint_path):
            self._load_checkpoint(checkpoint_path)
            return

        self._inicializar_estado_inicial(all_workers_data, all_machines_data, schedule_config)

    def _inicializar_estado_inicial(self, all_workers_data: List[tuple[str, int]], 
                                   all_machines_data: Dict[str, Any], 
                                   schedule_config: Any) -> None:
        """Prepara las líneas temporales y recursos."""
        for worker_name, _ in all_workers_data:
            self.gestor_recursos.registrar_recurso(worker_name, es_trabajador=True)
        for machine_id in all_machines_data.keys():
            self.gestor_recursos.registrar_recurso(machine_id, es_trabajador=False)

        from dataclasses import is_dataclass, asdict

        for i, step in enumerate(self.state.production_flow):
            # 1. Obtener y normalizar datos de la tarea
            raw_task = step['task']
            if is_dataclass(raw_task):
                task_data = asdict(cast(Any, raw_task))
                # DTOs use 'tiempo_optimo', motor uses 'duration', 'duration_per_unit' or 'tiempo'
                if 'tiempo_optimo' in task_data:
                    task_data['duration'] = task_data['tiempo_optimo']
                    task_data['duration_per_unit'] = task_data['tiempo_optimo']
                # Mapear 'codigo' a 'id' if not present
                if 'codigo' in task_data and 'id' not in task_data:
                    task_data['id'] = task_data['codigo']
                # Se asegura el nombre
                if 'descripcion' in task_data and 'name' not in task_data:
                    task_data['name'] = task_data['descripcion']
            else:
                task_data = raw_task.copy()
                # Compatibilidad para dicts legacy que puedan tener 'tiempo' en lugar de 'duration'
                if 'tiempo' in task_data and 'duration' not in task_data:
                    task_data['duration'] = task_data['tiempo']

            task_data['trigger_units'] = step.get('trigger_units', 1)

            if step.get('start_date'):
                from datetime import datetime as dt
                if isinstance(step['start_date'], dt):
                    task_data['scheduled_start_date'] = step['start_date']
                else:
                    task_data['scheduled_start_date'] = dt.combine(step['start_date'], schedule_config.WORK_START_TIME)

            if step.get('previous_task_index') is not None:
                task_data['previous_task_index'] = step['previous_task_index']

            linea = LineaTemporalTarea(task_data, self.gestor_recursos, self.calculador_tiempos)
            
            # Extraer trabajadores
            workers_data = step.get('workers', [])
            nombres = []
            for w in workers_data:
                if isinstance(w, dict) and 'name' in w: nombres.append(w['name'])
                elif isinstance(w, str): nombres.append(w)
            
            linea.trabajadores_asignados = nombres
            self.state.lineas_temporales[linea.id] = linea
            self.state.indice_a_tarea_id[i] = linea.id
            self.state.tarea_id_a_indice[linea.id] = i

    def _generar_eventos_iniciales(self) -> None:
        """Identifica tareas raíz y genera sus eventos iniciales."""
        tareas_con_dep = {self.state.indice_a_tarea_id.get(i) for i, s in enumerate(self.state.production_flow) if s.get('previous_task_index') is not None}
        
        raices = []
        fechas = []
        for i, step in enumerate(self.state.production_flow):
            t_id = self.state.indice_a_tarea_id.get(i)
            if not t_id: continue
            tarea = self.state.lineas_temporales[t_id]
            if step.get('is_cycle_start'):
                if t_id not in tareas_con_dep:
                    raices.append(tarea)
                    f = tarea.scheduled_start_date or self.state.tiempo_actual
                    fechas.append(f)
                else:
                    self.logger.warning(f"⚠️ La tarea '{tarea.name}' está marcada como inicio de ciclo pero tiene dependencia estándar.")

        if fechas:
            self.state.tiempo_actual = min(fechas)

        eventos = []
        for tarea in raices:
            ts = max(self.state.tiempo_actual, tarea.scheduled_start_date) if tarea.scheduled_start_date else self.state.tiempo_actual
            if not self.runner.tiene_evento_futuro(tarea.id, 1):
                trabs = getattr(tarea, 'trabajadores_asignados', [])
                if not trabs: continue
                id_instancia = tarea.iniciar_instancia_inicial(trabs, ts, 1)
                eventos.append(EventoInicioUnidad(timestamp=ts, datos={'tarea_id': tarea.id, 'unidad': 1, 'iniciado_por_fecha': True, 'id_instancia': id_instancia}))
        
        self.runner.programar_eventos(eventos)

    def ejecutar_simulacion(self, checkpoint_interval: int = 5000) -> tuple[List[Dict[str, Any]], List[CalculationDecision]]:
        """Bucle principal de simulación."""
        try:
            self._generar_eventos_iniciales()
            iteracion = 0
            while self.state.eventos_futuros:
                iteracion += 1
                timestamp, _, evento = heapq.heappop(self.state.eventos_futuros)
                self.state.tiempo_actual = timestamp

                # Procesar evento (el motor se pasa a sí mismo como contexto)
                nuevos = evento.procesar(self)
                if nuevos:
                    self.runner.programar_eventos(nuevos)

                self.registro_temporal.guardar_evento(evento)

            # Finalización: consultar_eventos vacía el buffer a disco antes de leer
            all_events = self.registro_temporal.consultar_eventos()
            results = self.results_compiler.compilar_resultados(all_events)
            audit = self.results_compiler.compilar_audit_log(all_events)
            
            return results, audit

        finally:
            self.registro_temporal.cleanup()

    def _load_from_checkpoint(self, path: str) -> None:
        data = self.runner.load_checkpoint(path)
        self.state.tiempo_actual = data['tiempo_actual']
        self.state.eventos_futuros = data['eventos_futuros']
        self.state.event_counter = data['event_counter']
        self.state.lineas_temporales = data['lineas_temporales']
        self.gestor_recursos = data['gestor_recursos']

    # Proxies para compatibilidad de eventos
    def programar_eventos(self, eventos: Sequence[Any]) -> None: self.runner.programar_eventos(eventos)
    def cancelar_eventos(self, eventos: List[Any]) -> None: self.runner.cancelar_eventos(eventos)
    def _verificar_dependencias_cumplidas(self, *args: Any, **kwargs: Any) -> List[Any]:
        if 'runner' not in kwargs and len(args) < 4: # runner is 4th pos arg
            kwargs['runner'] = self.runner
        return self.dependency_handler.verificar_dependencias_cumplidas(*args, **kwargs)
    def _tiene_evento_futuro(self, *args: Any, **kwargs: Any) -> bool:
        return self.runner.tiene_evento_futuro(*args, **kwargs)
    
    def _load_checkpoint(self, path: str) -> None:
        self._load_from_checkpoint(path)
        

        
    def _encontrar_tareas_dependientes(self, tarea_id: int | str) -> List[int]:
        return self.dependency_handler.encontrar_tareas_dependientes(str(tarea_id))

    def _save_checkpoint(self, path: str) -> None:
        self.runner.save_checkpoint(self.gestor_recursos, path)

    def find_task_index_by_id(self, tarea_id: str) -> int | None:
        """Devuelve el índice de flujo para un `tarea_id` usando el mapeo interno del motor."""
        return self.state.tarea_id_a_indice.get(cast(int, tarea_id)) if isinstance(tarea_id, int) else self.state.tarea_id_a_indice.get(next((k for k in self.state.tarea_id_a_indice.keys() if str(k) == str(tarea_id)), -1))

    @property
    def tiempo_actual(self) -> datetime: return self.state.tiempo_actual
    @tiempo_actual.setter
    def tiempo_actual(self, val: datetime) -> None: self.state.tiempo_actual = val
    
    @property
    def audit_log_interno(self) -> List[Any]: return self.state.audit_log_interno
    @audit_log_interno.setter
    def audit_log_interno(self, val: List[Any]) -> None: self.state.audit_log_interno = val

    @property
    def lineas_temporales(self) -> Dict[int, LineaTemporalTarea]: return self.state.lineas_temporales
    @lineas_temporales.setter
    def lineas_temporales(self, val: Dict[int, LineaTemporalTarea]) -> None: self.state.lineas_temporales = val

    @property
    def event_counter(self) -> int: return self.state.event_counter
    @event_counter.setter
    def event_counter(self, val: int) -> None: self.state.event_counter = val
    
    @property
    def eventos_futuros(self) -> List[tuple[datetime, int, Any]]: return self.state.eventos_futuros
    @eventos_futuros.setter
    def eventos_futuros(self, val: List[tuple[datetime, int, Any]]) -> None: self.state.eventos_futuros = val

    @property
    def indice_a_tarea_id(self) -> Dict[int, int]: return self.state.indice_a_tarea_id
    @indice_a_tarea_id.setter
    def indice_a_tarea_id(self, val: Dict[int, int]) -> None: self.state.indice_a_tarea_id = val

    @property
    def tarea_id_a_indice(self) -> Dict[int, int]: return self.state.tarea_id_a_indice
    @tarea_id_a_indice.setter
    def tarea_id_a_indice(self, val: Dict[int, int]) -> None: self.state.tarea_id_a_indice = val

    @property
    def production_flow(self) -> List[Dict[str, Any]]: return self.state.production_flow
    @production_flow.setter
    def production_flow(self, val: List[Dict[str, Any]]) -> None: self.state.production_flow = val
