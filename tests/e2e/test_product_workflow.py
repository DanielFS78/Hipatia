import pytest
from core.dtos import ProductDTO, SubfabricacionDTO, ProcesoMecanicoDTO

@pytest.mark.e2e
class TestProductWorkflow:
    """
    End-to-End tests simulating real Product management workflows.
    Verifies integration of ProductRepository with data models and correct DTO usage.
    """

    def test_full_product_lifecycle(self, repos, session):
        """
        Scenario: Production Manager creates a new product, updates it, and manages its lifecycle.
        
        1. Create new product with components (Manager action)
        2. Search/Verify product existence
        3. Initial Verification of Details
        4. Update product details and components
        5. Verify updates
        6. Delete product
        """
        product_repo = repos["product"]
        
        # 1. Create new product with components
        print("\nStep 1: Manager creates product 'Smartphone Mockup'")
        
        prod_data = {
            "codigo": "PHONE-001",
            "descripcion": "Smartphone Mockup Model X",
            "departamento": "Ensamblaje",
            "tipo_trabajador": 2,
            "donde": "Estante A1",
            "tiene_subfabricaciones": True,
            "tiempo_optimo": 0.0 # Calculado
        }
        
        sub_data = [
            {
                "descripcion": "Ensamblar carcasa",
                "tiempo": 15.0,
                "tipo_trabajador": 1,
                "maquina_id": None
            },
            {
                # Simulando un proceso mecánico también pasado como subfabricación
                # Nota: En la implementación actual, los procesos mecánicos se suelen añadir separados o via logica especifica
                # Pero add_product soporta sub_data para Subfabricacion table.
                "descripcion": "Pegar pantalla",
                "tiempo": 10.0,
                "tipo_trabajador": 2,
                "maquina_id": None
            }
        ]
        
        # Add product logic in repo might differ slightly, let's look at how app.py calls it or repo's add_product
        # Repo's add_product(self, data, sub_data=None)
        success = product_repo.add_product(prod_data, sub_data)
        assert success is True
        
        # 2. Search/Verify product existence
        print("Step 2: Searching for the product")
        search_results = product_repo.search_products("PHONE")
        assert len(search_results) == 1
        assert isinstance(search_results[0], ProductDTO)
        assert search_results[0].codigo == "PHONE-001"
        assert search_results[0].descripcion == "Smartphone Mockup Model X"
        
        # 3. Initial Verification of Details
        print("Step 3: Verifying details and components")
        product, subfabs, processes = product_repo.get_product_details("PHONE-001")
        
        assert isinstance(product, ProductDTO)
        assert product.codigo == "PHONE-001"
        assert product.tiene_subfabricaciones is True
        
        assert len(subfabs) == 2
        assert isinstance(subfabs[0], SubfabricacionDTO)
        
        # 4. Update product details
        print("Step 4: Updating product description and Department")
        
        # Update logic in current implementation usually requires re-sending data.
        # Check repo.update_product(codigo_original, data, subfabricaciones)
        
        updated_data = prod_data.copy()
        updated_data["descripcion"] = "Smartphone Mockup Model X - V2"
        updated_data["departamento"] = "Packaging"
        
        # Let's remove one subfab and add a new one
        updated_sub_data = [
            # Keep first one
            sub_data[0],
            # Add new one
            {
                "descripcion": "Empaquetado final",
                "tiempo": 5.0,
                "tipo_trabajador": 1,
                "maquina_id": None
            }
        ]
        
        success_update = product_repo.update_product("PHONE-001", updated_data, updated_sub_data)
        assert success_update is True
        
        # 5. Verify updates
        print("Step 5: Verifying updates")
        product_v2, subfabs_v2, processes_v2 = product_repo.get_product_details("PHONE-001")
        
        assert product_v2.descripcion == "Smartphone Mockup Model X - V2"
        assert product_v2.departamento == "Packaging"
        
        # Should have 2 subfabs (one kept, one new)
        assert len(subfabs_v2) == 2
        descriptions = [s.descripcion for s in subfabs_v2]
        assert "Ensamblar carcasa" in descriptions
        assert "Empaquetado final" in descriptions
        assert "Pegar pantalla" not in descriptions
        
        # 6. Delete product
        print("Step 6: Deleting product")
        success_delete = product_repo.delete_product("PHONE-001")
        assert success_delete is True
        
        # Verify deletion
        product_deleted, _, _ = product_repo.get_product_details("PHONE-001")
        assert product_deleted is None
