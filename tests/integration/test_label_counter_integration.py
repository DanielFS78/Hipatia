# tests/integration/test_label_counter_integration.py
import pytest
from database.repositories.label_counter_repository import LabelCounterRepository
from database.models import FabricacionContador, Fabricacion
from core.dtos import LabelRangeDTO

@pytest.mark.integration
class TestLabelCounterRepositoryIntegration:

    @pytest.fixture
    def repo(self, session):
        # session_factory is needed but in integration tests with conftest 
        # normally we pass a factory or the session. 
        # Assuming BaseRepository standard usage with session_factory.
        # We need a callable that returns the session. 
        # But wait, BaseRepository calls session_factory().
        # If we pass lambda: session, it works.
        return LabelCounterRepository(lambda: session)

    @pytest.fixture
    def fabricacion(self, session):
        # Need a fabricacion for FK constraint
        fab = Fabricacion(codigo="FAB-TEST-001", descripcion="Test Fabricacion")
        session.add(fab)
        session.commit()
        return fab

    def test_get_next_unit_range_integration(self, repo, fabricacion):
        # 1. First call - should create counter
        r1 = repo.get_next_unit_range(fabricacion.id, 10)
        
        assert isinstance(r1, LabelRangeDTO)
        assert r1.start == 1
        assert r1.end == 10
        assert r1.count == 10

        # 2. Second call - should increment
        r2 = repo.get_next_unit_range(fabricacion.id, 5)
        
        assert isinstance(r2, LabelRangeDTO)
        assert r2.start == 11
        assert r2.end == 15
        assert r2.count == 5

        # Verify DB state manually
        session = repo.get_session()
        contador = session.query(FabricacionContador).filter_by(fabricacion_id=fabricacion.id).first()
        assert contador.ultimo_numero_unidad == 15

    def test_concurrency_simulation(self, repo, fabricacion):
        # Although strict concurrency is hard to test with sqlite in a single process test,
        # we can verify logic consistency in sequence.
        
        results = []
        for _ in range(5):
            results.append(repo.get_next_unit_range(fabricacion.id, 10))
        
        # Check no overlap
        ranges = [(r.start, r.end) for r in results]
        # Expected: (1,10), (11,20), (21,30), (31,40), (41,50)
        # Note: if previous test ran, start might be higher, so let's check relative consistency
        
        sorted_ranges = sorted(ranges, key=lambda x: x[0])
        
        last_end = sorted_ranges[0][0] - 1
        for start, end in sorted_ranges:
            assert start == last_end + 1
            assert end == start + 9
            last_end = end
