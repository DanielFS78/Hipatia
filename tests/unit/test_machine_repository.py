# tests/unit/test_machine_repository.py
"""
Tests unitarios completos para MachineRepository.
Cubren gestión de máquinas, mantenimiento y la lógica crítica de grupos de preparación.

Autor: Sistema de Tests Migración SQLAlchemy
Fecha: 25/12/2025
"""

import pytest
from unittest.mock import MagicMock
from datetime import date
from database.models import Maquina, GrupoPreparacion, PreparacionPaso, Subfabricacion, Producto

# ==============================================================================
# FIXTURES ESPECÍFICOS
# ==============================================================================

@pytest.fixture
def session_no_close(session):
    """
    Envuelve la sesión para evitar que 'session.close()' la cierre realmente
    cuando es llamado por los repositorios. Esto es necesario porque los tests
    reutilizan la misma sesión en memoria.
    """
    original_close = session.close
    session.close = MagicMock() # Mockear close para que no haga nada
    yield session
    # Restaurar para limpieza final si fuera necesario (aunque el fixture session hace teardown)
    session.close = original_close

@pytest.fixture
def machine_repo_test(repos, session_no_close):
    """Devuelve el repositorio usando la sesión 'no cerrable'."""
    # Actualizamos el factory del repo para devolver nuestra sesión modificada
    repo = repos["machine"]
    repo.session_factory = lambda: session_no_close
    return repo

# ==============================================================================
# TESTS DE OBTENCIÓN (GET)
# ==============================================================================

@pytest.mark.unit
class TestMachineRepositoryGetMethods:
    """Tests para métodos de obtención de máquinas."""

    def test_get_all_machines_empty(self, machine_repo_test):
        """Prueba que get_all_machines() devuelve lista vacía si no hay máquinas."""
        machines = machine_repo_test.get_all_machines()
        assert machines == []

    def test_get_all_machines_with_data(self, machine_repo_test, session_no_close):
        """Prueba la obtención de todas las máquinas activas."""
        # Arrange
        m1 = Maquina(nombre="M1", departamento="D1", tipo_proceso="P1", activa=True)
        m2 = Maquina(nombre="M2", departamento="D1", tipo_proceso="P2", activa=True)
        session_no_close.add_all([m1, m2])
        session_no_close.commit()
        
        # Act
        machines = machine_repo_test.get_all_machines()
        
        # Assert
        assert len(machines) == 2
        # Verificar orden alfabético - usando atributos DTO
        assert machines[0].nombre == "M1"
        assert machines[1].nombre == "M2"
        # Verificar que son objetos DTO con atributos
        assert hasattr(machines[0], 'id')
        assert hasattr(machines[0], 'nombre')
        assert hasattr(machines[0], 'departamento')
        assert hasattr(machines[0], 'tipo_proceso')
        assert hasattr(machines[0], 'activa')

    def test_get_all_machines_excludes_inactive(self, machine_repo_test, session_no_close):
        """Prueba que se excluyen las máquinas inactivas por defecto."""
        # Arrange
        m_active = Maquina(nombre="Activa", departamento="D1", tipo_proceso="P1", activa=True)
        m_inactive = Maquina(nombre="Inactiva", departamento="D1", tipo_proceso="P1", activa=False)
        session_no_close.add_all([m_active, m_inactive])
        session_no_close.commit()
        
        # Act
        machines = machine_repo_test.get_all_machines(include_inactive=False)
        
        # Assert
        assert len(machines) == 1
        assert machines[0].nombre == "Activa"

    def test_get_all_machines_include_inactive(self, machine_repo_test, session_no_close):
        """Prueba que se incluyen inactivas si se solicita."""
        m_active = Maquina(nombre="Activa", departamento="D1", tipo_proceso="P1", activa=True)
        m_inactive = Maquina(nombre="Inactiva", departamento="D1", tipo_proceso="P1", activa=False)
        session_no_close.add_all([m_active, m_inactive])
        session_no_close.commit()
        
        machines = machine_repo_test.get_all_machines(include_inactive=True)
        assert len(machines) == 2

    def test_get_latest_machines_limit(self, machine_repo_test, session_no_close):
        """Prueba que get_latest_machines respeta el límite y orden."""
        # Crear 5 máquinas
        for i in range(1, 6):
            session_no_close.add(Maquina(nombre=f"M{i}", departamento="D", tipo_proceso="P", activa=True))
        session_no_close.commit()
        
        # Pedir las últimas 3
        machines = machine_repo_test.get_latest_machines(limit=3)
        
        assert len(machines) == 3
        # Deben ser M5, M4, M3 (orden descendente por ID)
        assert "M5" in machines[0].nombre
        
    def test_get_machines_by_process_type(self, machine_repo_test, session_no_close):
        """Prueba filtrado por tipo de proceso."""
        m1 = Maquina(nombre="Torno1", departamento="D", tipo_proceso="Mecanizado", activa=True)
        m2 = Maquina(nombre="Fresadora1", departamento="D", tipo_proceso="Mecanizado", activa=True)
        m3 = Maquina(nombre="Soldador1", departamento="D", tipo_proceso="Soldadura", activa=True)
        session_no_close.add_all([m1, m2, m3])
        session_no_close.commit()
        
        machines = machine_repo_test.get_machines_by_process_type("Mecanizado")
        
        assert len(machines) == 2
        names = [m.nombre for m in machines]
        assert "Torno1" in names
        assert "Fresadora1" in names
        assert "Soldador1" not in names

    def test_get_distinct_machine_processes(self, machine_repo_test, session_no_close):
        """Prueba obtención de tipos de procesos únicos."""
        session_no_close.add(Maquina(nombre="M1", departamento="D", tipo_proceso="Corte", activa=True))
        session_no_close.add(Maquina(nombre="M2", departamento="D", tipo_proceso="Corte", activa=True))
        session_no_close.add(Maquina(nombre="M3", departamento="D", tipo_proceso="Ensamblaje", activa=True))
        session_no_close.commit()
        
        processes = machine_repo_test.get_distinct_machine_processes()
        
        assert len(processes) == 2
        assert "Corte" in processes
        assert "Ensamblaje" in processes

# ==============================================================================
# TESTS DE GESTIÓN DE MÁQUINAS (ADD/UPDATE)
# ==============================================================================

@pytest.mark.unit
class TestMachineRepositoryCRUD:
    """Tests para añadir y actualizar máquinas."""

    def test_add_machine_success(self, machine_repo_test):
        """Prueba añadir una máquina nueva."""
        result = machine_repo_test.add_machine(
            nombre="Nueva Maquina",
            departamento="Producción",
            tipo_proceso="General"
        )
        
        assert result == True
        machines = machine_repo_test.get_all_machines()
        assert len(machines) == 1
        assert machines[0].nombre == "Nueva Maquina"

    def test_add_machine_duplicate_name_updates(self, machine_repo_test, session_no_close):
        """Prueba que si se añade una máquina con nombre existente, se actualiza."""
        # Arrange
        m = Maquina(nombre="Existente", departamento="Viejo", tipo_proceso="Viejo", activa=True)
        session_no_close.add(m)
        session_no_close.commit()
        original_id = m.id
        
        # Act
        result = machine_repo_test.add_machine(
            nombre="Existente",
            departamento="Nuevo Dept",
            tipo_proceso="Nuevo Proc"
        )
        
        # Assert
        assert result == True
        # Verificar que se actualizó y no se creó otra
        updated = session_no_close.query(Maquina).filter_by(id=original_id).first()
        assert updated.departamento == "Nuevo Dept"
        assert updated.tipo_proceso == "Nuevo Proc"
        
        count = session_no_close.query(Maquina).count()
        assert count == 1

    def test_add_machine_explicit_id(self, machine_repo_test, session_no_close):
        """Prueba actualizar una máquina pasando su ID explícitamente."""
        m = Maquina(nombre="Original", departamento="D", tipo_proceso="P", activa=True)
        session_no_close.add(m)
        session_no_close.commit()
        m_id = m.id
        
        # Act: Cambiamos nombre pasando el ID
        result = machine_repo_test.add_machine(
            nombre="Nuevo Nombre",
            departamento="D",
            tipo_proceso="P",
            machine_id=m_id
        )
        
        assert result == True
        updated = session_no_close.get(Maquina, m_id)
        assert updated.nombre == "Nuevo Nombre"

    def test_update_machine_success(self, machine_repo_test, session_no_close):
        """Prueba el método update_machine explícito."""
        m = Maquina(nombre="Update Me", departamento="D", tipo_proceso="P", activa=True)
        session_no_close.add(m)
        session_no_close.commit()
        m_id = m.id # Capturar ID antes
        
        result = machine_repo_test.update_machine(
            machine_id=m_id,
            nombre="Updated",
            departamento="D_New",
            tipo_proceso="P_New",
            activa=False
        )
        
        assert result == True
        updated = session_no_close.get(Maquina, m_id)
        assert updated.nombre == "Updated"
        assert updated.activa == False

    def test_update_machine_not_found(self, machine_repo_test):
        """Prueba que update_machine falla si no existe el ID."""
        result = machine_repo_test.update_machine(999, "N", "D", "P", True)
        assert result == False

# ==============================================================================
# TESTS DE MANTENIMIENTO
# ==============================================================================

@pytest.mark.unit
class TestMachineMaintenance:
    """Tests para registrar y consultar mantenimientos."""

    def test_add_machine_maintenance(self, machine_repo_test, session_no_close):
        """Prueba añadir registro de mantenimiento."""
        m = Maquina(nombre="Maint Test", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        m_id = m.id # Capturar ID
        
        fecha = date.today()
        result = machine_repo_test.add_machine_maintenance(m_id, fecha, "Revisión anual")
        
        assert result == True
        
        history = machine_repo_test.get_machine_maintenance_history(m_id)
        assert len(history) == 1
        # Ahora usamos atributos DTO
        assert str(history[0].maintenance_date) == str(fecha)
        assert history[0].notes == "Revisión anual"

    def test_get_machine_maintenance_history_order(self, machine_repo_test, session_no_close):
        """Prueba que el historial viene ordenado por fecha descendente."""
        m = Maquina(nombre="Maint Order", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        m_id = m.id # Capturar ID
        
        d1 = date(2025, 1, 1)
        d2 = date(2025, 2, 1)
        
        machine_repo_test.add_machine_maintenance(m_id, d1, "Enero")
        machine_repo_test.add_machine_maintenance(m_id, d2, "Febrero")
        
        history = machine_repo_test.get_machine_maintenance_history(m_id)
        
        assert len(history) == 2
        assert history[0].notes == "Febrero" # Más reciente primero
        assert history[1].notes == "Enero"

# ==============================================================================
# TESTS CRÍTICOS: GRUPOS DE PREPARACIÓN
# ==============================================================================

@pytest.mark.unit
class TestMachinePrepGroup:
    """Tests para grupos de preparación (Lógica crítica)."""

    def test_add_prep_group_success(self, machine_repo_test, session_no_close):
        """Prueba añadir un grupo correctamente."""
        # Crear máquina
        m = Maquina(nombre="M Prep", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        m_id = m.id
        
        # Act
        # Seed Product
        p = Producto(codigo="PROD1", descripcion="Desc", departamento="D", tipo_trabajador=1, tiene_subfabricaciones=False)
        session_no_close.add(p)
        session_no_close.commit()
        
        group_id = machine_repo_test.add_prep_group(
            machine_id=m_id,
            name="Grupo 1",
            description="Desc 1",
            producto_codigo="PROD1"
        )
        
        # Assert
        assert isinstance(group_id, int)
        # Verificar en BD
        saved = session_no_close.get(GrupoPreparacion, group_id)
        assert saved.nombre == "Grupo 1"
        assert saved.maquina_id == m_id

    def test_add_prep_group_duplicate_name_for_machine(self, machine_repo_test, session_no_close):
        """
        Prueba CRÍTICA: No permitir dos grupos con el mismo nombre en la misma máquina.
        Debe devolver 'UNIQUE_CONSTRAINT'.
        """
        # Arrange
        m = Maquina(nombre="M Dupe", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        m_id = m.id
        
        # Primer grupo
        machine_repo_test.add_prep_group(m_id, "Grupo A", "Desc", None)
        
        # Act: Intentar añadir el mismo nombre (aunque cambie descripción)
        result = machine_repo_test.add_prep_group(
            machine_id=m_id,
            name="Grupo A",
            description="Otra descripción",
            producto_codigo=None
        )
        
        # Assert
        assert result == "UNIQUE_CONSTRAINT"
        
        # Verificar que no se duplicó
        grupos = machine_repo_test.get_groups_for_machine(m_id)
        assert len(grupos) == 1

    def test_get_groups_for_machine(self, machine_repo_test, session_no_close):
        """Prueba obtener grupos de una máquina."""
        m = Maquina(nombre="M Groups", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        m_id = m.id
        
        machine_repo_test.add_prep_group(m_id, "Z Grupo", "Desc", None)
        machine_repo_test.add_prep_group(m_id, "A Grupo", "Desc", None)
        
        groups = machine_repo_test.get_groups_for_machine(m_id)
        
        assert len(groups) == 2
        # Verificar orden alfabético - usando atributos DTO
        assert groups[0].nombre == "A Grupo"
        assert groups[1].nombre == "Z Grupo"

    def test_update_prep_group(self, machine_repo_test, session_no_close):
        """Prueba actualizar un grupo."""
        m = Maquina(nombre="M Update", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        
        # Seed Products for FK
        p1 = Producto(codigo="PORIG", descripcion="Desc", departamento="D", tipo_trabajador=1, tiene_subfabricaciones=False)
        p2 = Producto(codigo="PNEW", descripcion="Desc", departamento="D", tipo_trabajador=1, tiene_subfabricaciones=False)
        session_no_close.add_all([p1, p2])
        session_no_close.commit()

        g_id = machine_repo_test.add_prep_group(m.id, "Original", "Desc", None)
        
        # Act
        result = machine_repo_test.update_prep_group(
            group_id=g_id,
            name="Cambiado",
            description="Nueva Desc",
            producto_codigo="PNEW"
        )
        
        assert result == True
        updated = session_no_close.get(GrupoPreparacion, g_id)
        assert updated.nombre == "Cambiado"
        assert updated.producto_codigo == "PNEW"

    def test_delete_prep_group_cascade(self, machine_repo_test, session_no_close):
        """
        Prueba CRÍTICA: Eliminar un grupo debe eliminar sus pasos (Cascade).
        """
        # Arrange
        m = Maquina(nombre="M Cascade", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        
        g_id = machine_repo_test.add_prep_group(m.id, "Grupo Borrar", "Desc", None)
        
        # Añadir pasos al grupo
        machine_repo_test.add_prep_step(g_id, "Paso 1", 10.0, "D", False)
        machine_repo_test.add_prep_step(g_id, "Paso 2", 20.0, "D", False)
        
        # Verificar que existen
        assert session_no_close.query(PreparacionPaso).filter_by(grupo_id=g_id).count() == 2
        
        # Act: Eliminar grupo
        result = machine_repo_test.delete_prep_group(g_id)
        
        # Assert
        assert result == True
        # El grupo no debe existir
        assert session_no_close.get(GrupoPreparacion, g_id) is None
        # Los pasos NO deben existir (Cascade)
        assert session_no_close.query(PreparacionPaso).filter_by(grupo_id=g_id).count() == 0

    def test_get_group_details_success(self, machine_repo_test, session_no_close):
        """Prueba obtener detalles de un grupo existente - Cubre líneas 404-415."""
        # Arrange
        m = Maquina(nombre="M Details", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        
        # Crear producto para FK
        p = Producto(codigo="DET_PROD", descripcion="Producto Details", departamento="D", 
                    tipo_trabajador=1, tiene_subfabricaciones=False)
        session_no_close.add(p)
        session_no_close.commit()
        
        g_id = machine_repo_test.add_prep_group(m.id, "Grupo Detalle", "Descripcion detallada", "DET_PROD")
        
        # Act
        result = machine_repo_test.get_group_details(g_id)
        
        # Assert
        assert result is not None
        from core.dtos import PreparationGroupDTO
        assert isinstance(result, PreparationGroupDTO)
        assert result.id == g_id
        assert result.nombre == "Grupo Detalle"
        assert result.descripcion == "Descripcion detallada"
        assert result.producto_codigo == "DET_PROD"

    def test_get_group_details_not_found(self, machine_repo_test, session_no_close):
        """Prueba obtener detalles de un grupo inexistente - Cubre rama None lineas 407-408."""
        # Act
        result = machine_repo_test.get_group_details(99999)
        
        # Assert
        assert result is None

    def test_get_group_details_without_producto(self, machine_repo_test, session_no_close):
        """Prueba obtener detalles de un grupo sin producto asociado."""
        # Arrange
        m = Maquina(nombre="M No Prod", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        
        g_id = machine_repo_test.add_prep_group(m.id, "Grupo Sin Prod", "Desc", None)
        
        # Act
        result = machine_repo_test.get_group_details(g_id)
        
        # Assert
        assert result is not None
        assert result.producto_codigo is None

# ==============================================================================
# TESTS DE PASOS DE PREPARACION
# ==============================================================================


@pytest.mark.unit
class TestMachinePrepStep:
    """Tests para pasos individuales dentro de grupos."""

    def test_add_prep_step_success(self, machine_repo_test, session_no_close):
        """Prueba añadir paso."""
        m = Maquina(nombre="M", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        g_id = machine_repo_test.add_prep_group(m.id, "G", "D", None)
        
        # Act
        s_id = machine_repo_test.add_prep_step(
            group_id=g_id,
            name="Calentar",
            time=15.5,
            description="Subir temp",
            is_daily=True
        )
        
        assert isinstance(s_id, int)
        step = session_no_close.get(PreparacionPaso, s_id)
        assert step.nombre == "Calentar"
        assert step.tiempo_fase == 15.5
        assert step.es_diario == True

    def test_update_prep_step_partial(self, machine_repo_test, session_no_close):
        """Prueba actualización parcial de un paso (usando dict)."""
        m = Maquina(nombre="M", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        g_id = machine_repo_test.add_prep_group(m.id, "G", "D", None)
        s_id = machine_repo_test.add_prep_step(g_id, "Original", 10, "D", False)
        
        # Act: Solo cambiar tiempo y nombre
        data = {
            "nombre": "Cambiado",
            "tiempo_fase": 99.9
            # description y es_diario no se pasan, deben mantenerse
        }
        result = machine_repo_test.update_prep_step(s_id, data)
        
        # Assert
        assert result == True
        updated = session_no_close.get(PreparacionPaso, s_id)
        assert updated.nombre == "Cambiado"
        assert updated.tiempo_fase == 99.9
        assert updated.descripcion == "D" # Se mantiene

    def test_get_steps_for_group(self, machine_repo_test, session_no_close):
        """Prueba obtener pasos de un grupo."""
        m = Maquina(nombre="M", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        g_id = machine_repo_test.add_prep_group(m.id, "G", "D", None)
        
        machine_repo_test.add_prep_step(g_id, "S1", 10, "D", False)
        machine_repo_test.add_prep_step(g_id, "S2", 20, "D", True)
        
        steps = machine_repo_test.get_steps_for_group(g_id)
        
        assert len(steps) == 2
        # Usando atributos DTO: id, nombre, tiempo_fase, descripcion, es_diario
        assert steps[0].nombre == "S1"
        assert steps[1].es_diario == True # S2 es diario

    def test_delete_prep_step(self, machine_repo_test, session_no_close):
        """Prueba eliminar un paso individual."""
        m = Maquina(nombre="M", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        g_id = machine_repo_test.add_prep_group(m.id, "G", "D", None)
        s_id = machine_repo_test.add_prep_step(g_id, "S1", 10, "D", False)
        
        result = machine_repo_test.delete_prep_step(s_id)
        
        assert result == True
        assert session_no_close.get(PreparacionPaso, s_id) is None

# ==============================================================================
# TESTS DE ESTADÍSTICAS
# ==============================================================================

@pytest.mark.unit
class TestMachineUsageStats:
    """Tests para cálculo de estadísticas de uso."""

    def test_get_machine_usage_stats(self, machine_repo_test, session_no_close):
        """Prueba el cálculo de tiempos totales por máquina con JOIN."""
        
        # Arrange: Crear Máquinas
        m1 = Maquina(nombre="M Alta", departamento="D", tipo_proceso="P")
        m2 = Maquina(nombre="M Baja", departamento="D", tipo_proceso="P")
        session_no_close.add_all([m1, m2])
        
        # Crear Producto Dummy para FK
        p = Producto(
            codigo="P1",
            descripcion="Desc",
            departamento="D",
            tipo_trabajador=1,
            tiene_subfabricaciones=True
        )
        session_no_close.add(p)
        session_no_close.commit()
        
        # Crear Subfabricaciones CORRECTAS
        sf1 = Subfabricacion(
            producto_codigo="P1",
            descripcion="Op 1",
            tiempo=100.0,
            tipo_trabajador=1,
            maquina_id=m1.id
        )
        sf2 = Subfabricacion(
            producto_codigo="P1",
            descripcion="Op 2",
            tiempo=50.0,
            tipo_trabajador=1,
            maquina_id=m1.id
        )
        sf3 = Subfabricacion(
            producto_codigo="P1",
            descripcion="Op 3",
            tiempo=10.0,
            tipo_trabajador=1,
            maquina_id=m2.id
        )
        
        session_no_close.add_all([sf1, sf2, sf3])
        session_no_close.commit()
        
        # Act
        stats = machine_repo_test.get_machine_usage_stats()
        
        # Assert
        # Debe devolver [(Nombre, TotalTime)] ordenado desc
        assert len(stats) == 2
        assert stats[0][0] == "M Alta"
        assert stats[0][1] == 150.0 # 100 + 50
        assert stats[1][0] == "M Baja"
        assert stats[1][1] == 10.0

# ==============================================================================
# TESTS DE COBERTURA DE CÓDIGO (EDGE CASES)
# ==============================================================================

@pytest.mark.unit
class TestMachineRepositoryCoverage:
    """Tests adicionales para cubrir ramas de error y casos límite."""

    def test_add_machine_id_not_found(self, machine_repo_test, session_no_close):
        """Prueba add_machine con un machine_id que no existe (warning)."""
        result = machine_repo_test.add_machine(
            nombre="Maquina Fantasma",
            departamento="D",
            tipo_proceso="P",
            machine_id=9999
        )
        
        assert result == True
        # Verificar que se creó con un NUEVO ID, no 9999
        m = session_no_close.query(Maquina).filter_by(nombre="Maquina Fantasma").first()
        assert m is not None
        assert m.id != 9999

    def test_add_machine_id_conflict_with_name(self, machine_repo_test, session_no_close):
        """Prueba conflicto: ID pasado no coincide con el ID de la máquina encontrada por nombre."""
        m = Maquina(nombre="Conflicto", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        real_id = m.id
        
        result = machine_repo_test.add_machine(
            nombre="Conflicto",
            departamento="D",
            tipo_proceso="P",
            machine_id=real_id + 1 # ID incorrecto
        )
        
        assert result == False

    def test_update_prep_group_not_found(self, machine_repo_test):
        """Prueba actualizar grupo inexistente."""
        result = machine_repo_test.update_prep_group(999, "N", "D")
        assert result == False

    def test_delete_prep_group_not_found(self, machine_repo_test):
        """Prueba eliminar grupo inexistente."""
        result = machine_repo_test.delete_prep_group(999)
        assert result == False

    def test_update_prep_step_not_found(self, machine_repo_test):
        """Prueba actualizar paso inexistente."""
        result = machine_repo_test.update_prep_step(999, {})
        assert result == False

    def test_delete_prep_step_not_found(self, machine_repo_test):
        """Prueba eliminar paso inexistente."""
        result = machine_repo_test.delete_prep_step(999)
        assert result == False

    def test_add_machine_concurrency_integrity_error(self, machine_repo_test, session_no_close):
        """
        Prueba manejo de IntegrityError simulando una condición de carrera.
        Simula:
        1. Query inicial -> None (procede a crear)
        2. Insert/Flush -> Falla con IntegrityError (otro hilo insertó)
        3. Query recuperación -> Encuentra la máquina creada por otro hilo
        """
        from sqlalchemy.exc import IntegrityError
        
        # Necesitamos un mock de session muy específico
        mock_session = MagicMock()
        
        # 1. Configurar query inicial para devolver None (simulando que no existe al principio)
        # Y el query de recuperación para devolver un objeto (simulando que apareció)
        existing_machine = MagicMock(id=888, nombre="Concurrente")
        
        # side_effect para chain: query().filter_by().first()
        # Primer llamada (inicial) -> None
        # Segunda llamada (recuperación) -> existing_machine
        # Tercera llamada (log/check) -> existing_machine 
        
        # Mockeamos el objeto Query devuelto por session.query(Maquina)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        
        # Configurar filter_by para devolverse a sí mismo (para encadenar)
        mock_query.filter_by.return_value = mock_query
        
        # Configurar first() para devolver None primero, luego el objeto
        mock_query.first.side_effect = [None, existing_machine, existing_machine]
        
        # Configurar flush para lanzar IntegrityError
        mock_session.flush.side_effect = IntegrityError("Mock", "params", "orig")
        
        # Inyectar el mock session en el factory
        machine_repo_test.session_factory = lambda: mock_session
        
        # Act
        result = machine_repo_test.add_machine(
            nombre="Concurrente",
            departamento="D",
            tipo_proceso="P"
        )
        
        # Assert
        assert result == True
        # Verificar que se llamó a rollback
        mock_session.rollback.assert_called_once()

    def test_add_machine_integrity_error_unknown(self, machine_repo_test, session_no_close):
        """
        Prueba manejo de IntegrityError cuando NO se recupera la máquina (ej: otro constraint).
        Debe devolver "UNIQUE_CONSTRAINT".
        """
        from sqlalchemy.exc import IntegrityError
        
        mock_session = MagicMock()
        
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        
        # first() devuelve siempre None (antes y después del error)
        mock_query.first.return_value = None
        
        # flush falla
        mock_session.flush.side_effect = IntegrityError("Mock", "params", "orig")
        
        machine_repo_test.session_factory = lambda: mock_session
        
        result = machine_repo_test.add_machine(
            nombre="ErrorRaro",
            departamento="D",
            tipo_proceso="P"
        )
        
        assert result == "UNIQUE_CONSTRAINT"
        mock_session.rollback.assert_called_once()

    # ==============================================================================
    # TESTS PARA COBERTURA 100% Y BASE REPOSITORY
    # ==============================================================================

    def test_delete_machine_success(self, machine_repo_test, session_no_close):
        """Prueba unitaria de eliminación exitosa."""
        m = Maquina(nombre="BorrarUnit", departamento="D", tipo_proceso="P")
        session_no_close.add(m)
        session_no_close.commit()
        m_id = m.id
        
        result = machine_repo_test.delete_machine(m_id)
        assert result == True
        assert session_no_close.get(Maquina, m_id) is None

    def test_delete_machine_not_found(self, machine_repo_test):
        """Prueba eliminar máquina inexistente para cubrir rama if not maquina."""
        result = machine_repo_test.delete_machine(9999)
        assert result == False

    def test_get_machine_usage_stats_empty(self, machine_repo_test):
        """Asegurar cobertura de estadísticas vacías."""
        stats = machine_repo_test.get_machine_usage_stats()
        assert stats == []

    def test_safe_execute_no_session(self, machine_repo_test):
        """Simula fallo al obtener sesión para cubrir línea 48-49 de base.py."""
        machine_repo_test.get_session = MagicMock(return_value=None)
        result = machine_repo_test.get_all_machines()
        assert result == []

    def test_get_session_exception(self, machine_repo_test):
        """Simula excepción en factory para cubrir línea 37-39 de base.py."""
        machine_repo_test.session_factory = MagicMock(side_effect=Exception("Factory error"))
        result = machine_repo_test.get_all_machines()
        assert result == []

    def test_safe_execute_sqlalchemy_error(self, machine_repo_test):
        """Cubre el bloque de SQLAlchemyError en BaseRepository."""
        from sqlalchemy.exc import SQLAlchemyError
        mock_session = MagicMock()
        mock_session.query.side_effect = SQLAlchemyError("Mocked SA Error")
        machine_repo_test.session_factory = lambda: mock_session
        
        result = machine_repo_test.get_all_machines()
        assert result == []
        mock_session.rollback.assert_called_once()

    def test_safe_execute_generic_exception(self, machine_repo_test):
        """Cubre el bloque de Exception genérica en BaseRepository."""
        mock_session = MagicMock()
        mock_session.query.side_effect = Exception("Simulated crash")
        machine_repo_test.session_factory = lambda: mock_session
        
        result = machine_repo_test.get_all_machines()
        assert result == []
        mock_session.rollback.assert_called_once()

    def test_safe_execute_expunge(self, machine_repo_test, session):
        """Cubre el borrado de objetos de la sesión (expunge) en base.py."""
        from database.models import Maquina
        m = Maquina(nombre="ExpungeTest", departamento="D", tipo_proceso="T")
        session.add(m)
        session.flush()
        
        def _op(session):
            return m
            
        result = machine_repo_test.safe_execute(_op)
        assert result.nombre == "ExpungeTest"

    def test_safe_execute_expunge_list(self, machine_repo_test, session):
        """Cubre el borrado de lista de objetos de la sesión en base.py."""
        from database.models import Maquina
        m1 = Maquina(nombre="E1", departamento="D", tipo_proceso="T")
        m2 = Maquina(nombre="E2", departamento="D", tipo_proceso="T")
        session.add_all([m1, m2])
        session.flush()
        
        def _op(session):
            return [m1, m2]
            
        result = machine_repo_test.safe_execute(_op)
        assert len(result) == 2
