
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from database.models import (
    Trabajador, Fabricacion, Producto, TrabajoLog, IncidenciaLog,
    PasoTrazabilidad, trabajador_fabricacion_link, fabricacion_productos, Maquina
)
from database.repositories.tracking_repository import TrackingRepository
from core.tracking_dtos import (
    TrabajoLogDTO, PasoTrazabilidadDTO, IncidenciaLogDTO, 
    IncidenciaAdjuntoDTO, FabricacionAsignadaDTO
)
from sqlalchemy import insert
from sqlalchemy.orm import Session

# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def session_no_close(session):
    """
    Prevents repository from closing the session during tests.
    """
    original_close = session.close
    session.close = MagicMock()
    yield session
    session.close = original_close

@pytest.fixture
def tracking_repo_test(session_no_close):
    """Returns repository instance using the shared session."""
    return TrackingRepository(lambda: session_no_close)

@pytest.fixture
def seed_tracking_data(session_no_close):
    """Seeds basic data for tracking tests."""
    session = session_no_close
    
    # 1. Trabajador
    worker = Trabajador(nombre_completo="Juan Test", tipo_trabajador=1, activo=True)
    session.add(worker)
    
    # 2. Producto
    prod = Producto(
        codigo="PROD-TRACK-01", 
        descripcion="Producto Tracker",
        departamento="Test",
        tipo_trabajador=1,
        tiene_subfabricaciones=False,
        tiempo_optimo=100.0
    )
    session.add(prod)
    
    # 3. Fabricacion
    fab = Fabricacion(codigo="FAB-TRACK-01", descripcion="Fab Tracker")
    session.add(fab)
    
    # 4. Maquina
    maquina = Maquina(nombre="Maquina Trazabilidad", departamento="T", tipo_proceso="P", activa=True)
    session.add(maquina)
    
    session.commit()
    
    return {
        "worker_id": worker.id,
        "product_code": prod.codigo,
        "fab_id": fab.id,
        "fab_code": fab.codigo,
        "maquina_id": maquina.id
    }

# ==============================================================================
# TESTS
# ==============================================================================

@pytest.mark.unit
class TestTrackingRepositoryFull:

    # --- Core Work Log (Inicio/Fin/Obtencion) ---

    def test_iniciar_trabajo_creates_new(self, tracking_repo_test, seed_tracking_data):
        """Test iniciar_trabajo creates a new log when none exists."""
        dto = tracking_repo_test.iniciar_trabajo(
            qr_code="QR-NEW-001",
            trabajador_id=seed_tracking_data['worker_id'],
            fabricacion_id=seed_tracking_data['fab_id'],
            producto_codigo=seed_tracking_data['product_code']
        )
        assert dto is not None
        assert dto.qr_code == "QR-NEW-001"
        assert dto.estado == "en_proceso"
        assert dto.trabajador_nombre == "Juan Test"

    def test_obtener_o_crear_trabajo_existing(self, tracking_repo_test, seed_tracking_data):
        """Test retrieving an existing log instead of creating new."""
        # Create first
        dto1 = tracking_repo_test.iniciar_trabajo(
            qr_code="QR-EXIST-001",
            trabajador_id=seed_tracking_data['worker_id'],
            fabricacion_id=seed_tracking_data['fab_id'],
            producto_codigo=seed_tracking_data['product_code']
        )
        # Call again
        dto2 = tracking_repo_test.obtener_o_crear_trabajo_log_por_qr(
            qr_code="QR-EXIST-001",
            trabajador_id=seed_tracking_data['worker_id'],
            fabricacion_id=seed_tracking_data['fab_id'],
            producto_codigo=seed_tracking_data['product_code'],
            notas="Retry"
        )
        
        assert dto1.id == dto2.id
        # Should not update notes or state on retrieval
        assert dto2.notas is None

    def test_obtener_o_crear_error_handling(self, tracking_repo_test, seed_tracking_data):
        """Test error handling with mocked integrity error."""
        from sqlalchemy.exc import IntegrityError
        
        # We need to simulate an error during the add/commit phase
        # Since we pass lambda: session_no_close, getting access to the session to mock commit is tricky
        # unless we access it from the repo.
        
        # Strategy: Pass invalid ID and assert None (relies on DB constraint which might be off).
        # Better Strategy: Mock session.commit() on the session object used.
        
        session = tracking_repo_test.session_factory()
        original_commit = session.commit
        session.commit = MagicMock(side_effect=IntegrityError("Mock", "params", "orig"))
        
        dto = tracking_repo_test.obtener_o_crear_trabajo_log_por_qr(
            qr_code="QR-ERR",
            trabajador_id=seed_tracking_data['worker_id'],
            fabricacion_id=seed_tracking_data['fab_id'],
            producto_codigo="PROD"
        )
        
        # Restore
        session.commit = original_commit
        
        assert dto is None

    # ... existing start/find tests ...

    def test_finalizar_trabajo(self, tracking_repo_test, seed_tracking_data):
        """Test finalizing a work log."""
        job = tracking_repo_test.iniciar_trabajo("QR-FIN-001", seed_tracking_data['worker_id'], seed_tracking_data['fab_id'], seed_tracking_data['product_code'])
        
        # Act
        completed_job = tracking_repo_test.finalizar_trabajo_log(job.id, "Finalizado OK")
        
        # Assert
        assert completed_job is not None
        assert completed_job.estado == "completado"
        assert completed_job.tiempo_fin is not None
        assert completed_job.duracion_segundos is not None
        assert "Finalizado OK" in completed_job.notas

        # Verify idempotency or error on already finished?
        # Setup defines logic: "en_proceso" filter prevents re-finishing via this method main path returning None
        retry = tracking_repo_test.finalizar_trabajo_log(job.id, "Again")
        assert retry is None

    def test_pausar_reanudar_trabajo(self, tracking_repo_test, seed_tracking_data):
        """Test pause and resume flow."""
        job = tracking_repo_test.iniciar_trabajo("QR-PAUSE-001", seed_tracking_data['worker_id'], seed_tracking_data['fab_id'], seed_tracking_data['product_code'])
        
        # Pause
        success = tracking_repo_test.pausar_trabajo(job.qr_code, "Lunch")
        assert success is True
        
        # Verify state
        job_paused = tracking_repo_test.obtener_trabajo_por_qr("QR-PAUSE-001")
        assert job_paused.estado == "pausado"
        assert "Lunch" in job_paused.notas
        
        # Resume
        success_resume = tracking_repo_test.reanudar_trabajo(job.qr_code)
        assert success_resume is True
        
        job_resumed = tracking_repo_test.obtener_trabajo_por_qr("QR-PAUSE-001")
        assert job_resumed.estado == "en_proceso"
        # Relaxed match to avoid encoding issues
        assert "Reanudac" in job_resumed.notas

    def test_trazabilidad_pasos(self, tracking_repo_test, seed_tracking_data):
        """Test step traceability lifecycle."""
        job = tracking_repo_test.iniciar_trabajo("QR-STEP-001", seed_tracking_data['worker_id'], seed_tracking_data['fab_id'], seed_tracking_data['product_code'])
        
        # 1. Start Step
        step = tracking_repo_test.iniciar_nuevo_paso(
            trabajo_log_id=job.id,
            trabajador_id=seed_tracking_data['worker_id'],
            paso_nombre="Corte",
            tipo_paso="manual",
            maquina_id=seed_tracking_data['maquina_id']
        )
        assert step is not None
        assert step.estado_paso == "en_proceso"
        assert step.paso_nombre == "Corte"
        
        # 2. Check Active Step
        active = tracking_repo_test.get_paso_activo_por_trabajador(seed_tracking_data['worker_id'])
        assert active is not None
        assert active.id == step.id
        
        # 3. Finalize Step
        finalized = tracking_repo_test.finalizar_paso(step.id)
        assert finalized is not None
        assert finalized.estado_paso == "completado"
        assert finalized.tiempo_fin_paso is not None
        
        # 4. Verify no active step
        active_after = tracking_repo_test.get_paso_activo_por_trabajador(seed_tracking_data['worker_id'])
        assert active_after is None
        
        # 5. Get Last Step
        last = tracking_repo_test.get_ultimo_paso_para_qr(job.id)
        assert last is not None
        assert last.id == step.id

    # --- Incidencias ---

    def test_registrar_incidencia(self, tracking_repo_test, seed_tracking_data, tmp_path, session_no_close):
        """Test registering incidence with attachments."""
        job = tracking_repo_test.iniciar_trabajo("QR-INC-001", seed_tracking_data['worker_id'], seed_tracking_data['fab_id'], seed_tracking_data['product_code'])
        
        # Create dummy file
        dummy_file = tmp_path / "foto.jpg"
        dummy_file.write_text("fake image content")
        
        inc = tracking_repo_test.registrar_incidencia(
            trabajo_log_id=job.id,
            trabajador_id=seed_tracking_data['worker_id'],
            tipo_incidencia="Defecto",
            descripcion="Roto",
            rutas_fotos=[str(dummy_file)]
        )
        
        # Verify DTO
        assert inc is not None
        assert inc.tipo_incidencia == "Defecto"
        
        # Check DB directly to confirm insertion
        session = session_no_close
        adjuntos_db = session.query(IncidenciaLog).filter_by(id=inc.id).first().adjuntos
        assert len(adjuntos_db) == 1
        assert adjuntos_db[0].nombre_archivo == "foto.jpg"
        
        # Check DTO list (This failed before, let's see if plain DB check passes, implying DTO mapping issue if this fails)
        assert len(inc.adjuntos) == 1
        assert str(dummy_file) in inc.adjuntos[0].ruta_archivo

    def test_registrar_incidencia_error(self, tracking_repo_test, seed_tracking_data):
        """Test incidence registration error with mock."""
        from sqlalchemy.exc import SQLAlchemyError
        
        session = tracking_repo_test.session_factory()
        original_commit = session.commit
        session.commit = MagicMock(side_effect=SQLAlchemyError("Mock DB Error"))
        
        inc = tracking_repo_test.registrar_incidencia(
            trabajo_log_id=1, # Valid ID (doesn't matter due to mock)
            trabajador_id=seed_tracking_data['worker_id'],
            tipo_incidencia="Error",
            descripcion="Desc"
        )
        
        session.commit = original_commit
        assert inc is None

    def test_anadir_foto_y_resolver(self, tracking_repo_test, seed_tracking_data, tmp_path):
        """Test adding photo later and resolving incidence."""
        job = tracking_repo_test.iniciar_trabajo("QR-RES-001", seed_tracking_data['worker_id'], seed_tracking_data['fab_id'], seed_tracking_data['product_code'])
        
        # 1. Register without photo
        inc = tracking_repo_test.registrar_incidencia(job.id, seed_tracking_data['worker_id'], "Tipo", "Desc")
        assert len(inc.adjuntos) == 0
        
        # 2. Add photo
        dummy_file = tmp_path / "extra.jpg"
        dummy_file.write_text("content")
        
        adj = tracking_repo_test.añadir_foto_a_incidencia(inc.id, str(dummy_file), "Extra")
        assert adj is not None
        # DTO has ruta_archivo, not nombre_archivo
        assert str(dummy_file) in adj.ruta_archivo 
        assert adj.tipo_archivo == "image/jpeg" # Default mapped if extension is jpg
        
        # 3. Resolve
        res = tracking_repo_test.resolver_incidencia(inc.id, "Fixed")
        assert res is not None
        assert res.estado == "resuelta"
        assert res.fecha_resolucion is not None

    def test_resolver_incidencia_not_found(self, tracking_repo_test):
        res = tracking_repo_test.resolver_incidencia(99999, "Sol")
        assert res is None

    def test_obtener_incidencias_abiertas(self, tracking_repo_test, seed_tracking_data):
        """Test fetching open incidents."""
        # 1. Create Open
        job = tracking_repo_test.iniciar_trabajo("QR-OPEN-001", seed_tracking_data['worker_id'], seed_tracking_data['fab_id'], seed_tracking_data['product_code'])
        tracking_repo_test.registrar_incidencia(job.id, seed_tracking_data['worker_id'], "Open", "Desc")
        
        # 2. Create and Resolve
        job2 = tracking_repo_test.iniciar_trabajo("QR-CLOSED-001", seed_tracking_data['worker_id'], seed_tracking_data['fab_id'], seed_tracking_data['product_code'])
        inc2 = tracking_repo_test.registrar_incidencia(job2.id, seed_tracking_data['worker_id'], "Closed", "Desc")
        tracking_repo_test.resolver_incidencia(inc2.id, "Done")
        
        # 3. Fetch Open
        open_incs = tracking_repo_test.obtener_incidencias_abiertas()
        assert len(open_incs) >= 1
        states = {i.estado for i in open_incs}
        assert "resuelta" not in states
        assert "abierta" in states
        
        # 4. Filter by Fabrication
        by_fab = tracking_repo_test.obtener_incidencias_abiertas(fabricacion_id=seed_tracking_data['fab_id'])
        assert len(by_fab) >= 1

    # --- Lists & Assignments ---

    def test_obtener_trabajos_activos_filters(self, tracking_repo_test, seed_tracking_data):
        """Test active jobs filtering."""
        # Clear previous
        # Create Job 1 (User 1, Fab 1)
        tracking_repo_test.iniciar_trabajo("QR-ACT-001", seed_tracking_data['worker_id'], seed_tracking_data['fab_id'], seed_tracking_data['product_code'])
        
        # Assume another user/fab exists or just filter by existing
        
        all_active = tracking_repo_test.obtener_trabajos_activos()
        assert len(all_active) >= 1
        
        by_worker = tracking_repo_test.obtener_trabajos_activos(trabajador_id=seed_tracking_data['worker_id'])
        assert len(by_worker) >= 1
        
        by_fab = tracking_repo_test.obtener_trabajos_activos(fabricacion_id=seed_tracking_data['fab_id'])
        assert len(by_fab) >= 1
        
        by_none = tracking_repo_test.obtener_trabajos_activos(trabajador_id=99999)
        assert len(by_none) == 0

    def test_get_fabricaciones_por_trabajador(self, tracking_repo_test, seed_tracking_data, session_no_close):
        """Test fetching assigned assignments including complex joins."""
        session = session_no_close
        
        # 1. Assign worker to fabrication manually via link table
        stmt = insert(trabajador_fabricacion_link).values(
            trabajador_id=seed_tracking_data['worker_id'], 
            fabricacion_id=seed_tracking_data['fab_id'],
            estado='activo',
            fecha_asignacion=datetime.now(timezone.utc)
        )
        session.execute(stmt)
        
        # 2. Add product link to fabrication
        stmt2 = insert(fabricacion_productos).values(
            fabricacion_id=seed_tracking_data['fab_id'],
            producto_codigo=seed_tracking_data['product_code'],
            cantidad=5
        )
        session.execute(stmt2)
        session.commit()
        
        # 3. Test Repository Method
        dtos = tracking_repo_test.get_fabricaciones_por_trabajador(seed_tracking_data['worker_id'])
        
        assert len(dtos) == 1
        fab = dtos[0]
        assert fab.id == seed_tracking_data['fab_id']
        assert fab.estado == 'activo'
        assert len(fab.productos) == 1
        assert fab.productos[0]['codigo'] == seed_tracking_data['product_code']
        assert fab.productos[0]['cantidad'] == 5

    def test_actualizar_estado_asignacion(self, tracking_repo_test, seed_tracking_data, session_no_close):
        """Test updating assignment state."""
        session = session_no_close
        # Setup assignment
        stmt = insert(trabajador_fabricacion_link).values(
            trabajador_id=seed_tracking_data['worker_id'], 
            fabricacion_id=seed_tracking_data['fab_id'],
            estado='activo'
        )
        session.execute(stmt)
        session.commit()
        
        # Update
        success = tracking_repo_test.actualizar_estado_asignacion(
            seed_tracking_data['worker_id'],
            seed_tracking_data['fab_id'],
            "completado"
        )
        assert success is True
        
        # Verify not found case
        fail = tracking_repo_test.actualizar_estado_asignacion(999, 999, "completado")
        assert fail is False


@pytest.mark.unit  
class TestTrackingRepositoryAssignments:
    """Tests for trabajador-fabricacion assignment methods."""

    def test_asignar_trabajador_a_fabricacion_success(self, tracking_repo_test, seed_tracking_data):
        """Assign worker to fabrication successfully."""
        success = tracking_repo_test.asignar_trabajador_a_fabricacion(
            seed_tracking_data['worker_id'],
            seed_tracking_data['fab_id']
        )
        assert success is True

    def test_asignar_trabajador_already_assigned(self, tracking_repo_test, seed_tracking_data, session_no_close):
        """Re-assign returns True (idempotent)."""
        # First assign
        tracking_repo_test.asignar_trabajador_a_fabricacion(
            seed_tracking_data['worker_id'],
            seed_tracking_data['fab_id']
        )
        # Re-assign
        success = tracking_repo_test.asignar_trabajador_a_fabricacion(
            seed_tracking_data['worker_id'],
            seed_tracking_data['fab_id']
        )
        assert success is True

    def test_asignar_trabajador_not_found(self, tracking_repo_test, seed_tracking_data):
        """Assign with invalid IDs returns False."""
        success = tracking_repo_test.asignar_trabajador_a_fabricacion(
            99999,  # invalid worker
            seed_tracking_data['fab_id']
        )
        assert success is False

        success2 = tracking_repo_test.asignar_trabajador_a_fabricacion(
            seed_tracking_data['worker_id'],
            99999  # invalid fabrication
        )
        assert success2 is False

    def test_desasignar_trabajador_success(self, tracking_repo_test, seed_tracking_data):
        """Desasignar worker from fabrication."""
        # First assign
        tracking_repo_test.asignar_trabajador_a_fabricacion(
            seed_tracking_data['worker_id'],
            seed_tracking_data['fab_id']
        )
        # Then desasignar
        success = tracking_repo_test.desasignar_trabajador_de_fabricacion(
            seed_tracking_data['worker_id'],
            seed_tracking_data['fab_id']
        )
        assert success is True

    def test_desasignar_trabajador_not_assigned(self, tracking_repo_test, seed_tracking_data):
        """Desasignar when not assigned returns False."""
        success = tracking_repo_test.desasignar_trabajador_de_fabricacion(
            seed_tracking_data['worker_id'],
            seed_tracking_data['fab_id']
        )
        assert success is False

    def test_desasignar_trabajador_not_found(self, tracking_repo_test):
        """Desasignar with invalid IDs returns False."""
        success = tracking_repo_test.desasignar_trabajador_de_fabricacion(99999, 99999)
        assert success is False

    def test_obtener_trabajadores_de_fabricacion(self, tracking_repo_test, seed_tracking_data):
        """Get workers assigned to fabrication."""
        # Assign first
        tracking_repo_test.asignar_trabajador_a_fabricacion(
            seed_tracking_data['worker_id'],
            seed_tracking_data['fab_id']
        )
        
        workers = tracking_repo_test.obtener_trabajadores_de_fabricacion(seed_tracking_data['fab_id'])
        
        assert len(workers) >= 1
        assert any(w.id == seed_tracking_data['worker_id'] for w in workers)

    def test_obtener_trabajadores_de_fabricacion_empty(self, tracking_repo_test, seed_tracking_data):
        """Fabrication with no workers returns empty list."""
        workers = tracking_repo_test.obtener_trabajadores_de_fabricacion(seed_tracking_data['fab_id'])
        assert workers == []

    def test_obtener_trabajadores_fabricacion_not_found(self, tracking_repo_test):
        """Non-existent fabrication returns empty list."""
        workers = tracking_repo_test.obtener_trabajadores_de_fabricacion(99999)
        assert workers == []


@pytest.mark.unit
class TestTrackingRepositoryOrdenesExport:
    """Tests for ordenes fabricacion and export methods."""

    def test_get_all_ordenes_fabricacion_empty(self, tracking_repo_test):
        """No ordenes returns empty list."""
        result = tracking_repo_test.get_all_ordenes_fabricacion()
        assert result == []

    def test_get_all_ordenes_fabricacion_with_data(self, tracking_repo_test, seed_tracking_data):
        """Get unique ordenes from trabajo logs."""
        # Create trabajo logs with orden_fabricacion
        job1 = tracking_repo_test.obtener_o_crear_trabajo_log_por_qr(
            qr_code="QR-OF-001",
            trabajador_id=seed_tracking_data['worker_id'],
            fabricacion_id=seed_tracking_data['fab_id'],
            producto_codigo=seed_tracking_data['product_code'],
            orden_fabricacion="OF-2024-001"
        )
        job2 = tracking_repo_test.obtener_o_crear_trabajo_log_por_qr(
            qr_code="QR-OF-002",
            trabajador_id=seed_tracking_data['worker_id'],
            fabricacion_id=seed_tracking_data['fab_id'],
            producto_codigo=seed_tracking_data['product_code'],
            orden_fabricacion="OF-2024-002"
        )
        # Duplicate orden
        job3 = tracking_repo_test.obtener_o_crear_trabajo_log_por_qr(
            qr_code="QR-OF-003",
            trabajador_id=seed_tracking_data['worker_id'],
            fabricacion_id=seed_tracking_data['fab_id'],
            producto_codigo=seed_tracking_data['product_code'],
            orden_fabricacion="OF-2024-001"  # same as job1
        )
        
        ordenes = tracking_repo_test.get_all_ordenes_fabricacion()
        
        # Should have 2 unique ordenes
        assert len(ordenes) == 2
        assert "OF-2024-001" in ordenes
        assert "OF-2024-002" in ordenes

    def test_get_all_ordenes_excludes_null(self, tracking_repo_test, seed_tracking_data):
        """Exclude NULL and empty orden_fabricacion."""
        # Create job without orden
        tracking_repo_test.iniciar_trabajo(
            qr_code="QR-NO-OF",
            trabajador_id=seed_tracking_data['worker_id'],
            fabricacion_id=seed_tracking_data['fab_id'],
            producto_codigo=seed_tracking_data['product_code']
        )
        
        ordenes = tracking_repo_test.get_all_ordenes_fabricacion()
        # Should not contain None
        assert None not in ordenes

    def test_pausar_trabajo_not_found(self, tracking_repo_test):
        """Pause non-existent work returns False."""
        success = tracking_repo_test.pausar_trabajo("NON-EXISTENT-QR", "Test")
        assert success is False

    def test_reanudar_trabajo_not_found(self, tracking_repo_test):
        """Resume non-existent work returns False."""
        success = tracking_repo_test.reanudar_trabajo("NON-EXISTENT-QR")
        assert success is False

    def test_finalizar_paso_not_found(self, tracking_repo_test):
        """Finalize non-existent step returns None."""
        result = tracking_repo_test.finalizar_paso(99999)
        assert result is None

    def test_obtener_trabajo_por_qr_not_found(self, tracking_repo_test):
        """Get non-existent QR returns None."""
        result = tracking_repo_test.obtener_trabajo_por_qr("NON-EXISTENT")
        assert result is None

    def test_obtener_trabajo_por_id_not_found(self, tracking_repo_test):
        """Get non-existent ID returns None."""
        result = tracking_repo_test.obtener_trabajo_por_id(99999)
        assert result is None

    def test_get_paso_activo_none(self, tracking_repo_test, seed_tracking_data):
        """No active paso returns None."""
        result = tracking_repo_test.get_paso_activo_por_trabajador(seed_tracking_data['worker_id'])
        assert result is None

    def test_get_ultimo_paso_para_qr_none(self, tracking_repo_test, seed_tracking_data):
        """No pasos for trabajo returns None."""
        job = tracking_repo_test.iniciar_trabajo(
            "QR-NO-STEPS",
            seed_tracking_data['worker_id'],
            seed_tracking_data['fab_id'],
            seed_tracking_data['product_code']
        )
        result = tracking_repo_test.get_ultimo_paso_para_qr(job.id)
        assert result is None

    def test_añadir_foto_incidencia_not_found(self, tracking_repo_test, tmp_path):
        """Add photo to non-existent incidencia returns None."""
        dummy_file = tmp_path / "test.jpg"
        dummy_file.write_text("content")
        
        result = tracking_repo_test.añadir_foto_a_incidencia(99999, str(dummy_file))
        assert result is None
