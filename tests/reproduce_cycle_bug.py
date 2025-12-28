
import logging
import unittest
from datetime import datetime, timedelta
from event_engine import MotorDeEventos
from time_calculator import CalculadorDeTiempos
from schedule_config import ScheduleConfig

# Configure simple logging
logging.basicConfig(level=logging.INFO)

class TestCyclicDependencyFix(unittest.TestCase):
    def test_cyclic_propagation_scenario(self):
        """
        Simulates the user scenario:
        - Task A: 10 units, Cycle start.
        - Task B: Depends on A (needs 9 units of A to start).
        - Task C: Depends on B.
        - Cycle: C -> A.
        
        The critical part is that A finishes its 10 units quickly.
        B waits for 9 units of A.
        When B finally starts and finishes 1 unit, it triggers C.
        C finishes 1 unit and triggers A (Cycle).
        BUT A IS ALREADY DONE with its 10 units.
        
        Logic should propagate: C -> A references -> B.
        B should realize it has more units to do and can start because A provided enough stock (10 > 9).
        """
        
        # 1. Setup minimal infrastructure
        schedule_config = ScheduleConfig(None)
        time_calc = CalculadorDeTiempos(schedule_config)
        start_date = datetime(2025, 1, 1, 8, 0)
        
        # 2. Define Flow
        # Task 0: A -- 10 units total.
        # Task 1: B -- 10 units total. Depends on A (9 units).
        # Task 2: C -- 10 units total. Depends on B. Cycle -> 0 (A)
        
        production_flow = [
            # Tarea A [0]
            {
                'task': {
                    'id': 'task_A', 'name': 'Tarea A', 'duration_per_unit': 10, 
                    'unidades_a_producir': 10, # Make it 10 for speed, scenario said 100 but logic holds
                    'machine_id': None 
                },
                'workers': [{'name': 'Worker1'}],
                'is_cycle_start': True,
                'min_predecessor_units': 1,
                'start_date': start_date, # Ensure reference date exists
                'trigger_units': 10
            },
            # Tarea B [1]
            {
                'task': {
                    'id': 'task_B', 'name': 'Tarea B', 'duration_per_unit': 10,
                    'unidades_a_producir': 5, # Can produce max 5 (10/2)
                    'machine_id': None
                },
                'workers': [{'name': 'Worker2'}],
                'previous_task_index': 0, # Depends on A
                'min_predecessor_units': 2, # Requires 2 A per 1 B
                'trigger_units': 5
            },
             # Tarea C [2]
            {
                'task': {
                    'id': 'task_C', 'name': 'Tarea C', 'duration_per_unit': 10,
                    'unidades_a_producir': 5,
                    'machine_id': None
                },
                'workers': [{'name': 'Worker2'}], # Same worker as B to force serialization if needed, or diff
                'previous_task_index': 1, # Depends on B
                'min_predecessor_units': 1,
                'trigger_units': 5,
                
                # Cycle config
                'units_per_cycle': 1,
                'next_cyclic_task_index': 0 # Back to A
            }
        ]
        
        # Workers
        all_workers = [('Worker1', 1), ('Worker2', 1)]
        all_machines = {}
        
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
        results, audit = engine.ejecutar_simulacion()
        
        # 5. Verify Results
        # Check that Task B and C finished ALL their units.
        
        task_b_results = [r for r in results if r['Tarea'] == 'Tarea B']
        task_c_results = [r for r in results if r['Tarea'] == 'Tarea C']
        
        print(f"Task B count: {len(task_b_results)}")
        print(f"Task C count: {len(task_c_results)}")
        
        self.assertEqual(len(task_b_results), 5, "Tarea B should have finished 5 units")
        self.assertEqual(len(task_c_results), 5, "Tarea C should have finished 5 units")
        
if __name__ == '__main__':
    unittest.main()
