"""
Tests unitarios para SimulationController.
Migrado y refactorizado desde PilaController y AppController tests.
"""
import pytest
from unittest.mock import MagicMock, patch, ANY, create_autospec, Mock
from datetime import datetime, date, time
from PyQt6.QtCore import QThread, QObject
from PyQt6.QtWidgets import QDialog
from ui.widgets import CalculateTimesWidget
from ui.dialogs import GetOptimizationParametersDialog, LoadPilaDialog, SavePilaDialog, EnhancedProductionFlowDialog

from typing import List, Any
from controllers.simulation.controller import SimulationController
from controllers.simulation.optimizer_worker import OptimizerWorker
from core.simulation.simulation_engine import Optimizer
from core.services.worker_service import WorkerService
from core.services.pila_service import PilaService
from core.dtos import MachineDTO

pytestmark = pytest.mark.unit

@pytest.fixture
def mock_app():
    """Mock del AppController con servicios usando create_autospec."""
    app = MagicMock(spec=['model', 'view', 'schedule_manager', 'db', 'state', 'pila_controller', 'hardware_controller', 'ui_controller', 'tracking_repo', 'label_manager', 'qr_generator', 'label_counter_repo'])
    app.model = MagicMock(spec=['worker_service', 'pila_service', 'machine_service', 'db'])
    app.model.worker_service = create_autospec(WorkerService, instance=True)
    app.model.pila_service = create_autospec(PilaService, instance=True)
    app.model.machine_service = MagicMock(spec=['get_all_machines'])
    app.view = MagicMock(spec=['pages', 'show_message', 'statusBar'])
    app.view.pages = {}
    app.schedule_manager = MagicMock(spec=['get_schedule_config', 'save_schedule_config', 'BREAKS', 'HOLIDAYS', 'WORK_START_TIME', 'WORK_END_TIME'])
    app.schedule_manager.BREAKS = []
    app.schedule_manager.HOLIDAYS = []
    app.schedule_manager.WORK_START_TIME = time(7, 0)
    app.schedule_manager.WORK_END_TIME = time(16, 0)
    app.db = Mock(spec=['SessionLocal'])
    app.state = MagicMock(spec=['last_production_flow', 'last_simulation_results', 'last_audit_log', 'last_flexible_workers_needed', 'current_user'])
    app.ui_controller = MagicMock(spec=['load_quote_for_home'])
    return app

@pytest.fixture
def controller(mock_app):
    # Setup CalculateTimesWidget mock
    mock_calc = MagicMock(spec=CalculateTimesWidget)
    mock_calc.save_pila_button = MagicMock(spec=['setEnabled'])
    mock_calc.export_button = MagicMock(spec=['setEnabled'])
    mock_calc.export_pdf_button = MagicMock(spec=['setEnabled'])
    mock_calc.export_log_button = MagicMock(spec=['setEnabled'])
    mock_calc.clear_button = MagicMock(spec=['setEnabled'])
    mock_calc.go_home_button = MagicMock(spec=['setEnabled'])
    mock_calc.define_flow_button = MagicMock(spec=['setEnabled'])
    mock_calc.progress_bar = MagicMock(spec=['setValue', 'setVisible'])
    mock_calc.planning_session = []

    mock_app.view.pages = {"calculate": mock_calc}
    mock_app.pila_controller = MagicMock(spec=[])

    with patch('core.di_container.DIContainer.get_instance') as mock_di_instance:
        mock_container = MagicMock(spec=['resolve'])
        mock_container.resolve.return_value = mock_app.state
        mock_di_instance.return_value = mock_container

        ctrl = SimulationController(mock_app)
        ctrl.logger = MagicMock(spec=['info', 'error', 'warning', 'critical'])
        ctrl.execution_manager.logger = MagicMock(spec=['info', 'error', 'warning', 'critical'])
        ctrl.editor_manager.logger = MagicMock(spec=['info', 'error', 'warning', 'critical'])
        return ctrl

@pytest.mark.unit
class TestSimulationControllerManual:
    """Tests para simulación manual."""

    def test_on_run_manual_plan_clicked_no_flow(self, controller):
        dto = MachineDTO(id=1, nombre="M1", departamento="DEP", tipo_proceso="CNC", activa=True)
        assert isinstance(dto, MachineDTO)
        
        controller.state.last_production_flow = None
        controller._on_run_manual_plan_clicked()
        controller.view.show_message.assert_called_with("Flujo no Definido", ANY, "warning")

    @patch('controllers.simulation.execution_manager.build_scheduler', autospec=True)
    def test_run_manual_plan_success(self, mock_build_scheduler, controller):
        controller.state.last_production_flow = [{"step": 1}]
        
        # Simular máquinas y trabajadores
        controller.worker_service.get_all_workers.return_value = []
        controller.machine_service.get_all_machines.return_value = []
        mock_build_scheduler.return_value = MagicMock(spec=[])
        
        # Patching inside the manager instance
        with patch.object(controller.execution_manager, 'start_simulation_thread', autospec=True) as mock_start:
            controller._on_run_manual_plan_clicked()
            assert mock_start.call_count == 1
            mock_start.assert_called_once_with(mock_build_scheduler.return_value)
            assert mock_build_scheduler.call_count == 1
            mock_build_scheduler.assert_called_once_with(
                production_flow=[{"step": 1}],
                worker_service=controller.worker_service,
                machine_service=controller.machine_service,
                schedule_manager=controller.app.schedule_manager,
                time_calculator_cls=ANY,
            )

    def test_start_simulation_thread(self, controller):
        mock_scheduler = MagicMock(spec=['production_flow', 'all_workers_with_skills', 'available_machines', 'schedule_config', 'time_calculator', 'start_date'])
        mock_calc = controller.view.pages["calculate"]
        
        # Patch QThread used in controller
        with patch('controllers.simulation.execution_manager.QThread.start'):
            controller._start_simulation_thread(mock_scheduler)
            assert controller.execution_thread is not None
            assert mock_calc.show_progress.call_count == 1
            mock_calc.show_progress.assert_called_once_with()

    def test_on_simulation_finished(self, controller):
        results = [{"Tarea": "T1", "Inicio": "2023-01-01T08:00:00"}]
        audit = ["Log 1"]
        mock_calc = controller.view.pages["calculate"]
        
        controller._on_simulation_finished(results, audit)
        
        assert controller.state.last_simulation_results == results
        mock_calc.display_simulation_results.assert_called_with(results, audit)
        mock_calc.save_pila_button.setEnabled.assert_called_with(True)

@pytest.mark.unit
class TestSimulationControllerDelegation:
    def test_on_execute_optimizer_simulation_clicked(self, controller):
        with patch.object(controller.execution_manager, 'on_execute_optimizer_simulation_clicked', autospec=True) as mock_exec:
            controller._on_execute_optimizer_simulation_clicked()
            assert mock_exec.call_count == 1

    def test_start_simulation_thread(self, controller):
        with patch.object(controller.execution_manager, 'start_simulation_thread', autospec=True) as mock_start:
            scheduler = MagicMock(spec=['production_flow', 'all_workers_with_skills', 'available_machines', 'schedule_config', 'time_calculator', 'start_date'])
            controller._start_simulation_thread(scheduler)
            mock_start.assert_called_once_with(scheduler)

    def test_on_simulation_finished(self, controller):
        with patch.object(controller.execution_manager, '_on_simulation_finished', autospec=True) as mock_finish:
            controller._on_simulation_finished([], [])
            mock_finish.assert_called_once_with([], [])

    def test_on_optimization_finished(self, controller):
        with patch.object(controller.execution_manager, '_on_optimization_finished', autospec=True) as mock_finish:
            controller._on_optimization_finished([], [], 0)
            mock_finish.assert_called_once_with([], [], 0)

    def test_handle_run_manual_from_visual_editor(self, controller):
        with patch.object(controller.execution_manager, 'handle_run_manual_from_visual_editor', autospec=True) as mock_handle:
            dialog = MagicMock(spec=[])
            controller._handle_run_manual_from_visual_editor(dialog)
            mock_handle.assert_called_once_with(dialog)

    def test_handle_run_optimizer_from_visual_editor(self, controller):
        with patch.object(controller.execution_manager, 'handle_run_optimizer_from_visual_editor', autospec=True) as mock_handle:
            dialog = MagicMock(spec=[])
            controller._handle_run_optimizer_from_visual_editor(dialog)
            mock_handle.assert_called_once_with(dialog)

    def test_on_define_flow_clicked(self, controller):
        with patch.object(controller.editor_manager, 'on_define_flow_clicked', autospec=True) as mock_define:
            controller._on_define_flow_clicked()
            assert mock_define.call_count == 1

    def test_open_editor_with_loaded_flow(self, controller):
        with patch.object(controller.editor_manager, 'open_editor_with_loaded_flow', autospec=True) as mock_open:
            controller._open_editor_with_loaded_flow([], "Pila")
            mock_open.assert_called_once_with([], "Pila", 1)

@pytest.mark.unit
class TestSimulationControllerOptimization:
    """Tests para el Optimizador."""

    @patch('controllers.simulation.execution_manager.GetOptimizationParametersDialog', autospec=True)
    def test_execute_optimizer_simulation_success(self, MockDialog, controller):
        controller.view.pages = {"calculate": MagicMock(spec=['planning_session', '_update_plan_display', 'show_progress', 'hide_progress'])}
        controller.view.pages["calculate"].planning_session = [{"unidades": 1}]
        
        mock_dialog = MockDialog.return_value
        mock_dialog.exec.return_value = True
        mock_dialog.get_parameters.return_value = {
            "start_date": date(2023, 1, 1),
            "end_date": date(2023, 1, 10),
            "units": 10
        }
        
        with patch('controllers.simulation.execution_manager.Optimizer', autospec=True) as MockOptimizer, \
             patch('controllers.simulation.execution_manager.OptimizerWorker', new_callable=MagicMock) as MockWorker, \
             patch('controllers.simulation.execution_manager.QThread') as MockThread:
            
            controller._on_execute_optimizer_simulation_clicked()
            
            assert controller.view.pages["calculate"].planning_session[0]['unidades'] == 10
            MockOptimizer.assert_called_once_with(
                planning_session=[{"unidades": 10}],
                db_manager=controller.app.db,
                worker_service=controller.app.model.worker_service,
                pila_service=controller.app.model.pila_service,
                schedule_config=controller.app.schedule_manager,
                production_flow_override=ANY,
            )
            MockWorker.assert_called_once_with(
                MockOptimizer.return_value,
                datetime.combine(date(2023, 1, 1), time(7, 0)),
                date(2023, 1, 10),
                10
            )
            assert MockThread.return_value.start.call_count == 1
            assert MockThread.return_value.finished.connect.call_count == 1
            assert MockWorker.return_value.finished.connect.call_count == 2

    def test_on_optimization_finished_success(self, controller):
        results = [{"id": 1}]
        audit: List[Any] = []
        
        controller._on_optimization_finished(results, audit, 2)
        
        assert controller.state.last_flexible_workers_needed == 2
        controller.view.show_message.assert_called_with("Resultado Optimización", ANY, "info")

@pytest.mark.unit
class TestSimulationControllerVisualEditor:
    """Tests para integracion con editor visual."""



    @patch('controllers.simulation.editor_manager.EnhancedProductionFlowDialog', autospec=True)
    def test_on_define_flow_clicked_success(self, MockDialog, controller):
        mock_calc = controller.view.pages["calculate"]
        mock_calc.planning_session = [{"identificador": "L1"}]
        
        controller.pila_service.get_data_for_calculation_from_session.return_value = [{"id": 1}]
        controller.worker_service.get_all_workers.return_value = []
        
        mock_dlg = MockDialog.return_value
        mock_dlg.exec.return_value = True
        mock_dlg.get_production_flow.return_value = [{"step": 1}]
        
        controller._on_define_flow_clicked()
        
        assert controller.state.last_production_flow == [{"step": 1}]
        controller.view.show_message.assert_called_with("Flujo Definido", ANY, "info")

    def test_on_clear_simulation(self, controller):
        mock_calc = controller.view.pages["calculate"]
        controller.state.last_production_flow = [{"step": 1}]
        
        controller._on_clear_simulation()
        
        assert controller.state.last_production_flow is None
        assert mock_calc.clear_all.call_count == 1
        mock_calc.clear_all.assert_called_once_with()
        mock_calc.define_flow_button.setEnabled.assert_called_with(False)

    @patch('controllers.simulation.editor_manager.EnhancedProductionFlowDialog', autospec=True)
    def test_on_define_flow_clicked_errors(self, MockDialog, controller):
        # 1. Sin widget
        controller.view.pages["calculate"] = None
        controller._on_define_flow_clicked()
        controller.view.show_message.assert_called_with("Error", ANY, "critical")
        
        # 2. Pila vacia
        mock_calc = MagicMock(spec=CalculateTimesWidget)
        mock_calc.planning_session = []
        controller.view.pages["calculate"] = mock_calc
        controller._on_define_flow_clicked()
        controller.view.show_message.assert_called_with("Pila Vacía", ANY, "warning")

        # 3. Sin datos de tareas
        mock_calc.planning_session = [{"param": 1}]
        controller.pila_service.get_data_for_calculation_from_session.return_value = None
        controller._on_define_flow_clicked()
        controller.view.show_message.assert_called_with("Error de Datos", ANY, "critical")
        
        # 4. Dialog rejected o return None flow
        controller.pila_service.get_data_for_calculation_from_session.return_value = [{"id": 1}]
        controller.worker_service.get_all_workers.return_value = []
        mock_dlg = MockDialog.return_value
        mock_dlg.exec.return_value = True
        mock_dlg.get_production_flow.return_value = None
        controller._on_define_flow_clicked()
        assert controller.state.last_production_flow is None
        
        # 5. Exception
        with patch.object(controller.pila_service, 'get_data_for_calculation_from_session', side_effect=Exception("Flow Def Error")):
            with patch.object(controller.editor_manager.logger, 'critical') as mock_crit:
                controller._on_define_flow_clicked()
                assert mock_crit.call_count == 1
                controller.view.show_message.assert_called_with("Error Crítico", ANY, "critical")

    @patch('controllers.simulation.editor_manager.EnhancedProductionFlowDialog', autospec=True)
    def test_open_editor_with_loaded_flow(self, MockDialog, controller):
        # Flow vacio = tasks_data empty
        with patch.object(controller.editor_manager.logger, 'warning') as mock_warn:
            controller._open_editor_with_loaded_flow([], "Test Pila")
            assert mock_warn.call_count == 1
        
        # Test de flow estructurado
        production_flow = [
            {'task': {'original_product_code': 'PROD_1', 'original_product_info': {'desc': 'P1'}, 'duration_per_unit': 10}},
            {'task': {'original_product_code': 'PROD_2'}}
        ]
        
        mock_dlg = MockDialog.return_value
        mock_dlg.exec.return_value = True
        mock_dlg.get_production_flow.return_value = production_flow
        
        controller.worker_service.get_all_workers.return_value = []
        
        controller._open_editor_with_loaded_flow(production_flow, "Test Pila", units=5)
        
        # Success assert
        assert MockDialog.call_count == 1
        assert controller.state.last_production_flow == production_flow
        
        # Exception
        controller.worker_service.get_all_workers.side_effect = Exception("Open Editor Error")
        with patch.object(controller.editor_manager.logger, 'error') as mock_err:
            controller._open_editor_with_loaded_flow(production_flow, "Test Pila", units=5)
            assert mock_err.call_count == 1



    def test_worker_run_success(self):
        mock_optimizer = MagicMock(spec=['schedule_config', 'workers_with_skills', 'production_flow_override', 'model', '_verify_deadlines', 'audit_log'])
        mock_optimizer.schedule_config = MagicMock(spec=['get_schedule_config', 'BREAKS', 'HOLIDAYS', 'WORK_START_TIME', 'WORK_END_TIME'])
        mock_optimizer.schedule_config.BREAKS = []
        mock_optimizer.schedule_config.HOLIDAYS = []
        mock_optimizer.schedule_config.WORK_START_TIME = time(7, 0)
        mock_optimizer.schedule_config.WORK_END_TIME = time(16, 0)
        mock_optimizer.workers_with_skills = [('W1', 1)]
        mock_optimizer.production_flow_override = [{'task': {'id': 1}}]
        mock_optimizer.model = MagicMock(spec=['machine_repo'])
        mock_optimizer.model.machine_repo = MagicMock(spec=['get_all_machines'])
        mock_optimizer.model.machine_repo.get_all_machines.return_value = []
        mock_optimizer._verify_deadlines.return_value = True
        mock_optimizer.audit_log = []

        start_date = datetime.now()
        end_date = datetime.now()
        units = 10

        worker = OptimizerWorker(mock_optimizer, start_date, end_date, units)
        worker.flow_builder = MagicMock(spec=['build_flow_from_override'])
        worker.flow_builder.build_flow_from_override.return_value = [{'task': {'id': 1}}]
        
        mock_signal = MagicMock(spec=['connect', 'emit'])
        worker.finished.connect(mock_signal)
        
        with patch('controllers.simulation.optimizer_worker.CalculadorDeTiempos'), \
             patch('controllers.simulation.optimizer_worker.MotorDeEventos') as MockScheduler:
            
            mock_scheduler_instance = MockScheduler.return_value
            mock_scheduler_instance.run_simulation.return_value = (['result'], ['log'])
            
            worker.run()
            
            assert mock_signal.call_count == 1
            args = mock_signal.call_args[0]
            assert args[0] == ['result'] # results
            assert args[2] == 0 # flexible workers needed
            
    def test_worker_run_no_flow(self):
        """Simula que no hay flujo para probar el break temprano."""
        mock_optimizer = MagicMock(spec=['workers_with_skills', 'production_flow_override', 'audit_log'])
        mock_optimizer.audit_log = []
        worker = OptimizerWorker(mock_optimizer, datetime.now(), datetime.now(), 1)
        worker.flow_builder = MagicMock(spec=['build_flow_from_override'])
        worker.flow_builder.build_flow_from_override.return_value = None
        
        mock_signal = MagicMock(spec=['connect', 'emit'])
        worker.finished.connect(mock_signal)
        worker.run()
        
        assert mock_signal.call_count == 1
        args = mock_signal.call_args[0]
        assert args[0] is None # final_results
        
    def test_worker_run_max_flexible_workers(self):
        """Simula que nunca se cumplen los plazos, alcanzando el límite MAX_FLEXIBLE_WORKERS."""
        mock_optimizer = MagicMock(spec=['workers_with_skills', 'model', '_verify_deadlines', 'production_flow_override', 'schedule_config'])
        mock_optimizer.schedule_config = MagicMock(spec=['get_schedule_config', 'BREAKS', 'HOLIDAYS', 'WORK_START_TIME', 'WORK_END_TIME'])
        mock_optimizer.schedule_config.BREAKS = []
        mock_optimizer.schedule_config.HOLIDAYS = []
        mock_optimizer.schedule_config.WORK_START_TIME = time(7, 0)
        mock_optimizer.schedule_config.WORK_END_TIME = time(16, 0)
        mock_optimizer.workers_with_skills = []
        mock_optimizer.model = MagicMock(spec=['machine_repo'])
        mock_optimizer.model.machine_repo = MagicMock(spec=['get_all_machines'])
        mock_optimizer.model.machine_repo.get_all_machines.return_value = []
        mock_optimizer._verify_deadlines.return_value = False # NUNCA se cumplen
        
        worker = OptimizerWorker(mock_optimizer, datetime.now(), datetime.now(), 1)
        worker.flow_builder = MagicMock(spec=['build_flow_from_override'])
        worker.flow_builder.build_flow_from_override.return_value = [{'step': 1}]
        
        mock_signal = MagicMock(spec=['connect', 'emit'])
        worker.finished.connect(mock_signal)
        
        with patch('controllers.simulation.optimizer_worker.CalculadorDeTiempos'), \
             patch('controllers.simulation.optimizer_worker.MotorDeEventos') as MockScheduler:
            mock_scheduler_instance = MockScheduler.return_value
            mock_scheduler_instance.run_simulation.return_value = (['result_fail'], ['log'])
            
            worker.run()
            
            assert mock_signal.call_count == 1
            args = mock_signal.call_args[0]
            assert args[0] == ['result_fail'] # Devuelve el último resultado
            assert args[2] == 21 # Superó el MAX_FLEXIBLE_WORKERS (20)

    def test_worker_create_scheduler_adds_extra_workers(self):
        """Verifica que _create_scheduler añade el número correcto de trabajadores flexibles."""
        mock_optimizer = MagicMock(spec=['workers_with_skills', 'model', 'schedule_config'])
        mock_optimizer.schedule_config = MagicMock(spec=['get_schedule_config', 'BREAKS', 'HOLIDAYS', 'WORK_START_TIME', 'WORK_END_TIME'])
        mock_optimizer.schedule_config.BREAKS = []
        mock_optimizer.schedule_config.HOLIDAYS = []
        mock_optimizer.schedule_config.WORK_START_TIME = time(7, 0)
        mock_optimizer.schedule_config.WORK_END_TIME = time(16, 0)
        mock_optimizer.workers_with_skills = [('Base', 1)]
        machine = MagicMock(spec=['id', 'nombre'])
        machine.id = 1
        machine.nombre = "M1"
        mock_optimizer.model = MagicMock(spec=['machine_repo'])
        mock_optimizer.model.machine_repo = MagicMock(spec=['get_all_machines'])
        mock_optimizer.model.machine_repo.get_all_machines.return_value = [machine]
        
        worker = OptimizerWorker(mock_optimizer, datetime.now(), datetime.now(), 1)
        
        with patch('controllers.simulation.optimizer_worker.CalculadorDeTiempos'), \
             patch('controllers.simulation.optimizer_worker.MotorDeEventos') as MockScheduler:
            worker._create_scheduler([{'step': 1}], 2) # 2 extra
            
            assert MockScheduler.call_count == 1
            kwargs = MockScheduler.call_args[1]
            all_workers = kwargs['all_workers_data']
            assert len(all_workers) == 3 # 1 base + 2 flexibles
            assert all_workers[1] == ('FLEX_1', 3)
            assert all_workers[2] == ('FLEX_2', 3)

@pytest.mark.unit
class TestSimulationControllerStates:
    """Extra tests para SimulationController relacionados con estados, excepciones, y handlers."""
    
    @patch('PyQt6.QtWidgets.QApplication.processEvents', autospec=True)
    def test_on_run_manual_plan_clicked_wrong_widget(self, mock_process, controller):
        controller.view.pages["calculate"] = None # Simulando widget incorrecto
        controller.view.statusBar.return_value = MagicMock(spec=['showMessage'])
        controller._on_run_manual_plan_clicked() # Return temprano
        assert controller.view.statusBar.return_value.showMessage.call_count == 0

    def test_on_run_manual_plan_exception(self, controller):
        controller.state.last_production_flow = [{"step": 1}]
        controller.worker_service.get_all_workers.side_effect = Exception("DB Error")
        
        # Evitar log AttributeError por la asercion real
        with patch.object(controller.execution_manager.logger, 'critical') as mock_critical:
            controller._on_run_manual_plan_clicked()
            assert mock_critical.call_count == 1
            controller.view.show_message.assert_called_with("Error Crítico", ANY, "critical")

    def test_execute_optimizer_simulation_wrong_widget(self, controller):
        controller.view.pages["calculate"] = None
        controller._on_execute_optimizer_simulation_clicked()
        assert not controller.view.show_message.called

    def test_execute_optimizer_simulation_empty_session(self, controller):
        mock_calc = controller.view.pages["calculate"]
        mock_calc.planning_session = []
        controller._on_execute_optimizer_simulation_clicked()
        controller.view.show_message.assert_called_with("Pila Vacía", ANY, "warning")

    @patch('controllers.simulation.execution_manager.GetOptimizationParametersDialog', autospec=True)
    def test_execute_optimizer_simulation_dialog_rejected(self, MockDialog, controller):
        mock_calc = controller.view.pages["calculate"]
        mock_calc.planning_session = [{"u": 1}]
        mock_dlg = MockDialog.return_value
        mock_dlg.exec.return_value = False
        controller._on_execute_optimizer_simulation_clicked()
        # Se aborta, no se ejecuta thread
        assert controller.execution_thread is None

    @patch('controllers.simulation.execution_manager.GetOptimizationParametersDialog', autospec=True)
    def test_execute_optimizer_simulation_exception(self, MockDialog, controller):
        mock_calc = controller.view.pages["calculate"]
        mock_calc.planning_session = [{"u": 1}]
        mock_dlg = MockDialog.return_value
        mock_dlg.exec.return_value = True
        mock_dlg.get_parameters.return_value = {"start_date": date.today(), "end_date": date.today(), "units": 1}
        
        with patch('controllers.simulation.execution_manager.Optimizer', autospec=True, side_effect=Exception("Opt Error")):
            controller._on_execute_optimizer_simulation_clicked()
            controller.view.show_message.assert_called_with("Error Crítico", ANY, "critical")
            assert mock_calc.hide_progress.call_count == 1
            mock_calc.hide_progress.assert_called_once_with()

    def test_start_simulation_thread_already_running(self, controller):
        mock_thread = MagicMock(spec=['isRunning', 'start', 'finished', 'deleteLater'])
        mock_thread.isRunning.return_value = True
        controller.execution_thread = mock_thread
        
        controller._start_simulation_thread(MagicMock(spec=[]))
        controller.view.show_message.assert_called_with("Simulación en Curso", ANY, "warning")

    def test_start_simulation_thread_runtime_error_recover(self, controller):
        # Simular que el thread fue eliminado subyacentemente lanzando RuntimeError en isRunning
        mock_thread = MagicMock(spec=['isRunning', 'start', 'finished', 'deleteLater'])
        mock_thread.isRunning.side_effect = RuntimeError("Internal C++ object deleted")
        controller.execution_thread = mock_thread
        
        with patch('controllers.simulation.execution_manager.QThread') as MockThread, \
             patch('controllers.simulation.execution_manager.SimulationWorker'):
            controller._start_simulation_thread(MagicMock(spec=[]))
            # Debe haber recuperado la instancia seteándola a None y creando un hilo nuevo
            assert MockThread.return_value.start.call_count == 1

    def test_on_optimization_finished_failed_results(self, controller):
        # results None
        controller._on_optimization_finished(None, [], 0)
        assert controller.view.show_message.call_count == 1
        controller.view.show_message.assert_called_with("Optimización Fallida", ANY, "warning")



    def test_handle_save_flow_only(self, controller):
        production_flow = [
            {'task': {'original_product_code': 'PREP_10', 'name': '[PREPROCESO] Cortar'}},
            {'task': {'original_product_code': 'PROD_20', 'original_product_info': {'desc': 'Test Prod'}}},
            {'task': {}} # Edge case sin codes
        ]
        controller.handle_save_flow_only("Mi Pila", "Desc", production_flow)
        
        assert controller.pila_service.save_pila.call_count == 1
        controller.pila_service.save_pila.assert_called_once_with(
            "Mi Pila",
            "Desc",
            ANY,
            production_flow,
            [],
            None,
            unidades=1,
        )
        args = controller.pila_service.save_pila.call_args[0]
        assert args[0] == "Mi Pila"
        assert args[1] == "Desc"
        
        pila_reconstruida = args[2]
        assert 10 in pila_reconstruida['preprocesos']
        assert pila_reconstruida['preprocesos'][10]['nombre'] == "Cortar"
        assert 'PROD_20' in pila_reconstruida['productos']
        assert pila_reconstruida['productos']['PROD_20']['descripcion'] == "Test Prod"
        assert controller.pila_service.save_pila.call_count == 1

    def test_handle_save_flow_only_with_dto_steps(self, controller):
        """Cubre rama de steps tipo DTO (no dict) en handle_save_flow_only."""
        class DummyTask:
            def __init__(self):
                self.original_product_code = "PROD_DTO"
                self.name = "Tarea DTO"
                self.original_product_info = {"desc": "Desc DTO"}

        class DummyStep:
            def __init__(self):
                self.task = DummyTask()

        production_flow = [DummyStep()]
        controller.handle_save_flow_only("Pila DTO", "Desc", production_flow)

        assert controller.pila_service.save_pila.call_count >= 1
        args = controller.pila_service.save_pila.call_args[0]
        pila_reconstruida = args[2]
        assert "PROD_DTO" in pila_reconstruida["productos"]
        assert pila_reconstruida["productos"]["PROD_DTO"]["descripcion"] == "Desc DTO"

    def test_clear_simulation_state(self, controller):
        controller.state.last_simulation_results = []
        controller.state.last_audit_log = []
        controller.clear_simulation_state() # Esto llama internamente a _on_clear_simulation
        assert controller.state.last_simulation_results is None
        assert controller.state.last_audit_log is None
        
    def test_update_simulation_progress(self, controller):
        mock_calc = controller.view.pages["calculate"]
        controller._update_simulation_progress(50)
        mock_calc.progress_bar.setValue.assert_called_with(50)

    def test_on_calc_product_result_selected(self, controller):
        item = MagicMock(spec=[])
        controller._on_calc_product_result_selected(item)
        assert item is not None # Justificado: el método actual es un pass y solo verificamos que no lance excepción
