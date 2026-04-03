# core/simulation/engine/dependency_handler.py
"""
Lógica o utilidades del núcleo (`dependency_handler`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

import logging
from datetime import datetime
from typing import List, Any, Optional
from ..simulation_events import EventoInicioUnidad

class DependencyHandler:
    """
    Gestiona la validación y propagación de dependencias entre tareas.
    """
    def __init__(self, state: Any, logger: Optional[Any] = None):
        self.state = state
        self.logger = logger or logging.getLogger(__name__)

    def encontrar_tareas_dependientes(self, tarea_id: str) -> List[Any]:
        """Encuentra todas las tareas que dependen de la tarea especificada."""
        tareas_dependientes: List[Any] = []
        if tarea_id not in self.state.tarea_id_a_indice:
            self.logger.warning(f"No se puede encontrar el índice de '{tarea_id}' para verificar dependencias.")
            return tareas_dependientes
        
        indice_predecesora = self.state.tarea_id_a_indice[tarea_id]
        for linea_temporal in self.state.lineas_temporales.values():
            if linea_temporal.id == tarea_id:
                continue
            if linea_temporal.dependency_index == indice_predecesora:
                tareas_dependientes.append(linea_temporal)
                self.logger.debug(f"  🔗 '{linea_temporal.name}' depende de '{tarea_id}'")
        return tareas_dependientes

    def verificar_dependencias_cumplidas(self, 
                                        tarea_completada_id: str, 
                                        unidad_completada: int, 
                                        timestamp_actual: datetime, 
                                        runner: Any,
                                        eventos_ya_creados: List[Any] | None = None,
                                        visitados: set[str] | None = None) -> List[Any]:
        """
        Verifica si se desbloquean nuevas unidades tras completar una tarea.
        (Versión mejorada con propagación recursion).
        """
        if eventos_ya_creados is None: eventos_ya_creados = []
        if visitados is None: visitados = set()

        if tarea_completada_id in visitados: return []
        visitados.add(tarea_completada_id)

        eventos_generados: List[Any] = []
        tareas_dependientes = self.encontrar_tareas_dependientes(tarea_completada_id)

        if not tareas_dependientes: return eventos_generados

        linea_predecesora = self.state.lineas_temporales[tarea_completada_id]
        unidades_predecesor_completadas = linea_predecesora.unidades_finalizadas_total

        for tarea_dependiente in tareas_dependientes:
            indice_dependiente = self.state.tarea_id_a_indice.get(tarea_dependiente.id)
            if indice_dependiente is None: continue

            # LÓGICA PASSTHROUGH
            if tarea_dependiente.unidades_finalizadas_total >= tarea_dependiente.unidades_a_producir:
                self.logger.info(f"  ⏩ Propagando señal a través de '{tarea_dependiente.name}' ya completada.")
                eventos_propagados = self.verificar_dependencias_cumplidas(
                    tarea_completada_id=tarea_dependiente.id,
                    unidad_completada=tarea_dependiente.unidades_finalizadas_total,
                    timestamp_actual=timestamp_actual,
                    runner=runner,
                    eventos_ya_creados=eventos_ya_creados,
                    visitados=visitados
                )
                eventos_generados.extend(eventos_propagados)
                continue

            # Identificar unidad a despertar
            paso_flujo_dependiente = self.state.production_flow[indice_dependiente]
            min_predecessor_units = paso_flujo_dependiente.get('min_predecessor_units', 1)

            unidades_en_proceso_o_programadas = {inst['unidad_actual'] for inst in tarea_dependiente.instancias_activas}
            
            # Buscar en eventos futuros (runner)
            for _, _, ev in runner.state.eventos_futuros:
                if not ev.cancelado and ev.datos.get('tarea_id') == tarea_dependiente.id:
                    if ev.tipo_evento in ['INICIO_UNIDAD', 'FIN_BLOQUE_TRABAJO']:
                        unidades_en_proceso_o_programadas.add(ev.datos.get('unidad', ev.datos.get('numero_unidad')))

            # Buscar en eventos recién creados
            for ev in eventos_ya_creados + eventos_generados:
                if not ev.cancelado and ev.datos.get('tarea_id') == tarea_dependiente.id:
                    if ev.tipo_evento == 'INICIO_UNIDAD':
                        unidades_en_proceso_o_programadas.add(ev.datos.get('unidad'))

            unidad_a_iniciar = tarea_dependiente.unidades_finalizadas_total + 1
            while unidad_a_iniciar in unidades_en_proceso_o_programadas:
                unidad_a_iniciar += 1

            if unidad_a_iniciar > tarea_dependiente.unidades_a_producir:
                continue

            unidades_predecesor_requeridas = (unidad_a_iniciar - 1) * min_predecessor_units + min_predecessor_units

            if unidades_predecesor_completadas >= unidades_predecesor_requeridas:
                timestamp_inicio = timestamp_actual
                trabajadores = getattr(tarea_dependiente, 'trabajadores_asignados', [])
                
                if not trabajadores and not tarea_dependiente.machine_id:
                    self.logger.error(f"  ❌ Tarea '{tarea_dependiente.name}' sin recursos. No se puede iniciar.")
                    continue
                
                nuevo_id_instancia = tarea_dependiente.iniciar_instancia_inicial(
                    trabajadores, timestamp_inicio, numero_unidad=unidad_a_iniciar
                )

                evento_inicio = EventoInicioUnidad(
                    timestamp=timestamp_inicio,
                    datos={
                        'tarea_id': tarea_dependiente.id,
                        'unidad': unidad_a_iniciar,
                        'desbloqueada_por': tarea_completada_id,
                        'id_instancia': nuevo_id_instancia
                    }
                )
                self.logger.info(f"🚀 DESBLOQUEANDO: '{tarea_dependiente.name}' U{unidad_a_iniciar}")
                eventos_generados.append(evento_inicio)

        return eventos_generados
