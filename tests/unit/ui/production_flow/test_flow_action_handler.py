import pytest
from unittest.mock import MagicMock, patch, create_autospec
from PyQt6.QtWidgets import QWidget, QMessageBox, QInputDialog

pytestmark = pytest.mark.unit

# Imports para specs
from controllers.app_controller import AppController
from ui.dialogs.production_flow.enhanced_flow_presenter import EnhancedFlowPresenter
from ui.widgets.production_flow.flow_graph_manager import FlowGraphManager
from ui.widgets.production_flow.inspector_panel import ProductionTaskInspector
from ui.widgets.production_flow.library_panel import TaskLibraryPanel
from ui.dialogs.production_flow.flow_action_handler import FlowActionHandler

@pytest.fixture
def action_handler_deps(qtbot):
    parent = QWidget()
    presenter = create_autospec(EnhancedFlowPresenter, instance=True)
    presenter.canvas_tasks = []  # Atributo de instancia no detectado por autospec
    graph_manager = create_autospec(FlowGraphManager, instance=True)
    controller = create_autospec(AppController, instance=True)
    qtbot.addWidget(parent)
    handler = FlowActionHandler(parent, presenter, graph_manager, controller)
    return handler, presenter, graph_manager, controller, parent

def test_handle_cycle_end(action_handler_deps):
    handler, presenter, graph_manager, _, _ = action_handler_deps
    mock_sim = object()

    with patch('ui.dialogs.production_flow.flow_action_handler.CycleEndConfigDialog', autospec=True) as MockDialog:
        mock_dialog = MockDialog.return_value
        mock_dialog.exec.return_value = True
        mock_dialog.get_configuration.return_value = {'is_cycle_end': True, 'return_to_index': 0}
        
        presenter.apply_cycle_end_config.return_value = True
        
        handler.handle_cycle_end(0, mock_sim)
        
        presenter.apply_cycle_end_config.assert_called_once_with(0, True, 0)
        graph_manager.update_connections.assert_called_once_with(0)
        graph_manager.update_all_cycle_effects.assert_called_once_with(mock_sim)

def test_handle_reassignment(action_handler_deps):
    handler, presenter, _, _, _ = action_handler_deps
    
    presenter.get_worker_config.return_value = {'name': 'Worker 1', 'reassignment_rule': None}
    presenter.get_task.return_value = {'data': {}}
    
    with patch('ui.dialogs.production_flow.flow_action_handler.ReassignmentRuleDialog', autospec=True) as MockDialog:
        mock_dialog = MockDialog.return_value
        mock_dialog.exec.return_value = True
        mock_dialog.get_rule.return_value = 'some_rule'
        
        handler.handle_reassignment(0, 'Worker 1')
        
        assert presenter.get_worker_config.return_value['reassignment_rule'] == 'some_rule'
        presenter.get_worker_config.assert_called_once_with(0, 'Worker 1')
        presenter.get_task.assert_called_once_with(0)

def test_delete_task_confirmed(action_handler_deps):
    handler, _, graph_manager, _, _ = action_handler_deps
    inspector = create_autospec(ProductionTaskInspector, instance=True)
    
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
        res = handler.delete_task(0, inspector)
        assert res is None
        graph_manager.remove_task_widget.assert_called_once_with(0)
        inspector.clear.assert_called_once_with()

def test_clear_canvas_confirmed(action_handler_deps):
    handler, _, graph_manager, _, _ = action_handler_deps
    inspector = create_autospec(ProductionTaskInspector, instance=True)
    
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
        res = handler.clear_canvas(inspector)
        assert res is None
        graph_manager.clear.assert_called_once_with()
        inspector.clear.assert_called_once_with()

def test_save_pila_only(action_handler_deps):
    handler, presenter, graph_manager, controller, _ = action_handler_deps
    presenter.build_production_flow.return_value = []
    
    # QInputDialog.getText es estático; autospec en patch.object deja un mock no invocable.
    with patch(
        "ui.dialogs.production_flow.flow_action_handler.QInputDialog.getText",
    ) as mock_get_text:
        mock_get_text.side_effect = [("Nombre", True), ("Desc", True)]
        handler.save_pila_only()
        graph_manager.synchronize_positions.assert_called_once_with()
        controller.handle_save_flow_only.assert_called_once_with('Nombre', 'Desc', [])

def test_initialize_library(action_handler_deps):
    handler, presenter, _, _, _ = action_handler_deps
    library_panel = create_autospec(TaskLibraryPanel, instance=True)
    tasks: list[object] = []
    
    handler.initialize_library(tasks, library_panel)
    presenter.prepare_task_data.assert_called_once_with(tasks)
    library_panel.populate_tasks.assert_called_once_with()


def test_pila_list_load_api_falls_back_to_model(action_handler_deps):
    handler, _, _, controller, _ = action_handler_deps
    handler._pila_service = None
    model = MagicMock(spec=["get_all_pilas", "load_pila"])
    controller.model = model
    assert handler._pila_list_load_api() is model


def test_load_saved_pila_uses_single_api_for_list_and_load(action_handler_deps):
    handler, _, _, _, _ = action_handler_deps
    api = MagicMock(spec=["get_all_pilas", "load_pila"])
    p = MagicMock(spec=["nombre", "id"])
    p.nombre = "Pila A"
    p.id = 7
    api.get_all_pilas.return_value = [p]
    flow_obj: dict[str, bool] = {"ok": True}
    api.load_pila.return_value = (None, None, flow_obj, None)
    with patch.object(handler, "_pila_list_load_api", return_value=api):
        with patch.object(
            QInputDialog,
            "getItem",
            return_value=("Pila A (ID: 7)", True),
        ):
            cb = MagicMock(spec=["__call__"])
            handler.load_saved_pila(cb)
    api.get_all_pilas.assert_called_once_with()
    api.load_pila.assert_called_once_with(7)
    cb.assert_called_once_with(flow_obj)
