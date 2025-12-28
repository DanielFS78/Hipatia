# tests/unit/test_worker_repository.py
"""
Tests unitarios completos para WorkerRepository.
Cubren todos los métodos CRUD, autenticación y anotaciones.
Actualizado para usar DTOs en lugar de tuplas.

Autor: Sistema de Tests Migración SQLAlchemy
Fecha: 25/12/2025
"""

import pytest
import hashlib
from datetime import datetime
from database.models import Trabajador, TrabajadorPilaAnotacion, Pila
from core.dtos import WorkerDTO, WorkerAnnotationDTO


# ==============================================================================
# TESTS DE OBTENCIÓN (GET)
# ==============================================================================

@pytest.mark.unit
class TestWorkerRepositoryGetMethods:
    """Tests para métodos de obtención de trabajadores."""

    # --- Tests para get_all_workers ---

    def test_get_all_workers_empty(self, repos):
        """
        Prueba que get_all_workers() devuelve una lista vacía
        cuando la base de datos no tiene trabajadores.
        """
        worker_repo = repos["worker"]
        workers = worker_repo.get_all_workers()
        
        assert workers == []
        assert isinstance(workers, list)

    def test_get_all_workers_with_data(self, repos, session):
        """
        Prueba que get_all_workers() devuelve todos los trabajadores activos
        correctamente formateados como tuplas.
        """
        worker_repo = repos["worker"]
        
        # Arrange: Crear trabajadores de prueba
        w1 = Trabajador(
            nombre_completo="Ana García",
            activo=True,
            notas="Operaria senior",
            tipo_trabajador=2
        )
        w2 = Trabajador(
            nombre_completo="Carlos López",
            activo=True,
            notas="Técnico junior",
            tipo_trabajador=1
        )
        session.add_all([w1, w2])
        session.commit()
        
        # Act
        workers = worker_repo.get_all_workers()
        
        # Assert
        assert len(workers) == 2
        assert isinstance(workers[0], WorkerDTO)
        # Verificar orden alfabético por nombre
        assert workers[0].nombre_completo == "Ana García"
        assert workers[1].nombre_completo == "Carlos López"

    def test_get_all_workers_excludes_inactive(self, repos, session):
        """
        Prueba que get_all_workers() excluye trabajadores inactivos por defecto.
        """
        worker_repo = repos["worker"]
        
        # Arrange
        w_active = Trabajador(nombre_completo="Activo", activo=True, notas="", tipo_trabajador=1)
        w_inactive = Trabajador(nombre_completo="Inactivo", activo=False, notas="", tipo_trabajador=1)
        session.add_all([w_active, w_inactive])
        session.commit()
        
        # Act
        workers = worker_repo.get_all_workers(include_inactive=False)
        
        # Assert
        assert len(workers) == 1
        assert workers[0].nombre_completo == "Activo"

    def test_get_all_workers_include_inactive(self, repos, session):
        """
        Prueba que get_all_workers(include_inactive=True) incluye todos los trabajadores.
        """
        worker_repo = repos["worker"]
        
        # Arrange
        w_active = Trabajador(nombre_completo="Activo", activo=True, notas="", tipo_trabajador=1)
        w_inactive = Trabajador(nombre_completo="Inactivo", activo=False, notas="", tipo_trabajador=1)
        session.add_all([w_active, w_inactive])
        session.commit()
        
        # Act
        workers = worker_repo.get_all_workers(include_inactive=True)
        
        # Assert
        assert len(workers) == 2

    # --- Tests para get_latest_workers ---

    def test_get_latest_workers_empty(self, repos):
        """
        Prueba que get_latest_workers() devuelve lista vacía sin datos.
        """
        worker_repo = repos["worker"]
        workers = worker_repo.get_latest_workers()
        
        assert workers == []

    def test_get_latest_workers_respects_limit(self, repos, session):
        """
        Prueba que get_latest_workers() respeta el límite especificado.
        """
        worker_repo = repos["worker"]
        
        # Arrange: Crear 15 trabajadores
        for i in range(1, 16):
            session.add(Trabajador(
                nombre_completo=f"Trabajador {i:02d}",
                activo=True,
                notas="",
                tipo_trabajador=1
            ))
        session.commit()
        
        # Act
        workers = worker_repo.get_latest_workers(limit=5)
        
        # Assert
        assert len(workers) == 5
        # Deben venir ordenados por ID descendente (más recientes primero)
        assert "15" in workers[0].nombre_completo  # El más reciente

    def test_get_latest_workers_default_limit(self, repos, session):
        """
        Prueba que get_latest_workers() usa límite 10 por defecto.
        """
        worker_repo = repos["worker"]
        
        # Arrange: Crear 15 trabajadores
        for i in range(1, 16):
            session.add(Trabajador(
                nombre_completo=f"Trabajador {i}",
                activo=True,
                notas="",
                tipo_trabajador=1
            ))
        session.commit()
        
        # Act
        workers = worker_repo.get_latest_workers()
        
        # Assert
        assert len(workers) == 10

    # --- Tests para get_worker_details ---

    def test_get_worker_details_existing(self, repos, session):
        """
        Prueba que get_worker_details() devuelve diccionario con todos los campos.
        """
        worker_repo = repos["worker"]
        
        # Arrange
        w = Trabajador(
            nombre_completo="María Fernández",
            activo=True,
            notas="Especialista",
            tipo_trabajador=3,
            username="mfernandez",
            role="Trabajador"
        )
        session.add(w)
        session.commit()
        worker_id = w.id
        
        # Act
        details = worker_repo.get_worker_details(worker_id)
        
        # Assert
        assert details is not None
        assert isinstance(details, dict)
        assert details["id"] == worker_id
        assert details["nombre_completo"] == "María Fernández"
        assert details["activo"] == True
        assert details["notas"] == "Especialista"
        assert details["tipo_trabajador"] == 3
        assert details["username"] == "mfernandez"
        assert details["role"] == "Trabajador"
        # Verificar que no incluye password_hash por seguridad
        assert "password_hash" not in details

    def test_get_worker_details_not_found(self, repos):
        """
        Prueba que get_worker_details() devuelve None para ID inexistente.
        """
        worker_repo = repos["worker"]
        
        details = worker_repo.get_worker_details(99999)
        
        assert details is None


# ==============================================================================
# TESTS DE CREACIÓN Y ACTUALIZACIÓN (ADD/UPDATE)
# ==============================================================================

@pytest.mark.unit
class TestWorkerRepositoryCRUD:
    """Tests para operaciones CRUD de trabajadores."""

    # --- Tests para add_worker ---

    def test_add_worker_success(self, repos):
        """
        Prueba que add_worker() crea un nuevo trabajador correctamente.
        """
        worker_repo = repos["worker"]
        
        # Act
        result = worker_repo.add_worker(
            nombre_completo="Pedro Martínez",
            notas="Nuevo empleado",
            tipo_trabajador=1,
            activo=True
        )
        
        # Assert
        assert result == True
        
        # Verificar que se creó
        workers = worker_repo.get_all_workers()
        assert len(workers) == 1
        assert workers[0].nombre_completo == "Pedro Martínez"

    def test_add_worker_with_credentials(self, repos):
        """
        Prueba que add_worker() acepta credenciales opcionales.
        """
        worker_repo = repos["worker"]
        password_hash = hashlib.sha256("test123".encode('utf-8')).hexdigest()
        
        # Act
        result = worker_repo.add_worker(
            nombre_completo="Admin Test",
            notas="Usuario de prueba",
            tipo_trabajador=1,
            username="admin_test",
            password_hash=password_hash,
            role="Responsable"
        )
        
        # Assert
        assert result == True
        
        # Verificar detalles
        workers = worker_repo.get_all_workers()
        worker_id = workers[0].id
        details = worker_repo.get_worker_details(worker_id)
        
        assert details["username"] == "admin_test"
        assert details["role"] == "Responsable"

    def test_add_worker_duplicate_name_updates(self, repos, session):
        """
        Prueba que add_worker() actualiza si el nombre ya existe.
        """
        worker_repo = repos["worker"]
        
        # Arrange: Crear trabajador inicial
        w = Trabajador(
            nombre_completo="Juan Duplicado",
            activo=True,
            notas="Original",
            tipo_trabajador=1
        )
        session.add(w)
        session.commit()
        
        # Act: Intentar añadir con mismo nombre
        result = worker_repo.add_worker(
            nombre_completo="Juan Duplicado",
            notas="Actualizado",
            tipo_trabajador=2
        )
        
        # Assert
        assert result == True
        workers = worker_repo.get_all_workers(include_inactive=True)
        assert len(workers) == 1
        assert workers[0].tipo_trabajador == 2  # tipo_trabajador actualizado

    # --- Tests para update_worker ---

    def test_update_worker_success(self, repos, session):
        """
        Prueba que update_worker() modifica los datos correctamente.
        """
        worker_repo = repos["worker"]
        
        # Arrange
        w = Trabajador(
            nombre_completo="Nombre Original",
            activo=True,
            notas="Notas iniciales",
            tipo_trabajador=1
        )
        session.add(w)
        session.commit()
        worker_id = w.id
        
        # Act
        result = worker_repo.update_worker(
            worker_id=worker_id,
            nombre_completo="Nombre Actualizado",
            activo=False,
            notas="Notas modificadas",
            tipo_trabajador=3
        )
        
        # Assert
        assert result == True
        details = worker_repo.get_worker_details(worker_id)
        assert details["nombre_completo"] == "Nombre Actualizado"
        assert details["activo"] == False
        assert details["notas"] == "Notas modificadas"
        assert details["tipo_trabajador"] == 3

    def test_update_worker_not_found(self, repos):
        """
        Prueba que update_worker() devuelve False para ID inexistente.
        """
        worker_repo = repos["worker"]
        
        result = worker_repo.update_worker(
            worker_id=99999,
            nombre_completo="No Existe",
            activo=True,
            notas="",
            tipo_trabajador=1
        )
        
        assert result == False

    # --- Tests para delete_worker ---

    def test_delete_worker_success(self, repos, session):
        """
        Prueba que delete_worker() elimina el trabajador.
        """
        worker_repo = repos["worker"]
        
        # Arrange
        w = Trabajador(
            nombre_completo="A Eliminar",
            activo=True,
            notas="",
            tipo_trabajador=1
        )
        session.add(w)
        session.commit()
        worker_id = w.id
        
        # Act
        result = worker_repo.delete_worker(worker_id)
        
        # Assert
        assert result == True
        workers = worker_repo.get_all_workers(include_inactive=True)
        assert len(workers) == 0

    def test_delete_worker_not_found(self, repos):
        """
        Prueba que delete_worker() devuelve False para ID inexistente.
        """
        worker_repo = repos["worker"]
        
        result = worker_repo.delete_worker(99999)
        
        assert result == False


# ==============================================================================
# TESTS DE AUTENTICACIÓN
# ==============================================================================

@pytest.mark.unit
class TestWorkerRepositoryAuthentication:
    """Tests para funciones de autenticación."""

    def test_authenticate_user_success(self, repos, session):
        """
        Prueba autenticación exitosa con credenciales correctas.
        """
        worker_repo = repos["worker"]
        password = "mi_password_123"
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        # Arrange
        w = Trabajador(
            nombre_completo="Usuario Auth",
            activo=True,
            notas="",
            tipo_trabajador=1,
            username="usuario_auth",
            password_hash=password_hash,
            role="Trabajador"
        )
        session.add(w)
        session.commit()
        
        # Act
        result = worker_repo.authenticate_user("usuario_auth", password)
        
        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert result["nombre"] == "Usuario Auth"
        assert result["role"] == "Trabajador"

    def test_authenticate_user_wrong_password(self, repos, session):
        """
        Prueba que autenticación falla con contraseña incorrecta.
        """
        worker_repo = repos["worker"]
        password_hash = hashlib.sha256("correcta".encode('utf-8')).hexdigest()
        
        # Arrange
        w = Trabajador(
            nombre_completo="Usuario Test",
            activo=True,
            notas="",
            tipo_trabajador=1,
            username="user_test",
            password_hash=password_hash,
            role="Trabajador"
        )
        session.add(w)
        session.commit()
        
        # Act
        result = worker_repo.authenticate_user("user_test", "incorrecta")
        
        # Assert
        assert result is None

    def test_authenticate_user_not_found(self, repos):
        """
        Prueba que autenticación falla con usuario inexistente.
        """
        worker_repo = repos["worker"]
        
        result = worker_repo.authenticate_user("no_existe", "cualquier")
        
        assert result is None

    def test_update_user_credentials_success(self, repos, session):
        """
        Prueba actualización completa de credenciales.
        """
        worker_repo = repos["worker"]
        
        # Arrange
        w = Trabajador(
            nombre_completo="Credenciales Test",
            activo=True,
            notas="",
            tipo_trabajador=1,
            username="old_user",
            password_hash=hashlib.sha256("old_pass".encode('utf-8')).hexdigest(),
            role="Trabajador"
        )
        session.add(w)
        session.commit()
        worker_id = w.id
        
        # Act
        result = worker_repo.update_user_credentials(
            worker_id=worker_id,
            username="new_user",
            password="new_pass",
            role="Responsable"
        )
        
        # Assert
        assert result == True
        
        # Verificar que las nuevas credenciales funcionan
        auth_result = worker_repo.authenticate_user("new_user", "new_pass")
        assert auth_result is not None
        assert auth_result["role"] == "Responsable"

    def test_update_user_credentials_empty_password(self, repos, session):
        """
        Prueba que contraseña vacía no cambia el hash existente.
        """
        worker_repo = repos["worker"]
        original_password = "original_pass"
        original_hash = hashlib.sha256(original_password.encode('utf-8')).hexdigest()
        
        # Arrange
        w = Trabajador(
            nombre_completo="Password Test",
            activo=True,
            notas="",
            tipo_trabajador=1,
            username="pass_test",
            password_hash=original_hash,
            role="Trabajador"
        )
        session.add(w)
        session.commit()
        worker_id = w.id
        
        # Act: Actualizar sin cambiar contraseña
        result = worker_repo.update_user_credentials(
            worker_id=worker_id,
            username="pass_test",
            password="",  # Vacía
            role="Responsable"
        )
        
        # Assert
        assert result == True
        # Contraseña original debe seguir funcionando
        auth_result = worker_repo.authenticate_user("pass_test", original_password)
        assert auth_result is not None

    def test_update_user_password_success(self, repos, session):
        """
        Prueba actualización solo de contraseña.
        """
        worker_repo = repos["worker"]
        
        # Arrange
        w = Trabajador(
            nombre_completo="Solo Password",
            activo=True,
            notas="",
            tipo_trabajador=1,
            username="solo_pass",
            password_hash=hashlib.sha256("old".encode('utf-8')).hexdigest(),
            role="Trabajador"
        )
        session.add(w)
        session.commit()
        worker_id = w.id
        
        # Act
        result = worker_repo.update_user_password(worker_id, "nueva_contrasena")
        
        # Assert
        assert result == True
        # Verificar nueva contraseña
        auth_result = worker_repo.authenticate_user("solo_pass", "nueva_contrasena")
        assert auth_result is not None

    def test_update_user_password_not_found(self, repos):
        """
        Prueba que update_user_password devuelve False para ID inexistente.
        """
        worker_repo = repos["worker"]
        
        result = worker_repo.update_user_password(99999, "cualquier")
        
        assert result == False


# ==============================================================================
# TESTS DE ANOTACIONES
# ==============================================================================

@pytest.mark.unit
class TestWorkerRepositoryAnnotations:
    """Tests para gestión de anotaciones de trabajadores.
    
    NOTA: Los tests de anotaciones están marcados como skip debido a un problema
    de compatibilidad con datetime.UTC en el modelo TrabajadorPilaAnotacion.
    Este problema debe corregirse en database/models.py antes de habilitar estos tests.
    """

    @pytest.fixture
    def setup_pila(self, session):
        """Fixture que crea una pila de prueba necesaria para anotaciones."""
        from database.models import Pila
        pila = Pila(
            nombre="Pila Test Anotaciones",
            descripcion="Pila para tests"
        )
        session.add(pila)
        session.commit()
        pila_id = pila.id  # Capturar ID antes de cerrar sesión
        return pila_id

    # Skipped removed
    def test_add_worker_annotation_success(self, repos, session, setup_pila):
        """
        Prueba que add_worker_annotation() crea una anotación correctamente.
        """
        worker_repo = repos["worker"]
        
        # Arrange
        w = Trabajador(
            nombre_completo="Anotador",
            activo=True,
            notas="",
            tipo_trabajador=1
        )
        session.add(w)
        session.commit()
        worker_id = w.id
        pila_id = setup_pila
        
        # Act
        result = worker_repo.add_worker_annotation(
            worker_id=worker_id,
            pila_id=pila_id,
            annotation="Esta es una anotación de prueba"
        )
        
        # Assert
        assert result == True

    def test_get_worker_annotations_empty(self, repos, session):
        """
        Prueba que get_worker_annotations() devuelve lista vacía sin anotaciones.
        """
        worker_repo = repos["worker"]
        
        # Arrange: Crear trabajador sin anotaciones
        w = Trabajador(
            nombre_completo="Sin Anotaciones",
            activo=True,
            notas="",
            tipo_trabajador=1
        )
        session.add(w)
        session.commit()
        worker_id = w.id  # Capturar ID antes de cerrar sesión
        
        # Act
        annotations = worker_repo.get_worker_annotations(worker_id)
        
        # Assert
        assert annotations == []

    # Skipped removed
    def test_get_worker_annotations_with_data(self, repos, session, setup_pila):
        """
        Prueba que get_worker_annotations() devuelve las anotaciones correctamente.
        """
        worker_repo = repos["worker"]
        
        # Arrange
        w = Trabajador(
            nombre_completo="Con Anotaciones",
            activo=True,
            notas="",
            tipo_trabajador=1
        )
        session.add(w)
        session.commit()
        worker_id = w.id
        pila_id = setup_pila
        
        # Añadir anotaciones
        worker_repo.add_worker_annotation(worker_id, pila_id, "Primera anotación")
        worker_repo.add_worker_annotation(worker_id, pila_id, "Segunda anotación")
        
        # Act
        annotations = worker_repo.get_worker_annotations(worker_id)
        
        # Assert
        assert len(annotations) == 2
        assert isinstance(annotations[0], WorkerAnnotationDTO)

    # Skipped removed
    def test_get_worker_annotations_only_own(self, repos, session, setup_pila):
        """
        Prueba que get_worker_annotations() solo devuelve las del trabajador indicado.
        """
        worker_repo = repos["worker"]
        pila_id = setup_pila
        
        # Arrange: Crear dos trabajadores
        w1 = Trabajador(nombre_completo="Trabajador 1", activo=True, notas="", tipo_trabajador=1)
        w2 = Trabajador(nombre_completo="Trabajador 2", activo=True, notas="", tipo_trabajador=1)
        session.add_all([w1, w2])
        session.commit()
        worker1_id = w1.id  # Capturar IDs antes de usar en otra sesión
        worker2_id = w2.id
        
        worker_repo.add_worker_annotation(worker1_id, pila_id, "Anotación de T1")
        worker_repo.add_worker_annotation(worker2_id, pila_id, "Anotación de T2")
        worker_repo.add_worker_annotation(worker2_id, pila_id, "Otra de T2")
        
        # Act
        annotations_w1 = worker_repo.get_worker_annotations(worker1_id)
        annotations_w2 = worker_repo.get_worker_annotations(worker2_id)
        
        # Assert
        assert len(annotations_w1) == 1
        assert len(annotations_w2) == 2


# ==============================================================================
# TESTS DE EDGE CASES Y ROBUSTEZ
# ==============================================================================

@pytest.mark.unit
class TestWorkerRepositoryEdgeCases:
    """Tests para casos límite y situaciones especiales."""

    def test_add_worker_empty_name(self, repos):
        """
        Prueba comportamiento con nombre vacío.
        """
        worker_repo = repos["worker"]
        
        # El comportamiento esperado depende de la validación del modelo
        # Aquí verificamos que no lanza excepción no controlada
        result = worker_repo.add_worker(
            nombre_completo="",
            notas="",
            tipo_trabajador=1
        )
        
        # Debería devolver True o error controlado
        assert result in [True, False, "UNIQUE_CONSTRAINT"]

    def test_get_worker_details_returns_correct_types(self, repos, session):
        """
        Prueba que los tipos de datos devueltos son correctos.
        """
        worker_repo = repos["worker"]
        
        # Arrange
        w = Trabajador(
            nombre_completo="Tipos Test",
            activo=True,
            notas="Nota de prueba",
            tipo_trabajador=2,
            username="tipos_test",
            role="Trabajador"
        )
        session.add(w)
        session.commit()
        worker_id = w.id  # Capturar ID antes de que la sesión expire
        
        # Act
        details = worker_repo.get_worker_details(worker_id)
        
        # Assert tipos
        assert isinstance(details["id"], int)
        assert isinstance(details["nombre_completo"], str)
        assert isinstance(details["activo"], bool)
        assert isinstance(details["tipo_trabajador"], int)

    def test_update_worker_partial_fields(self, repos, session):
        """
        Prueba que update_worker actualiza todos los campos aunque sean iguales.
        """
        worker_repo = repos["worker"]
        
        # Arrange
        w = Trabajador(
            nombre_completo="Parcial Test",
            activo=True,
            notas="Original",
            tipo_trabajador=1
        )
        session.add(w)
        session.commit()
        worker_id = w.id  # Capturar ID antes de que la sesión expire
        
        # Act: Actualizar solo algunos valores pero pasar todos
        result = worker_repo.update_worker(
            worker_id=worker_id,
            nombre_completo="Parcial Test",  # Mismo nombre
            activo=True,  # Mismo estado
            notas="Modificado",  # Diferente
            tipo_trabajador=1  # Mismo tipo
        )
        
        # Assert
        assert result == True
        details = worker_repo.get_worker_details(worker_id)
        assert details["notas"] == "Modificado"

    def test_concurrent_add_same_worker(self, repos):
        """
        Prueba que añadir el mismo trabajador dos veces no duplica.
        """
        worker_repo = repos["worker"]
        
        # 1. Añadir primero
        worker_repo.add_worker("Concurrent Worker", "Nota", 1)
        
        # 2. Añadir segundo (mismo nombre)
        result = worker_repo.add_worker("Concurrent Worker", "Otra nota", 1)
        
        # Debería devolver True (actualizado) o UNIQUE_CONSTRAINT
        assert result in [True, "UNIQUE_CONSTRAINT"]
        
        # Verificar que solo hay 1
        workers = worker_repo.get_all_workers()
        assert len(workers) == 1

    def test_add_worker_with_existing_id_not_found(self, repos):
        """
        Prueba add_worker con un ID que no existe en la BD.
        Cover lines 153-155:
        if worker_id is not None:
            target_worker = session.query(Trabajador).filter_by(id=worker_id).first()
            if not target_worker: ...
        """
        worker_repo = repos["worker"]
        
        # Intentar actualizar un ID que no existe
        # El comportamiento actual documentado en código es logging warning y continuar buscando por nombre
        # o devolver False si decidimos no crearlo.
        # En el código actual: "Decidimos no crearlo... return False" está comentado, 
        # así que busca por nombre a continuación.
        
        result = worker_repo.add_worker(
            nombre_completo="New Worker With Bad ID",
            worker_id=999999
        )
        
        # Al no encontrar el ID, busca por nombre. No lo encuentra. Crea uno nuevo.
        assert result is True
        
        workers = worker_repo.get_all_workers()
        assert len(workers) == 1
        assert workers[0].nombre_completo == "New Worker With Bad ID"
        # El ID NO será 999999, será uno autogenerado
        assert workers[0].id != 999999

    def test_add_worker_conflict_id_vs_name(self, repos, session):
        """
        Prueba conflicto: Se pasa un ID de un trabajador, pero el nombre corresponde a OTRO trabajador distinto.
        Cover lines 179-181.
        """
        worker_repo = repos["worker"]
        
        # Crear trabajador A
        w1 = Trabajador(nombre_completo="Worker A", activo=True)
        # Crear trabajador B
        w2 = Trabajador(nombre_completo="Worker B", activo=True)
        session.add_all([w1, w2])
        session.commit()
        w1_id = w1.id
        w2_id = w2.id
        
        # Intentar actualizar pasando ID de w1, pero nombre de w2
        # El código busca por ID -> encuentra w1
        # El código busca por nombre -> encuentra w2
        # target_worker se establece inicialmente (logica actual prioriza ID o nombre?)
        # Revisando código:
        # 1. Busca por ID (w1) -> target_worker = w1
        # 2. Si target_worker es None, busca por nombre.
        # 3. PERO si buscó por ID, target_worker ya es w1. 
        # ESPERA: El código dice: 
        # "if target_worker is None: target_worker = query(nombre)..."
        # Entonces si encuentra por ID, NO busca por nombre para reemplazar target_worker.
        # PERO luego dice:
        # "if target_worker:"
        #    "if worker_id is None or target_worker.id == worker_id:" -> Actualiza
        #    "else: Conflicto..."
        #
        # Para forzar el conflicto/else, necesitamos que target_worker NO sea el del ID.
        # Esto sucede si NO encontramos por ID (o no pasamos ID), encontramos por Nombre,
        # Y LUEGO pasamos un ID que no coincide.
        #
        # Caso: Pasamos ID inválido (no encontrado), pero nombre existente.
        
        result = worker_repo.add_worker(
            nombre_completo="Worker B", # Nombre de W2
            worker_id=999999 # ID que no existe
        )
        
        # Flujo:
        # 1. Busca ID 999999 -> No encuentra. target_worker = None.
        # 2. Busca Nombre "Worker B" -> Encuentra w2. target_worker = w2.
        # 3. Entra en if target_worker:
        # 4. Check: worker_id (999999) is None? NO.
        # 5. Check: target_worker.id (w2.id) == worker_id (999999)? NO.
        # 6. ELSE -> Conflicto.
        
        assert result is False

    def test_add_worker_integrity_error(self, repos, session):
        """
        Simula un IntegrityError al hacer flush.
        Cover lines 198-203.
        """
        worker_repo = repos["worker"]
        
        # Crear trabajador previo
        w = Trabajador(nombre_completo="Existing", username="user_exist")
        session.add(w)
        session.commit()
        
        # Intentar crear nuevo con MISMO username (que es unique) pero distinto nombre
        # Esto debería fallar en DB level con IntegrityError
        
        result = worker_repo.add_worker(
            nombre_completo="New Name",
            username="user_exist" # Duplicate username!
        )
        
        # El repositorio captura IntegrityError y devuelve "UNIQUE_CONSTRAINT"
        assert result == "UNIQUE_CONSTRAINT"

    def test_update_user_credentials_worker_not_found(self, repos):
        """
        Prueba update_user_credentials con worker inexistente.
        Cover line 353 (return False path).
        """
        worker_repo = repos["worker"]
        result = worker_repo.update_user_credentials(99999, "u", "p", "r")
        assert result is False

    def test_concurrent_add_same_worker(self, repos):
        """
        Prueba que añadir el mismo trabajador dos veces no duplica.
        """
        worker_repo = repos["worker"]
        
        # Act: Añadir dos veces
        result1 = worker_repo.add_worker(
            nombre_completo="Concurrente",
            notas="Primera vez",
            tipo_trabajador=1
        )
        result2 = worker_repo.add_worker(
            nombre_completo="Concurrente",
            notas="Segunda vez",
            tipo_trabajador=2
        )
        
        # Assert
        assert result1 == True
        assert result2 == True  # Debe actualizar, no fallar
        
        workers = worker_repo.get_all_workers()
        assert len(workers) == 1
        # Debe tener los datos de la segunda llamada
        assert workers[0].tipo_trabajador == 2  # tipo_trabajador actualizado
