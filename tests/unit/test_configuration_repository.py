
import pytest
from datetime import date
import json
from database.models import Configuration
from database.repositories.configuration_repository import ConfigurationRepository

from unittest.mock import MagicMock

@pytest.fixture
def session_no_close(session):
    original_close = session.close
    session.close = MagicMock()
    yield session
    session.close = original_close

@pytest.fixture
def config_repo(session_no_close):
    return ConfigurationRepository(lambda: session_no_close)

@pytest.mark.unit
class TestConfigurationRepositorySettings:
    """Tests para get_setting y set_setting."""

    def test_get_setting_existing(self, config_repo, session_no_close):
        # Arrange
        item = Configuration(clave="test_key", valor="test_value")
        session_no_close.add(item)
        session_no_close.commit()

        # Act
        val = config_repo.get_setting("test_key")

        # Assert
        assert val == "test_value"

    def test_get_setting_default(self, config_repo, session_no_close):
        val = config_repo.get_setting("non_existent", default_value="default")
        assert val == "default"

    def test_get_setting_none(self, config_repo, session_no_close):
        val = config_repo.get_setting("non_existent")
        assert val is None

    def test_set_setting_new(self, config_repo, session_no_close):
        # Act
        success = config_repo.set_setting("new_key", "new_value")
        
        # Assert
        assert success is True
        item = session_no_close.query(Configuration).filter_by(clave="new_key").first()
        assert item is not None
        assert item.valor == "new_value"

    def test_set_setting_update(self, config_repo, session_no_close):
        # Arrange
        item = Configuration(clave="update_key", valor="old_value")
        session_no_close.add(item)
        session_no_close.commit()

        # Act
        success = config_repo.set_setting("update_key", "new_value")

        # Assert
        assert success is True
        session_no_close.refresh(item)
        assert item.valor == "new_value"
        
    def test_get_default_error_value(self, config_repo, session_no_close):
        """Test el valor por defecto en caso de error global."""
        assert config_repo._get_default_error_value() is None

@pytest.mark.unit
class TestConfigurationRepositoryHolidays:
    """Tests para gestión de festivos."""

    def test_get_holidays_empty(self, config_repo, session_no_close):
        holidays = config_repo.get_holidays()
        assert holidays == []

    def test_get_holidays_valid(self, config_repo, session_no_close):
        # Arrange
        data = '[{"date": "2025-01-01", "description": "New Year"}, "2025-12-25"]'
        config_repo.set_setting("holidays", data)

        # Act
        holidays = config_repo.get_holidays()

        # Assert
        assert len(holidays) == 2
        assert date(2025, 1, 1) in holidays
        assert date(2025, 12, 25) in holidays

    def test_get_holidays_invalid_json(self, config_repo, session_no_close):
        config_repo.set_setting("holidays", "{invalid_json}")
        holidays = config_repo.get_holidays()
        assert holidays == []
        
    def test_get_holidays_attribute_error(self, config_repo, session_no_close):
        """Test para get_holidays con datos mal formados (AttributeError/ValueError)."""
        # Simulamos datos que causen error al procesar (ej: entero en lugar de string/dict)
        data = '[123, {"date": null}, "invalid-date"]' 
        config_repo.set_setting("holidays", data)
        # Mock logger para verificar que se loguea el error
        config_repo.logger = MagicMock()
        
        holidays = config_repo.get_holidays()
        
        # Debería filtrar los errores y devolver lista vacía o lo que pueda parsear
        # 'invalid-date' lanzará ValueError en split
        # 123 lanzará AttributeError (int no tiene split)
        assert holidays == []
        assert config_repo.logger.warning.call_count >= 1

    def test_add_holiday_new(self, config_repo, session_no_close):
        # Act
        d = date(2025, 5, 1)
        success = config_repo.add_holiday(d, "Labor Day")

        # Assert
        assert success is True
        holidays = config_repo.get_holidays()
        assert d in holidays

    def test_add_holiday_existing(self, config_repo, session_no_close):
        # Arrange
        d = date(2025, 5, 1)
        config_repo.add_holiday(d, "Labor Day")

        # Act
        success = config_repo.add_holiday(d, "Duplicate")

        # Assert
        assert success is True
        holidays = config_repo.get_holidays()
        # Should still be 1 because we check for duplicates
        assert len(holidays) == 1

    def test_add_holiday_json_error(self, config_repo, session_no_close):
        """Test add_holiday cuando el JSON de settings está corrupto."""
        config_repo.set_setting("holidays", "{bad_json}")
        d = date(2025, 5, 1)
        # Should initialize empty list and add the new one, seemingly overwriting/ignoring bad data
        success = config_repo.add_holiday(d, "Restored")
        assert success is True
        holidays = config_repo.get_holidays()
        assert len(holidays) == 1
        assert d in holidays
        
    def test_add_holiday_duplicate(self, config_repo, session_no_close):
         # Arrange
        d = date(2025, 5, 1)
        config_repo.add_holiday(d, "Labor Day")
        
        # Act - Try adding again explicitly testing duplicate branch logic if different from above
        # The previous test covers it but let's be explicit
        success = config_repo.add_holiday(d, "Another Description")
        assert success is True

    def test_remove_holiday_existing(self, config_repo, session_no_close):
        # Arrange
        d1 = date(2025, 5, 1)
        d2 = date(2025, 12, 25)
        config_repo.add_holiday(d1)
        config_repo.add_holiday(d2)

        # Act
        success = config_repo.remove_holiday(d1)

        # Assert
        assert success is True
        holidays = config_repo.get_holidays()
        assert d1 not in holidays
        assert d2 in holidays # Ensure d2 was appended (line 165 coverage)

    def test_remove_holiday_non_existent(self, config_repo, session_no_close):
        d = date(2025, 5, 1)
        success = config_repo.remove_holiday(d)
        assert success is True
        
    def test_remove_holiday_json_error(self, config_repo, session_no_close):
        """Test remove_holiday cuando el JSON de settings está corrupto."""
        config_repo.set_setting("holidays", "{bad_json}")
        d = date(2025, 5, 1)
        success = config_repo.remove_holiday(d)
        assert success is False
