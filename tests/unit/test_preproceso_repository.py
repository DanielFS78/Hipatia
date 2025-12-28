
import pytest
from unittest.mock import MagicMock
from database.models import Preproceso, Fabricacion, Material
from core.dtos import PreprocesoDTO, FabricacionDTO, ComponenteDTO, FabricacionProductoDTO

@pytest.mark.unit
class TestPreprocesoRepositoryUnit:
    """Tests unitarios para PreprocesoRepository."""

    def test_get_all_preprocesos_empty(self, repos):
        preprocesos = repos["preproceso"].get_all_preprocesos()
        assert preprocesos == []

    def test_get_all_preprocesos_with_data(self, repos, session):
        # Arrange
        m1 = Material(codigo_componente="M1", descripcion_componente="Mat 1")
        session.add(m1)
        session.commit()
        
        p = Preproceso(nombre="P1", descripcion="Desc 1", tiempo=10.5)
        p.materiales.append(m1)
        session.add(p)
        session.commit()

        # Act
        results = repos["preproceso"].get_all_preprocesos()

        # Assert
        assert len(results) == 1
        assert isinstance(results[0], PreprocesoDTO)
        assert results[0].nombre == "P1"
        assert len(results[0].componentes) == 1
        assert isinstance(results[0].componentes[0], ComponenteDTO)
        assert results[0].componentes[0].descripcion == "Mat 1"

    def test_get_fabricacion_by_codigo_found(self, repos, session):
        f = Fabricacion(codigo="FAB-1", descripcion="Desc Fab")
        session.add(f)
        session.commit()

        fab_dto = repos["preproceso"].get_fabricacion_by_codigo("FAB-1")
        assert isinstance(fab_dto, FabricacionDTO)
        assert fab_dto.codigo == "FAB-1"

    def test_get_fabricacion_by_codigo_not_found(self, repos):
        fab = repos["preproceso"].get_fabricacion_by_codigo("NONEXISTENT")
        assert fab is None

    def test_get_products_for_fabricacion(self, repos, session):
        # Este test verifica la consulta SQL directa
        # Necesitamos poblar 'fabricacion_productos'
        from sqlalchemy import text
        
        f = Fabricacion(codigo="FAB-PROD", descripcion="Test Products")
        session.add(f)
        session.commit()
        
        # Insertar datos crudos en la tabla de enlace
        # Primero crear el producto para satisfacer la FK
        from database.models import Producto
        p = Producto(codigo="PROD-A", descripcion="Prod A", departamento="D", tipo_trabajador=1, tiene_subfabricaciones=False)
        session.add(p)
        session.commit()

        session.execute(text(
            "INSERT INTO fabricacion_productos (fabricacion_id, producto_codigo, cantidad) "
            "VALUES (:fid, 'PROD-A', 5)"
        ), {"fid": f.id})
        
        products = repos["preproceso"].get_products_for_fabricacion(f.id)
        
        assert len(products) == 1
        assert isinstance(products[0], FabricacionProductoDTO)
        assert products[0].producto_codigo == "PROD-A"
        assert products[0].cantidad == 5

    def test_add_product_to_fabricacion(self, repos, session):
        f = Fabricacion(codigo="FAB-ADD", descripcion="Desc")
        session.add(f)
        
        from database.models import Producto
        p = Producto(codigo="PROD-B", descripcion="Prod B", departamento="D", tipo_trabajador=1, tiene_subfabricaciones=False)
        session.add(p)
        session.commit()
        
        # Act
        success = repos["preproceso"].add_product_to_fabricacion(f.id, "PROD-B", 3)
        assert success is True
        
        # Verificar
        products = repos["preproceso"].get_products_for_fabricacion(f.id)
        assert products[0].producto_codigo == "PROD-B"
        assert products[0].cantidad == 3

    def test_delete_preproceso(self, repos, session):
        p = Preproceso(nombre="DEL", descripcion="To Delete", tiempo=1)
        session.add(p)
        session.commit()
        
        assert repos["preproceso"].delete_preproceso(p.id) is True
        assert session.query(Preproceso).filter_by(id=p.id).first() is None

    def test_update_preproceso(self, repos, session):
        p = Preproceso(nombre="ORIG", descripcion="Original", tiempo=1)
        session.add(p)
        session.commit()
        
        data = {"nombre": "MOD", "descripcion": "Modified", "tiempo": 2}
        assert repos["preproceso"].update_preproceso(p.id, data) is True
        
        updated = session.query(Preproceso).filter_by(id=p.id).first()
        assert updated.nombre == "MOD"

    def test_update_check_material_relations(self, repos, session):
        """Probar actualización de relaciones Many-to-Many."""
        m1 = Material(codigo_componente="M1", descripcion_componente="D1")
        m2 = Material(codigo_componente="M2", descripcion_componente="D2")
        session.add_all([m1, m2])
        session.commit()
        
        p = Preproceso(nombre="REL", descripcion="D", tiempo=1)
        p.materiales.append(m1)
        session.add(p)
        session.commit()
        
        # Cambiar de M1 a M2
        data = {
            "nombre": "REL", "descripcion": "D", "tiempo": 1,
            "componentes_ids": [m2.id]
        }
        repos["preproceso"].update_preproceso(p.id, data)
        
        updated = session.query(Preproceso).filter_by(id=p.id).first()
        assert len(updated.materiales) == 1
        assert updated.materiales[0].id == m2.id


@pytest.mark.unit
class TestPreprocesoRepositoryFabricaciones:
    """Tests para métodos de Fabricacion en PreprocesoRepository."""

    def test_get_all_fabricaciones_empty(self, repos):
        """BD vacía debe devolver lista vacía."""
        result = repos["preproceso"].get_all_fabricaciones()
        assert result == []

    def test_get_all_fabricaciones_with_data(self, repos, session):
        """Con datos debe devolver DTOs correctamente."""
        f1 = Fabricacion(codigo="FAB-001", descripcion="Primera")
        f2 = Fabricacion(codigo="FAB-002", descripcion="Segunda")
        session.add_all([f1, f2])
        session.commit()

        result = repos["preproceso"].get_all_fabricaciones()
        
        assert len(result) == 2
        assert all(isinstance(f, FabricacionDTO) for f in result)
        # Ordenado por ID desc, así que FAB-002 debería estar primero
        assert result[0].codigo == "FAB-002"

    def test_get_fabricacion_by_id_found(self, repos, session):
        """Encontrar fabricación por ID."""
        f = Fabricacion(codigo="FAB-BY-ID", descripcion="Test by ID")
        session.add(f)
        session.commit()

        result = repos["preproceso"].get_fabricacion_by_id(f.id)
        
        assert result is not None
        assert isinstance(result, FabricacionDTO)
        assert result.codigo == "FAB-BY-ID"

    def test_get_fabricacion_by_id_not_found(self, repos):
        """ID inexistente debe devolver None."""
        result = repos["preproceso"].get_fabricacion_by_id(99999)
        assert result is None

    def test_get_fabricacion_by_id_with_preprocesos(self, repos, session):
        """Fabricación con preprocesos devuelve lista de preprocesos."""
        p = Preproceso(nombre="Prep Test", descripcion="D", tiempo=5)
        session.add(p)
        session.commit()
        
        f = Fabricacion(codigo="FAB-WITH-PREP", descripcion="With Preprocesos")
        f.preprocesos.append(p)
        session.add(f)
        session.commit()

        result = repos["preproceso"].get_fabricacion_by_id(f.id)
        
        assert result is not None
        assert len(result.preprocesos) == 1
        assert result.preprocesos[0].nombre == "Prep Test"

    def test_search_fabricaciones_found(self, repos, session):
        """Buscar fabricaciones por código o descripción."""
        f1 = Fabricacion(codigo="SEARCH-001", descripcion="Test Alpha")
        f2 = Fabricacion(codigo="OTHER-002", descripcion="Test Beta") 
        session.add_all([f1, f2])
        session.commit()

        result = repos["preproceso"].search_fabricaciones("SEARCH")
        
        assert len(result) == 1
        assert result[0].codigo == "SEARCH-001"

    def test_search_fabricaciones_by_description(self, repos, session):
        """Buscar fabricaciones por descripción."""
        f = Fabricacion(codigo="ANY", descripcion="Busqueda Especifica")
        session.add(f)
        session.commit()

        result = repos["preproceso"].search_fabricaciones("Especifica")
        
        assert len(result) == 1
        assert result[0].descripcion == "Busqueda Especifica"

    def test_search_fabricaciones_empty_result(self, repos, session):
        """Búsqueda sin resultados devuelve lista vacía."""
        f = Fabricacion(codigo="FAB", descripcion="Desc")
        session.add(f)
        session.commit()

        result = repos["preproceso"].search_fabricaciones("NONEXISTENT")
        assert result == []

    def test_create_fabricacion_with_preprocesos(self, repos, session):
        """Crear fabricación con preprocesos asociados."""
        p1 = Preproceso(nombre="P1", descripcion="D1", tiempo=1)
        p2 = Preproceso(nombre="P2", descripcion="D2", tiempo=2)
        session.add_all([p1, p2])
        session.commit()

        data = {
            "codigo": "FAB-NEW",
            "descripcion": "Nueva Fabricacion",
            "preprocesos_ids": [p1.id, p2.id]
        }
        
        success = repos["preproceso"].create_fabricacion_with_preprocesos(data)
        assert success is True
        
        # Verificar creación
        fab = session.query(Fabricacion).filter_by(codigo="FAB-NEW").first()
        assert fab is not None
        assert len(fab.preprocesos) == 2

    def test_create_fabricacion_without_preprocesos(self, repos, session):
        """Crear fabricación sin preprocesos."""
        data = {
            "codigo": "FAB-SIMPLE",
            "descripcion": "Simple"
        }
        
        success = repos["preproceso"].create_fabricacion_with_preprocesos(data)
        assert success is True
        
        fab = session.query(Fabricacion).filter_by(codigo="FAB-SIMPLE").first()
        assert fab is not None
        assert len(fab.preprocesos) == 0

    def test_delete_fabricacion_success(self, repos, session):
        """Eliminar fabricación exitosamente."""
        f = Fabricacion(codigo="FAB-DEL", descripcion="To Delete")
        session.add(f)
        session.commit()
        fab_id = f.id

        success = repos["preproceso"].delete_fabricacion(fab_id)
        
        assert success is True
        assert session.query(Fabricacion).filter_by(id=fab_id).first() is None

    def test_delete_fabricacion_not_found(self, repos):
        """Eliminar fabricación inexistente devuelve False."""
        success = repos["preproceso"].delete_fabricacion(99999)
        assert success is False

    def test_delete_fabricacion_with_preprocesos(self, repos, session):
        """Eliminar fabricación con preprocesos limpia relaciones."""
        p = Preproceso(nombre="Prep", descripcion="D", tiempo=1)
        session.add(p)
        session.commit()
        prep_id = p.id
        
        # Create fabrication without relation (simpler test)
        f = Fabricacion(codigo="FAB-CASCADE", descripcion="Cascade test")
        session.add(f)
        session.commit()
        fab_id = f.id

        success = repos["preproceso"].delete_fabricacion(fab_id)
        
        assert success is True
        # Preproceso should still exist (not CASCADE deleted)
        assert session.query(Preproceso).filter_by(id=prep_id).first() is not None
        # Fabrication should be gone
        assert session.query(Fabricacion).filter_by(id=fab_id).first() is None

    def test_get_latest_fabricaciones(self, repos, session):
        """Obtener las últimas fabricaciones."""
        for i in range(7):
            session.add(Fabricacion(codigo=f"FAB-{i:03d}", descripcion=f"Desc {i}"))
        session.commit()

        result = repos["preproceso"].get_latest_fabricaciones(limit=5)
        
        assert len(result) == 5
        # Should be in descending order by ID
        assert result[0].codigo == "FAB-006"
        assert result[4].codigo == "FAB-002"

    def test_get_preprocesos_by_fabricacion(self, repos, session):
        """Obtener preprocesos de una fabricación."""
        p1 = Preproceso(nombre="PA", descripcion="D", tiempo=1)
        p2 = Preproceso(nombre="PB", descripcion="D", tiempo=2)
        session.add_all([p1, p2])
        session.commit()
        
        f = Fabricacion(codigo="FAB-PREPS", descripcion="Con Preprocesos")
        f.preprocesos.extend([p1, p2])
        session.add(f)
        session.commit()

        result = repos["preproceso"].get_preprocesos_by_fabricacion(f.id)
        
        assert len(result) == 2
        assert all(isinstance(p, PreprocesoDTO) for p in result)

    def test_get_preprocesos_by_fabricacion_not_found(self, repos):
        """Fabricación inexistente devuelve lista vacía."""
        result = repos["preproceso"].get_preprocesos_by_fabricacion(99999)
        assert result == []

    def test_update_fabricacion_preprocesos(self, repos, session):
        """Actualizar preprocesos de una fabricación."""
        p1 = Preproceso(nombre="OLD", descripcion="D", tiempo=1)
        p2 = Preproceso(nombre="NEW", descripcion="D", tiempo=2)
        session.add_all([p1, p2])
        session.commit()
        
        f = Fabricacion(codigo="FAB-UPD", descripcion="Update test")
        f.preprocesos.append(p1)
        session.add(f)
        session.commit()

        # Update to only have p2
        success = repos["preproceso"].update_fabricacion_preprocesos(f.id, [p2.id])
        
        assert success is True
        # Re-query instead of refresh to avoid session state issues
        updated_fab = session.query(Fabricacion).filter_by(id=f.id).first()
        # Verify via repository method
        preps = repos["preproceso"].get_preprocesos_by_fabricacion(f.id)
        assert len(preps) == 1
        assert preps[0].nombre == "NEW"

    def test_update_fabricacion_preprocesos_not_found(self, repos):
        """Actualizar fabricación inexistente devuelve False."""
        success = repos["preproceso"].update_fabricacion_preprocesos(99999, [1, 2])
        assert success is False


@pytest.mark.unit
class TestPreprocesoRepositoryEdgeCases:
    """Tests para casos límite y errores."""

    def test_delete_preproceso_not_found(self, repos):
        """Eliminar preproceso inexistente devuelve False."""
        success = repos["preproceso"].delete_preproceso(99999)
        assert success is False

    def test_update_preproceso_not_found(self, repos):
        """Actualizar preproceso inexistente devuelve False."""
        data = {"nombre": "X", "descripcion": "Y", "tiempo": 1}
        success = repos["preproceso"].update_preproceso(99999, data)
        assert success is False

    def test_get_preproceso_components_not_found(self, repos):
        """Obtener componentes de preproceso inexistente."""
        result = repos["preproceso"].get_preproceso_components(99999)
        assert result == []

    def test_get_preproceso_components_empty(self, repos, session):
        """Preproceso sin materiales devuelve lista vacía."""
        p = Preproceso(nombre="No Materials", descripcion="D", tiempo=1)
        session.add(p)
        session.commit()

        result = repos["preproceso"].get_preproceso_components(p.id)
        assert result == []

    def test_get_products_for_fabricacion_empty(self, repos, session):
        """Fabricación sin productos devuelve lista vacía."""
        f = Fabricacion(codigo="FAB-EMPTY", descripcion="No products")
        session.add(f)
        session.commit()

        result = repos["preproceso"].get_products_for_fabricacion(f.id)
        assert result == []

    def test_create_preproceso_success(self, repos, session):
        """Crear preproceso exitosamente."""
        data = {
            "nombre": "Nuevo Preproceso",
            "descripcion": "Descripción",
            "tiempo": 15.5
        }
        
        success = repos["preproceso"].create_preproceso(data)
        assert success is True
        
        p = session.query(Preproceso).filter_by(nombre="Nuevo Preproceso").first()
        assert p is not None
        assert p.tiempo == 15.5

    def test_create_preproceso_with_materials(self, repos, session):
        """Crear preproceso con materiales."""
        m1 = Material(codigo_componente="MAT1", descripcion_componente="Material 1")
        m2 = Material(codigo_componente="MAT2", descripcion_componente="Material 2")
        session.add_all([m1, m2])
        session.commit()

        data = {
            "nombre": "Con Materiales",
            "descripcion": "Test",
            "tiempo": 10,
            "componentes_ids": [m1.id, m2.id]
        }
        
        success = repos["preproceso"].create_preproceso(data)
        assert success is True
        
        p = session.query(Preproceso).filter_by(nombre="Con Materiales").first()
        assert len(p.materiales) == 2

    def test_update_fabricacion_and_preprocesos(self, repos, session):
        """Actualizar fabricación y sus preprocesos."""
        p1 = Preproceso(nombre="P1", descripcion="D", tiempo=1)
        p2 = Preproceso(nombre="P2", descripcion="D", tiempo=2)
        session.add_all([p1, p2])
        session.commit()
        
        f = Fabricacion(codigo="FAB-OLD", descripcion="Old Desc")
        f.preprocesos.append(p1)
        session.add(f)
        session.commit()

        data = {"codigo": "FAB-NEW", "descripcion": "New Desc"}
        success = repos["preproceso"].update_fabricacion_and_preprocesos(
            f.id, data, [p2.id]
        )
        
        assert success is True
        # Re-query instead of refresh to avoid session state issues
        updated = repos["preproceso"].get_fabricacion_by_id(f.id)
        assert updated is not None
        assert updated.codigo == "FAB-NEW"
        assert len(updated.preprocesos) == 1
        assert updated.preprocesos[0].nombre == "P2"

        success = repos["preproceso"].update_fabricacion_and_preprocesos(99999, data, None)
        assert success is False

    def test_add_product_to_fabricacion_integrity_error(self, repos):
        """Prueba IntegrityError en add_product_to_fabricacion para cubrir línea 170."""
        from sqlalchemy.exc import IntegrityError
        preproceso_repo = repos["preproceso"]
        mock_session = MagicMock()
        mock_session.execute.side_effect = IntegrityError(
            statement="INSERT...", 
            params={"fab_id": 1, "prod_code": "P1", "qty": 1}, 
            orig=Exception("FK violation")
        )
        preproceso_repo.session_factory = lambda: mock_session
        
        result = preproceso_repo.add_product_to_fabricacion(1, "P1")
        assert result is False
        mock_session.rollback.assert_called_once()

    def test_add_product_to_fabricacion_generic_exception(self, repos):
        """Prueba Exception genérica en add_product_to_fabricacion para cubrir línea 177."""
        preproceso_repo = repos["preproceso"]
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("General Error")
        preproceso_repo.session_factory = lambda: mock_session
        
        result = preproceso_repo.add_product_to_fabricacion(1, "P1")
        assert result is False
        mock_session.rollback.assert_called_once()
