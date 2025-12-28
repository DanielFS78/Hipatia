import pytest

@pytest.mark.e2e
class TestPreprocesoWorkflow:
    """Tests End-to-End para el flujo de trabajo de Preprocesos y Fabricaciones."""

    def test_complete_fabricacion_workflow(self, repos, session):
        """
        Simula el flujo completo:
        1. Crear materiales
        2. Crear preprocesos usando esos materiales
        3. Crear fabricación usando esos preprocesos
        4. Añadir productos a la fabricación
        5. Verificar todo
        6. Eliminar todo
        """
        # 1. Crear Materiales (usando session directa dado que no tenemos repo de material completo aun)
        from database.models import Material
        m = Material(codigo_componente="E2E-MAT", descripcion_componente="Material E2E")
        session.add(m)
        session.commit()
        
        # 2. Crear Preproceso
        repo = repos["preproceso"]
        prep_data = {
            "nombre": "Preproceso E2E",
            "descripcion": "Descripción E2E",
            "tiempo": 50.0,
            "componentes_ids": [m.id]
        }
        assert repo.create_preproceso(prep_data) is True
        
        # Obtener ID del preproceso creado (necesario para el siguiente paso)
        # En una app real lo tendríamos del retorno o de una búsqueda
        preproceso = repo.get_all_preprocesos()[-1] # Asumimos que es el último
        assert preproceso.nombre == "Preproceso E2E"
        prep_id = preproceso.id
        
        # 3. Crear Fabricación
        fab_data = {
            "codigo": "FAB-E2E-001",
            "descripcion": "Fabricación End-to-End",
            "preprocesos_ids": [prep_id]
        }
        assert repo.create_fabricacion_with_preprocesos(fab_data) is True
        
        # 4. Añadir productos a la fabricación
        # Primero crear el producto para satisfacer la FK
        from database.models import Producto
        prod = Producto(
             codigo="PROD-FINAL-E2E", 
             descripcion="Producto Final", 
             departamento="Ensamblaje", 
             tipo_trabajador=1, 
             tiene_subfabricaciones=False
        )
        session.add(prod)
        session.commit()

        # Primero buscamos la fabricación creada
        fab = repo.get_fabricacion_by_codigo("FAB-E2E-001")
        assert fab is not None
        
        assert repo.add_product_to_fabricacion(fab.id, "PROD-FINAL-E2E", 10) is True
        
        # 5. Verificar estado final
        fab_details = repo.get_fabricacion_by_id(fab.id)
        assert fab_details.codigo == "FAB-E2E-001"
        assert len(fab_details.preprocesos) == 1
        assert fab_details.preprocesos[0].nombre == "Preproceso E2E"
        
        products = repo.get_products_for_fabricacion(fab.id)
        assert len(products) == 1
        assert products[0].producto_codigo == "PROD-FINAL-E2E"
        assert products[0].cantidad == 10
        
        # 6. Eliminar (Cleanup)
        assert repo.delete_fabricacion(fab.id) is True
        assert repo.get_fabricacion_by_codigo("FAB-E2E-001") is None
        
        # Verificar que la eliminación en cascada de la tabla link funcionó
        # (aunque el test unitario ya lo cubre, este es un chequeo extra de e2e)
        products_after = repo.get_products_for_fabricacion(fab.id)
        assert len(products_after) == 0
