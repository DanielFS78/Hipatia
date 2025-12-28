import pytest
from datetime import datetime
from database.repositories.iteration_repository import IterationRepository
from database.models import Producto
from core.dtos import ProductIterationDTO

class TestIterationIntegration:
    
    @pytest.fixture
    def repository(self, session):
        return IterationRepository(session_factory=lambda: session)

    @pytest.fixture
    def sample_product(self, session):
        prod = Producto(
            codigo="PROD_INT_TEST",
            descripcion="Integration Test Product",
            departamento="Test",
            tipo_trabajador="1",
            tiempo_optimo=10.0,
            tiene_subfabricaciones=False,
            donde="Test Location"
        )
        session.add(prod)
        session.commit()
        return prod

    def test_full_lifecycle(self, repository, sample_product):
        # ... existing content ...
        # (Content omitted for brevity, but logically needs no change as repository is passed)
        # However, to use multi_replace effectively on a large block, I should target specific definitions if possible
        # or replace the fixtures block.
        pass # Placeholder for tool logic, actual replacement below handles just fixtures/defs if cleaner
        
    # Better strategy: Replace just the fixtures and method signatures


    def test_full_lifecycle(self, repository, sample_product):
        # 1. Add Iteration
        materials = [
            {'codigo': 'MAT_A', 'descripcion': 'Material A'},
            {'codigo': 'MAT_B', 'descripcion': 'Material B'}
        ]
        
        iter_id = repository.add_product_iteration(
            codigo_producto=sample_product.codigo,
            responsable="Tester",
            descripcion="Initial Version",
            tipo_fallo="New",
            materiales_list=materials
        )
        assert iter_id is not None
        
        # 2. Get Iteration
        iterations = repository.get_product_iterations(sample_product.codigo)
        assert len(iterations) == 1
        dto = iterations[0]
        assert isinstance(dto, ProductIterationDTO)
        assert dto.id == iter_id
        assert dto.descripcion == "Initial Version"
        assert len(dto.materiales) == 2
        
        # Verify materials
        mat_codes = sorted([m.codigo for m in dto.materiales])
        assert mat_codes == ['MAT_A', 'MAT_B']
        
        # 3. Update Iteration
        success = repository.update_product_iteration(
            iteracion_id=iter_id,
            responsable="Senior Tester",
            descripcion="Updated Version",
            tipo_fallo="Update"
        )
        assert success is True
        
        iterations_updated = repository.get_product_iterations(sample_product.codigo)
        assert iterations_updated[0].nombre_responsable == "Senior Tester"
        
        # 4. Delete Iteration
        success_del = repository.delete_product_iteration(iter_id)
        assert success_del is True
        
        iterations_final = repository.get_product_iterations(sample_product.codigo)
        assert len(iterations_final) == 0

    def test_material_reuse(self, repository, sample_product, session):
        # Add iteration 1 with MAT_X
        repository.add_product_iteration(
            sample_product.codigo, "User1", "Desc1", "Type1",
            [{'codigo': 'MAT_X', 'descripcion': 'Material X'}]
        )
        
        # Add iteration 2 with MAT_X (same code, same desc)
        repository.add_product_iteration(
            sample_product.codigo, "User2", "Desc2", "Type2",
            [{'codigo': 'MAT_X', 'descripcion': 'Material X'}]
        )
        
        # Verify only 1 Material with code MAT_X exists in DB
        from database.models import Material
        mats = session.query(Material).filter_by(codigo_componente='MAT_X').all()
        assert len(mats) == 1

    def test_get_all_iterations_with_dates(self, repository, sample_product):
        repository.add_product_iteration(
            sample_product.codigo, "User1", "Desc1", "Type1", []
        )
        
        all_iters = repository.get_all_iterations_with_dates()
        # Filter for our test product just in case DB is dirty
        our_iters = [it for it in all_iters if it.producto_codigo == sample_product.codigo]
        
        assert len(our_iters) == 1
        assert isinstance(our_iters[0], ProductIterationDTO)
        assert our_iters[0].producto_descripcion == "Integration Test Product"
