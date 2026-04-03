
"""
Capa de datos (`config`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the project root directory (where .env is located)
PROJECT_ROOT: Path = Path(__file__).parent.parent


class DatabaseConfig:
    _runtime_db_url: Optional[str] = None

    @classmethod
    def set_db_url(cls, url: str) -> None:
        """Allows runtime override of the database URL."""
        cls._runtime_db_url = url

    @classmethod
    def get_db_url(cls) -> str:
        """
        Returns the database connection URL.
        Priority: Runtime override > Environment variables > Default SQLite.
        """
        if cls._runtime_db_url:
            return cls._runtime_db_url

        db_type = os.getenv("DB_TYPE", "sqlite")
        
        if db_type == "postgresql":
            user = os.getenv("DB_USER", "postgres")
            password = os.getenv("DB_PASSWORD", "password")
            host = os.getenv("DB_HOST", "localhost")
            port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "tiempos_fabricacion")
            return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        
        # Default to SQLite - construct absolute path
        db_path = os.getenv("DB_PATH", "data/montaje.db")
        # If relative path, make it relative to project root
        if not os.path.isabs(db_path):
            db_path = str(PROJECT_ROOT / db_path)
            # Ensure the directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return f"sqlite:///{db_path}"

    @staticmethod
    def get_echo_sql() -> bool:
        """Returns True if SQL queries should be logged."""
        return os.getenv("DB_ECHO", "False").lower() == "true"

    @staticmethod
    def get_log_dir() -> str:
        """Returns the directory for log files."""
        log_dir = os.getenv("LOG_DIR", "logs")
        if not os.path.isabs(log_dir):
            log_dir = str(PROJECT_ROOT / log_dir)
        return log_dir

    @staticmethod
    def get_backup_dir() -> str:
        """Returns the directory for backup files."""
        backup_dir = os.getenv("BACKUP_DIR", "backups")
        if not os.path.isabs(backup_dir):
            backup_dir = str(PROJECT_ROOT / backup_dir)
        return backup_dir
