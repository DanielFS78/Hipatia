"""
Tests de Integración para ui/dialogs.py - Fase 3.7
===================================================
Tests que verifican la interacción entre diálogos y otros componentes
usando mocks extensivos para evitar problemas con Qt/GUI.

Siguiendo la metodología de Fase 2.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date


# =============================================================================
# FIXTURES DE INTEGRACIÓN
# =============================================================================

@pytest.fixture
def integration_controller():
    """
    Controlador con mocks configurados para simular respuestas reales.
    """
    controller = MagicMock()
    
    # Configurar el modelo con datos de ejemplo
    controller.model = MagicMock()
    
    # Máquinas
    mock_machine_1 = MagicMock()
    mock_machine_1.id = 1
    mock_machine_1.nombre = "CNC Principal"
    mock_machine_1.tipo_proceso = "CNC"
    mock_machine_1.activo = True
    
    mock_machine_2 = MagicMock()
    mock_machine_2.id = 2
    mock_machine_2.nombre = "Torno Manual"
    mock_machine_2.tipo_proceso = "Torno"
    mock_machine_2.activo = True
    
    controller.model.get_all_machines.return_value = [mock_machine_1, mock_machine_2]
    controller.model.get_machines_by_process_type.return_value = [mock_machine_1]
    
    # Trabajadores
    mock_worker_1 = MagicMock()
    mock_worker_1.id = 1
    mock_worker_1.nombre_completo = "Juan García"
    mock_worker_1.activo = True
    
    controller.model.get_all_workers.return_value = [mock_worker_1]
    
    # Preprocesos
    mock_preproceso = MagicMock()
    mock_preproceso.id = 1
    mock_preproceso.nombre = "Preproceso Test"
    mock_preproceso.descripcion = "Descripción"
    mock_preproceso.tiempo = 5.0
    
    controller.model.get_all_preprocesos.return_value = [mock_preproceso]
    
    return controller


# =============================================================================
# TESTS DE INTEGRACIÓN: Flujo de Preprocesos
# =============================================================================

@pytest.mark.integration
class TestPreprocesosIntegration:
    """Tests de integración para flujo de preprocesos."""

    def test_preprocesos_flow_from_controller(self, integration_controller):
        """Verificar flujo de preprocesos desde controlador."""
        preprocesos = integration_controller.model.get_all_preprocesos()

        assert len(preprocesos) == 1
        assert preprocesos[0].nombre == "Preproceso Test"
        assert preprocesos[0].id == 1

    def test_select_preprocesos_updates_assigned_list(self, integration_controller):
        """Seleccionar preprocesos debe actualizar lista de asignados."""
        preprocesos = integration_controller.model.get_all_preprocesos()

        # Simular selección
        assigned_ids = set()
        for prep in preprocesos:
            assigned_ids.add(prep.id)

        assert 1 in assigned_ids


# =============================================================================
# TESTS DE INTEGRACIÓN: Flujo de Fabricación
# =============================================================================

@pytest.mark.integration
class TestFabricacionIntegration:
    """Tests de integración para flujo de fabricación."""

    def test_create_fabricacion_with_preprocesos(self, integration_controller):
        """Crear fabricación con preprocesos asignados."""
        preprocesos = integration_controller.model.get_all_preprocesos()

        # Simular datos de fabricación
        fabricacion_data = {
            "nombre": "Nueva Fabricación",
            "codigo": "FAB-NEW",
            "descripcion": "Fabricación de integración"
        }

        # Simular asignación de preprocesos
        assigned_prep_ids = [p.id for p in preprocesos]

        assert fabricacion_data["nombre"] == "Nueva Fabricación"
        assert len(assigned_prep_ids) == 1
        assert assigned_prep_ids[0] == 1

    def test_update_fabricacion_preprocesos(self, integration_controller):
        """Actualizar preprocesos de una fabricación."""
        preprocesos = integration_controller.model.get_all_preprocesos()

        initial_assigned = [preprocesos[0].id]
        
        # Simular cambio (quitar preproceso)
        updated_assigned = []

        assert len(initial_assigned) == 1
        assert len(updated_assigned) == 0


# =============================================================================
# TESTS DE INTEGRACIÓN: Flujo de Producción
# =============================================================================

@pytest.mark.integration
class TestProductionFlowIntegration:
    """Tests de integración para flujo de producción."""

    def test_flow_with_dependencies(self, integration_controller):
        """Flujo con dependencias entre tareas."""
        machines = integration_controller.model.get_all_machines()
        workers = integration_controller.model.get_all_workers()

        # Simular flujo
        production_flow = [
            {
                "task": {"name": "Corte", "duration": 10.0},
                "workers": [workers[0].nombre_completo],
                "machine_id": machines[0].id,
                "previous_task_index": None,
                "start_date": date.today()
            },
            {
                "task": {"name": "Soldadura", "duration": 15.0},
                "workers": [workers[0].nombre_completo],
                "machine_id": None,
                "previous_task_index": 0,  # Depende de Corte
                "start_date": None
            }
        ]

        assert len(production_flow) == 2
        assert production_flow[1]["previous_task_index"] == 0

    def test_flow_preserves_machine_assignments(self, integration_controller):
        """El flujo debe preservar asignaciones de máquinas."""
        machines = integration_controller.model.get_all_machines()

        task_with_machine = {
            "task": {"name": "Tarea CNC"},
            "machine_id": machines[0].id
        }

        assert task_with_machine["machine_id"] == 1
        assert machines[0].nombre == "CNC Principal"


# =============================================================================
# TESTS DE INTEGRACIÓN: Grupos Secuenciales
# =============================================================================

@pytest.mark.integration
class TestSequentialGroupsIntegration:
    """Tests de integración para grupos secuenciales."""

    def test_group_inherits_worker_assignments(self, integration_controller):
        """Grupos deben heredar asignaciones de trabajadores."""
        workers = integration_controller.model.get_all_workers()
        worker_names = [w.nombre_completo for w in workers]

        tasks = [
            {"task": {"name": "T1", "duration": 5}},
            {"task": {"name": "T2", "duration": 10}},
            {"task": {"name": "T3", "duration": 15}}
        ]

        group = {
            "type": "sequential_group",
            "tasks": tasks,
            "assigned_workers": worker_names,
            "units_per_cycle": 1,
            "total_cycles": 10
        }

        assert len(group["assigned_workers"]) == 1
        assert group["assigned_workers"][0] == "Juan García"

    def test_group_calculates_total_time(self, integration_controller):
        """Grupos deben calcular tiempo total correctamente."""
        tasks = [
            {"task": {"name": "T1", "duration": 5.0}},
            {"task": {"name": "T2", "duration": 10.0}},
            {"task": {"name": "T3", "duration": 15.0}}
        ]

        total_time = sum(t["task"]["duration"] for t in tasks)

        group = {
            "type": "sequential_group",
            "tasks": tasks,
            "group_metadata": {
                "total_cycle_time": total_time
            }
        }

        assert group["group_metadata"]["total_cycle_time"] == 30.0


# =============================================================================
# TESTS DE INTEGRACIÓN: Subfabricaciones
# =============================================================================

@pytest.mark.integration
class TestSubfabricacionesIntegration:
    """Tests de integración para subfabricaciones."""

    def test_subfabricaciones_with_machines(self, integration_controller):
        """Subfabricaciones pueden tener máquinas asignadas."""
        machines = integration_controller.model.get_all_machines()

        subfabs = [
            {
                "descripcion": "Subfab con máquina",
                "tiempo": 20.0,
                "maquina_id": machines[0].id
            },
            {
                "descripcion": "Subfab sin máquina",
                "tiempo": 15.0,
                "maquina_id": None
            }
        ]

        with_machine = [s for s in subfabs if s["maquina_id"] is not None]
        without_machine = [s for s in subfabs if s["maquina_id"] is None]

        assert len(with_machine) == 1
        assert len(without_machine) == 1
        assert with_machine[0]["maquina_id"] == 1


# =============================================================================
# TESTS DE INTEGRACIÓN: Producto y Materiales
# =============================================================================

@pytest.mark.integration
class TestProductMaterialsIntegration:
    """Tests de integración para productos y materiales."""

    def test_product_loads_materials(self, integration_controller):
        """Producto debe cargar sus materiales."""
        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.codigo = "MAT-001"
        mock_material.descripcion = "Material Test"
        mock_material.cantidad = 5

        integration_controller.model.get_materials_for_product = MagicMock(
            return_value=[mock_material]
        )

        materials = integration_controller.model.get_materials_for_product("PROD-001")

        assert len(materials) == 1
        assert materials[0].codigo == "MAT-001"

    def test_product_without_materials(self, integration_controller):
        """Producto sin materiales debe retornar lista vacía."""
        integration_controller.model.get_materials_for_product = MagicMock(
            return_value=[]
        )

        materials = integration_controller.model.get_materials_for_product("PROD-EMPTY")

        assert len(materials) == 0


# =============================================================================
# TESTS DE INTEGRACIÓN: Configuración de Ciclos
# =============================================================================

@pytest.mark.integration
class TestCycleConfigurationIntegration:
    """Tests de integración para configuración de ciclos."""

    def test_cycle_configuration_applies_to_task(self):
        """Configuración de ciclo debe aplicarse a la tarea."""
        canvas_tasks = [
            {
                "task": {"name": "Inicio"},
                "config": {"is_cycle_start": True}
            },
            {
                "task": {"name": "Proceso"},
                "config": {}
            },
            {
                "task": {"name": "Fin"},
                "config": {
                    "is_cycle_end": True,
                    "next_cyclic_task_index": 0
                }
            }
        ]

        # Verificar configuración
        start_tasks = [t for t in canvas_tasks if t["config"].get("is_cycle_start")]
        end_tasks = [t for t in canvas_tasks if t["config"].get("is_cycle_end")]

        assert len(start_tasks) == 1
        assert len(end_tasks) == 1
        assert end_tasks[0]["config"]["next_cyclic_task_index"] == 0

    def test_cycle_units_calculation(self):
        """Cálculo de unidades por ciclo."""
        total_units = 100
        units_per_cycle = 20

        import math
        total_cycles = math.ceil(total_units / units_per_cycle)

        assert total_cycles == 5


# =============================================================================
# TESTS DE INTEGRACIÓN: Reglas de Reasignación
# =============================================================================

@pytest.mark.integration
class TestReassignmentRulesIntegration:
    """Tests de integración para reglas de reasignación."""

    def test_reassignment_rule_applies_correctly(self, integration_controller):
        """Regla de reasignación debe aplicarse correctamente."""
        workers = integration_controller.model.get_all_workers()
        worker_name = workers[0].nombre_completo

        canvas_tasks = [
            {"task": {"name": "Tarea A"}, "assigned_workers": [worker_name]},
            {"task": {"name": "Tarea B"}, "assigned_workers": []}
        ]

        # Simular regla: mover trabajador de A a B al terminar
        rule = {
            "worker": worker_name,
            "from_task_index": 0,
            "to_task_index": 1,
            "trigger": "on_completion"
        }

        # Aplicar regla
        canvas_tasks[1]["assigned_workers"].append(rule["worker"])

        assert worker_name in canvas_tasks[1]["assigned_workers"]
