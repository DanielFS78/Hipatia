# tests/db/test_product_repository.py
"""
Tests para el ProductRepository.
"""

import pytest
from database.models import Producto, Subfabricacion, ProcesoMecanico  # Importamos los modelos
from core.dtos import ProductDTO, SubfabricacionDTO, ProcesoMecanicoDTO

# Marcamos toda la clase con "integration"
@pytest.mark.integration
class TestProductRepository:

    # --- Tests para get_all_products ---

    def test_get_all_products_empty(self, repos):
        """
        Prueba que get_all_products() devuelve una lista vacía
        cuando la base de datos no tiene productos.
        """
        # Obtenemos el repo de la fixture 'repos'
        product_repo = repos["product"]

        products = product_repo.get_all_products()

        assert products == []
        assert isinstance(products, list)

    def test_get_all_products_with_data(self, repos, session):
        """
        Prueba que get_all_products() devuelve todos los productos
        correctamente formateados como DTOs y ordenados por código.
        """
        # Obtenemos el repo de la fixture 'repos'
        product_repo = repos["product"]

        # 1. Arrange (Usamos la fixture 'session' raíz)
        p2 = Producto(
            codigo="PROD-B", descripcion="Producto B", departamento="Montaje",
            tipo_trabajador=1, tiene_subfabricaciones=False
        )
        p1 = Producto(
            codigo="PROD-A", descripcion="Producto A", departamento="Corte",
            tipo_trabajador=2, tiene_subfabricaciones=True
        )
        session.add_all([p2, p1])
        session.commit()

        # 2. Act
        products = product_repo.get_all_products()

        # 3. Assert
        assert len(products) == 2
        assert isinstance(products[0], ProductDTO)
        assert isinstance(products[1], ProductDTO)
        
        # Debe estar ordenado por código
        assert products[0].codigo == "PROD-A"
        assert products[0].descripcion == "Producto A"
        assert products[1].codigo == "PROD-B"
        assert products[1].descripcion == "Producto B"

    # --- Tests para search_products ---

    @pytest.fixture
    def setup_search_data(self, session):
        """
        Fixture de ayuda para poblar la base de datos con datos de prueba
        para los tests de búsqueda.
        """
        p1 = Producto(codigo="MOTOR-001", descripcion="Motor Eléctrico 500W", departamento="Montaje", tipo_trabajador=1,
                      tiene_subfabricaciones=False)
        p2 = Producto(codigo="CAJA-002", descripcion="Caja de Acero Inoxidable", departamento="Corte",
                      tipo_trabajador=2, tiene_subfabricaciones=True)
        p3 = Producto(codigo="PANEL-003", descripcion="Panel de control (motor)", departamento="Montaje",
                      tipo_trabajador=1, tiene_subfabricaciones=False)
        session.add_all([p1, p2, p3])
        session.commit()

    def test_search_products_no_query(self, repos, setup_search_data):
        """
        Prueba que search_products() sin consulta (None o "")
        devuelve todos los productos como DTOs.
        """
        product_repo = repos["product"]

        products_none = product_repo.search_products(None)
        products_empty = product_repo.search_products("")

        assert len(products_none) == 3
        assert len(products_empty) == 3
        assert products_none == products_empty
        assert isinstance(products_none[0], ProductDTO)

    def test_search_products_short_query(self, repos, setup_search_data):
        """
        Prueba que search_products() con una consulta demasiado corta (< 2 caracteres)
        devuelve una lista vacía.
        """
        product_repo = repos["product"]
        products = product_repo.search_products("M")
        assert products == []

    def test_search_products_by_code(self, repos, setup_search_data):
        """
        Prueba que la búsqueda por una parte del código funciona.
        """
        product_repo = repos["product"]

        # 1. Arrange
        query = "MOTOR"  # Esto debe encontrar "MOTOR-001" (código) y "...(motor)" (descripción)

        # 2. Act
        products = product_repo.search_products(query)

        # 3. Assert (SQLite 'LIKE' es case-insensitive por defecto)
        assert len(products) == 2
        assert isinstance(products[0], ProductDTO)
        assert products[0].codigo == "MOTOR-001"
        assert products[1].codigo == "PANEL-003"

    def test_search_products_by_description(self, repos, setup_search_data):
        """
        Prueba que la búsqueda por una parte de la descripción funciona.
        """
        product_repo = repos["product"]
        products = product_repo.search_products("motor")
        assert len(products) == 2
        assert products[0].codigo == "MOTOR-001"
        assert products[1].codigo == "PANEL-003"

    def test_search_products_no_match(self, repos, setup_search_data):
        """
        Prueba que la búsqueda de un término que no existe
        devuelve una lista vacía.
        """
        product_repo = repos["product"]
        products = product_repo.search_products("TORNILLO")
        assert products == []

    # --- Tests para get_latest_products ---

    @pytest.fixture
    def setup_latest_products_data(self, session):
        """
        Fixture de ayuda para poblar la base de datos con 12 productos
        con códigos predecibles (PROD-01 a PROD-12).
        """
        products = [
            Producto(
                codigo=f"PROD-{i:02d}", descripcion=f"Producto {i}",
                departamento="Test", tipo_trabajador=1, tiene_subfabricaciones=False
            ) for i in range(1, 13)
        ]
        session.add_all(products)
        session.commit()

    def test_get_latest_products_default_limit(self, repos, setup_latest_products_data):
        """
        Prueba que get_latest_products() usa el límite por defecto (10)
        y ordena por código descendente (o la lógica que tenga, orden de inserción/código).
        """
        product_repo = repos["product"]
        products = product_repo.get_latest_products()
        assert len(products) == 10
        assert isinstance(products[0], ProductDTO)
        # Asumiendo ordenación por código desc o similar si no hay created_at explícito
        assert products[0].codigo == "PROD-12"
        assert products[-1].codigo == "PROD-03"

    def test_get_latest_products_custom_limit(self, repos, setup_latest_products_data):
        """
        Prueba que get_latest_products() respeta un límite personalizado (5).
        """
        product_repo = repos["product"]
        products = product_repo.get_latest_products(limit=5)
        assert len(products) == 5
        assert isinstance(products[0], ProductDTO)
        assert products[0].codigo == "PROD-12"
        assert products[-1].codigo == "PROD-08"

    def test_get_latest_products_less_than_limit(self, repos, session):
        """
        Prueba que el método funciona si hay menos productos que el límite.
        """
        product_repo = repos["product"]
        p1 = Producto(codigo="A-01", descripcion="Prod A", departamento="Test", tipo_trabajador=1,
                      tiene_subfabricaciones=False)
        p2 = Producto(codigo="B-02", descripcion="Prod B", departamento="Test", tipo_trabajador=1,
                      tiene_subfabricaciones=False)
        p3 = Producto(codigo="C-03", descripcion="Prod C", departamento="Test", tipo_trabajador=1,
                      tiene_subfabricaciones=False)
        session.add_all([p1, p2, p3])
        session.commit()

        products = product_repo.get_latest_products(limit=10)
        assert len(products) == 3
        assert isinstance(products[0], ProductDTO)
        assert products[0].codigo == "C-03"

    def test_get_latest_products_empty(self, repos):
        """
        Prueba que devuelve una lista vacía si no hay productos.
        """
        product_repo = repos["product"]
        products = product_repo.get_latest_products()
        assert products == []

    # --- Tests para get_product_details ---

    def test_get_product_details_not_found(self, repos):
        """
        Prueba que get_product_details() devuelve (None, [], [])
        cuando el producto no existe.
        """
        product_repo = repos["product"]
        producto, subfabs, procesos = product_repo.get_product_details("NO-EXISTE")
        assert producto is None
        assert subfabs == []
        assert procesos == []

    def test_get_product_details_simple_product(self, repos, session):
        """
        Prueba los detalles de un producto simple, sin subfabricaciones
        ni procesos mecánicos.
        """
        product_repo = repos["product"]

        # 1. Arrange
        p1_data = {
            "codigo": "SIMPLE-001", "descripcion": "Producto Simple",
            "departamento": "Montaje", "tipo_trabajador": 1,
            "donde": "Almacén A", "tiene_subfabricaciones": False,
            "tiempo_optimo": 120.5
        }
        p1 = Producto(**p1_data)
        session.add(p1)
        session.commit()

        # 2. Act
        producto, subfabs, procesos = product_repo.get_product_details("SIMPLE-001")

        # 3. Assert
        assert producto is not None
        assert isinstance(producto, ProductDTO)
        assert producto.codigo == "SIMPLE-001"
        assert producto.descripcion == "Producto Simple"
        assert producto.tiempo_optimo == 120.5
        
        assert subfabs == []
        assert procesos == []

    def test_get_product_details_complex_product(self, repos, session):
        """
        Prueba los detalles de un producto complejo con subfabricaciones
        y procesos mecánicos.
        """
        product_repo = repos["product"]

        # 1. Arrange
        p = Producto(
            codigo="COMPLEX-001", descripcion="Producto Complejo",
            departamento="Mecanizado", tipo_trabajador=3,
            donde="Estantería B", tiene_subfabricaciones=True,
            tiempo_optimo=300.0
        )
        session.add(p)

        sub = Subfabricacion(
            producto_codigo="COMPLEX-001", descripcion="Montaje inicial",
            tiempo=50.0, tipo_trabajador=1, maquina_id=None
        )
        proc = ProcesoMecanico(
            producto_codigo="COMPLEX-001", nombre="Torneado",
            descripcion="Torneado de eje", tiempo=25.0, tipo_trabajador=3
        )
        session.add_all([sub, proc])
        session.commit()

        sub_id = sub.id
        proc_id = proc.id

        # 2. Act
        producto, subfabs, procesos = product_repo.get_product_details("COMPLEX-001")

        # 3. Assert
        assert isinstance(producto, ProductDTO)
        assert producto.codigo == "COMPLEX-001"

        assert len(subfabs) == 1
        assert isinstance(subfabs[0], SubfabricacionDTO)
        assert subfabs[0].id == sub_id
        assert subfabs[0].descripcion == "Montaje inicial"
        assert subfabs[0].tiempo == 50.0
        assert subfabs[0].tipo_trabajador == 1
        assert subfabs[0].maquina_id is None

        assert len(procesos) == 1
        assert isinstance(procesos[0], ProcesoMecanicoDTO)
        assert procesos[0].id == proc_id
        assert procesos[0].nombre == "Torneado"
        assert procesos[0].tiempo == 25.0
        assert procesos[0].tipo_trabajador == 3