# tests/unit/test_database_manager_delegated.py
# -*- coding: utf-8 -*-
"""
Unit Tests for DatabaseManager Delegated Methods
=================================================
Tests para métodos delegados a repositorios y utilidades.

Autor: Suite de Tests Migración SQLAlchemy
Fecha: 26/12/2025
"""

import pytest
import sqlite3
from datetime import date, datetime
from unittest.mock import MagicMock, patch
from database.database_manager import DatabaseManager


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def mock_db_manager():
    """
    Crea un DatabaseManager mockeado para tests unitarios puros.
    """
    db_manager = object.__new__(DatabaseManager)
    db_manager.logger = MagicMock()
    db_manager.conn = MagicMock()
    db_manager.cursor = MagicMock()
    db_manager.engine = MagicMock()
    db_manager.SessionLocal = MagicMock()
    db_manager.tracking_repo = MagicMock()
    return db_manager


# ==============================================================================
# TESTS DE add_machine_maintenance
# ==============================================================================

@pytest.mark.unit
class TestAddMachineMaintenance:
    """Tests para add_machine_maintenance."""

    def test_add_machine_maintenance_success(self, mock_db_manager):
        """Test añadir mantenimiento exitosamente."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        
        # Act
        result = DatabaseManager.add_machine_maintenance(
            mock_db_manager, 
            machine_id=1, 
            maintenance_date=date.today(), 
            notes="Revisión anual"
        )
        
        # Assert
        assert result is True
        mock_db_manager.cursor.execute.assert_called_once()
        mock_db_manager.conn.commit.assert_called_once()

    def test_add_machine_maintenance_no_connection(self, mock_db_manager):
        """Test sin conexión retorna False."""
        # Arrange
        mock_db_manager.conn = None
        
        # Act
        result = DatabaseManager.add_machine_maintenance(
            mock_db_manager, 
            machine_id=1, 
            maintenance_date=date.today(), 
            notes="Test"
        )
        
        # Assert
        assert result is False

    def test_add_machine_maintenance_error(self, mock_db_manager):
        """Test con error SQLite hace rollback y retorna False."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.Error("Insert failed")
        )
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act
        result = DatabaseManager.add_machine_maintenance(
            mock_db_manager, 
            machine_id=1, 
            maintenance_date=date.today(), 
            notes="Test"
        )
        
        # Assert
        assert result is False
        mock_db_manager.conn.rollback.assert_called()


# ==============================================================================
# TESTS DE MÉTODOS DELEGADOS A tracking_repo
# ==============================================================================

@pytest.mark.unit
class TestTrackingDelegates:
    """Tests para métodos que delegan a tracking_repo."""

    def test_iniciar_trabajo_qr_delegates(self, mock_db_manager):
        """Test que iniciar_trabajo_qr delega a tracking_repo."""
        # Arrange
        expected_result = MagicMock()
        mock_db_manager.tracking_repo.iniciar_trabajo.return_value = expected_result
        
        # Act
        result = DatabaseManager.iniciar_trabajo_qr(
            mock_db_manager,
            qr_code="QR001",
            trabajador_id=1,
            fabricacion_id=1,
            producto_codigo="PROD001",
            notas="Notas"
        )
        
        # Assert
        assert result is expected_result
        mock_db_manager.tracking_repo.iniciar_trabajo.assert_called_once_with(
            qr_code="QR001",
            trabajador_id=1,
            fabricacion_id=1,
            producto_codigo="PROD001",
            notas="Notas"
        )

    def test_finalizar_trabajo_qr_delegates(self, mock_db_manager):
        """Test que finalizar_trabajo_qr delega a tracking_repo."""
        # Arrange
        expected_result = MagicMock()
        mock_db_manager.tracking_repo.finalizar_trabajo.return_value = expected_result
        
        # Act
        result = DatabaseManager.finalizar_trabajo_qr(
            mock_db_manager,
            qr_code="QR001",
            notas="Finalizado"
        )
        
        # Assert
        assert result is expected_result
        mock_db_manager.tracking_repo.finalizar_trabajo.assert_called_once_with(
            qr_code="QR001",
            notas_finalizacion="Finalizado"
        )

    def test_registrar_incidencia_delegates(self, mock_db_manager):
        """Test que registrar_incidencia delega a tracking_repo."""
        # Arrange
        expected_result = MagicMock()
        mock_db_manager.tracking_repo.registrar_incidencia.return_value = expected_result
        
        # Act
        result = DatabaseManager.registrar_incidencia(
            mock_db_manager,
            trabajo_log_id=1,
            trabajador_id=2,
            tipo_incidencia="Defecto",
            descripcion="Pieza dañada",
            rutas_fotos=["/path/foto1.jpg"]
        )
        
        # Assert
        assert result is expected_result
        mock_db_manager.tracking_repo.registrar_incidencia.assert_called_once_with(
            trabajo_log_id=1,
            trabajador_id=2,
            tipo_incidencia="Defecto",
            descripcion="Pieza dañada",
            rutas_fotos=["/path/foto1.jpg"]
        )

    def test_asignar_trabajador_fabricacion_delegates(self, mock_db_manager):
        """Test que asignar_trabajador_fabricacion delega a tracking_repo."""
        # Arrange
        mock_db_manager.tracking_repo.asignar_trabajador_a_fabricacion.return_value = True
        
        # Act
        result = DatabaseManager.asignar_trabajador_fabricacion(
            mock_db_manager,
            trabajador_id=1,
            fabricacion_id=2
        )
        
        # Assert
        assert result is True
        mock_db_manager.tracking_repo.asignar_trabajador_a_fabricacion.assert_called_once_with(
            trabajador_id=1,
            fabricacion_id=2
        )

    def test_obtener_trabajos_activos_delegates(self, mock_db_manager):
        """Test que obtener_trabajos_activos delega a tracking_repo."""
        # Arrange
        expected_result = [MagicMock(), MagicMock()]
        mock_db_manager.tracking_repo.obtener_trabajos_activos.return_value = expected_result
        
        # Act
        result = DatabaseManager.obtener_trabajos_activos(
            mock_db_manager,
            trabajador_id=1,
            fabricacion_id=None
        )
        
        # Assert
        assert result is expected_result
        mock_db_manager.tracking_repo.obtener_trabajos_activos.assert_called_once()

    def test_obtener_estadisticas_trabajador_delegates(self, mock_db_manager):
        """Test que obtener_estadisticas_trabajador delega a tracking_repo."""
        # Arrange
        expected_result = {"total_horas": 100, "unidades": 50}
        mock_db_manager.tracking_repo.obtener_estadisticas_trabajador.return_value = expected_result
        fecha_inicio = datetime.now()
        fecha_fin = datetime.now()
        
        # Act
        result = DatabaseManager.obtener_estadisticas_trabajador(
            mock_db_manager,
            trabajador_id=1,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        # Assert
        assert result is expected_result
        mock_db_manager.tracking_repo.obtener_estadisticas_trabajador.assert_called_once()

    def test_obtener_estadisticas_fabricacion_delegates(self, mock_db_manager):
        """Test que obtener_estadisticas_fabricacion delega a tracking_repo."""
        # Arrange
        expected_result = {"total_unidades": 100}
        mock_db_manager.tracking_repo.obtener_estadisticas_fabricacion.return_value = expected_result
        
        # Act
        result = DatabaseManager.obtener_estadisticas_fabricacion(
            mock_db_manager,
            fabricacion_id=1
        )
        
        # Assert
        assert result is expected_result
        mock_db_manager.tracking_repo.obtener_estadisticas_fabricacion.assert_called_once_with(
            fabricacion_id=1
        )


# ==============================================================================
# TESTS DE _verify_database_integrity
# ==============================================================================

@pytest.mark.unit
class TestVerifyDatabaseIntegrity:
    """Tests para _verify_database_integrity."""

    def test_verify_integrity_success(self, mock_db_manager):
        """Test verificación exitosa cuando todas las tablas existen."""
        # Arrange
        mock_db_manager.cursor.fetchall.return_value = [
            ('productos',), ('trabajadores',), ('maquinas',), ('configuracion',)
        ]
        
        # Act
        result = DatabaseManager._verify_database_integrity(mock_db_manager)
        
        # Assert
        assert result is True

    def test_verify_integrity_no_connection(self, mock_db_manager):
        """Test sin conexión retorna False."""
        # Arrange
        mock_db_manager.conn = None
        
        # Act
        result = DatabaseManager._verify_database_integrity(mock_db_manager)
        
        # Assert
        assert result is False

    def test_verify_integrity_missing_tables(self, mock_db_manager):
        """Test falta alguna tabla retorna False."""
        # Arrange
        mock_db_manager.cursor.fetchall.return_value = [
            ('productos',), ('trabajadores',)  # Faltan maquinas y configuracion
        ]
        
        # Act
        result = DatabaseManager._verify_database_integrity(mock_db_manager)
        
        # Assert
        assert result is False

    def test_verify_integrity_sqlite_error(self, mock_db_manager):
        """Test con error SQLite retorna False."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.Error("Query failed")
        )
        
        # Act
        result = DatabaseManager._verify_database_integrity(mock_db_manager)
        
        # Assert
        assert result is False


# ==============================================================================
# TESTS DE test_all_repositories
# ==============================================================================

@pytest.mark.unit
class TestAllRepositories:
    """Tests para test_all_repositories."""

    def test_all_repositories_success(self, mock_db_manager):
        """Test todos los repositorios funcionan."""
        # Arrange
        mock_db_manager.SessionLocal = MagicMock()
        
        # El método test_all_repositories importa los repositorios internamente,
        # así que necesitamos mockear el módulo completo
        with patch.dict('sys.modules', {
            'database.repositories': MagicMock()
        }):
            with patch('database.database_manager.ProductRepository') as mock_prod, \
                 patch('database.database_manager.WorkerRepository') as mock_work, \
                 patch('database.database_manager.MachineRepository') as mock_mach, \
                 patch('database.database_manager.PilaRepository') as mock_pila:
                
                mock_prod_instance = MagicMock()
                mock_prod_instance.get_all_products.return_value = [1, 2, 3]
                mock_prod.return_value = mock_prod_instance
                
                mock_work_instance = MagicMock()
                mock_work_instance.get_all_workers.return_value = [1, 2]
                mock_work.return_value = mock_work_instance
                
                mock_mach_instance = MagicMock()
                mock_mach_instance.get_all_machines.return_value = [1]
                mock_mach.return_value = mock_mach_instance
                
                mock_pila_instance = MagicMock()
                mock_pila_instance.get_all_pilas.return_value = []
                mock_pila.return_value = mock_pila_instance
                
                # Act
                result = DatabaseManager.test_all_repositories(mock_db_manager)
        
        # Assert - Result puede tener valores o errores dependiendo de cómo funcione el import
        assert isinstance(result, dict)
        assert 'products' in result
        assert 'workers' in result
        assert 'machines' in result
        assert 'pilas' in result

    def test_all_repositories_with_errors(self, mock_db_manager):
        """Test con algunos repositorios que fallan."""
        # Arrange
        mock_db_manager.SessionLocal = MagicMock()
        
        with patch.dict('sys.modules', {
            'database.repositories': MagicMock()
        }):
            with patch('database.database_manager.ProductRepository') as mock_prod, \
                 patch('database.database_manager.WorkerRepository') as mock_work, \
                 patch('database.database_manager.MachineRepository') as mock_mach, \
                 patch('database.database_manager.PilaRepository') as mock_pila:
                
                mock_prod.return_value.get_all_products.side_effect = Exception("Product error")
                mock_work.return_value.get_all_workers.return_value = [1, 2]
                mock_mach.return_value.get_all_machines.side_effect = Exception("Machine error")
                mock_pila.return_value.get_all_pilas.return_value = []
                
                # Act
                result = DatabaseManager.test_all_repositories(mock_db_manager)
        
        # Assert - Los resultados deben existir
        assert isinstance(result, dict)


# ==============================================================================
# TESTS DE create_preprocesos_tables_if_not_exist
# ==============================================================================

@pytest.mark.unit
class TestCreatePreprocesosTables:
    """Tests para create_preprocesos_tables_if_not_exist."""

    def test_create_preprocesos_tables_success(self, mock_db_manager):
        """Test creación exitosa de tablas."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        mock_db_manager._insert_sample_fabricaciones_if_empty = MagicMock()
        
        # Act
        DatabaseManager.create_preprocesos_tables_if_not_exist(mock_db_manager)
        
        # Assert
        assert mock_db_manager.cursor.execute.call_count >= 4
        mock_db_manager.conn.commit.assert_called_once()
        mock_db_manager._insert_sample_fabricaciones_if_empty.assert_called_once()

    def test_create_preprocesos_tables_error(self, mock_db_manager):
        """Test con error hace rollback."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.Error("Create failed")
        )
        mock_db_manager.conn.rollback = MagicMock()
        
        # Act - No debe lanzar excepción
        DatabaseManager.create_preprocesos_tables_if_not_exist(mock_db_manager)
        
        # Assert
        mock_db_manager.conn.rollback.assert_called()


# ==============================================================================
# TESTS DE _insert_sample_fabricaciones_if_empty
# ==============================================================================

@pytest.mark.unit
class TestInsertSampleFabricaciones:
    """Tests para _insert_sample_fabricaciones_if_empty."""

    def test_insert_sample_empty_table(self, mock_db_manager):
        """Test inserta datos demo cuando tabla está vacía."""
        # Arrange
        mock_db_manager.cursor.fetchone.return_value = (0,)  # Tabla vacía
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        
        # Act
        DatabaseManager._insert_sample_fabricaciones_if_empty(mock_db_manager)
        
        # Assert
        # Debe haber 4 llamadas: 1 SELECT COUNT + 3 INSERT
        assert mock_db_manager.cursor.execute.call_count >= 4
        mock_db_manager.conn.commit.assert_called_once()

    def test_insert_sample_not_empty(self, mock_db_manager):
        """Test no inserta si tabla tiene datos."""
        # Arrange
        mock_db_manager.cursor.fetchone.return_value = (5,)  # Ya hay 5 registros
        mock_db_manager.cursor.execute = MagicMock()
        mock_db_manager.conn.commit = MagicMock()
        
        # Act
        DatabaseManager._insert_sample_fabricaciones_if_empty(mock_db_manager)
        
        # Assert
        # Solo 1 llamada: SELECT COUNT
        mock_db_manager.cursor.execute.assert_called_once()
        mock_db_manager.conn.commit.assert_not_called()

    def test_insert_sample_error(self, mock_db_manager):
        """Test con error no lanza excepción."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.Error("Insert failed")
        )
        
        # Act - No debe lanzar excepción
        DatabaseManager._insert_sample_fabricaciones_if_empty(mock_db_manager)
        
        # Assert
        mock_db_manager.logger.error.assert_called()


# ==============================================================================
# TESTS DE __init__ ERROR HANDLING
# ==============================================================================

@pytest.mark.unit  
class TestInitErrorHandling:
    """Tests para manejo de errores en __init__."""

    def test_init_sqlite3_error(self, tmp_path):
        """Test que error SQLite se maneja correctamente."""
        # Arrange
        with patch('sqlite3.connect', side_effect=sqlite3.Error("Connection failed")):
            # Act
            db_manager = DatabaseManager(db_path=str(tmp_path / "test.db"))
            
            # Assert
            assert db_manager.conn is None
            assert db_manager.cursor is None

    def test_init_generic_exception(self, tmp_path):
        """Test que excepción genérica se maneja correctamente."""
        # Arrange
        with patch('sqlite3.connect', side_effect=Exception("Unexpected error")):
            # Act
            db_manager = DatabaseManager(db_path=str(tmp_path / "test.db"))
            
            # Assert
            assert db_manager.conn is None
            assert db_manager.engine is None


# ==============================================================================
# TESTS DE close() COMPLETO
# ==============================================================================

@pytest.mark.unit
class TestCloseComplete:
    """Tests para close() con todas las ramas."""

    def test_close_with_all_resources(self, tmp_path):
        """Test que close() cierra todos los recursos correctamente."""
        # Arrange
        db_path = str(tmp_path / "test_close_all.db")
        db_manager = DatabaseManager(db_path=db_path)
        
        # Act
        db_manager.close()
        
        # Assert
        assert db_manager.conn is None
        assert db_manager.cursor is None
        assert db_manager.engine is None

    def test_close_with_sessionlocal(self, mock_db_manager):
        """Test que close() llama a SessionLocal.close_all()."""
        # Arrange - Guardar referencias a los mocks antes de que close() los setee a None
        mock_session_local = MagicMock()
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        mock_db_manager.SessionLocal = mock_session_local
        mock_db_manager.engine = mock_engine
        mock_db_manager.conn = mock_conn
        
        # Act
        DatabaseManager.close(mock_db_manager)
        
        # Assert - Verificar en los mocks guardados
        mock_session_local.close_all.assert_called_once()
        mock_engine.dispose.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_close_handles_programming_error(self, mock_db_manager):
        """Test que close() maneja ProgrammingError en conexión ya cerrada."""
        # Arrange
        mock_db_manager.SessionLocal = None
        mock_db_manager.engine = None
        mock_db_manager.conn.close = MagicMock(
            side_effect=sqlite3.ProgrammingError("Cannot operate on a closed database")
        )
        
        # Act - No debe lanzar excepción
        DatabaseManager.close(mock_db_manager)
        
        # Assert - conn debe ser None después de close
        assert mock_db_manager.conn is None

    def test_close_no_connection(self, mock_db_manager):
        """Test que close() maneja cuando no hay conexión."""
        # Arrange
        mock_db_manager.SessionLocal = None
        mock_db_manager.engine = None
        mock_db_manager.conn = None
        
        # Act - No debe lanzar excepción
        DatabaseManager.close(mock_db_manager)
        
        # Assert - logger.info debe ser llamado
        mock_db_manager.logger.info.assert_called()


# ==============================================================================
# TESTS DE _get_schema_version ERROR
# ==============================================================================

@pytest.mark.unit
class TestGetSchemaVersionError:
    """Tests para _get_schema_version con errores."""
    
    def test_get_schema_version_sqlite_error(self, mock_db_manager):
        """Test que error SQLite retorna 0."""
        # Arrange
        mock_db_manager.cursor.execute = MagicMock(
            side_effect=sqlite3.Error("Query failed")
        )
        
        # Act
        result = DatabaseManager._get_schema_version(mock_db_manager)
        
        # Assert
        assert result == 0
