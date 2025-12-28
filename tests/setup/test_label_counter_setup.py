# tests/setup/test_label_counter_setup.py
import pytest
from database.repositories.label_counter_repository import LabelCounterRepository

class TestLabelCounterSetup:
    
    def test_repository_instantiation(self):
        # Just verify we can instantiate it
        repo = LabelCounterRepository(lambda: None)
        assert repo is not None
        assert hasattr(repo, 'get_next_unit_range')

    def test_model_exists(self):
        from database.models import FabricacionContador
        assert FabricacionContador.__tablename__ == 'fabricacion_contadores'
