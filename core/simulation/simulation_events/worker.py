# core/simulation/events/worker.py

"""
Lógica o utilidades del núcleo (`worker`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

from dataclasses import dataclass
from typing import Any, List
from .base import EventoDeSimulacion

@dataclass
class EventoReasignacionTrabajador(EventoDeSimulacion):
    """Evento que reasigna un trabajador de una tarea a otra."""
    tipo_evento: str = 'REASIGNACION_TRABAJADOR'
    prioridad: int = 0

    def procesar(self, motor_eventos: Any) -> List[EventoDeSimulacion]:
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

    def procesar(self, motor_eventos: Any) -> List[EventoDeSimulacion]:
        """
        Registra el tiempo de inactividad en el audit log.
        """
        from core.services.calculation_audit import CalculationDecision, DecisionStatus

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

        # Añadir a la lista interna del motor de eventos
        motor_eventos.audit_log_interno.append(decision)

        return []
