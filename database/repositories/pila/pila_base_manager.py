
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: pila.pila_base_manager
Descripción: Persistencia y consultas de pilas, lotes, bitácora y flujo de trabajo de fabricación.
"""

import uuid
from typing import Any, List
from ..base import BaseRepository

class PilaBaseManager(BaseRepository):
    """Gestor de utilidades base para el dominio de Pilas (serialización de flujos)."""

    def convert_indices_to_ids(self, production_flow: List[Any]) -> None:
        """Convierte índices relativos en IDs únicos persistentes para el flujo."""
        index_to_id_map = {}
        for i, step in enumerate(production_flow):
            if 'unique_id' not in step or not step['unique_id']:
                step['unique_id'] = str(uuid.uuid4())
            index_to_id_map[i] = step['unique_id']
        for step in production_flow:
            if 'previous_task_index' in step and step['previous_task_index'] is not None:
                idx = step.get('previous_task_index')
                if idx in index_to_id_map: step['previous_task_id'] = index_to_id_map[idx]
                del step['previous_task_index']
            if 'next_cyclic_task_index' in step and step['next_cyclic_task_index'] is not None:
                idx = step.get('next_cyclic_task_index')
                if idx in index_to_id_map: step['next_cyclic_task_id'] = index_to_id_map[idx]
                del step['next_cyclic_task_index']

    def convert_ids_to_indices(self, production_flow: List[Any]) -> None:
        """Reconvierte IDs persistentes en índices relativos para uso en memoria/UI."""
        id_to_index_map = {step.get('unique_id'): i for i, step in enumerate(production_flow) if step.get('unique_id')}
        for step in production_flow:
            if 'previous_task_id' in step and step['previous_task_id'] is not None:
                step['previous_task_index'] = id_to_index_map.get(step['previous_task_id'])
                del step['previous_task_id']
            if 'next_cyclic_task_id' in step and step['next_cyclic_task_id'] is not None:
                step['next_cyclic_task_index'] = id_to_index_map.get(step['next_cyclic_task_id'])
                del step['next_cyclic_task_id']
            if 'unique_id' in step: del step['unique_id']
