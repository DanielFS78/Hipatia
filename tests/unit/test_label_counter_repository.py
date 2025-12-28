# tests/unit/test_label_counter_repository.py
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from database.repositories.label_counter_repository import LabelCounterRepository
from database.models import FabricacionContador
from core.dtos import LabelRangeDTO

class TestLabelCounterRepositoryUnit:

    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=Session)

    @pytest.fixture
    def repo(self, mock_session):
        repo = LabelCounterRepository(lambda: mock_session)
        return repo

    def test_get_next_unit_range_success_existing_counter(self, repo, mock_session):
        # Arrange
        fabricacion_id = 1
        cantidad = 10
        current_counter = FabricacionContador(fabricacion_id=fabricacion_id, ultimo_numero_unidad=50)
        
        # Configure mock query
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first.return_value = current_counter

        # Act
        result = repo.get_next_unit_range(fabricacion_id, cantidad)

        # Assert
        assert isinstance(result, LabelRangeDTO)
        assert result.fabricacion_id == fabricacion_id
        assert result.start == 51
        assert result.end == 60
        assert result.count == 10
        assert current_counter.ultimo_numero_unidad == 60 # Check side effect on object
        mock_session.commit.assert_called_once()

    def test_get_next_unit_range_success_new_counter(self, repo, mock_session):
        # Arrange
        fabricacion_id = 2
        cantidad = 5
        
        # Configure mock query to return None (no existing counter)
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first.return_value = None

        # Act
        result = repo.get_next_unit_range(fabricacion_id, cantidad)

        # Assert
        assert isinstance(result, LabelRangeDTO)
        assert result.fabricacion_id == fabricacion_id
        assert result.start == 1
        assert result.end == 5
        assert result.count == 5
        
        # Verify a new object was added
        mock_session.add.assert_called_once()
        added_obj = mock_session.add.call_args[0][0]
        assert isinstance(added_obj, FabricacionContador)
        assert added_obj.fabricacion_id == fabricacion_id
        assert added_obj.ultimo_numero_unidad == 5
        mock_session.commit.assert_called_once()

    def test_get_next_unit_range_error(self, repo, mock_session):
        # Arrange
        mock_session.query.side_effect = Exception("DB Error")

        # Act
        result = repo.get_next_unit_range(1, 10)

        # Assert
        assert result is None
        mock_session.rollback.assert_called_once()

    def test_close_does_nothing(self, repo):
        # Just ensure it doesn't crash
        repo.close()
