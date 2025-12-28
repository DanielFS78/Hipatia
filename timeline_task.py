# timeline_task.py
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

# Importamos las dependencias que necesitará esta clase
from time_calculator import CalculadorDeTiempos
from resource_manager import GestorDeRecursos
from simulation_events import EventoDeSimulacion, EventoInicioUnidad, EventoFinUnidad


class LineaTemporalTarea:
    """
    Representa el estado y la progresión de una única tarea a lo largo del tiempo.
    Gestiona sus propios recursos, dependencias y genera sus propios eventos de simulación.
    """

    def __init__(self, task_data: Dict[str, Any], gestor_recursos: GestorDeRecursos,
                 calculador_tiempos: CalculadorDeTiempos):

        self.logger = logging.getLogger(__name__)

        # --- Dependencias Externas ---
        self.gestor_recursos = gestor_recursos
        self.calculador_tiempos = calculador_tiempos

        # Guardamos el diccionario original de la tarea para referencia
        self.task_data = task_data

        # --- Atributos Estáticos (propiedades de la tarea) ---
        # Estos datos vienen del diccionario generado por _prepare_task_data
        self.id = task_data.get('id', 'task_sin_id')
        self.name = task_data.get('name', 'Tarea sin nombre')
        self.duration_per_unit = task_data.get('duration', 0.0)
        self.required_skill_level = task_data.get('tipo_trabajador', 1)
        self.machine_id = task_data.get('machine_id')
        self.dependency_index = task_data.get('previous_task_index')

        # CRÍTICO: Capturar la fecha de inicio programada si existe
        self.scheduled_start_date = task_data.get('scheduled_start_date', None)

        if self.scheduled_start_date:
            self.logger.info(
                f"Tarea '{self.name}' tiene fecha de inicio programada: "
                f"{self.scheduled_start_date.strftime('%d/%m/%Y %H:%M')}"
            )

        # --- Atributos de Estado (evolucionan durante la simulación) ---
        self.unidades_a_producir = task_data.get('trigger_units', 1)
        # MANTENER para compatibilidad, pero su rol cambia
        self.unidades_completadas = 0  # Servirá como alias
        self.trabajadores_asignados: List[str] = []  # Será una lista agregada de todos los trabajadores

        # NUEVO: Estructura para trabajo paralelo
        self.instancias_activas: List[Dict] = []
        # Cada diccionario en la lista tendrá esta estructura:
        # {
        #     'id_instancia': str (uuid),
        #     'trabajadores': List[str],
        #     'unidad_actual': int,
        #     'inicio_unidad': datetime,
        #     'evento_fin_programado': EventoDeSimulacion (referencia)
        # }

        # NUEVO: Contador global
        self.unidades_finalizadas_total = 0

        self.historial_unidades: List[Dict[str, Any]] = []  # [ {'unidad': 1, 'fin': datetime}, ... ]

        # Mantiene una referencia a los eventos futuros para poder cancelarlos
        self.eventos_futuros: List[EventoDeSimulacion] = []

        self.logger.info(f"Inicializada LineaTemporal para Tarea '{self.name}' ({self.id})")

    def __repr__(self):
        return f"<LineaTemporalTarea(id={self.id}, name='{self.name}', completadas={self.unidades_completadas}/{self.unidades_a_producir})>"

    def iniciar_instancia_inicial(self, trabajadores: List[str],
                                  fecha_inicio: datetime,
                                  numero_unidad: int = 1) -> str:
        """
        Crea la primera instancia de trabajo para esta tarea.
        Llamado desde:
            - generar_eventos_de_produccion()
            - EventoInicioUnidad.procesar() (para la primera unidad)
        Args:
            trabajadores: Lista de IDs de trabajadores
            fecha_inicio: Momento de inicio de la instancia

        Returns:
            id_instancia: UUID de la instancia creada
        """
        id_instancia = str(uuid.uuid4())

        instancia = {
            'id_instancia': id_instancia,
            'trabajadores': trabajadores.copy(),
            'unidad_actual': numero_unidad,
            'inicio_unidad': fecha_inicio,
            'evento_fin_programado': None  # Se asigna después
        }

        self.instancias_activas.append(instancia)

        # Mantener trabajadores_asignados actualizado
        for trab in trabajadores:
            if trab not in self.trabajadores_asignados:
                self.trabajadores_asignados.append(trab)

        self.logger.info(
            f"✨ Nueva instancia {id_instancia[:8]} creada en '{self.name}' "
            f"con trabajadores {trabajadores}"
        )

        return id_instancia

    def agregar_instancia_paralela(self, trabajador_id: str,
                                   fecha_inicio: datetime,
                                   motor_eventos) -> Optional[str]:
        """
        Añade un trabajador en una nueva instancia paralela.
        Llamado desde:
            - EventoReasignacionTrabajador.procesar() cuando action='UNIRSE_PARALELO'
        Args:
            trabajador_id: ID del trabajador que se une
            fecha_inicio: Momento en que se une
            motor_eventos: Referencia al motor para generar eventos

        Returns:
            id_instancia si se creó exitosamente, None si no hay trabajo disponible
        """
        # --- LOG 1 (Al inicio) ---
        self.logger.critical(
            f"DEBUG PARALLEL_ADD: Tarea '{self.name}' - Worker '{trabajador_id}' intenta unirse en paralelo.")

        # 1. Verificar si hay unidades disponibles
        if self.unidades_finalizadas_total >= self.unidades_a_producir:
            self.logger.warning(
                f"⚠️ No se puede crear instancia paralela: "
                f"tarea '{self.name}' ya completó todas sus unidades"
            )
            return None

        # 2. Calcular próxima unidad disponible
        # Las instancias activas están trabajando en ciertas unidades
        # Necesitamos encontrar la próxima unidad que no esté siendo trabajada
        unidades_en_proceso = {inst['unidad_actual'] for inst in self.instancias_activas}

        self.logger.critical(f"DEBUG PARALLEL_ADD: Unidades en proceso: {unidades_en_proceso}")
        self.logger.critical(f"DEBUG PARALLEL_ADD: Unidades finalizadas total: {self.unidades_finalizadas_total}")

        proxima_unidad = self.unidades_finalizadas_total + 1
        while proxima_unidad in unidades_en_proceso:
            proxima_unidad += 1

        # --- LOG 3 (Después de proxima_unidad) ---
        self.logger.critical(f"DEBUG PARALLEL_ADD: Próxima unidad calculada: {proxima_unidad}")

        if proxima_unidad > self.unidades_a_producir:
            self.logger.warning(
                f"⚠️ No hay unidades disponibles para nueva instancia en '{self.name}'"
            )
            return None

        # 3. Crear nueva instancia
        id_instancia = str(uuid.uuid4())

        instancia = {
            'id_instancia': id_instancia,
            'trabajadores': [trabajador_id],
            'unidad_actual': proxima_unidad,
            'inicio_unidad': fecha_inicio,
            'evento_fin_programado': None
        }
        # --- LOG 4 (Antes de append) ---
        self.logger.critical(f"DEBUG PARALLEL_ADD: Creando instancia {id_instancia[:8]} para unidad {proxima_unidad}.")
        self.instancias_activas.append(instancia)

        # Actualizar trabajadores_asignados
        if trabajador_id not in self.trabajadores_asignados:
            self.trabajadores_asignados.append(trabajador_id)

        self.logger.info(
            f"🔀 Instancia paralela {id_instancia[:8]} creada en '{self.name}' "
            f"para trabajador '{trabajador_id}' en unidad {proxima_unidad}"
        )

        # 4. Generar evento de inicio para esta instancia
        # IMPORTANTE: Esta importación debe estar aquí (o global)
        # La movemos aquí para evitar una importación circular si simulation_events
        # importa timeline_task.
        from simulation_events import EventoInicioUnidad
        evento_inicio = EventoInicioUnidad(
            timestamp=fecha_inicio,
            datos={
                'tarea_id': self.id,
                'unidad': proxima_unidad,
                'id_instancia': id_instancia,  # NUEVO: identificador de instancia
                'es_instancia_paralela': True
            }
        )

        # --- LOG 5 (Antes de programar evento) ---
        self.logger.critical(
            f"DEBUG PARALLEL_ADD: Programando EventoInicioUnidad para instancia {id_instancia[:8]}, unidad {proxima_unidad}.")

        # Guardar referencia (opcional, para poder cancelar después)
        self.eventos_futuros.append(evento_inicio)

        # Retornar evento para que motor lo programe
        motor_eventos.programar_eventos([evento_inicio])

        return id_instancia

    def completar_unidad_instancia(self, id_instancia: str) -> Dict:
        """
        Marca una unidad como completada para una instancia específica.
        Actualiza contadores y ELIMINA la instancia, devolviendo sus trabajadores
        para que el motor de eventos decida su próximo paso.

        Llamado desde:
            - EventoFinUnidad.procesar()

        Args:
            id_instancia: UUID de la instancia que completó su unidad

        Returns:
            Dict con información de la finalización:
            {
                'instancia_completada': True, # Siempre es True si se encontró
                'tarea_completada': bool,    # True si la tarea entera ha terminado
                'siguiente_unidad': None,   # El motor decidirá esto
                'trabajadores_liberados': List[str] # Trabajadores a liberar
            }
        """
        # 1. Encontrar la instancia
        instancia = None
        for inst in self.instancias_activas:
            if inst['id_instancia'] == id_instancia:
                instancia = inst
                break

        if not instancia:
            self.logger.error(f"❌ Instancia {id_instancia[:8]} no encontrada en '{self.name}' al completar unidad.")
            return {
                'instancia_completada': False,  # No se encontró, así que no se completó
                'tarea_completada': (self.unidades_finalizadas_total >= self.unidades_a_producir),
                'siguiente_unidad': None,
                'trabajadores_liberados': []
            }

        # 2. Incrementar contador global
        self.unidades_finalizadas_total += 1
        self.unidades_completadas = self.unidades_finalizadas_total  # Mantener sincronizado

        self.logger.info(
            f"✅ Instancia {id_instancia[:8]} completó unidad {instancia['unidad_actual']} "
            f"de '{self.name}' (Total: {self.unidades_finalizadas_total}/{self.unidades_a_producir})"
        )

        # 3. Verificar si la TAREA completa está terminada
        tarea_completada = (self.unidades_finalizadas_total >= self.unidades_a_producir)

        # 4. Obtener trabajadores y ELIMINAR la instancia
        # Hacemos esto ANTES de comprobar si la tarea está completada
        # para asegurar que la instancia siempre se elimine de la lista de activas.
        trabajadores_inst = instancia['trabajadores'].copy()
        self.instancias_activas.remove(instancia)

        self.logger.info(
            f"🔚 Instancia {id_instancia[:8]} eliminada. "
            f"Trabajadores {trabajadores_inst} liberados para decisión del motor."
        )

        if tarea_completada:
            # CASO A: TAREA COMPLETADA
            # La tarea ha terminado. Todos los trabajadores de *esta* instancia quedan libres.
            # (Si había otras instancias paralelas, se cancelarán en EventoFinUnidad)
            self.logger.info(
                f"🏁 Tarea '{self.name}' COMPLETADA (alcanzó {self.unidades_finalizadas_total})."
            )

            return {
                'instancia_completada': True,
                'tarea_completada': True,
                'siguiente_unidad': None,
                'trabajadores_liberados': trabajadores_inst
            }

        # CASO B: TAREA NO COMPLETADA
        # La tarea continúa, pero esta instancia ha terminado su trabajo.
        # Devolvemos los trabajadores para que el motor decida.
        return {
            'instancia_completada': True,  # La instancia SÍ completó su unidad
            'tarea_completada': False,  # La tarea NO está completa
            'siguiente_unidad': None,  # El motor decidirá la siguiente unidad
            'trabajadores_liberados': trabajadores_inst  # Devolvemos los trabajadores
        }

    def obtener_instancia(self, id_instancia: str) -> Optional[Dict]:
        """
        Obtiene los datos de una instancia específica.
        Args:
            id_instancia: UUID de la instancia

        Returns:
            Dict con datos de la instancia o None si no existe
        """
        for inst in self.instancias_activas:
            if inst['id_instancia'] == id_instancia:
                return inst
        return None

    def generar_eventos_de_produccion(self, desde_fecha: datetime) -> List[EventoDeSimulacion]:
        """
        Genera el evento de inicio para la primera unidad, creando la instancia inicial.
        CAMBIO: Ya no genera evento de fin, solo de inicio.
        """
        self.logger.info(f"🟢 GENERANDO EVENTOS para '{self.name}' unidad {self.unidades_finalizadas_total + 1}")

        # Usamos el nuevo contador global
        if self.unidades_finalizadas_total >= self.unidades_a_producir:
            return []  # La tarea ya está completa

        # --- 1. Verificar que tenemos trabajadores asignados ---
        if not self.trabajadores_asignados:
            self.logger.warning(f"Tarea '{self.name}' no tiene trabajadores. No se puede planificar.")
            return []

        # --- 2. Crear instancia inicial (si no existe) ---
        if not self.instancias_activas:
            # Si no hay instancias, creamos la primera
            id_instancia = self.iniciar_instancia_inicial(
                self.trabajadores_asignados,
                desde_fecha
            )
        else:
            # Si ya existe (ej. en un recálculo), usamos la primera
            id_instancia = self.instancias_activas[0]['id_instancia']

        # --- 3. Generar SOLO el evento de inicio ---
        # El evento de inicio ahora debe saber a qué instancia pertenece
        unidad_actual = self.unidades_finalizadas_total + 1

        evento_inicio = EventoInicioUnidad(
            timestamp=desde_fecha,
            datos={
                'tarea_id': self.id,
                'unidad': unidad_actual,
                'id_instancia': id_instancia  # NUEVO: Asociamos a la instancia
            }
        )

        # Guardamos una referencia para poder cancelarlo después si es necesario
        self.eventos_futuros.append(evento_inicio)

        self.logger.debug(
            f"📋 Generado evento de inicio para '{self.name}' "
            f"unidad {unidad_actual} instancia {id_instancia[:8]}"
        )
        return [evento_inicio]

    def agregar_trabajador(self, trabajador_id: str, motor_eventos):
        """Añade un trabajador a la tarea y dispara un recálculo."""
        if trabajador_id not in self.trabajadores_asignados:
            self.trabajadores_asignados.append(trabajador_id)
            self.logger.info(f"Trabajador '{trabajador_id}' añadido a la tarea '{self.name}'. Disparando recálculo.")
            # El momento del recálculo es ahora mismo (el tiempo actual del motor)
            ahora = motor_eventos.tiempo_actual
            self.recalcular_eventos_futuros(motor_eventos, ahora)

    def recalcular_eventos_futuros(self, motor_eventos, desde_fecha: datetime):
        """
        Cancela todos los eventos futuros de esta tarea y genera nuevos eventos
        basados en el estado actual. Este es el núcleo del recálculo dinámico.
        """
        # --- Paso 1: Cancelar eventos futuros ---
        self.logger.info(f"Recalculando eventos para '{self.name}' debido a un cambio.")

        eventos_a_cancelar = self.eventos_futuros.copy()
        self.eventos_futuros.clear()  # Limpiamos la lista de referencias

        motor_eventos.cancelar_eventos(eventos_a_cancelar)

        # --- Paso 2: Generar nuevos eventos desde el estado actual ---
        nuevos_eventos = self.generar_eventos_de_produccion(desde_fecha)
        motor_eventos.programar_eventos(nuevos_eventos)

    def info_instancias(self) -> str:
        """Devuelve string con información de todas las instancias activas."""
        if not self.instancias_activas:
            return "Sin instancias activas"

        info = f"Instancias activas en '{self.name}':\n"
        for inst in self.instancias_activas:
            info += (
                f"  - {inst['id_instancia'][:8]}: "
                f"Trabajadores={inst['trabajadores']}, "
                f"Unidad={inst['unidad_actual']}\n"
            )
        info += f"Total completado: {self.unidades_finalizadas_total}/{self.unidades_a_producir}"
        return info

    @property
    def esta_completada(self) -> bool:
        """
        Propiedad que devuelve True si la tarea ha completado todas sus unidades.
        """
        return self.unidades_completadas >= self.unidades_a_producir