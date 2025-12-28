# simulation_events.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List


# --- CLASE BASE REFACTORIZADA ---
# Se elimina 'order=True' y se deja que el motor ordene por el timestamp explícitamente.
@dataclass
class EventoDeSimulacion:
    """Clase base para todos los eventos de la simulación."""
    timestamp: datetime
    datos: dict = field(default_factory=dict)
    cancelado: bool = field(default=False)
    tipo_evento: str = field(init=False)
    prioridad: int = field(init=False)

    def procesar(self, motor_eventos) -> List['EventoDeSimulacion']:
        """Método que debe ser implementado por las subclases."""
        raise NotImplementedError


# --- SUBCLASES REFACTORIZADAS ---
# Ya no tienen __init__, usan el de la clase base y definen sus propios valores.

@dataclass
class EventoInicioUnidad(EventoDeSimulacion):
    """Evento que marca el inicio del trabajo en una unidad de una tarea."""
    tipo_evento: str = 'INICIO_UNIDAD'
    prioridad: int = 2

    def procesar(self, motor_eventos) -> List['EventoDeSimulacion']:
        """
        Planifica una unidad para una INSTANCIA específica, consultando la
        disponibilidad real de los recursos de ESA instancia.
        """
        # --- 1. Obtener datos del evento ---
        tarea_id = self.datos.get('tarea_id')
        numero_unidad = self.datos.get('unidad')
        id_instancia = self.datos.get('id_instancia')  # CRÍTICO: ID de la instancia
        es_paralela = self.datos.get('es_instancia_paralela', False)

        motor_eventos.logger.info(
            f"🟦 [EventoInicioUnidad] Procesando tarea='{tarea_id}', U{numero_unidad}, "
            f"Instancia={id_instancia[:8] if id_instancia else 'N/A'}"
        )

        if not tarea_id or tarea_id not in motor_eventos.lineas_temporales:
            motor_eventos.logger.warning(f"❌ EventoInicioUnidad: tarea {tarea_id} no encontrada.")
            return []

        linea_temporal = motor_eventos.lineas_temporales[tarea_id]

        # --- 2. Obtener o crear instancia ---
        if not id_instancia:
            motor_eventos.logger.error(
                f"❌ EventoInicioUnidad: No se proveyó id_instancia para '{linea_temporal.name}'.")
            return []

        instancia = linea_temporal.obtener_instancia(id_instancia)

        if not instancia:
            # Esto puede pasar si la tarea se canceló pero el evento ya estaba en cola
            motor_eventos.logger.warning(
                f"❌ EventoInicioUnidad: Instancia {id_instancia[:8]} no encontrada en '{linea_temporal.name}'. "
                f"Probablemente fue cancelada. Se ignora."
            )
            return []

        # --- 3. Verificar estado de la tarea ---
        # Usamos el contador global
        if linea_temporal.unidades_finalizadas_total >= linea_temporal.unidades_a_producir:
            motor_eventos.logger.debug(f"   Tarea '{linea_temporal.name}' ya completada globalmente. Ignorando evento.")
            return []

        trabajadores_instancia = instancia['trabajadores']
        # --- LOG 6 (Después de obtener trabajadores_instancia) ---
        motor_eventos.logger.critical(
            f"DEBUG INICIO_U: Instancia {id_instancia[:8]} - Trabajadores: {trabajadores_instancia}")
        motor_eventos.logger.info(
            f"   Trabajadores en esta instancia ({id_instancia[:8]}): {trabajadores_instancia}"
        )

        if not trabajadores_instancia:
            motor_eventos.logger.error(
                f"⚠️ Instancia {id_instancia[:8]} en '{linea_temporal.name}' no tiene trabajadores. No se puede planificar.")
            return []

        # --- 4. Calcular disponibilidad de recursos de la instancia ---
        recursos_necesarios = trabajadores_instancia.copy()
        if linea_temporal.machine_id:
            recursos_necesarios.append(linea_temporal.machine_id)

        motor_eventos.logger.debug(f"   Recursos necesarios para instancia: {recursos_necesarios}")

        inicio_propuesto = self.timestamp
        motor_eventos.logger.debug(f"   Inicio propuesto inicial: {inicio_propuesto}")

        for recurso_id in recursos_necesarios:
            es_trabajador = recurso_id in motor_eventos.gestor_recursos.calendario_trabajadores
            motor_eventos.logger.debug(f"   Consultando disponibilidad de '{recurso_id}' (trabajador={es_trabajador})")
            try:
                disponibilidad_recurso = motor_eventos.gestor_recursos.encontrar_siguiente_momento_disponible(
                    recurso_id, inicio_propuesto, es_trabajador
                )
                motor_eventos.logger.debug(f"   → Disponible desde: {disponibilidad_recurso}")

                if disponibilidad_recurso > inicio_propuesto:
                    inicio_propuesto = disponibilidad_recurso
            except Exception as e:
                motor_eventos.logger.critical(f"❌ ERROR al consultar disponibilidad de '{recurso_id}': {e}",
                                              exc_info=True)
                return []

        # 1. Asigna el valor a inicio_real PRIMERO
        inicio_real = inicio_propuesto
        # 2. AHORA usa inicio_real en el log
        motor_eventos.logger.critical(
            f"DEBUG INICIO_U: Instancia {id_instancia[:8]} - Inicio real calculado: {inicio_real.strftime('%d/%m %H:%M')}")

        # --- 5. Calcular duración y fin ---
        # Mantenemos tu lógica de 'duration_per_unit'
        # El plan (fuente 167) sugiere dividir por num_trabajadores si no hay máquina.
        # Si 'duration_per_unit' ya es el tiempo final (independiente de trabajadores), esta lógica es correcta.
        # Si 'duration_per_unit' es el "esfuerzo total" y debe dividirse, habría que cambiarlo.
        # Por ahora, mantengo tu implementación:

        tiempo_base = linea_temporal.duration_per_unit
        num_trabajadores = len(trabajadores_instancia)

        if linea_temporal.machine_id:
            # Si hay máquina, tu lógica actual usa duration_per_unit directamente
            duracion_esta_unidad = tiempo_base
        else:
            # Si no hay máquina, el plan sugiere dividir por trabajadores.
            # TU LÓGICA ACTUAL: usa tiempo_base directo.
            # LÓGICA DEL PLAN: duracion_esta_unidad = tiempo_base / num_trabajadores
            # ADOPTAMOS LA LÓGICA DEL PLAN (si esto es incorrecto, avísame):
            if num_trabajadores > 0:
                duracion_esta_unidad = tiempo_base / num_trabajadores
            else:
                duracion_esta_unidad = tiempo_base  # Fallback
                # --- LOG 8 (Después de calcular duracion_esta_unidad) ---
        motor_eventos.logger.critical(
            f"DEBUG INICIO_U: Instancia {id_instancia[:8]} - Duración unidad calculada: {duracion_esta_unidad:.2f} min")
        motor_eventos.logger.debug(
            f"   Duración base: {tiempo_base} min / {num_trabajadores} trabajadores = {duracion_esta_unidad} min")

        try:
            fin_real = motor_eventos.calculador_tiempos.add_work_minutes(inicio_real, duracion_esta_unidad)
            motor_eventos.logger.debug(f"   Fin calculado: {fin_real}")
        except Exception as e:
            motor_eventos.logger.critical(f"❌ ERROR al calcular fin de tarea: {e}", exc_info=True)
            return []

        # --- 6. Asignar recursos y actualizar instancia ---
        motor_eventos.logger.debug(f"   Asignando recursos...")
        for recurso_id in recursos_necesarios:
            es_trabajador = recurso_id in motor_eventos.gestor_recursos.calendario_trabajadores
            try:
                motor_eventos.gestor_recursos.asignar_recurso(recurso_id, inicio_real, fin_real, tarea_id,
                                                              es_trabajador)
            except Exception as e:
                motor_eventos.logger.critical(f"❌ ERROR al asignar recurso '{recurso_id}': {e}", exc_info=True)
                return []

        # Actualizar la instancia en la línea temporal
        instancia['inicio_unidad'] = inicio_real

        motor_eventos.logger.info(
            f"▶️ Planificando [Instancia {id_instancia[:8]}] unidad {numero_unidad} de '{linea_temporal.name}' "
            f"de {inicio_real.strftime('%d/%m %H:%M')} a {fin_real.strftime('%d/%m %H:%M')}"
        )

        # --- 7. Generar EventoFinUnidad ---
        motor_eventos.logger.debug(f"   Creando EventoFinUnidad...")
        try:
            evento_fin = EventoFinUnidad(
                timestamp=fin_real,
                datos={
                    'tarea_id': tarea_id,
                    'numero_unidad': numero_unidad,
                    'id_instancia': id_instancia,  # CRÍTICO: Pasar la instancia
                    'inicio': inicio_real,
                    'trabajadores': trabajadores_instancia.copy(),  # Solo trabajadores de la instancia
                    'maquina_id': linea_temporal.machine_id,
                    'duracion_calculada': duracion_esta_unidad
                }
            )

            # Guardar referencia al evento de fin en la instancia
            instancia['evento_fin_programado'] = evento_fin

            motor_eventos.logger.info(f"✅ EventoFinUnidad creado para U{numero_unidad} [Instancia {id_instancia[:8]}]")
            return [evento_fin]

        except Exception as e:
            motor_eventos.logger.critical(f"❌ ERROR CRÍTICO al crear EventoFinUnidad: {e}", exc_info=True)
            return []

@dataclass
class EventoFinUnidad(EventoDeSimulacion):
    """Evento que marca la finalización de una unidad, liberando recursos."""
    tipo_evento: str = 'FIN_BLOQUE_TRABAJO'
    prioridad: int = 1

    # PEGA ESTE MÉTODO COMPLETO DENTRO DE LA CLASE EventoFinUnidad EN simulation_events.py
    # (Reemplaza el método procesar existente)

    def procesar(self, motor_eventos) -> List['EventoDeSimulacion']:
        """
        Procesa la finalización de una unidad de una INSTANCIA específica.
        Maneja la lógica de continuación de la instancia, finalización de tarea,
        ciclos y dependencias con una CADENA DE PRIORIDAD ESTRICTA.
        """
        # --- 1. Obtener datos del evento ---
        tarea_id = self.datos.get('tarea_id')
        numero_unidad_completada = self.datos.get('numero_unidad')
        id_instancia = self.datos.get('id_instancia')  # CRÍTICO: Qué instancia terminó

        if not tarea_id or tarea_id not in motor_eventos.lineas_temporales:
            motor_eventos.logger.warning(f"❌ EventoFinUnidad: tarea '{tarea_id}' no encontrada.")
            return []

        linea_temporal_actual = motor_eventos.lineas_temporales[tarea_id]

        if not id_instancia:
            motor_eventos.logger.error(
                f"❌ EventoFinUnidad: No se proveyó id_instancia para '{linea_temporal_actual.name}'. Se ignora.")
            return []

        motor_eventos.logger.info(
            f"\n{'=' * 70}\n"
            f"🏁 FIN UNIDAD: '{linea_temporal_actual.name}' U{numero_unidad_completada} "
            f"[Instancia {id_instancia[:8]}]\n"
            f"   Hora: {self.timestamp.strftime('%d/%m %H:%M')}"
        )

        # --- 2. Actualizar estado en LineaTemporal ---
        # (Asumimos que 'completar_unidad_instancia' ha sido refactorizado como te indiqué:
        # ahora solo incrementa el contador global y ELIMINA la instancia,
        # devolviendo los trabajadores que contenía)

        linea_temporal_actual.historial_unidades.append(
            {'unidad': numero_unidad_completada, 'fin': self.timestamp, 'inicio': self.datos.get('inicio')}
        )

        # Obtenemos los trabajadores de la instancia ANTES de que 'completar...' la elimine
        instancia_actual = linea_temporal_actual.obtener_instancia(id_instancia)
        trabajadores_instancia = instancia_actual['trabajadores'].copy() if instancia_actual else []

        # Este método (refactorizado) actualiza contadores y ELIMINA la instancia
        resultado = linea_temporal_actual.completar_unidad_instancia(id_instancia)

        # Ahora, 'instancia_completada' SIEMPRE será True (si la instancia existía)
        tarea_completada = resultado['tarea_completada']
        trabajadores_liberados = resultado['trabajadores_liberados']

        motor_eventos.logger.info(
            f"   Estado post-completar: Tarea_Completa={tarea_completada}, "
            f"Trabajadores liberados: {trabajadores_liberados}"
        )

        # Inicializar lista de eventos
        eventos_nuevos = []

        # --- 3. Obtener configuración de Reglas (Reasignación y Ciclos) ---

        # **OBTENER CONFIGURACIÓN DE CICLOS** (Prioridad 3)
        indice_actual = motor_eventos.tarea_id_a_indice.get(tarea_id)
        units_per_cycle = 1
        next_cyclic_index = None
        se_completo_ciclo_matematico = False  # Renombrada para claridad

        if indice_actual is not None and 0 <= indice_actual < len(motor_eventos.production_flow):
            step_config_actual = motor_eventos.production_flow[indice_actual]
            units_per_cycle = max(1, step_config_actual.get('units_per_cycle', 1))
            next_cyclic_index = step_config_actual.get('next_cyclic_task_index')
            se_completo_ciclo_matematico = (numero_unidad_completada % units_per_cycle == 0)

        # --- Definir final_reassignment_rule_applies ---
        final_reassignment_rule_applies = False
        if tarea_completada:  # Solo tiene sentido chequear si la tarea está completada
            indice_actual = motor_eventos.tarea_id_a_indice.get(tarea_id)
            if indice_actual is not None and 0 <= indice_actual < len(motor_eventos.production_flow):
                step_config = motor_eventos.production_flow[indice_actual]
                workers_config = step_config.get('workers', [])
                for worker_config in workers_config:
                    # Comprobar si es un dict y si el trabajador estaba en la instancia que acaba de terminar
                    if isinstance(worker_config, dict) and worker_config.get('name') in trabajadores_instancia:
                        regla = worker_config.get('reassignment_rule')
                        # Comprobar si existe la regla y es del tipo ON_FINISH
                        if regla and regla.get('condition_type') == 'ON_FINISH':
                            final_reassignment_rule_applies = True
                            motor_eventos.logger.debug(
                                f"   ℹ️ Detectada regla ON_FINISH aplicable para worker '{worker_config.get('name')}' en esta tarea completada.")
                            break  # Encontramos una, no necesitamos buscar más
        # --- FIN: Definir final_reassignment_rule_applies ---

        motor_eventos.logger.debug(
            f"📋 Configuración de reglas:\n"
            f"   • ¿Regla ON_FINISH final aplica?: {final_reassignment_rule_applies}\n"
            f"   • ¿Ciclo matemático completado?: {se_completo_ciclo_matematico}\n"
            f"   • ¿Hay tarea cíclica?: {next_cyclic_index is not None}"
        )

        # ============================================================================
        # 👑 INICIO DE LA LÓGICA DE DECISIÓN PRIORIZADA (CORREGIDA) 👑
        # ============================================================================

        # ----------------------------------------------------------------------------
        # PRIORIDAD 1: ¿Se activa AHORA una regla ON_FINISH aplicable?
        # (Ocurre si tarea_completada=True Y esta es la tarea con la regla ON_FINISH)
        # ----------------------------------------------------------------------------
        if tarea_completada and final_reassignment_rule_applies:
            motor_eventos.logger.info(
                f"🎯 PRIORIDAD 1: REASIGNACIÓN ON_FINISH desde tarea completada '{linea_temporal_actual.name}'.")
            # Es importante llamar a _verificar_reglas_reasignacion para generar el evento
            eventos_reasignacion_on_finish = self._verificar_reglas_reasignacion(
                motor_eventos, tarea_id, numero_unidad_completada,
                trabajadores_instancia, True  # tarea_completada es True
            )
            # Filtrar para quedarnos solo con las reglas ON_FINISH
            eventos_reasignacion_on_finish = [
                ev for ev in eventos_reasignacion_on_finish
                if ev.datos.get('motivo', '').find('ON_FINISH') != -1
            ]
            if eventos_reasignacion_on_finish:
                eventos_nuevos.extend(eventos_reasignacion_on_finish)
            else:
                # Si por alguna razón no se generó evento (ej. target_task_id es None), el trabajador queda libre
                motor_eventos.logger.warning(
                    f"  ⚠️ Regla ON_FINISH detectada pero no generó evento. Trabajador(es) {trabajadores_liberados} quedan libres.")
                eventos_nuevos.extend(self._registrar_inactividad_trabajadores(motor_eventos, linea_temporal_actual))

        # ----------------------------------------------------------------------------
        # PRIORIDAD 2: ¿La TAREA está COMPLETA pero NO era la de la regla ON_FINISH final?
        # ----------------------------------------------------------------------------
        elif tarea_completada and not final_reassignment_rule_applies:
            # ANTES de liberar al trabajador, VERIFICAR si había un ciclo pendiente
            if next_cyclic_index is not None:
                motor_eventos.logger.info(
                    f"  ⚠️ Tarea '{linea_temporal_actual.name}' completada, pero hay ciclo pendiente hacia índice {next_cyclic_index}. Siguiendo ciclo.")

                # --- INICIO LÓGICA DE CICLO (COPIADA) ---
                trabajadores_ciclicos = trabajadores_liberados.copy()
                motor_eventos.logger.debug(f"  📦 Trabajadores a migrar: {trabajadores_ciclicos}")
                if not (0 <= next_cyclic_index < len(motor_eventos.production_flow)):
                    motor_eventos.logger.error(f"  ❌ ERROR: Índice cíclico {next_cyclic_index} fuera de rango")
                    return eventos_nuevos
                next_tarea_id = motor_eventos.indice_a_tarea_id.get(next_cyclic_index)
                if not next_tarea_id:
                    motor_eventos.logger.error(
                        f"  ❌ ERROR: No se encontró tarea_id para índice cíclico {next_cyclic_index}")
                    return eventos_nuevos
                linea_temporal_siguiente = motor_eventos.lineas_temporales.get(next_tarea_id)
                if not linea_temporal_siguiente:
                    motor_eventos.logger.error(
                        f"  ❌ ERROR: No se encontró LineaTemporal para tarea_id '{next_tarea_id}'")
                    return eventos_nuevos
                unidad_a_programar_en_ciclo = linea_temporal_siguiente.unidades_finalizadas_total + 1
                motor_eventos.logger.debug(
                    f"  🎯 Tarea destino del ciclo: '{linea_temporal_siguiente.name}'\n"
                    f"     • Próxima unidad: {unidad_a_programar_en_ciclo}"
                )
                if unidad_a_programar_en_ciclo > linea_temporal_siguiente.unidades_a_producir:
                    motor_eventos.logger.info(
                        f"  ⭐ CICLO COMPLETO: Tarea '{linea_temporal_siguiente.name}' "
                        f"ya completó todas sus unidades. "
                        f"Trabajadores {trabajadores_ciclicos} quedan libres."
                    )
                elif motor_eventos._tiene_evento_futuro(next_tarea_id, unidad_a_programar_en_ciclo):
                    motor_eventos.logger.warning(
                        f"  ⚠️ SALTO CÍCLICO OMITIDO: Ya existe un evento programado para "
                        f"'{linea_temporal_siguiente.name}' U{unidad_a_programar_en_ciclo}. "
                        f"Trabajadores {trabajadores_ciclicos} quedan libres."
                    )
                else:
                    motor_eventos.logger.info(
                        f"  🔄 MIGRANDO TRABAJADORES AL CICLO:\n"
                        f"     • Hacia: '{linea_temporal_siguiente.name}' (U{unidad_a_programar_en_ciclo})\n"
                        f"     • Trabajadores: {trabajadores_ciclicos}"
                    )
                    try:
                        nuevo_id_instancia = linea_temporal_siguiente.iniciar_instancia_inicial(
                            trabajadores=trabajadores_ciclicos,
                            fecha_inicio=self.timestamp,
                            numero_unidad = unidad_a_programar_en_ciclo
                        )
                        motor_eventos.logger.info(f"     • Instancia nueva: {nuevo_id_instancia[:8]}")
                        evento_ciclico = EventoInicioUnidad(
                            timestamp=self.timestamp,
                            datos={
                                'tarea_id': next_tarea_id,
                                'unidad': unidad_a_programar_en_ciclo,
                                'id_instancia': nuevo_id_instancia,
                                'activado_por_ciclo': True,
                                'desde_tarea': tarea_id,
                                'instancia_origen': id_instancia,
                                'trabajadores_migrados': trabajadores_ciclicos
                            }
                        )
                        eventos_nuevos.append(evento_ciclico)
                        if hasattr(motor_eventos, 'audit_log_interno'):
                            from calculation_audit import CalculationDecision, DecisionStatus
                            decision = CalculationDecision(
                                timestamp=self.timestamp, decision_type='MIGRACION_CICLICA',
                                reason=f"Ciclo completado en '{linea_temporal_actual.name}', migrando trabajadores a '{linea_temporal_siguiente.name}'",
                                user_friendly_reason=f"Trabajadores retornaron al inicio del ciclo",
                                details={'tarea_origen': linea_temporal_actual.name,
                                         'tarea_destino': linea_temporal_siguiente.name,
                                         'trabajadores': trabajadores_ciclicos,
                                         'instancia_nueva': nuevo_id_instancia[:8]},
                                status=DecisionStatus.POSITIVE, icon="🔄"
                            )
                            motor_eventos.audit_log_interno.append(decision)
                    except Exception as e:
                        motor_eventos.logger.error(
                            f"  ❌ ERROR CRÍTICO al crear instancia en tarea destino: {e}",
                            exc_info=True
                        )
                        return eventos_nuevos
                # --- FIN LÓGICA DE CICLO (COPIADA) ---

            else:
                # SI NO había ciclo, AHORA sí queda libre
                motor_eventos.logger.info(
                    f"🎉 PRIORIDAD 2: TAREA '{linea_temporal_actual.name}' COMPLETADA "
                    f"({linea_temporal_actual.unidades_finalizadas_total}/{linea_temporal_actual.unidades_a_producir}) "
                    f"- Worker(s) {trabajadores_liberados} libres."
                )

                # --- INICIO LÓGICA TAREA COMPLETADA (COPIADA) ---
                eventos_a_cancelar = linea_temporal_actual.eventos_futuros.copy()
                if eventos_a_cancelar:
                    motor_eventos.logger.info(
                        f"  ❌ Cancelando {len(eventos_a_cancelar)} eventos futuros pendientes.")
                    if hasattr(motor_eventos, 'cancelar_eventos'):
                        motor_eventos.cancelar_eventos(eventos_a_cancelar)
                    linea_temporal_actual.eventos_futuros.clear()
                eventos_nuevos.extend(self._registrar_inactividad_trabajadores(motor_eventos, linea_temporal_actual))
                # --- FIN LÓGICA TAREA COMPLETADA (COPIADA) ---

        # ----------------------------------------------------------------------------
        # PRIORIDAD 3: ¿Aplica una regla de REASIGNACIÓN ESTÁNDAR (AFTER_UNITS)?
        # ----------------------------------------------------------------------------
        elif not tarea_completada:  # Solo se ejecuta si la tarea NO está completa
            # Llamamos a verificar reglas, pero forzando tarea_completada=False
            # para que solo se activen las reglas tipo AFTER_UNITS
            eventos_reasignacion_std = self._verificar_reglas_reasignacion(
                motor_eventos,
                tarea_id,
                numero_unidad_completada,
                trabajadores_instancia,
                False  # Forzamos False para ignorar ON_FINISH
            )
            # Filtro extra de seguridad para ignorar reglas ON_FINISH
            eventos_reasignacion_std = [
                ev for ev in eventos_reasignacion_std
                if ev.datos.get('motivo', '').find('ON_FINISH') == -1
            ]

            if eventos_reasignacion_std:
                motor_eventos.logger.info(
                    f"  ↪️ PRIORIDAD 3: REASIGNACIÓN ESTÁNDAR (AFTER_UNITS). {len(eventos_reasignacion_std)} evento(s) generado(s)."
                )
                eventos_nuevos.extend(eventos_reasignacion_std)
                # La reasignación tiene prioridad sobre el ciclo y la continuación para estos trabajadores.

            # ----------------------------------------------------------------------------
            # PRIORIDAD 4: ¿Aplica CICLO? (Si TAREA NO completa Y NO hubo reasignación estándar)
            # ----------------------------------------------------------------------------
            elif se_completo_ciclo_matematico and next_cyclic_index is not None:
                motor_eventos.logger.info("  🔄 PRIORIDAD 4: CICLO. Iniciando migración cíclica...")

                # --- INICIO LÓGICA DE CICLO (COPIADA) ---
                trabajadores_ciclicos = trabajadores_liberados.copy()
                motor_eventos.logger.debug(f"  📦 Trabajadores a migrar: {trabajadores_ciclicos}")
                if not (0 <= next_cyclic_index < len(motor_eventos.production_flow)):
                    motor_eventos.logger.error(f"  ❌ ERROR: Índice cíclico {next_cyclic_index} fuera de rango")
                    return eventos_nuevos
                next_tarea_id = motor_eventos.indice_a_tarea_id.get(next_cyclic_index)
                if not next_tarea_id:
                    motor_eventos.logger.error(
                        f"  ❌ ERROR: No se encontró tarea_id para índice cíclico {next_cyclic_index}")
                    return eventos_nuevos
                linea_temporal_siguiente = motor_eventos.lineas_temporales.get(next_tarea_id)
                if not linea_temporal_siguiente:
                    motor_eventos.logger.error(
                        f"  ❌ ERROR: No se encontró LineaTemporal para tarea_id '{next_tarea_id}'")
                    return eventos_nuevos
                unidad_a_programar_en_ciclo = linea_temporal_siguiente.unidades_finalizadas_total + 1
                motor_eventos.logger.debug(
                    f"  🎯 Tarea destino del ciclo: '{linea_temporal_siguiente.name}'\n"
                    f"     • Próxima unidad: {unidad_a_programar_en_ciclo}"
                )
                if unidad_a_programar_en_ciclo > linea_temporal_siguiente.unidades_a_producir:
                    motor_eventos.logger.info(
                        f"  ⭐ CICLO COMPLETO: Tarea '{linea_temporal_siguiente.name}' "
                        f"ya completó todas sus unidades. "
                        f"Trabajadores {trabajadores_ciclicos} quedan libres."
                    )
                elif motor_eventos._tiene_evento_futuro(next_tarea_id, unidad_a_programar_en_ciclo):
                    motor_eventos.logger.warning(
                        f"  ⚠️ SALTO CÍCLICO OMITIDO: Ya existe un evento programado para "
                        f"'{linea_temporal_siguiente.name}' U{unidad_a_programar_en_ciclo}. "
                        f"Trabajadores {trabajadores_ciclicos} quedan libres."
                    )
                else:
                    motor_eventos.logger.info(
                        f"  🔄 MIGRANDO TRABAJADORES AL CICLO:\n"
                        f"     • Hacia: '{linea_temporal_siguiente.name}' (U{unidad_a_programar_en_ciclo})\n"
                        f"     • Trabajadores: {trabajadores_ciclicos}"
                    )
                    try:
                        nuevo_id_instancia = linea_temporal_siguiente.iniciar_instancia_inicial(
                            trabajadores=trabajadores_ciclicos,
                            fecha_inicio=self.timestamp,
                            numero_unidad=unidad_a_programar_en_ciclo
                        )
                        motor_eventos.logger.info(f"     • Instancia nueva: {nuevo_id_instancia[:8]}")
                        evento_ciclico = EventoInicioUnidad(
                            timestamp=self.timestamp,
                            datos={
                                'tarea_id': next_tarea_id,
                                'unidad': unidad_a_programar_en_ciclo,
                                'id_instancia': nuevo_id_instancia,
                                'activado_por_ciclo': True,
                                'desde_tarea': tarea_id,
                                'instancia_origen': id_instancia,
                                'trabajadores_migrados': trabajadores_ciclicos
                            }
                        )
                        eventos_nuevos.append(evento_ciclico)
                        if hasattr(motor_eventos, 'audit_log_interno'):
                            from calculation_audit import CalculationDecision, DecisionStatus
                            decision = CalculationDecision(
                                timestamp=self.timestamp, decision_type='MIGRACION_CICLICA',
                                reason=f"Ciclo completado en '{linea_temporal_actual.name}', migrando trabajadores a '{linea_temporal_siguiente.name}'",
                                user_friendly_reason=f"Trabajadores retornaron al inicio del ciclo",
                                details={'tarea_origen': linea_temporal_actual.name,
                                         'tarea_destino': linea_temporal_siguiente.name,
                                         'trabajadores': trabajadores_ciclicos,
                                         'instancia_nueva': nuevo_id_instancia[:8]},
                                status=DecisionStatus.POSITIVE, icon="🔄"
                            )
                            motor_eventos.audit_log_interno.append(decision)
                    except Exception as e:
                        motor_eventos.logger.error(
                            f"  ❌ ERROR CRÍTICO al crear instancia en tarea destino: {e}",
                            exc_info=True
                        )
                        return eventos_nuevos
                # --- FIN LÓGICA DE CICLO (COPIADA) ---

            # ----------------------------------------------------------------------------
            # PRIORIDAD 5: (Default) CONTINUAR (Si TAREA NO completa Y NO hubo reasignación ni ciclo)
            # ----------------------------------------------------------------------------
            else:
                motor_eventos.logger.info(
                    f"  ➡️ PRIORIDAD 5: CONTINUAR. {trabajadores_liberados} seguirán en '{linea_temporal_actual.name}'"
                )

                # --- INICIO LÓGICA CONTINUAR (COPIADA) ---
                unidades_en_proceso = {
                    inst['unidad_actual']
                    for inst in linea_temporal_actual.instancias_activas
                }
                siguiente_unidad_actual = linea_temporal_actual.unidades_finalizadas_total + 1
                while siguiente_unidad_actual in unidades_en_proceso and siguiente_unidad_actual <= linea_temporal_actual.unidades_a_producir:
                    siguiente_unidad_actual += 1

                if siguiente_unidad_actual > linea_temporal_actual.unidades_a_producir:
                    motor_eventos.logger.info(
                        f"  🔚 No hay más unidades disponibles en '{linea_temporal_actual.name}'. "
                        f"Trabajadores {trabajadores_liberados} quedan libres."
                    )
                    eventos_nuevos.extend(
                        self._registrar_inactividad_trabajadores(motor_eventos, linea_temporal_actual))
                else:
                    puede_continuar = True
                    razon_bloqueo = None
                    if indice_actual is not None and 0 <= indice_actual < len(motor_eventos.production_flow):
                        step_config = motor_eventos.production_flow[indice_actual]
                        dependency_index = step_config.get('previous_task_index')
                        if dependency_index is not None:
                            min_pred_units = step_config.get('min_predecessor_units', 1)
                            unidades_predecesor_requeridas = (
                                                                         siguiente_unidad_actual - 1) * min_pred_units + min_pred_units
                            pred_tarea_id = motor_eventos.indice_a_tarea_id.get(dependency_index)
                            if pred_tarea_id:
                                pred_linea_temporal = motor_eventos.lineas_temporales.get(pred_tarea_id)
                                if pred_linea_temporal:
                                    unidades_predecesor_completadas = pred_linea_temporal.unidades_finalizadas_total
                                    motor_eventos.logger.debug(
                                        f"  🔍 Verificación de dependencia para U{siguiente_unidad_actual}:\n"
                                        f"     • Predecesor: '{pred_linea_temporal.name}'\n"
                                        f"     • Requeridas: {unidades_predecesor_requeridas}\n"
                                        f"     • Completadas: {unidades_predecesor_completadas}"
                                    )
                                    if unidades_predecesor_completadas < unidades_predecesor_requeridas:
                                        puede_continuar = False
                                        razon_bloqueo = (
                                            f"Esperando {unidades_predecesor_requeridas - unidades_predecesor_completadas} unidad(es) más de '{pred_linea_temporal.name}'")
                    if puede_continuar:
                        motor_eventos.logger.info(
                            f"  ⬆️ CONTINUACIÓN: Creando nueva instancia para U{siguiente_unidad_actual} "
                            f"en '{linea_temporal_actual.name}' con {trabajadores_liberados}"
                        )
                        nuevo_id_instancia = linea_temporal_actual.iniciar_instancia_inicial(
                            trabajadores_liberados,
                            self.timestamp,
                            siguiente_unidad_actual
                        )
                        evento_continuacion = EventoInicioUnidad(
                            timestamp=self.timestamp,
                            datos={
                                'tarea_id': tarea_id,
                                'unidad': siguiente_unidad_actual,
                                'id_instancia': nuevo_id_instancia
                            }
                        )
                        eventos_nuevos.append(evento_continuacion)
                    else:
                        motor_eventos.logger.info(
                            f"  ⏸️ CONTINUACIÓN BLOQUEADA: {razon_bloqueo}"
                        )
                        eventos_nuevos.extend(
                            self._registrar_inactividad_trabajadores(motor_eventos, linea_temporal_actual))

        # ============================================================================
        # 👑 FIN DE LA LÓGICA DE DECISIÓN PRIORIZADA 👑
        # ============================================================================

        # SIEMPRE: Verificar dependencias estándar para OTRAS tareas
        # (Esto despierta las "tareas durmientes")
        motor_eventos.logger.debug("🔗 Verificando dependencias estándar (despertar tareas)...")
        eventos_dependencias = motor_eventos._verificar_dependencias_cumplidas(
            tarea_completada_id=tarea_id,
            # Usamos el contador global, que es la fuente de verdad
            unidad_completada=linea_temporal_actual.unidades_finalizadas_total,
            timestamp_actual=self.timestamp,
            eventos_ya_creados=eventos_nuevos
        )
        if eventos_dependencias:
            motor_eventos.logger.info(
                f"  🔓 Dependencias: {len(eventos_dependencias)} tarea(s) desbloqueada(s)"
            )
            eventos_nuevos.extend(eventos_dependencias)
        else:
            motor_eventos.logger.debug("  ✓ Sin dependencias que desbloquear")

        # --- Log final ---
        motor_eventos.logger.info(
            f"{'=' * 70}\n"
            f"📦 RESUMEN EventoFinUnidad '{linea_temporal_actual.name}' U{numero_unidad_completada} [Inst {id_instancia[:8]}]:\n"
            f"   • Eventos generados: {len(eventos_nuevos)}\n"
            f"{'=' * 70}\n"
        )

        return eventos_nuevos

    def _verificar_reglas_reasignacion(self, motor_eventos, tarea_origen_id: str,
                                       unidades_completadas: int,
                                       trabajadores_instancia: List[str],
                                       tarea_completada: bool) -> List['EventoDeSimulacion']:
        """
        Verifica si algún trabajador debe ser reasignado según las reglas configuradas.
        """
        eventos_reasignacion = []

        motor_eventos.logger.info(
            f"\n{'🔍' * 30}\n"
            f"🔍 VERIFICANDO REGLAS DE REASIGNACIÓN:\n"
            f"   • Tarea origen: {tarea_origen_id}\n"
            f"   • Unidades completadas: {unidades_completadas}\n"
            f"   • Trabajadores instancia: {trabajadores_instancia}\n"
            f"   • Tarea completada: {tarea_completada}\n"
        )

        if not trabajadores_instancia:
            motor_eventos.logger.debug("   ⏭️ No hay trabajadores en instancia")
            return []

        # Obtener configuración
        indice_origen = motor_eventos.tarea_id_a_indice.get(tarea_origen_id)
        if indice_origen is None:
            return []

        step_config = motor_eventos.production_flow[indice_origen]
        workers_config = step_config.get('workers', [])

        for worker_config in workers_config:
            if not isinstance(worker_config, dict):
                continue

            worker_name = worker_config.get('name')
            regla = worker_config.get('reassignment_rule')

            if not regla or not worker_name:
                continue

            # Verificar si el trabajador está en esta instancia
            if worker_name not in trabajadores_instancia:
                continue

            # Verificar condición según tipo
            cumple_condicion = False
            condition_type = regla.get('condition_type')

            if condition_type == 'AFTER_UNITS':
                condition_value = regla.get('condition_value', 0)
                cumple_condicion = (unidades_completadas >= condition_value)
                motor_eventos.logger.debug(
                    f"      📊 '{worker_name}' - AFTER_UNITS: {unidades_completadas} >= {condition_value} = {cumple_condicion}"
                )

            elif condition_type == 'ON_FINISH':
                cumple_condicion = tarea_completada
                motor_eventos.logger.debug(
                    f"      📊 '{worker_name}' - ON_FINISH: tarea_completada = {cumple_condicion}"
                )

            if cumple_condicion:
                target_task_id = regla.get('target_task_id')
                mode = regla.get('mode', 'PARALLEL_JOIN')

                motor_eventos.logger.info(
                    f"\n   ✅ REGLA DISPARADA PARA '{worker_name}':\n"
                    f"      • Condición: {condition_type}\n"
                    f"      • Tarea destino: {target_task_id}\n"
                    f"      • Modo: {mode}\n"
                )

                evento_reasignacion = EventoReasignacionTrabajador(
                    timestamp=self.timestamp,
                    datos={
                        'trabajador_id': worker_name,
                        'tarea_origen': tarea_origen_id,
                        'tarea_destino': target_task_id,
                        'mode': mode,
                        'motivo': f"Condición cumplida: {condition_type}"
                    }
                )
                eventos_reasignacion.append(evento_reasignacion)

        motor_eventos.logger.info(
            f"{'🔍' * 30}\n"
            f"📊 RESULTADO: {len(eventos_reasignacion)} reasignación(es) generada(s)\n"
        )

        return eventos_reasignacion

    def _registrar_inactividad_trabajadores(self, motor_eventos, linea_temporal_actual: 'LineaTemporalTarea') -> \
            List['EventoDeSimulacion']:
        """
        Calcula y registra la inactividad de los trabajadores asignados a una tarea
        cuando esta se bloquea o finaliza. Añade directamente al audit_log_interno.
        """
        from calculation_audit import CalculationDecision, DecisionStatus

        # ✅ DIAGNÓSTICO
        motor_eventos.logger.critical("=" * 80)
        motor_eventos.logger.critical(f"🔍 DEBUG _registrar_inactividad_trabajadores:")
        motor_eventos.logger.critical(f"  Tarea completada: {linea_temporal_actual.name}")
        motor_eventos.logger.critical(f"  Trabajadores asignados: {linea_temporal_actual.trabajadores_asignados}")
        motor_eventos.logger.critical(f"  Timestamp actual: {self.timestamp}")

        trabajadores_tarea = linea_temporal_actual.trabajadores_asignados

        # --- UMBRAL DE INACTIVIDAD (en minutos) ---
        UMBRAL_MINUTOS_INACTIVIDAD = 5

        motor_eventos.logger.critical(f"  Umbral de inactividad: {UMBRAL_MINUTOS_INACTIVIDAD} min")

        # ✅ NUEVA ESTRATEGIA: Buscar en eventos_futuros cuándo se desbloqueará esta tarea
        # Buscar el próximo evento FIN_BLOQUE_TRABAJO del predecesor que desbloqueará esta tarea

        # Obtener configuración de dependencias de esta tarea
        tarea_id_actual = None
        for tid, linea in motor_eventos.lineas_temporales.items():
            if linea == linea_temporal_actual:
                tarea_id_actual = tid
                break

        motor_eventos.logger.critical(f"  Tarea ID actual: {tarea_id_actual}")

        if not tarea_id_actual:
            motor_eventos.logger.critical("  ✗ No se pudo obtener tarea_id actual")
            motor_eventos.logger.critical("=" * 80)
            return []

        # Obtener dependency_index directamente de la línea temporal
        dependency_index = linea_temporal_actual.dependency_index

        motor_eventos.logger.critical(
            f"  Dependency index (de linea_temporal): {dependency_index} (type: {type(dependency_index)})")

        # ✅ CORRECCIÓN: 0 es un índice válido, solo None o negativo significa sin dependencia
        if dependency_index is None or (isinstance(dependency_index, int) and dependency_index < 0):
            motor_eventos.logger.critical("  ✗ Esta tarea no tiene dependencias (no está bloqueada)")
            motor_eventos.logger.critical("=" * 80)
            return []

        motor_eventos.logger.critical(f"  ✓ Dependency index válido: {dependency_index}")

        # Obtener tarea predecesora
        pred_tarea_id = motor_eventos.indice_a_tarea_id.get(dependency_index)
        if not pred_tarea_id:
            motor_eventos.logger.critical("  ✗ No se encontró tarea predecesora")
            motor_eventos.logger.critical("=" * 80)
            return []

        pred_linea_temporal = motor_eventos.lineas_temporales.get(pred_tarea_id)
        if not pred_linea_temporal:
            motor_eventos.logger.critical("  ✗ No se encontró línea temporal predecesora")
            motor_eventos.logger.critical("=" * 80)
            return []

        motor_eventos.logger.critical(f"  Predecesor: {pred_linea_temporal.name}")
        motor_eventos.logger.critical(f"  Unidades completadas predecesor: {pred_linea_temporal.unidades_completadas}")

        # Buscar el próximo evento FIN_BLOQUE_TRABAJO del predecesor
        proxima_finalizacion_predecesor = None
        unidad_que_desbloqueara = linea_temporal_actual.unidades_completadas + 1

        for evento_futuro in sorted(motor_eventos.eventos_futuros):
            timestamp_futuro, _, evento_obj = evento_futuro

            if timestamp_futuro <= self.timestamp:
                continue

            if hasattr(evento_obj, 'tipo_evento') and evento_obj.tipo_evento == 'FIN_BLOQUE_TRABAJO':
                ev_tarea_id = evento_obj.datos.get('tarea_id')
                ev_unidad = evento_obj.datos.get('numero_unidad')

                if ev_tarea_id == pred_tarea_id:
                    motor_eventos.logger.critical(
                        f"    Encontrado FIN del predecesor: U{ev_unidad} en {timestamp_futuro.strftime('%d/%m %H:%M')}"
                    )
                    # El primero que encontremos será el que desbloquee la siguiente unidad
                    proxima_finalizacion_predecesor = timestamp_futuro
                    break

        if proxima_finalizacion_predecesor:
            tiempo_espera_min = (proxima_finalizacion_predecesor - self.timestamp).total_seconds() / 60
            motor_eventos.logger.critical(f"  ✓ Tiempo de espera calculado: {tiempo_espera_min:.1f} min")

            if tiempo_espera_min > UMBRAL_MINUTOS_INACTIVIDAD:
                for trabajador_id in trabajadores_tarea:
                    motor_eventos.logger.warning(
                        f"     ⚠️ TIEMPO INACTIVO DETECTADO:\n"
                        f"        Trabajador: {trabajador_id}\n"
                        f"        Tarea bloqueada: {linea_temporal_actual.name}\n"
                        f"        Tiempo de espera: {tiempo_espera_min:.1f} minutos\n"
                        f"        Esperando a: {pred_linea_temporal.name}"
                    )

                    decision = CalculationDecision(
                        timestamp=self.timestamp,
                        task_name=linea_temporal_actual.name,
                        decision_type='TIEMPO_INACTIVO',
                        reason=f"El trabajador {trabajador_id} completó '{linea_temporal_actual.name}' U{linea_temporal_actual.unidades_completadas} "
                               f"y debe esperar {tiempo_espera_min:.1f} minutos a que '{pred_linea_temporal.name}' complete su siguiente unidad",
                        user_friendly_reason=f"Trabajador inactivo {tiempo_espera_min:.1f} min esperando material de {pred_linea_temporal.name}",
                        details={
                            'trabajador': trabajador_id,
                            'wait_time': tiempo_espera_min,
                            'wait_minutes': tiempo_espera_min,
                            'tarea_actual': linea_temporal_actual.name,
                            'proxima_tarea': f"{linea_temporal_actual.name} U{unidad_que_desbloqueara}",
                            'esperando_a': pred_linea_temporal.name,
                            'resource': f"Trabajador ({trabajador_id})"
                        },
                        status=DecisionStatus.WARNING,
                        icon="⏸️"
                    )

                    motor_eventos.audit_log_interno.append(decision)
                    motor_eventos.logger.critical(f"      ✅ Evento de inactividad añadido al audit_log_interno")
            else:
                motor_eventos.logger.critical(
                    f"  ✗ Tiempo de espera ({tiempo_espera_min:.1f} min) no supera umbral ({UMBRAL_MINUTOS_INACTIVIDAD} min)"
                )
        else:
            motor_eventos.logger.critical("  ✗ No se encontró próxima finalización del predecesor")

        motor_eventos.logger.critical(
            f"  Total eventos en audit_log_interno ahora: {len(motor_eventos.audit_log_interno)}")
        motor_eventos.logger.critical("=" * 80)

        return []

@dataclass
class EventoReasignacionTrabajador(EventoDeSimulacion):
    """Evento que reasigna un trabajador de una tarea a otra."""
    tipo_evento: str = 'REASIGNACION_TRABAJADOR'
    prioridad: int = 0

    def procesar(self, motor_eventos) -> List['EventoDeSimulacion']:
        """
        Procesa la reasignación de un trabajador con soporte para modo paralelo.
        """
        trabajador_id = self.datos.get('trabajador_id')
        tarea_origen_id = self.datos.get('tarea_origen')
        tarea_destino_id = self.datos.get('tarea_destino')
        mode = self.datos.get('mode', 'REPLACE')  # PARALLEL_JOIN o REPLACE
        motivo = self.datos.get('motivo', 'Reasignación programada')

        motor_eventos.logger.info(
            f"🔄 [{self.timestamp.strftime('%d/%m %H:%M')}] REASIGNACIÓN ({mode}): "
            f"Trabajador '{trabajador_id}' de '{tarea_origen_id}' → '{tarea_destino_id}' ({motivo})"
        )

        # Remover de origen (en ambos modos)
        if tarea_origen_id and tarea_origen_id in motor_eventos.lineas_temporales:
            linea_origen = motor_eventos.lineas_temporales[tarea_origen_id]
            if trabajador_id in linea_origen.trabajadores_asignados:
                linea_origen.trabajadores_asignados.remove(trabajador_id)
                motor_eventos.logger.debug(f"   ↪️ Removido de '{linea_origen.name}'")

        # Procesar según el modo
        if tarea_destino_id and tarea_destino_id in motor_eventos.lineas_temporales:
            linea_destino = motor_eventos.lineas_temporales[tarea_destino_id]

            motor_eventos.logger.critical(
                f"DEBUG REASSIGN: Worker '{trabajador_id}' - Target '{tarea_destino_id}' - MODE DETECTED: '{mode}'")

            if mode == 'PARALLEL_JOIN':
                # MODO PARALELO: Crear nueva instancia paralela
                motor_eventos.logger.info(
                    f"   🔀 Iniciando instancia paralela en '{linea_destino.name}'"
                )
                id_instancia = linea_destino.agregar_instancia_paralela(
                    trabajador_id,
                    self.timestamp,
                    motor_eventos
                )

                if id_instancia:
                    motor_eventos.logger.info(
                        f"   ✅ Instancia paralela {id_instancia[:8]} creada exitosamente"
                    )
                else:
                    motor_eventos.logger.warning(
                        f"   ⚠️ No se pudo crear instancia paralela (tarea completada o sin unidades)"
                    )
            else:
                # MODO REEMPLAZO: Solo añadir a la lista (comportamiento anterior)
                if trabajador_id not in linea_destino.trabajadores_asignados:
                    linea_destino.trabajadores_asignados.append(trabajador_id)
                    motor_eventos.logger.debug(f"   ↪️ Añadido a '{linea_destino.name}'")

                    # Recalcular eventos si existe el método
                    if hasattr(linea_destino, 'recalcular_eventos_futuros'):
                        linea_destino.recalcular_eventos_futuros(motor_eventos, self.timestamp)

        return []

@dataclass
class EventoTiempoInactivo(EventoDeSimulacion):
    """
    Evento que registra cuando un trabajador queda inactivo esperando trabajo.
    No genera nuevos eventos, solo registra la situación en el audit log.
    """
    tipo_evento: str = 'TIEMPO_INACTIVO'
    prioridad: int = 5

    def procesar(self, motor_eventos) -> List['EventoDeSimulacion']:
        """
        Registra el tiempo de inactividad en el audit log.
        """
        from calculation_audit import CalculationDecision, DecisionStatus

        trabajador = self.datos.get('trabajador', 'Trabajador desconocido')
        tarea_actual = self.datos.get('tarea_actual', 'N/A')
        tiempo_espera_min = self.datos.get('tiempo_espera_min', 0)
        proxima_tarea = self.datos.get('proxima_tarea', 'N/A')

        motor_eventos.logger.warning(
            f"⏸️ TIEMPO INACTIVO DETECTADO:\n"
            f"   Trabajador: {trabajador}\n"
            f"   Tarea finalizada: {tarea_actual}\n"
            f"   Tiempo de espera: {tiempo_espera_min:.1f} minutos\n"
            f"   Próxima tarea: {proxima_tarea}"
        )

        # Crear decisión de auditoría
        decision = CalculationDecision(
            timestamp=self.timestamp,
            task_name=tarea_actual,
            decision_type='TIEMPO_INACTIVO',
            reason=f"El trabajador {trabajador} terminó '{tarea_actual}' y no tiene siguiente "
                   f"tarea disponible por {tiempo_espera_min:.1f} minutos",
            user_friendly_reason=f"Tiempo de inactividad: {tiempo_espera_min:.1f} min esperando siguiente tarea",
            details={
                'trabajador': trabajador,
                'wait_time': tiempo_espera_min,
                'wait_minutes': tiempo_espera_min,
                'tarea_actual': tarea_actual,
                'proxima_tarea': proxima_tarea,
                'resource': f"Trabajador ({trabajador})"
            },
            status=DecisionStatus.WARNING,
            icon="⏸️"
        )

        # COMIENZA A COPIAR DESDE AQUÍ (Reemplazar la línea anterior)
        # Añadir a la lista interna del motor de eventos
        motor_eventos.audit_log_interno.append(decision)
        # TERMINA DE COPIAR AQUÍ

        return []  # No genera más eventos