"""
Tests unitarios para DatabaseManager (SQLAlchemy).
Reescrito para la API actual: db_url, engine, SessionLocal, repositorios.
"""
import sys

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from database.database_manager import DatabaseManager
from database.models import Trabajador
from sqlalchemy import create_engine


@pytest.mark.unit
class TestDatabaseManagerFull:
    """Tests completos para DatabaseManager con SQLAlchemy."""

    def test_init_success(self, tmp_path):
        """Test inicialización exitosa con SQLite."""
        db_path = str(tmp_path / "test_init.db")
        db_url = f"sqlite:///{db_path}"
        with DatabaseManager(db_url=db_url) as db:
            assert db.engine is not None
            assert db.SessionLocal is not None

    def test_bootstrap_admin_when_frozen_sqlite_empty(self, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
        """PyInstaller: BD nueva en fichero sin usuarios con login recibe admin/admin."""
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        db_path = str(tmp_path / "frozen_bootstrap.db")
        db_url = f"sqlite:///{db_path}"
        with DatabaseManager(db_url=db_url) as db:
            session = db.get_session()
            try:
                row = session.query(Trabajador).filter(Trabajador.username == "admin").one()
                assert row.activo is True
                assert (row.role or "").lower() == "admin"
            finally:
                session.close()

    def test_init_with_engine(self):
        """Test inicialización con engine pre-configurado."""
        engine = create_engine("sqlite:///:memory:")
        with DatabaseManager(engine=engine) as db:
            assert db.engine is engine
            assert db.SessionLocal is not None

    def test_init_default_url(self):
        """Test inicialización con URL por defecto de DatabaseConfig."""
        with patch('database.database_manager.DatabaseConfig') as mock_config:
            mock_config.get_db_url.return_value = "sqlite:///:memory:"
            mock_config.get_echo_sql.return_value = False
            db = DatabaseManager()
            assert db.engine is not None
            db.close()

    def test_init_general_error(self):
        """Test inicialización con error general."""
        with patch('database.database_manager.create_engine', side_effect=Exception("Boom")):
            with patch('database.database_manager.DatabaseConfig') as mock_config:
                mock_config.get_db_url.return_value = "sqlite:///:memory:"
                mock_config.get_echo_sql.return_value = False
                db = DatabaseManager()
                assert db.engine is None
                assert db.SessionLocal is None
                db.close()

    def test_get_session_success(self, tmp_path):
        """Test get_session devuelve una sesión válida."""
        db_path = str(tmp_path / "test_session.db")
        db_url = f"sqlite:///{db_path}"
        with DatabaseManager(db_url=db_url) as db:
            session = db.get_session()
            assert session is not None
            session.close()

    def test_get_session_not_initialized(self):
        """Test get_session lanza excepción si SessionLocal es None."""
        with patch('database.database_manager.DatabaseConfig') as mock_config:
            mock_config.get_db_url.return_value = "sqlite:///:memory:"
            mock_config.get_echo_sql.return_value = False
            db = DatabaseManager()
            db.SessionLocal = None
            with pytest.raises(Exception, match="Base de datos no inicializada"):
                db.get_session()
            assert db.SessionLocal is None
            db.close()
    def test_close(self, tmp_path):
        """Test cierre correcto de conexiones."""
        db_path = str(tmp_path / "test_close.db")
        db_url = f"sqlite:///{db_path}"
        db = DatabaseManager(db_url=db_url)
        assert db.engine is not None
        db.close()
        assert db.engine is None

    def test_context_manager(self, tmp_path):
        """Test uso como context manager."""
        db_path = str(tmp_path / "test_ctx.db")
        db_url = f"sqlite:///{db_path}"
        with DatabaseManager(db_url=db_url) as db:
            assert db.engine is not None
        # Después de salir del context manager, engine es None
        assert db.engine is None

    def test_db_path_property_sqlite(self, tmp_path):
        """Test propiedad db_path para SQLite."""
        db_path = str(tmp_path / "test_prop.db")
        db_url = f"sqlite:///{db_path}"
        with DatabaseManager(db_url=db_url) as db:
            assert db.db_path == db_path

    def test_db_path_property_non_sqlite(self):
        """Test propiedad db_path devuelve cadena vacía para no-SQLite."""
        engine = create_engine("sqlite:///:memory:")
        with DatabaseManager(db_url="postgresql://user:pass@host/db", engine=engine) as db:
            assert db.db_path == ""

    def test_repositories_initialized(self, tmp_path):
        """Test que los repositorios se inicializan correctamente."""
        db_path = str(tmp_path / "test_repos.db")
        db_url = f"sqlite:///{db_path}"
        with DatabaseManager(db_url=db_url) as db:
            assert hasattr(db, 'product_repo')
            assert hasattr(db, 'worker_repo')
            assert hasattr(db, 'machine_repo')
            assert hasattr(db, 'pila_repo')
            assert hasattr(db, 'tracking_repo')
            assert hasattr(db, 'reports_repo')

    def test_create_tables_if_not_exist(self, tmp_path):
        """Test que create_all se ejecuta durante init."""
        db_path = str(tmp_path / "test_tables.db")
        db_url = f"sqlite:///{db_path}"
        with patch('database.database_manager.Base') as mock_base:
            with DatabaseManager(db_url=db_url) as db:
                assert mock_base.metadata.create_all.call_count == 1
                mock_base.metadata.create_all.assert_called_once_with(bind=db.engine)

    def test_create_tables_error(self, tmp_path):
        """Test manejo de error en _create_tables_if_not_exist."""
        db_path = str(tmp_path / "test_tables_err.db")
        db_url = f"sqlite:///{db_path}"
        with patch('database.database_manager.Base') as mock_base:
            mock_base.metadata.create_all.side_effect = Exception("Table error")
            # No debe lanzar excepción
            db = DatabaseManager(db_url=db_url)
            assert db is not None
            db.close()

    def test_init_repositories_skipped_if_no_session(self):
        """Test que _init_repositories no se ejecuta sin SessionLocal."""
        with patch('database.database_manager.create_engine', side_effect=Exception("Boom")):
            with patch('database.database_manager.DatabaseConfig') as mock_config:
                mock_config.get_db_url.return_value = "sqlite:///:memory:"
                mock_config.get_echo_sql.return_value = False
                db = DatabaseManager()
                assert not hasattr(db, 'product_repo')
                db.close()

    def test_compare_with_db(self, tmp_path):
        """Test compare_with_db delega a SyncService."""
        from core.dtos import DatabaseComparisonDTO
        db_path = str(tmp_path / "test_sync.db")
        db_url = f"sqlite:///{db_path}"
        with DatabaseManager(db_url=db_url) as db:
            with patch('core.sync_service.SyncService', autospec=True) as mock_sync_cls:
                mock_sync = MagicMock(spec=["compare_databases"])
                mock_sync_cls.return_value = mock_sync
                mock_comparison = DatabaseComparisonDTO(tables=[])
                mock_sync.compare_databases.return_value = mock_comparison
                
                result = db.compare_with_db("/tmp/foreign.db")
                
                assert mock_sync.compare_databases.call_count == 1
                mock_sync.compare_databases.assert_called_once_with("/tmp/foreign.db")
                assert result == mock_comparison

    def test_apply_sync_changes(self, tmp_path):
        """Test apply_sync_changes delega a SyncService."""
        from core.dtos import DatabaseComparisonDTO
        db_path = str(tmp_path / "test_apply.db")
        db_url = f"sqlite:///{db_path}"
        with DatabaseManager(db_url=db_url) as db:
            with patch('core.sync_service.SyncService', autospec=True) as mock_sync_cls:
                mock_sync = MagicMock(spec=["apply_changes"])
                mock_sync_cls.return_value = mock_sync
                mock_sync.apply_changes.return_value = 5
                
                mock_comparison = DatabaseComparisonDTO(tables=[])
                result = db.apply_sync_changes(mock_comparison)
                
                assert mock_sync.apply_changes.call_count == 1
                mock_sync.apply_changes.assert_called_once_with(mock_comparison)
                assert result == 5
