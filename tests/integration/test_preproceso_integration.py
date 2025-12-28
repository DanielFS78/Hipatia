import pytest
from database.models import Preproceso, Fabricacion, Material

@pytest.mark.integration
class TestPreprocesoIntegration:
    """Tests de integración para PreprocesoRepository."""

    def test_preproceso_material_interaction(self, repos, session):
        """Verifica la interacción completa entre preprocesos y materiales."""
        # 1. Crear Materiales
        mat_repo = repos["material"]
        m1 = Material(codigo_componente="INT-01", descripcion_componente="Integrated Mat 1")
        m2 = Material(codigo_componente="INT-02", descripcion_componente="Integrated Mat 2")
        session.add_all([m1, m2])
        session.commit()
        
        # 2. Crear Preproceso usando los IDs de materiales creados
        repo = repos["preproceso"]
        data = {
            "nombre": "Preproceso Integrado",
            "descripcion": "Test Integración",
            "tiempo": 30.0,
            "componentes_ids": [m1.id, m2.id]
        }
        repo.create_preproceso(data)
        
        # 3. Verificar que la relación se persistió
        preproceso = session.query(Preproceso).filter_by(nombre="Preproceso Integrado").first()
        assert len(preproceso.materiales) == 2
        
        # 4. Verificar recuperación mediante repositorio (método legacy que devuelve tuplas)
        componentes = repo.get_preproceso_components(preproceso.id)
        assert len(componentes) == 2
        # Ordenado por descripcion: Integrated Mat 1, Integrated Mat 2
        assert componentes[0].descripcion == "Integrated Mat 1"

    def test_fabricacion_full_lifecycle(self, repos, session):
        """Verifica ciclo de vida de fabricación con preprocesos."""
        # Arrange
        p1 = Preproceso(nombre="P1", descripcion="D1", tiempo=10)
        p2 = Preproceso(nombre="P2", descripcion="D2", tiempo=20)
        session.add_all([p1, p2])
        session.commit()
        
        repo = repos["preproceso"]
        
        # Act: Crear con preprocesos
        data = {"codigo": "FAB-INT", "descripcion": "Fab Integration"}
        data["preprocesos_ids"] = [p1.id, p2.id]
        repo.create_fabricacion_with_preprocesos(data)
        
        # Assert: Verificar
        fab_dto = repo.get_fabricacion_by_id(
            session.query(Fabricacion).filter_by(codigo="FAB-INT").first().id
        )
        assert len(fab_dto.preprocesos) == 2
        
        # Act: Actualizar (quitar un preproceso)
        repo.update_fabricacion_and_preprocesos(fab_dto.id, data, [p1.id])
        
        # Assert
        fab_dto_updated = repo.get_fabricacion_by_id(fab_dto.id)
        assert len(fab_dto_updated.preprocesos) == 1
        assert fab_dto_updated.preprocesos[0].nombre == "P1"
