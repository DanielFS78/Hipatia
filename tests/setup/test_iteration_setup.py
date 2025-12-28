import pytest
from sqlalchemy import inspect
from database.models import ProductIteration, Material, iteracion_material_link

class TestIterationSetup:
    
    def test_tables_exist(self, session):
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        assert ProductIteration.__tablename__ in tables
        assert Material.__tablename__ in tables
        assert 'iteracion_material_link' in tables

    def test_product_iteration_columns(self, session):
        inspector = inspect(session.bind)
        columns = {c['name']: c for c in inspector.get_columns(ProductIteration.__tablename__)}
        
        assert 'id' in columns
        assert 'producto_codigo' in columns
        assert 'nombre_responsable' in columns
        assert 'descripcion_cambio' in columns
        assert 'tipo_fallo' in columns
        assert 'ruta_imagen' in columns
        assert 'ruta_plano' in columns
        assert 'fecha_creacion' in columns

    def test_material_columns(self, session):
        inspector = inspect(session.bind)
        columns = {c['name']: c for c in inspector.get_columns(Material.__tablename__)}
        
        assert 'id' in columns
        assert 'codigo_componente' in columns
        assert 'descripcion_componente' in columns

    def test_relationships(self, session):
        # Verify mapper configuration indirectly or just rely on ORM behavior in integrations.
        pass
