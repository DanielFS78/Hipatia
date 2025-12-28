import pytest
from database.repositories.iteration_repository import IterationRepository
from database.repositories.product_repository import ProductRepository
from database.models import Producto

class TestIterationWorkflow:
    
    @pytest.fixture
    def iteration_repo(self, session):
        return IterationRepository(session_factory=lambda: session)
        
    @pytest.fixture
    def product_repo(self, session):
        return ProductRepository(session_factory=lambda: session)

    def test_iteration_workflow(self, iteration_repo, product_repo, session):
        # 1. Setup: Create Product
        prod_code = "WORKFLOW_PROD"
        # Manually creating product as ProductRepository might expect DTOs or different args
        # Let's simple insert to be safe on dependency
        p = Producto(
            codigo=prod_code,
            descripcion="Workflow Product",
            departamento="Dept",
            tipo_trabajador="1",
            tiempo_optimo=10,
            tiene_subfabricaciones=False,
            donde="Test Location"
        )
        session.add(p)
        session.commit()
        
        # 2. Action: User adds iteration
        materials = [{'codigo': 'W_MAT_1', 'descripcion': 'Workflow Mat 1'}]
        new_id = iteration_repo.add_product_iteration(
            prod_code, "WorkflowUser", "Critical fix", "Bug", materials
        )
        assert new_id is not None
        
        # 3. Action: User views history (Dashboard/Historial)
        history = iteration_repo.get_all_iterations_with_dates()
        matches = [h for h in history if h.id == new_id]
        assert len(matches) == 1
        item = matches[0]
        assert item.producto_codigo == prod_code
        assert item.nombre_responsable == "WorkflowUser"
        
        # 4. Action: User views details for specific product
        details = iteration_repo.get_product_iterations(prod_code)
        assert len(details) == 1
        assert details[0].materiales[0].codigo == 'W_MAT_1'
        
        # 5. Action: User updates image path (e.g. via drag & drop)
        iteration_repo.update_iteration_image_path(new_id, "/tmp/new_image.png")
        
        # Verify update
        details_updated = iteration_repo.get_product_iterations(prod_code)
        assert details_updated[0].ruta_imagen == "/tmp/new_image.png"
