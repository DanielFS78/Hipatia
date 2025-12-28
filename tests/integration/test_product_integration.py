import pytest
from sqlalchemy import select, inspect
from database.models import Producto, Subfabricacion, ProcesoMecanico, Material

@pytest.mark.integration
class TestProductIntegration:
    """
    Tests de integración para ProductRepository.
    Verifica interacciones directas con la base de datos, cascadas y relaciones.
    """

    def test_create_product_with_subfabricaciones_persistence(self, repos, session):
        """
        Verifica que al crear un producto con subfabricaciones, estas se persisten
        correctamente en la base de datos y se pueden recuperar mediante consultas SQL directas.
        """
        product_repo = repos["product"]

        # Arrange
        prod_data = {
            "codigo": "INT-001",
            "descripcion": "Integration Test Product",
            "departamento": "Integration",
            "tipo_trabajador": 1,
            "tiene_subfabricaciones": True
        }
        subfabs = [
            {"descripcion": "Subfab Int 1", "tiempo": 10.0, "tipo_trabajador": 1, "maquina_id": None},
            {"descripcion": "Subfab Int 2", "tiempo": 20.0, "tipo_trabajador": 1, "maquina_id": None}
        ]

        # Act
        product_repo.add_product(prod_data, subfabs)

        # Assert (Direct SQL verification)
        # Verificar Producto
        stmt_prod = select(Producto).where(Producto.codigo == "INT-001")
        prod_db = session.execute(stmt_prod).scalar_one_or_none()
        assert prod_db is not None
        assert prod_db.descripcion == "Integration Test Product"

        # Verificar Subfabricaciones
        stmt_subs = select(Subfabricacion).where(Subfabricacion.producto_codigo == "INT-001")
        subs_db = session.execute(stmt_subs).scalars().all()
        assert len(subs_db) == 2
        descs = [s.descripcion for s in subs_db]
        assert "Subfab Int 1" in descs
        assert "Subfab Int 2" in descs

    def test_product_cascade_delete(self, repos, session):
        """
        Verifica que la eliminación de un producto elimina en cascada 
        sus subfabricaciones y procesos mecánicos.
        """
        product_repo = repos["product"]

        # Arrange: Crear producto con dependencias
        prod_data = {
            "codigo": "CASCADE-TEST",
            "descripcion": "To be deleted",
            "departamento": "Test",
            "tipo_trabajador": 1,
            "tiene_subfabricaciones": True,
            "procesos_mecanicos": [
                 {"nombre": "P1", "descripcion": "D1", "tiempo": 10, "tipo_trabajador": 1}
            ]
        }
        subfabs = [
            {"descripcion": "S1", "tiempo": 10.0, "tipo_trabajador": 1}
        ]
        
        product_repo.add_product(prod_data, subfabs)
        
        # Verificar existencia previa
        assert session.execute(select(Producto).filter_by(codigo="CASCADE-TEST")).scalar_one_or_none() is not None
        assert len(session.execute(select(Subfabricacion).filter_by(producto_codigo="CASCADE-TEST")).scalars().all()) == 1
        assert len(session.execute(select(ProcesoMecanico).filter_by(producto_codigo="CASCADE-TEST")).scalars().all()) == 1

        # Act
        product_repo.delete_product("CASCADE-TEST")
        
        # Assert: Todo debe haber desaparecido
        assert session.execute(select(Producto).filter_by(codigo="CASCADE-TEST")).scalar_one_or_none() is None
        assert len(session.execute(select(Subfabricacion).filter_by(producto_codigo="CASCADE-TEST")).scalars().all()) == 0
        assert len(session.execute(select(ProcesoMecanico).filter_by(producto_codigo="CASCADE-TEST")).scalars().all()) == 0

    def test_product_materials_relationship_persistence(self, repos, session):
        """
        Verifica la persistencia de la relación Many-to-Many entre Productos y Materiales.
        """
        product_repo = repos["product"]

        # Arrange
        # 1. Crear producto
        p = Producto(
            codigo="MAT-REL-TEST",
            descripcion="Product with Materials",
            departamento="Test",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        )
        session.add(p)
        
        # 2. Crear materiales
        m1 = Material(codigo_componente="M-001", descripcion_componente="Material 1")
        m2 = Material(codigo_componente="M-002", descripcion_componente="Material 2")
        session.add_all([m1, m2])
        session.flush()

        # 3. Relacionar
        p.materiales.append(m1)
        p.materiales.append(m2)
        session.commit()

        # Act & Assert
        # Verificar desde el repositorio
        materials_dto = product_repo.get_materials_for_product("MAT-REL-TEST")
        assert len(materials_dto) == 2
        
        # Verificar desde SQL directo en tabla intermedia si es posible, 
        # o verificando la carga inversa desde Material
        
        
        # Recargar material y ver productos
        # Nota: m1 está detached porque safe_execute cierra la sesión.
        # Consultamos de nuevo para verificar persistencia inversa.
        stmt_m = select(Material).where(Material.codigo_componente == "M-001")
        m1_db = session.execute(stmt_m).scalar_one()
        # Al acceder a la relación, SQLAlchemy debería cargarla lazy
        assert len(m1_db.productos) == 1
        assert m1_db.productos[0].codigo == "MAT-REL-TEST"
