# -*- coding: utf-8 -*-
"""
Nombre del Módulo: flow_simulation_service
Descripción: Simulación paso a paso de flujos de producción y orden de ejecución de tareas.

Incluye ``SimulationSession`` para avanzar tarea a tarea y ``FlowSimulationService`` para
preparar el orden y datos auxiliares del motor de simulación.
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Set

class SimulationSession:
    """
    Gestiona el estado de una sesión de simulación paso a paso.
    """
    def __init__(self, order: List[int]) -> None:
        self.order = order
        self.current_index = 0

    def next_step(self) -> Optional[int]:
        """
        Avanza al siguiente paso de la simulación.
        
        Returns:
            int or None: El índice de la tarea actual, -1 para indicador visual, 
                         o None si la simulación ha terminado.
        """
        if self.current_index >= len(self.order):
            return None
        
        step = self.order[self.current_index]
        self.current_index += 1
        return step

class FlowSimulationService:
    """
    Servicio encargado de la lógica de simulación y cálculo del orden de ejecución
    para flujos de producción.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("EvolucionTiemposApp")

    def calculate_preview_order(self, canvas_tasks: List[Dict[str, Any]]) -> List[int]:
        """
        Calcula el orden de ejecución teórico basándose en:
        1. Tareas de inicio de ciclo o sin dependencias.
        2. Dependencias directas.
        3. Saltos cíclicos (se indican pero no se siguen recursivamente en preview).

        Args:
            canvas_tasks (list): Lista de diccionarios con la configuración de las tareas
                                 (formato del canvas/diálogo).

        Returns:
            list: Lista de índices en el orden de ejecución teórico.
                  Puede incluir -1 para indicar un salto cíclico visual.
        """
        order: List[int] = []
        visited = set()
        queue = []  # Usaremos una cola para un recorrido más ordenado (BFS-like)

        # Paso 1: Identificar tareas iniciales (inicio de ciclo o sin dependencias)
        initial_tasks = []
        has_cycle_starts = any(task.get('config', {}).get('is_cycle_start', False) for task in canvas_tasks)

        for i, task in enumerate(canvas_tasks):
            is_initial = False
            config = task.get('config', {})
            start_cond = config.get('start_condition', {})

            if has_cycle_starts:
                # Si hay marcadas como inicio de ciclo, esas son las iniciales
                if config.get('is_cycle_start', False):
                    is_initial = True
            else:
                # Si no hay marcadas, las iniciales son las que NO tienen dependencia
                if start_cond.get('type') != 'dependency' or start_cond.get('value') is None:
                    is_initial = True

            if is_initial:
                initial_tasks.append(i)

        # Añadir las tareas iniciales a la cola
        queue.extend(sorted(initial_tasks))  # Ordenar por índice inicial
        visited.update(initial_tasks)

        self.logger.debug(f"Tareas iniciales para preview: {queue}")

        # Paso 2: Procesar la cola hasta que esté vacía
        processed_in_order = []  # Lista para guardar el orden final
        while queue:
            current_idx = queue.pop(0)
            processed_in_order.append(current_idx)

            # Buscar tareas que dependen DIRECTAMENTE de 'current_idx'
            dependents = []
            for i, task in enumerate(canvas_tasks):
                if i not in visited:
                    config = task.get('config', {})
                    start_cond = config.get('start_condition', {})
                    if start_cond.get('type') == 'dependency' and start_cond.get('value') == current_idx:
                        dependents.append(i)

            # Añadir dependientes a la cola (ordenados por su índice original)
            dependents.sort()
            for dep_idx in dependents:
                if dep_idx not in visited:
                    queue.append(dep_idx)
                    visited.add(dep_idx)

            # Verificar salto cíclico desde 'current_idx'
            current_config = canvas_tasks[current_idx].get('config', {})
            cyclic_next = current_config.get('next_cyclic_task_index')
            if cyclic_next is not None and 0 <= cyclic_next < len(canvas_tasks):
                # Indicador visual de ciclo
                # Solo lo añadimos si la tarea destino aún no ha sido procesada en el orden
                # para evitar añadir indicadores redundantes si el ciclo ya se visitó
                if cyclic_next not in processed_in_order and cyclic_next not in queue:
                    processed_in_order.append(-1)  # Indicador visual
                    # Añadir el destino del ciclo a la cola si no está ya visitado
                    if cyclic_next not in visited:
                        queue.append(cyclic_next)
                        visited.add(cyclic_next)
                    self.logger.debug(f"   Salto cíclico detectado: {current_idx} -> {cyclic_next}")

        # Paso 3: Añadir tareas huérfanas (si las hubiera, por si acaso)
        # Esto puede ocurrir si hay dependencias rotas o tareas aisladas
        remaining_tasks = []
        for i in range(len(canvas_tasks)):
            if i not in visited:
                remaining_tasks.append(i)
        remaining_tasks.sort()
        processed_in_order.extend(remaining_tasks)

        return processed_in_order

    def start_simulation(self, canvas_tasks: List[Dict[str, Any]]) -> SimulationSession:
        """
        Inicia una sesión de simulación.

        Args:
            canvas_tasks (list): Lista de tareas del canvas.

        Returns:
            SimulationSession: Objeto de sesión para controlar la simulación.
        """
        order = self.calculate_preview_order(canvas_tasks)
        return SimulationSession(order)

    def identify_last_tasks_in_cycles(self, canvas_tasks: List[Dict[str, Any]]) -> Set[int]:
        """
        Identifica las últimas tareas de cada cadena de ciclo.
        Una tarea es "última" si tiene next_cyclic_task_index pero ninguna otra tarea
        tiene a esta como next_cyclic_task_index (es decir, nadie apunta a ella en el ciclo).

        Args:
            canvas_tasks (list): Lista de tareas del canvas.

        Returns:
            set: Conjunto de índices de tareas que son el último paso de un ciclo.
        """
        last_tasks = set()

        # Encontrar todas las tareas que tienen conexión cíclica saliente
        tasks_with_cyclic_out = set()
        for i, canvas_task in enumerate(canvas_tasks):
            config = canvas_task.get('config', {})
            if config.get('next_cyclic_task_index') is not None:
                tasks_with_cyclic_out.add(i)

        # Para cada tarea con conexión cíclica, verificar si es la última
        for task_idx in tasks_with_cyclic_out:
            is_last = True

            # Verificar si alguna otra tarea apunta a esta
            for other_idx, other_task in enumerate(canvas_tasks):
                if other_idx == task_idx:
                    continue

                other_config = other_task.get('config', {})
                if other_config.get('next_cyclic_task_index') == task_idx:
                    # Otra tarea apunta a esta, no es la última
                    is_last = False
                    break

            if is_last:
                last_tasks.add(task_idx)

        # También incluir tareas marcadas explícitamente como fin de ciclo
        for i, canvas_task in enumerate(canvas_tasks):
            config = canvas_task.get('config', {})
            if config.get('is_cycle_end', False):
                last_tasks.add(i)

        return last_tasks
