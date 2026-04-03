# -*- coding: utf-8 -*-
"""
Nombre del Módulo: resource_manager.py
Descripción: Gestiona la disponibilidad y asignación de recursos (operarios y 
             máquinas) durante la simulación, controlando solapamientos.
"""
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict
from threading import Lock
# Importamos las clases base que ya creamos.
# Asumimos que la raíz del proyecto está en el path de Python.
from .simulation_events import EventoReasignacionTrabajador
from core.services.time_calculator import CalculadorDeTiempos


@dataclass
class IntervaloOcupacion:
    """Representa un bloque de tiempo en el que un recurso está ocupado."""
    inicio: datetime
    fin: datetime
    tarea_id: str


@dataclass
class ReglaReasignacion:
    """
    Define y almacena las condiciones lógicas del negocio bajo las cuales 
    se reasignan operarios físicos en la cadena de montaje de producción.
    
    Reglas de Negocio soportadas y modeladas:
    - 'AFTER_UNITS' (Balanceo de carga in-situ / Desplazamientos Secuenciales): 
      Implica especificar la regla con `condicion_tipo="AFTER_UNITS"` y un
      número N en `condicion_valor`.
      El sistema asume que el operario ensamblará forzosamente N iteraciones
      íntegras del proceso (tarea_origen_id), finalizando el cupo tras el cual,
      sin mediación de su supervisor, transicionará automáticamente al inicio 
      de registro de un nodo alternativo (tarea_destino_id) equilibrando cargas.
    """
    trabajador_id: str
    tarea_origen_id: str
    tarea_destino_id: str
    condicion_tipo: str  # E.g., 'AFTER_UNITS'
    condicion_valor: int


class GestorDeRecursos:
    """Gestiona la disponibilidad y asignación de trabajadores y máquinas."""

    def __init__(self, time_calculator: CalculadorDeTiempos) -> None:
        self.logger = logging.getLogger(__name__)
        self.time_calculator = time_calculator

        # Estructura de datos avanzada: Un diccionario por cada recurso que contiene
        # una lista ordenada de sus intervalos de ocupación.
        self.calendario_trabajadores: Dict[str, List[IntervaloOcupacion]] = {}
        self.calendario_maquinas: Dict[int, List[IntervaloOcupacion]] = {}
        self.lock = Lock()
        # Registro de reglas de reasignación pendientes.
        self.reglas_reasignacion: List[ReglaReasignacion] = []

    def registrar_recurso(self, recurso_id: str | int, es_trabajador: bool = True) -> None:
        """Inicializa el calendario para un nuevo trabajador o máquina."""
        if es_trabajador:
            if isinstance(recurso_id, str):
                 if recurso_id not in self.calendario_trabajadores:
                    self.calendario_trabajadores[recurso_id] = []
            else:
                 self.logger.error(f"ID de trabajador inválido: {recurso_id} ({type(recurso_id)})")
        else:
            if isinstance(recurso_id, int):
                if recurso_id not in self.calendario_maquinas:
                    self.calendario_maquinas[recurso_id] = []
            else:
                 self.logger.error(f"ID de máquina inválido: {recurso_id} ({type(recurso_id)})")

    def programar_reasignacion(self, regla: ReglaReasignacion) -> None:
        """Registra una nueva regla de reasignación para ser evaluada."""
        self.reglas_reasignacion.append(regla)
        self.logger.info(
            f"Regla de reasignación programada: {regla.trabajador_id} de {regla.tarea_origen_id} a {regla.tarea_destino_id}")

    def encontrar_siguiente_momento_disponible(self, recurso_id: str, desde_fecha: datetime,
                                               es_trabajador: bool = True) -> datetime:
        """
        Encuentra la primera fecha/hora en que un recurso está libre a partir de 'desde_fecha',
        respetando tanto los bloques de trabajo ya asignados como el horario laboral.
        THREAD-SAFE: Protegido con lock para prevenir lecturas inconsistentes.
        """
        with self.lock:  # ✅ Bloqueo para thread safety
            if es_trabajador:
                if isinstance(recurso_id, str):
                    intervalos_ocupados = list(self.calendario_trabajadores.get(recurso_id, []))
                else:
                    intervalos_ocupados = []
            else:
                if isinstance(recurso_id, int):
                    intervalos_ocupados = list(self.calendario_maquinas.get(recurso_id, []))
                else:
                    intervalos_ocupados = []

        # El resto del procesamiento se hace fuera del lock para no bloquearlo demasiado tiempo
        # 1. Ajustar 'desde_fecha' al próximo momento laborable válido usando el calculador.
        momento_propuesto = self.time_calculator.add_work_minutes(desde_fecha, 0)

        # 2. Bucle para resolver conflictos con tareas ya asignadas.
        while True:
            # Comprobar si el momento_propuesto se solapa con algún trabajo ya asignado.
            conflicto = next(
                (intervalo for intervalo in intervalos_ocupados
                 if intervalo.inicio <= momento_propuesto < intervalo.fin),
                None
            )

            if conflicto:
                # Si hay conflicto, nuestro nuevo momento propuesto es justo cuando termina ese trabajo.
                momento_propuesto = self.time_calculator.add_work_minutes(conflicto.fin, 0)
                continue
            else:
                # Si no hay conflictos, hemos encontrado un hueco válido.
                return momento_propuesto

    def asignar_recurso(self, recurso_id: str, inicio: datetime, fin: datetime,
                        tarea_id: str, es_trabajador: bool = True) -> None:
        """
        Añade un nuevo intervalo de ocupación al calendario de un recurso.
        THREAD-SAFE: Protegido con lock para prevenir modificaciones concurrentes.
        """
        with self.lock:  # ✅ Bloqueo para thread safety
            calendario = self.calendario_trabajadores if es_trabajador else self.calendario_maquinas

            # Obtener o crear la lista de intervalos para este recurso
            if es_trabajador:
                 if isinstance(recurso_id, str):
                     if recurso_id not in self.calendario_trabajadores:
                         self.calendario_trabajadores[recurso_id] = []
                     intervalos = self.calendario_trabajadores[recurso_id]
                 else:
                     self.logger.error("ID trabajador invalido")
                     return
            else:
                 if isinstance(recurso_id, int):
                     if recurso_id not in self.calendario_maquinas:
                         self.calendario_maquinas[recurso_id] = []
                     intervalos = self.calendario_maquinas[recurso_id]
                 else:
                     self.logger.error("ID maquina invalido")
                     return

            # Crear el nuevo intervalo
            nuevo_intervalo = IntervaloOcupacion(inicio=inicio, fin=fin, tarea_id=tarea_id)

            # Insertar y ordenar de forma segura
            intervalos.append(nuevo_intervalo)
            intervalos.sort(key=lambda i: i.inicio)

            self.logger.debug(
                f"Recurso '{recurso_id}' asignado a tarea '{tarea_id}' "
                f"de {inicio.strftime('%d/%m %H:%M')} a {fin.strftime('%d/%m %H:%M')}"
            )

    def notificar_unidades_completadas(self, tarea_id: str, unidades_completadas: int) -> List[
        EventoReasignacionTrabajador]:
        """
        Evalúa si la finalización de unidades en una tarea dispara alguna regla de reasignación.
        """
        eventos_generados = []
        reglas_a_eliminar = []

        for regla in self.reglas_reasignacion:
            if regla.tarea_origen_id == tarea_id:
                if regla.condicion_tipo == 'AFTER_UNITS' and unidades_completadas >= regla.condicion_valor:
                    # Se cumplió la condición, generamos el evento
                    evento = EventoReasignacionTrabajador(
                        timestamp=datetime.now(),  # El motor sobrescribirá esto con el tiempo correcto
                        datos={
                            'trabajador_id': regla.trabajador_id,
                            'tarea_origen_id': regla.tarea_origen_id,
                            'tarea_destino_id': regla.tarea_destino_id
                        }
                    )
                    eventos_generados.append(evento)
                    reglas_a_eliminar.append(regla)
                    self.logger.info(f"¡Disparada reasignación para {regla.trabajador_id}!")

        # Eliminar las reglas que ya se han disparado
        self.reglas_reasignacion = [r for r in self.reglas_reasignacion if r not in reglas_a_eliminar]

        return eventos_generados