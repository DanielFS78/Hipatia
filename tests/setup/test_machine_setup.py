
import pytest
from sqlalchemy import inspect
from database.models import Maquina, MachineMaintenanc, GrupoPreparacion

@pytest.mark.setup
class TestMachineDatabaseSetup:
    """Tests de configuración de esquema para el módulo de Máquinas."""
    
    def test_maquinas_table_exists(self, session):
        """Verifica que la tabla 'maquinas' existe en la BD."""
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        assert "maquinas" in tables
    
    def test_maquinas_columns(self, session):
        """Verifica que la tabla 'maquinas' tiene las columnas correctas."""
        inspector = inspect(session.bind)
        columns = {c['name']: c for c in inspector.get_columns("maquinas")}
        
        expected_columns = [
            'id', 
            'nombre', 
            'departamento', 
            'tipo_proceso', 
            'activa'
        ]
        
        for col in expected_columns:
            assert col in columns, f"Falta la columna '{col}' en la tabla 'maquinas'"
            
        # Verificar tipos específicos (opcional pero recomendado)
        assert columns['nombre']['nullable'] is False
        assert columns['departamento']['nullable'] is False
    
    def test_machine_maintenance_foreign_key(self, session):
        """Verifica la FK de maintenance hacia maquinas."""
        inspector = inspect(session.bind)
        fks = inspector.get_foreign_keys("machine_maintenance")
        
        fk_found = False
        for fk in fks:
            if fk['referred_table'] == 'maquinas' and 'machine_id' in fk['constrained_columns']:
                fk_found = True
                break
        
        assert fk_found, "No se encontró FK de machine_maintenance.machine_id -> maquinas.id"

    def test_grupos_preparacion_foreign_keys(self, session):
        """Verifica las FKs de grupos_preparacion."""
        inspector = inspect(session.bind)
        fks = inspector.get_foreign_keys("grupos_preparacion")
        referred_tables = [fk['referred_table'] for fk in fks]
        
        assert "maquinas" in referred_tables, "Falta FK hacia 'maquinas'"
        assert "productos" in referred_tables, "Falta FK hacia 'productos'"
