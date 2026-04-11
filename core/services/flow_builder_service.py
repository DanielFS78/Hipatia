# -*- coding: utf-8 -*-
"""
Nombre del Módulo: flow_builder_service
Descripción: Construcción y ajuste de listas de pasos de flujo de producción (dict en memoria).

Aplica unidades de disparo, copia profunda de overrides del editor visual y asignación
heurística de trabajadores por nivel de habilidad requerido en la tarea.
"""

import copy
import logging
from typing import List, Dict, Any, Optional

class FlowBuilderService:
    """
    Construye y refina flujos de producción antes de simulación o persistencia.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("EvolucionTiemposApp")

    def build_flow_from_override(self, production_flow_override: List[Dict[str, Any]], units: int) -> List[Dict[str, Any]]:
        """
        Clona el flujo definido por el usuario (p. ej. editor) y fija ``trigger_units`` en cada paso.

        Args:
            production_flow_override: Secuencia de pasos con tareas y metadatos.
            units: Unidades de disparo a aplicar a cada paso.

        Returns:
            Lista nueva de pasos o lista vacía si no hay override.
        """
        if not production_flow_override:
            return []

        production_flow = copy.deepcopy(production_flow_override)
        for step in production_flow:
            step['trigger_units'] = units
        return production_flow

    def resolve_worker_assignments(self, production_flow: List[Dict[str, Any]], available_workers_sorted: List[Any]) -> List[Dict[str, Any]]:
        """
        Rellena ``workers`` en pasos vacíos eligiendo el primer operario que cumple el nivel requerido.

        Args:
            production_flow: Pasos del flujo; se mutan entradas sin trabajadores asignados.
            available_workers_sorted: Candidatos ordenados (p. ej. de mayor a menor habilidad).

        Returns:
            El mismo flujo con listas ``workers`` rellenadas o vacías si no hay candidato.
        """
        for step in production_flow:
            workers_in_step = step.get('workers')
            if not workers_in_step:
                task_data = step.get('task', {})
                required_skill = task_data.get('required_skill_level', 1)
                
                assigned_worker = None
                for worker in available_workers_sorted:
                    if getattr(worker, 'tipo_trabajador', 0) >= required_skill:
                        assigned_worker = worker
                        break
                        
                if assigned_worker:
                    step['workers'] = [{'name': getattr(assigned_worker, 'nombre_completo', 'Unknown')}]
                else:
                    self.logger.warning(f"No suitable worker found for task '{task_data.get('name')}' (Skill: {required_skill})")
                    step['workers'] = []
                    
        return production_flow
