# tests/setup/test_worker_setup.py
import pytest
from sqlalchemy import inspect
from database.models import Base, Trabajador

@pytest.mark.setup
class TestWorkerDatabaseSetup:
    """
    Tests de configuración para verificar que el esquema de la base de datos
    se crea correctamente para el módulo de Trabajadores.
    """

    def test_workers_table_exists(self, session):
        """Verifica que la tabla 'trabajadores' existe en la BD."""
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        assert "trabajadores" in tables

    def test_workers_table_columns(self, session):
        """Verifica que todas las columnas esperadas existen con los tipos correctos via SQLAlchemy reflect."""
        inspector = inspect(session.bind)
        columns = {c['name']: c for c in inspector.get_columns("trabajadores")}
        
        expected_columns = [
            'id', 'nombre_completo', 'activo', 'notas', 
            'tipo_trabajador', 'username', 'password_hash', 'role'
        ]
        
        for col_name in expected_columns:
            assert col_name in columns, f"Falta la columna {col_name} en trabajadors"

    def test_worker_annotations_relationship(self, session):
        """Verifica que la tabla de anotaciones y sus claves foráneas existen."""
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        assert "trabajador_pila_anotaciones" in tables
        
        fks = inspector.get_foreign_keys("trabajador_pila_anotaciones")
        fk_tables = [fk['referred_table'] for fk in fks]
        
        assert "trabajadores" in fk_tables
        assert "pilas" in fk_tables
