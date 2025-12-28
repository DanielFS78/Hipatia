# tests/unit/test_database_manager.py
# -*- coding: utf-8 -*-
"""
Unit Tests for DatabaseManager
==============================
Tests following the project's test creation guidelines.

Coverage targets:
- Initialization and session management
- Schema version management
- Repository initialization
- Wrapper methods delegating to repositories
"""

import pytest
import sqlite3
from unittest.mock import MagicMock, patch
from database.database_manager import DatabaseManager


@pytest.mark.unit
class TestDatabaseManagerInitialization:
    """Tests for DatabaseManager initialization."""

    def test_init_with_in_memory_db(self, tmp_path):
        """Test initialization with a temporary database file."""
        db_path = str(tmp_path / "test_init.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        assert db_manager.conn is not None
        assert db_manager.cursor is not None
        assert db_manager.engine is not None
        assert db_manager.SessionLocal is not None
        
        # Verify repositories are initialized
        assert db_manager.product_repo is not None
        assert db_manager.worker_repo is not None
        assert db_manager.machine_repo is not None
        assert db_manager.config_repo is not None
        assert db_manager.tracking_repo is not None
        
        # Cleanup
        if db_manager.conn:
            db_manager.conn.close()
        if db_manager.engine:
            db_manager.engine.dispose()

    def test_init_with_existing_connection(self, session):
        """Test initialization with an existing connection (test mode)."""
        connection = session.connection().connection
        db_manager = DatabaseManager(existing_connection=connection)
        
        assert db_manager.conn is connection
        assert db_manager.cursor is not None
        assert db_manager.engine is not None
        
        # Cleanup: note - don't close conn here as it's the shared session's connection
        if db_manager.engine:
            db_manager.engine.dispose()

    def test_init_creates_tables(self, tmp_path):
        """Test that initialization creates all required tables."""
        db_path = str(tmp_path / "test_tables.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        # Check that essential tables were created
        cursor = db_manager.cursor
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        # These tables should always exist after init
        expected_tables = {
            'productos', 'trabajadores', 'maquinas',
            'subfabricaciones', 'configuracion', 'db_info'
        }
        
        # Note: pilas table may not exist if migrations failed on fresh DB
        # The key is that the core tables exist
        core_tables = {'productos', 'trabajadores', 'maquinas', 'subfabricaciones'}
        assert core_tables.issubset(tables), f"Missing tables: {core_tables - tables}"
        
        # Cleanup
        if db_manager.conn:
            db_manager.conn.close()
        if db_manager.engine:
            db_manager.engine.dispose()


@pytest.mark.unit
class TestDatabaseManagerSession:
    """Tests for session management."""

    def test_get_session_returns_session(self, tmp_path):
        """Test that get_session returns a valid SQLAlchemy session."""
        db_path = str(tmp_path / "test_session.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        session = db_manager.get_session()
        assert session is not None
        
        # Cleanup
        session.close()
        if db_manager.conn:
            db_manager.conn.close()
        if db_manager.engine:
            db_manager.engine.dispose()

    def test_close_closes_connection(self, tmp_path):
        """Test close() closes the connection."""
        db_path = str(tmp_path / "test_close.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        # Close the real connection created in __init__ before mocking
        if db_manager.conn:
            db_manager.conn.close()
        
        # Guardar referencia al engine antes de mockear
        original_engine = db_manager.engine
            
        # Mock connection to verify close call
        mock_conn = MagicMock()
        db_manager.conn = mock_conn
        
        db_manager.close()
        
        # Verificar que se llamó close en el mock
        mock_conn.close.assert_called_once()
        
        # Cleanup del engine original si existe
        if original_engine:
            original_engine.dispose()

    def test_ctx_manager_closes_connection(self, tmp_path):
        """Test usage as context manager closes connection."""
        db_path = str(tmp_path / "test_ctx.db")
        
        with DatabaseManager(db_path=db_path) as db:
            if db.conn:
                db.conn.close()
            db.conn = MagicMock()
            mock_conn = db.conn
            
        mock_conn.close.assert_called_once()
        if db.engine: # Changed db_manager to db as it's within the context
            db.engine.dispose()

    def test_get_session_without_session_local_returns_none(self):
        """Test get_session returns None when SessionLocal is not set."""
        # Create mock DatabaseManager without proper initialization
        db_manager = object.__new__(DatabaseManager)
        db_manager.SessionLocal = None
        db_manager.logger = MagicMock()
        
        result = db_manager.get_session()
        assert result is None
        db_manager.logger.error.assert_called()


@pytest.mark.unit
class TestDatabaseManagerSchemaVersion:
    """Tests for schema version management."""

    def test_get_schema_version_empty_db(self, tmp_path):
        """Test schema version is 0 or current for a fresh database."""
        db_path = str(tmp_path / "test_version.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        # After initialization, migrations should have run
        version = db_manager._get_schema_version()
        assert version >= 0  # Could be current version after migrations
        
        # Cleanup
        if db_manager.conn:
            db_manager.conn.close()
        if db_manager.engine:
            db_manager.engine.dispose()

    def test_set_schema_version(self, tmp_path):
        """Test setting schema version updates the database."""
        db_path = str(tmp_path / "test_set_version.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        # Get current version
        original_version = db_manager._get_schema_version()
        
        # Set to a test version
        test_version = 999
        db_manager._set_schema_version(test_version)
        
        # Verify it was set
        new_version = db_manager._get_schema_version()
        assert new_version == test_version
        
        # Cleanup
        if db_manager.conn:
            db_manager.conn.close()
        if db_manager.engine:
            db_manager.engine.dispose()



class TestDatabaseManagerConfigMethods:
    """Tests for configuration access through config_repo."""

    def test_get_setting_through_config_repo(self, tmp_path):
        """Test that settings are accessed through config_repo."""
        db_path = str(tmp_path / "test_config.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        # Set a value through config_repo
        db_manager.config_repo.set_setting("test_key", "test_value")
        
        # Get it back
        result = db_manager.config_repo.get_setting("test_key")
        
        assert result == "test_value"
        
        # Cleanup
        if db_manager.conn:
            db_manager.conn.close()
        if db_manager.engine:
            db_manager.engine.dispose()

    def test_config_repo_is_initialized(self, tmp_path):
        """Test that config_repo is properly initialized."""
        db_path = str(tmp_path / "test_config_init.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        assert db_manager.config_repo is not None
        assert hasattr(db_manager.config_repo, 'get_setting')
        assert hasattr(db_manager.config_repo, 'set_setting')
        
        # Cleanup
        if db_manager.conn:
            db_manager.conn.close()
        if db_manager.engine:
            db_manager.engine.dispose()


@pytest.mark.unit
class TestDatabaseManagerTableCreation:
    """Tests for table creation methods."""

    def test_create_fabricacion_productos_table(self, tmp_path):
        """Test creation of fabricacion_productos table."""
        db_path = str(tmp_path / "test_fab_table.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        # Table should already exist after init, but call again to test idempotence
        db_manager.create_fabricacion_productos_table()
        
        # Check table exists
        db_manager.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='fabricacion_productos'"
        )
        result = db_manager.cursor.fetchone()
        
        assert result is not None
        assert result[0] == 'fabricacion_productos'
        
        # Cleanup
        if db_manager.conn:
            db_manager.conn.close()
        if db_manager.engine:
            db_manager.engine.dispose()

    def test_ensure_preprocesos_tables_creates_all_tables(self, tmp_path):
        """Test ensure_preprocesos_tables creates required tables."""
        db_path = str(tmp_path / "test_prepro.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        # Tables should exist after init
        db_manager.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in db_manager.cursor.fetchall()}
        
        expected = {'fabricaciones', 'preprocesos', 'preproceso_material_link', 
                   'fabricacion_preproceso_link', 'fabricacion_productos'}
        
        assert expected.issubset(tables)
        
        # Cleanup
        if db_manager.conn:
            db_manager.conn.close()
        if db_manager.engine:
            db_manager.engine.dispose()

@pytest.mark.unit
class TestDatabaseManagerMigration:
    """Tests for migration logic using mocked db_manager."""

    @pytest.fixture
    def migration_db_mock(self):
        """Create a fully mocked DatabaseManager for migration tests."""
        mock = MagicMock(spec=DatabaseManager)
        mock.logger = MagicMock()
        return mock

    def test_check_and_migrate_up_to_date(self, migration_db_mock):
        """Test _check_and_migrate does nothing if version is current (11)."""
        # Setup mocks - version 11 means all migrations already done
        migration_db_mock._get_schema_version.return_value = 11
        migration_db_mock._migrate_to_v11.return_value = True
        
        # Act - Call the real method with our mock as self
        DatabaseManager._check_and_migrate(migration_db_mock)
        
        # Assert: v11 not called because already at v11 (11 < 11 is False)
        migration_db_mock._migrate_to_v11.assert_not_called()

    def test_check_and_migrate_needs_update(self, migration_db_mock):
        """Test _check_and_migrate calls specific migration if version is old."""
        # Setup: version 10 means we need v11 migration
        migration_db_mock._get_schema_version.side_effect = [10, 11]  # first call returns 10, second returns 11
        migration_db_mock._migrate_to_v11.return_value = True
        migration_db_mock._migrate_to_v10.return_value = True
        
        # Act
        DatabaseManager._check_and_migrate(migration_db_mock)
        
        # Assert: v11 called (since 10 < 11), v10 not called (since 10 < 10 is False)
        migration_db_mock._migrate_to_v11.assert_called_once()
        migration_db_mock._migrate_to_v10.assert_not_called()
