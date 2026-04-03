# -*- coding: utf-8 -*-
"""
Lógica o utilidades del núcleo (`flow_builder_service`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

import copy
import logging
from typing import List, Dict, Any, Optional

class FlowBuilderService:
    """
    Service responsible for constructing and refining production flows.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("EvolucionTiemposApp")

    def build_flow_from_override(self, production_flow_override: List[Dict[str, Any]], units: int) -> List[Dict[str, Any]]:
        """
        Creates a production flow from an override (e.g., from Visual Editor),
        updating units for each step.
        """
        if not production_flow_override:
            return []

        production_flow = copy.deepcopy(production_flow_override)
        for step in production_flow:
            step['trigger_units'] = units
        return production_flow

    def resolve_worker_assignments(self, production_flow: List[Dict[str, Any]], available_workers_sorted: List[Any]) -> List[Dict[str, Any]]:
        """
        Assigns default workers to steps that don't have them, based on skill level.
        
        Args:
            production_flow: The list of flow steps.
            available_workers_sorted: List of worker objects, ideally sorted by skill level (descending).
            
        Returns:
            The modified production flow with workers assigned where possible.
        """
        for step in production_flow:
            # Check if workers are already assigned
            workers_in_step = step.get('workers')
            if not workers_in_step:
                task_data = step.get('task', {})
                required_skill = task_data.get('required_skill_level', 1)
                
                assigned_worker = None
                # Try to find the first worker who meets the skill requirement
                for worker in available_workers_sorted:
                    # Assuming worker object has 'tipo_trabajador' and 'nombre_completo'
                    # We use duck typing here or could strict type with a Protocol if needed
                    if getattr(worker, 'tipo_trabajador', 0) >= required_skill:
                        assigned_worker = worker
                        break
                        
                if assigned_worker:
                    step['workers'] = [{'name': getattr(assigned_worker, 'nombre_completo', 'Unknown')}]
                else:
                    self.logger.warning(f"No suitable worker found for task '{task_data.get('name')}' (Skill: {required_skill})")
                    step['workers'] = []
                    
        return production_flow
