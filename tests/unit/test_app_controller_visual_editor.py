import sys
import pytest
from unittest.mock import MagicMock, patch, ANY
sys.modules["PyQt6.QtCharts"] = MagicMock()
sys.modules["pandas"] = MagicMock() # FIX: Mock pandas to prevent ImportErrors

from datetime import datetime
from PyQt6.QtWidgets import QDialog
from controllers.app_controller import AppController
from core.app_model import AppModel
from schedule_config import ScheduleConfig

@pytest.fixture
def mock_controller(qapp): # qapp fixture ensures QApplication exists
    model = MagicMock(spec=AppModel)
    model.db = MagicMock() # FIX: Add db attribute
    model.pila_repo = MagicMock() # FIX: Add pila_repo
    
    # Mock sub-controllers to avoid dependency issues and provide method delegation
    with patch('controllers.app_controller.ProductController') as MockProdCtrl, \
         patch('controllers.app_controller.WorkerController') as MockWorkerCtrl, \
         patch('controllers.app_controller.PilaController') as MockPilaCtrl:
        
        # Configure the mock pila controller to have the delegate method
        mock_pila_instance = MockPilaCtrl.return_value
        mock_pila_instance._start_simulation_thread = MagicMock()
        
        controller = AppController(model, MagicMock(), MagicMock())
        yield controller

class TestAppControllerVisualEditor:
    
    def test_handle_save_pila_from_visual_editor_success(self, mock_controller):
        """Test legitimate save flow."""
        flow_dialog = MagicMock()
        flow_dialog.get_production_flow.return_value = [{"task": {"original_product_code": "P1", "original_product_info": {"desc": "D1"}}}]
        
        # Mock SavePilaDialog
        with patch('controllers.app_controller.SavePilaDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = True
            dialog_instance.get_data.return_value = ("My Pila", "Desc")
            
            mock_controller._handle_save_pila_from_visual_editor(flow_dialog)
            
            # Verify model.save_pila called with correct structure
            mock_controller.model.save_pila.assert_called_once()
            args = mock_controller.model.save_pila.call_args[1]
            assert args["nombre"] == "My Pila"
            assert "P1" in args["pila_de_calculo"]["productos"]

    def test_handle_save_pila_empty_flow(self, mock_controller):
        """Test save with empty flow."""
        flow_dialog = MagicMock()
        flow_dialog.get_production_flow.return_value = []
        
        mock_controller._handle_save_pila_from_visual_editor(flow_dialog)
        
        mock_controller.view.show_message.assert_called_with("Flujo Vacío", ANY, "warning")
        mock_controller.model.save_pila.assert_not_called()

    def test_handle_load_pila_into_visual_editor_success(self, mock_controller):
        """Test legitimate load flow."""
        flow_dialog = MagicMock()
        mock_controller.model.pila_repo.get_all_pilas.return_value = [{"id": 1}]
        
        with patch('controllers.app_controller.LoadPilaDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = True
            dialog_instance.get_selected_id.return_value = 1
            dialog_instance.delete_requested = False
            
            # Mock load_pila return
            mock_controller.model.pila_repo.load_pila.return_value = ({"nombre": "P1"}, {}, [{"step": 1}], [])
            
            mock_controller._handle_load_pila_into_visual_editor(flow_dialog)
            
            flow_dialog._load_flow_onto_canvas.assert_called_once_with([{"step": 1}])
            mock_controller.view.show_message.assert_called_with("Pila Cargada", ANY, "info")

    def test_on_define_flow_clicked_success(self, mock_controller):
        """Test opening the definition dialog."""
        mock_calc_page = MagicMock()
        mock_calc_page.planning_session = [{"unidades": 10}]
        mock_controller.view.pages.get.return_value = mock_calc_page
        
        mock_controller.model.get_data_for_calculation_from_session.return_value = ["tasks"]
        mock_controller.model.get_all_workers.return_value = []
        
        with patch('controllers.app_controller.EnhancedProductionFlowDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = True
            dialog_instance.get_production_flow.return_value = ["flow"]
            
            mock_controller._on_define_flow_clicked()
            
            assert mock_controller.last_production_flow == ["flow"]
            mock_controller.view.show_message.assert_called_with("Flujo Definido", ANY, "info")

    def test_on_run_manual_plan_clicked_success(self, mock_controller):
        """Test running manual plan from existing flow."""
        mock_controller.last_production_flow = [{"task": {"required_skill_level": 1}}]
        
        # Import the actual widget class to create a proper mock instance
        from ui.widgets import CalculateTimesWidget
        from unittest.mock import create_autospec
        
        # Create a mock that IS an instance of CalculateTimesWidget type-wise
        # by using create_autospec which preserves the class for isinstance checks
        mock_page = create_autospec(CalculateTimesWidget, instance=True)
        mock_controller.view.pages.get.return_value = mock_page
        
        mock_controller.model.get_all_workers.return_value = []
        mock_controller.model.get_all_machines.return_value = []
        
        with patch('controllers.app_controller.AdaptadorScheduler') as MockScheduler, \
             patch('controllers.app_controller.CalculadorDeTiempos') as MockCalc:
            
            mock_controller._on_run_manual_plan_clicked()
            
            MockScheduler.assert_called_once()

    def test_handle_run_manual_from_visual_editor(self, mock_controller):
        """Test running manual from editor."""
        flow_dialog = MagicMock()
        flow_dialog.get_production_flow.return_value = [{"task": {"required_skill_level": 1}}]
        
        mock_controller.view.pages.get.return_value = MagicMock()
        mock_controller.model.get_all_workers.return_value = []
        mock_controller.model.get_all_machines.return_value = []
        
        # Patch threading start
        mock_controller._start_simulation_thread = MagicMock()
        
        with patch('simulation_adapter.AdaptadorScheduler') as MockScheduler, \
             patch('time_calculator.CalculadorDeTiempos') as MockCalc:
            
            mock_controller._handle_run_manual_from_visual_editor(flow_dialog)
            
            MockScheduler.assert_called_once()
            mock_controller._start_simulation_thread.assert_called_once()
    
    def test_handle_run_optimizer_from_visual_editor(self, mock_controller):
        """Test running optimizer from editor."""
        flow_dialog = MagicMock()
        flow_dialog.get_production_flow.return_value = ["flow"]
        
        calc_page = MagicMock()
        calc_page.planning_session = [{"id": 1}]
        mock_controller.view.pages.get.return_value = calc_page
        
        with patch('controllers.app_controller.GetOptimizationParametersDialog') as MockParams, \
             patch('controllers.app_controller.Optimizer') as MockOptimizer:
            
            dialog = MockParams.return_value
            dialog.exec.return_value = True
            from datetime import date
            dialog.get_parameters.return_value = {"start_date": date.today(), "end_date": date.today(), "units": 5}
            
            # Patch threading
            mock_controller.OptimizerWorker = MagicMock()
            
            mock_controller._handle_run_optimizer_from_visual_editor(flow_dialog)
            
            MockOptimizer.assert_called_once()
            # Verify production_flow was passed
            call_kwargs = MockOptimizer.call_args[1]
            assert call_kwargs['production_flow_override'] == ["flow"]

