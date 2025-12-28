
import pytest
from unittest.mock import MagicMock
from database.repositories.configuration_repository import ConfigurationRepository
from database.models import Configuration

@pytest.fixture
def session_no_close(session):
    original_close = session.close
    session.close = MagicMock()
    yield session
    session.close = original_close

@pytest.mark.integration
class TestConfigurationIntegration:
    """Tests de integración para persistencia de configuración."""

    def test_configuration_persistence(self, session_no_close):
        """Verifica que la configuración persiste entre instancias del repositorio."""
        
        # 1. Guardar con una instancia
        repo1 = ConfigurationRepository(lambda: session_no_close)
        repo1.set_setting("app_theme", "dark")
        
        # 2. Leer con otra instancia (misma sesión por ahora, pero simula acceso global)
        repo2 = ConfigurationRepository(lambda: session_no_close)
        val = repo2.get_setting("app_theme")
        
        assert val == "dark"

    def test_configuration_holidays_persistence(self, session_no_close):
        """Verifica persistencia compleja (JSON) de festivos."""
        from datetime import date
        
        repo = ConfigurationRepository(lambda: session_no_close)
        d = date(2025, 12, 31)
        repo.add_holiday(d, "New Year Eve")
        
        # Verificar en BD raw
        raw_config = session_no_close.query(Configuration).filter_by(clave="holidays").first()
        assert raw_config is not None
        assert "2025-12-31" in raw_config.valor
