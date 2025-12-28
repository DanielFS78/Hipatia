# event_engine.py
import logging
import heapq
import pickle
import os
import time
from datetime import datetime, date
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from PyQt6.QtWidgets import QApplication

# Importamos todos los componentes de nuestra nueva arquitectura
from time_calculator import CalculadorDeTiempos
from resource_manager import GestorDeRecursos
from temporal_storage import RegistroTemporal
from timeline_task import LineaTemporalTarea
from simulation_events import EventoDeSimulacion, EventoInicioUnidad, EventoFinUnidad
from calculation_audit import CalculationDecision, DecisionStatus

class MotorDeEventos:
    """
    Orquesta la simulación basada en eventos discretos, coordinando tareas,
    recursos y la persistencia de resultados con procesamiento en paralelo.
    """

    def __init__(self, production_flow: List[Dict], all_workers_data: List,
                 all_machines_data: Dict, schedule_config, start_date: datetime,
                 time_calculator: CalculadorDeTiempos,
                 checkpoint_path: str = None,
                 visual_dialog_reference=None):  # <-- AÑADIDO

        self.production_flow = production_flow
        self.logger = logging.getLogger(__name__)
        self.lock = Lock()
        self.visual_dialog_reference = visual_dialog_reference

        # --- 1. Inicializar Componentes de Soporte ---
        self.calculador_tiempos = time_calculator
        self.gestor_recursos = GestorDeRecursos(self.calculador_tiempos)
        temp_db_path = f"temp_simulation_{datetime.now().strftime('%Y%m%d%H%M%S')}.db"
        self.registro_temporal = RegistroTemporal(db_path=temp_db_path)

        if checkpoint_path and os.path.exists(checkpoint_path):
            self._load_checkpoint(checkpoint_path)
            return

        # --- 2. Preparar el Estado Inicial de la Simulación ---
        self.tiempo_actual = start_date
        self.eventos_futuros = []
        self.event_counter = 0
        self.audit_log_interno = []
        self.lineas_temporales: Dict[str, LineaTemporalTarea] = {}

        for worker_name, skill_level in all_workers_data:
            self.gestor_recursos.registrar_recurso(worker_name, es_trabajador=True)
        for machine_id in all_machines_data.keys():
            self.gestor_recursos.registrar_recurso(machine_id, es_trabajador=False)

        # --- 3. Crear las Líneas Temporales de Tareas y mapeo de índices ---
        self.indice_a_tarea_id = {}
        self.tarea_id_a_indice = {}

        for i, step in enumerate(production_flow):
            # ✅ DIAGNÓSTICO TEMPORAL (puedes eliminarlo después)
            self.logger.critical("=" * 80)
            self.logger.critical(f"🔍 DIAGNÓSTICO PASO {i}:")
            self.logger.critical(f"  Task name: {step.get('task', {}).get('name', 'SIN NOMBRE')}")
            self.logger.critical(f"  Workers field exists: {'workers' in step}")
            self.logger.critical(f"  Workers value: {step.get('workers', 'NO EXISTE')}")
            self.logger.critical(f"  Workers type: {type(step.get('workers', None))}")
            if step.get('workers'):
                self.logger.critical(f"  Workers length: {len(step.get('workers', []))}")
                for idx, w in enumerate(step.get('workers', [])):
                    self.logger.critical(f"    Worker {idx}: {w} (type: {type(w)})")
            self.logger.critical("=" * 80)
            # FIN DIAGNÓSTICO

            task_data = step['task'].copy()
            task_data['trigger_units'] = step.get('trigger_units', 1)

            if 'start_date' in step and step['start_date'] is not None:
                from datetime import datetime as dt
                if isinstance(step['start_date'], dt):
                    task_data['scheduled_start_date'] = step['start_date']
                else:
                    task_data['scheduled_start_date'] = dt.combine(
                        step['start_date'],
                        schedule_config.WORK_START_TIME
                    )
                self.logger.info(
                    f"📅 Tarea '{task_data.get('name', 'Sin nombre')}' configurada con fecha de inicio: "
                    f"{task_data['scheduled_start_date'].strftime('%d/%m/%Y %H:%M')}"
                )

            if 'previous_task_index' in step and step['previous_task_index'] is not None:
                task_data['previous_task_index'] = step['previous_task_index']
                self.logger.debug(
                    f"Tarea '{task_data.get('name')}' tiene dependencia con índice {step['previous_task_index']}"
                )

            linea_temporal = LineaTemporalTarea(task_data, self.gestor_recursos, self.calculador_tiempos)

            self.lineas_temporales[linea_temporal.id] = linea_temporal
            self.indice_a_tarea_id[i] = linea_temporal.id
            self.tarea_id_a_indice[linea_temporal.id] = i

            # ✅ CORRECCIÓN CRÍTICA: Extraer nombres de trabajadores de forma robusta
            workers_data = step.get('workers', [])
            trabajadores_nombres = []

            if workers_data:
                for w in workers_data:
                    if isinstance(w, dict) and 'name' in w:
                        # Formato: [{'name': 'Daniel Sanz', 'reassignment_rule': None}]
                        trabajadores_nombres.append(w['name'])
                    elif isinstance(w, str):
                        # Formato antiguo: ['Daniel Sanz']
                        trabajadores_nombres.append(w)
                    else:
                        self.logger.warning(
                            f"⚠️ Formato de trabajador no reconocido en tarea '{task_data.get('name')}': {w}"
                        )

            linea_temporal.trabajadores_asignados = trabajadores_nombres

            # Log de verificación
            if trabajadores_nombres:
                self.logger.debug(
                    f"✅ Asignados {len(trabajadores_nombres)} trabajador(es) a '{linea_temporal.name}': "
                    f"{', '.join(trabajadores_nombres)}"
                )
            else:
                self.logger.warning(
                    f"⚠️ Tarea '{linea_temporal.name}' no tiene trabajadores asignados. "
                    f"No podrá ejecutarse."
                )

            self.logger.debug(
                f"Tarea registrada: índice={i}, id={linea_temporal.id}, "
                f"name='{linea_temporal.name}', dependency_index={linea_temporal.dependency_index}, "
                f"scheduled_start={'Sí' if linea_temporal.scheduled_start_date else 'NO'}"
            )

        self.logger.info(f"Motor de eventos inicializado DESDE CERO con {len(self.lineas_temporales)} tareas.")

    def _generar_eventos_iniciales(self):
        """
        CORREGIDO v6: Las tareas con fecha programada SON raíces, SIEMPRE.
        El hecho de que sean objetivo de un salto cíclico NO las descalifica como raíz.
        La lógica de "ignorar fecha cuando se activa por ciclo" se maneja en EventoFinUnidad.
        """
        self.logger.info(
            "\n" + "=" * 80 + "\n"
                              "INICIANDO GENERACIÓN DE EVENTOS INICIALES\n" +
            "=" * 80
        )

        # --- PASO 1: Identificar tareas con dependencias ESTÁNDAR ---
        # Solo las dependencias estándar (previous_task_index) impiden que una tarea sea raíz
        tareas_con_dependencia_estandar = set()

        for i, step in enumerate(self.production_flow):
            target_task_id = self.indice_a_tarea_id.get(i)
            if not target_task_id:
                continue

            # Solo dependencias estándar cuentan para bloquear raíces
            dep_index_std = step.get('previous_task_index')
            if dep_index_std is not None:
                tareas_con_dependencia_estandar.add(target_task_id)
                self.logger.debug(
                    f"  📌 Tarea '{self.lineas_temporales[target_task_id].name}' (idx {i}) "
                    f"tiene dependencia estándar desde índice {dep_index_std}"
                )

        # --- PASO 2: Identificar todas las RAÍCES VERDADERAS ---
        # CORREGIDO: Una tarea es RAÍZ si está marcada manualmente como is_cycle_start
        # Esto respeta la configuración manual del usuario en la interfaz
        raices_verdaderas = []
        fechas_programadas = []

        for i, step in enumerate(self.production_flow):
            tarea_id = self.indice_a_tarea_id.get(i)
            if not tarea_id:
                continue

            tarea = self.lineas_temporales.get(tarea_id)
            if not tarea:
                continue

            # CORREGIDO: is_cycle_start está directamente en step, no en un sub-dict 'config'
            es_inicio_ciclo = step.get('is_cycle_start', False)

            # Una tarea es raíz si:
            # 1. Está marcada manualmente como inicio de ciclo (is_cycle_start=True)
            # 2. NO tiene dependencia estándar (esto ya se verificó en PASO 1)
            es_raiz = (
                    es_inicio_ciclo and
                    tarea_id not in tareas_con_dependencia_estandar
            )

            if es_raiz:
                raices_verdaderas.append(tarea)

                # Usar la fecha programada si existe, o la fecha actual del motor
                fecha_inicio = tarea.scheduled_start_date if (hasattr(tarea,
                                                                      'scheduled_start_date') and tarea.scheduled_start_date) else self.tiempo_actual
                fechas_programadas.append(fecha_inicio)

                self.logger.info(
                    f"  🌳 RAÍZ DETECTADA (is_cycle_start): '{tarea.name}' (índice {i}) → "
                    f"{fecha_inicio.strftime('%d/%m/%Y %H:%M')}"
                )
            elif es_inicio_ciclo and tarea_id in tareas_con_dependencia_estandar:
                # Advertir si alguien marcó una tarea como inicio de ciclo pero tiene dependencia
                self.logger.warning(
                    f"  ⚠️ Tarea '{tarea.name}' está marcada como inicio de ciclo pero tiene "
                    f"dependencia estándar. NO se usará como raíz."
                )

        # --- PASO 3: Ajustar tiempo de simulación a la fecha más temprana ---
        if fechas_programadas:
            fecha_mas_temprana = min(fechas_programadas)
            if fecha_mas_temprana < self.tiempo_actual:
                self.logger.info(
                    f"\n⏰ AJUSTANDO tiempo de inicio de simulación:\n"
                    f"   De: {self.tiempo_actual.strftime('%d/%m/%Y %H:%M')}\n"
                    f"   A:  {fecha_mas_temprana.strftime('%d/%m/%Y %H:%M')}"
                )
                self.tiempo_actual = fecha_mas_temprana

        # --- PASO 4: Generar eventos para todas las raíces ---
        eventos_iniciales = []
        eventos_por_timestamp = {}

        for tarea in raices_verdaderas:
            timestamp_evento = max(self.tiempo_actual, tarea.scheduled_start_date)

            if not self._tiene_evento_futuro(tarea.id, 1):
                # --- INICIO MODIFICACIÓN ---
                # 1. Crear la instancia inicial ANTES de crear el evento
                #    Asegurarse de que 'trabajadores_asignados' existe en 'tarea'
                trabajadores_tarea = getattr(tarea, 'trabajadores_asignados', [])
                if not trabajadores_tarea:
                    self.logger.warning(
                        f"Tarea raíz '{tarea.name}' sin trabajadores asignados. Omitiendo evento inicial.")
                    continue  # Saltar esta tarea si no tiene trabajadores

                # Usamos timestamp_evento como fecha de inicio de la instancia
                id_instancia_inicial = tarea.iniciar_instancia_inicial(trabajadores_tarea, timestamp_evento, 1)

                # 2. Crear el evento INCLUYENDO el id_instancia
                evento = EventoInicioUnidad(
                    timestamp=timestamp_evento,
                    datos={
                        'tarea_id': tarea.id,
                        'unidad': 1,
                        'iniciado_por_fecha': True,
                        'id_instancia': id_instancia_inicial  # <-- AÑADIDO
                    }
                )
                eventos_iniciales.append(evento)

                # Agrupar por timestamp
                ts_key = timestamp_evento.strftime('%d/%m/%Y %H:%M')
                if ts_key not in eventos_por_timestamp:
                    eventos_por_timestamp[ts_key] = []
                eventos_por_timestamp[ts_key].append(tarea.name)

                self.logger.info(
                    f"  📅 Evento creado: '{tarea.name}' → {ts_key}"
                )
            else:
                self.logger.warning(
                    f"  ⚠️ Evento duplicado detectado para '{tarea.name}' - OMITIDO"
                )

        # --- Log de eventos agrupados ---
        if eventos_por_timestamp:
            self.logger.info(f"\n📅 EVENTOS AGRUPADOS POR TIMESTAMP:")
            for ts, tareas in sorted(eventos_por_timestamp.items()):
                if len(tareas) > 1:
                    self.logger.info(
                        f"   🔸 {ts} → {len(tareas)} tareas paralelas:\n" +
                        "\n".join([f"      • {t}" for t in tareas])
                    )
                else:
                    self.logger.info(f"   🔸 {ts} → {tareas[0]}")

        # --- Log final ---
        self.logger.info(
            f"\n" + "=" * 80 + "\n"
                               f"✅ GENERACIÓN COMPLETADA:\n"
                               f"   • Raíces verdaderas detectadas: {len(raices_verdaderas)}\n"
                               f"   • Eventos iniciales generados: {len(eventos_iniciales)}\n"
                               f"   • Simulación comenzará en: {self.tiempo_actual.strftime('%d/%m/%Y %H:%M')}\n" +
            "=" * 80
        )

        self.programar_eventos(eventos_iniciales)

    def _verificar_dependencias_cumplidas(self, tarea_completada_id: str,
                                          unidad_completada: int,
                                          timestamp_actual: datetime,
                                          eventos_ya_creados: List = None,
                                          visitados: set = None) -> List:  # <-- AÑADIDO: set de visitados
        """
        CORREGIDO: Verifica si la finalización de una unidad desbloquea unidades
        de tareas dependientes. 
        
        MEJORA CRÍTICA: Si una tarea dependiente YA está completada, la señal "atraviesa"
        esa tarea y verifica recursivamente a SUS dependientes. Esto soluciona el bloqueo
        en ciclos donde una tarea intermedia (ej. A) termina antes que las otras (B y C).
        """
        if eventos_ya_creados is None:
            eventos_ya_creados = []
            
        if visitados is None:
            visitados = set()

        # Evitar bucles infinitos de propagación
        if tarea_completada_id in visitados:
            return []
        
        visitados.add(tarea_completada_id)

        eventos_generados = []
        tareas_dependientes = self._encontrar_tareas_dependientes(tarea_completada_id)

        if not tareas_dependientes:
            return eventos_generados

        self.logger.debug(
            f"🔍 Verificando dependencias: '{self.lineas_temporales[tarea_completada_id].name}' "
            f"alcanzó {unidad_completada} unidades. Encontradas {len(tareas_dependientes)} tarea(s) dependiente(s)."
        )

        linea_predecesora = self.lineas_temporales[tarea_completada_id]
        unidades_predecesor_completadas_GLOBAL = linea_predecesora.unidades_finalizadas_total

        if unidad_completada != unidades_predecesor_completadas_GLOBAL:
            # Nota: Esto es normal en llamadas recursivas donde simulamos desbloqueos desde tareas terminadas hace tiempo
            pass

        for tarea_dependiente in tareas_dependientes:
            indice_dependiente = self.tarea_id_a_indice.get(tarea_dependiente.id)
            if indice_dependiente is None:
                continue

            # --- NUEVA LÓGICA DE PROPAGACIÓN (PASSTHROUGH) ---
            if tarea_dependiente.unidades_finalizadas_total >= tarea_dependiente.unidades_a_producir:
                self.logger.info(
                    f"  ⏩ Tarea dependiente '{tarea_dependiente.name}' YA ESTÁ COMPLETADA. "
                    f"Propagando señal a través de ella..."
                )
                # Llamada recursiva: La tarea dependiente actúa como si acabara de completar 
                # su última unidad para despertar a SUS dependientes.
                eventos_propagados = self._verificar_dependencias_cumplidas(
                    tarea_completada_id=tarea_dependiente.id,
                    unidad_completada=tarea_dependiente.unidades_finalizadas_total,
                    timestamp_actual=timestamp_actual, # Usamos el mismo tiempo actual
                    eventos_ya_creados=eventos_ya_creados,
                    visitados=visitados
                )
                eventos_generados.extend(eventos_propagados)
                continue # Pasamos a la siguiente dependiente
            # --- FIN NUEVA LÓGICA ---

            paso_flujo_dependiente = self.production_flow[indice_dependiente]
            min_predecessor_units = paso_flujo_dependiente.get('min_predecessor_units', 1)

            # --- LÓGICA DE DESPERTAR TAREA DURMIENTE (CORREGIDA) ---

            # 1. Construir una lista de todas las unidades ya gestionadas (activas, programadas, o recién creadas)
            unidades_en_proceso_o_programadas = {
                inst['unidad_actual'] for inst in tarea_dependiente.instancias_activas
            }

            # 2. Buscar en la cola principal del motor
            for _, _, ev in self.eventos_futuros:
                if not ev.cancelado and ev.datos.get('tarea_id') == tarea_dependiente.id:
                    if ev.tipo_evento == 'INICIO_UNIDAD' or (
                            ev.tipo_evento == 'FIN_BLOQUE_TRABAJO' and ev.datos.get('numero_unidad')):
                        unidades_en_proceso_o_programadas.add(ev.datos.get('unidad', ev.datos.get('numero_unidad')))

            # 3. Buscar en la lista temporal de eventos que se acaban de crear
            for ev in eventos_ya_creados:
                if not ev.cancelado and ev.datos.get('tarea_id') == tarea_dependiente.id:
                    if ev.tipo_evento == 'INICIO_UNIDAD':
                        unidades_en_proceso_o_programadas.add(ev.datos.get('unidad'))
            
            # También chequear en los eventos que acabamos de generar en esta misma llamada recursiva
            for ev in eventos_generados:
                if not ev.cancelado and ev.datos.get('tarea_id') == tarea_dependiente.id:
                    if ev.tipo_evento == 'INICIO_UNIDAD':
                        unidades_en_proceso_o_programadas.add(ev.datos.get('unidad'))

            # 4. Encontrar la próxima unidad que NO esté en esa lista
            unidad_a_iniciar = tarea_dependiente.unidades_finalizadas_total + 1
            while unidad_a_iniciar in unidades_en_proceso_o_programadas:
                unidad_a_iniciar += 1

            self.logger.debug(
                f"  Comprobando '{tarea_dependiente.name}':\n"
                f"     • Finalizadas: {tarea_dependiente.unidades_finalizadas_total}\n"
                f"     • En proceso o Programadas: {unidades_en_proceso_o_programadas}\n"
                f"     • Próxima unidad a despertar: {unidad_a_iniciar}"
            )
            # --- FIN DE LA CORRECCIÓN ---

            # Validaciones de seguridad
            if unidad_a_iniciar > tarea_dependiente.unidades_a_producir:
                continue  # Ya terminó, no despertar

            # Calcular cuántas unidades predecesoras se necesitan para ESTA unidad
            unidades_predecesor_requeridas = (unidad_a_iniciar - 1) * min_predecessor_units + min_predecessor_units

            self.logger.debug(
                f"  Comprobando '{tarea_dependiente.name}' U{unidad_a_iniciar}:\n"
                f"     • Requiere: {unidades_predecesor_requeridas} de '{linea_predecesora.name}'\n"
                f"     • Disponibles: {unidades_predecesor_completadas_GLOBAL}"
            )

            # Si se cumple la condición de despertar
            if unidades_predecesor_completadas_GLOBAL >= unidades_predecesor_requeridas:

                # La dependencia SIEMPRE determina el inicio
                timestamp_inicio = timestamp_actual
                if hasattr(tarea_dependiente, 'scheduled_start_date') and tarea_dependiente.scheduled_start_date:
                    self.logger.info(
                        f"  ⚠️ Tarea '{tarea_dependiente.name}' desbloqueada por dependencia. "
                        f"Su fecha programada ({tarea_dependiente.scheduled_start_date.strftime('%d/%m %H:%M')}) será ignorada."
                    )

                # Crear y programar el nuevo evento de inicio
                self.logger.info(
                    f"🚀 DESBLOQUEANDO: '{tarea_dependiente.name}' unidad {unidad_a_iniciar} a las {timestamp_inicio.strftime('%d/%m %H:%M')}"
                )

                # --- AHORA SÍ: Creamos la instancia para la tarea despertada ---
                trabajadores_tarea_dependiente = getattr(tarea_dependiente, 'trabajadores_asignados', [])
                # Si es una tarea que requiere trabajadores y no tiene, error.
                # Si es tipo máquina pura (sin workers), trabajadores_tarea_dependiente será [] y está bien si la lógica lo soporta.
                # Por seguridad, asumimos que siempre necesita 'algo'.
                if not trabajadores_tarea_dependiente and not tarea_dependiente.machine_id: 
                     self.logger.error(
                        f"  ❌ Tarea despertada '{tarea_dependiente.name}' no tiene trabajadores ni máquina. No se puede iniciar.")
                     continue
                
                # Creamos la instancia USANDO LA UNIDAD CORRECTA
                nuevo_id_instancia = tarea_dependiente.iniciar_instancia_inicial(
                    trabajadores_tarea_dependiente,
                    timestamp_inicio,
                    numero_unidad=unidad_a_iniciar  # <-- PASAR LA UNIDAD
                )

                evento_inicio = EventoInicioUnidad(
                    timestamp=timestamp_inicio,
                    datos={
                        'tarea_id': tarea_dependiente.id,
                        'unidad': unidad_a_iniciar,
                        'desbloqueada_por': tarea_completada_id,
                        'id_instancia': nuevo_id_instancia  # <-- CRÍTICO
                    }
                )
                eventos_generados.append(evento_inicio)
            else:
                self.logger.debug(f"  ...condición no cumplida. '{tarea_dependiente.name}' sigue durmiendo.")

        return eventos_generados

    def _tiene_evento_futuro(self, tarea_id: str, numero_unidad: int,
                             id_instancia: Optional[str] = None) -> bool:
        """
        Verifica si ya existe un evento programado (no cancelado) para una
        unidad específica de una tarea (y opcionalmente, una instancia).
        Es CRÍTICO para evitar la duplicación de eventos.
        MODIFICADO: Ahora considera id_instancia.
        """
        with self.lock:  # Asegurar acceso thread-safe a la cola de eventos
            for _, _, evento in self.eventos_futuros:

                if (not evento.cancelado and
                        isinstance(evento, (EventoInicioUnidad, EventoFinUnidad))):

                    datos = evento.datos
                    # Comprobar si la tarea y la unidad coinciden
                    if (datos.get('tarea_id') == tarea_id and
                            datos.get('unidad') == numero_unidad):

                        # Si se especificó una instancia, debe coincidir
                        if id_instancia:
                            if datos.get('id_instancia') == id_instancia:
                                return True
                        else:
                            # Si no se especificó instancia, cualquier coincidencia es válida
                            return True
            return False

    def _encontrar_tareas_dependientes(self, tarea_id: str) -> List:
        """
        Encuentra todas las tareas que tienen como dependencia la tarea especificada.

        Args:
            tarea_id: ID de la tarea predecesora

        Returns:
            Lista de LineaTemporalTarea que dependen de esta tarea
        """
        tareas_dependientes = []
        # Obtener el índice de la tarea predecesora
        if tarea_id not in self.tarea_id_a_indice:
            self.logger.warning(
                f"No se puede encontrar el índice de la tarea '{tarea_id}' "
                f"en el mapeo. No se pueden verificar dependencias."
            )
            return tareas_dependientes
        indice_predecesora = self.tarea_id_a_indice[tarea_id]
        # Buscar todas las tareas cuyo dependency_index apunta a este índice
        for linea_temporal in self.lineas_temporales.values():

            # ==================== INICIO DE LA CORRECCIÓN ====================
            # Si la tarea que estamos comprobando es la misma que la que se completó,
            # la ignoramos para evitar bucles infinitos.
            if linea_temporal.id == tarea_id:
                continue
            # ===================== FIN DE LA CORRECCIÓN ======================
            if linea_temporal.dependency_index == indice_predecesora:
                tareas_dependientes.append(linea_temporal)
                self.logger.debug(
                    f"  🔗 '{linea_temporal.name}' depende de '{tarea_id}' "
                    f"(dependency_index={indice_predecesora})"
                )
        return tareas_dependientes

    def programar_eventos(self, eventos: List[EventoDeSimulacion]):
        """Añade una lista de eventos al heap de forma segura para hilos (thread-safe)."""
        with self.lock:
            self.logger.info(f"📥 programar_eventos: Recibidos {len(eventos)} eventos")  # ✅ AÑADIR
            for evento in eventos:
                heapq.heappush(self.eventos_futuros, (evento.timestamp, self.event_counter, evento))
                self.event_counter += 1

    def cancelar_eventos(self, eventos_a_cancelar: List[EventoDeSimulacion]):
        for evento in eventos_a_cancelar:
            evento.cancelado = True
        self.logger.debug(f"Marcados {len(eventos_a_cancelar)} eventos para cancelación.")

    def _save_checkpoint(self, checkpoint_path='simulation_checkpoint.pkl'):
        self.logger.info(f"Guardando checkpoint de la simulación en: {checkpoint_path}")
        simulation_state = {
            'tiempo_actual': self.tiempo_actual,
            'eventos_futuros': self.eventos_futuros,
            'event_counter': self.event_counter,
            'lineas_temporales': self.lineas_temporales,
            'gestor_recursos': self.gestor_recursos,
        }
        try:
            with open(checkpoint_path, 'wb') as f:
                pickle.dump(simulation_state, f)
            self.logger.info("Checkpoint guardado con éxito.")
        except (pickle.PicklingError, IOError) as e:
            self.logger.critical(f"No se pudo guardar el checkpoint de la simulación: {e}")

    def _load_checkpoint(self, checkpoint_path):
        self.logger.info(f"Reanudando simulación desde checkpoint: {checkpoint_path}")
        try:
            with open(checkpoint_path, 'rb') as f:
                simulation_state = pickle.load(f)
            self.tiempo_actual = simulation_state['tiempo_actual']
            self.eventos_futuros = simulation_state['eventos_futuros']
            self.event_counter = simulation_state['event_counter']
            self.lineas_temporales = simulation_state['lineas_temporales']
            self.gestor_recursos = simulation_state['gestor_recursos']
            self.logger.info(f"Checkpoint cargado con éxito. La simulación se reanudará en {self.tiempo_actual}.")
        except (pickle.UnpicklingError, IOError, KeyError) as e:
            self.logger.critical(f"No se pudo cargar el checkpoint: {e}. Iniciando simulación desde cero.")
            raise RuntimeError(f"El archivo de checkpoint está corrupto o es incompatible: {e}")

    def ejecutar_simulacion(self, checkpoint_interval=5000, max_workers=None):
        """
        Ejecuta el bucle principal de simulación de forma SECUENCIAL para garantizar la estabilidad.
        """
        # PASO NUEVO: Limpiar fechas conflictivas
        self._generar_eventos_iniciales()
        self.logger.info("🚀 Iniciando bucle principal de procesamiento en modo SECUENCIAL...")

        start_simulation_time = time.perf_counter()
        processed_event_count = 0
        iteracion = 0

        # Log inicial del estado de la cola
        self.logger.info(f"📊 Estado inicial: {len(self.eventos_futuros)} eventos en cola")

        # --- BUCLE SECUENCIAL ---
        while self.eventos_futuros:
            iteracion += 1

            if iteracion % 10 == 1 or iteracion <= 5:
                self.logger.info(f"🔄 Iteración {iteracion}: {len(self.eventos_futuros)} eventos en cola")

            # Extraer el siguiente evento
            timestamp, _, evento = heapq.heappop(self.eventos_futuros)
            self.tiempo_actual = timestamp

            self.logger.info(
                f"🔵 [{self.tiempo_actual.strftime('%d/%m %H:%M')}] "
                f"Procesando evento #{iteracion}: {evento.tipo_evento}"
            )

            # ⚠️ OPTIMIZACIÓN MÁXIMA: Visualización deshabilitada para mejor rendimiento
            # Las señales visuales están comentadas para evitar overhead en simulaciones grandes
            # (El bloque de emisión de señales ha sido eliminado)

            # ✅ QUITAR EL TRY TEMPORALMENTE
            self.logger.info(f"   → Procesando evento...")
            nuevos_eventos = evento.procesar(self)

            if nuevos_eventos:
                self.programar_eventos(nuevos_eventos)
                self.logger.info(f"   ✓ {len(nuevos_eventos)} nuevo(s) evento(s) programado(s)")
            else:
                self.logger.warning(f"   ⚠️ NO retornó eventos (nuevos_eventos={nuevos_eventos})")

            self.registro_temporal.guardar_evento(evento)
            processed_event_count += 1
            self.logger.info(f"   ✓ Evento procesado")

        end_simulation_time = time.perf_counter()
        total_duration = end_simulation_time - start_simulation_time
        events_per_second = processed_event_count / total_duration if total_duration > 0 else 0

        self.logger.info("=" * 50)
        self.logger.info("📊 INFORME DE RENDIMIENTO DE LA SIMULACIÓN (SECUENCIAL) 📊")
        self.logger.info("=" * 50)
        self.logger.info(f"  Duración Total: {total_duration:.2f} segundos")
        self.logger.info(f"  Eventos Procesados: {processed_event_count}")
        self.logger.info(f"  Rendimiento Medio: {events_per_second:.2f} eventos/segundo")
        self.logger.info(f"  Iteraciones realizadas: {iteracion}")
        self.logger.info(f"  Eventos restantes: {len(self.eventos_futuros)}")
        self.logger.info("=" * 50)

        if self.eventos_futuros:
            self.logger.warning(f"⚠️ Simulación incompleta: {len(self.eventos_futuros)} eventos sin procesar")
        else:
            self.logger.info("✅ Simulación completada. No hay más eventos por procesar.")

            self.logger.info(f"🏁 Simulación completada en {self.tiempo_actual.strftime('%d/%m/%Y %H:%M')}")

            # ✅ CORRECCIÓN CRÍTICA: Forzar el vaciado del buffer antes de consultar
            self.logger.info("💾 Vaciando buffer de eventos a disco antes de consultar...")
            if hasattr(self.registro_temporal, '_flush_buffer_to_disk'):
                self.registro_temporal._flush_buffer_to_disk()
                self.logger.info("✅ Buffer de eventos vaciado exitosamente")
            else:
                self.logger.warning("⚠️ No se encontró el método _flush_buffer_to_disk")

            # 1. Obtener todos los eventos procesados del registro temporal
            all_processed_events = self.registro_temporal.consultar_eventos()
            self.logger.info(f"Recuperados {len(all_processed_events)} eventos procesados del registro temporal.")

            # 2. Compilar los resultados finales usando los eventos procesados
            results = self._compilar_resultados_compatibles(all_processed_events)
            self.logger.info(f"Compilados {len(results)} resultados finales.")

            # 3. ✅ CORRECCIÓN: Compilar el audit log completo (que ya incluye audit_log_interno)
            audit_log_completo = self._compilar_audit_log_compatible(all_processed_events)
            self.logger.info(f"Audit log completo compilado con {len(audit_log_completo)} eventos.")

            # 4. Devolver los resultados y el audit log completo
            return results, audit_log_completo

    def _compilar_resultados_compatibles(self, all_events):
        """
        CORREGIDO: Lee la lista de eventos del motor y crea UNA entrada de resultado
        por CADA unidad individual completada, calculando la duración REAL de trabajo
        y añadiendo columnas de contexto para el Excel, INCLUYENDO EL IDENTIFICADOR DEL LOTE.
        """
        resultados_individuales = []

        # ✅ DIAGNÓSTICO TEMPORAL
        self.logger.critical("=" * 80)
        self.logger.critical(f"🔍 DEBUG _compilar_resultados_compatibles:")
        self.logger.critical(f"  Total eventos recibidos: {len(all_events)}")

        # Contar tipos de eventos
        tipos_eventos = {}
        for ev in all_events:
            tipo = ev.get('tipo_evento', 'DESCONOCIDO')
            tipos_eventos[tipo] = tipos_eventos.get(tipo, 0) + 1

        self.logger.critical(f"  Tipos de eventos encontrados:")
        for tipo, cantidad in tipos_eventos.items():
            self.logger.critical(f"    - {tipo}: {cantidad}")

        # Mostrar los primeros 3 eventos como ejemplo
        self.logger.critical(f"  Muestra de primeros 3 eventos:")
        for i, ev in enumerate(all_events[:3]):
            self.logger.critical(f"    Evento {i}: {ev}")
        self.logger.critical("=" * 80)
        # FIN DIAGNÓSTICO

        # --- PASO 1: Recopilar todos los eventos de fin de unidad ---
        for evento in all_events:
            if evento['tipo_evento'] != 'FIN_BLOQUE_TRABAJO':
                continue

            datos = evento.get('datos', {})
            tarea_id = datos.get('tarea_id')

            if not tarea_id or tarea_id not in self.lineas_temporales:
                self.logger.warning(f"Evento de fin sin tarea válida: tarea_id={tarea_id}")
                continue

            linea_temporal = self.lineas_temporales[tarea_id]
            task_info = linea_temporal.task_data  # Accedemos a los datos originales de la tarea
            numero_unidad = datos.get('numero_unidad', datos.get('unidad', 1))
            inicio_bloque = datos.get('inicio')
            fin_bloque = evento.get('timestamp')

            if isinstance(inicio_bloque, str):
                try:
                    inicio_bloque = datetime.fromisoformat(inicio_bloque)
                except (ValueError, AttributeError):
                    inicio_bloque = None

            # ✅ CORRECCIÓN 1: Calcular duración REAL de trabajo
            if inicio_bloque and fin_bloque:
                duracion_min = self.calculador_tiempos.calculate_work_minutes_between(
                    inicio_bloque, fin_bloque
                )
            else:
                duracion_min = 0.0

            trabajadores = datos.get('trabajadores', [])
            # Usamos el nombre base de la tarea (sin el "Unidad X") para Tarea
            nombre_base_tarea = task_info.get('name', 'Tarea Desconocida')
            # Creamos un nombre más descriptivo para el log/detalle si fuera necesario
            nombre_completo_unidad = f"{nombre_base_tarea} - Unidad {numero_unidad}"

            product_info = task_info.get('original_product_info', {})

            # ✅ CORRECCIÓN 2: Extraer de forma robusta el código y la descripción del producto origen
            product_desc = product_info.get('desc', task_info.get('product_desc', 'N/A'))
            product_code = task_info.get('original_product_code', task_info.get('product_code', 'N/A'))

            # --- 👇 INICIO DE LA MODIFICACIÓN IMPORTANTE 👇 ---
            # Recuperamos el fabricacion_id (identificador del lote) desde task_info
            identificador_lote = task_info.get('fabricacion_id', 'N/A')
            # --- 👆 FIN DE LA MODIFICACIÓN IMPORTANTE 👆 ---

            resultado_unidad = {
                # Mantenemos 'Tarea' con el nombre base para agrupar en el Excel si se desea
                'Tarea': nombre_base_tarea,
                # Añadimos un campo más específico si es necesario para depuración
                'TareaDetalle': nombre_completo_unidad,
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
                # --- 👇 INCLUSIÓN DEL NUEVO DATO 👇 ---
                'fabricacion_id': identificador_lote,  # Se añade la clave y el valor
                # --- 👆 FIN INCLUSIÓN 👆 ---
                'Index': self.tarea_id_a_indice.get(tarea_id),  # Índice original en production_flow
                'Parent Index': task_info.get('previous_task_index'),  # Índice del predecesor
            }
            # --- 👇 LÍNEA DE DEPURACIÓN A AÑADIR 👇 ---
            self.logger.critical(f"DEBUG: Contenido de resultado_unidad antes de añadir: {resultado_unidad}")
            # --- 👆 FIN LÍNEA DE DEPURACIÓN 👆 ---
            resultados_individuales.append(resultado_unidad)

        if not resultados_individuales:
            return []

        # --- PASO 2: Encontrar la fecha de inicio global (sin cambios) ---
        fecha_inicio_simulacion_valida = [r['Inicio'] for r in resultados_individuales if r['Inicio']]
        if not fecha_inicio_simulacion_valida:
            # Manejar caso donde no hay fechas de inicio válidas
            self.logger.warning("No se encontraron fechas de inicio válidas en los resultados.")
            fecha_inicio_simulacion = date.today()  # O alguna otra fecha por defecto
        else:
            fecha_inicio_simulacion = min(fecha_inicio_simulacion_valida).date()

        # --- PASO 3: Añadir las columnas de "Día X" formateadas (sin cambios) ---
        for result in resultados_individuales:
            # Añadir manejo de errores por si Inicio o Fin son None
            dia_inicio_num = (result['Inicio'].date() - fecha_inicio_simulacion).days + 1 if result['Inicio'] else 0
            dia_fin_num = (result['Fin'].date() - fecha_inicio_simulacion).days + 1 if result['Fin'] else 0
            inicio_hora_str = result['Inicio'].strftime('%H:%M') if result['Inicio'] else 'N/A'
            fin_hora_str = result['Fin'].strftime('%H:%M') if result['Fin'] else 'N/A'

            result['Inicio Formateado'] = f"Día {dia_inicio_num} - {inicio_hora_str}"
            result['Fin Formateado'] = f"Día {dia_fin_num} - {fin_hora_str}"

            dias_laborables = 0
            if result['Inicio'] and result['Fin']:
                try:
                    # Asegurarse que count_workdays maneje None
                    dias_laborables = self.calculador_tiempos.count_workdays(
                        result['Inicio'], result['Fin']
                    )
                except Exception as e:
                    self.logger.warning(
                        f"No se pudieron calcular los días laborables para '{result.get('TareaDetalle', 'N/A')}': {e}")
            result['Dias Laborables'] = dias_laborables if dias_laborables is not None else 0

        self.logger.info(
            f"📊 Resultados compilados: {len(resultados_individuales)} unidades individuales con contexto completo."
        )

        return resultados_individuales

    def _compilar_audit_log_compatible(self, all_events):
        """
        CORREGIDO: Convierte la lista de eventos en un audit log detallado y legible.
        Genera descripciones específicas por tipo de evento con iconos y status apropiados.
        MODIFICADO: Ahora incluye también los eventos del audit_log_interno (como TIEMPO_INACTIVO).
        """
        audit_log = []

        # Primero, compilar los eventos estándar desde all_events
        for evento in all_events:
            tipo_evento = evento.get('tipo_evento', 'DESCONOCIDO')
            datos = evento.get('datos', {})
            timestamp = evento.get('timestamp')

            # Extraer el ID de la tarea de los datos del evento
            tarea_id = datos.get('tarea_id')
            task_info = {'name': 'Tarea Desconocida', 'product_code': 'N/A', 'product_desc': 'N/A'}

            # Buscar la información de la tarea en las líneas temporales
            if tarea_id and tarea_id in self.lineas_temporales:
                original_task_data = self.lineas_temporales[tarea_id].task_data
                task_info = {
                    'name': original_task_data.get('name', 'N/A'),
                    'product_code': original_task_data.get('original_product_code', 'N/A'),
                    'product_desc': original_task_data.get('original_product_info', {}).get('desc', 'N/A')
                }

            # ✅ NUEVO: Generar descripción específica según el tipo de evento
            reason, user_friendly_reason, icon, status = self._generar_descripcion_evento(
                tipo_evento, datos, task_info
            )

            decision = CalculationDecision(
                timestamp=timestamp,
                decision_type=tipo_evento,
                reason=reason,
                user_friendly_reason=user_friendly_reason,
                task_name=task_info.get('name', 'N/A'),
                product_code=task_info.get('product_code', 'N/A'),
                product_desc=task_info.get('product_desc', 'N/A'),
                status=status,
                icon=icon
            )
            audit_log.append(decision)

        # ✅ NUEVO: Añadir los eventos del audit_log_interno (TIEMPO_INACTIVO, etc.)
        if hasattr(self, 'audit_log_interno') and self.audit_log_interno:
            self.logger.info(f"📝 Añadiendo {len(self.audit_log_interno)} eventos del audit_log_interno")
            audit_log.extend(self.audit_log_interno)
        else:
            self.logger.debug("📝 No hay eventos en audit_log_interno para añadir")

        # Ordenar todo el audit log por timestamp para mantener orden cronológico
        audit_log.sort(key=lambda x: x.timestamp if hasattr(x, 'timestamp') else datetime.min)

        self.logger.info(
            f"📋 Audit log compilado: {len(audit_log)} eventos registrados "
            f"({len(all_events)} estándar + "
            f"{len(self.audit_log_interno) if hasattr(self, 'audit_log_interno') else 0} internos)"
        )
        return audit_log

    def _generar_descripcion_evento(self, tipo_evento: str, datos: dict,
                                    task_info: dict) -> tuple:
        """
        Genera descripciones específicas, iconos y status para cada tipo de evento.

        Returns:
            tuple: (reason, user_friendly_reason, icon, status)
        """
        task_name = task_info.get('name', 'Tarea')

        # ============================================================================
        # INICIO DE UNIDAD
        # ============================================================================
        if tipo_evento == 'INICIO_UNIDAD':
            numero_unidad = datos.get('unidad', datos.get('numero_unidad', '?'))
            trabajadores = datos.get('trabajadores', [])
            desbloqueada_por = datos.get('desbloqueada_por')

            if desbloqueada_por:
                reason = (
                    f"Iniciando unidad {numero_unidad} de '{task_name}' "
                    f"(desbloqueada por dependencia completada)"
                )
                user_friendly_reason = (
                    f"Se inició la unidad {numero_unidad} después de completarse "
                    f"su tarea predecesora"
                )
                icon = "🔓"
            else:
                reason = f"Iniciando unidad {numero_unidad} de '{task_name}'"
                user_friendly_reason = (
                    f"Se dio inicio a la producción de la unidad {numero_unidad}"
                )
                icon = "▶️"

            if trabajadores:
                trabajadores_str = ', '.join(trabajadores) if isinstance(trabajadores, list) else str(trabajadores)
                reason += f" con trabajadores: {trabajadores_str}"

            return reason, user_friendly_reason, icon, DecisionStatus.POSITIVE

        # ============================================================================
        # FIN DE BLOQUE DE TRABAJO (Unidad completada)
        # ============================================================================
        elif tipo_evento == 'FIN_BLOQUE_TRABAJO':
            numero_unidad = datos.get('numero_unidad', datos.get('unidad', '?'))
            trabajadores = datos.get('trabajadores', [])
            duracion = datos.get('duracion_calculada', 0)

            trabajadores_str = ', '.join(trabajadores) if isinstance(trabajadores, list) else str(trabajadores)

            reason = (
                f"Completada unidad {numero_unidad} de '{task_name}' "
                f"por {trabajadores_str} en {duracion:.1f} min"
            )
            user_friendly_reason = (
                f"Se finalizó exitosamente la producción de la unidad {numero_unidad} "
                f"en {duracion:.1f} minutos"
            )
            icon = "✅"
            return reason, user_friendly_reason, icon, DecisionStatus.POSITIVE

        # ============================================================================
        # REASIGNACIÓN DE TRABAJADOR
        # ============================================================================
        elif tipo_evento == 'REASIGNACION_TRABAJADOR':
            trabajador_id = datos.get('trabajador_id', 'Trabajador')
            tarea_origen = datos.get('tarea_origen', 'N/A')
            tarea_destino = datos.get('tarea_destino', 'N/A')
            motivo = datos.get('motivo', 'Reasignación programada')

            reason = (
                f"Reasignación: '{trabajador_id}' de '{tarea_origen}' a '{tarea_destino}' "
                f"({motivo})"
            )
            user_friendly_reason = (
                f"El trabajador {trabajador_id} fue reasignado para optimizar la producción"
            )
            icon = "🔄"
            return reason, user_friendly_reason, icon, DecisionStatus.NEUTRAL

        # ============================================================================
        # ESPERA POR RECURSOS (Cuello de botella)
        # ============================================================================
        elif tipo_evento == 'ESPERA_RECURSOS':
            recurso = datos.get('recurso', 'recurso no especificado')
            tiempo_espera = datos.get('tiempo_espera_min', 0)

            reason = (
                f"'{task_name}' esperó {tiempo_espera:.1f} min por '{recurso}'"
            )
            user_friendly_reason = (
                f"Se detectó una demora de {tiempo_espera:.1f} minutos esperando "
                f"por {recurso}"
            )
            icon = "⏳"

            # Clasificar severidad de la espera
            if tiempo_espera > 60:
                status = DecisionStatus.WARNING
            else:
                status = DecisionStatus.NEUTRAL

            return reason, user_friendly_reason, icon, status

        # ============================================================================
        # VERIFICACIÓN DE DEPENDENCIAS
        # ============================================================================
        elif tipo_evento == 'VERIFICAR_DEPENDENCIA':
            tarea_esperada = datos.get('tarea_esperada', 'tarea predecesora')

            reason = f"Verificando si '{tarea_esperada}' ha completado suficientes unidades"
            user_friendly_reason = f"Comprobando el cumplimiento de dependencias"
            icon = "🔍"
            return reason, user_friendly_reason, icon, DecisionStatus.NEUTRAL

        # ============================================================================
        # EVENTO GENÉRICO O DESCONOCIDO
        # ============================================================================
        else:
            reason = f"Evento '{tipo_evento}': {datos}"
            user_friendly_reason = f"Evento de tipo '{tipo_evento}' procesado"
            icon = "⚙️"
            return reason, user_friendly_reason, icon, DecisionStatus.NEUTRAL