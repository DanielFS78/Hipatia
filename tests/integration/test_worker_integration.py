"""Tests de integración para WorkerRepository."""
import pytest
from database.models import Trabajador
from database.repositories.worker import WorkerRepository

@pytest.mark.integration
class TestWorkerRepositoryIntegration:
    """
    Tests de integración para WorkerRepository usando una base de datos 
    basada en archivo (no memoria) para verificar persistencia real y comportamiento
    de transacciones.
    """

    def test_persistence_between_sessions(self, temp_db_file):
        """
        Prueba que los datos persisten entre diferentes sesiones/conexiones.
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from database.models import Base
        
        # Setup: Crear DB y sesión 1
        engine = create_engine(f"sqlite:///{temp_db_file}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        
        try:
            # Sesión 1: Insertar dato
            session1 = Session()
            repo1 = WorkerRepository(lambda: session1)
            repo1.add_worker("Persist Worker", "Note", 1)
            session1.close()  # Cierra conexión
            
            # Sesión 2: Leer dato
            session2 = Session()
            repo2 = WorkerRepository(lambda: session2)
            workers = repo2.get_all_workers()
            session2.close()
            
            assert len(workers) == 1
            # WorkerRepository devuelve WorkerDTO con atributos tipados
            assert workers[0].nombre_completo == "Persist Worker"
        finally:
            engine.dispose()  # Cerrar engine correctamente
        
    def test_transaction_rollback_on_error(self, temp_db_file):
        """
        Prueba que una excepción provoca rollback y no deja datos sucios.
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from database.models import Base
        
        engine = create_engine(f"sqlite:///{temp_db_file}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            repo = WorkerRepository(lambda: session)
            
            # Insertar trabajador válido
            repo.add_worker("Valid Worker", "", 1)
            
            # Verificar que el trabajador fue insertado correctamente
            from database.models import Trabajador
            count_before = session.query(Trabajador).count()
            assert count_before == 1
            
            # Verificar que safe_execute maneja errores sin dejar datos sucios
            # Intentar operación que falla (ID duplicado)
            try:
                w_dup = Trabajador(id=1, nombre_completo="Duplicate", activo=True)
                session.add(w_dup)
                session.commit()
            except Exception:
                session.rollback()
            
            # El count debe seguir siendo 1 (rollback funcionó)
            count_after = session.query(Trabajador).count()
            assert count_after == 1
        finally:
            session.close()
            engine.dispose()

    def test_interaction_with_pila_repository(self, temp_db_file):
        """
        Prueba la integración entre Worker y Pila (relación foránea real).
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from database.models import Base, Pila, TrabajadorPilaAnotacion
        
        engine = create_engine(f"sqlite:///{temp_db_file}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            worker_repo = WorkerRepository(lambda: session)
            
            # 1. Crear Worker
            worker_repo.add_worker("Worker For Pila", "", 1)
            worker = session.query(Trabajador).first()
            assert worker is not None
            worker_id = worker.id # Capturar ID mientras está attachado
            
            # 2. Crear Pila
            pila = Pila(nombre="Pila 1", descripcion="Desc")
            session.add(pila)
            session.commit()
            pila_id = pila.id
            
            # 3. Añadir anotación (usa ambos)
            # Pasamos IDs, así que repo hará su propia query interna si es necesario
            result = worker_repo.add_worker_annotation(worker_id, pila_id, "Integration Note")
            assert result is True
            
            # 4. Verificar integridad referencial (Delete worker -> Delete annotation?)
            # El modelo tiene cascade="all, delete-orphan" en Trabajador.anotaciones
            
            worker_repo.delete_worker(worker_id)
            
            # Verificar que la anotación se borró
            count = session.query(TrabajadorPilaAnotacion).count()
            assert count == 0
            
        finally:
            session.close()
            engine.dispose()  # Cerrar engine correctamente
