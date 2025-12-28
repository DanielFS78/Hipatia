# tests/e2e/test_label_counter_e2e.py
import pytest
from database.repositories.label_counter_repository import LabelCounterRepository
from database.models import Fabricacion
from core.dtos import LabelRangeDTO

@pytest.mark.e2e
class TestLabelCounterE2E:

    def test_full_label_counter_flow(self, session):
        """
        Simulates a real usage flow:
        1. Create a Fabricacion.
        2. Request labels for it multiple times.
        3. Verify persistence across "sessions" (re-instantiating repo).
        """
        # Setup Dependency
        fab = Fabricacion(codigo="E2E-FAB-LABELS", descripcion="E2E Labels Test")
        session.add(fab)
        session.commit()
        fab_id = fab.id
        
        # 1. First interaction
        repo1 = LabelCounterRepository(lambda: session)
        range1 = repo1.get_next_unit_range(fab_id, 100)
        assert range1.start == 1
        assert range1.end == 100
        
        # 2. Second interaction (simulating new request/component logic)
        repo2 = LabelCounterRepository(lambda: session)
        range2 = repo2.get_next_unit_range(fab_id, 50)
        assert range2.start == 101
        assert range2.end == 150
        
        # 3. Third interaction
        range3 = repo1.get_next_unit_range(fab_id, 1)
        assert range3.start == 151
        assert range3.end == 151
