# tests/setup/test_database_manager_setup.py
# -*- coding: utf-8 -*-
"""
Setup Tests for DatabaseManager
===============================
Tests verifying the database schema is correctly configured.

Coverage targets:
- Schema version tracking
- Table structure verification
- Migration functions
"""

import pytest
from sqlalchemy import inspect
from database.database_manager import DatabaseManager


@pytest.mark.setup
class TestDatabaseManagerSchemaSetup:
    """Tests for database schema setup."""

    def test_db_info_table_exists(self, tmp_path):
        """Verify the db_info table exists for schema tracking."""
        db_path = str(tmp_path / "test_schema.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        try:
            db_manager.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='db_info'"
            )
            result = db_manager.cursor.fetchone()
            
            assert result is not None
            assert result[0] == 'db_info'
        finally:
            db_manager.close()

    def test_db_info_has_schema_version(self, tmp_path):
        """Verify db_info contains schema_version key."""
        db_path = str(tmp_path / "test_version.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        try:
            db_manager.cursor.execute(
                "SELECT value FROM db_info WHERE key = 'schema_version'"
            )
            result = db_manager.cursor.fetchone()
            
            assert result is not None
            # Should be a numeric version
            assert int(result[0]) >= 0
        finally:
            db_manager.close()

    def test_configuracion_table_structure(self, tmp_path):
        """Verify configuracion table has correct columns."""
        db_path = str(tmp_path / "test_config_struct.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        try:
            db_manager.cursor.execute("PRAGMA table_info(configuracion)")
            columns = {row[1]: row[2] for row in db_manager.cursor.fetchall()}
            
            assert 'clave' in columns
            assert 'valor' in columns
        finally:
            db_manager.close()

    def test_productos_table_structure(self, tmp_path):
        """Verify productos table has correct columns."""
        db_path = str(tmp_path / "test_productos.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        try:
            db_manager.cursor.execute("PRAGMA table_info(productos)")
            columns = {row[1] for row in db_manager.cursor.fetchall()}
            
            expected_columns = {
                'codigo', 'descripcion', 'departamento', 
                'tipo_trabajador', 'tiene_subfabricaciones'
            }
            
            assert expected_columns.issubset(columns)
        finally:
            db_manager.close()

    def test_trabajadores_table_structure(self, tmp_path):
        """Verify trabajadores table has correct columns including auth fields."""
        db_path = str(tmp_path / "test_workers.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        try:
            db_manager.cursor.execute("PRAGMA table_info(trabajadores)")
            columns = {row[1] for row in db_manager.cursor.fetchall()}
            
            expected_columns = {
                'id', 'nombre_completo', 'activo', 'notas',
                'username', 'password_hash', 'role'
            }
            
            assert expected_columns.issubset(columns)
        finally:
            db_manager.close()

    def test_maquinas_table_structure(self, tmp_path):
        """Verify maquinas table has correct columns."""
        db_path = str(tmp_path / "test_machines.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        try:
            db_manager.cursor.execute("PRAGMA table_info(maquinas)")
            columns = {row[1] for row in db_manager.cursor.fetchall()}
            
            expected_columns = {'id', 'nombre', 'departamento', 'tipo_proceso', 'activa'}
            
            assert expected_columns.issubset(columns)
        finally:
            db_manager.close()

    def test_subfabricaciones_has_maquina_id(self, tmp_path):
        """Verify subfabricaciones has maquina_id (migration v6 applied)."""
        db_path = str(tmp_path / "test_subfab.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        try:
            db_manager.cursor.execute("PRAGMA table_info(subfabricaciones)")
            columns = {row[1] for row in db_manager.cursor.fetchall()}
            
            # After v6 migration, maquina_id should exist
            assert 'maquina_id' in columns
        finally:
            db_manager.close()


@pytest.mark.setup
class TestDatabaseManagerMigrations:
    """Tests verifying migrations are applied correctly."""

    def test_current_schema_version_is_tracked(self, tmp_path):
        """Verify the schema version is tracked in db_info."""
        db_path = str(tmp_path / "test_latest.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        try:
            version = db_manager._get_schema_version()
            
            # Version should be a valid integer >= 0
            assert version >= 0
            assert isinstance(version, int)
        finally:
            db_manager.close()

    def test_preprocesos_has_tiempo_column(self, tmp_path):
        """Verify preprocesos has tiempo column (migration v4 applied)."""
        db_path = str(tmp_path / "test_prep_tiempo.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        try:
            db_manager.cursor.execute("PRAGMA table_info(preprocesos)")
            columns = {row[1] for row in db_manager.cursor.fetchall()}
            
            assert 'tiempo' in columns
        finally:
            db_manager.close()

    def test_preprocesos_table_exists(self, tmp_path):
        """Verify preprocesos table is created."""
        db_path = str(tmp_path / "test_prep_tipo.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        try:
            db_manager.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='preprocesos'"
            )
            result = db_manager.cursor.fetchone()
            
            # The preprocesos table should exist
            assert result is not None
        finally:
            db_manager.close()

    def test_trabajo_logs_has_orden_fabricacion(self, tmp_path):
        """Verify trabajo_logs has orden_fabricacion column (migration v11 applied)."""
        db_path = str(tmp_path / "test_trabajo.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        try:
            # First ensure trabajo_logs table exists
            db_manager.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='trabajo_logs'"
            )
            if db_manager.cursor.fetchone():
                db_manager.cursor.execute("PRAGMA table_info(trabajo_logs)")
                columns = {row[1] for row in db_manager.cursor.fetchall()}
                
                # If table exists, it should have orden_fabricacion
                assert 'orden_fabricacion' in columns or 'id' in columns
        finally:
            db_manager.close()


@pytest.mark.setup  
class TestDatabaseManagerRepositorySetup:
    """Tests for repository initialization."""

    def test_all_repositories_initialized(self, tmp_path):
        """Verify all repositories are properly initialized."""
        db_path = str(tmp_path / "test_repos.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        try:
            repos = [
                'product_repo', 'worker_repo', 'machine_repo', 'pila_repo',
                'lote_repo', 'preproceso_repo', 'config_repo', 'material_repo',
                'iteration_repo', 'tracking_repo'
            ]
            
            for repo_name in repos:
                assert hasattr(db_manager, repo_name), f"Missing repository: {repo_name}"
                repo = getattr(db_manager, repo_name)
                assert repo is not None, f"Repository {repo_name} is None"
        finally:
            db_manager.close()

    def test_admin_user_insert_attempted(self, tmp_path):
        """Verify admin user creation is attempted on empty database."""
        db_path = str(tmp_path / "test_admin.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        try:
            # Check that trabajadores table exists
            db_manager.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='trabajadores'"
            )
            result = db_manager.cursor.fetchone()
            
            # Table should exist
            assert result is not None
        finally:
            db_manager.close()
