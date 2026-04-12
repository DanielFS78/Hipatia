"""
Nombre del Módulo: core.simulation.timeline_task_parallel

Descripción: Funciones puras de apoyo (sin estado de proceso): ``agregar_instancia_paralela_ops``, ``completar_unidad_instancia_ops``. Integración típica con: ``__future__``, ``uuid``, ``datetime``.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any


def agregar_instancia_paralela_ops(
    task: Any,
    trabajador_id: str,
    fecha_inicio: datetime,
    motor_eventos: Any,
) -> str | None:
    """Crea una instancia paralela y programa su evento de inicio."""
    task.logger.critical(
        f"DEBUG PARALLEL_ADD: Tarea '{task.name}' - Worker '{trabajador_id}' intenta unirse en paralelo."
    )

    if task.unidades_finalizadas_total >= task.unidades_a_producir:
        task.logger.warning(
            f"⚠️ No se puede crear instancia paralela: tarea '{task.name}' ya completó todas sus unidades"
        )
        return None

    unidades_en_proceso = {inst["unidad_actual"] for inst in task.instancias_activas}
    task.logger.critical(f"DEBUG PARALLEL_ADD: Unidades en proceso: {unidades_en_proceso}")
    task.logger.critical(f"DEBUG PARALLEL_ADD: Unidades finalizadas total: {task.unidades_finalizadas_total}")

    proxima_unidad = task.unidades_finalizadas_total + 1
    while proxima_unidad in unidades_en_proceso:
        proxima_unidad += 1

    task.logger.critical(f"DEBUG PARALLEL_ADD: Próxima unidad calculada: {proxima_unidad}")
    if proxima_unidad > task.unidades_a_producir:
        task.logger.warning(f"⚠️ No hay unidades disponibles para nueva instancia en '{task.name}'")
        return None

    id_instancia = str(uuid.uuid4())
    instancia = {
        "id_instancia": id_instancia,
        "trabajadores": [trabajador_id],
        "unidad_actual": proxima_unidad,
        "inicio_unidad": fecha_inicio,
        "evento_fin_programado": None,
    }
    task.logger.critical(
        f"DEBUG PARALLEL_ADD: Creando instancia {id_instancia[:8]} para unidad {proxima_unidad}."
    )
    task.instancias_activas.append(instancia)

    if trabajador_id not in task.trabajadores_asignados:
        task.trabajadores_asignados.append(trabajador_id)

    task.logger.info(
        f"🔀 Instancia paralela {id_instancia[:8]} creada en '{task.name}' "
        f"para trabajador '{trabajador_id}' en unidad {proxima_unidad}"
    )

    from .simulation_events import EventoInicioUnidad

    evento_inicio = EventoInicioUnidad(
        timestamp=fecha_inicio,
        datos={
            "tarea_id": task.id,
            "unidad": proxima_unidad,
            "id_instancia": id_instancia,
            "es_instancia_paralela": True,
        },
    )
    task.logger.critical(
        f"DEBUG PARALLEL_ADD: Programando EventoInicioUnidad para instancia {id_instancia[:8]}, unidad {proxima_unidad}."
    )
    task.eventos_futuros.append(evento_inicio)
    motor_eventos.programar_eventos([evento_inicio])
    return id_instancia


def completar_unidad_instancia_ops(task: Any, id_instancia: str) -> dict[str, Any]:
    """Completa unidad de una instancia y retorna su estado agregado."""
    instancia = next((inst for inst in task.instancias_activas if inst["id_instancia"] == id_instancia), None)
    if not instancia:
        task.logger.error(f"❌ Instancia {id_instancia[:8]} no encontrada en '{task.name}' al completar unidad.")
        return {
            "instancia_completada": False,
            "tarea_completada": (task.unidades_finalizadas_total >= task.unidades_a_producir),
            "siguiente_unidad": None,
            "trabajadores_liberados": [],
        }

    task.unidades_finalizadas_total += 1
    task.unidades_completadas = task.unidades_finalizadas_total
    task.logger.info(
        f"✅ Instancia {id_instancia[:8]} completó unidad {instancia['unidad_actual']} "
        f"de '{task.name}' (Total: {task.unidades_finalizadas_total}/{task.unidades_a_producir})"
    )

    tarea_completada = task.unidades_finalizadas_total >= task.unidades_a_producir
    trabajadores_inst = instancia["trabajadores"].copy()
    task.instancias_activas.remove(instancia)
    task.logger.info(
        f"🔚 Instancia {id_instancia[:8]} eliminada. "
        f"Trabajadores {trabajadores_inst} liberados para decisión del motor."
    )

    if tarea_completada:
        task.logger.info(f"🏁 Tarea '{task.name}' COMPLETADA (alcanzó {task.unidades_finalizadas_total}).")
        return {
            "instancia_completada": True,
            "tarea_completada": True,
            "siguiente_unidad": None,
            "trabajadores_liberados": trabajadores_inst,
        }

    return {
        "instancia_completada": True,
        "tarea_completada": False,
        "siguiente_unidad": None,
        "trabajadores_liberados": trabajadores_inst,
    }

