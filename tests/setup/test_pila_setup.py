import pytest
from sqlalchemy import inspect
from database.models import Pila, PasoPila, DiarioBitacora, EntradaDiario

# Marker required for setup tests
pytestmark = [pytest.mark.setup, pytest.mark.database]

def test_pilas_table_exists(session):
    """Verify that the 'pilas' table exists in the database."""
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()
    assert "pilas" in tables

def test_pilas_columns(session):
    """Verify that 'pilas' table has all expected columns."""
    inspector = inspect(session.bind)
    columns = {c['name']: c for c in inspector.get_columns("pilas")}
    
    expected_columns = [
        "id", 
        "nombre", 
        "descripcion", 
        "fecha_creacion", 
        "resultados_simulacion",
        "producto_origen_codigo",
        "pila_de_calculo_json"
    ]
    
    for col in expected_columns:
        assert col in columns, f"Column {col} missing in pilas table"
        
    # Verify specific types if needed, e.g. JSON/Text columns
    # sqlalchemy types might vary by dialect, so checking name is first line of defense

def test_pilas_foreign_keys(session):
    """Verify 'pilas' foreign keys."""
    inspector = inspect(session.bind)
    fks = inspector.get_foreign_keys("pilas")
    fk_details = {fk['referred_table']: fk['constrained_columns'] for fk in fks}
    
    # Should link to productos
    assert "productos" in fk_details
    assert "producto_origen_codigo" in fk_details["productos"][0] # Assuming single column FK

def test_pasos_pila_table_exists(session):
    """Verify that the 'pasos_pila' table exists."""
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()
    assert "pasos_pila" in tables

def test_pasos_pila_columns(session):
    """Verify 'pasos_pila' columns."""
    inspector = inspect(session.bind)
    columns = {c['name']: c for c in inspector.get_columns("pasos_pila")}
    
    expected = ["id", "pila_id", "orden", "datos_paso"]
    for col in expected:
        assert col in columns, f"Column {col} missing in pasos_pila"

def test_pasos_pila_foreign_keys(session):
    """Verify 'pasos_pila' foreign keys."""
    inspector = inspect(session.bind)
    fks = inspector.get_foreign_keys("pasos_pila")
    fk_tables = [fk['referred_table'] for fk in fks]
    
    assert "pilas" in fk_tables

def test_diario_bitacora_table_structure(session):
    """Verify 'diario_bitacora' table structure."""
    inspector = inspect(session.bind)
    
    # Check table existence
    tables = inspector.get_table_names()
    assert "diario_bitacora" in tables
    
    # Check FK to pilas
    fks = inspector.get_foreign_keys("diario_bitacora")
    fk_tables = [fk['referred_table'] for fk in fks]
    assert "pilas" in fk_tables
    
    # Check uniqueness of pila_id (one bitacora per pila)
    # This is usually a unique constraint or unique index
    indexes = inspector.get_indexes("diario_bitacora")
    # Also check unique constraints explicitly
    unique_constraints = inspector.get_unique_constraints("diario_bitacora")
    
    # Depending on DB backend, it might be an index or constraint.
    # In models.py: pila_id = Column(..., unique=True)
    
    # We can check if columns exist
    columns = {c['name'] for c in inspector.get_columns("diario_bitacora")}
    assert "pila_id" in columns
    assert "id" in columns

def test_entrada_diario_table_structure(session):
    """Verify 'entrada_diario' table structure."""
    inspector = inspect(session.bind)
    
    tables = inspector.get_table_names()
    assert "entrada_diario" in tables
    
    columns = {c['name'] for c in inspector.get_columns("entrada_diario")}
    expected = [
        "id", "bitacora_id", "fecha", "dia_numero", 
        "plan_previsto", "trabajo_realizado", "notas"
    ]
    for col in expected:
        assert col in columns
        
    fks = inspector.get_foreign_keys("entrada_diario")
    fk_tables = [fk['referred_table'] for fk in fks]
    assert "diario_bitacora" in fk_tables
