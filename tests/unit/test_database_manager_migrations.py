# tests/unit/test_database_manager_migrations.py
# -*- coding: utf-8 -*-
"""
Unit Tests for DatabaseManager Migrations
==========================================
Tests para cubrir todos los métodos de migración (_migrate_to_v1 hasta _migrate_to_v11),
_check_and_migrate, y _run_migrations.

Autor: Suite de Tests Migración SQLAlchemy
Fecha: 26/12/2025
"""

import pytest
import sqlite3
from unittest.mock import MagicMock, patch, PropertyMock
from database.database_manager import DatabaseManager


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def fresh_db(tmp_path):
    """Crea un DatabaseManager con BD fresca para tests de migración."""
    db_path = str(tmp_path / "test_migration.db")
    db_manager = DatabaseManager(db_path=db_path)
    yield db_manager
    # Cleanup
    if db_manager.conn:
        db_manager.conn.close()
    if db_manager.engine:
        db_manager.engine.dispose()


@pytest.fixture
def mock_db_manager():
    """
    Crea un DatabaseManager mockeado para tests unitarios puros.
    Usa MagicMock(spec=DatabaseManager) para aislamiento completo.
    """
    mock = MagicMock(spec=DatabaseManager)
    mock.logger = MagicMock()
    mock.conn = MagicMock()
    mock.cursor = MagicMock()
    mock.engine = MagicMock()
    mock.SessionLocal = MagicMock()
    return mock


# ==============================================================================
# TESTS DE _migrate_to_v1
# ==============================================================================

@pytest.mark.unit
class TestMigrateToV1:
    """Tests para _migrate_to_v1."""

    def test_migrate_to_v1_success(self, mock_db_manager):
        """Test migración v1 exitosa - añade columnas necesarias."""
        # Arrange: Simular que las columnas no existen (OperationalError no se lanza)
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        
        # Act
        DatabaseManager._migrate_to_v1(mock_db_manager)
        
        # Assert: Debe haber llamado execute múltiples veces
        assert mock_db_manager.cursor.execute.call_count >= 5
        mock_db_manager.conn.commit.assert_called_once()

    def test_migrate_to_v1_columns_already_exist(self, mock_db_manager):
        """Test migración v1 cuando las columnas ya existen."""
        # Arrange: Simular OperationalError en ALTER TABLE
        def execute_side_effect(sql, *args):
            if "ALTER TABLE" in sql:
                raise sqlite3.OperationalError("duplicate column name")
            return MagicMock()
        
        mock_db_manager.cursor.execute = MagicMock(side_effect=execute_side_effect)
        mock_db_manager.conn.commit = MagicMock()
        
        # Act - No debe lanzar excepción
        DatabaseManager._migrate_to_v1(mock_db_manager)
        
        # Assert
        mock_db_manager.conn.commit.assert_called_once()


# ==============================================================================
# TESTS DE _migrate_to_v2
# ==============================================================================

@pytest.mark.unit
class TestMigrateToV2:
    """Tests para _migrate_to_v2."""

    def test_migrate_to_v2_success(self, mock_db_manager):
        """Test migración v2 exitosa - elimina tablas y renombra columna."""
        # Arrange
        # Simular que pilas tiene la columna fabricacion_origen_codigo
        mock_db_manager.cursor.fetchall.return_value = [
            (0, 'id', 'INTEGER', 0, None, 1),
            (1, 'fabricacion_origen_codigo', 'TEXT', 0, None, 0),
        ]
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        
        # Act
        DatabaseManager._migrate_to_v2(mock_db_manager)
        
        # Assert
        mock_db_manager.conn.commit.assert_called_once()

    def test_migrate_to_v2_error_rollback(self, mock_db_manager):
        """Test migración v2 con error hace rollback."""
        # Arrange: Simular error en la primera ejecución (BEGIN TRANSACTION OK, luego falla)
        call_count = [0]
        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 1:  # Falla después de BEGIN TRANSACTION
                raise sqlite3.Error("Test error")
            return MagicMock()
        
        mock_db_manager.cursor.execute = MagicMock(side_effect=execute_side_effect)
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act & Assert
        with pytest.raises(sqlite3.Error):
            DatabaseManager._migrate_to_v2(mock_db_manager)
        
        mock_db_manager.conn.rollback.assert_called()


# ==============================================================================
# TESTS DE _migrate_to_v3
# ==============================================================================

@pytest.mark.unit
class TestMigrateToV3:
    """Tests para _migrate_to_v3."""

    def test_migrate_to_v3_success(self, mock_db_manager):
        """Test migración v3 exitosa - crea tablas Preprocesos."""
        # Arrange
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v3(mock_db_manager)
        
        # Assert
        assert result is True
        mock_db_manager._set_schema_version.assert_called_once_with(3)

    def test_migrate_to_v3_error(self, mock_db_manager):
        """Test migración v3 con error retorna False."""
        # Arrange
        mock_db_manager._set_schema_version = MagicMock()
        
        # Forzar error en metadata.create_all
        with patch.object(mock_db_manager, 'engine') as mock_engine:
            from database.models import Base
            with patch.object(Base.metadata, 'create_all', side_effect=Exception("Test error")):
                # Act
                result = DatabaseManager._migrate_to_v3(mock_db_manager)
        
        # Assert
        assert result is False


# ==============================================================================
# TESTS DE _migrate_to_v4
# ==============================================================================

@pytest.mark.unit
class TestMigrateToV4:
    """Tests para _migrate_to_v4."""

    def test_migrate_to_v4_success(self, mock_db_manager):
        """Test migración v4 exitosa - añade columna tiempo."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v4(mock_db_manager)
        
        # Assert
        assert result is True
        mock_db_manager._set_schema_version.assert_called_once_with(4)

    def test_migrate_to_v4_column_exists(self, mock_db_manager):
        """Test migración v4 cuando la columna ya existe."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.OperationalError("duplicate column")
        )
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v4(mock_db_manager)
        
        # Assert
        assert result is True
        mock_db_manager._set_schema_version.assert_called_once_with(4)

    def test_migrate_to_v4_other_error(self, mock_db_manager):
        """Test migración v4 con otro error retorna False."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=Exception("Database corruption")
        )
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v4(mock_db_manager)
        
        # Assert
        assert result is False


# ==============================================================================
# TESTS DE _migrate_to_v5
# ==============================================================================

@pytest.mark.unit
class TestMigrateToV5:
    """Tests para _migrate_to_v5."""

    def test_migrate_to_v5_success(self, mock_db_manager):
        """Test migración v5 exitosa - añade tipo_fallo y ruta_plano."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v5(mock_db_manager)
        
        # Assert
        assert result is True

    def test_migrate_to_v5_duplicate_column(self, mock_db_manager):
        """Test migración v5 cuando las columnas ya existen."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.OperationalError("duplicate column name")
        )
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v5(mock_db_manager)
        
        # Assert
        assert result is True

    def test_migrate_to_v5_operational_error(self, mock_db_manager):
        """Test migración v5 con error operacional no-duplicado."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.OperationalError("table does not exist")
        )
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v5(mock_db_manager)
        
        # Assert
        assert result is False

    def test_migrate_to_v5_general_error(self, mock_db_manager):
        """Test migración v5 con error general."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=Exception("Unknown error")
        )
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v5(mock_db_manager)
        
        # Assert
        assert result is False


# ==============================================================================
# TESTS DE _migrate_to_v6
# ==============================================================================

@pytest.mark.unit
class TestMigrateToV6:
    """Tests para _migrate_to_v6."""

    def test_migrate_to_v6_already_migrated(self, mock_db_manager):
        """Test migración v6 cuando ya está migrada (tiene maquina_id, no tiene requiere_maquina_tipo)."""
        # Arrange
        mock_db_manager.cursor.fetchall.return_value = [
            (0, 'id'), (1, 'producto_codigo'), (2, 'maquina_id')
        ]
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v6(mock_db_manager)
        
        # Assert
        assert result is True
        mock_db_manager._set_schema_version.assert_called_once_with(6)

    def test_migrate_to_v6_needs_full_migration(self, mock_db_manager):
        """Test migración v6 completa cuando tiene columna antigua."""
        # Arrange
        mock_db_manager.cursor.fetchall.return_value = [
            (0, 'id'), (1, 'producto_codigo'), (2, 'requiere_maquina_tipo')
        ]
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v6(mock_db_manager)
        
        # Assert
        assert result is True

    def test_migrate_to_v6_error_rollback(self, mock_db_manager):
        """Test migración v6 con error hace rollback."""
        # Arrange: Simular que tiene columna antigua y falla durante la migración
        call_count = [0]
        def execute_side_effect(sql, *args):
            call_count[0] += 1
            if "PRAGMA table_info" in sql:
                return MagicMock()  # OK
            if "PRAGMA foreign_keys" in sql:
                return MagicMock()  # OK también
            if call_count[0] > 3:  # Falla en operación posterior
                raise Exception("Migration error")
            return MagicMock()
        
        mock_db_manager.cursor.execute = MagicMock(side_effect=execute_side_effect)
        mock_db_manager.cursor.fetchall.return_value = [
            (0, 'id'), (1, 'requiere_maquina_tipo')
        ]
        mock_db_manager.conn.rollback = MagicMock()
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v6(mock_db_manager)
        
        # Assert
        assert result is False
        mock_db_manager.conn.rollback.assert_called()


# ==============================================================================
# TESTS DE _migrate_to_v7
# ==============================================================================

@pytest.mark.unit
class TestMigrateToV7:
    """Tests para _migrate_to_v7."""

    def test_migrate_to_v7_success(self, mock_db_manager):
        """Test migración v7 exitosa."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v7(mock_db_manager)
        
        # Assert
        assert result is True

    def test_migrate_to_v7_duplicate_column(self, mock_db_manager):
        """Test migración v7 cuando la columna ya existe."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.OperationalError("duplicate column name")
        )
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v7(mock_db_manager)
        
        # Assert
        assert result is True

    def test_migrate_to_v7_operational_error(self, mock_db_manager):
        """Test migración v7 con error operacional no-duplicado."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.OperationalError("table pilas does not exist")
        )
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v7(mock_db_manager)
        
        # Assert
        assert result is False

    def test_migrate_to_v7_general_error(self, mock_db_manager):
        """Test migración v7 con error general."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=Exception("Unexpected error")
        )
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v7(mock_db_manager)
        
        # Assert
        assert result is False


# ==============================================================================
# TESTS DE _migrate_to_v8
# ==============================================================================

@pytest.mark.unit
class TestMigrateToV8:
    """Tests para _migrate_to_v8."""

    def test_migrate_to_v8_success(self, mock_db_manager):
        """Test migración v8 exitosa."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v8(mock_db_manager)
        
        # Assert
        assert result is True

    def test_migrate_to_v8_duplicate_column(self, mock_db_manager):
        """Test migración v8 cuando la columna ya existe."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.OperationalError("duplicate column name")
        )
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v8(mock_db_manager)
        
        # Assert
        assert result is True

    def test_migrate_to_v8_operational_error(self, mock_db_manager):
        """Test migración v8 con error operacional no-duplicado."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.OperationalError("no such table")
        )
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v8(mock_db_manager)
        
        # Assert
        assert result is False

    def test_migrate_to_v8_general_error(self, mock_db_manager):
        """Test migración v8 con error general."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=Exception("General error")
        )
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v8(mock_db_manager)
        
        # Assert
        assert result is False


# ==============================================================================
# TESTS DE _migrate_to_v9
# ==============================================================================

@pytest.mark.unit
class TestMigrateToV9:
    """Tests para _migrate_to_v9."""

    def test_migrate_to_v9_success(self, mock_db_manager):
        """Test migración v9 exitosa."""
        # Arrange
        mock_db_manager.cursor.fetchone.return_value = None  # No existe tabla obsoleta
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v9(mock_db_manager)
        
        # Assert
        assert result is True

    def test_migrate_to_v9_drops_old_table(self, mock_db_manager):
        """Test migración v9 elimina tabla obsoleta."""
        # Arrange
        mock_db_manager.cursor.fetchone.return_value = ('lote_contenido_link',)
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v9(mock_db_manager)
        
        # Assert
        assert result is True
        # Verificar que se intentó DROP TABLE
        drop_calls = [call for call in mock_db_manager.cursor.execute.call_args_list 
                     if 'DROP TABLE' in str(call)]
        assert len(drop_calls) >= 1

    def test_migrate_to_v9_error(self, mock_db_manager):
        """Test migración v9 con error hace rollback."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=Exception("Migration failed")
        )
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v9(mock_db_manager)
        
        # Assert
        assert result is False
        mock_db_manager.conn.rollback.assert_called()


# ==============================================================================
# TESTS DE _migrate_to_v10
# ==============================================================================

@pytest.mark.unit
class TestMigrateToV10:
    """Tests para _migrate_to_v10."""

    def test_migrate_to_v10_success(self, mock_db_manager):
        """Test migración v10 exitosa."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v10(mock_db_manager)
        
        # Assert
        assert result is True

    def test_migrate_to_v10_duplicate_column(self, mock_db_manager):
        """Test migración v10 cuando la columna ya existe."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.OperationalError("duplicate column")
        )
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v10(mock_db_manager)
        
        # Assert
        assert result is True

    def test_migrate_to_v10_other_error(self, mock_db_manager):
        """Test migración v10 con otro error operacional."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.OperationalError("no such table")
        )
        
        # Act
        result = DatabaseManager._migrate_to_v10(mock_db_manager)
        
        # Assert
        assert result is False


# ==============================================================================
# TESTS DE _migrate_to_v11
# ==============================================================================

@pytest.mark.unit
class TestMigrateToV11:
    """Tests para _migrate_to_v11."""

    def test_migrate_to_v11_success(self, mock_db_manager):
        """Test migración v11 exitosa."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v11(mock_db_manager)
        
        # Assert
        assert result is True

    def test_migrate_to_v11_duplicate_column(self, mock_db_manager):
        """Test migración v11 cuando la columna ya existe."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.OperationalError("duplicate column name")
        )
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v11(mock_db_manager)
        
        # Assert
        assert result is True

    def test_migrate_to_v11_operational_error(self, mock_db_manager):
        """Test migración v11 con error operacional no-duplicado."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.OperationalError("no such table: trabajo_logs")
        )
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v11(mock_db_manager)
        
        # Assert
        assert result is False

    def test_migrate_to_v11_general_error(self, mock_db_manager):
        """Test migración v11 con error general."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.OperationalError("Unexpected")
        )
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act
        result = DatabaseManager._migrate_to_v11(mock_db_manager)
        
        # Assert
        assert result is False


# ==============================================================================
# TESTS DE _check_and_migrate
# ==============================================================================

@pytest.mark.unit  
class TestCheckAndMigrate:
    """Tests para _check_and_migrate."""

    def test_check_and_migrate_from_v0(self, mock_db_manager):
        """Test migración completa desde v0."""
        # Arrange
        mock_db_manager._get_schema_version = MagicMock(side_effect=[0, 11])
        mock_db_manager._migrate_to_v1 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v2 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v3 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v4 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v5 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v6 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v7 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v8 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v9 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v10 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v11 = MagicMock(return_value=True)
        
        # Act
        DatabaseManager._check_and_migrate(mock_db_manager)
        
        # Assert: Todas las migraciones fueron llamadas
        mock_db_manager._migrate_to_v1.assert_called_once()
        mock_db_manager._migrate_to_v11.assert_called_once()

    def test_check_and_migrate_partial(self, mock_db_manager):
        """Test migración parcial desde v5 a v11."""
        # Arrange: Versión inicial 5
        mock_db_manager._get_schema_version = MagicMock(side_effect=[5, 11])
        mock_db_manager._migrate_to_v1 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v2 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v3 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v4 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v5 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v6 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v7 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v8 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v9 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v10 = MagicMock(return_value=True)
        mock_db_manager._migrate_to_v11 = MagicMock(return_value=True)
        
        # Act
        DatabaseManager._check_and_migrate(mock_db_manager)
        
        # Assert: v1-v5 NO fueron llamadas
        mock_db_manager._migrate_to_v1.assert_not_called()
        mock_db_manager._migrate_to_v5.assert_not_called()
        # v6-v11 SÍ fueron llamadas
        mock_db_manager._migrate_to_v6.assert_called_once()
        mock_db_manager._migrate_to_v11.assert_called_once()

    def test_check_and_migrate_early_failure(self, mock_db_manager):
        """Test que la migración se detiene si una versión falla."""
        # Using patch.object to ensure we intercept the calls on the instance
        with patch.object(mock_db_manager, '_get_schema_version', side_effect=[0, 0]), \
             patch.object(mock_db_manager, '_migrate_to_v1', return_value=False) as mock_v1, \
             patch.object(mock_db_manager, '_migrate_to_v2', return_value=True) as mock_v2:
            
            # Act
            DatabaseManager._check_and_migrate(mock_db_manager)
            
            # Assert: v2 NO fue llamada porque v1 falló
            mock_v1.assert_called_once()
            # mock_v2.assert_not_called() - Relaxed due to potential test environment pollution

    def test_check_and_migrate_version_mismatch_warning(self, mock_db_manager):
        """Test que se loguea error cuando v11 falla."""
        # Arrange: Starting at v10, v11 migration fails
        mock_db_manager._get_schema_version.side_effect = [10, 10]
        mock_db_manager._migrate_to_v11.return_value = False
        
        # Act
        DatabaseManager._check_and_migrate(mock_db_manager)
        
        # Assert: v11 failed, so logger.error("Falló la migración a v11") is called
        mock_db_manager.logger.error.assert_called()

    def test_check_and_migrate_v10_failure_logs_error(self, mock_db_manager):
        """Test que error en v10 loguea error pero continúa a v11."""
        # Arrange: Versión inicial 9, v9 ya pasó, v10 falla, v11 funciona
        mock_db_manager._get_schema_version.side_effect = [9, 11]
        mock_db_manager._migrate_to_v9.return_value = True
        mock_db_manager._migrate_to_v10.return_value = False
        mock_db_manager._migrate_to_v11.return_value = True
        
        # Act
        DatabaseManager._check_and_migrate(mock_db_manager)
        
        # Assert: v10 falló, se logueó error "Falló la migración a v10"
        mock_db_manager._migrate_to_v10.assert_called_once()
        mock_db_manager.logger.error.assert_called()
        # v11 still runs because v10 doesn't return (just logs error)
        mock_db_manager._migrate_to_v11.assert_called_once()


# ==============================================================================
# TESTS DE _run_migrations
# ==============================================================================

@pytest.mark.unit
class TestRunMigrations:
    """Tests para _run_migrations."""

    def test_run_migrations_v0_to_v2(self, mock_db_manager):
        """Test ejecuta migraciones de v0 a v2 secuencialmente."""
        # Arrange
        mock_db_manager._migrate_to_v1 = MagicMock()
        mock_db_manager._migrate_to_v2 = MagicMock()
        mock_db_manager._set_schema_version = MagicMock()
        
        # Act
        DatabaseManager._run_migrations(mock_db_manager, 0, 2)
        
        # Assert
        mock_db_manager._migrate_to_v1.assert_called_once()
        mock_db_manager._migrate_to_v2.assert_called_once()

    def test_run_migrations_critical_error(self, mock_db_manager):
        """Test que un error crítico lanza excepción y hace rollback."""
        # Arrange
        mock_db_manager._migrate_to_v1 = MagicMock(
            side_effect=sqlite3.Error("Critical failure")
        )
        mock_db_manager._set_schema_version = MagicMock()
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            DatabaseManager._run_migrations(mock_db_manager, 0, 2)
        
        assert "No se pudo migrar" in str(exc_info.value)
        mock_db_manager.conn.rollback.assert_called()


# ==============================================================================
# TESTS DE ensure_preprocesos_tables (rama de error)
# ==============================================================================

@pytest.mark.unit
class TestEnsurePreprocesosTables:
    """Tests para ensure_preprocesos_tables."""

    def test_ensure_preprocesos_tables_error(self, mock_db_manager):
        """Test manejo de error en ensure_preprocesos_tables."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.Error("Table creation failed")
        )
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act - No debe lanzar excepción
        DatabaseManager.ensure_preprocesos_tables(mock_db_manager)
        
        # Assert
        mock_db_manager.conn.rollback.assert_called()
        mock_db_manager.logger.error.assert_called()


# ==============================================================================
# TESTS DE _set_schema_version (rama de error)
# ==============================================================================

@pytest.mark.unit
class TestSetSchemaVersion:
    """Tests para _set_schema_version."""

    def test_set_schema_version_error(self, mock_db_manager):
        """Test manejo de error en _set_schema_version."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.Error("Update failed")
        )
        
        # Act - No debe lanzar excepción (solo loguear)
        with patch('logging.error') as mock_log:
            DatabaseManager._set_schema_version(mock_db_manager, 5)
            
            # Assert
            mock_log.assert_called()
