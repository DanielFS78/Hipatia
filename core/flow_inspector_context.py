# -*- coding: utf-8 -*-
"""
Nombre del Módulo: flow_inspector_context
Descripcion: DTO de vista para enlazar el grafo de flujo con el inspector de tarea
             sin construir mapas intermedios con subindices en el dialogo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FlowInspectorTaskContext:
    """Datos listos para `InspectorPanel.set_task` y listas asociadas."""

    task_canvas_id: Any
    task_body: dict[str, Any]
    task_config: dict[str, Any]
    all_tasks_rows: list[dict[str, Any]]
    workers: list[str]

    def inspector_step_payload(self) -> dict[str, Any]:
        """Formato esperado por el inspector (id + task + config)."""
        return {"id": self.task_canvas_id, "task": self.task_body, "config": self.task_config}
