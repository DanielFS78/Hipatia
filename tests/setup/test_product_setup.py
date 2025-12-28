# tests/setup/test_product_setup.py
"""
Tests de configuración para verificar que el esquema de la base de datos
se crea correctamente para el módulo de Productos.
"""

import pytest
from sqlalchemy import inspect
from database.models import Base, Producto, Subfabricacion, ProcesoMecanico


@pytest.mark.setup
class TestProductDatabaseSetup:
    """
    Tests de configuración para verificar que el esquema de la base de datos
    se crea correctamente para el módulo de Productos.
    """

    def test_productos_table_exists(self, session):
        """Verifica que la tabla 'productos' existe en la BD."""
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        assert "productos" in tables

    def test_productos_table_columns(self, session):
        """Verifica que todas las columnas esperadas existen."""
        inspector = inspect(session.bind)
        columns = {c['name']: c for c in inspector.get_columns("productos")}
        
        expected_columns = [
            'codigo', 'descripcion', 'departamento', 
            'tipo_trabajador', 'donde', 'tiene_subfabricaciones', 
            'tiempo_optimo'
        ]
        
        for col_name in expected_columns:
            assert col_name in columns, f"Falta la columna {col_name} en productos"

    def test_productos_primary_key(self, session):
        """Verifica que 'codigo' es la clave primaria."""
        inspector = inspect(session.bind)
        pk_constraint = inspector.get_pk_constraint("productos")
        
        assert 'codigo' in pk_constraint['constrained_columns']

    def test_subfabricaciones_table_exists(self, session):
        """Verifica que la tabla 'subfabricaciones' existe en la BD."""
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        assert "subfabricaciones" in tables

    def test_subfabricaciones_table_columns(self, session):
        """Verifica columnas de subfabricaciones."""
        inspector = inspect(session.bind)
        columns = {c['name']: c for c in inspector.get_columns("subfabricaciones")}
        
        expected_columns = [
            'id', 'producto_codigo', 'descripcion', 
            'tiempo', 'tipo_trabajador', 'maquina_id'
        ]
        
        for col_name in expected_columns:
            assert col_name in columns, f"Falta la columna {col_name} en subfabricaciones"

    def test_subfabricaciones_foreign_key(self, session):
        """Verifica que subfabricaciones tiene FK hacia productos."""
        inspector = inspect(session.bind)
        fks = inspector.get_foreign_keys("subfabricaciones")
        fk_tables = [fk['referred_table'] for fk in fks]
        
        assert "productos" in fk_tables

    def test_procesos_mecanicos_table_exists(self, session):
        """Verifica que la tabla 'procesos_mecanicos' existe en la BD."""
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        assert "procesos_mecanicos" in tables

    def test_procesos_mecanicos_table_columns(self, session):
        """Verifica columnas de procesos_mecanicos."""
        inspector = inspect(session.bind)
        columns = {c['name']: c for c in inspector.get_columns("procesos_mecanicos")}
        
        expected_columns = [
            'id', 'producto_codigo', 'nombre', 
            'descripcion', 'tiempo', 'tipo_trabajador'
        ]
        
        for col_name in expected_columns:
            assert col_name in columns, f"Falta la columna {col_name} en procesos_mecanicos"

    def test_procesos_mecanicos_foreign_key(self, session):
        """Verifica que procesos_mecanicos tiene FK hacia productos."""
        inspector = inspect(session.bind)
        fks = inspector.get_foreign_keys("procesos_mecanicos")
        fk_tables = [fk['referred_table'] for fk in fks]
        
        assert "productos" in fk_tables

    def test_materiales_table_exists(self, session):
        """Verifica que la tabla 'materiales' existe en la BD."""
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        assert "materiales" in tables

    def test_materiales_foreign_key(self, session):
        """Verifica que la tabla de enlace producto_material_link existe (M-M)."""
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        
        # Material usa relación many-to-many vía tabla de enlace
        assert "producto_material_link" in tables
        
        # La tabla de enlace debe tener FK hacia productos y materiales
        fks = inspector.get_foreign_keys("producto_material_link")
        fk_tables = [fk['referred_table'] for fk in fks]
        
        assert "productos" in fk_tables
        assert "materiales" in fk_tables
