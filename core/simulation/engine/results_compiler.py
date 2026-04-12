# core/simulation/engine/results_compiler.py
"""
Nombre del Módulo: core.simulation.engine.results_compiler

Descripción: Define protocolos o tipos principales: ``ResultsCompiler``. Compila los resultados de la simulación y genera el log de auditoría. Integración típica con: ``datetime``, ``core``.
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from core.services.calculation_audit import CalculationDecision, DecisionStatus

class ResultsCompiler:
    """
    Compila los resultados de la simulación y genera el log de auditoría.
    """
    def __init__(self, state: Any, time_calculator: Any, logger: Optional[Any] = None):
        self.state = state
        self.time_calculator = time_calculator
        self.logger = logger or logging.getLogger(__name__)

    def compilar_resultados(self, all_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crea una entrada de resultado por cada unidad individual completada."""
        resultados_individuales = []
        
        for evento in all_events:
            if evento.get('tipo_evento') != 'FIN_BLOQUE_TRABAJO':
                continue

            datos = evento.get('datos', {})
            tarea_id = datos.get('tarea_id')
            if not tarea_id or tarea_id not in self.state.lineas_temporales:
                continue

            linea_temporal = self.state.lineas_temporales[tarea_id]
            task_info = linea_temporal.task_data
            numero_unidad = datos.get('numero_unidad', datos.get('unidad', 1))
            inicio_bloque = datos.get('inicio')
            fin_bloque = evento.get('timestamp')

            if isinstance(inicio_bloque, str):
                try:
                    inicio_bloque = datetime.fromisoformat(inicio_bloque)
                except Exception as e:
                    self.logger.warning("Fallo al convertir inicio_bloque '%s' a datetime: %s", inicio_bloque, e)
                    inicio_bloque = None

            duracion_min = self.time_calculator.calculate_work_minutes_between(inicio_bloque, fin_bloque) if (inicio_bloque and fin_bloque) else 0.0

            trabajadores = datos.get('trabajadores', [])
            nombre_base_tarea = task_info.get('name', 'Tarea Desconocida')
            product_info = task_info.get('original_product_info', {})
            product_desc = product_info.get('desc', task_info.get('product_desc', 'N/A'))
            product_code = task_info.get('original_product_code', task_info.get('product_code', 'N/A'))
            identificador_lote = task_info.get('fabricacion_id', 'N/A')

            resultado_unidad = {
                'Tarea': nombre_base_tarea,
                'TareaDetalle': f"{nombre_base_tarea} - Unidad {numero_unidad}",
                'Departamento': task_info.get('department', 'N/A'),
                'Inicio': inicio_bloque,
                'Fin': fin_bloque,
                'Duracion (min)': round(duracion_min, 2),
                'Trabajador Asignado': ', '.join(trabajadores) if trabajadores else 'Sin asignar',
                'Lista Trabajadores': trabajadores,
                'nombre_maquina': datos.get('maquina_id') or task_info.get('machine_id') or 'N/A',
                'Codigo Producto': product_code,
                'Descripcion Producto': product_desc,
                'Numero Unidad': numero_unidad,
                'fabricacion_id': identificador_lote,
                'Index': self.state.tarea_id_a_indice.get(tarea_id),
                'Parent Index': task_info.get('previous_task_index'),
            }
            resultados_individuales.append(resultado_unidad)

        if not resultados_individuales: return []

        # Formateo de fechas y días laborables
        fecha_inicio_simulacion_valida = [r['Inicio'] for r in resultados_individuales if r['Inicio']]
        fecha_inicio_simulacion = min(fecha_inicio_simulacion_valida).date() if fecha_inicio_simulacion_valida else date.today()

        for result in resultados_individuales:
            dia_inicio_num = (result['Inicio'].date() - fecha_inicio_simulacion).days + 1 if result['Inicio'] else 0
            dia_fin_num = (result['Fin'].date() - fecha_inicio_simulacion).days + 1 if result['Fin'] else 0
            inicio_hora_str = result['Inicio'].strftime('%H:%M') if result['Inicio'] else 'N/A'
            fin_hora_str = result['Fin'].strftime('%H:%M') if result['Fin'] else 'N/A'

            result['Inicio Formateado'] = f"Día {dia_inicio_num} - {inicio_hora_str}"
            result['Fin Formateado'] = f"Día {dia_fin_num} - {fin_hora_str}"

            dias_laborables = 0
            if result['Inicio'] and result['Fin']:
                try:
                    dias_laborables = self.time_calculator.count_workdays(result['Inicio'], result['Fin'])
                except Exception as e:
                    self.logger.warning("Error al calcular días laborables para la tarea '%s': %s", result.get('Tarea'), e, exc_info=True)
            result['Dias Laborables'] = dias_laborables if dias_laborables is not None else 0

        self.logger.info(f"📊 Resultados compilados: {len(resultados_individuales)} unidades.")
        return resultados_individuales

    def compilar_audit_log(self, all_events: List[Dict[str, Any]]) -> List[CalculationDecision]:
        """Convierte los eventos en un audit log legible."""
        audit_log = []
        for evento in all_events:
            tipo_evento = evento.get('tipo_evento', 'DESCONOCIDO')
            datos = evento.get('datos', {})
            timestamp = evento.get('timestamp')
            tarea_id = datos.get('tarea_id')
            
            task_info = {'name': 'Tarea Desconocida', 'product_code': 'N/A', 'product_desc': 'N/A'}
            if tarea_id and tarea_id in self.state.lineas_temporales:
                orig = self.state.lineas_temporales[tarea_id].task_data
                task_info = {
                    'name': orig.get('name', 'N/A'),
                    'product_code': orig.get('original_product_code', 'N/A'),
                    'product_desc': orig.get('original_product_info', {}).get('desc', 'N/A')
                }

            reason, user_friendly, icon, status = self._generar_descripcion(tipo_evento, datos, task_info)

            if timestamp is None:
                timestamp = datetime.now()

            decision = CalculationDecision(
                timestamp=timestamp,
                decision_type=tipo_evento,
                reason=reason,
                user_friendly_reason=user_friendly,
                task_name=task_info.get('name', 'N/A'),
                product_code=task_info.get('product_code', 'N/A'),
                product_desc=task_info.get('product_desc', 'N/A'),
                status=status,
                icon=icon
            )
            audit_log.append(decision)

        if hasattr(self.state, 'audit_log_interno') and self.state.audit_log_interno:
            audit_log.extend(self.state.audit_log_interno)

        audit_log.sort(key=lambda x: x.timestamp if hasattr(x, 'timestamp') else datetime.min)
        return audit_log

    def _generar_descripcion(self, tipo_evento: str, datos: Dict[str, Any], task_info: Dict[str, Any]) -> tuple[str, str, str, DecisionStatus]:
        """Genera descripciones específicas para cada tipo de evento."""
        task_name = task_info.get('name', 'Tarea')
        if tipo_evento == 'INICIO_UNIDAD':
            numero_unidad = datos.get('unidad', datos.get('numero_unidad', '?'))
            trabajadores = datos.get('trabajadores', [])
            desbloqueada_por = datos.get('desbloqueada_por')
            icon = "🔓" if desbloqueada_por else "▶️"
            reason = f"Iniciando unidad {numero_unidad} de '{task_name}'"
            if desbloqueada_por: reason += " (desbloqueada por dependencia)"
            user_friendly = f"Se inició la unidad {numero_unidad}"
            return reason, user_friendly, icon, DecisionStatus.POSITIVE

        elif tipo_evento == 'FIN_BLOQUE_TRABAJO':
            numero_unidad = datos.get('numero_unidad', datos.get('unidad', '?'))
            duracion = datos.get('duracion_calculada', 0)
            reason = f"Completada unidad {numero_unidad} de '{task_name}' en {duracion:.1f} min"
            user_friendly = f"Se finalizó la unidad {numero_unidad} en {duracion:.1f} min"
            return reason, user_friendly, "✅", DecisionStatus.POSITIVE

        elif tipo_evento == 'REASIGNACION_TRABAJADOR':
            return f"Reasignación: {datos.get('trabajador_id')}", "Optimización de producción", "🔄", DecisionStatus.NEUTRAL

        elif tipo_evento == 'ESPERA_RECURSOS':
            tiempo = datos.get('tiempo_espera_min', 0)
            status = DecisionStatus.WARNING if tiempo > 60 else DecisionStatus.NEUTRAL
            return f"'{task_name}' esperó {tiempo:.1f} min", f"Demora por recursos ({tiempo:.1f} min)", "⏳", status

        elif tipo_evento == 'VERIFICAR_DEPENDENCIA':
            tarea_esp = datos.get('tarea_esperada', 'Predecesora')
            return f"Verificando dependencia de '{tarea_esp}'", "Verificando dependencias", "🔍", DecisionStatus.NEUTRAL

        return f"Evento '{tipo_evento}'", "Evento procesado", "⚙️", DecisionStatus.NEUTRAL
