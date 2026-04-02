"""Tests para ProductionTaskInspector (panel de inspección de tareas)."""
import pytest
from PyQt6.QtCore import Qt, QDate, QDateTime
from datetime import datetime
from unittest.mock import MagicMock

from ui.widgets.production_flow.inspector_panel import ProductionTaskInspector

@pytest.fixture
def sample_task_data():
    return {
        'id': 'T1',
        'task': {
            'name': 'Test Task',
            'duration': 15
        },
        'trigger_units': 5,
        'config': {
            'start_condition': {
                'type': 'dependency',
                'value': 0
            },
            'min_predecessor_units': 2,
            'is_cycle_start': True,
            'units_per_cycle': 1,
            'next_cyclic_task_index': None,
            'machine_id': 1,
            'workers': ['W1']
        }
    }

@pytest.fixture
def available_tasks():
    return [
        {'id': 'T0', 'task': {'name': 'Previous Task', 'duration': 10}},
        {'id': 'T1', 'task': {'name': 'Test Task', 'duration': 15}},
        {'id': 'T2', 'task': {'name': 'Next Task', 'duration': 20}}
    ]

@pytest.fixture
def machines():
    m1 = MagicMock(spec=["id", "nombre"])
    m1.id = 1
    m1.nombre = "Machine A"
    m2 = MagicMock(spec=["id", "nombre"])
    m2.id = 2
    m2.nombre = "Machine B"
    return [m1, m2]

@pytest.fixture
def available_workers():
    return ['W1', 'W2', 'W3']

@pytest.mark.unit
class TestProductionTaskInspector:

    def test_init_and_clear(self, qtbot):
        inspector = ProductionTaskInspector()
        qtbot.addWidget(inspector)
        
        assert inspector.current_task_id is None
        
        # Call clear
        inspector.clear()
        assert not inspector.content_scroll.isVisibleTo(inspector)
        assert inspector.placeholder.isVisibleTo(inspector)

    def test_set_task(self, qtbot, sample_task_data, available_tasks, machines, available_workers):
        inspector = ProductionTaskInspector()
        qtbot.addWidget(inspector)
        
        inspector.set_task(sample_task_data, available_tasks, machines, available_workers)
        
        # Verify UI visibility
        assert inspector.content_scroll.isVisibleTo(inspector)
        assert not inspector.placeholder.isVisibleTo(inspector)
        
        # Verify header
        assert inspector.widgets.title.text() == 'Test Task'
        assert inspector.widgets.duration_label.text() == 'Duración: 15 min'

        # Verify condition dependency
        assert inspector.widgets.dependency_radio.isChecked()
        assert inspector.widgets.min_units_spin.value() == 2

        # Verify cycle marker
        assert inspector.widgets.cycle_start_cb.isChecked()

        # Verify Goals
        assert inspector.widgets.units_spin.value() == 5

        # Verify Workers
        assert inspector.widgets.assigned_workers_list.count() == 1
        worker_item = inspector.widgets.assigned_workers_list.item(0)
        assert worker_item is not None
        assert worker_item.text() == 'W1'

    def test_set_task_with_date_condition(self, qtbot):
        inspector = ProductionTaskInspector()
        qtbot.addWidget(inspector)
        
        dt = QDateTime.currentDateTime()
        data = {
            'id': 'T1',
            'config': {
                'start_condition': {
                    'type': 'date',
                    'value': dt
                }
            }
        }
        
        inspector.set_task(data)
        assert inspector.widgets.start_date_radio.isChecked()
        assert inspector.widgets.start_date_edit.dateTime() == dt

    def test_signal_emitting(self, qtbot, sample_task_data, available_tasks, machines, available_workers):
        inspector = ProductionTaskInspector()
        qtbot.addWidget(inspector)
        
        inspector.set_task(sample_task_data, available_tasks, machines, available_workers)
        
        # We replace the actual emit function
        inspector.configChanged = MagicMock(spec=["emit"])
        
        # Change machine combo to index 2 (Machine B)
        inspector.widgets.machine_combo.setCurrentIndex(2)
        # Check through configChanged signal directly
        inspector.configChanged.emit.assert_any_call('T1', 'machine_id', 2)

        # Change dependency
        inspector.widgets.dependency_combo.setCurrentIndex(1)
        inspector.configChanged.emit.assert_any_call('T1', 'previous_task_index', 2) # T2 is at idx 2

        # Change next cyclic
        inspector.widgets.next_cyclic_combo.setCurrentIndex(1)
        # next_cyclic_combo index 0 is Ninguna(None). Index 1 is T0 (idx 0).
        inspector.configChanged.emit.assert_any_call('T1', 'next_cyclic_task_index', 0)

    def test_assign_unassign_worker(self, qtbot, sample_task_data, available_workers):
        inspector = ProductionTaskInspector()
        qtbot.addWidget(inspector)
        
        inspector.set_task(sample_task_data, None, None, available_workers)
        
        inspector.configChanged = MagicMock(spec=["emit"])
        
        # Select from available and assign
        item = inspector.widgets.available_workers_list.item(0)  # Should be W2
        assert item is not None
        item.setSelected(True)
        
        inspector._on_assign_worker()
        
        # Check that it emitted configChanged and refreshed list
        assert inspector.configChanged.emit.called
        assert inspector.widgets.assigned_workers_list.count() == 2
        assert inspector.widgets.available_workers_list.count() == 1

        # Select from assigned and unassign
        assigned_item = inspector.widgets.assigned_workers_list.item(1)  # Should be W2
        assert assigned_item is not None
        assigned_item.setSelected(True)
        
        inspector._on_unassign_worker()
        
        # Check again
        assert inspector.widgets.assigned_workers_list.count() == 1
        assert inspector.widgets.available_workers_list.count() == 2

    def test_get_selected_assigned_worker(self, qtbot, sample_task_data):
        inspector = ProductionTaskInspector()
        qtbot.addWidget(inspector)
        
        inspector.set_task(sample_task_data)
        
        # No selection
        assert inspector.get_selected_assigned_worker() is None
        
        # Select W1
        item = inspector.widgets.assigned_workers_list.item(0)
        assert item is not None
        item.setSelected(True)
        assert inspector.get_selected_assigned_worker() == 'W1'
