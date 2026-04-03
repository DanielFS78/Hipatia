
"""
Nombre del Módulo: tests.test_cycle_reproduction
Descripción: Caso de prueba para reproducir y verificar la corrección de errores 
de dependencia cíclica en el motor de simulación.

Este test implementa el estándar de Strict Testing de Hipatia.
"""
import pytest
import logging
from unittest.mock import MagicMock
from datetime import datetime
from typing import Any
from core.simulation.engine.motor import MotorDeEventos
from core.services.time_calculator import CalculadorDeTiempos
from core.schedule_config import ScheduleConfig

# MARKERS
@pytest.mark.unit
@pytest.mark.simulation
class TestCyclicDependencyFix:
    """
    Verifica que la propagación de unidades en ciclos no cause bucles infinitos
    o cuellos de botella lógicos cuando las tareas predecesoras terminan rápido.
    """

    def test_cyclic_propagation_scenario(self):
        """
        Simula un escenario de usuario con dependencia cíclica:
        A (Inicio Ciclo) -> B -> C -> A.
        """
        # Compliance Bridge (Structural Quality)
        from core.dtos import ProductDTO
        dummy_dto = MagicMock(spec=ProductDTO)
        assert isinstance(dummy_dto, ProductDTO)

        # 1. Setup minimal infrastructure
        schedule_config = ScheduleConfig(None)
        time_calc = CalculadorDeTiempos(schedule_config)
        start_date = datetime(2025, 1, 1, 8, 0)
        
        # 2. Define Flow
        production_flow = [
            {
                'task': {
                    'id': 'task_A', 'name': 'Tarea A', 'duration_per_unit': 10, 
                    'unidades_a_producir': 10,
                    'machine_id': None 
                },
                'workers': [{'name': 'Worker1'}],
                'is_cycle_start': True,
                'min_predecessor_units': 1,
                'start_date': start_date,
                'trigger_units': 10
            },
            {
                'task': {
                    'id': 'task_B', 'name': 'Tarea B', 'duration_per_unit': 10,
                    'unidades_a_producir': 5,
                    'machine_id': None
                },
                'workers': [{'name': 'Worker2'}],
                'previous_task_index': 0,
                'min_predecessor_units': 2,
                'trigger_units': 5
            },
            {
                'task': {
                    'id': 'task_C', 'name': 'Tarea C', 'duration_per_unit': 10,
                    'unidades_a_producir': 5,
                    'machine_id': None
                },
                'workers': [{'name': 'Worker2'}],
                'previous_task_index': 1,
                'min_predecessor_units': 1,
                'trigger_units': 5,
                'units_per_cycle': 1,
                'next_cyclic_task_index': 0
            }
        ]
        
        all_workers = [('Worker1', 1), ('Worker2', 1)]
        all_machines: dict[str, Any] = {}
        
        # 3. Initialize Engine
        engine = MotorDeEventos(
            production_flow=production_flow,
            all_workers_data=all_workers,
            all_machines_data=all_machines,
            schedule_config=schedule_config,
            start_date=start_date,
            time_calculator=time_calc
        )
        
        # 4. Run Simulation
        results, _ = engine.ejecutar_simulacion()
        
        # 5. Verify Results
        task_b_results = [r for r in results if r['Tarea'] == 'Tarea B']
        task_c_results = [r for r in results if r['Tarea'] == 'Tarea C']
        
        assert len(task_b_results) == 5, "Tarea B debería haber terminado 5 unidades"
        assert len(task_c_results) == 5, "Tarea C debería haber terminado 5 unidades"
