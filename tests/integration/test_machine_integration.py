
import pytest
from database.models import Maquina, MachineMaintenanc, GrupoPreparacion, PreparacionPaso, Producto

@pytest.mark.integration
class TestMachineIntegration:
    """Tests de integración para interacciones reales de base de datos y relaciones."""

    def test_machine_cascade_delete_maintenance(self, repos, session):
        """Verifica que eliminar una máquina elimina sus mantenimientos."""
        machine_repo = repos["machine"]
        
        # 1. Crear Máquina y mantenimiento
        m = Maquina(nombre="CascadeTest", departamento="D", tipo_proceso="P")
        session.add(m)
        session.commit()
        m_id = m.id
        
        # Añadir mantenimiento directamente (o via repo)
        maint = MachineMaintenanc(machine_id=m_id, maintenance_date="2025-01-01", notes="Notas")
        session.add(maint)
        session.commit()
        
        assert session.query(MachineMaintenanc).filter_by(machine_id=m_id).count() == 1
        
        # 2. Eliminar máquina (simulando borrado desde modelo, ya que el repo no tiene delete_machine aún expuesto o explícito en la interfaz analizada, 
        # pero verificamos la propiedad de la BD. Si el repo tuviera delete_machine lo usaríamos)
        # Revisando el repo analizado, NO TIENE delete_machine público, pero TIENE delete_prep_group.
        # Vamos a verificar la cascada de BD borrando el objeto.
        
        session.delete(m)
        session.commit()
        
        # 3. Verificar cascada
        assert session.query(MachineMaintenanc).filter_by(machine_id=m_id).count() == 0

    def test_machine_prep_group_product_relation(self, repos, session):
        """Verifica que se puede asignar un producto real a un grupo de preparación."""
        machine_repo = repos["machine"]
        
        # Crear Máquina
        m = Maquina(nombre="RelTest", departamento="D", tipo_proceso="P")
        session.add(m)
        
        # Crear Producto
        p = Producto(codigo="PROD-REL", descripcion="Desc", departamento="D", tipo_trabajador=1, tiene_subfabricaciones=False)
        session.add(p)
        session.commit()
        
        # Usar el repo para crear el grupo vinculado
        g_id = machine_repo.add_prep_group(
            machine_id=m.id,
            name="Grupo Con Producto", 
            description="Desc", 
            producto_codigo="PROD-REL"
        )
        
        session.commit() # Asegurar persistencia
        
        # Verificar relación
        grupo = session.get(GrupoPreparacion, g_id)
        assert grupo.producto_codigo == "PROD-REL"
        assert grupo.producto.descripcion == "Desc" # Acceso via relación ORM

    def test_prep_group_cascade_delete_steps(self, repos, session):
        """Verifica que al borrar un grupo se borran sus pasos (Integración real)."""
        machine_repo = repos["machine"]
        
        # Setup
        m = Maquina(nombre="GroupCascade", departamento="D", tipo_proceso="P")
        session.add(m)
        session.commit()
        
        g_id = machine_repo.add_prep_group(m.id, "G borrar", "D", None)
        machine_repo.add_prep_step(g_id, "S1", 10, "D", False)
        session.commit()
        
        assert session.query(PreparacionPaso).count() == 1
        
        # Act
        machine_repo.delete_prep_group(g_id)
        # El repo hace safe_execute que hace commit/rollback.
        
        # Assert
        assert session.get(GrupoPreparacion, g_id) is None
        assert session.query(PreparacionPaso).filter_by(grupo_id=g_id).count() == 0
