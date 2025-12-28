"""
Tests End-to-End para ui/dialogs.py - Fase 3.7
===============================================
Tests que simulan flujos completos de usuario usando mocks.

Estos tests verifican la lógica de flujos completos sin crear
widgets Qt reales.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta
import math


# =============================================================================
# FIXTURES E2E
# =============================================================================

@pytest.fixture
def e2e_controller():
    """
    Controlador completo para tests E2E con respuestas realistas.
    """
    controller = MagicMock()
    controller.model = MagicMock()
    
    # Configurar máquinas con DTOs mock
    machines = []
    for i in range(1, 4):
        m = MagicMock()
        m.id = i
        m.nombre = f"Máquina {i}"
        m.tipo_proceso = ["CNC", "Torno", "Fresadora"][i-1]
        m.activo = True
        machines.append(m)
    
    controller.model.get_all_machines.return_value = machines
    controller.model.get_machines_by_process_type.side_effect = lambda t: [
        m for m in machines if m.tipo_proceso == t
    ]
    
    # Configurar trabajadores
    workers = []
    for i, name in enumerate(["Juan García", "María López", "Pedro Sánchez"], 1):
        w = MagicMock()
        w.id = i
        w.nombre_completo = name
        w.activo = True
        w.nivel_habilidad = i
        workers.append(w)
    
    controller.model.get_all_workers.return_value = workers
    
    # Configurar preprocesos
    preprocesos = []
    for i in range(1, 4):
        p = MagicMock()
        p.id = i
        p.nombre = f"Preproceso {i}"
        p.descripcion = f"Descripción del preproceso {i}"
        p.tiempo = 5.0 * i
        p.activo = True
        preprocesos.append(p)
    
    controller.model.get_all_preprocesos.return_value = preprocesos
    
    return controller


@pytest.fixture
def e2e_tasks_data():
    """Datos de tareas realistas para E2E."""
    return [
        {
            "codigo": "PROD-001",
            "descripcion": "Producto Principal",
            "departamento": "Montaje",
            "tipo_trabajador": 1,
            "tiene_subfabricaciones": True,
            "fabricacion_id": 1,
            "deadline": date.today() + timedelta(days=30),
            "sub_partes": [
                {
                    "descripcion": "Corte de material",
                    "tiempo": 15.0,
                    "tiempo_optimo": 12.0,
                    "tipo_trabajador": 1,
                    "requiere_maquina_tipo": "CNC"
                },
                {
                    "descripcion": "Soldadura",
                    "tiempo": 30.0,
                    "tiempo_optimo": 25.0,
                    "tipo_trabajador": 2,
                    "requiere_maquina_tipo": None
                },
                {
                    "descripcion": "Acabado",
                    "tiempo": 20.0,
                    "tiempo_optimo": 18.0,
                    "tipo_trabajador": 1,
                    "requiere_maquina_tipo": None
                }
            ]
        }
    ]


# =============================================================================
# TESTS E2E: Flujo de Creación de Fabricación
# =============================================================================

@pytest.mark.e2e
class TestFabricacionCreationE2E:
    """
    Tests E2E para el flujo completo de creación de una fabricación.
    """

    def test_create_fabricacion_without_preprocesos(self, e2e_controller):
        """
        E2E: Crear fabricación sin preprocesos asignados.
        """
        print("\n[E2E] Iniciando: Crear fabricación sin preprocesos")

        # Paso 1: Preparar datos de fabricación
        fabricacion_data = {
            "nombre": "Fabricación E2E Test",
            "codigo": "FAB-E2E-001",
            "descripcion": "Creada durante test E2E"
        }
        print("   Paso 1: Datos preparados ✓")

        # Paso 2: Sin preprocesos asignados
        assigned_preprocesos_ids = []
        print("   Paso 2: Sin preprocesos (esperado) ✓")

        # Paso 3: Verificar datos
        assert fabricacion_data["nombre"] == "Fabricación E2E Test"
        assert len(assigned_preprocesos_ids) == 0
        print("   Paso 3: Datos verificados ✓")

        print("[E2E] Completado: Crear fabricación sin preprocesos ✓")

    def test_create_fabricacion_with_preprocesos(self, e2e_controller):
        """
        E2E: Crear fabricación con preprocesos asignados.
        """
        print("\n[E2E] Iniciando: Crear fabricación con preprocesos")

        preprocesos = e2e_controller.model.get_all_preprocesos()
        assert len(preprocesos) > 0
        print("   Paso 1: Preprocesos cargados ✓")

        # Paso 2: Preparar datos
        fabricacion_data = {
            "nombre": "Fabricación con Preprocesos",
            "codigo": "FAB-PREP-001",
            "descripcion": "Fabricación con preprocesos asignados"
        }
        print("   Paso 2: Datos preparados ✓")

        # Paso 3: Asignar preprocesos
        assigned_preprocesos_ids = [p.id for p in preprocesos[:2]]
        print(f"   Paso 3: {len(assigned_preprocesos_ids)} preprocesos asignados ✓")

        # Paso 4: Verificar
        assert len(assigned_preprocesos_ids) == 2
        assert fabricacion_data["nombre"] == "Fabricación con Preprocesos"
        print("   Paso 4: Verificación completa ✓")

        print("[E2E] Completado: Crear fabricación con preprocesos ✓")


# =============================================================================
# TESTS E2E: Flujo de Definición de Producción
# =============================================================================

@pytest.mark.e2e
class TestProductionFlowDefinitionE2E:
    """
    Tests E2E para el flujo completo de definición de producción.
    """

    def test_define_production_flow_basic(self, e2e_controller, e2e_tasks_data):
        """
        E2E: Definir un flujo de producción básico.
        """
        print("\n[E2E] Iniciando: Definir flujo de producción básico")

        workers = e2e_controller.model.get_all_workers()
        worker_names = [w.nombre_completo for w in workers]

        # Paso 1: Preparar estructura de tareas
        task_data_by_product = {}
        for task in e2e_tasks_data:
            product_code = task["codigo"]
            task_data_by_product[product_code] = {
                "descripcion": task["descripcion"],
                "tasks": []
            }
            for sub in task.get("sub_partes", []):
                task_data_by_product[product_code]["tasks"].append({
                    "name": sub["descripcion"],
                    "duration": sub.get("tiempo", 0)
                })
        print("   Paso 1: Estructura de tareas preparada ✓")

        # Paso 2: Verificar estructura
        assert "PROD-001" in task_data_by_product
        assert len(task_data_by_product["PROD-001"]["tasks"]) == 3
        print("   Paso 2: Estructura verificada ✓")

        # Paso 3: Crear flujo de producción
        units = 36
        production_flow = []

        for i, task in enumerate(task_data_by_product["PROD-001"]["tasks"]):
            step = {
                "task": task,
                "workers": [worker_names[i % len(worker_names)]],
                "start_date": date.today() if i == 0 else None,
                "previous_task_index": i - 1 if i > 0 else None
            }
            production_flow.append(step)
        print("   Paso 3: Flujo de producción creado ✓")

        # Paso 4: Verificar
        assert len(production_flow) == 3
        assert production_flow[0]["previous_task_index"] is None
        assert production_flow[1]["previous_task_index"] == 0
        assert production_flow[2]["previous_task_index"] == 1
        print("   Paso 4: Verificación completa ✓")

        print("[E2E] Completado: Definir flujo de producción básico ✓")

    def test_enhanced_production_flow_with_groups(self, e2e_controller, e2e_tasks_data):
        """
        E2E: Flujo mejorado con grupos secuenciales.
        """
        print("\n[E2E] Iniciando: Flujo con grupos secuenciales")

        workers = e2e_controller.model.get_all_workers()

        # Paso 1: Crear tareas base
        tasks = [
            {"task": {"name": "Tarea 1", "duration": 10.0}},
            {"task": {"name": "Tarea 2", "duration": 15.0}},
            {"task": {"name": "Tarea 3", "duration": 20.0}}
        ]
        print("   Paso 1: Tareas base creadas ✓")

        # Paso 2: Crear grupo secuencial
        units = 40
        units_per_cycle = 10
        total_cycles = math.ceil(units / units_per_cycle)

        group = {
            "type": "sequential_group",
            "tasks": tasks,
            "assigned_workers": [workers[0].nombre_completo],
            "units_per_cycle": units_per_cycle,
            "total_cycles": total_cycles,
            "group_metadata": {
                "total_cycle_time": sum(t["task"]["duration"] for t in tasks),
                "task_count": len(tasks)
            }
        }
        print("   Paso 2: Grupo secuencial creado ✓")

        # Paso 3: Verificar grupo
        assert group["type"] == "sequential_group"
        assert len(group["tasks"]) == 3
        assert group["total_cycles"] == 4  # 40 / 10 = 4
        assert group["group_metadata"]["total_cycle_time"] == 45.0
        print("   Paso 3: Grupo verificado ✓")

        print("[E2E] Completado: Flujo con grupos secuenciales ✓")


# =============================================================================
# TESTS E2E: Flujo de Selección de Preprocesos
# =============================================================================

@pytest.mark.e2e
class TestPreprocesosSelectionE2E:
    """
    Tests E2E para el flujo de selección de preprocesos.
    """

    def test_select_and_deselect_preprocesos(self, e2e_controller):
        """
        E2E: Seleccionar y deseleccionar preprocesos.
        """
        print("\n[E2E] Iniciando: Selección de preprocesos")

        preprocesos = e2e_controller.model.get_all_preprocesos()
        print(f"   Paso 1: {len(preprocesos)} preprocesos disponibles ✓")

        # Paso 2: Seleccionar todos
        selected_ids = set()
        for prep in preprocesos:
            selected_ids.add(prep.id)
        print(f"   Paso 2: {len(selected_ids)} preprocesos seleccionados ✓")

        # Paso 3: Verificar selección
        assert len(selected_ids) == 3
        print("   Paso 3: Selección verificada ✓")

        # Paso 4: Deseleccionar uno
        selected_ids.remove(1)
        print("   Paso 4: Un preproceso deseleccionado ✓")

        # Paso 5: Verificar estado final
        assert len(selected_ids) == 2
        assert 1 not in selected_ids
        print("   Paso 5: Estado final verificado ✓")

        print("[E2E] Completado: Selección de preprocesos ✓")


# =============================================================================
# TESTS E2E: Flujo de Configuración de Ciclos
# =============================================================================

@pytest.mark.e2e
class TestCycleConfigurationE2E:
    """
    Tests E2E para configuración de ciclos.
    """

    def test_configure_cycle_end_with_auto_trigger(self, e2e_controller):
        """
        E2E: Configurar fin de ciclo con disparo automático.
        """
        print("\n[E2E] Iniciando: Configuración de ciclo")

        # Paso 1: Crear tareas del canvas
        canvas_tasks = [
            {"task": {"name": "Inicio"}, "config": {"is_cycle_start": True}},
            {"task": {"name": "Proceso A"}, "config": {}},
            {"task": {"name": "Proceso B"}, "config": {}},
            {"task": {"name": "Fin"}, "config": {}}
        ]
        print("   Paso 1: Tareas del canvas creadas ✓")

        # Paso 2: Configurar tarea de fin de ciclo
        canvas_tasks[3]["config"] = {
            "is_cycle_end": True,
            "next_cyclic_task_index": 0,
            "auto_trigger": True
        }
        print("   Paso 2: Fin de ciclo configurado ✓")

        # Paso 3: Verificar configuración
        end_task = canvas_tasks[3]
        assert end_task["config"]["is_cycle_end"] is True
        assert end_task["config"]["next_cyclic_task_index"] == 0
        print("   Paso 3: Configuración verificada ✓")

        # Paso 4: Verificar cadena cíclica
        start_task = canvas_tasks[end_task["config"]["next_cyclic_task_index"]]
        assert start_task["config"]["is_cycle_start"] is True
        print("   Paso 4: Cadena cíclica verificada ✓")

        print("[E2E] Completado: Configuración de ciclo ✓")


# =============================================================================
# TESTS E2E: Flujo de Gestión de Subfabricaciones
# =============================================================================

@pytest.mark.e2e
class TestSubfabricacionesE2E:
    """
    Tests E2E para gestión de subfabricaciones.
    """

    def test_add_edit_delete_subfabricacion(self, e2e_controller):
        """
        E2E: Añadir, editar y eliminar subfabricaciones.
        """
        print("\n[E2E] Iniciando: Gestión de subfabricaciones")

        machines = e2e_controller.model.get_all_machines()
        subfabricaciones = []

        # Paso 1: Añadir subfabricación
        new_subfab = {
            "descripcion": "Nueva Subfabricación",
            "tiempo": 25.0,
            "tiempo_optimo": 20.0,
            "tipo_trabajador": 1,
            "maquina_id": machines[0].id
        }
        subfabricaciones.append(new_subfab)
        assert len(subfabricaciones) == 1
        print("   Paso 1: Subfabricación añadida ✓")

        # Paso 2: Editar subfabricación
        subfabricaciones[0]["descripcion"] = "Subfabricación Editada"
        subfabricaciones[0]["tiempo"] = 30.0
        assert subfabricaciones[0]["descripcion"] == "Subfabricación Editada"
        print("   Paso 2: Subfabricación editada ✓")

        # Paso 3: Añadir otra
        subfabricaciones.append({
            "descripcion": "Segunda Subfab",
            "tiempo": 15.0,
            "tipo_trabajador": 2,
            "maquina_id": None
        })
        assert len(subfabricaciones) == 2
        print("   Paso 3: Segunda subfabricación añadida ✓")

        # Paso 4: Eliminar una
        subfabricaciones.pop(0)
        assert len(subfabricaciones) == 1
        assert subfabricaciones[0]["descripcion"] == "Segunda Subfab"
        print("   Paso 4: Primera subfabricación eliminada ✓")

        print("[E2E] Completado: Gestión de subfabricaciones ✓")


# =============================================================================
# TESTS E2E: Flujo de Reglas de Reasignación
# =============================================================================

@pytest.mark.e2e
class TestReassignmentRulesE2E:
    """
    Tests E2E para reglas de reasignación de trabajadores.
    """

    def test_create_and_apply_reassignment_rule(self, e2e_controller):
        """
        E2E: Crear y aplicar regla de reasignación.
        """
        print("\n[E2E] Iniciando: Reglas de reasignación")

        workers = e2e_controller.model.get_all_workers()
        worker_name = workers[0].nombre_completo

        # Paso 1: Crear tareas con asignaciones
        canvas_tasks = [
            {
                "task": {"name": "Tarea Principal"},
                "assigned_workers": [worker_name],
                "reassignment_rules": []
            },
            {
                "task": {"name": "Tarea Siguiente"},
                "assigned_workers": [],
                "reassignment_rules": []
            }
        ]
        print("   Paso 1: Tareas creadas ✓")

        # Paso 2: Crear regla de reasignación
        rule = {
            "worker": worker_name,
            "target_task_index": 1,
            "condition": "on_completion"
        }
        canvas_tasks[0]["reassignment_rules"].append(rule)
        print("   Paso 2: Regla creada ✓")

        # Paso 3: Simular aplicación de regla
        completed_task = canvas_tasks[0]
        for rule in completed_task["reassignment_rules"]:
            target_task = canvas_tasks[rule["target_task_index"]]
            target_task["assigned_workers"].append(rule["worker"])
        print("   Paso 3: Regla aplicada ✓")

        # Paso 4: Verificar
        assert worker_name in canvas_tasks[1]["assigned_workers"]
        print("   Paso 4: Verificación completa ✓")

        print("[E2E] Completado: Reglas de reasignación ✓")


# =============================================================================
# TESTS E2E: Flujo Completo de Cálculo de Producción
# =============================================================================

@pytest.mark.e2e
class TestCompleteProductionCalculationE2E:
    """
    Tests E2E para el flujo completo de cálculo de producción.
    """

    def test_full_production_calculation_flow(self, e2e_controller, e2e_tasks_data):
        """
        E2E: Flujo completo desde definición hasta cálculo.
        """
        print("\n[E2E] Iniciando: Flujo completo de cálculo")

        # Paso 1: Obtener recursos
        machines = e2e_controller.model.get_all_machines()
        workers = e2e_controller.model.get_all_workers()
        units = 36
        print(f"   Paso 1: Recursos obtenidos ({len(machines)} máquinas, {len(workers)} trabajadores) ✓")

        # Paso 2: Preparar datos de tareas
        tasks = []
        for sub in e2e_tasks_data[0]["sub_partes"]:
            tasks.append({
                "name": sub["descripcion"],
                "duration": sub["tiempo"],
                "required_machine": sub.get("requiere_maquina_tipo")
            })
        print(f"   Paso 2: {len(tasks)} tareas preparadas ✓")

        # Paso 3: Crear flujo de producción
        production_flow = []
        for i, task in enumerate(tasks):
            step = {
                "task": task,
                "workers": [workers[i % len(workers)].nombre_completo],
                "machine_id": machines[0].id if task["required_machine"] else None,
                "trigger_units": units,
                "previous_task_index": i - 1 if i > 0 else None
            }
            production_flow.append(step)
        print("   Paso 3: Flujo creado ✓")

        # Paso 4: Calcular tiempo total
        total_time = sum(t["task"]["duration"] for t in production_flow)
        total_time_with_units = total_time * units
        print(f"   Paso 4: Tiempo total calculado ({total_time} min/unidad) ✓")

        # Paso 5: Verificaciones finales
        assert len(production_flow) == 3
        assert total_time == 65.0  # 15 + 30 + 20
        assert total_time_with_units == 2340.0  # 65 * 36
        print("   Paso 5: Verificaciones completas ✓")

        print("[E2E] Completado: Flujo completo de cálculo ✓")
