# -*- coding: utf-8 -*-
"""
Nombre del Módulo: flow_canvas_io
Descripcion: Lectura tipada de mapas del grafo de flujo (entradas ``canvas_tasks`` del presenter)
             desde capa no-UI, para que los widgets no usen ``.get``/``[]`` en bucles de pintado.
             Expone ``canvas_task_body``, ``flow_task_entry_config``, ``flow_task_entry_widget``,
             normalización de aristas (``CanvasVisualConnection``) y flags de ciclo en ``config``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, MutableMapping, Tuple, Union

from core.dtos import CanvasCyclicConnectionFlags


@dataclass
class CanvasVisualConnection:
    """Arista visual entre dos widgets del canvas de flujo de producción (``ProductionFlowCanvas``)."""

    start: Any
    end: Any
    connection_type: str = "normal"
    is_from_mother: bool = False
    is_to_mother: bool = False


def canvas_visual_connection_from_mapping(m: Mapping[str, Any]) -> CanvasVisualConnection:
    """Construye una conexion visual desde el dict historico start/end/type."""
    t = m.get("type", "normal")
    return CanvasVisualConnection(
        start=m.get("start"),
        end=m.get("end"),
        connection_type=str(t) if t is not None else "normal",
        is_from_mother=bool(m.get("is_from_mother", False)),
        is_to_mother=bool(m.get("is_to_mother", False)),
    )


def normalize_canvas_visual_connections(
    items: Iterable[Union[CanvasVisualConnection, Mapping[str, Any]]],
) -> list[CanvasVisualConnection]:
    """Normaliza entradas dict o DTO a lista homogenea."""
    out: list[CanvasVisualConnection] = []
    for item in items:
        if isinstance(item, CanvasVisualConnection):
            out.append(item)
        else:
            out.append(canvas_visual_connection_from_mapping(item))
    return out


def flow_task_entry_widget(task: Mapping[str, Any]) -> Any:
    """Widget PyQt asociado a una entrada ``canvas_tasks[i]`` (clave ``widget``)."""
    return task.get("widget")


def flow_task_entry_config(task: Mapping[str, Any]) -> Mapping[str, Any]:
    """Subdict ``config`` de una entrada de tarea en el canvas de flujo."""
    raw = task.get("config")
    return raw if isinstance(raw, dict) else {}


def flow_task_entry_is_cycle_start(task: Mapping[str, Any]) -> bool:
    """True si la entrada marca inicio de ciclo en ``config``."""
    return bool(flow_task_entry_config(task).get("is_cycle_start", False))


def canvas_task_body(task: Mapping[str, Any]) -> Any:
    """Cuerpo `data` de una entrada `presenter.canvas_tasks[i]`."""
    return task.get("data")


def canvas_task_display_name(task: Mapping[str, Any], fallback: str) -> str:
    """Nombre de tarea para listas de dialogo (`data` dict o DTO con `.name`)."""
    body = canvas_task_body(task)
    if isinstance(body, Mapping):
        n = body.get("name", fallback)
        return str(n) if n is not None else fallback
    name_attr = getattr(body, "name", None)
    if name_attr is not None:
        return str(name_attr)
    return fallback


def flow_task_config_is_cycle_end_flag(cfg: Mapping[str, Any]) -> bool:
    """True si config marca fin de ciclo."""
    return bool(cfg.get("is_cycle_end", False))


def flow_task_config_is_cycle_start_flag(cfg: Mapping[str, Any]) -> bool:
    """True si config marca inicio de ciclo."""
    return bool(cfg.get("is_cycle_start", False))


def flow_task_config_cycle_return_to_index(cfg: Mapping[str, Any]) -> Any:
    """Índice de tarea a la que regresa el ciclo (clave ``cycle_return_to_index`` en ``config``)."""
    return cfg.get("cycle_return_to_index")


def cycle_end_dialog_configuration_values(cfg: Mapping[str, Any]) -> tuple[Any, Any]:
    """Par (is_cycle_end, return_to_index) del dict de `CycleEndConfigDialog.get_configuration`."""
    return cfg.get("is_cycle_end"), cfg.get("return_to_index")


def worker_line_config_display_name(config: Mapping[str, Any], fallback: str) -> str:
    """Nombre visible de una linea de trabajador en el canvas (clave `name`)."""
    return str(config.get("name", fallback))


def worker_line_config_reassignment_rule(config: Mapping[str, Any]) -> Any:
    """Regla de reasignacion asociada a la linea de trabajador, si existe."""
    return config.get("reassignment_rule")


def worker_line_config_set_reassignment_rule(config: MutableMapping[str, Any], rule: Any) -> None:
    """Persiste la regla de reasignacion en la config mutable de la linea."""
    config["reassignment_rule"] = rule


def connection_widgets_pair(conn: Mapping[str, Any] | CanvasVisualConnection) -> Tuple[Any, Any]:
    """Devuelve (start, end) tal como los guarda el modelo de conexiones del canvas."""
    if isinstance(conn, CanvasVisualConnection):
        return conn.start, conn.end
    return conn.get("start"), conn.get("end")


def connection_link_type(conn: Mapping[str, Any] | CanvasVisualConnection) -> str:
    """Tipo de arista: 'normal' o 'cyclic'."""
    if isinstance(conn, CanvasVisualConnection):
        return conn.connection_type
    t = conn.get("type", "normal")
    return str(t) if t is not None else "normal"


def connection_cyclic_paint_flags(
    conn: Mapping[str, Any] | CanvasVisualConnection,
) -> CanvasCyclicConnectionFlags:
    """Flags de pintado para aristas cíclicas (mapeo serializable o ``CanvasVisualConnection``)."""
    if isinstance(conn, CanvasVisualConnection):
        return CanvasCyclicConnectionFlags(
            is_from_mother=conn.is_from_mother,
            is_to_mother=conn.is_to_mother,
        )
    return CanvasCyclicConnectionFlags.from_connection_mapping(conn)
