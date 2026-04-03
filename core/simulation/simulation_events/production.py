# core/simulation/events/production.py

"""
Lógica o utilidades del núcleo (`production`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
from .base import EventoDeSimulacion
from .worker import EventoReasignacionTrabajador

@dataclass
class EventoInicioUnidad(EventoDeSimulacion):
    """Evento que marca el inicio del trabajo en una unidad de una tarea."""
    tipo_evento: str = 'INICIO_UNIDAD'
    prioridad: int = 2

    def procesar(self, motor_eventos) -> List['EventoDeSimulacion']:
        """
        Planifica una unidad para una INSTANCIA específica.
        """
        tarea_id = self.datos.get('tarea_id')
        numero_unidad = self.datos.get('unidad')
        id_instancia = self.datos.get('id_instancia')
        
        motor_eventos.logger.info(
            f"🟦 [EventoInicioUnidad] Procesando tarea='{tarea_id}', U{numero_unidad}, "
            f"Instancia={id_instancia[:8] if id_instancia else 'N/A'}"
        )

        if not tarea_id or tarea_id not in motor_eventos.lineas_temporales:
            return []

        linea_temporal = motor_eventos.lineas_temporales[tarea_id]

        if not id_instancia:
            return []

        instancia = linea_temporal.obtener_instancia(id_instancia)
        if not instancia:
            return []

        if linea_temporal.unidades_finalizadas_total >= linea_temporal.unidades_a_producir:
            return []

        trabajadores_instancia = instancia['trabajadores']
        
        if not trabajadores_instancia and not linea_temporal.machine_id:
            return []

        recursos_necesarios = trabajadores_instancia.copy()
        if linea_temporal.machine_id:
            recursos_necesarios.append(linea_temporal.machine_id)

        inicio_propuesto = self.timestamp
        for recurso_id in recursos_necesarios:
            es_trabajador = recurso_id in motor_eventos.gestor_recursos.calendario_trabajadores
            disponibilidad_recurso = motor_eventos.gestor_recursos.encontrar_siguiente_momento_disponible(
                    recurso_id, inicio_propuesto, es_trabajador
                )
            if disponibilidad_recurso > inicio_propuesto:
                inicio_propuesto = disponibilidad_recurso

        inicio_real = inicio_propuesto
        tiempo_base = linea_temporal.duration_per_unit
        num_trabajadores = len(trabajadores_instancia)

        if linea_temporal.machine_id:
            duracion_esta_unidad = tiempo_base
        else:
            if num_trabajadores > 0:
                duracion_esta_unidad = tiempo_base / num_trabajadores
            else:
                duracion_esta_unidad = tiempo_base

        fin_real = motor_eventos.calculador_tiempos.add_work_minutes(inicio_real, duracion_esta_unidad)

        for recurso_id in recursos_necesarios:
            es_trabajador = recurso_id in motor_eventos.gestor_recursos.calendario_trabajadores
            motor_eventos.gestor_recursos.asignar_recurso(recurso_id, inicio_real, fin_real, tarea_id, es_trabajador)

        instancia['inicio_unidad'] = inicio_real

        motor_eventos.logger.info(
            f"▶️ Planificando [Instancia {id_instancia[:8]}] unidad {numero_unidad} de '{linea_temporal.name}' "
            f"de {inicio_real.strftime('%d/%m %H:%M')} a {fin_real.strftime('%d/%m %H:%M')}"
        )

        evento_fin = EventoFinUnidad(
            timestamp=fin_real,
            datos={
                'tarea_id': tarea_id,
                'numero_unidad': numero_unidad,
                'id_instancia': id_instancia,
                'inicio': inicio_real,
                'trabajadores': trabajadores_instancia.copy(),
                'maquina_id': linea_temporal.machine_id,
                'duracion_calculada': duracion_esta_unidad
            }
        )
        instancia['evento_fin_programado'] = evento_fin
        return [evento_fin]

@dataclass
class EventoFinUnidad(EventoDeSimulacion):
    """Evento que marca la finalización de una unidad, liberando recursos."""
    tipo_evento: str = 'FIN_BLOQUE_TRABAJO'
    prioridad: int = 1

    def procesar(self, motor_eventos) -> List['EventoDeSimulacion']:
        tarea_id = self.datos.get('tarea_id')
        numero_unidad_completada = self.datos.get('numero_unidad')
        id_instancia = self.datos.get('id_instancia')

        if not tarea_id or tarea_id not in motor_eventos.lineas_temporales:
            return []

        linea_temporal_actual = motor_eventos.lineas_temporales[tarea_id]
        if not id_instancia:
            return []

        linea_temporal_actual.historial_unidades.append(
            {'unidad': numero_unidad_completada, 'fin': self.timestamp, 'inicio': self.datos.get('inicio')}
        )

        instancia_actual = linea_temporal_actual.obtener_instancia(id_instancia)
        trabajadores_instancia = instancia_actual['trabajadores'].copy() if instancia_actual else []
        resultado = linea_temporal_actual.completar_unidad_instancia(id_instancia)
        tarea_completada = resultado['tarea_completada']
        trabajadores_liberados = resultado['trabajadores_liberados']

        eventos_nuevos = []

        indice_actual = motor_eventos.tarea_id_a_indice.get(tarea_id)
        units_per_cycle = 1
        next_cyclic_index = None
        se_completo_ciclo_matematico = False

        if indice_actual is not None and 0 <= indice_actual < len(motor_eventos.production_flow):
            step_config_actual = motor_eventos.production_flow[indice_actual]
            units_per_cycle = max(1, step_config_actual.get('units_per_cycle', 1))
            next_cyclic_index = step_config_actual.get('next_cyclic_task_index')
            se_completo_ciclo_matematico = (numero_unidad_completada % units_per_cycle == 0)

        final_reassignment_rule_applies = False
        if tarea_completada:
            if indice_actual is not None and 0 <= indice_actual < len(motor_eventos.production_flow):
                step_config = motor_eventos.production_flow[indice_actual]
                workers_config = step_config.get('workers', [])
                for worker_config in workers_config:
                    if isinstance(worker_config, dict) and worker_config.get('name') in trabajadores_instancia:
                        regla = worker_config.get('reassignment_rule')
                        if regla and regla.get('condition_type') == 'ON_FINISH':
                            final_reassignment_rule_applies = True
                            break

        if tarea_completada and final_reassignment_rule_applies:
            eventos_reasignacion_on_finish = self._verificar_reglas_reasignacion(
                motor_eventos, tarea_id, numero_unidad_completada,
                trabajadores_instancia, True
            )
            eventos_reasignacion_on_finish = [
                ev for ev in eventos_reasignacion_on_finish
                if ev.datos.get('motivo', '').find('ON_FINISH') != -1
            ]
            if eventos_reasignacion_on_finish:
                eventos_nuevos.extend(eventos_reasignacion_on_finish)
            else:
                eventos_nuevos.extend(self._registrar_inactividad_trabajadores(motor_eventos, linea_temporal_actual))

        elif tarea_completada and not final_reassignment_rule_applies:
            if next_cyclic_index is not None:
                eventos_nuevos.extend(self._manejar_ciclo(motor_eventos, next_cyclic_index, trabajadores_liberados, id_instancia))
            else:
                eventos_a_cancelar = linea_temporal_actual.eventos_futuros.copy()
                if eventos_a_cancelar:
                    if hasattr(motor_eventos, 'cancelar_eventos'):
                        motor_eventos.cancelar_eventos(eventos_a_cancelar)
                    linea_temporal_actual.eventos_futuros.clear()
                eventos_nuevos.extend(self._registrar_inactividad_trabajadores(motor_eventos, linea_temporal_actual))

        elif not tarea_completada:
            eventos_reasignacion_std = self._verificar_reglas_reasignacion(
                motor_eventos, tarea_id, numero_unidad_completada, trabajadores_instancia, False
            )
            eventos_reasignacion_std = [
                ev for ev in eventos_reasignacion_std
                if ev.datos.get('motivo', '').find('ON_FINISH') == -1
            ]

            if eventos_reasignacion_std:
                eventos_nuevos.extend(eventos_reasignacion_std)
            elif se_completo_ciclo_matematico and next_cyclic_index is not None:
                eventos_nuevos.extend(self._manejar_ciclo(motor_eventos, next_cyclic_index, trabajadores_liberados, id_instancia))
            else:
                eventos_nuevos.extend(self._continuar_tarea(motor_eventos, linea_temporal_actual, trabajadores_liberados, indice_actual))

        eventos_dependencias = motor_eventos._verificar_dependencias_cumplidas(
            tarea_completada_id=tarea_id,
            unidad_completada=linea_temporal_actual.unidades_finalizadas_total,
            timestamp_actual=self.timestamp,
            eventos_ya_creados=eventos_nuevos
        )
        if eventos_dependencias:
            eventos_nuevos.extend(eventos_dependencias)

        return eventos_nuevos

    def _manejar_ciclo(self, motor_eventos, next_cyclic_index, trabajadores_ciclicos, id_instancia_origen) -> List[EventoDeSimulacion]:
        next_tarea_id = motor_eventos.indice_a_tarea_id.get(next_cyclic_index)
        if not next_tarea_id: return []
        linea_temporal_siguiente = motor_eventos.lineas_temporales.get(next_tarea_id)
        if not linea_temporal_siguiente: return []
        
        unidad_a_programar = linea_temporal_siguiente.unidades_finalizadas_total + 1
        if unidad_a_programar > linea_temporal_siguiente.unidades_a_producir or motor_eventos._tiene_evento_futuro(next_tarea_id, unidad_a_programar):
            return []

        nuevo_id = linea_temporal_siguiente.iniciar_instancia_inicial(trabajadores_ciclicos, self.timestamp, unidad_a_programar)
        return [EventoInicioUnidad(timestamp=self.timestamp, datos={'tarea_id': next_tarea_id, 'unidad': unidad_a_programar, 'id_instancia': nuevo_id, 'activado_por_ciclo': True})]

    def _continuar_tarea(self, motor_eventos, linea_temporal, trabajadores, indice_actual) -> List[EventoDeSimulacion]:
        siguiente_unidad = linea_temporal.unidades_finalizadas_total + 1
        unidades_en_proceso = {inst['unidad_actual'] for inst in linea_temporal.instancias_activas}
        while siguiente_unidad in unidades_en_proceso and siguiente_unidad <= linea_temporal.unidades_a_producir:
            siguiente_unidad += 1

        if siguiente_unidad > linea_temporal.unidades_a_producir:
            return self._registrar_inactividad_trabajadores(motor_eventos, linea_temporal)

        puede_continuar = True
        if indice_actual is not None and 0 <= indice_actual < len(motor_eventos.production_flow):
            step_config = motor_eventos.production_flow[indice_actual]
            dependency_index = step_config.get('previous_task_index')
            if dependency_index is not None:
                min_pred_units = step_config.get('min_predecessor_units', 1)
                req_units = (siguiente_unidad - 1) * min_pred_units + min_pred_units
                pred_id = motor_eventos.indice_a_tarea_id.get(dependency_index)
                if pred_id:
                    pred_lt = motor_eventos.lineas_temporales.get(pred_id)
                    if pred_lt and pred_lt.unidades_finalizadas_total < req_units:
                        puede_continuar = False

        if puede_continuar:
            nuevo_id = linea_temporal.iniciar_instancia_inicial(trabajadores, self.timestamp, siguiente_unidad)
            return [EventoInicioUnidad(timestamp=self.timestamp, datos={'tarea_id': linea_temporal.id, 'unidad': siguiente_unidad, 'id_instancia': nuevo_id})]
        else:
            return self._registrar_inactividad_trabajadores(motor_eventos, linea_temporal)

    def _verificar_reglas_reasignacion(self, motor_eventos, tarea_id, unidades, trabajadores, completada) -> List[EventoDeSimulacion]:
        indices = motor_eventos.tarea_id_a_indice.get(tarea_id)
        if indices is None: return []
        step_config = motor_eventos.production_flow[indices]
        workers_config = step_config.get('workers', [])
        
        eventos: List[EventoDeSimulacion] = []
        for wc in workers_config:
            if not isinstance(wc, dict): continue
            name = wc.get('name')
            regla = wc.get('reassignment_rule')
            if not regla or name not in trabajadores: continue
            
            tipo = regla.get('condition_type')
            if (tipo == 'AFTER_UNITS' and unidades >= regla.get('condition_value', 0)) or (tipo == 'ON_FINISH' and completada):
                eventos.append(EventoReasignacionTrabajador(
                    timestamp=self.timestamp,
                    datos={'trabajador_id': name, 'tarea_origen': tarea_id, 'tarea_destino': regla.get('target_task_id'), 'mode': regla.get('mode', 'REPLACE'), 'motivo': f"Condición cumplida: {tipo}"}
                ))
        return eventos

    def _registrar_inactividad_trabajadores(self, motor_eventos, linea_temporal) -> List[EventoDeSimulacion]:
        from core.services.calculation_audit import CalculationDecision, DecisionStatus
        
        trabajadores_tarea = linea_temporal.trabajadores_asignados
        if not trabajadores_tarea: return []

        dependency_index = linea_temporal.dependency_index
        if dependency_index is None or dependency_index < 0: return []

        pred_id = motor_eventos.indice_a_tarea_id.get(dependency_index)
        if not pred_id: return []

        # Buscar próximo fin del predecesor
        proxima_fin = None
        for timestamp_futuro, _, evento_obj in sorted(motor_eventos.eventos_futuros):
            if timestamp_futuro <= self.timestamp: continue
            if getattr(evento_obj, 'tipo_evento', None) == 'FIN_BLOQUE_TRABAJO':
                if evento_obj.datos.get('tarea_id') == pred_id:
                    proxima_fin = timestamp_futuro
                    break
        
        if proxima_fin:
            espera = (proxima_fin - self.timestamp).total_seconds() / 60
            if espera > 5: # Umbral
                for t_id in trabajadores_tarea:
                    decision = CalculationDecision(
                        timestamp=self.timestamp, decision_type='TIEMPO_INACTIVO',
                        reason=f"Esperando a {pred_id}", user_friendly_reason="Inactividad por dependencia",
                        details={'trabajador': t_id, 'espera': espera}, status=DecisionStatus.WARNING
                    )
                    motor_eventos.audit_log_interno.append(decision)
        return []
