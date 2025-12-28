
import pytest
from datetime import date
from core.dtos import MachineDTO

@pytest.mark.e2e
class TestMachineWorkflow:
    """Tests End-to-End para el flujo completo de gestión de Máquinas."""

    def test_machine_full_lifecycle(self, repos, session):
        """
        Escenario: Ciclo de vida completo de un usuario gestionando una máquina.
        
        1. Crear máquina
        2. Buscar y verificar
        3. Actualizar datos
        4. Añadir mantenimiento
        5. Añadir grupos de preparación
        6. Eliminar máquina
        7. Verificar limpieza
        """
        machine_repo = repos["machine"]
        
        # 1. CREAR
        print("\nStep 1: Crear máquina")
        success = machine_repo.add_machine(
            nombre="E2E Machine",
            departamento="Planta 1",
            tipo_proceso="Mecanizado",
            activa=True
        )
        assert success == True
        
        # 2. BUSCAR
        print("Step 2: Buscar máquina")
        # Asumimos que podemos encontrarla por nombre obteniendo todas o filtrando
        machines = machine_repo.get_all_machines()
        target_machine = next((m for m in machines if m.nombre == "E2E Machine"), None)
        
        assert target_machine is not None
        assert isinstance(target_machine, MachineDTO)
        m_id = target_machine.id
        
        # 3. ACTUALIZAR
        print("Step 3: Actualizar máquina")
        success = machine_repo.update_machine(
            machine_id=m_id,
            nombre="E2E Machine V2",
            departamento="Planta 2",
            tipo_proceso="Ensamblaje",
            activa=True
        )
        assert success == True
        
        # Verificar actualización
        machines_v2 = machine_repo.get_all_machines()
        updated_machine = next(m for m in machines_v2 if m.id == m_id)
        assert updated_machine.nombre == "E2E Machine V2"
        assert updated_machine.departamento == "Planta 2"
        
        # 4. MANTENIMIENTO
        print("Step 4: Añadir mantenimiento")
        success = machine_repo.add_machine_maintenance(
            machine_id=m_id,
            maintenance_date=date.today(),
            notes="Mantenimiento inicial"
        )
        assert success == True
        
        history = machine_repo.get_machine_maintenance_history(m_id)
        assert len(history) == 1
        assert history[0].notes == "Mantenimiento inicial"
        
        # 5. GRUPOS DE PREPARACIÓN
        print("Step 5: Añadir grupos y pasos")
        g_id = machine_repo.add_prep_group(
            machine_id=m_id,
            name="Grupo E2E",
            description="Test",
            producto_codigo=None
        )
        assert isinstance(g_id, int)
        
        s_id = machine_repo.add_prep_step(
            group_id=g_id,
            name="Paso E2E",
            time=5.0,
            description="Desc",
            is_daily=True
        )
        assert isinstance(s_id, int)
        
        # 6. ELIMINAR
        print("Step 6: Eliminar máquina")
        # AHORA que implementamos delete_machine, esto debería funcionar
        success = machine_repo.delete_machine(m_id)
        assert success == True
        
        # 7. VERIFICAR LIMPIEZA
        print("Step 7: Verificar limpieza")
        machines_final = machine_repo.get_all_machines()
        deleted = next((m for m in machines_final if m.id == m_id), None)
        assert deleted is None
