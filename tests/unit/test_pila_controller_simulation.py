import pytest
from unittest.mock import MagicMock, patch, ANY
from PyQt6.QtCore import Qt
from controllers.pila_controller import PilaController
from ui.widgets import CalculateTimesWidget

# --- FIXTURES ---

@pytest.fixture
def controller():
    """Returns PilaController with mocked dependencies."""
    mock_app = MagicMock()
    mock_app.model = MagicMock()
    mock_app.model.get_all_workers.return_value = []
    mock_app.model.get_all_machines.return_value = []
    
    mock_app.view = MagicMock()
    mock_app.view.pages = {}
    mock_app.view.show_message = MagicMock()
    mock_app.view.statusBar().showMessage = MagicMock()
    
    mock_app.schedule_manager = MagicMock()
    mock_app.db = mock_app.model.db
    mock_app.last_production_flow = None # Init attribute

    return PilaController(mock_app)

# --- TESTS ---

class TestPilaControllerSimulation:

    def test_on_run_manual_plan_clicked_no_flow(self, controller):
        """Test error when running manual plan without defined flow."""
        mock_calc = MagicMock(spec=CalculateTimesWidget)
        controller.view.pages = {"calculate": mock_calc}
        controller.app.last_production_flow = None # No flow
        
        controller._on_run_manual_plan_clicked()
        
        controller.view.show_message.assert_called_with(
            "Flujo no Definido", ANY, "warning"
        )
        mock_calc.show_progress.assert_not_called()

    def test_on_run_manual_plan_clicked_success(self, controller):
        """Test successful manual plan execution."""
        mock_calc = MagicMock(spec=CalculateTimesWidget)
        controller.view.pages = {"calculate": mock_calc}
        controller.app.last_production_flow = [{'task': {'id': 1}, 'workers': [], 'trigger_units': 1}]
        
        # Mocks for scheduling
        # AdaptadorScheduler is imported in pila_controller, so we patch it there
        with patch('controllers.pila_controller.CalculadorDeTiempos'), \
             patch('controllers.pila_controller.AdaptadorScheduler') as MockScheduler, \
             patch.object(controller, '_start_simulation_thread') as mock_start_thread, \
             patch('PyQt6.QtWidgets.QApplication.processEvents'):
            
            controller._on_run_manual_plan_clicked()
            
            MockScheduler.assert_called_once()
            mock_start_thread.assert_called_once()
            mock_calc.show_progress.assert_called_once()

    def test_on_execute_optimizer_simulation_clicked_empty_stack(self, controller):
        """Test optimization with empty planning session."""
        mock_calc = MagicMock(spec=CalculateTimesWidget)
        mock_calc.planning_session = [] # Empty
        controller.view.pages = {"calculate": mock_calc}
        
        controller._on_execute_optimizer_simulation_clicked()
        
        controller.view.show_message.assert_called_with("Pila Vacía", ANY, "warning")

    def test_handle_run_manual_from_visual_editor_success(self, controller):
        """Test running manual from visual editor."""
        mock_dialog = MagicMock()
        mock_dialog.get_production_flow.return_value = [{'task': {'name': 'T1'}, 'workers': []}]
        
        # Mock sorted workers
        worker_dto = MagicMock(nombre_completo="Juan", tipo_trabajador=3)
        controller.model.get_all_workers.return_value = [worker_dto]
        
        with patch('controllers.pila_controller.AdaptadorScheduler') as MockScheduler, \
             patch.object(controller, '_start_simulation_thread') as mock_start, \
             patch('PyQt6.QtWidgets.QApplication.processEvents'):
             
             controller._handle_run_manual_from_visual_editor(mock_dialog)
             
             mock_start.assert_called_once()
             # Verify auto-assignment of worker
             args = MockScheduler.call_args[1]
             flow = args['production_flow']
             assert flow[0]['workers'][0]['name'] == 'Juan'

             assert flow[0]['workers'][0]['name'] == 'Juan'

    def test_add_lote_to_pila_clicked(self, controller):
        """Verifica añadir un lote a la pila de planificación."""
        # Setup mock widget
        mock_calc_widget = MagicMock(spec=CalculateTimesWidget)
        
        # Explicitly attach attributes that might be dynamic
        mock_calc_widget.lote_search_results = MagicMock()
        mock_calc_widget.define_flow_button = MagicMock()
        mock_calc_widget._update_plan_display = MagicMock()
        
        controller.view.pages = {"calculate": mock_calc_widget}
        
        # Setup selection
        mock_item = MagicMock()
        mock_item.data.return_value = (1, "LOTE-001") # ID, Código
        mock_calc_widget.lote_search_results.currentItem.return_value = mock_item
        
        # Initialize planning session list
        mock_calc_widget.planning_session = []
        
        controller._on_add_lote_to_pila_clicked()
        
        # Verificar que se añadió a la sesión
        assert len(mock_calc_widget.planning_session) == 1
        entry = mock_calc_widget.planning_session[0]
        assert entry['lote_template_id'] == 1
        assert entry['lote_codigo'] == "LOTE-001"
        assert entry['unidades'] == 1
        
        # Verificar actualizaciones de UI
        mock_calc_widget.define_flow_button.setEnabled.assert_called_with(True)
        mock_calc_widget._update_plan_display.assert_called_once()
