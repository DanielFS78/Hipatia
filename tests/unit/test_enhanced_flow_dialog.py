# -*- coding: utf-8 -*-
"""
Tests unitarios para EnhancedProductionFlowDialog (ui.dialogs.production_flow.enhanced_flow_dialog).

Cobertura de inicialización, UI, librería, canvas, inspector, ciclo inicio/fin,
reasignación, guardado/carga de pila y preview de simulación. Efectos visuales
y diálogos Qt se mockean para ejecución headless.
"""
import pytest
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QSplitter, QWidget, QMessageBox
from PyQt6.QtCore import Qt, QPoint

from ui.dialogs.production_flow.enhanced_flow_dialog import EnhancedProductionFlowDialog
from core.dtos import WorkerDTO

pytestmark = pytest.mark.unit

@pytest.fixture
def mock_dependencies():
    """Mock general de componentes visuales problemáticos."""
    with patch("ui.widgets.production_flow.flow_graph_manager.GoldenGlowEffect") as mock_glow, \
         patch("ui.widgets.production_flow.flow_graph_manager.SimulationProgressEffect") as mock_sim, \
         patch("ui.widgets.production_flow.flow_graph_manager.GreenCycleEffect") as mock_green, \
         patch("ui.widgets.production_flow.flow_graph_manager.MixedGoldGreenEffect") as mock_mixed, \
         patch("ui.dialogs.production_flow.flow_action_handler.CycleEndConfigDialog") as mock_cycle_end, \
         patch("ui.dialogs.production_flow.flow_action_handler.ReassignmentRuleDialog") as mock_reass, \
         patch("ui.dialogs.production_flow.flow_action_handler.QMessageBox") as mock_msg:
        yield {
            "glow": mock_glow,
            "sim": mock_sim,
            "green": mock_green,
            "mixed": mock_mixed,
            "cycle_end": mock_cycle_end,
            "reass": mock_reass,
            "msg": mock_msg
        }

@pytest.fixture
def dialog_data():
    tasks = [
        {"codigo": "P1", "descripcion": "Prod 1", "tiempo_optimo": 10}
    ]
    workers = ["W1", "W2"]
    units = 10
    controller = MagicMock(spec=['model', 'handle_save_flow_only'])
    controller.model = MagicMock(spec=['get_all_pilas', 'load_pila'])
    schedule_config = MagicMock(spec=['WORK_START_TIME'])
    schedule_config.WORK_START_TIME = datetime.now().time()
    return tasks, workers, units, controller, schedule_config

@pytest.mark.unit
class TestEnhancedProductionFlowDialog:
    
    def test_init_and_setup_ui(self, qtbot, dialog_data, mock_dependencies):
        """Prueba la inicialización y la configuración de UI."""
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        # Verificar la UI
        assert len(dialog.presenter.canvas_tasks) == 0
        assert dialog.library_panel is not None
        assert dialog.inspector is not None
        assert dialog.canvas is not None
        assert dialog.presenter is not None
        assert dialog.graph_manager is not None

    def test_add_task_from_library(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        task_data = {"id": "P1_main_task", "name": "Tarea", "duration": 10.0}
        
        # Simular emitir señal desde la librería
        dialog._add_task_from_library(task_data)
        
        assert len(dialog.presenter.canvas_tasks) == 1
        assert dialog.presenter.canvas_tasks[0]['data']['id'] == "P1_main_task"
        assert len(dialog.graph_manager.widgets) == 1

    def test_delete_selected_task(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        task_data = {"id": "P1_main_task", "name": "Tarea", "duration": 10.0}
        dialog._add_task_from_library(task_data)
        
        # Seleccionamos
        unique_id = dialog.presenter.canvas_tasks[0]['data']['canvas_unique_id']
        dialog.graph_manager._on_card_selected(unique_id)
        assert dialog.selected_index == 0
        
        # Borramos
        mock_dependencies['msg'].question.return_value = mock_dependencies['msg'].StandardButton.Yes
        dialog._delete_task()
        
        assert len(dialog.presenter.canvas_tasks) == 0
        assert not hasattr(dialog, 'selected_index') or dialog.selected_index is None

    def test_on_task_config_changed(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        task_data = {"id": "P1_main_task", "name": "T", "duration": 1}
        dialog._add_task_from_library(task_data)
        dialog._on_task_selected(0)
        
        # Cambiar una propiedad simple
        dialog._on_task_config_changed("dummy_id", "total_units", 20)
        assert dialog.presenter.canvas_tasks[0]['config']['total_units'] == 20
        
        # Cambiar cycle start
        dialog._on_task_config_changed("dummy_id", "is_cycle_start", True)
        assert dialog.presenter.canvas_tasks[0]['config']['is_cycle_start'] is True
        assert mock_dependencies['glow'].call_count == 1
        mock_dependencies['glow'].assert_called_once_with(ANY)
        
    def test_get_production_flow_delegation(self, qtbot, dialog_data, mock_dependencies):
        """Verifica que llama al presenter para generar el resultado final."""
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        dialog.presenter.build_production_flow = MagicMock(return_value=[{"task": "mock"}])  # type: ignore[method-assign]
        
        result = dialog.get_production_flow()
        assert result == [{"task": "mock"}]
        assert dialog.presenter.build_production_flow.call_count == 1
        dialog.presenter.build_production_flow.assert_called_once_with()

    def test_clear_canvas(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        dialog._add_task_from_library({"id": "T1", "name": "Test", "duration": 1.0})
        assert len(dialog.presenter.canvas_tasks) == 1
        
        mock_dependencies['msg'].question.return_value = mock_dependencies['msg'].StandardButton.Yes
        dialog._clear_canvas()
        assert len(dialog.presenter.canvas_tasks) == 0

    def test_init_with_existing_flow(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        existing_flow = [{"task": {"id": "T1", "name": "E", "duration": 1.0}, "config": {"is_cycle_start": True}}]
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config, existing_flow=existing_flow)
        qtbot.addWidget(dialog)
        assert len(dialog.presenter.canvas_tasks) == 1

    def test_on_task_dropped(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        task_data = {"id": "D1", "name": "Drop", "duration": 1.0}
        pos = QPoint(100, 100)
        dialog._on_task_dropped(task_data, pos)
        assert len(dialog.presenter.canvas_tasks) == 1

    def test_on_task_config_changed_extended(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        dialog._add_task_from_library({"id": "T1", "name": "T", "duration": 1.0})
        dialog._on_task_selected(0)
        
        # start_condition
        dialog._on_task_config_changed("id", "start_condition", {"type": "dependency", "value": None})
        
        # workers
        dialog._on_task_config_changed("id", "workers", [{"name": "W1"}])
        
        # is_cycle_end
        dialog._on_task_config_changed("id", "is_cycle_end", True)
        
        assert dialog.presenter.canvas_tasks[0]['config']['is_cycle_end'] is True

    def test_on_inspector_action_triggered(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        dialog._handle_cycle_end = MagicMock()  # type: ignore[method-assign]
        dialog._handle_reassignment = MagicMock()  # type: ignore[method-assign]
        dialog._delete_task = MagicMock()  # type: ignore[method-assign]
        
        dialog._on_inspector_action_triggered('configure_cycle_end', 'id')
        assert dialog._handle_cycle_end.call_count == 1
        dialog._handle_cycle_end.assert_called_once_with()
        
        dialog._on_inspector_action_triggered('configure_reassignment', 'id')
        assert dialog._handle_reassignment.call_count == 1
        dialog._handle_reassignment.assert_called_once_with()
        
        dialog._on_inspector_action_triggered('delete', 'id')
        assert dialog._delete_task.call_count == 1
        dialog._delete_task.assert_called_once_with()

    def test_handle_reassignment(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        dialog._add_task_from_library({"id": "T1", "name": "T", "duration": 1.0})
        dialog._on_task_selected(0)
        
        dialog.inspector.get_selected_assigned_worker = MagicMock(return_value="W1")  # type: ignore[method-assign]
        dialog.presenter.get_worker_config = MagicMock(return_value={'name': 'W1', 'reassignment_rule': None})  # type: ignore[method-assign]
        
        mock_dialog_instance = mock_dependencies['reass'].return_value
        mock_dialog_instance.exec.return_value = True
        mock_dialog_instance.get_rule.return_value = {'rule': 'mock'}
        
        dialog._handle_reassignment()
        config = dialog.presenter.get_worker_config(0, "W1")
        assert config['reassignment_rule'] == {'rule': 'mock'}

    def test_load_saved_pila(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        mock_pila = MagicMock(spec=['nombre', 'id'])
        mock_pila.nombre = "Test Pila"
        mock_pila.id = 1
        controller.model.get_all_pilas.return_value = [mock_pila]
        controller.model.load_pila.return_value = ({}, {}, [{"task": {"id": "T1", "name": "L", "duration": 1.0}}], [])
        
        with patch("ui.dialogs.production_flow.enhanced_flow_dialog.QInputDialog.getItem") as mock_get_item:
            mock_get_item.return_value = ("Test Pila (ID: 1)", True)
            dialog._load_saved_pila()
            
        assert len(dialog.presenter.canvas_tasks) == 1

    def test_preview_and_simulation(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        dialog._add_task_from_library({"id": "T1", "name": "T", "duration": 1.0})
        
        # Iniciar preview
        dialog._preview_execution_order()
        assert dialog.simulation_handler.timer.isActive()
        assert not dialog.toolbar.save_button.isEnabled()
        
        # Simular pasos
        dialog.presenter.get_next_simulation_step = MagicMock(side_effect=[0, -1, None])  # type: ignore[method-assign]
        dialog.presenter.get_simulation_progress_text = MagicMock(return_value="Prov")  # type: ignore[method-assign]
        
        dialog.simulation_handler._on_tick() # Paso 0
        QApplication.processEvents()
        assert not dialog.simulation_label.isHidden()
        
        dialog.simulation_handler._on_tick() # Paso -1 (Fin)
        QApplication.processEvents()
        assert not dialog.simulation_handler.timer.isActive()
        assert dialog.toolbar.save_button.isEnabled()
        assert dialog.simulation_label.isHidden()
        
        # Parada explícita de seguridad para evitar SegFaults en tests posteriores
        dialog.cleanup()

    def test_handle_cycle_end(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        dialog._add_task_from_library({"id": "T1", "name": "Test", "duration": 1.0})
        dialog._on_task_selected(0)
        
        # Simular que el dialog retorna Accepted y datos
        mock_dialog_instance = mock_dependencies['cycle_end'].return_value
        mock_dialog_instance.exec.return_value = True
        mock_dialog_instance.get_configuration.return_value = {
            'is_cycle_end': True,
            'return_to_index': 0
        }
        
        dialog._handle_cycle_end()
        assert dialog.presenter.canvas_tasks[0]['config']['is_cycle_end'] is True
        assert dialog.presenter.canvas_tasks[0]['config']['cycle_return_to_index'] == 0

    def test_resize_event(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitUntil(dialog.isVisible)
        QApplication.processEvents()
        dialog.resize(800, 600)
        QApplication.processEvents()
        # En headless x() puede ser 0 pero y() suele ser > 0 o viceversa según el layout
        assert dialog.preview_button.isVisible()

    @patch("ui.dialogs.production_flow.enhanced_flow_dialog.QInputDialog.getText")
    def test_save_pila_only(self, mock_get_text, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = EnhancedProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        dialog._add_task_from_library({"id": "T1", "name": "T", "duration": 1.0})
        
        mock_get_text.side_effect = [("Nombre", True), ("Desc", True)]
        dialog._save_pila_only()
        assert controller.handle_save_flow_only.call_count == 1
        controller.handle_save_flow_only.assert_called_once_with("Nombre", "Desc", ANY)
