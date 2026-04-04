# -*- coding: utf-8 -*-
"""Tests unitarios para DefineFlowPresenter: prepare_task_data, group_tasks, CRUD, model queries."""
import pytest
from unittest.mock import MagicMock, create_autospec
from ui.dialogs.production_flow.define_flow_presenter import DefineFlowPresenter
from core.dtos import FlowTaskDataDTO, FlowTaskConfigDTO, ProductionFlowStepDTO, FlowItemDTO
from datetime import date

pytestmark = pytest.mark.unit


from core.app_model import AppModel
from core.schedule_config import ScheduleConfig
from unittest.mock import call

pytestmark = pytest.mark.unit


class DummyPainter:
    def setPen(self, *args): pass
    def drawLine(self, *args): pass
    def setBrush(self, *args): pass
    def drawEllipse(self, *args): pass
    def drawPolygon(self, *args): pass

class DummyColor:
    def red(self): return 0
    def green(self): return 0
    def blue(self): return 0
    def alpha(self): return 255


@pytest.fixture
def presenter():
    mock_config = create_autospec(ScheduleConfig, instance=True)
    mock_config.WORK_START_TIME = None
    return DefineFlowPresenter(schedule_config=mock_config, default_units=10)

@pytest.mark.unit
class TestDefineFlowPresenter:

    def test_init(self, presenter):
        assert presenter.default_units == 10
        assert presenter.get_production_flow() == []
        assert presenter.model is None

    def test_prepare_task_data_simple(self, presenter):
        tasks_data = [{
            'codigo': 'PROD1',
            'descripcion': 'Producto simple',
            'tiene_subfabricaciones': False
        }]
        result = presenter.prepare_task_data(tasks_data)
        assert 'PROD1' in result
        assert result['PROD1'].descripcion == 'Producto simple'
        assert len(result['PROD1'].tasks) == 0

    def test_prepare_task_data_with_subfabrications(self, presenter):
        tasks_data = [{
            'codigo': 'P1',
            'descripcion': 'Main',
            'tiene_subfabricaciones': True,
            'sub_partes': [
                {'name': 'Tarea 1', 'tiempo': '5,5'},
                {'name': 'Tarea 2', 'duration': 'invalid'},
                {'name': 'Tarea 3'}
            ]
        }]
        result = presenter.prepare_task_data(tasks_data)
        tasks = result['P1'].tasks
        assert len(tasks) == 3
        assert tasks[0].duration == 5.5
        assert tasks[1].duration == 0.0
        assert tasks[2].duration == 0.0

    def test_group_tasks_validation(self, presenter):
        task_0 = FlowTaskDataDTO(id="T0", name="T0", duration=1.0, duration_per_unit=1.0, department="Gen")
        step_0 = ProductionFlowStepDTO(task=task_0, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date"))
        presenter.set_production_flow([step_0])
        with pytest.raises(ValueError, match="Se requieren al menos 2 tareas"):
            presenter.group_tasks([0], [], 1, 10)
        assert presenter.get_production_flow() == [step_0]
            
        task_1 = FlowTaskDataDTO(id="T1", name="T1", duration=1.0, duration_per_unit=1.0, department="Gen")
        task_2 = FlowTaskDataDTO(id="T2", name="T2", duration=1.0, duration_per_unit=1.0, department="Gen")
        presenter.set_production_flow([
            step_0,
            ProductionFlowStepDTO(task=task_1, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date")),
            ProductionFlowStepDTO(task=task_2, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date"))
        ])
        with pytest.raises(ValueError, match="consecutivas"):
            presenter.group_tasks([0, 2], [], 1, 10)
        assert len(presenter.get_production_flow()) == 3

    def test_group_tasks_success(self, presenter):
        tasks = [
            FlowTaskDataDTO(id='T0', name='T0', duration=1.0, duration_per_unit=1.0, department='A'),
            FlowTaskDataDTO(id='T1', name='T1', duration=2.0, duration_per_unit=2.0, department='B'),
            FlowTaskDataDTO(id='T2', name='T2', duration=3.0, duration_per_unit=3.0, department='B'),
            FlowTaskDataDTO(id='T3', name='T3', duration=1.0, duration_per_unit=1.0, department='C')
        ]
        presenter.set_production_flow([
            ProductionFlowStepDTO(task=t, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date"))
            for t in tasks
        ])
        # Configurar dependencia manual para T3
        presenter.get_step(3).config.previous_task_index = 2
        presenter.get_step(3).config.start_condition_type = "dependency"
        
        # Agrupamos T1 y T2 (índices 1 y 2)
        new_flow = presenter.group_tasks(
            selected_indices=[1, 2],
            selected_workers=["W1"],
            units_per_cycle=5,
            total_units=10
        )
        
        assert len(new_flow) == 3
        assert new_flow[0].task.id == 'T0'
        
        group = new_flow[1]
        assert group.config.is_group is True
        assert group.config.workers == ['W1']
        assert group.config.units_per_cycle == 5
        
        metadata = group.config.group_metadata
        assert metadata['task_count'] == 2
        assert metadata['total_cycle_time'] == 5 # 2 + 3
        assert metadata['total_optimal_time'] == 5 # 2 + 3
        
        # T3 debe haber actualizado su dependencia: dependía del antiguo 2 (T2),
        # que ahora está agrupado en el nuevo índice 1
        assert new_flow[2].config.previous_task_index == 1

    def test_crud_ops(self, presenter):
        task = FlowTaskDataDTO(id="T1", name="T", duration=1.0, duration_per_unit=1.0, department="G")
        step = ProductionFlowStepDTO(task=task, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date"))
        presenter.set_production_flow([step])
        assert presenter.get_production_flow() == [step]
        
        step2 = ProductionFlowStepDTO(task=task, config=FlowTaskConfigDTO(workers=["W"], machine_id=None, start_condition_type="date"))
        presenter.add_step(step2)
        assert len(presenter.get_production_flow()) == 2
        
        assert presenter.get_step(0).task.id == "T1"
        assert presenter.get_step(99) is None
        
        presenter.update_step(0, step2)
        assert presenter.get_step(0).config.workers == ["W"]

    def test_delete_step_logic(self, presenter):
        tasks = [FlowTaskDataDTO(id=f"T{i}", name=f"T{i}", duration=1.0, duration_per_unit=1.0, department="G") for i in range(4)]
        presenter.set_production_flow([
            ProductionFlowStepDTO(task=t, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date"))
            for t in tasks
        ])
        # Configurar dependencias
        presenter.get_step(1).config.previous_task_index = 0
        presenter.get_step(2).config.previous_task_index = 1
        presenter.get_step(3).config.previous_task_index = 0
        
        presenter.delete_step(1)
        assert len(presenter.get_production_flow()) == 3
        assert presenter.get_step(1).config.previous_task_index is None # El antiguo 2
        assert presenter.get_step(2).config.previous_task_index == 0 # El antiguo 3
        
        # Eliminar fuera de rango
        presenter.delete_step(99)
        assert len(presenter.get_production_flow()) == 3

    def test_model_queries(self, presenter):
        task = FlowTaskDataDTO(id="T", name="T", duration=1.0, duration_per_unit=1.0, department="G", requiere_maquina_tipo="A")
        assert presenter.get_machines_for_task(task) == []
        assert presenter.get_prep_info("P1") == (None, None)
        assert presenter.get_prep_steps_for_machine(1) == []
        assert presenter.get_default_step_ids(10) == []

    def test_get_prep_info_prefers_preparation_service(self):
        mock_config = create_autospec(ScheduleConfig, instance=True)
        mock_config.WORK_START_TIME = None
        prep = MagicMock(spec=["get_prep_info_for_product"])
        prep.get_prep_info_for_product.return_value = (7, 8)
        fab = MagicMock(spec=["get_prep_info_for_product"])
        fab.get_prep_info_for_product.return_value = (9, 10)
        p = DefineFlowPresenter(
            schedule_config=mock_config,
            default_units=1,
            preparation_service=prep,
            fabricacion_service=fab,
        )
        assert p.get_prep_info("X") == (7, 8)
        prep.get_prep_info_for_product.assert_called_once_with("X")
        fab.get_prep_info_for_product.assert_not_called()

    def test_group_tasks_non_consecutive_error(self, presenter):
        tasks = [FlowTaskDataDTO(id=f"T{i}", name=f"T{i}", duration=1.0, duration_per_unit=1.0, department="G") for i in range(3)]
        presenter.set_production_flow([
            ProductionFlowStepDTO(task=t, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date"))
            for t in tasks
        ])
        with pytest.raises(ValueError, match="consecutivas"):
            presenter.group_tasks([0, 2], [], 1, 10)
        assert len(presenter.get_production_flow()) == 3

    def test_group_tasks_zero_cycle_guard(self, presenter):
        tasks = [FlowTaskDataDTO(id=f"T{i}", name=f"T{i}", duration=1.0, duration_per_unit=1.0, department="G") for i in range(2)]
        presenter.set_production_flow([
            ProductionFlowStepDTO(task=t, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date"))
            for t in tasks
        ])
        # group_tasks ya no recibe el flujo por parámetro, usa self.production_flow
        new_flow = presenter.group_tasks([0, 1], [], 0, 10)
        # 10 / 0 guard -> total_cycles no se calcula en group_tasks ahora sino en set_production_flow (legacy logic) o se asume 1
        # En la nueva implementación group_tasks usa FlowTaskConfigDTO
        assert new_flow[0].config.is_group is True
        
        # Con modelo estricto
        mock_model = create_autospec(AppModel, instance=True)
        presenter.model = mock_model
        
        # machines
        mock_model.get_machines_by_process_type.return_value = ["M1"]
        task_with_machine = FlowTaskDataDTO(id="TM", name="TM", requiere_maquina_tipo="T1", duration=1.0, duration_per_unit=1.0, department="G")
        assert presenter.get_machines_for_task(task_with_machine) == ["M1"]
        mock_model.get_machines_by_process_type.assert_called_once_with("T1")
        assert presenter.get_machines_for_task(None) == []
        
        # prep info
        mock_model.get_prep_info_for_product.return_value = (1, 2)
        assert presenter.get_prep_info("P1") == (1, 2)
        mock_model.get_prep_info_for_product.assert_called_once_with("P1")
        
        # prep steps
        mock_group = MagicMock(spec=['id'])
        mock_group.id = 10
        mock_model.get_groups_for_machine.return_value = [mock_group]
        
        mock_step = MagicMock(spec=['id'])
        mock_step.id = 50
        mock_model.get_steps_for_group.return_value = [mock_step]
        
        steps = presenter.get_prep_steps_for_machine(1)
        assert len(steps) == 1
        assert steps[0].id == 50
        mock_model.get_groups_for_machine.assert_called_once_with(1)
        mock_model.get_steps_for_group.assert_called_once_with(10)

        assert presenter.get_default_step_ids(10) == [50]
        # Ya se llamó antes, ahora verificamos la nueva llamada
        mock_model.get_groups_for_machine.assert_has_calls([call(1)])
        mock_model.get_steps_for_group.assert_has_calls([call(10), call(10)])
    def test_get_step_view_model_empty(self, presenter):
        task1 = FlowTaskDataDTO(id="P1", name="P1", duration=1.0, duration_per_unit=1.0, department="G")
        task2 = FlowTaskDataDTO(id="P2", name="P2", duration=1.0, duration_per_unit=1.0, department="G")
        presenter.set_production_flow([
            ProductionFlowStepDTO(task=task1, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date")),
            ProductionFlowStepDTO(task=task2, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="dependency", previous_task_index=0))
        ])
        vm1 = presenter.get_step_view_model(0)
        vm2 = presenter.get_step_view_model(1)
        assert vm1.title == "PASO 1: P1"
        assert vm2.title == "PASO 2: P2"
        assert "Depende de 'P1'" in vm2.condition

    def test_get_step_view_model_individual(self, presenter):
        mock_machine = MagicMock(spec=['id', 'nombre'])
        mock_machine.id = 1
        mock_machine.nombre = "Prensa A"
        
        mock_model = create_autospec(AppModel, instance=True)
        mock_model.get_all_machines.return_value = [mock_machine]
        presenter.model = mock_model

        task = FlowTaskDataDTO(id="T", name="Corte", requiere_maquina_tipo="Prensa", duration=1.0, duration_per_unit=1.0, department="G")
        config = FlowTaskConfigDTO(workers=["Juan"], machine_id=1, start_condition_type="date")
        step = ProductionFlowStepDTO(task=task, config=config)
        presenter.set_production_flow([step])
        
        vm = presenter.get_step_view_model(0)
        assert vm.title == "PASO 1: Corte"
        assert vm.machine == "Prensa A"
        assert vm.workers == "Juan"
        mock_model.get_all_machines.assert_called_once_with(include_inactive=True)

    def test_get_step_view_model_with_dependencies(self, presenter):
        task1 = FlowTaskDataDTO(id="P1", name="P1", duration=1.0, duration_per_unit=1.0, department="G")
        task2 = FlowTaskDataDTO(id="P2", name="P2", duration=1.0, duration_per_unit=1.0, department="G")
        task3 = FlowTaskDataDTO(id="P3", name="P3", duration=1.0, duration_per_unit=1.0, department="G")
        
        presenter.set_production_flow([
            ProductionFlowStepDTO(task=task1, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date")),
            ProductionFlowStepDTO(task=task2, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="dependency", previous_task_index=0, min_predecessor_units=5)),
            ProductionFlowStepDTO(task=task3, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="worker", depends_on_worker="Juan"))
        ])
        
        # Test dependencia de tarea
        vm2 = presenter.get_step_view_model(1)
        assert "Depende de 'P1'" in vm2.condition
        assert "5 uds." in vm2.condition
        
        # Test dependencia de operario
        vm3 = presenter.get_step_view_model(2)
        assert "Depende de operario: Juan" in vm3.condition

    def test_get_step_view_model_machine_from_model(self, presenter):
        # Linea 171-172
        mock_machine = MagicMock(spec=['id', 'nombre'])
        mock_machine.id = 1
        mock_machine.nombre = "M-Top-Secret"
        
        mock_model = create_autospec(AppModel, instance=True)
        mock_model.get_all_machines.return_value = [mock_machine]
        presenter.model = mock_model
        
        # Usar DTO directamente para evitar ambigüedad en set_production_flow
        task = FlowTaskDataDTO(id="T", name="T", duration=1.0, duration_per_unit=1.0, department="G")
        config = FlowTaskConfigDTO(workers=[], machine_id=1, start_condition_type="date")
        flow = [ProductionFlowStepDTO(task=task, config=config)]
        presenter.set_production_flow(flow)
        
        vm = presenter.get_step_view_model(0)
        assert vm.machine == "M-Top-Secret"
        mock_model.get_all_machines.assert_called_once_with(include_inactive=True)
    def test_get_machines_for_task_no_model_direct(self, presenter):
        # Linea 102 coverage
        presenter.model = None
        task = FlowTaskDataDTO(id="T", name="T", duration=1.0, duration_per_unit=1.0, department="G")
        assert presenter.get_machines_for_task(task) == []
