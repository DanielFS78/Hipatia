# -*- coding: utf-8 -*-
"""Tests unitarios para DatabaseConfig: runtime override, postgresql/sqlite, env vars."""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from database.config import DatabaseConfig

pytestmark = pytest.mark.unit


# Helper to reset state between tests
@pytest.fixture(autouse=True)
def reset_db_config():
    DatabaseConfig._runtime_db_url = None
    yield
    DatabaseConfig._runtime_db_url = None

class TestDatabaseConfig:

    def test_runtime_override(self):
        DatabaseConfig.set_db_url("sqlite:///override.db")
        assert DatabaseConfig.get_db_url() == "sqlite:///override.db"
        
        # Override takes precedence over env vars
        with patch.dict(os.environ, {"DB_TYPE": "postgresql"}):
            assert DatabaseConfig.get_db_url() == "sqlite:///override.db"

    def test_postgresql_config(self):
        env_vars = {
            "DB_TYPE": "postgresql",
            "DB_USER": "test_user",
            "DB_PASSWORD": "test_password",
            "DB_HOST": "test_host",
            "DB_PORT": "5432",
            "DB_NAME": "test_db"
        }
        with patch.dict(os.environ, env_vars):
            url = DatabaseConfig.get_db_url()
            assert url == "postgresql://test_user:test_password@test_host:5432/test_db"

    def test_sqlite_default(self):
        # Default with no env vars
        with patch.dict(os.environ, {}, clear=True):
             # Force reload or clean state logic if needed? 
             # PROJECT_ROOT is constant, we can't easily change it but we can check the end of string
             url = DatabaseConfig.get_db_url()
             assert url.startswith("sqlite:///")
             assert url.endswith("montaje.db")

    def test_sqlite_custom_path_relative(self):
        # Must enforce sqlite type because .env might contain postgresql
        with patch.dict(os.environ, {"DB_PATH": "custom/path.db", "DB_TYPE": "sqlite"}):
            url = DatabaseConfig.get_db_url()
            assert "custom/path.db" in url
            assert url.startswith("sqlite:///")

    def test_sqlite_custom_path_absolute(self):
        abs_path = "/tmp/absolute.db"
        with patch.dict(os.environ, {"DB_PATH": abs_path, "DB_TYPE": "sqlite"}):
            url = DatabaseConfig.get_db_url()
            assert url == f"sqlite:///{abs_path}"

    def test_get_echo_sql(self):
        with patch.dict(os.environ, {"DB_ECHO": "True"}):
            assert DatabaseConfig.get_echo_sql() is True
            
        with patch.dict(os.environ, {"DB_ECHO": "False"}):
            assert DatabaseConfig.get_echo_sql() is False
            
        with patch.dict(os.environ, {}): # Default
            assert DatabaseConfig.get_echo_sql() is False

    def test_get_log_dir_default(self):
        with patch.dict(os.environ, {}, clear=True):
            log_dir = DatabaseConfig.get_log_dir()
            assert log_dir.endswith("logs")

    def test_get_log_dir_absolute(self):
        with patch.dict(os.environ, {"LOG_DIR": "/var/logs"}):
            assert DatabaseConfig.get_log_dir() == "/var/logs"

    def test_get_backup_dir_default(self):
        with patch.dict(os.environ, {}, clear=True):
            backup_dir = DatabaseConfig.get_backup_dir()
            assert backup_dir.endswith("backups")

    def test_get_backup_dir_absolute(self):
        with patch.dict(os.environ, {"BACKUP_DIR": "/var/backups"}):
            assert DatabaseConfig.get_backup_dir() == "/var/backups"
