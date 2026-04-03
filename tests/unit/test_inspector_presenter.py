"""Tests para InspectorPresenter."""
import pytest
from ui.widgets.production_flow.inspector_presenter import InspectorPresenter

@pytest.fixture
def presenter():
    return InspectorPresenter()

@pytest.mark.unit
class TestInspectorPresenter:

    def test_set_task_none(self, presenter):
        presenter.set_task(None)
        assert presenter.current_task_id is None
        assert presenter.current_task_data == {}
        assert presenter.all_possible_workers == []

    def test_set_task_valid(self, presenter):
        data = {'id': 'T1', 'config': {'workers': ['W1', {'name': 'W2', 'rule': None}]}}
        presenter.set_task(data, ['W1', 'W2', 'W3'])
        
        assert presenter.current_task_id == 'T1'
        assert presenter.current_task_data == data
        assert presenter.all_possible_workers == ['W1', 'W2', 'W3']

    def test_get_workers_lists_empty(self, presenter):
        assigned, available = presenter.get_workers_lists()
        assert assigned == []
        assert available == []

    def test_get_workers_lists(self, presenter):
        data = {'id': 'T1', 'config': {'workers': ['W1', {'name': 'W2', 'rule': None}]}}
        presenter.set_task(data, ['W1', 'W2', 'W3', 'W4'])
        
        assigned, available = presenter.get_workers_lists()
        assert assigned == ['W1', 'W2']
        assert available == ['W3', 'W4']

    def test_assign_workers(self, presenter):
        data = {'id': 'T1', 'config': {'workers': ['W1']}}
        presenter.set_task(data, ['W1', 'W2', 'W3'])
        
        updated = presenter.assign_workers(['W2'])
        assert len(updated) == 2
        assert updated[0] == 'W1'
        assert updated[1] == {'name': 'W2', 'rule': None}

        # Assign existing
        updated = presenter.assign_workers(['W1'])
        assert len(updated) == 2
        assert updated[0] == 'W1'

    def test_unassign_workers(self, presenter):
        data = {'id': 'T1', 'config': {'workers': ['W1', {'name': 'W2', 'rule': None}]}}
        presenter.set_task(data, ['W1', 'W2', 'W3'])
        
        updated = presenter.unassign_workers(['W2'])
        assert len(updated) == 1
        assert updated[0] == 'W1'

    def test_build_dependency_list(self, presenter):
        presenter.set_task({'id': 'T2'}, [])
        all_tasks = [
            {'id': 'T1', 'task': {'name': 'First'}},
            {'id': 'T2', 'task': {'name': 'Second'}},
            {'id': 'T3', 'task': {'name': 'Third'}}
        ]
        
        deps = presenter.build_dependency_list(all_tasks)
        
        assert len(deps) == 2
        assert deps[0] == ("0: First", 0)
        assert deps[1] == ("2: Third", 2)
