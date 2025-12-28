# tests/unit/test_product_repository.py
"""
Tests unitarios completos para ProductRepository.
Cubren todos los métodos CRUD y gestión de subfabricaciones/procesos mecánicos.
Actualizado para usar DTOs en lugar de tuplas.

Autor: Sistema de Tests
Fecha: 25/12/2025
"""

import pytest
from unittest.mock import MagicMock
from database.models import Producto, Subfabricacion, ProcesoMecanico, Material
from core.dtos import ProductDTO, SubfabricacionDTO, ProcesoMecanicoDTO, MaterialDTO


# ==============================================================================
# TESTS DE OBTENCIÓN (GET)
# ==============================================================================

@pytest.mark.unit
class TestProductRepositoryGetMethods:
    """Tests para métodos de obtención de productos."""

    # --- Tests para get_all_products ---

    def test_get_all_products_empty(self, repos):
        """
        Prueba que get_all_products() devuelve una lista vacía
        cuando la base de datos no tiene productos.
        """
        product_repo = repos["product"]
        products = product_repo.get_all_products()
        
        assert products == []
        assert isinstance(products, list)

    def test_get_all_products_with_data(self, repos, session):
        """
        Prueba que get_all_products() devuelve todos los productos
        correctamente formateados como DTOs y ordenados por código.
        """
        product_repo = repos["product"]
        
        # Arrange: Crear productos de prueba
        p1 = Producto(
            codigo="PROD-A",
            descripcion="Producto A",
            departamento="Corte",
            tipo_trabajador=2,
            tiene_subfabricaciones=True
        )
        p2 = Producto(
            codigo="PROD-B",
            descripcion="Producto B",
            departamento="Montaje",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        )
        session.add_all([p2, p1])
        session.commit()
        
        # Act
        products = product_repo.get_all_products()
        
        # Assert
        assert len(products) == 2
        assert isinstance(products[0], ProductDTO)
        # Verificar orden alfabético por código
        assert products[0].codigo == "PROD-A"
        assert products[1].codigo == "PROD-B"

    # --- Tests para search_products ---

    def test_search_products_no_query(self, repos, session):
        """
        Prueba que search_products() sin consulta devuelve todos los productos.
        """
        product_repo = repos["product"]
        
        # Arrange
        p1 = Producto(codigo="TEST-001", descripcion="Test 1", departamento="A", 
                      tipo_trabajador=1, tiene_subfabricaciones=False)
        session.add(p1)
        session.commit()
        
        # Act
        products_none = product_repo.search_products(None)
        products_empty = product_repo.search_products("")
        
        # Assert
        assert len(products_none) == 1
        assert products_none == products_empty

    def test_search_products_short_query(self, repos, session):
        """
        Prueba que search_products() con consulta muy corta devuelve lista vacía.
        """
        product_repo = repos["product"]
        
        # Arrange
        session.add(Producto(codigo="MOTOR-001", descripcion="Motor", departamento="A",
                             tipo_trabajador=1, tiene_subfabricaciones=False))
        session.commit()
        
        # Act
        products = product_repo.search_products("M")
        
        # Assert
        assert products == []

    def test_search_products_by_code_and_description(self, repos, session):
        """
        Prueba que search_products() busca en código y descripción.
        """
        product_repo = repos["product"]
        
        # Arrange
        p1 = Producto(codigo="MOTOR-001", descripcion="Motor Eléctrico", departamento="A",
                      tipo_trabajador=1, tiene_subfabricaciones=False)
        p2 = Producto(codigo="CAJA-002", descripcion="Caja de motor", departamento="A",
                      tipo_trabajador=1, tiene_subfabricaciones=False)
        p3 = Producto(codigo="PANEL-003", descripcion="Panel simple", departamento="A",
                      tipo_trabajador=1, tiene_subfabricaciones=False)
        session.add_all([p1, p2, p3])
        session.commit()
        
        # Act: Buscar "motor" (debe encontrar en código y descripción)
        products = product_repo.search_products("motor")
        
        # Assert
        assert len(products) == 2
        codigos = [p.codigo for p in products]
        assert "MOTOR-001" in codigos
        assert "CAJA-002" in codigos

    # --- Tests para get_latest_products ---

    def test_get_latest_products_empty(self, repos):
        """
        Prueba que get_latest_products() devuelve lista vacía sin datos.
        """
        product_repo = repos["product"]
        products = product_repo.get_latest_products()
        
        assert products == []

    def test_get_latest_products_respects_limit(self, repos, session):
        """
        Prueba que get_latest_products() respeta el límite especificado.
        """
        product_repo = repos["product"]
        
        # Arrange: Crear 15 productos
        for i in range(1, 16):
            session.add(Producto(
                codigo=f"PROD-{i:02d}",
                descripcion=f"Producto {i}",
                departamento="Test",
                tipo_trabajador=1,
                tiene_subfabricaciones=False
            ))
        session.commit()
        
        # Act
        products = product_repo.get_latest_products(limit=5)
        
        # Assert
        assert len(products) == 5
        assert isinstance(products[0], ProductDTO)

    # --- Tests para get_product_details ---

    def test_get_product_details_not_found(self, repos):
        """
        Prueba que get_product_details() devuelve (None, [], []) para código inexistente.
        """
        product_repo = repos["product"]
        
        producto, subfabs, procesos = product_repo.get_product_details("NO-EXISTE")
        
        assert producto is None
        assert subfabs == []
        assert procesos == []

    def test_get_product_details_simple_product(self, repos, session):
        """
        Prueba detalles de producto simple sin subfabricaciones.
        """
        product_repo = repos["product"]
        
        # Arrange
        p = Producto(
            codigo="SIMPLE-001",
            descripcion="Producto Simple",
            departamento="Montaje",
            tipo_trabajador=1,
            donde="Almacén A",
            tiene_subfabricaciones=False,
            tiempo_optimo=120.5
        )
        session.add(p)
        session.commit()
        
        # Act
        producto, subfabs, procesos = product_repo.get_product_details("SIMPLE-001")
        
        # Assert
        assert producto is not None
        assert isinstance(producto, ProductDTO)
        assert producto.codigo == "SIMPLE-001"
        assert producto.tiempo_optimo == 120.5
        assert subfabs == []
        assert procesos == []

    def test_get_product_details_with_subfabs_and_procesos(self, repos, session):
        """
        Prueba detalles de producto complejo con subfabricaciones y procesos.
        """
        product_repo = repos["product"]
        
        # Arrange
        p = Producto(
            codigo="COMPLEX-001",
            descripcion="Producto Complejo",
            departamento="Mecanizado",
            tipo_trabajador=3,
            tiene_subfabricaciones=True
        )
        session.add(p)
        session.flush()
        
        sub = Subfabricacion(
            producto_codigo="COMPLEX-001",
            descripcion="Montaje inicial",
            tiempo=50.0,
            tipo_trabajador=1,
            maquina_id=None
        )
        proc = ProcesoMecanico(
            producto_codigo="COMPLEX-001",
            nombre="Torneado",
            descripcion="Torneado de eje",
            tiempo=25.0,
            tipo_trabajador=3
        )
        session.add_all([sub, proc])
        session.commit()
        
        # Act
        producto, subfabs, procesos = product_repo.get_product_details("COMPLEX-001")
        
        # Assert
        assert isinstance(producto, ProductDTO)
        assert len(subfabs) == 1
        assert isinstance(subfabs[0], SubfabricacionDTO)
        assert subfabs[0].descripcion == "Montaje inicial"
        
        assert len(procesos) == 1
        assert isinstance(procesos[0], ProcesoMecanicoDTO)
        assert procesos[0].nombre == "Torneado"


# ==============================================================================
# TESTS DE CREACIÓN Y ACTUALIZACIÓN (ADD/UPDATE/DELETE)
# ==============================================================================

@pytest.mark.unit
class TestProductRepositoryCRUD:
    """Tests para operaciones CRUD de productos."""

    # --- Tests para add_product ---

    def test_add_product_success(self, repos):
        """
        Prueba que add_product() crea un nuevo producto correctamente.
        """
        product_repo = repos["product"]
        
        # Act
        data = {
            "codigo": "NEW-001",
            "descripcion": "Producto Nuevo",
            "departamento": "Montaje",
            "tipo_trabajador": 1,
            "donde": "Estante A",
            "tiene_subfabricaciones": False,
            "tiempo_optimo": 60.0
        }
        result = product_repo.add_product(data)
        
        # Assert
        assert result == True
        
        # Verificar que se creó
        products = product_repo.get_all_products()
        assert len(products) == 1
        assert products[0].codigo == "NEW-001"
        assert products[0].descripcion == "Producto Nuevo"

    def test_add_product_with_subfabricaciones(self, repos):
        """
        Prueba que add_product() crea subfabricaciones correctamente.
        """
        product_repo = repos["product"]
        
        # Act
        data = {
            "codigo": "SUB-001",
            "descripcion": "Con Subfabricaciones",
            "departamento": "Montaje",
            "tipo_trabajador": 2,
            "tiene_subfabricaciones": True,
            "tiempo_optimo": 0.0
        }
        subfabs = [
            {"descripcion": "Paso 1", "tiempo": 10.0, "tipo_trabajador": 1, "maquina_id": None},
            {"descripcion": "Paso 2", "tiempo": 20.0, "tipo_trabajador": 1, "maquina_id": None}
        ]
        result = product_repo.add_product(data, subfabs)
        
        # Assert
        assert result == True
        
        producto, subfabricaciones, _ = product_repo.get_product_details("SUB-001")
        assert len(subfabricaciones) == 2
        assert subfabricaciones[0].descripcion == "Paso 1"
        assert subfabricaciones[1].descripcion == "Paso 2"

    def test_add_product_with_procesos_mecanicos(self, repos):
        """
        Prueba que add_product() crea procesos mecánicos correctamente.
        """
        product_repo = repos["product"]
        
        # Act
        data = {
            "codigo": "PROC-001",
            "descripcion": "Con Procesos Mecánicos",
            "departamento": "Mecanizado",
            "tipo_trabajador": 3,
            "tiene_subfabricaciones": False,
            "tiempo_optimo": 0.0,
            "procesos_mecanicos": [
                {"nombre": "Fresado", "descripcion": "Fresado CNC", "tiempo": 30.0, "tipo_trabajador": 3},
                {"nombre": "Torneado", "descripcion": "Torneado", "tiempo": 25.0, "tipo_trabajador": 3}
            ]
        }
        result = product_repo.add_product(data)
        
        # Assert
        assert result == True
        
        producto, _, procesos = product_repo.get_product_details("PROC-001")
        assert len(procesos) == 2

    def test_add_product_invalid_maquina_id(self, repos):
        """
        Prueba que add_product() maneja maquina_id inválido gracefully.
        """
        product_repo = repos["product"]
        
        # Act: maquina_id con valor inválido
        data = {
            "codigo": "INVALID-001",
            "descripcion": "Test Inválido",
            "departamento": "Test",
            "tipo_trabajador": 1,
            "tiene_subfabricaciones": True
        }
        subfabs = [
            {"descripcion": "Paso con máquina inválida", "tiempo": 10.0, 
             "tipo_trabajador": 1, "maquina_id": "invalid_string"}
        ]
        result = product_repo.add_product(data, subfabs)
        
        # Assert: Debe manejar el error y convertir a None
        assert result == True
        
        _, subfabricaciones, _ = product_repo.get_product_details("INVALID-001")
        assert len(subfabricaciones) == 1
        assert subfabricaciones[0].maquina_id is None

    def test_add_product_duplicate(self, repos, session):
        """
        Prueba que add_product() devuelve False al intentar crear un duplicado.
        """
        product_repo = repos["product"]
        
        # Arrange: Crear producto inicial
        data = {
            "codigo": "DUP-001",
            "descripcion": "Original",
            "departamento": "Test",
            "tipo_trabajador": 1,
            "tiene_subfabricaciones": False
        }
        # Primer insert funciona
        assert product_repo.add_product(data) is True
        
        # Act: Intentar crear el mismo producto nuevamente
        result = product_repo.add_product(data)
        
        # Assert
        assert result is False
        
        # Verificar que sigue existiendo solo una instancia correcta
        p, _, _ = product_repo.get_product_details("DUP-001")
        assert p is not None
        assert p.descripcion == "Original"

    # --- Tests para update_product ---

    def test_update_product_success(self, repos, session):
        """
        Prueba que update_product() modifica los datos correctamente.
        """
        product_repo = repos["product"]
        
        # Arrange
        p = Producto(
            codigo="UPDATE-001",
            descripcion="Original",
            departamento="Montaje",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        )
        session.add(p)
        session.commit()
        
        # Act
        updated_data = {
            "codigo": "UPDATE-001",
            "descripcion": "Actualizado",
            "departamento": "Corte",
            "tipo_trabajador": 2,
            "tiene_subfabricaciones": False,
            "tiempo_optimo": 100.0
        }
        result = product_repo.update_product("UPDATE-001", updated_data)
        
        # Assert
        assert result == True
        producto, _, _ = product_repo.get_product_details("UPDATE-001")
        assert producto.descripcion == "Actualizado"
        assert producto.departamento == "Corte"
        assert producto.tipo_trabajador == 2

    def test_update_product_with_code_change(self, repos, session):
        """
        Prueba que update_product() puede cambiar el código del producto.
        """
        product_repo = repos["product"]
        
        # Arrange
        p = Producto(
            codigo="OLD-CODE",
            descripcion="Test",
            departamento="Test",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        )
        session.add(p)
        session.commit()
        
        # Act
        updated_data = {
            "codigo": "NEW-CODE",
            "descripcion": "Test",
            "departamento": "Test",
            "tipo_trabajador": 1,
            "tiene_subfabricaciones": False
        }
        result = product_repo.update_product("OLD-CODE", updated_data)
        
        # Assert
        assert result == True
        # Código antiguo no debe existir
        old_producto, _, _ = product_repo.get_product_details("OLD-CODE")
        assert old_producto is None
        # Código nuevo debe existir
        new_producto, _, _ = product_repo.get_product_details("NEW-CODE")
        assert new_producto is not None

    def test_update_product_not_found(self, repos):
        """
        Prueba que update_product() devuelve False para código inexistente.
        """
        product_repo = repos["product"]
        
        data = {
            "codigo": "NO-EXISTE",
            "descripcion": "Test",
            "departamento": "Test",
            "tipo_trabajador": 1,
            "tiene_subfabricaciones": False
        }
        result = product_repo.update_product("NO-EXISTE", data)
        
        assert result == False

    def test_update_product_replaces_subfabricaciones(self, repos):
        """
        Prueba que update_product() reemplaza las subfabricaciones existentes.
        """
        product_repo = repos["product"]
        
        # Arrange: Crear producto con subfabricaciones usando el repo
        data = {
            "codigo": "REPLACE-001",
            "descripcion": "Test",
            "departamento": "Test",
            "tipo_trabajador": 1,
            "tiene_subfabricaciones": True
        }
        old_subfabs = [
            {"descripcion": "Subfab Original", "tiempo": 10.0, "tipo_trabajador": 1}
        ]
        product_repo.add_product(data, old_subfabs)
        
        # Verificar estado inicial
        _, initial_subfabs, _ = product_repo.get_product_details("REPLACE-001")
        assert len(initial_subfabs) == 1
        assert initial_subfabs[0].descripcion == "Subfab Original"
        
        # Act: Actualizar con nuevas subfabricaciones
        updated_data = {
            "codigo": "REPLACE-001",
            "descripcion": "Test",
            "departamento": "Test",
            "tipo_trabajador": 1,
            "tiene_subfabricaciones": True
        }
        new_subfabs = [
            {"descripcion": "Nueva Subfab 1", "tiempo": 15.0, "tipo_trabajador": 2},
            {"descripcion": "Nueva Subfab 2", "tiempo": 20.0, "tipo_trabajador": 2}
        ]
        result = product_repo.update_product("REPLACE-001", updated_data, new_subfabs)
        
        # Assert
        assert result == True
        _, subfabs, _ = product_repo.get_product_details("REPLACE-001")
        assert len(subfabs) == 2
        descripciones = [s.descripcion for s in subfabs]
        assert "Nueva Subfab 1" in descripciones
        assert "Nueva Subfab 2" in descripciones
        assert "Subfab Original" not in descripciones

    # --- Tests para delete_product ---

    def test_delete_product_success(self, repos, session):
        """
        Prueba que delete_product() elimina el producto.
        """
        product_repo = repos["product"]
        
        # Arrange
        p = Producto(
            codigo="DELETE-001",
            descripcion="A Eliminar",
            departamento="Test",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        )
        session.add(p)
        session.commit()
        
        # Act
        result = product_repo.delete_product("DELETE-001")
        
        # Assert
        assert result == True
        products = product_repo.get_all_products()
        assert len(products) == 0

    def test_delete_product_not_found(self, repos):
        """
        Prueba que delete_product() devuelve False para código inexistente.
        """
        product_repo = repos["product"]
        
        result = product_repo.delete_product("NO-EXISTE")
        
        assert result == False


# ==============================================================================
# TESTS DE MATERIALES
# ==============================================================================

@pytest.mark.unit
class TestProductRepositoryMaterials:
    """Tests para gestión de materiales de productos."""

    def test_get_materials_for_product_empty(self, repos, session):
        """
        Prueba que get_materials_for_product() devuelve lista vacía sin materiales.
        """
        product_repo = repos["product"]
        
        # Arrange: Producto sin materiales
        p = Producto(
            codigo="NO-MATERIALS",
            descripcion="Sin Materiales",
            departamento="Test",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        )
        session.add(p)
        session.commit()
        
        # Act
        materials = product_repo.get_materials_for_product("NO-MATERIALS")
        
        # Assert
        assert materials == []

    def test_get_materials_for_product_not_found(self, repos):
        """
        Prueba que get_materials_for_product() devuelve lista vacía para producto inexistente.
        """
        product_repo = repos["product"]
        
        materials = product_repo.get_materials_for_product("NO-EXISTE")
        
        assert materials == []

    def test_get_materials_for_product_with_materials(self, repos, session):
        """
        Prueba que get_materials_for_product() devuelve materiales como DTOs.
        """
        product_repo = repos["product"]
        
        # Arrange: Producto con materiales (relación M-M)
        p = Producto(
            codigo="WITH-MATERIALS",
            descripcion="Con Materiales",
            departamento="Test",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        )
        session.add(p)
        session.flush()
        
        # Crear materiales y asociarlos al producto vía relación M-M
        m1 = Material(
            codigo_componente="COMP-001",
            descripcion_componente="Componente 1"
        )
        m2 = Material(
            codigo_componente="COMP-002",
            descripcion_componente="Componente 2"
        )
        session.add_all([m1, m2])
        session.flush()
        
        # Asociar materiales al producto mediante la relación
        p.materiales.append(m1)
        p.materiales.append(m2)
        session.commit()
        
        # Act
        materials = product_repo.get_materials_for_product("WITH-MATERIALS")
        
        # Assert
        assert len(materials) == 2
        assert isinstance(materials[0], MaterialDTO)
        codigos = [m.codigo_componente for m in materials]
        assert "COMP-001" in codigos
        assert "COMP-002" in codigos


# ==============================================================================
# TESTS DE EDGE CASES Y ROBUSTEZ
# ==============================================================================

@pytest.mark.unit
class TestProductRepositoryEdgeCases:
    """Tests para casos límite y situaciones especiales."""

    def test_search_products_special_characters(self, repos, session):
        """
        Prueba búsqueda con caracteres especiales.
        """
        product_repo = repos["product"]
        
        # Arrange
        p = Producto(
            codigo="SPECIAL-001",
            descripcion="Producto (especial) 100%",
            departamento="Test",
            tipo_trabajador=1,
            tiene_subfabricaciones=False
        )
        session.add(p)
        session.commit()
        
        # Act
        products = product_repo.search_products("100%")
        
        # Assert
        assert len(products) == 1
        assert products[0].codigo == "SPECIAL-001"

    def test_add_product_empty_opcional_fields(self, repos):
        """
        Prueba que add_product() funciona con campos opcionales vacíos.
        """
        product_repo = repos["product"]
        
        data = {
            "codigo": "MINIMAL-001",
            "descripcion": "Producto Mínimo",
            "departamento": "Test",
            "tipo_trabajador": 1,
            "tiene_subfabricaciones": False
            # donde y tiempo_optimo no especificados
        }
        result = product_repo.add_product(data)
        
        assert result == True
        producto, _, _ = product_repo.get_product_details("MINIMAL-001")
        assert producto.donde == ""
        assert producto.tiempo_optimo == 0.0

    def test_get_product_details_returns_correct_types(self, repos, session):
        """
        Prueba que los tipos de datos devueltos son correctos.
        """
        product_repo = repos["product"]
        
        # Arrange
        p = Producto(
            codigo="TYPES-001",
            descripcion="Test Tipos",
            departamento="Test",
            tipo_trabajador=2,
            donde="Ubicación",
            tiene_subfabricaciones=True,
            tiempo_optimo=99.5
        )
        session.add(p)
        session.commit()
        
        # Act
        producto, subfabs, procesos = product_repo.get_product_details("TYPES-001")
        
        # Assert tipos
        assert isinstance(producto.codigo, str)
        assert isinstance(producto.descripcion, str)
        assert isinstance(producto.departamento, str)
        assert isinstance(producto.tipo_trabajador, int)
        assert isinstance(producto.donde, str)
        assert isinstance(producto.tiene_subfabricaciones, bool)
        assert isinstance(producto.tiempo_optimo, float)
        assert isinstance(subfabs, list)
        assert isinstance(procesos, list)

    def test_get_product_details_exception(self, repos):
        """Prueba get_product_details cuando ocurre una excepción para cubrir línea 182."""
        product_repo = repos["product"]
        # Mock session to raise exception
        mock_session = MagicMock()
        mock_session.query.side_effect = Exception("Mock Error")
        product_repo.session_factory = lambda: mock_session
        
        prod, sub, proc = product_repo.get_product_details("ANY")
        assert prod is None
        assert sub == []
        assert proc == []

    def test_update_product_with_procesos_mecanicos(self, repos, session):
        """Prueba actualización incluyendo procesos mecánicos para cubrir bucles de guardado."""
        product_repo = repos["product"]
        # Arrange
        p_data = {
            "codigo": "P-PROC", 
            "descripcion": "D", 
            "departamento": "D", 
            "tipo_trabajador": 1, 
            "tiene_subfabricaciones": False
        }
        product_repo.add_product(p_data)
        
        # Act
        new_data = p_data.copy()
        new_data["procesos_mecanicos"] = [
            {"nombre": "Torno", "descripcion": "Mecanizado", "tiempo": 15.0, "tipo_trabajador": 2},
            {"nombre": "Fresado", "descripcion": "Acabado", "tiempo": 10.0, "tipo_trabajador": 2}
        ]
        result = product_repo.update_product("P-PROC", new_data)
        
        # Assert
        assert result == True
        _, _, procesos = product_repo.get_product_details("P-PROC")
        assert len(procesos) == 2
        assert procesos[0].nombre == "Torno"
        assert procesos[1].nombre == "Fresado"
