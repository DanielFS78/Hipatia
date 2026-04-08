# -*- coding: utf-8 -*-
"""Tests unitarios para SyncService: comparación y merge de bases de datos."""

import os
import pytest
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.unit

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Producto, Trabajador, Maquina


class TestSyncService:
    """Test suite for SyncService database comparison and merge operations."""

    @pytest.fixture
    def local_db(self, tmp_path):
        """Create a local SQLite database with test data."""
        db_path = tmp_path / "local.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Add some test data (include ALL required fields)
        session.add(Producto(
            codigo="PROD-001", 
            descripcion="Local Product 1",
            departamento="produccion",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        ))
        session.add(Producto(
            codigo="PROD-002", 
            descripcion="Local Product 2",
            departamento="produccion",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        ))
        session.add(Trabajador(nombre_completo="Local Worker 1", activo=True, tipo_trabajador=1))
        session.commit()
        session.close()
        
        yield str(db_path), engine, Session
        engine.dispose()

    @pytest.fixture
    def foreign_db(self, tmp_path):
        """Create a foreign SQLite database with overlapping and new data."""
        db_path = tmp_path / "foreign.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Add overlapping and new data (include ALL required fields)
        session.add(Producto(
            codigo="PROD-001", 
            descripcion="Modified Product 1",
            departamento="produccion",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        ))  # Updated
        session.add(Producto(
            codigo="PROD-003", 
            descripcion="Foreign Product 3",
            departamento="produccion",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        ))  # New
        session.add(Trabajador(nombre_completo="Foreign Worker 2", activo=True, tipo_trabajador=1))  # New
        session.commit()
        session.close()
        
        yield str(db_path), engine
        engine.dispose()

    def test_compare_databases_finds_new_records(self, local_db, foreign_db):
        """Test that compare_databases identifies new records in foreign DB."""
        local_path, _, local_session_factory = local_db
        foreign_path, _ = foreign_db
        
        from core.sync_service import SyncService
        sync_service = SyncService(local_session_factory)
        
        comparison = sync_service.compare_databases(foreign_path)
        
        # Should find differences in productos
        table_diff = next((t for t in comparison.tables if t.table_name == 'productos'), None)
        assert table_diff is not None
        
        # Check for new product (PROD-003)
        productos_new = [d for d in table_diff.differences if d.action == 'new']
        assert any(p.data.fields['codigo'] == 'PROD-003' for p in productos_new)

    def test_compare_databases_finds_updated_records(self, local_db, foreign_db):
        """Test that compare_databases identifies updated records."""
        local_path, _, local_session_factory = local_db
        foreign_path, _ = foreign_db
        
        from core.sync_service import SyncService
        sync_service = SyncService(local_session_factory)
        
        comparison = sync_service.compare_databases(foreign_path)
        
        # Should find updated PROD-001
        table_diff = next((t for t in comparison.tables if t.table_name == 'productos'), None)
        assert table_diff is not None
        
        productos_updated = [d for d in table_diff.differences if d.action == 'updated']
        updated_codes = [p.data.fields['codigo'] for p in productos_updated]
        assert 'PROD-001' in updated_codes

    def test_compare_databases_empty_when_identical(self, local_db):
        """Test that compare_databases returns empty when DBs are identical."""
        local_path, _, local_session_factory = local_db
        
        from core.sync_service import SyncService
        sync_service = SyncService(local_session_factory)
        
        # Compare with itself
        comparison = sync_service.compare_databases(local_path)
        
        # Should find no tables with differences
        assert len(comparison.tables) == 0

    def test_apply_changes_inserts_new_records(self, local_db, foreign_db):
        """Test that apply_changes correctly inserts new records."""
        local_path, local_engine, local_session_factory = local_db
        foreign_path, _ = foreign_db
        
        from core.sync_service import SyncService
        from core.dtos import DatabaseComparisonDTO, SyncTableDifferencesDTO
        sync_service = SyncService(local_session_factory)
        
        # Get differences
        comparison = sync_service.compare_databases(foreign_path)
        
        # Filter only new products
        table_diff = next((t for t in comparison.tables if t.table_name == 'productos'), None)
        if table_diff:
            new_products = [d for d in table_diff.differences if d.action == 'new']
            
            if new_products:
                selected_comparison = DatabaseComparisonDTO(tables=[
                    SyncTableDifferencesDTO(table_name='productos', differences=new_products)
                ])
                count = sync_service.apply_changes(selected_comparison)
                
                assert count > 0
                
                # Verify product exists in local DB
                session = local_session_factory()
                prod = session.query(Producto).filter_by(codigo='PROD-003').first()
                assert prod is not None
                assert prod.descripcion == "Foreign Product 3"
                session.close()

    def test_apply_changes_updates_existing_records(self, local_db, foreign_db):
        """Test that apply_changes correctly updates existing records."""
        local_path, local_engine, local_session_factory = local_db
        foreign_path, _ = foreign_db
        
        from core.sync_service import SyncService
        from core.dtos import DatabaseComparisonDTO, SyncTableDifferencesDTO
        sync_service = SyncService(local_session_factory)
        
        # Get differences
        comparison = sync_service.compare_databases(foreign_path)
        
        # Filter only updated products
        table_diff = next((t for t in comparison.tables if t.table_name == 'productos'), None)
        if table_diff:
            updated_products = [d for d in table_diff.differences if d.action == 'updated']
            
            if updated_products:
                selected_comparison = DatabaseComparisonDTO(tables=[
                    SyncTableDifferencesDTO(table_name='productos', differences=updated_products)
                ])
                count = sync_service.apply_changes(selected_comparison)
                
                assert count > 0
                
                # Verify product was updated in local DB
                session = local_session_factory()
                prod = session.query(Producto).filter_by(codigo='PROD-001').first()
                assert prod is not None
                assert prod.descripcion == "Modified Product 1"
                session.close()

    def test_service_public_api_is_invoked(self, local_db, foreign_db):
        """Smoke de interacción: SyncService se invoca vía su API pública."""
        local_path, _, local_session_factory = local_db
        foreign_path, _ = foreign_db
        from core.dtos import DatabaseComparisonDTO

        from core.sync_service import SyncService
        sync_service = SyncService(local_session_factory)

        with patch.object(sync_service, "compare_databases", wraps=sync_service.compare_databases) as spy_compare:
            comparison = sync_service.compare_databases(foreign_path)
            spy_compare.assert_called_once_with(foreign_path)
        assert isinstance(comparison, DatabaseComparisonDTO)

    def test_compare_applies_subfabricaciones_procesos_materiales_y_bom(self, tmp_path):
        """La copia extranjera con BOM completo debe aparecer en la comparación y aplicarse en local."""
        from database.models import Material, ProcesoMecanico, Subfabricacion

        local_path = tmp_path / "local_bom.db"
        foreign_path = tmp_path / "foreign_bom.db"

        def seed_db(path: object, *, with_children: bool) -> None:
            engine = create_engine(f"sqlite:///{path}")
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            session = Session()
            session.add(
                Producto(
                    codigo="BOM-1",
                    descripcion="Prod",
                    departamento="mec",
                    tipo_trabajador=1,
                    tiene_subfabricaciones=with_children,
                )
            )
            if with_children:
                mat = Material(codigo_componente="MAT-A", descripcion_componente="Pieza A")
                session.add(mat)
                session.flush()
                prod = session.query(Producto).filter_by(codigo="BOM-1").one()
                prod.materiales.append(mat)
                session.add(
                    Subfabricacion(
                        producto_codigo="BOM-1",
                        descripcion="Sub1",
                        tiempo=1.0,
                        tipo_trabajador=1,
                    )
                )
                session.add(
                    ProcesoMecanico(
                        producto_codigo="BOM-1",
                        nombre="Fresado",
                        descripcion="Operación",
                        tiempo=2.0,
                        tipo_trabajador=1,
                    )
                )
            session.commit()
            session.close()
            engine.dispose()

        seed_db(local_path, with_children=False)
        seed_db(foreign_path, with_children=True)

        local_engine = create_engine(f"sqlite:///{local_path}")
        local_session_factory = sessionmaker(bind=local_engine)

        from core.sync_service import SyncService

        sync_service = SyncService(local_session_factory)
        comparison = sync_service.compare_databases(str(foreign_path))
        names = {t.table_name for t in comparison.tables}
        assert "subfabricaciones" in names
        assert "procesos_mecanicos" in names
        assert "materiales" in names
        assert "producto_material_link" in names

        applied = sync_service.apply_changes(comparison)
        assert applied >= 4

        verify = local_session_factory()
        try:
            assert verify.query(Subfabricacion).filter_by(producto_codigo="BOM-1").count() == 1
            assert verify.query(ProcesoMecanico).filter_by(producto_codigo="BOM-1").count() == 1
            assert verify.query(Material).filter_by(codigo_componente="MAT-A").count() == 1
            prod = verify.query(Producto).filter_by(codigo="BOM-1").one()
            assert len(prod.materiales) == 1
            assert prod.materiales[0].codigo_componente == "MAT-A"
        finally:
            verify.close()
            local_engine.dispose()
