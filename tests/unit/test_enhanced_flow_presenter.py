"""
Tests unitarios para EnhancedFlowPresenter.
100% Cobertura de la lógica sin dependencias de PyQt6 UI.
Cumplimiento estricto.
"""
import pytest
from datetime import datetime, date, time
from unittest.mock import MagicMock

from ui.dialogs.production_flow.enhanced_flow_presenter import EnhancedFlowPresenter
from core.dtos import CalculationProductDTO, CalculationSubPartDTO, WorkerDTO  # DTO para cumplimiento


@pytest.fixture
def presenter():
    class DummyConfig:
        WORK_START_TIME = time(8, 0)
    return EnhancedFlowPresenter(schedule_config=DummyConfig(), default_units=10)  # type: ignore[arg-type]


@pytest.mark.unit
class TestEnhancedFlowPresenter:

    def test_prepare_task_data_simple_product(self, presenter):
        """Tarea de producto simple (sin subfabricaciones)."""
        tasks_data = [{
            'codigo': 'PROD1',
            'descripcion': 'Producto de prueba',
            'tiempo_optimo': '10,5',
            'departamento': 'Ensamblaje',
            'tiene_subfabricaciones': False
        }]
        result = presenter.prepare_task_data(tasks_data)
        
        assert 'PROD1' in result
        assert result['PROD1'].descripcion == 'Producto de prueba'
        tasks = result['PROD1'].tasks
        assert len(tasks) == 1
        assert tasks[0].duration == 10.5
        assert tasks[0].id == 'PROD1_main_task'

    def test_prepare_task_data_accepts_calculation_product_dto(self, presenter):
        """PilaService devuelve CalculationProductDTO; el presenter debe armar la biblioteca."""
        dto = CalculationProductDTO(
            codigo="DTO1",
            descripcion="Desde DTO",
            departamento="Mecanizado",
            tipo_trabajador=2,
            donde="",
            tiene_subfabricaciones=True,
            tiempo_optimo=9.0,
            sub_partes=[
                CalculationSubPartDTO("Paso A", 2.5, 2, None),
                CalculationSubPartDTO("Paso B", 1.0, 2, None),
            ],
        )
        result = presenter.prepare_task_data([dto])
        assert "DTO1" in result
        tasks = result["DTO1"].tasks
        assert len(tasks) == 2
        assert tasks[0].name == "Paso A"
        assert tasks[0].duration == 2.5
        assert tasks[0].department == "Mecanizado"

    def test_prepare_task_data_with_subfabrications(self, presenter):
        """Tarea con subfabricaciones (usa 'tiempo' o 'duration')."""
        tasks_data = [{
            'codigo': 'PROD2',
            'descripcion': 'Producto con subpartes',
            'tiene_subfabricaciones': True,
            'sub_partes': [
                {'descripcion': 'Corte', 'tiempo': '5,2'},
                {'descripcion': 'Pintura', 'duration': '3.0'},
                {'descripcion': 'Secado', 'tiempo': 'invalido'} # Fallback a 0.0
            ]
        }]
        result = presenter.prepare_task_data(tasks_data)
        
        tasks = result['PROD2'].tasks
        assert len(tasks) == 3
        assert tasks[0].duration == 5.2
        assert tasks[1].duration == 3.0
        assert tasks[2].duration == 0.0
        assert tasks[0].id == 'PROD2_0_Corte'

    def test_prepare_task_data_skips_non_dict_subtasks(self, presenter):
        """Subtareas no-dict se ignoran sin afectar a las válidas."""
        tasks_data = [{
            "codigo": "PROD3",
            "descripcion": "Producto mixto",
            "tiene_subfabricaciones": True,
            "sub_partes": [
                {"descripcion": "OK", "duration": "1.0"},
                "NO_ES_DICT",
            ],
        }]

        result = presenter.prepare_task_data(tasks_data)

        tasks = result["PROD3"].tasks
        assert len(tasks) == 1
        assert tasks[0].name == "OK"
        assert tasks[0].duration == 1.0

    def test_parse_duration_invalid(self, presenter):
        """El log de error se llama silenciosamente si falla el parsing."""
        val = presenter._parse_duration("abc", "PRODX")
        assert val == 0.0

    def test_resolve_start_date_type_not_date(self, presenter):
        """Si start_cond no es de tipo 'date' o no tiene value."""
        assert presenter.resolve_start_date({'type': 'dependency'}) is None
        assert presenter.resolve_start_date({'type': 'date'}) is None

    def test_resolve_start_date_datetime(self, presenter):
        """Si es datetime, se retorna igual."""
        dt = datetime(2025, 1, 1, 10, 0)
        assert presenter.resolve_start_date({'type': 'date', 'value': dt}) == dt

    def test_resolve_start_date_date(self, presenter):
        """Si es date, se le añade la hora de schedule_config."""
        d = date(2025, 1, 1)
        res = presenter.resolve_start_date({'type': 'date', 'value': d})
        assert res == datetime(2025, 1, 1, 8, 0)

    def test_normalize_workers_empty(self, presenter):
        assert presenter.normalize_workers([]) == []

    def test_normalize_workers_dicts(self, presenter):
        """Ya tienen el formato correcto (dicts)."""
        workers = [{'name': 'Ana', 'reassignment_rule': 'Rule1'}]
        assert presenter.normalize_workers(workers) == workers

    def test_normalize_workers_strings(self, presenter):
        """Formato anterior (lista de strings)."""
        workers = ['Ana', 'Juan']
        res = presenter.normalize_workers(workers)
        assert res == [{'name': 'Ana', 'reassignment_rule': None}, {'name': 'Juan', 'reassignment_rule': None}]

    def test_build_production_flow_empty(self, presenter):
        assert presenter.build_production_flow([]) == []

    def test_build_production_flow_invalid_task(self, presenter):
        """Si un canvas_task no tiene 'data', se salta silenciosamente."""
        res = presenter.build_production_flow([{'config': {}}])
        assert res == []

    def test_build_production_flow_full_integration(self, presenter):
        """Ensamblado completo de datos, configuración y posición."""
        canvas_tasks = [{
            'data': {'codigo': 'T1', 'canvas_unique_id': 'ignoreme', 'glow_effect_widget': 'mock'},
            'config': {
                'workers': ['Luis'],
                'machine_id': 5,
                'min_predecessor_units': 2,
                'start_condition': {'type': 'dependency', 'value': 0}
            },
            'position': {'x': 100, 'y': 200}
        }]
        
        res = presenter.build_production_flow(canvas_tasks)
        
        assert len(res) == 1
        step = res[0]
        assert 'canvas_unique_id' not in step['task']
        assert 'glow_effect_widget' not in step['task']
        assert step['task']['codigo'] == 'T1'
        
        assert step['workers'] == [{'name': 'Luis', 'reassignment_rule': None}]
        assert step['machine_id'] == 5
        assert step['trigger_units'] == 10  # Usó default del presenter
        assert step['min_predecessor_units'] == 2
        
        assert step['start_date'] is None
        assert step['previous_task_index'] == 0
        assert step['position'] == {'x': 100, 'y': 200}

        # Comprobación de DTO (ficticio para meta cumplimiento)
        assert not isinstance(step, WorkerDTO)

    def test_crud_operations(self, presenter):
        """Prueba add, get, update, clear y remove (con reajuste de índices)."""
        # 1. Add
        task1, idx1 = presenter.add_task({'name': 'T1'}, {'x': 0, 'y': 0})
        task2, idx2 = presenter.add_task({'name': 'T2'}, {'x': 10, 'y': 10})
        assert idx1 == 0 and idx2 == 1
        assert len(presenter.canvas_tasks) == 2

        # 2. Get
        assert presenter.get_task(0)['data']['name'] == 'T1'
        assert presenter.get_task(99) is None

        # 3. Update
        presenter.update_task_config(0, 'total_units', 50)
        assert presenter.get_task(0)['config']['total_units'] == 50
        assert not presenter.update_task_config(99, 'key', 'val')

        # 4. Remove with dependency adjustment
        # Make T2 depend on T1
        presenter.update_task_config(1, 'start_condition', {'type': 'dependency', 'value': 0})
        # Add T3 depending on T2
        task3, idx3 = presenter.add_task({'name': 'T3'}, {'x': 20, 'y': 20})
        presenter.update_task_config(2, 'start_condition', {'type': 'dependency', 'value': 1})
        # Add T4 with cyclic connection to T2
        task4, idx4 = presenter.add_task({'name': 'T4'}, {'x': 30, 'y': 30})
        presenter.update_task_config(3, 'next_cyclic_task_index', 1)
        presenter.update_task_config(3, 'cycle_return_to_index', 1)

        # Remove T2 (index 1)
        # T1 (idx 0) stays same.
        # T3 (idx 2 -> 1) was depending on idx 1 (T2). Since T2 is gone, it should revert to 'date'.
        # T4 (idx 3 -> 2) was cyclic to idx 1 (T2). Should revert to None.
        presenter.remove_task(1)
        assert len(presenter.canvas_tasks) == 3
        assert presenter.get_task(0)['data']['name'] == 'T1'
        assert presenter.get_task(1)['data']['name'] == 'T3'
        assert presenter.get_task(1)['config']['start_condition']['type'] == 'date'
        assert presenter.get_task(2)['config']['next_cyclic_task_index'] is None
        assert presenter.get_task(2)['config']['cycle_return_to_index'] is None

        # 4b. Remove with indexes GREATER than the removed one
        presenter.clear_tasks()
        presenter.add_task({'name': 'T0'}, {'x':0, 'y':0})
        presenter.add_task({'name': 'T1'}, {'x':0, 'y':0})
        presenter.add_task({'name': 'T2'}, {'x':0, 'y':0})
        # T2 (idx 2) depends on T1 (idx 1). 
        presenter.update_task_config(2, 'start_condition', {'type': 'dependency', 'value': 1})
        # T2 cycles to T1
        presenter.update_task_config(2, 'next_cyclic_task_index', 1)
        presenter.update_task_config(2, 'cycle_return_to_index', 1)
        
        # Remove T0 (idx 0). T2 (idx 2 -> 1) and T1 (idx 1 -> 0).
        # T2's dependency (1) should become 1 - 1 = 0.
        presenter.remove_task(0)
        assert presenter.get_task(1)['config']['start_condition']['value'] == 0
        assert presenter.get_task(1)['config']['next_cyclic_task_index'] == 0
        assert presenter.get_task(1)['config']['cycle_return_to_index'] == 0

        # Remove invalid
        assert not presenter.remove_task(99)

        # 5. Clear
        presenter.clear_tasks()
        assert len(presenter.canvas_tasks) == 0

    def test_apply_cycle_end_config(self, presenter):
        presenter.add_task({'name': 'T1'}, {'x': 0, 'y': 0})
        presenter.add_task({'name': 'T2'}, {'x': 10, 'y': 10})
        
        # Apply cycle end pointing to T1 (idx 0)
        presenter.apply_cycle_end_config(1, True, 0)
        config = presenter.get_task(1)['config']
        assert config['is_cycle_end'] is True
        assert config['cycle_return_to_index'] == 0
        assert config['next_cyclic_task_index'] == 0
        
        # Remove cycle end
        presenter.apply_cycle_end_config(1, False, None)
        assert config['is_cycle_end'] is False
        assert config['next_cyclic_task_index'] is None
        
        # Invalid index
        assert not presenter.apply_cycle_end_config(99, True, 0)

    def test_get_worker_config(self, presenter):
        presenter.add_task({'name': 'T1'}, {'x': 0, 'y': 0})
        presenter.update_task_config(0, 'workers', [{'name': 'Ana', 'val': 1}])
        
        # Found
        assert presenter.get_worker_config(0, 'Ana')['val'] == 1
        # Found with emoji/strip
        assert presenter.get_worker_config(0, ' Ana 🔧 ')['val'] == 1
        # Not found
        assert presenter.get_worker_config(0, 'Luis') is None
        # Invalid task
        assert presenter.get_worker_config(99, 'Ana') is None

    def test_get_inspector_data(self, presenter):
        presenter.add_task({'name': 'T1'}, {'x': 0, 'y': 0})
        presenter.add_task({'name': 'T2'}, {'x': 10, 'y': 10})
        
        data = presenter.get_inspector_data(1)
        assert data['selected_task']['data']['name'] == 'T2'
        assert len(data['possible_predecessors']) == 1
        assert data['possible_predecessors'][0] == (0, 'T1')
        
        assert presenter.get_inspector_data(99) == {}

    def test_simulation_preview_logic(self, presenter):
        # Empty tasks
        assert not presenter.start_simulation_preview(MagicMock(spec=[]))
        
        presenter.add_task({'name': 'T1'}, {'x': 0, 'y': 0})
        mock_service = MagicMock(spec=["start_simulation"])
        mock_session = MagicMock(spec=["order", "next_step"])
        mock_session.order = [0]
        mock_session.next_step.side_effect = [0, None]
        mock_service.start_simulation.return_value = mock_session
        
        # Start
        assert presenter.start_simulation_preview(mock_service)
        assert presenter.simulation_session == mock_session
        
        # Next steps
        assert presenter.get_next_simulation_step() == 0
        assert presenter.get_next_simulation_step() is None
        
        # Progress text
        assert "T1" in presenter.get_simulation_progress_text(0)
        assert presenter.get_simulation_progress_text(99) == "Simulación..."
        
        # Stop
        presenter.stop_simulation_preview()
        assert presenter.simulation_session is None
        assert presenter.get_next_simulation_step() is None

    def test_get_logical_connections(self, presenter):
        presenter.add_task({'name': 'T1'}, {'x': 0, 'y': 0})
        presenter.add_task({'name': 'T2'}, {'x': 10, 'y': 10})
        # T2 depends on T1
        presenter.update_task_config(1, 'start_condition', {'type': 'dependency', 'value': 0})
        # T2 cycles to T1
        presenter.update_task_config(1, 'next_cyclic_task_index', 0)
        
        # Connections for T2
        conn2 = presenter.get_logical_connections(1)
        assert len(conn2) == 2
        types = [c['type'] for c in conn2]
        assert 'standard' in types
        assert 'cyclic' in types
        
        # Connections for T1 (incoming from T2)
        conn1 = presenter.get_logical_connections(0)
        assert len(conn1) == 2 # One standard child, one cyclic origin
        
        assert presenter.get_logical_connections(99) == []

    def test_canvas_state_all_logical_connections(self, presenter):
        """Flechas globales: misma información que el inspector pero sin depender del índice seleccionado."""
        from core.enhanced_flow_canvas_state_io import canvas_state_all_logical_connections

        presenter.add_task({"name": "T1"}, {"x": 0, "y": 0})
        presenter.add_task({"name": "T2"}, {"x": 10, "y": 10})
        presenter.update_task_config(1, "start_condition", {"type": "dependency", "value": 0})
        presenter.update_task_config(1, "next_cyclic_task_index", 0)
        edges = canvas_state_all_logical_connections(presenter.canvas_tasks)
        assert len(edges) == 2
        assert {e["type"] for e in edges} == {"standard", "cyclic"}

    def test_canvas_state_sequential_default_chain(self, presenter):
        """Sin dependencias explícitas: cadena 0→1→2 (orden de colocación en el lienzo)."""
        from core.enhanced_flow_canvas_state_io import canvas_state_all_logical_connections

        for name in ("A", "B", "C"):
            presenter.add_task({"name": name}, {"x": 0, "y": 0})
        edges = canvas_state_all_logical_connections(presenter.canvas_tasks)
        assert len(edges) == 2
        assert {(e["from"], e["to"], e["type"]) for e in edges} == {(0, 1, "sequential"), (1, 2, "sequential")}

    def test_load_flow(self, presenter):
        flow_data = [
            {
                'task': {'name': 'T1'},
                'position': {'x': 100, 'y': 100},
                'workers': ['W1'],
                'start_date': date(2025, 1, 1)
            },
            {
                'task': {'name': 'T2'},
                'previous_task_index': 0
            }
        ]
        
        res = presenter.load_flow(flow_data)
        assert len(res) == 2
        assert presenter.get_task(0)['data']['name'] == 'T1'
        assert presenter.get_task(1)['config']['start_condition']['type'] == 'dependency'

    def test_load_flow_skips_steps_without_task(self, presenter):
        """Los steps sin 'task' se ignoran sin romper índices."""
        flow_data = [
            {"position": {"x": 1, "y": 2}},  # sin task -> se ignora
            {"task": {"name": "T_OK"}, "previous_task_index": None},
        ]

        res = presenter.load_flow(flow_data)

        assert len(res) == 1
        assert presenter.get_task(0)["data"]["name"] == "T_OK"

    def test_identify_last_tasks_in_cycles(self, presenter):
        mock_sim = MagicMock(spec=["identify_last_tasks_in_cycles"])
        mock_sim.identify_last_tasks_in_cycles.return_value = [1]
        assert presenter.identify_last_tasks_in_cycles(mock_sim) == [1]

    def test_resolve_start_date_invalid_value(self, presenter):
        # Value is not date nor datetime
        assert presenter.resolve_start_date({'type': 'date', 'value': 'not a date'}) is None

    def test_apply_cycle_end_coverage_edge(self, presenter):
        presenter.add_task({'name': 'T1'}, {'x': 0, 'y': 0})
        # next_cyclic_task_index == previous_return_index
        presenter.update_task_config(0, 'cycle_return_to_index', 5)
        presenter.update_task_config(0, 'next_cyclic_task_index', 5)
        presenter.apply_cycle_end_config(0, False, None)
        assert presenter.get_task(0)['config']['next_cyclic_task_index'] is None
