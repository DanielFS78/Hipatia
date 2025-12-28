import pytest
from unittest.mock import MagicMock, patch, call
from controllers.app_controller import AppController
from controllers.pila_controller import OptimizerWorker

# --- FIXTURES ---

@pytest.fixture
def mock_app_components():
    """Returns mocked model, view, config."""
    model = MagicMock()
    model.worker_repo.get_all_workers.return_value = []
    view = MagicMock()
    config = MagicMock()
    return model, view, config

# --- TESTS ---

class TestOptimizerWorker:
    
    def test_worker_run_success(self, mock_app_components):
        """Test successful optimization run in worker."""
        # Setup mocks
        mock_optimizer = MagicMock()
        mock_optimizer.schedule_config = MagicMock()
        mock_optimizer._prepare_and_prioritize_tasks.return_value = [{'name': 'Task 1', 'required_skill_level': 1}]
        mock_optimizer.model.worker_repo.get_all_workers.return_value = [
            MagicMock(nombre_completo="Worker 1", tipo_trabajador=3)
        ]
        mock_optimizer.model.machine_repo.get_all_machines.return_value = []
        mock_optimizer._verify_deadlines.return_value = True # Success on first try
        mock_optimizer.audit_log = []

        start_date = "2025-01-01"
        end_date = "2025-01-05"
        units = 10

        # Use OptimizerWorker from pila_controller directly
        worker = OptimizerWorker(mock_optimizer, start_date, end_date, units)
        
        # Connect signal
        mock_signal = MagicMock()
        worker.finished.connect(mock_signal)
        
        # Mock dependencies inside run()
        with patch('controllers.pila_controller.CalculadorDeTiempos'), \
             patch('controllers.pila_controller.AdaptadorScheduler') as MockScheduler:
            
            mock_scheduler_instance = MockScheduler.return_value
            mock_scheduler_instance.run_simulation.return_value = (['result'], ['log'])
            
            worker.run()
            
            # Verify signal emitted
            mock_signal.assert_called_once()
            args = mock_signal.call_args[0]
            assert args[0] == ['result'] # results
            assert args[2] == 0 # flexible workers needed

    def test_worker_run_needs_flexible_workers(self, mock_app_components):
        """Test optimization loop adding flexible workers."""
        mock_optimizer = MagicMock()
        mock_optimizer._prepare_and_prioritize_tasks.return_value = [{'name': 'Hard Task'}]
        # First try fails, second succeeds
        mock_optimizer._verify_deadlines.side_effect = [False, True]
        mock_optimizer.model.worker_repo.get_all_workers.return_value = []
        mock_optimizer.model.machine_repo.get_all_machines.return_value = []
        mock_optimizer.audit_log = []

        # Use OptimizerWorker from pila_controller directly
        worker = OptimizerWorker(mock_optimizer, "2025-01-01", "2025-01-05", 1)
        
        mock_signal = MagicMock()
        worker.finished.connect(mock_signal)

        with patch('controllers.pila_controller.CalculadorDeTiempos'), \
             patch('controllers.pila_controller.AdaptadorScheduler') as MockScheduler:
             
            mock_scheduler_instance = MockScheduler.return_value
            mock_scheduler_instance.run_simulation.return_value = ([], [])
            
            worker.run()
            
            # Should have called verify_deadlines twice
            assert mock_optimizer._verify_deadlines.call_count == 2
            # Flexible workers should be 1
            args = mock_signal.call_args[0]
            assert args[2] == 1
