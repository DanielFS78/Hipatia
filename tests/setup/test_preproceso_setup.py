
import pytest
from sqlalchemy import inspect

@pytest.mark.setup
class TestPreprocesoDatabaseSetup:
    """Tests para verificar el esquema de base de datos de Preprocesos y Fabricaciones."""

    def test_preprocesos_table_exists(self, session):
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        assert "preprocesos" in tables

    def test_fabricaciones_table_exists(self, session):
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        assert "fabricaciones" in tables

    def test_preprocesos_columns(self, session):
        inspector = inspect(session.bind)
        columns = {c['name']: c for c in inspector.get_columns("preprocesos")}
        
        expected = ['id', 'nombre', 'descripcion', 'tiempo']
        for col in expected:
            assert col in columns
            
    def test_fabricaciones_columns(self, session):
        inspector = inspect(session.bind)
        columns = {c['name']: c for c in inspector.get_columns("fabricaciones")}
        
        expected = ['id', 'codigo', 'descripcion']
        for col in expected:
            assert col in columns
            
    def test_fabricacion_productos_link_table(self, session):
        """Verifica que la tabla de enlace manual existe (fabricacion_productos)."""
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        # Nota: el nombre exacto de la tabla puede variar según models.py, asumimos 'fabricacion_productos'
        # o revisamos si es una tabla m2m implícita.
        # Basado en repositories, se usa 'fabricacion_productos'
        assert "fabricacion_productos" in tables
        
        columns = {c['name']: c for c in inspector.get_columns("fabricacion_productos")}
        assert "fabricacion_id" in columns
        assert "producto_codigo" in columns
        assert "cantidad" in columns
